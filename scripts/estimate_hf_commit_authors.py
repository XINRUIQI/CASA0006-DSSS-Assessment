"""
Estimate the share of HF prominent projects that have:
  - single-author commit history (only the original author commits)
  - multi-author commit history (real collaboration signal)

Strategy
--------
Stratified random sample over HF prominent projects from
`data/processed/prominent_projects_master.csv`:
  - 3 strata by hf_type (model / dataset / space)
  - within each stratum, 3 popularity tiers by likes (low / mid / high)
  - sample N items per (type, tier) cell

For each sampled project, call HfApi().list_repo_commits and count
unique commit authors (excluding obvious bots).

Outputs a printed summary table; saves per-project results to
`data/raw/huggingface/hf_commit_author_sample.csv` for inspection.
"""

import os
import sys
import time
import random
import csv
from pathlib import Path
from collections import Counter, defaultdict

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from huggingface_hub import HfApi
from huggingface_hub.utils import HfHubHTTPError

MASTER = ROOT / "data" / "processed" / "prominent_projects_master.csv"
OUT = ROOT / "data" / "raw" / "huggingface" / "hf_commit_author_sample.csv"

PER_CELL = 25  # items per (hf_type x popularity tier)
SEED = 20260419

BOT_PATTERNS = (
    "-bot",
    "bot-",
    "librarian-bot",
    "system",
    "actions-user",
    "huggingface-bot",
)


def is_bot(name: str) -> bool:
    if not name:
        return True
    n = name.lower()
    return any(p in n for p in BOT_PATTERNS)


def stratified_sample(df: pd.DataFrame) -> pd.DataFrame:
    rng = random.Random(SEED)
    df = df.copy()
    df["likes_num"] = pd.to_numeric(df["metric_likes"], errors="coerce").fillna(0)

    chosen = []
    for hf_type in ["model", "dataset", "space"]:
        sub = df[df["hf_type"] == hf_type]
        if len(sub) == 0:
            continue
        # tiers by likes
        q1, q2 = sub["likes_num"].quantile([0.5, 0.9])
        tiers = {
            "low":  sub[sub["likes_num"] <= q1],
            "mid":  sub[(sub["likes_num"] > q1) & (sub["likes_num"] <= q2)],
            "high": sub[sub["likes_num"] > q2],
        }
        for tier_name, tier_df in tiers.items():
            if len(tier_df) == 0:
                continue
            n = min(PER_CELL, len(tier_df))
            picks = rng.sample(list(tier_df.index), n)
            for idx in picks:
                row = tier_df.loc[idx]
                chosen.append({
                    "project_id": row["project_id"],
                    "full_id": row["full_id"],
                    "hf_type": hf_type,
                    "tier": tier_name,
                    "likes": int(row["likes_num"]),
                })
    return pd.DataFrame(chosen)


def fetch_commit_authors(api: HfApi, full_id: str, hf_type: str):
    """Return (n_commits, unique_authors_excl_bots, unique_authors_incl_bots, error_str)."""
    try:
        commits = list(api.list_repo_commits(
            repo_id=full_id,
            repo_type=hf_type,
        ))
    except HfHubHTTPError as e:
        return (None, None, None, f"HTTP:{e.response.status_code if e.response else '?'}")
    except Exception as e:
        return (None, None, None, f"ERR:{type(e).__name__}")

    authors_all = set()
    authors_real = set()
    for c in commits:
        # GitCommitInfo has .authors (list[str])
        for a in (c.authors or []):
            if not a:
                continue
            authors_all.add(a)
            if not is_bot(a):
                authors_real.add(a)
    return (len(commits), len(authors_real), len(authors_all), "")


def main():
    print(f"Loading master: {MASTER}")
    df = pd.read_csv(MASTER, dtype=str)
    df = df[df["platform"] == "HuggingFace"]
    print(f"  HF prominent projects: {len(df)}")

    sample = stratified_sample(df)
    print(f"\nSample size: {len(sample)}")
    print(sample.groupby(["hf_type", "tier"]).size().unstack(fill_value=0))

    api = HfApi(token=os.getenv("HF_TOKEN") or None)

    rows = []
    t0 = time.time()
    for i, r in sample.iterrows():
        n_commits, n_real, n_all, err = fetch_commit_authors(
            api, r["full_id"], r["hf_type"]
        )
        rows.append({
            "full_id": r["full_id"],
            "hf_type": r["hf_type"],
            "tier": r["tier"],
            "likes": r["likes"],
            "n_commits": n_commits,
            "n_authors_real": n_real,
            "n_authors_all": n_all,
            "error": err,
        })
        if (i + 1) % 10 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            print(f"  [{i+1}/{len(sample)}] elapsed {elapsed:.0f}s rate {rate:.1f}/s")
        time.sleep(0.05)

    out_df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT, index=False)
    print(f"\nSaved sample → {OUT}")

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    ok = out_df[out_df["error"] == ""]
    print(f"Successful API calls: {len(ok)} / {len(out_df)}")
    if len(out_df) - len(ok) > 0:
        print("Errors:")
        print(out_df[out_df["error"] != ""]["error"].value_counts().to_string())

    if len(ok) == 0:
        return

    print("\n--- Distribution of unique non-bot commit authors per project ---")
    cnt = ok["n_authors_real"].value_counts().sort_index()
    print(cnt.to_string())

    print("\n--- Single-author vs multi-author share (overall) ---")
    single = (ok["n_authors_real"] <= 1).sum()
    multi = (ok["n_authors_real"] >= 2).sum()
    print(f"  single-author (≤1): {single} ({single/len(ok)*100:.1f}%)")
    print(f"  multi-author  (≥2): {multi} ({multi/len(ok)*100:.1f}%)")
    print(f"  multi (≥3):         {(ok['n_authors_real']>=3).sum()} ({(ok['n_authors_real']>=3).sum()/len(ok)*100:.1f}%)")
    print(f"  multi (≥5):         {(ok['n_authors_real']>=5).sum()} ({(ok['n_authors_real']>=5).sum()/len(ok)*100:.1f}%)")

    print("\n--- Breakdown by hf_type ---")
    for ht in ["model", "dataset", "space"]:
        sub = ok[ok["hf_type"] == ht]
        if len(sub) == 0:
            continue
        s = (sub["n_authors_real"] <= 1).sum()
        m = (sub["n_authors_real"] >= 2).sum()
        print(f"  {ht:8s} n={len(sub):3d}  single={s:3d} ({s/len(sub)*100:5.1f}%)  multi={m:3d} ({m/len(sub)*100:5.1f}%)  median_authors={sub['n_authors_real'].median():.1f}  mean={sub['n_authors_real'].mean():.2f}")

    print("\n--- Breakdown by popularity tier ---")
    for tier in ["low", "mid", "high"]:
        sub = ok[ok["tier"] == tier]
        if len(sub) == 0:
            continue
        s = (sub["n_authors_real"] <= 1).sum()
        m = (sub["n_authors_real"] >= 2).sum()
        print(f"  {tier:6s} n={len(sub):3d}  single={s:3d} ({s/len(sub)*100:5.1f}%)  multi={m:3d} ({m/len(sub)*100:5.1f}%)  median_authors={sub['n_authors_real'].median():.1f}")

    print("\n--- Top 10 most multi-author projects in sample ---")
    top = ok.sort_values("n_authors_real", ascending=False).head(10)
    print(top[["full_id", "hf_type", "tier", "likes", "n_commits", "n_authors_real"]].to_string(index=False))


if __name__ == "__main__":
    main()
