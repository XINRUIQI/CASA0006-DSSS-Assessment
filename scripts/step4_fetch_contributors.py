"""
Step 4 – Fetch contributor lists for prominent GitHub repos.

For each prominent repo, call  GET /repos/{owner}/{repo}/contributors
to obtain:
  - contributor login
  - contribution count

Then fetch each new contributor's location (if not already in our
owner_locations file).

Outputs
-------
data/raw/github/github_repo_contributors.csv
    repo_full_name, contributor_login, contributions

data/raw/github/github_owner_locations.csv   (appended with new users)

Supports resume: skips repos / users already fetched.
"""

import csv
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import GITHUB_TOKEN, DATA_RAW

HEADERS = {"Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

SESSION = requests.Session()
retry_strategy = Retry(
    total=5,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)
SESSION.mount("https://", HTTPAdapter(max_retries=retry_strategy))
SESSION.headers.update(HEADERS)

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
    for attempt in range(max_retries):
        try:
            return SESSION.get(url, params=params, timeout=30)
        except (requests.ConnectionError, requests.Timeout) as exc:
            wait = min(2 ** (attempt + 1), 120)
            print(f"  ⚠️  Connection error (attempt {attempt+1}/{max_retries}): {exc!r}")
            print(f"      Retrying in {wait}s …")
            time.sleep(wait)
    return SESSION.get(url, params=params, timeout=30)


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
    for i, login in enumerate(todo, 1):
        result = fetch_user_location(login)
        rows.append(result)

        if i % 200 == 0 or i == len(todo):
            print(f"  [{i}/{len(todo)}] last: {login} → '{result['location'][:40]}'")
            # Checkpoint save
            with open(loc_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=fieldnames)
                w.writeheader()
                w.writerows(rows)

        time.sleep(0.7)

    locs = [r for r in rows if r["location"].strip()]
    print(f"\n✅ Locations: {len(rows)} total, {len(locs)} with location")


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

    print("\n" + "=" * 60)
    print("Step 4 complete. Ready for step 5 (build core tables).")
    print("=" * 60)


if __name__ == "__main__":
    main()
