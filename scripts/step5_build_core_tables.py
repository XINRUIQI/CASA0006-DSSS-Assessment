"""
Step 5 – Build three core analysis tables from collected data.

Prerequisites
-------------
- data/raw/github/github_candidates.csv                    (from step 1a)
- data/raw/github/github_repo_contributors.csv             (from step 4)
- data/raw/github/github_repo_participation_events.csv     (from step 4, Part C)
- data/raw/github/github_owner_locations.csv               (from step 3a + step 4)
- data/processed/city_list.csv                             (from step 3d)

Outputs (all in data/output/)
-------
1. city_project_adoption_events.csv
2. city_collaboration_edges.csv
3. city_attributes.csv

Logic overview
--------------
- "adoption" = a contributor from city C participates in project P
  (the first month any contributor from C appears in P is the adoption month)
- "collaboration edge" = two cities share contributors on the same project
- "origination" = the city of the repo owner at creation time
- All timestamps are aggregated to YYYYMM monthly granularity.
- Participation events from Commits/PRs API (step 4 Part C) provide real
  first-event dates; created_month+1 approximation is used as fallback.
"""

import sys
import itertools
from pathlib import Path
from collections import defaultdict

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DATA_RAW, DATA_PROCESSED, DATA_OUTPUT

# We need the cleaning functions from step3b to map new contributors
from step3b_clean_and_map_locations import (
    _build_city_dict, clean_location, match_city, CITY_DICT
)


def _to_month(ts_str):
    """Convert ISO timestamp string to YYYYMM integer."""
    if not ts_str or pd.isna(ts_str):
        return None
    try:
        ts_str = str(ts_str).strip()
        return int(ts_str[:4]) * 100 + int(ts_str[5:7])
    except (ValueError, IndexError):
        return None


def load_data():
    """Load and prepare all required datasets."""
    print("  Loading data …")

    # 1. GitHub prominent repos
    gh = pd.read_csv(DATA_RAW / "github" / "github_candidates.csv", dtype=str)
    gh_prom = gh[gh["prominent_flag"] == "1"].copy()
    gh_prom["created_month"] = gh_prom["created_at"].apply(_to_month)
    print(f"    Prominent GitHub repos: {len(gh_prom)}")

    # 2. Contributors
    contrib_path = DATA_RAW / "github" / "github_repo_contributors.csv"
    if contrib_path.exists():
        contrib = pd.read_csv(contrib_path, dtype=str)
        print(f"    Contributor records: {len(contrib)}")
    else:
        print("    ⚠️  No contributor file found. Run step4 first.")
        contrib = pd.DataFrame(columns=["repo_full_name", "contributor_login", "contributions"])

    # 3. User locations
    loc_path = DATA_RAW / "github" / "github_owner_locations.csv"
    loc = pd.read_csv(loc_path, dtype=str).fillna("")
    print(f"    User location records: {len(loc)}")

    # 4. City list
    cities = pd.read_csv(DATA_PROCESSED / "city_list.csv", dtype=str)
    city_set = set(cities["matched_city"].str.strip().tolist())
    print(f"    Target cities: {len(city_set)}")

    # 5. Participation events (from step 4 Part C – Commits/PRs API)
    pe_path = DATA_RAW / "github" / "github_repo_participation_events.csv"
    if pe_path.exists():
        pe_df = pd.read_csv(pe_path, dtype=str)
        first_event_map = {}
        for _, row in pe_df.iterrows():
            m = _to_month(row.get("first_event_at", ""))
            if m:
                key = (row["repo_full_name"], row["actor_login"])
                if key not in first_event_map or m < first_event_map[key]:
                    first_event_map[key] = m
        print(f"    Participation events loaded: {len(first_event_map)}")
    else:
        first_event_map = {}
        print("    ⚠️  No participation events file found. "
              "Will use approximation for adoption lag.")

    return gh_prom, contrib, loc, cities, city_set, first_event_map


def build_user_city_map(loc_df, city_set):
    """Map login → city (only cities in our curated list)."""
    _build_city_dict()
    user_city = {}

    for _, row in loc_df.iterrows():
        login = row["login"]
        raw = row["location"]
        if not raw.strip():
            continue
        cleaned = clean_location(raw)
        if cleaned is None:
            continue
        result = match_city(cleaned)
        if result:
            city_name = result[0]
            if city_name in city_set:
                user_city[login] = city_name

    print(f"    Users mapped to target cities: {len(user_city)}")
    return user_city


