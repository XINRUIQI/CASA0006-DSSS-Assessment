"""
Step 4 – Fetch contributor data for prominent GitHub repos.

Part A: GET /repos/{owner}/{repo}/contributors  → contributor list
Part B: GET /users/{login}                      → contributor locations
Part C: GET /repos/{owner}/{repo}/commits       → commit history
         GET /repos/{owner}/{repo}/pulls         → PR history
         Build per-actor first-participation events for adoption-lag.

Outputs
-------
data/raw/github/github_repo_contributors.csv
    repo_full_name, contributor_login, contributions

data/raw/github/github_owner_locations.csv   (appended with new users)

data/raw/github/github_repo_participation_events.csv
    repo_full_name, actor_login, first_event_at, event_type

Supports resume: skips repos / users already fetched.
"""

import csv
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import GITHUB_TOKEN, DATA_RAW, TIME_START

HEADERS = {"Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

_RETRY_STRATEGY = Retry(
    total=5,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)

_thread_local = threading.local()


def _get_session():
    """Return a per-thread requests.Session (thread-safe)."""
    if not hasattr(_thread_local, "session"):
        s = requests.Session()
        s.mount("https://", HTTPAdapter(
            max_retries=_RETRY_STRATEGY,
            pool_maxsize=20,
        ))
        s.headers.update(HEADERS)
        _thread_local.session = s
    return _thread_local.session

CONTRIB_PER_PAGE = 100
MAX_CONTRIB_PAGES = 3        # up to 300 contributors per repo
LOCATION_BATCH_SAVE = 500    # checkpoint save interval


def _wait(resp):
    remaining = int(resp.headers.get("X-RateLimit-Remaining", 1))
    if remaining < 10:
        reset_ts = int(resp.headers.get("X-RateLimit-Reset", 0))
        sleep_sec = max(reset_ts - int(time.time()), 1) + 2
        print(f"  ⏳ Rate-limited ({remaining} left). Sleeping {sleep_sec}s …")
        time.sleep(sleep_sec)


# ───────────────────────────── Part A: Contributors ──────────────────────────

def _get_with_retry(url, params=None, max_retries=5):
    """GET with manual retry for ConnectionError on top of urllib3 retry."""
    session = _get_session()
    for attempt in range(max_retries):
        try:
            return session.get(url, params=params, timeout=30)
        except (requests.ConnectionError, requests.Timeout) as exc:
            wait = min(2 ** (attempt + 1), 120)
            print(f"  ⚠️  Connection error (attempt {attempt+1}/{max_retries}): {exc!r}")
            print(f"      Retrying in {wait}s …")
            time.sleep(wait)
    return session.get(url, params=params, timeout=30)


def fetch_contributors(repo_full_name):
    """Return list of (login, contributions) for a repo."""
    results = []
    for page in range(1, MAX_CONTRIB_PAGES + 1):
        url = f"https://api.github.com/repos/{repo_full_name}/contributors"
        params = {"per_page": CONTRIB_PER_PAGE, "page": page}
        resp = _get_with_retry(url, params=params)
        _wait(resp)
        if resp.status_code == 403:
            time.sleep(60)
            resp = _get_with_retry(url, params=params)
        if resp.status_code != 200:
            break
        items = resp.json()
        if not isinstance(items, list) or not items:
            break
        for c in items:
            login = c.get("login", "")
            contribs = c.get("contributions", 0)
            if login:
                results.append((login, contribs))
        if len(items) < CONTRIB_PER_PAGE:
            break
        time.sleep(0.3)
    return results


def collect_all_contributors():
    gh_csv = DATA_RAW / "github" / "github_candidates.csv"
    df = pd.read_csv(gh_csv, dtype=str)
    prominent = df[df["prominent_flag"] == "1"]
    repos = prominent["repo_full_name"].dropna().unique().tolist()
    print(f"  Prominent repos to fetch contributors for: {len(repos)}")

    out_path = DATA_RAW / "github" / "github_repo_contributors.csv"
    done_repos = set()
    existing_rows = []
    if out_path.exists():
        ex = pd.read_csv(out_path, dtype=str)
        done_repos = set(ex["repo_full_name"].unique())
        existing_rows = ex.values.tolist()
        print(f"  Already fetched: {len(done_repos)} repos (resuming)")

    todo = [r for r in repos if r not in done_repos]
    print(f"  Remaining: {len(todo)}\n")

    rows = list(existing_rows)
    for i, repo in enumerate(todo, 1):
        contribs = fetch_contributors(repo)
        for login, cnt in contribs:
            rows.append([repo, login, str(cnt)])

        if i % 100 == 0 or i == len(todo):
            print(f"  [{i}/{len(todo)}] {repo} → {len(contribs)} contributors")
            _save_contrib(rows, out_path)

        time.sleep(0.5)

    _save_contrib(rows, out_path)
    unique_logins = set(r[1] for r in rows)
    print(f"\n✅ Contributors: {len(rows)} records, {len(unique_logins)} unique users")
    return unique_logins


def _save_contrib(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["repo_full_name", "contributor_login", "contributions"])
        w.writerows(rows)


# ──────────────────────── Part B: Contributor Locations ───────────────────────

def fetch_user_location(login):
    url = f"https://api.github.com/users/{login}"
    resp = _get_with_retry(url)
    _wait(resp)
    if resp.status_code != 200:
        return {"login": login, "location": "", "name": "",
                "company": "", "bio": "", "type": "User", "status": f"http_{resp.status_code}"}
    data = resp.json()
    return {
        "login": login,
        "location": data.get("location") or "",
        "name": data.get("name") or "",
        "company": data.get("company") or "",
        "bio": (data.get("bio") or "")[:200],
        "type": data.get("type") or "User",
        "status": "ok",
    }


LOCATION_WORKERS = 10  # concurrent threads for location fetching


def fetch_missing_locations(all_logins):
    loc_path = DATA_RAW / "github" / "github_owner_locations.csv"
    if loc_path.exists():
        existing = pd.read_csv(loc_path, dtype=str)
        done = set(existing["login"].tolist())
        rows = existing.to_dict("records")
    else:
        done = set()
        rows = []

    todo = sorted(all_logins - done)
    print(f"\n  New contributor logins to fetch location: {len(todo)}")
    if not todo:
        print("  All locations already fetched.")
        return

    fieldnames = ["login", "location", "name", "company", "bio", "type", "status"]
    lock = threading.Lock()
    completed = [0]

    def _save_locations():
        with open(loc_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)

    def process_login(login):
        result = fetch_user_location(login)
        with lock:
            rows.append(result)
            completed[0] += 1
            if completed[0] % 500 == 0 or completed[0] == len(todo):
                print(f"  [{completed[0]}/{len(todo)}] last: {login} "
                      f"→ '{str(result.get('location', ''))[:40]}'")
                _save_locations()

    with ThreadPoolExecutor(max_workers=LOCATION_WORKERS) as pool:
        futures = [pool.submit(process_login, login) for login in todo]
        for f in as_completed(futures):
            try:
                f.result()
            except Exception as exc:
                print(f"  ⚠️  Location worker exception: {exc!r}")

    _save_locations()
    locs = [r for r in rows if isinstance(r.get("location", ""), str)
            and r["location"].strip()]
    print(f"\n✅ Locations: {len(rows)} total, {len(locs)} with location")


# ═══════════════════════════════════════════════════════════════════════════════
# Part C: Participation Chain (Commits API + PRs API)
#
# For each prominent repo, paginate through commits and PRs to extract
# each actor's FIRST participation event with a precise timestamp.
# All external requests are strictly serial with rate-limit checks.
# ═══════════════════════════════════════════════════════════════════════════════

MAX_COMMIT_PAGES = 50   # cap: 5 000 commits per repo
MAX_PR_PAGES = 20       # cap: 2 000 PRs per repo
CHECKPOINT_EVERY = 50   # save progress every N repos


def _strict_wait(resp):
    """Rate-limit guard for serial API calls (stricter than _wait)."""
    remaining = int(resp.headers.get("X-RateLimit-Remaining", 999))
    if remaining < 50:
        reset_ts = int(resp.headers.get("X-RateLimit-Reset", 0))
        sleep_sec = max(reset_ts - int(time.time()), 1) + 3
        print(f"  ⏳ Rate limit: {remaining} remaining. "
              f"Sleeping {sleep_sec}s until reset …")
        time.sleep(sleep_sec)


def _api_get(url, params=None):
    """Single serial GET with strict rate-limit check."""
    resp = _get_with_retry(url, params=params)
    _strict_wait(resp)
    return resp


def _fetch_repo_commits(repo):
    """
    Paginate GET /repos/{owner}/{repo}/commits.
    Return {login: earliest_ISO_date} for each commit author.
    """
    author_first = {}
    url = f"https://api.github.com/repos/{repo}/commits"
    base_params = {"per_page": 100}

    for page in range(1, MAX_COMMIT_PAGES + 1):
        params = {**base_params, "page": page}
        resp = _api_get(url, params=params)
        if resp.status_code == 409:
            break  # empty repo
        if resp.status_code != 200:
            break
        commits = resp.json()
        if not isinstance(commits, list) or not commits:
            break

        for c in commits:
            gh_author = c.get("author") or {}
            login = gh_author.get("login", "")
            if not login:
                continue
            date = (c.get("commit") or {}).get("author", {}).get("date", "")
            if not date:
                continue
            if login not in author_first or date < author_first[login]:
                author_first[login] = date

        if len(commits) < 100:
            break
    return author_first


def _fetch_repo_prs(repo):
    """
    Paginate GET /repos/{owner}/{repo}/pulls (oldest first).
    Return {login: earliest_ISO_date} for each PR author.
    """
    author_first = {}
    url = f"https://api.github.com/repos/{repo}/pulls"
    base_params = {"state": "all", "sort": "created",
                   "direction": "asc", "per_page": 100}

    for page in range(1, MAX_PR_PAGES + 1):
        params = {**base_params, "page": page}
        resp = _api_get(url, params=params)
        if resp.status_code != 200:
            break
        prs = resp.json()
        if not isinstance(prs, list) or not prs:
            break

        for pr in prs:
            login = (pr.get("user") or {}).get("login", "")
            if not login:
                continue
            date = pr.get("created_at", "")
            if not date:
                continue
            if login not in author_first or date < author_first[login]:
                author_first[login] = date

        if len(prs) < 100:
            break
    return author_first


def _save_events(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["repo_full_name", "actor_login",
                     "first_event_at", "event_type"])
        w.writerows(rows)


def collect_participation_events():
    """
    For each prominent repo, build a participation chain:
      1. 'create' event from candidates CSV (owner + created_at)
      2. 'commit' events from Commits API (each author's first commit)
      3. 'pr_opened' events from PRs API (each author's first PR)

    For each (repo, actor), only the earliest event is kept.
    """
    gh_csv = DATA_RAW / "github" / "github_candidates.csv"
    df = pd.read_csv(gh_csv, dtype=str)
    prominent = df[df["prominent_flag"] == "1"].copy()
    repos = prominent["repo_full_name"].dropna().unique().tolist()

    # Repo metadata for 'create' events
    repo_meta = {}
    for _, r in prominent.iterrows():
        repo_meta[r["repo_full_name"]] = {
            "owner": r.get("owner_login", ""),
            "created_at": r.get("created_at", ""),
        }

    out_path = DATA_RAW / "github" / "github_repo_participation_events.csv"
    done_repos = set()
    existing_rows = []
    if out_path.exists():
        ex = pd.read_csv(out_path, dtype=str)
        done_repos = set(ex["repo_full_name"].unique())
        existing_rows = ex.values.tolist()
        print(f"  Already processed: {len(done_repos)} repos (resuming)")

    todo = [r for r in repos if r not in done_repos]
    print(f"  Repos to process: {len(todo)}")
    if not todo:
        print("  All repos already processed.")
        return

    rows = list(existing_rows)
    total_api_calls = [0]
    start_time = time.time()

    for i, repo in enumerate(todo, 1):
        # --- Create event (from CSV, no API call) ---
        meta = repo_meta.get(repo, {})
        actor_events = {}  # login → (date, type)
        owner = meta.get("owner", "")
        created = meta.get("created_at", "")
        if owner and created:
            actor_events[owner] = (created, "create")

        # --- Commits (serial, rate-limited) ---
        commit_authors = _fetch_repo_commits(repo)
        for login, date in commit_authors.items():
            if login not in actor_events or date < actor_events[login][0]:
                actor_events[login] = (date, "commit")

        # --- PRs (serial, rate-limited) ---
        pr_authors = _fetch_repo_prs(repo)
        for login, date in pr_authors.items():
            if login not in actor_events or date < actor_events[login][0]:
                actor_events[login] = (date, "pr_opened")

        # --- Append rows ---
        for login, (date, etype) in actor_events.items():
            rows.append([repo, login, date, etype])

        # --- Progress & checkpoint ---
        if i % CHECKPOINT_EVERY == 0 or i == len(todo):
            elapsed = time.time() - start_time
            rate = i / elapsed * 3600 if elapsed > 0 else 0
            eta_h = (len(todo) - i) / rate if rate > 0 else 0
            print(f"  [{i}/{len(todo)}] {repo}: "
                  f"{len(commit_authors)} commit authors, "
                  f"{len(pr_authors)} PR authors  "
                  f"({rate:.0f} repos/hr, ETA {eta_h:.1f}h)")
            _save_events(rows, out_path)

    _save_events(rows, out_path)
    total_actors = len(rows)
    print(f"\n✅ Participation events: {total_actors} rows "
          f"across {len(done_repos) + len(todo)} repos")


# ──────────────────────────────── Main ───────────────────────────────────────

def main():
    print("=" * 60)
    print("Step 4: Fetch contributors & their locations")
    print("=" * 60)

    if not GITHUB_TOKEN:
        print("⚠️  GITHUB_TOKEN not set. Will be heavily rate-limited.\n"
              "   export GITHUB_TOKEN='ghp_…' before running.")

    # Part A: get contributor lists for all prominent repos
    all_logins = collect_all_contributors()

    # Part B: fetch locations for new contributors
    fetch_missing_locations(all_logins)

    # Part C: build participation chain (Commits + PRs)
    print("\n" + "-" * 60)
    print("Part C: Building participation chain (Commits API + PRs API)")
    print("-" * 60)
    collect_participation_events()

    print("\n" + "=" * 60)
    print("Step 4 complete. Ready for step 5 (build core tables).")
    print("=" * 60)


if __name__ == "__main__":
    main()
