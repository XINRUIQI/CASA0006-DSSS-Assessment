"""
Step 3d – Build the final curated city list (100-150 high-confidence cities).

1. Load location_mapping.csv
2. Keep only high + medium confidence matches
3. Aggregate: count how many prominent-project owners are in each city
4. Rank cities and select top 100-150
5. Output: data/processed/city_list.csv

This city list becomes the spatial backbone for all downstream analysis.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DATA_PROCESSED

TARGET_CITY_COUNT = 150  # upper bound; may keep fewer if not enough


def main():
    print("=" * 60)
    print("Step 3d: Build curated city list")
    print("=" * 60)

    loc_path = DATA_PROCESSED / "location_mapping.csv"
    df = pd.read_csv(loc_path, dtype=str).fillna("")

    # Keep only high/medium confidence
    confident = df[df["confidence"].isin(["high", "medium"])].copy()
    print(f"  Total location records: {len(df)}")
    print(f"  High/medium confidence: {len(confident)}")

    # Only GitHub entities (HF authors mostly lack location)
    gh_conf = confident[confident["platform"] == "GitHub"]
    print(f"  GitHub high/medium:     {len(gh_conf)}")

    # Filter out suspicious city names (2 chars or fewer, like "Eu", "Us")
    gh_conf = gh_conf[gh_conf["matched_city"].str.len() > 2]

    # Convert lat/lon to numeric before aggregation
    gh_conf["lat"] = pd.to_numeric(gh_conf["lat"], errors="coerce")
    gh_conf["lon"] = pd.to_numeric(gh_conf["lon"], errors="coerce")

    # Group by city name + country ONLY (not lat/lon) to merge duplicates
    city_counts = (
        gh_conf.groupby(["matched_city", "country"])
        .agg(
            entity_count=("entity_id", "nunique"),
            lat=("lat", "mean"),
            lon=("lon", "mean"),
        )
        .reset_index()
        .sort_values("entity_count", ascending=False)
    )

    print(f"\n  Unique cities found: {len(city_counts)}")

    # Select top cities
    selected = city_counts.head(TARGET_CITY_COUNT).copy()
    selected = selected.reset_index(drop=True)
    selected.index = selected.index + 1
    selected.index.name = "rank"

    # Save
    out_path = DATA_PROCESSED / "city_list.csv"
    selected.to_csv(out_path)
    print(f"\n✅ Saved {len(selected)} cities → {out_path}")

    # Display top 30
    print(f"\n📊 Top 30 cities:")
    print(selected.head(30)[["matched_city", "country", "entity_count"]]
          .to_string())

    # Regional summary
    print(f"\n📊 Cities by country (top 15):")
    country_counts = selected.groupby("country").agg(
        cities=("matched_city", "count"),
        total_entities=("entity_count", "sum"),
    ).sort_values("total_entities", ascending=False)
    print(country_counts.head(15).to_string())


if __name__ == "__main__":
    main()