# ═══════════════════════════════════════════════════════════════════════════════
# Table 1: city_project_adoption_events
# ═══════════════════════════════════════════════════════════════════════════════

def build_adoption_events(gh_prom, contrib, user_city, first_event_map):
    """
    For each (city, project) pair, determine:
      - whether the city is the originator (owner city at creation)
      - the first month a contributor from that city appeared
      - the adoption lag relative to global origin month

    Uses real participation event dates from Commits/PRs API when available;
    falls back to created_month / created_month+1 approximation otherwise.
    """
    print("\n  Building city_project_adoption_events …")

    repo_owner = dict(zip(gh_prom["repo_full_name"], gh_prom["owner_login"]))
    repo_created = dict(zip(gh_prom["repo_full_name"],
                            gh_prom["created_month"].astype("Int64")))

    city_project = defaultdict(dict)  # repo → {city: first_month}
    api_hits = 0
    api_misses = 0

    # Owner = originator
    for repo in gh_prom["repo_full_name"]:
        owner = repo_owner.get(repo, "")
        cm = repo_created.get(repo)
        if owner in user_city and cm and not pd.isna(cm):
            city = user_city[owner]
            real_month = first_event_map.get((repo, owner))
            city_project[repo][city] = real_month if real_month else int(cm)

    # Contributors
    for _, row in contrib.iterrows():
        repo = row["repo_full_name"]
        login = row["contributor_login"]
        if login not in user_city:
            continue
        if repo not in repo_created:
            continue
        city = user_city[login]
        cm = repo_created.get(repo)
        if cm is None or pd.isna(cm):
            continue
        cm = int(cm)

        real_month = first_event_map.get((repo, login))
        if real_month:
            contrib_month = real_month
            api_hits += 1
        else:
            contrib_month = cm if (login == repo_owner.get(repo)) else cm + 1
            if contrib_month % 100 > 12:
                contrib_month = (contrib_month // 100 + 1) * 100 + 1
            api_misses += 1

        if city not in city_project[repo] or contrib_month < city_project[repo][city]:
            city_project[repo][city] = contrib_month

    print(f"    Participation event hits: {api_hits}, "
          f"fallback approximations: {api_misses}")

    # --- Build event rows ---
    rows = []
    for repo, city_months in city_project.items():
        cm = repo_created.get(repo)
        if cm is None or pd.isna(cm):
            continue
        global_origin = int(cm)
        owner = repo_owner.get(repo, "")
        owner_city = user_city.get(owner, "")

        for city, first_month in city_months.items():
            lag = _month_diff(global_origin, first_month)
            rows.append({
                "city": city,
                "project_id": repo,
                "global_origin_month": global_origin,
                "city_first_adoption_month": first_month,
                "lag": lag,
                "is_originator": int(city == owner_city),
            })

    df = pd.DataFrame(rows)
    print(f"    Adoption events: {len(df)} rows "
          f"({df['city'].nunique()} cities, {df['project_id'].nunique()} projects)")
    return df


def _month_diff(m1, m2):
    """Number of months between YYYYMM integers."""
    y1, mo1 = divmod(m1, 100)
    y2, mo2 = divmod(m2, 100)
    return (y2 - y1) * 12 + (mo2 - mo1)


# ═══════════════════════════════════════════════════════════════════════════════
# Table 2: city_collaboration_edges
# ═══════════════════════════════════════════════════════════════════════════════

def build_collaboration_edges(gh_prom, contrib, user_city):
    """
    Two cities are connected if they share contributors on the same
    prominent project. Edge weight = number of shared projects.
    Also produce monthly snapshots for GraphSAGE.
    """
    print("\n  Building city_collaboration_edges …")

    repo_created = dict(zip(gh_prom["repo_full_name"],
                            gh_prom["created_month"].astype("Int64")))

    # For each repo, collect the set of cities involved
    repo_cities = defaultdict(set)

    # Owners
    repo_owner = dict(zip(gh_prom["repo_full_name"], gh_prom["owner_login"]))
    for repo, owner in repo_owner.items():
        if owner in user_city:
            repo_cities[repo].add(user_city[owner])

    # Contributors
    for _, row in contrib.iterrows():
        repo = row["repo_full_name"]
        login = row["contributor_login"]
        if login in user_city and repo in repo_created:
            repo_cities[repo].add(user_city[login])

    # Build edges: for each repo with ≥2 cities, create pairwise edges
    edge_counter = defaultdict(lambda: {"weight": 0, "shared_projects": 0,
                                         "months": set()})
    for repo, cities in repo_cities.items():
        if len(cities) < 2:
            continue
        cm = repo_created.get(repo)
        sorted_cities = sorted(cities)
        for c1, c2 in itertools.combinations(sorted_cities, 2):
            key = (c1, c2)
            edge_counter[key]["weight"] += 1
            edge_counter[key]["shared_projects"] += 1
            if cm and not pd.isna(cm):
                edge_counter[key]["months"].add(int(cm))

    # Flatten to rows (aggregate level: city pair)
    agg_rows = []
    for (c1, c2), info in edge_counter.items():
        agg_rows.append({
            "source_city": c1,
            "target_city": c2,
            "edge_weight": info["weight"],
            "shared_projects": info["shared_projects"],
        })

    df_agg = pd.DataFrame(agg_rows).sort_values("edge_weight", ascending=False)

    # Monthly edge table for GraphSAGE temporal splits
    monthly_rows = []
    for (c1, c2), info in edge_counter.items():
        for m in sorted(info["months"]):
            monthly_rows.append({
                "source_city": c1,
                "target_city": c2,
                "month": m,
                "edge_weight": 1,
            })

    df_monthly = pd.DataFrame(monthly_rows)

    print(f"    Aggregate edges: {len(df_agg)} city pairs")
    print(f"    Monthly edges:   {len(df_monthly)} rows")
    if len(df_agg) > 0:
        print(f"    Top 5 edges:")
        print(df_agg.head(5)[["source_city", "target_city", "edge_weight"]].to_string(index=False))

    return df_agg, df_monthly


# ═══════════════════════════════════════════════════════════════════════════════
# Table 3: city_attributes
# ═══════════════════════════════════════════════════════════════════════════════

def build_city_attributes(adoption_df, edges_agg_df, cities_df, gh_prom, user_city):
    """
    Aggregate city-level indicators:
      - origination_count / rate
      - adoption_count / rate
      - avg_adoption_lag
      - collaboration_count
      - degree, weighted_degree, betweenness (from edge table)
    """
    print("\n  Building city_attributes …")

    import networkx as nx

    city_list = cities_df[["matched_city", "country", "lat", "lon", "entity_count"]].copy()
    city_list = city_list.rename(columns={"matched_city": "city"})
    city_list["lat"] = pd.to_numeric(city_list["lat"], errors="coerce")
    city_list["lon"] = pd.to_numeric(city_list["lon"], errors="coerce")
    city_list["entity_count"] = pd.to_numeric(city_list["entity_count"], errors="coerce")

    # --- Innovation / origination ---
    if len(adoption_df) > 0:
        orig = adoption_df[adoption_df["is_originator"] == 1]
        orig_counts = orig.groupby("city").size().rename("origination_count")

        adopt_counts = adoption_df.groupby("city").agg(
            adoption_count=("project_id", "nunique"),
            avg_lag=("lag", "mean"),
            median_lag=("lag", "median"),
        )
    else:
        orig_counts = pd.Series(dtype=int, name="origination_count")
        adopt_counts = pd.DataFrame(columns=["adoption_count", "avg_lag", "median_lag"])

    city_list = city_list.merge(orig_counts, left_on="city", right_index=True, how="left")
    city_list = city_list.merge(adopt_counts, left_on="city", right_index=True, how="left")

    # --- Collaboration ---
    if len(edges_agg_df) > 0:
        collab_src = edges_agg_df.groupby("source_city")["edge_weight"].sum()
        collab_tgt = edges_agg_df.groupby("target_city")["edge_weight"].sum()
        collab_total = collab_src.add(collab_tgt, fill_value=0).rename("collaboration_count")
    else:
        collab_total = pd.Series(dtype=int, name="collaboration_count")

    city_list = city_list.merge(collab_total, left_on="city", right_index=True, how="left")

    # --- Network centrality ---
    if len(edges_agg_df) > 0:
        G = nx.Graph()
        for _, row in edges_agg_df.iterrows():
            G.add_edge(row["source_city"], row["target_city"],
                       weight=row["edge_weight"])

        degree = pd.Series(dict(G.degree(weight="weight")), name="weighted_degree")
        betweenness = pd.Series(nx.betweenness_centrality(G, weight="weight"),
                                name="betweenness")
        try:
            eigenvector = pd.Series(
                nx.eigenvector_centrality(G, weight="weight", max_iter=500),
                name="eigenvector_centrality")
        except nx.PowerIterationFailedConvergence:
            eigenvector = pd.Series(dtype=float, name="eigenvector_centrality")
    else:
        degree = pd.Series(dtype=float, name="weighted_degree")
        betweenness = pd.Series(dtype=float, name="betweenness")
        eigenvector = pd.Series(dtype=float, name="eigenvector_centrality")

    city_list = city_list.merge(degree, left_on="city", right_index=True, how="left")
    city_list = city_list.merge(betweenness, left_on="city", right_index=True, how="left")
    city_list = city_list.merge(eigenvector, left_on="city", right_index=True, how="left")

    # --- Per-capita rates ---
    pop = city_list["entity_count"].replace(0, np.nan)
    city_list["origination_rate"] = city_list["origination_count"] / pop
    city_list["adoption_rate"] = city_list["adoption_count"] / pop

    # Fill NaN
    fill_zero = ["origination_count", "adoption_count", "collaboration_count",
                 "weighted_degree", "betweenness", "eigenvector_centrality",
                 "origination_rate", "adoption_rate"]
    for col in fill_zero:
        if col in city_list.columns:
            city_list[col] = city_list[col].fillna(0)

    city_list["avg_lag"] = city_list["avg_lag"].round(2)
    city_list["median_lag"] = city_list["median_lag"].round(1)

    # Reorder columns
    col_order = [
        "city", "country", "lat", "lon", "entity_count",
        "origination_count", "origination_rate",
        "adoption_count", "adoption_rate",
        "avg_lag", "median_lag",
        "collaboration_count",
        "weighted_degree", "betweenness", "eigenvector_centrality",
    ]
    city_list = city_list[[c for c in col_order if c in city_list.columns]]

    print(f"    City attributes: {len(city_list)} cities, {len(city_list.columns)} columns")
    return city_list


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("Step 5: Build three core analysis tables")
    print("=" * 60)

    gh_prom, contrib, loc, cities, city_set, first_event_map = load_data()
    user_city = build_user_city_map(loc, city_set)

    # Table 1
    adoption_df = build_adoption_events(gh_prom, contrib, user_city, first_event_map)

    # Table 2
    edges_agg, edges_monthly = build_collaboration_edges(gh_prom, contrib, user_city)

    # Table 3
    city_attr = build_city_attributes(adoption_df, edges_agg, cities, gh_prom, user_city)

    # ── Save ──
    DATA_OUTPUT.mkdir(parents=True, exist_ok=True)

    adoption_df.to_csv(DATA_OUTPUT / "city_project_adoption_events.csv", index=False)
    print(f"\n✅ Saved → city_project_adoption_events.csv")

    edges_agg.to_csv(DATA_OUTPUT / "city_collaboration_edges.csv", index=False)
    edges_monthly.to_csv(DATA_OUTPUT / "city_collaboration_edges_monthly.csv", index=False)
    print(f"✅ Saved → city_collaboration_edges.csv + monthly variant")

    city_attr.to_csv(DATA_OUTPUT / "city_attributes.csv", index=False)
    print(f"✅ Saved → city_attributes.csv")

    # ── Summary ──
    print("\n" + "=" * 60)
    print("📊 Final summary")
    print("=" * 60)
    print(f"  city_project_adoption_events : {len(adoption_df)} rows")
    print(f"  city_collaboration_edges     : {len(edges_agg)} aggregate + {len(edges_monthly)} monthly")
    print(f"  city_attributes              : {len(city_attr)} cities × {len(city_attr.columns)} columns")

    if len(city_attr) > 0:
        print(f"\n  Top 10 cities by origination_count:")
        top = city_attr.nlargest(10, "origination_count")
        print(top[["city", "origination_count", "adoption_count",
                    "avg_lag", "weighted_degree"]].to_string(index=False))


if __name__ == "__main__":
    main()
