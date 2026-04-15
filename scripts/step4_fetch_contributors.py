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
        except (requests.ConnectionError, requests.Timeout,
                requests.exceptions.ChunkedEncodingError) as exc:
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
CHECKPOINT_EVERY = 10   # save progress every N repos
LOG_EVERY = 50          # print detailed log every N repos


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


def _build_target_repo_set():
    """
    Pre-filter: find repos that have at least one contributor in a
    target city.  Repos with no target-city contributor are skipped
    to save ~30% of API calls.  Pure local computation.
    """
    from step3b_clean_and_map_locations import (
        _build_city_dict, clean_location, match_city,
    )
    from config import DATA_PROCESSED

    contrib_path = DATA_RAW / "github" / "github_repo_contributors.csv"
    loc_path = DATA_RAW / "github" / "github_owner_locations.csv"
    city_path = DATA_PROCESSED / "city_list.csv"

    if not all(p.exists() for p in [contrib_path, loc_path, city_path]):
        return None  # can't filter, process all

    cities = pd.read_csv(city_path, dtype=str)
    city_set = set(cities["matched_city"].str.strip().tolist())

    loc = pd.read_csv(loc_path, dtype=str).fillna("")
    _build_city_dict()
    user_city = set()
    for _, row in loc.iterrows():
        raw = row["location"]
        if not raw.strip():
            continue
        cleaned = clean_location(raw)
        if cleaned is None:
            continue
        result = match_city(cleaned)
        if result and result[0] in city_set:
            user_city.add(row["login"])

    contrib = pd.read_csv(contrib_path, dtype=str)
    relevant = contrib[contrib["contributor_login"].isin(user_city)]
    target_repos = set(relevant["repo_full_name"].unique())

    # Also include repos whose OWNER is in a target city
    gh = pd.read_csv(DATA_RAW / "github" / "github_candidates.csv", dtype=str)
    prom = gh[gh["prominent_flag"] == "1"]
    owner_repos = prom[prom["owner_login"].isin(user_city)]["repo_full_name"]
    target_repos.update(owner_repos.tolist())

    return target_repos


def collect_participation_events(shard_id=None, shard_total=None):
    """
    For each prominent repo, build a participation chain:
      1. 'create' event from candidates CSV (owner + created_at)
      2. 'commit' events from Commits API (each author's first commit)
      3. 'pr_opened' events from PRs API (each author's first PR)

    For each (repo, actor), only the earliest event is kept.

    Optimizations:
      - Pre-filter to repos with target-city contributors (~30% fewer calls)
      - Sharding: split work across multiple processes (--shard N/M)
      - Checkpoint every CHECKPOINT_EVERY repos
      - Graceful KeyboardInterrupt handling (saves before exit)
    """
    gh_csv = DATA_RAW / "github" / "github_candidates.csv"
    df = pd.read_csv(gh_csv, dtype=str)
    prominent = df[df["prominent_flag"] == "1"].copy()
    all_repos = prominent["repo_full_name"].dropna().unique().tolist()

    # Pre-filter: only repos with target-city contributors
    print("  Pre-filtering repos with target-city contributors …")
    target_repos = _build_target_repo_set()
    if target_repos is not None:
        repos = [r for r in all_repos if r in target_repos]
        skipped = len(all_repos) - len(repos)
        print(f"  Target-city repos: {len(repos)} "
              f"(skipping {skipped} repos with no target-city contributors)")
    else:
        repos = all_repos
        print(f"  Could not pre-filter, processing all {len(repos)} repos")

    # Apply sharding: each shard takes a deterministic slice
    if shard_id is not None and shard_total is not None:
        repos = [r for i, r in enumerate(repos) if i % shard_total == (shard_id - 1)]
        print(f"  Shard {shard_id}/{shard_total}: {len(repos)} repos assigned")

    # Repo metadata for 'create' events
    repo_meta = {}
    for _, r in prominent.iterrows():
        repo_meta[r["repo_full_name"]] = {
            "owner": r.get("owner_login", ""),
            "created_at": r.get("created_at", ""),
        }

    # Shard-specific or default output path
    if shard_id is not None:
        out_path = (DATA_RAW / "github" /
                    f"github_repo_participation_events_s{shard_id}.csv")
    else:
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
    start_time = time.time()
    interrupted = False

    try:
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

            # --- Checkpoint (frequent saves to minimize data loss) ---
            if i % CHECKPOINT_EVERY == 0 or i == len(todo):
                _save_events(rows, out_path)

            # --- Progress log ---
            if i % LOG_EVERY == 0 or i == len(todo):
                elapsed = time.time() - start_time
                rate = i / elapsed * 3600 if elapsed > 0 else 0
                eta_h = (len(todo) - i) / rate if rate > 0 else 0
                print(f"  [{i}/{len(todo)}] {repo}: "
                      f"{len(commit_authors)} commits, "
                      f"{len(pr_authors)} PRs  "
                      f"({rate:.0f} repos/hr, ETA {eta_h:.1f}h)")

    except KeyboardInterrupt:
        interrupted = True
        print(f"\n  ⚠️  Interrupted! Saving progress ({i}/{len(todo)} done) …")
        _save_events(rows, out_path)
        print(f"  ✅ Progress saved. Re-run to resume from repo #{i}.")

    if not interrupted:
        total_actors = len(rows)
        print(f"\n✅ Participation events: {total_actors} rows "
              f"across {len(done_repos) + len(todo)} repos")


