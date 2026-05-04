"""
Step 5 – Build three core analysis tables from collected data.

Prerequisites
-------------
- data/raw/github/github_candidates.csv                    (from step 1a)
- data/raw/github/github_repo_contributors.csv             (from step 4)
- data/raw/github/github_repo_participation_events.csv     (from step 4, Part C)
- data/raw/github/github_owner_locations.csv               (from step 3a + step 4)
- data/processed/city_list.csv                             (from step 3d)
- data/processed/prominent_projects_master.csv             (from step 1c)
- data/processed/hf_derivation_edges.csv                   (from step 5b, optional)

Outputs (all in data/output/)
-------
1. city_project_adoption_events.csv
2. city_collaboration_edges.csv
3. city_attributes.csv

Logic overview
--------------
- "adoption" comes from two complementary sources:
    * GitHub contributor / participation events (a contributor from city C
      participates in repo R)
    * Hugging Face derivation relations (a model authored by city C
      declares ancestor model A as its base_model → C "adopted" A)
  In both cases, the first month the city appears in connection to the
  project is the adoption month.
- "origination" = the city of the project owner at creation time
  (GitHub repo owner OR HF project author).
- "collaboration edge" = two cities share contributors on the same project
  (GitHub) OR are linked by a derivation relation (HF descendant city → HF
  ancestor city).
- All timestamps are aggregated to YYYYMM monthly granularity.
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
from step_06_clean_map_locations import (
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

    # 3. User locations — GitHub owners + HF authors merged into one table
    loc_path = DATA_RAW / "github" / "github_owner_locations.csv"
    loc = pd.read_csv(loc_path, dtype=str).fillna("")
    print(f"    GitHub user location records: {len(loc)}")

    hf_loc_path = DATA_RAW / "huggingface" / "hf_author_locations.csv"
    if hf_loc_path.exists():
        hf_loc = pd.read_csv(hf_loc_path, dtype=str).fillna("")
        # Conform to the schema of github_owner_locations.csv
        # (login, location, type) so build_user_city_map works for both.
        hf_loc_renamed = pd.DataFrame({
            "login": hf_loc["author"],
            "location": hf_loc["raw_location"],
            "type": hf_loc["entity_type"].replace({
                "organization": "Organization",
                "user": "User",
                "unknown": "User",
            }),
        })
        loc = pd.concat([loc, hf_loc_renamed], ignore_index=True)
        print(f"    HF author location records  : {len(hf_loc_renamed)}")
        print(f"    Combined location records   : {len(loc)}")
    else:
        print("    ⚠️  No hf_author_locations.csv — HF authors will be skipped.")

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


def load_hf_data():
    """Load HF prominent projects + derivation edges parsed from local tags.

    Returns
    -------
    hf_prom : DataFrame
        Prominent HF rows from prominent_projects_master.csv with helper
        columns: ``author`` and ``created_month``.
    derivation_df : DataFrame
        Output of step5b (descendant_id → ancestor_id edges with relation,
        author and month info). Empty DataFrame if step5b hasn't been run.
    """
    print("\n  Loading HF data …")

    master_path = DATA_PROCESSED / "prominent_projects_master.csv"
    if not master_path.exists():
        print("    ⚠️  prominent_projects_master.csv missing; skipping HF.")
        return pd.DataFrame(), pd.DataFrame()

    master = pd.read_csv(master_path, dtype=str)
    hf_prom = master[master["platform"] == "HuggingFace"].copy()
    hf_prom["author"] = hf_prom["full_id"].fillna("").str.split("/").str[0]
    hf_prom["created_month"] = hf_prom["created_at"].apply(_to_month)
    print(f"    Prominent HF projects: {len(hf_prom)}")

    deriv_path = DATA_PROCESSED / "hf_derivation_edges.csv"
    if deriv_path.exists():
        deriv = pd.read_csv(deriv_path, dtype=str)
        for col in ("descendant_created_month",
                    "ancestor_created_month",
                    "lag_months"):
            if col in deriv.columns:
                deriv[col] = pd.to_numeric(deriv[col], errors="coerce")
        print(f"    HF derivation edges  : {len(deriv)}")
    else:
        print("    ⚠️  hf_derivation_edges.csv missing — run step5b first.")
        deriv = pd.DataFrame()

    return hf_prom, deriv


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

    # Source 1: Contributors API records (commit-based contributors)
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

    # Source 2: Participation events (includes PR-only contributors
    # not captured by the Contributors API)
    pr_only_added = 0
    for (repo, login), event_month in first_event_map.items():
        if login not in user_city:
            continue
        if repo not in repo_created:
            continue
        city = user_city[login]
        if city not in city_project.get(repo, {}):
            city_project[repo][city] = event_month
            pr_only_added += 1
        elif event_month < city_project[repo][city]:
            city_project[repo][city] = event_month

    print(f"    Participation event hits: {api_hits}, "
          f"fallback approximations: {api_misses}, "
          f"PR-only additions: {pr_only_added}")

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

    neg_count = (df["lag"] < 0).sum()
    if neg_count > 0:
        df = df[df["lag"] >= 0].reset_index(drop=True)
        print(f"    Excluded {neg_count} events with negative lag "
              "(forked repos / code migrations with inherited commit histories)")

    print(f"    Adoption events: {len(df)} rows "
          f"({df['city'].nunique()} cities, {df['project_id'].nunique()} projects)")
    return df


def _month_diff(m1, m2):
    """Number of months between YYYYMM integers."""
    y1, mo1 = divmod(m1, 100)
    y2, mo2 = divmod(m2, 100)
    return (y2 - y1) * 12 + (mo2 - mo1)


# ═══════════════════════════════════════════════════════════════════════════════
# Table 1 (HF supplement): origination + derivation-based adoption
# ═══════════════════════════════════════════════════════════════════════════════

def build_hf_adoption_events(hf_prom, deriv_df, user_city):
    """
    Construct HF adoption events from two sources:

    * Origination — every prominent HF project contributes one row at its
      author's city, with lag = 0 and is_originator = 1.
    * Derivation — for each prominent → prominent base_model edge, the
      descendant author's city is recorded as adopting the ancestor
      project; adoption month = descendant_created_month, lag relative to
      ancestor_created_month.

    Multiple events on the same (city, project_id) are collapsed to the
    earliest month.
    """
    print("\n  Building HF adoption events …")

    if hf_prom.empty:
        return pd.DataFrame(columns=[
            "city", "project_id", "global_origin_month",
            "city_first_adoption_month", "lag", "is_originator",
        ])

    project_origin = {}      # project_id -> origin_month
    project_owner_city = {}  # project_id -> owner_city
    # (city, project_id) -> first_adoption_month
    pair_first_month = {}

    # ── Origination events ───────────────────────────────────────────────────
    n_origin_with_city = 0
    for _, row in hf_prom.iterrows():
        pid = row["project_id"]
        cm = row["created_month"]
        if cm is None or pd.isna(cm):
            continue
        cm = int(cm)
        project_origin[pid] = cm

        author = row["author"]
        city = user_city.get(author)
        if not city:
            continue
        project_owner_city[pid] = city
        key = (city, pid)
        if key not in pair_first_month or cm < pair_first_month[key]:
            pair_first_month[key] = cm
        n_origin_with_city += 1

    print(f"    HF projects with author city: {n_origin_with_city} "
          f"({n_origin_with_city/len(hf_prom)*100:.1f}% of {len(hf_prom)})")

    # ── Derivation-based adoption events ─────────────────────────────────────
    n_deriv_kept = 0
    n_deriv_skipped_city = 0
    n_deriv_skipped_neg = 0
    if not deriv_df.empty:
        for _, edge in deriv_df.iterrows():
            ancestor_pid = edge["ancestor_project_id"]
            if ancestor_pid not in project_origin:
                continue
            d_month = edge.get("descendant_created_month")
            a_month = edge.get("ancestor_created_month")
            if pd.isna(d_month) or pd.isna(a_month):
                continue
            d_month = int(d_month)
            a_month = int(a_month)
            if d_month < a_month:
                # Implausible: descendant predates ancestor. Skip; usually
                # tag noise or cross-fork timestamps.
                n_deriv_skipped_neg += 1
                continue

            descendant_author = edge["descendant_author"]
            descendant_city = user_city.get(descendant_author)
            if not descendant_city:
                n_deriv_skipped_city += 1
                continue

            key = (descendant_city, ancestor_pid)
            if key not in pair_first_month or d_month < pair_first_month[key]:
                pair_first_month[key] = d_month
            n_deriv_kept += 1

    print(f"    HF derivation events kept   : {n_deriv_kept}")
    print(f"      (skipped no descendant city: {n_deriv_skipped_city}, "
          f"skipped negative lag: {n_deriv_skipped_neg})")

    # ── Build event rows ─────────────────────────────────────────────────────
    rows = []
    for (city, pid), first_month in pair_first_month.items():
        origin_m = project_origin.get(pid)
        if origin_m is None:
            continue
        lag = _month_diff(origin_m, first_month)
        rows.append({
            "city": city,
            "project_id": pid,
            "global_origin_month": origin_m,
            "city_first_adoption_month": first_month,
            "lag": lag,
            "is_originator": int(project_owner_city.get(pid) == city),
        })

    df = pd.DataFrame(rows)
    if len(df) > 0:
        n_neg = (df["lag"] < 0).sum()
        if n_neg > 0:
            df = df[df["lag"] >= 0].reset_index(drop=True)
            print(f"    Dropped {n_neg} HF events with negative lag")
    print(f"    HF adoption events total    : {len(df)} rows "
          f"({df['city'].nunique() if len(df) else 0} cities, "
          f"{df['project_id'].nunique() if len(df) else 0} projects)")
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# Table 2: city_collaboration_edges
# ═══════════════════════════════════════════════════════════════════════════════

def build_collaboration_edges(gh_prom, contrib, user_city,
                              hf_prom=None, deriv_df=None):
    """
    Construct undirected city-pair collaboration edges from two sources.

    GitHub: two cities are connected if they share contributors on the
    same prominent repo (counted once per shared repo).

    Hugging Face derivation: two cities are connected if a model authored
    by city A declares a model authored by city B as its base_model
    (counted once per descendant project; intra-city edges discarded).

    Edge weight = total number of shared projects across both sources.
    Monthly snapshot uses repo `created_month` for GitHub and
    `descendant_created_month` for HF.
    """
    print("\n  Building city_collaboration_edges …")

    repo_created = dict(zip(gh_prom["repo_full_name"],
                            gh_prom["created_month"].astype("Int64")))

    # repo_cities[project_key] = (set_of_cities, project_created_month)
    repo_cities = defaultdict(set)
    project_month = {}

    # ── GitHub side ───────────────────────────────────────────────────────────
    repo_owner = dict(zip(gh_prom["repo_full_name"], gh_prom["owner_login"]))
    for repo, owner in repo_owner.items():
        if owner in user_city:
            repo_cities[repo].add(user_city[owner])
        cm = repo_created.get(repo)
        if cm is not None and not pd.isna(cm):
            project_month[repo] = int(cm)

    for _, row in contrib.iterrows():
        repo = row["repo_full_name"]
        login = row["contributor_login"]
        if login in user_city and repo in repo_created:
            repo_cities[repo].add(user_city[login])

    n_gh_projects = len(repo_cities)

    # ── HF derivation side ────────────────────────────────────────────────────
    n_hf_pairs_added = 0
    if hf_prom is not None and deriv_df is not None and not deriv_df.empty:
        hf_origin_month = dict(zip(hf_prom["project_id"],
                                    hf_prom["created_month"]))
        for _, edge in deriv_df.iterrows():
            descendant_pid = edge["descendant_project_id"]
            ancestor_pid = edge["ancestor_project_id"]

            d_city = user_city.get(edge["descendant_author"])
            a_city = user_city.get(edge["ancestor_author"])
            if not d_city or not a_city or d_city == a_city:
                continue

            # Use the descendant project as the "shared project" key so each
            # descendant contributes exactly one shared-project unit
            # between the two cities. Avoid colliding with GitHub repo keys
            # by namespacing.
            key = f"hfderiv::{descendant_pid}"
            repo_cities[key] = {d_city, a_city}
            d_month = edge.get("descendant_created_month")
            if pd.notna(d_month):
                project_month[key] = int(d_month)
            n_hf_pairs_added += 1

    print(f"    Project units contributing edges: "
          f"GitHub repos={n_gh_projects}, HF derivation={n_hf_pairs_added}")

    # ── Aggregate to city pairs ──────────────────────────────────────────────
    edge_counter = defaultdict(lambda: {"weight": 0, "shared_projects": 0,
                                         "months": set()})
    for project_key, cities in repo_cities.items():
        if len(cities) < 2:
            continue
        cm = project_month.get(project_key)
        sorted_cities = sorted(cities)
        for c1, c2 in itertools.combinations(sorted_cities, 2):
            pair = (c1, c2)
            edge_counter[pair]["weight"] += 1
            edge_counter[pair]["shared_projects"] += 1
            if cm is not None:
                edge_counter[pair]["months"].add(int(cm))

    agg_rows = []
    for (c1, c2), info in edge_counter.items():
        agg_rows.append({
            "source_city": c1,
            "target_city": c2,
            "edge_weight": info["weight"],
            "shared_projects": info["shared_projects"],
        })

    df_agg = pd.DataFrame(agg_rows).sort_values("edge_weight",
                                                 ascending=False)

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
        print(df_agg.head(5)[["source_city", "target_city",
                              "edge_weight"]].to_string(index=False))

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
    hf_prom, deriv_df = load_hf_data()
    user_city = build_user_city_map(loc, city_set)

    # ── Table 1: GitHub adoption events ───────────────────────────────────────
    gh_adoption = build_adoption_events(gh_prom, contrib, user_city,
                                         first_event_map)
    print(f"    GitHub adoption rows: {len(gh_adoption)}")

    # ── Table 1 (HF supplement) ───────────────────────────────────────────────
    hf_adoption = build_hf_adoption_events(hf_prom, deriv_df, user_city)

    # Combine. (city, project_id) cannot collide because GitHub project_ids
    # use `owner/repo` form and HF project_ids use `hf_*_<full_id>` form.
    if len(hf_adoption) > 0:
        adoption_df = pd.concat([gh_adoption, hf_adoption], ignore_index=True)
    else:
        adoption_df = gh_adoption
    print(f"\n  Combined adoption events: {len(adoption_df)} rows "
          f"(GH={len(gh_adoption)}, HF={len(hf_adoption)})")

    # ── Table 2: collaboration edges (GH + HF) ────────────────────────────────
    edges_agg, edges_monthly = build_collaboration_edges(
        gh_prom, contrib, user_city, hf_prom=hf_prom, deriv_df=deriv_df,
    )

    # ── Table 3: city attributes ──────────────────────────────────────────────
    city_attr = build_city_attributes(adoption_df, edges_agg, cities,
                                       gh_prom, user_city)

    # ── Save ──────────────────────────────────────────────────────────────────
    DATA_OUTPUT.mkdir(parents=True, exist_ok=True)

    adoption_df.to_csv(DATA_OUTPUT / "city_project_adoption_events.csv",
                       index=False)
    print(f"\n✅ Saved → city_project_adoption_events.csv")

    edges_agg.to_csv(DATA_OUTPUT / "city_collaboration_edges.csv",
                     index=False)
    edges_monthly.to_csv(DATA_OUTPUT / "city_collaboration_edges_monthly.csv",
                         index=False)
    print(f"✅ Saved → city_collaboration_edges.csv + monthly variant")

    city_attr.to_csv(DATA_OUTPUT / "city_attributes.csv", index=False)
    print(f"✅ Saved → city_attributes.csv")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("📊 Final summary")
    print("=" * 60)
    n_gh_proj = adoption_df[~adoption_df["project_id"].str.startswith("hf_",
                            na=False)]["project_id"].nunique()
    n_hf_proj = adoption_df[adoption_df["project_id"].str.startswith("hf_",
                            na=False)]["project_id"].nunique()
    print(f"  city_project_adoption_events : {len(adoption_df)} rows")
    print(f"      distinct GH projects     : {n_gh_proj}")
    print(f"      distinct HF projects     : {n_hf_proj}")
    print(f"  city_collaboration_edges     : {len(edges_agg)} aggregate "
          f"+ {len(edges_monthly)} monthly")
    print(f"  city_attributes              : {len(city_attr)} cities × "
          f"{len(city_attr.columns)} columns")

    if len(city_attr) > 0:
        print(f"\n  Top 10 cities by origination_count:")
        top = city_attr.nlargest(10, "origination_count")
        print(top[["city", "origination_count", "adoption_count",
                    "avg_lag", "weighted_degree"]].to_string(index=False))


if __name__ == "__main__":
    main()
