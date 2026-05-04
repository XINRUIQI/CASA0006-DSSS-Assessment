"""
Step 3a – Fetch location info for GitHub users/orgs that own prominent repos.

For each unique owner_login in the prominent GitHub projects, call the
GitHub Users API to retrieve the `location` field.

Output: data/raw/github/github_owner_locations.csv
"""

import csv
import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import GITHUB_TOKEN, DATA_RAW, DATA_PROCESSED

HEADERS = {"Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


def _wait_for_rate_limit(resp):
    remaining = int(resp.headers.get("X-RateLimit-Remaining", 1))
    if remaining < 5:
        reset_ts = int(resp.headers.get("X-RateLimit-Reset", 0))
        sleep_sec = max(reset_ts - int(time.time()), 1) + 2
        print(f"  ⏳ Rate-limited ({remaining} left). Sleeping {sleep_sec}s …")
        time.sleep(sleep_sec)


def fetch_user_location(login, owner_type):
    """Fetch location from /users/{login} or /orgs/{login}."""
    if owner_type == "Organization":
        url = f"https://api.github.com/orgs/{login}"
    else:
        url = f"https://api.github.com/users/{login}"

    resp = requests.get(url, headers=HEADERS)
    _wait_for_rate_limit(resp)

    if resp.status_code == 404:
        return {"login": login, "location": "", "name": "", "company": "",
                "bio": "", "type": owner_type, "status": "not_found"}
    if resp.status_code != 200:
        time.sleep(5)
        return {"login": login, "location": "", "name": "", "company": "",
                "bio": "", "type": owner_type, "status": f"http_{resp.status_code}"}

    data = resp.json()
    return {
        "login": login,
        "location": data.get("location") or "",
        "name": data.get("name") or "",
        "company": data.get("company") or "",
        "bio": (data.get("bio") or "")[:200],
        "type": data.get("type") or owner_type,
        "status": "ok",
    }


def main():
    print("=" * 60)
    print("Step 3a: Fetch GitHub owner locations")
    print("=" * 60)

    if not GITHUB_TOKEN:
        print("⚠️  GITHUB_TOKEN not set. Will be heavily rate-limited.")

    gh_csv = DATA_RAW / "github" / "github_candidates.csv"
    df = pd.read_csv(gh_csv, dtype=str)
    prominent = df[df["prominent_flag"] == "1"]
    owners = prominent[["owner_login", "owner_type"]].drop_duplicates()
    print(f"  Prominent repos: {len(prominent)}")
    print(f"  Unique owners:   {len(owners)}")

    # Resume support: skip already-fetched logins
    out_path = DATA_RAW / "github" / "github_owner_locations.csv"
    done_logins = set()
    existing_rows = []
    if out_path.exists():
        existing = pd.read_csv(out_path, dtype=str)
        done_logins = set(existing["login"].tolist())
        existing_rows = existing.to_dict("records")
        print(f"  Already fetched:  {len(done_logins)} (will resume)")

    rows = list(existing_rows)
    todo = [(r["owner_login"], r["owner_type"])
            for _, r in owners.iterrows() if r["owner_login"] not in done_logins]
    total = len(todo)
    print(f"  Remaining to fetch: {total}\n")

    for i, (login, otype) in enumerate(todo, 1):
        result = fetch_user_location(login, otype)
        rows.append(result)

        if i % 100 == 0 or i == total:
            print(f"  [{i}/{total}] fetched — last: {login} → "
                  f"'{result['location'][:40]}'")
            # Checkpoint save every 500
            if i % 500 == 0 or i == total:
                _save(rows, out_path)

        time.sleep(0.8)  # ~72 req/min, well under 5000/hr limit

    _save(rows, out_path)

    # Summary
    locs = [r for r in rows if r["location"].strip()]
    print(f"\n📊 Summary: {len(rows)} owners fetched")
    print(f"   With location: {len(locs)} ({100*len(locs)/max(len(rows),1):.1f}%)")
    print(f"   Without location: {len(rows) - len(locs)}")


def _save(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["login", "location", "name", "company", "bio", "type", "status"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