# ──────────────────────────────── Shard merge ────────────────────────────────

def merge_shard_files():
    """Merge shard CSVs into the final participation_events file."""
    import glob as globmod
    pattern = str(DATA_RAW / "github" / "github_repo_participation_events_s*.csv")
    shard_files = sorted(globmod.glob(pattern))
    if not shard_files:
        print("  No shard files found.")
        return

    out_path = DATA_RAW / "github" / "github_repo_participation_events.csv"
    all_rows = []
    seen = set()
    for f in shard_files:
        df = pd.read_csv(f, dtype=str)
        for _, row in df.iterrows():
            key = (row["repo_full_name"], row["actor_login"])
            if key not in seen:
                seen.add(key)
                all_rows.append(row.tolist())
        print(f"  Loaded {len(df)} rows from {Path(f).name}")

    _save_events(all_rows, out_path)
    print(f"\n✅ Merged {len(all_rows)} rows → "
          f"github_repo_participation_events.csv")


# ──────────────────────────────── Main ───────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Step 4: Fetch contributors")
    parser.add_argument(
        "--shard", type=str, default=None, metavar="N/M",
        help="Run only shard N of M (e.g. --shard 1/2). "
             "Each shard writes its own file. Use --merge after all shards finish.")
    parser.add_argument(
        "--merge", action="store_true",
        help="Merge shard files into final participation_events.csv")
    parser.add_argument(
        "--part-c-only", action="store_true",
        help="Skip Part A/B, only run Part C (participation chain)")
    args = parser.parse_args()

    # Parse shard spec
    shard_id, shard_total = None, None
    if args.shard:
        try:
            n, m = args.shard.split("/")
            shard_id, shard_total = int(n), int(m)
            assert 1 <= shard_id <= shard_total
        except (ValueError, AssertionError):
            print("❌ --shard must be N/M where 1 ≤ N ≤ M, e.g. --shard 1/2")
            sys.exit(1)

    # Merge mode
    if args.merge:
        print("=" * 60)
        print("Merging shard files")
        print("=" * 60)
        merge_shard_files()
        return

    print("=" * 60)
    if shard_id:
        print(f"Step 4: Shard {shard_id}/{shard_total}")
    else:
        print("Step 4: Fetch contributors & their locations")
    print("=" * 60)

    if not GITHUB_TOKEN:
        print("⚠️  GITHUB_TOKEN not set. Will be heavily rate-limited.\n"
              "   export GITHUB_TOKEN='ghp_…' before running.")

    if not args.part_c_only:
        # Part A: get contributor lists for all prominent repos
        all_logins = collect_all_contributors()

        # Part B: fetch locations for new contributors
        fetch_missing_locations(all_logins)
    else:
        print("  Skipping Part A/B (--part-c-only)")

    # Part C: build participation chain (Commits + PRs)
    print("\n" + "-" * 60)
    print("Part C: Building participation chain (Commits API + PRs API)")
    if shard_id:
        print(f"         Shard {shard_id} of {shard_total}")
    print("-" * 60)
    collect_participation_events(shard_id=shard_id, shard_total=shard_total)

    print("\n" + "=" * 60)
    if shard_id:
        print(f"Shard {shard_id}/{shard_total} complete.")
        if shard_total > 1:
            print("After ALL shards finish, run:  python step4_fetch_contributors.py --merge")
    else:
        print("Step 4 complete. Ready for step 5 (build core tables).")
    print("=" * 60)


if __name__ == "__main__":
    main()
