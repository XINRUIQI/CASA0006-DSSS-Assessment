"""
Step 5b – Parse the Hugging Face derivation graph from the local
`tags` field that step1b stored on every HF candidate.

Background
----------
HF model cards encode parent-of-derivation relations as tags such as
    base_model:<owner>/<name>
    base_model:finetune:<owner>/<name>
    base_model:quantized:<owner>/<name>
    base_model:adapter:<owner>/<name>
    base_model:merge:<owner>/<name>

We restrict to:
  * descendants whose project_id is in `prominent_projects_master.csv`
    (any HF type, but only `model` carries base_model in practice);
  * ancestors whose project_id is also in the prominent set
    (so the resulting adoption events live within our analysis frame).

Outputs
-------
data/processed/hf_derivation_edges.csv
    descendant_id, ancestor_id, relation,
    descendant_project_id, ancestor_project_id,
    descendant_author, ancestor_author,
    descendant_created_month, ancestor_created_month, lag_months
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Optional

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DATA_PROCESSED

MASTER = DATA_PROCESSED / "prominent_projects_master.csv"
OUT = DATA_PROCESSED / "hf_derivation_edges.csv"

REL_PATTERN = re.compile(
    r"^base_model:(?:(finetune|quantized|adapter|merge):)?(.+)$",
    re.IGNORECASE,
)


def _parse_base_model_tags(tag_str: str):
    """Return list of (relation, parent_full_id) parsed from stored tags."""
    if not tag_str or pd.isna(tag_str):
        return []
    out = []
    for t in str(tag_str).split("|"):
        t = t.strip()
        m = REL_PATTERN.match(t)
        if m:
            rel = (m.group(1) or "generic").lower()
            parent = m.group(2).strip()
            if "/" in parent:
                out.append((rel, parent))
    return out


def _to_month(ts) -> Optional[int]:
    if not ts or pd.isna(ts):
        return None
    s = str(ts).strip()
    try:
        return int(s[:4]) * 100 + int(s[5:7])
    except (ValueError, IndexError):
        return None


def _month_diff(m_old: int, m_new: int) -> int:
    y1, mo1 = divmod(m_old, 100)
    y2, mo2 = divmod(m_new, 100)
    return (y2 - y1) * 12 + (mo2 - mo1)


def main():
    print("=" * 64)
    print("Step 5b: Parse HF derivation graph from local tags")
    print("=" * 64)

    if not MASTER.exists():
        print(f"❌ Missing {MASTER}. Run step1c first.")
        return

    df = pd.read_csv(MASTER, dtype=str)
    hf = df[df["platform"] == "HuggingFace"].copy()
    print(f"  HF prominent rows: {len(hf)}")

    # Build a lookup: full_id -> (project_id, author, created_month)
    info = {}
    for _, row in hf.iterrows():
        fid = row["full_id"]
        if not fid:
            continue
        info[fid] = {
            "project_id": row["project_id"],
            "author": fid.split("/")[0] if "/" in fid else "",
            "created_month": _to_month(row.get("created_at")),
        }
    print(f"  Lookup index size: {len(info)}")

    # Iterate over all HF rows, parse tags, keep edges where ancestor is in
    # the prominent set as well.
    rel_counter = defaultdict(int)
    keep_edges = []   # list of dict
    seen_pairs = set()  # de-duplicate (descendant_id, ancestor_id)

    for _, row in hf.iterrows():
        child = row["full_id"]
        if not child or child not in info:
            continue
        rels = _parse_base_model_tags(row["tags"])
        if not rels:
            continue

        # Resolve duplicate parents (generic + typed for the same parent):
        # keep the typed relation when present.
        seen_parents = {}
        for rel, parent in rels:
            if parent not in seen_parents or seen_parents[parent] == "generic":
                seen_parents[parent] = rel

        c_info = info[child]
        for parent, rel in seen_parents.items():
            rel_counter[rel] += 1
            if parent not in info:
                continue   # ancestor not in prominent set → skip
            if (child, parent) in seen_pairs:
                continue
            seen_pairs.add((child, parent))

            p_info = info[parent]
            d_month = c_info["created_month"]
            a_month = p_info["created_month"]
            lag = (_month_diff(a_month, d_month)
                   if (a_month is not None and d_month is not None) else None)

            keep_edges.append({
                "descendant_id": child,
                "ancestor_id": parent,
                "relation": rel,
                "descendant_project_id": c_info["project_id"],
                "ancestor_project_id": p_info["project_id"],
                "descendant_author": c_info["author"],
                "ancestor_author": p_info["author"],
                "descendant_created_month": d_month,
                "ancestor_created_month": a_month,
                "lag_months": lag,
            })

    edges_df = pd.DataFrame(keep_edges)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    edges_df.to_csv(OUT, index=False)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n  Raw base_model edges parsed (any relation): "
          f"{sum(rel_counter.values())}")
    for r, n in sorted(rel_counter.items(), key=lambda x: -x[1]):
        print(f"    {r:10s}: {n}")

    print(f"\n  Edges retained (both ends prominent): {len(edges_df)}")
    if len(edges_df) > 0:
        n_descendants = edges_df["descendant_id"].nunique()
        n_ancestors = edges_df["ancestor_id"].nunique()
        print(f"    distinct descendants: {n_descendants}")
        print(f"    distinct ancestors  : {n_ancestors}")
        print(f"    lag months distribution:")
        print(edges_df["lag_months"].describe().to_string())
        print(f"\n    relation breakdown (kept edges):")
        print(edges_df["relation"].value_counts().to_string())
        print(f"\n    top-10 ancestors by in-degree:")
        top = (edges_df.groupby("ancestor_id").size()
               .sort_values(ascending=False).head(10))
        print(top.to_string())

    print(f"\n✅ Saved → {OUT}")


if __name__ == "__main__":
    main()
