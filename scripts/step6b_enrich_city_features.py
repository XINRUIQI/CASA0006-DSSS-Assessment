"""
Step 6b – Enrich city_attributes.csv with pre-computed analytic features.

Adds columns consumed by downstream analysis (§9.1 K-means, §10.1 regression),
following the same pattern as road_safety_london_final: multi-source aggregations
are computed here (offline script) so the analysis notebook only reads columns and
applies simple log/z-score transforms.

New columns
-----------
  Temporal lag distribution:
    lag_std          — std dev of adoption lag across ALL events per city
    avg_lag_nonorig  — mean lag restricted to non-originator events (§10.1 DV)

  Geographic collaboration reach:
    cross_region_ratio_calc — share of collaboration weight that crosses macro-regions

  Project quality / engagement (from prominent_projects_master.csv):
    pop_top25_share     — mean share of adopted projects in top-25% popularity
    orig_top25_share    — Bayesian-smoothed share of originated projects in top-25%
    lag_quality_corr    — per-city correlation between adoption lag and popularity pctile
    avg_fork_star_ratio — mean fork/star ratio of GitHub projects engaged with

Prerequisites
-------------
  data/output/city_attributes.csv              (from step5 + step6)
  data/output/city_project_adoption_events.csv
  data/output/city_collaboration_edges.csv
  data/processed/prominent_projects_master.csv

Output
------
  Overwrites data/output/city_attributes.csv with 7 new columns appended.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DATA_OUTPUT, DATA_PROCESSED


def main():
    print("=" * 60)
    print("Step 6b: Enrich city_attributes with analytic features")
    print("=" * 60)

    # ── Load inputs ───────────────────────────────────────────────────────
    attr_path = DATA_OUTPUT / "city_attributes.csv"
    df       = pd.read_csv(attr_path)
    adoption = pd.read_csv(DATA_OUTPUT / "city_project_adoption_events.csv")
    edges    = pd.read_csv(DATA_OUTPUT / "city_collaboration_edges.csv")

    print(f"  Loaded {len(df)} cities, {len(adoption)} adoption events, "
          f"{len(edges)} collaboration edges")

    # Drop any columns that might already exist from a prior run
    existing_new = ["lag_std", "avg_lag_nonorig", "cross_region_ratio_calc",
                    "pop_top25_share", "orig_top25_share",
                    "lag_quality_corr", "avg_fork_star_ratio"]
    df = df.drop(columns=[c for c in existing_new if c in df.columns])

    # ── A. Temporal lag features ──────────────────────────────────────────
    # lag_std: std dev of lag across all adoption events per city
    lag_std = adoption.groupby("city")["lag"].std().rename("lag_std")
    df = df.merge(lag_std, left_on="city", right_index=True, how="left")

    # avg_lag_nonorig: mean lag of non-originator events only (used in §10.1)
    nonorig = adoption[adoption["is_originator"] == 0]
    avg_lag_nonorig = (nonorig.groupby("city")["lag"]
                              .mean()
                              .rename("avg_lag_nonorig"))
    df = df.merge(avg_lag_nonorig, left_on="city", right_index=True, how="left")
    print("  ✓ lag_std, avg_lag_nonorig")

    # ── B. Cross-region collaboration ratio ───────────────────────────────
    # Fraction of each city's total edge weight directed to a different macro-region
    city_region = df.set_index("city")["region"].to_dict()
    e = edges.copy()
    e["src_region"] = e["source_city"].map(city_region)
    e["tgt_region"] = e["target_city"].map(city_region)
    e["is_cross"]   = (e["src_region"] != e["tgt_region"]).astype(int)

    cr_src = (e[e["is_cross"] == 1]
              .groupby("source_city")["edge_weight"].sum())
    cr_tgt = (e[e["is_cross"] == 1]
              .groupby("target_city")["edge_weight"].sum())
    t_src  = e.groupby("source_city")["edge_weight"].sum()
    t_tgt  = e.groupby("target_city")["edge_weight"].sum()

    cross_ratio = (
        cr_src.add(cr_tgt, fill_value=0)
        / t_src.add(t_tgt, fill_value=0)
    ).rename("cross_region_ratio_calc")

    df = df.merge(cross_ratio, left_on="city", right_index=True, how="left")
    df["cross_region_ratio_calc"] = df["cross_region_ratio_calc"].fillna(0)
    print("  ✓ cross_region_ratio_calc")

    # ── C. Project quality / engagement features ──────────────────────────
    master_path = DATA_PROCESSED / "prominent_projects_master.csv"
    if not master_path.exists():
        print("  ⚠️  prominent_projects_master.csv not found – skipping quality features")
        for col in ["pop_top25_share", "orig_top25_share",
                    "lag_quality_corr", "avg_fork_star_ratio"]:
            df[col] = np.nan
    else:
        master = pd.read_csv(master_path, dtype=str)
        master["metric_stars"]     = pd.to_numeric(master["metric_stars"],     errors="coerce")
        master["metric_forks"]     = pd.to_numeric(master["metric_forks"],     errors="coerce")
        master["metric_downloads"] = pd.to_numeric(master["metric_downloads"], errors="coerce")

        gh = master[master["platform"] == "GitHub"].copy()
        hf = master[master["platform"] == "HuggingFace"].copy()
        gh["popularity_pctile"] = gh["metric_stars"].rank(pct=True)
        hf["popularity_pctile"] = hf["metric_downloads"].rank(pct=True)
        gh["fork_star_ratio"]   = (gh["metric_forks"]
                                   / gh["metric_stars"].replace(0, np.nan))

        metrics = pd.concat([
            gh[["full_id", "platform", "popularity_pctile", "fork_star_ratio"]],
            hf[["full_id", "platform", "popularity_pctile"]],
        ])

        adopt_m = adoption.merge(
            metrics, left_on="project_id", right_on="full_id", how="left"
        )
        am = adopt_m[adopt_m["popularity_pctile"].notna()].copy()
        am["is_top25"] = (am["popularity_pctile"] >= 0.75).astype(int)

        # C1: pop_top25_share — share of adopted projects that are top-25% by popularity
        pop_top25 = am.groupby("city")["is_top25"].mean().rename("pop_top25_share")
        df = df.merge(pop_top25, left_on="city", right_index=True, how="left")
        df["pop_top25_share"] = df["pop_top25_share"].fillna(
            df["pop_top25_share"].median()
        )

        # C2: orig_top25_share — Bayesian-smoothed share of originated top-25% projects
        orig = am[am["is_originator"] == 1]
        orig_top25_raw    = orig.groupby("city")["is_top25"].mean()
        orig_n            = orig.groupby("city").size()
        global_orig_top25 = float(orig["is_top25"].mean()) if len(orig) > 0 else 0.0
        smooth = pd.DataFrame({"raw": orig_top25_raw, "n": orig_n})
        smooth["orig_top25_share"] = (
            (smooth["raw"] * smooth["n"] + global_orig_top25 * 5)
            / (smooth["n"] + 5)
        )
        df = df.merge(
            smooth[["orig_top25_share"]],
            left_on="city", right_index=True, how="left"
        )
        df["orig_top25_share"] = df["orig_top25_share"].fillna(global_orig_top25)

        # C3: lag_quality_corr — correlation between adoption lag and project popularity
        def _lag_quality_corr(group):
            if len(group) < 5:
                return np.nan
            return group["lag"].corr(group["popularity_pctile"])

        lqc = (am[["city", "lag", "popularity_pctile"]]
                 .groupby("city")
                 .apply(_lag_quality_corr)
                 .rename("lag_quality_corr"))
        df = df.merge(lqc, left_on="city", right_index=True, how="left")
        df["lag_quality_corr"] = df["lag_quality_corr"].fillna(
            df["lag_quality_corr"].median()
        )

        # C4: avg_fork_star_ratio — mean fork/star ratio of GitHub projects
        gh_am = am[am["platform"] == "GitHub"]
        fsr   = (gh_am.groupby("city")["fork_star_ratio"]
                      .mean()
                      .rename("avg_fork_star_ratio"))
        df = df.merge(fsr, left_on="city", right_index=True, how="left")
        df["avg_fork_star_ratio"] = df["avg_fork_star_ratio"].fillna(
            df["avg_fork_star_ratio"].median()
        )
        print("  ✓ pop_top25_share, orig_top25_share, lag_quality_corr, avg_fork_star_ratio")

    # ── Save ──────────────────────────────────────────────────────────────
    df.to_csv(attr_path, index=False)
    print(f"\n✅ Updated city_attributes → {attr_path}")
    print(f"   {len(df)} cities × {len(df.columns)} columns")

    new_cols = ["lag_std", "avg_lag_nonorig", "cross_region_ratio_calc",
                "pop_top25_share", "orig_top25_share",
                "lag_quality_corr", "avg_fork_star_ratio"]
    print(f"\n  New columns summary:")
    print(df[new_cols].describe().round(4).to_string())


if __name__ == "__main__":
    main()
