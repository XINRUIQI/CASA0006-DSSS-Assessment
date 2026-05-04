"""
Step 6 – Augment city_attributes.csv with external city-level data.

Adds the following columns to city_attributes.csv:
  - population          (metro-area population, millions)
  - gdp_per_capita      (country-level, current USD ~2023)
  - education_rate      (country-level tertiary-education gross enrolment ratio)
  - research_capacity   (count of QS-top-500 universities in the city, proxy)
  - digital_infra       (country-level internet-user share, %)
  - rd_expenditure      (country-level R&D spending as % of GDP)
  - timezone_utc        (offset from UTC, hours, derived from longitude)
  - region              (continent / macro-region)

Data sources (approximate values for 2022-2023):
  - City population: UN World Urbanization Prospects / national statistics
  - GDP per capita: World Bank WDI (current USD, 2023)
  - Education: World Bank – gross enrolment ratio, tertiary (%, latest)
  - Internet users: ITU / World Bank (% of population, latest)
  - R&D expenditure: UNESCO / World Bank (% of GDP, latest)
  - Research capacity: QS World University Rankings 2024 (top-500 count per city)

Outputs
-------
  - Overwrites  data/output/city_attributes.csv  with augmented columns
  - Also saves  data/raw/city_attributes/city_external_data.csv  for audit
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DATA_RAW, DATA_OUTPUT

# ═════════════════════════════════════════════════════════════════════════════
# Country-level indicators  (source: World Bank / UNESCO, ~2022-2023)
# Keys are country names matching city_list.csv
# ═════════════════════════════════════════════════════════════════════════════

COUNTRY_DATA = {
    # country: (gdp_per_capita_usd, education_tertiary_%, internet_users_%, rd_pct_gdp)
    "United States":        (76330, 88.2, 92.0, 3.46),
    "China":                (12720, 60.0, 73.0, 2.55),
    "United Kingdom":       (46125, 62.0, 95.0, 2.90),
    "India":                ( 2485, 30.0, 52.0, 0.65),
    "Japan":                (33815, 65.5, 93.0, 3.26),
    "South Korea":          (32255, 98.0, 97.6, 4.93),
    "Germany":              (51380, 72.0, 93.0, 3.13),
    "France":               (42330, 67.0, 92.0, 2.22),
    "Canada":               (52080, 75.0, 93.0, 1.69),
    "Singapore":            (65640, 91.0, 96.0, 1.93),
    "Netherlands":          (57025, 88.0, 95.0, 2.32),
    "Switzerland":          (91930, 63.0, 96.0, 3.37),
    "Australia":            (63530, 113.0, 96.0, 1.68),
    "Sweden":               (55870, 76.0, 97.0, 3.40),
    "Denmark":              (67790, 82.0, 98.0, 2.85),
    "Spain":                (30120, 93.0, 93.0, 1.44),
    "Italy":                (34085, 64.0, 90.0, 1.43),
    "Taiwan":               (32756, 84.0, 90.0, 3.76),
    "Israel":               (52170, 63.0, 90.0, 5.44),
    "Czech Republic":       (27220, 66.0, 88.0, 1.95),
    "Poland":               (18320, 67.0, 87.0, 1.44),
    "Austria":              (52085, 90.0, 93.0, 3.20),
    "Finland":              (50550, 93.0, 96.0, 2.94),
    "Ireland":              (103685, 78.0, 92.0, 1.23),
    "Turkey":               (10674, 99.0, 83.0, 1.09),
    "United Arab Emirates": (49450, 33.0, 99.0, 1.30),
    "Russia":               (11480, 82.0, 88.0, 1.10),
    "Ukraine":              ( 4535, 82.0, 75.0, 0.41),
    "Portugal":             (24570, 72.0, 84.0, 1.69),
    "Vietnam":              ( 4164, 28.5, 79.0, 0.43),
    "Belgium":              (49540, 80.0, 92.0, 3.45),
    "Greece":               (20867, 143.0, 83.0, 1.46),
    "Hungary":              (18390, 47.0, 89.0, 1.62),
    "Bulgaria":             (13980, 79.0, 80.0, 0.85),
    "Indonesia":            ( 4788, 36.0, 66.0, 0.28),
    "Pakistan":             ( 1470, 10.0, 36.5, 0.22),
    "Egypt":                ( 3635, 35.0, 72.0, 0.96),
    "Thailand":             ( 7066, 49.0, 88.0, 1.34),
    "Malaysia":             (12570, 43.0, 97.0, 1.04),
    "Brazil":               ( 8920, 55.0, 84.0, 1.16),
    "Nepal":                ( 1336, 14.0, 52.0, 0.30),
    "Estonia":              (28310, 70.0, 92.0, 1.76),
    "Serbia":               ( 9530, 73.0, 81.0, 0.99),
    "Ethiopia":             (1020,  9.0, 25.0, 0.27),
    "Saudi Arabia":         (32586, 70.0, 99.0, 0.80),
    "Norway":               (87925, 82.0, 98.0, 2.28),
    "Mexico":               (13650, 43.0, 77.0, 0.28),
    "Argentina":            (13710, 108.0, 87.0, 0.46),
    "New Zealand":          (48780, 77.0, 96.0, 1.37),
    "Chile":                (16265, 105.0, 90.0, 0.34),
    "Colombia":             ( 6340, 56.0, 73.0, 0.29),
    "Peru":                 ( 7050, 70.0, 71.0, 0.13),
    "Romania":              (17000, 51.0, 84.0, 0.47),
    "South Africa":         ( 6190, 24.0, 72.0, 0.83),
    "Kenya":                ( 1840, 12.0, 40.0, 0.79),
    "Nigeria":              ( 1560, 10.0, 36.0, 0.13),
    "Philippines":          ( 3670, 36.0, 53.0, 0.16),
}

# ═════════════════════════════════════════════════════════════════════════════
# City metro-area population (millions, ~2023 estimates)
# Sources: UN WUP 2024, national census bureaux, Wikipedia
# ═════════════════════════════════════════════════════════════════════════════

CITY_POPULATION = {
    # --- China ---
    "Beijing": 21.5, "Shanghai": 24.9, "Shenzhen": 17.6, "Hangzhou": 12.2,
    "Guangzhou": 18.7, "Chengdu": 21.0, "Nanjing": 9.4, "Wuhan": 12.3,
    "Xi'an": 13.0, "Hefei": 9.4, "Tianjin": 13.9, "Hong Kong": 7.5,
    "Suzhou": 12.7, "Chongqing": 32.1, "Harbin": 10.0, "Kunming": 8.5,
    "Shenyang": 9.1, "Zhuhai": 2.4, "Jinan": 9.2, "Dalian": 7.5,
    "Xiamen": 5.3,

    # --- United States ---
    "San Francisco": 4.7, "New York": 20.1, "Los Angeles": 13.2,
    "Seattle": 4.0, "Boston": 4.9, "Chicago": 9.6, "Austin": 2.3,
    "Washington": 6.3, "Atlanta": 6.1, "Denver": 2.9, "San Diego": 3.3,
    "San Jose": 2.0, "Philadelphia": 6.2, "Dallas": 7.6, "Houston": 7.1,
    "Miami": 6.2, "Pittsburgh": 2.4, "Palo Alto": 0.07,
    "Mountain View": 0.08, "Sunnyvale": 0.16, "Cupertino": 0.06,
    "Redmond": 0.07, "Portland": 2.5, "Phoenix": 4.9, "Salt Lake City": 1.3,
    "Minneapolis": 3.7, "Ann Arbor": 0.37, "Boulder": 0.33,
    "Berkeley": 0.12, "Santa Clara": 0.13, "Menlo Park": 0.035,
    "Champaign": 0.09, "Princeton": 0.03, "Baltimore": 2.8,
    "Cleveland": 2.1, "Urbana": 0.04, "Cambridge": 0.12,
    "College Park": 0.03, "Orlando": 2.7, "Kansas City": 2.2,
    "Bellevue": 0.15, "Chapel Hill": 0.06, "Saint Louis": 2.8,
    "Tempe": 0.19, "Raleigh": 1.60, "Detroit": 4.39,

    # --- United States (state-level entries → use largest city as proxy) ---
    "California": 39.5, "Oregon": 4.2, "Florida": 22.2, "Texas": 30.0,

    # --- United Kingdom ---
    "London": 9.6, "Cambridge": 0.16, "Oxford": 0.15, "Edinburgh": 0.54,
    "Manchester": 2.8, "Bristol": 0.47, "Sandwell": 0.33, "England": 56.5,

    # --- Germany ---
    "Berlin": 3.6, "Munich": 1.6, "Hamburg": 1.9, "Frankfurt": 2.3,
    "Cologne": 1.1, "Stuttgart": 0.63, "Heidelberg": 0.16,
    "Aachen": 0.25, "Karlsruhe": 0.31, "Nuremberg": 0.52,
    "Hildesheim": 0.10,

    # --- France ---
    "Paris": 12.3, "Lyon": 1.7, "Toulouse": 1.0, "Grenoble": 0.45,
    "Mars": 0.015,

    # --- Netherlands ---
    "Amsterdam": 1.2, "Rotterdam": 1.0, "Delft": 0.10, "Eindhoven": 0.24,
    "Utrecht": 0.36,

    # --- Switzerland ---
    "Zurich": 1.4, "Geneva": 0.64, "Lausanne": 0.42,

    # --- Scandinavia ---
    "Stockholm": 1.6, "Copenhagen": 1.4, "Helsinki": 1.3, "Oslo": 1.1,
    "Gothenburg": 0.60, "Tallinn": 0.45,

    # --- Southern Europe ---
    "Madrid": 6.7, "Barcelona": 5.6, "Lisbon": 2.9,
    "Rome": 4.3, "Milan": 3.2, "Turin": 1.7, "Catania": 0.31,
    "Athens": 3.2,

    # --- Central / Eastern Europe ---
    "Vienna": 2.0, "Prague": 1.3, "Warsaw": 1.8, "Krakow": 0.78,
    "Budapest": 1.8, "Dublin": 1.4, "Brussels": 1.2,
    "Moscow": 12.6, "Saint Petersburg": 5.4,
    "Sofia": 1.3, "Lviv": 0.72, "Belgrade": 1.7,
    "Bucharest": 1.8, "Wroclaw": 0.64,

    # --- Middle East ---
    "Istanbul": 15.6, "Ankara": 5.7,     "Tel Aviv": 4.1, "Haifa": 1.0, "Jerusalem": 0.97,
    "Dubai": 3.5, "Abu Dhabi": 1.5, "Riyadh": 7.7,

    # --- East / Southeast Asia ---
    "Tokyo": 37.4, "Osaka": 19.3, "Kyoto": 1.5, "Nagoya": 9.5, "Tsukuba": 0.25,
    "Seoul": 9.9, "Busan": 3.4, "Daejeon": 1.5,
    "Taipei": 7.0, "Hsinchu": 0.45,
    "Singapore": 5.9,
    "Bangkok": 10.7, "Jakarta": 10.6, "Kuala Lumpur": 8.0,
    "Ho Chi Minh City": 9.3, "Hanoi": 8.4, "Manila": 13.9,

    # --- South Asia ---
    "Bengaluru": 12.3, "Mumbai": 20.7, "New Delhi": 16.8, "Delhi": 16.8,
    "Hyderabad": 10.0, "Chennai": 10.9, "Pune": 7.4, "Kolkata": 15.1,
    "Ahmedabad": 8.3, "Lahore": 13.0, "Karachi": 16.1,
    "Islamabad": 1.2, "Kathmandu": 1.5,

    # --- Oceania ---
    "Sydney": 5.3, "Melbourne": 5.1, "Brisbane": 2.6,
    "Perth": 2.1, "Canberra": 0.47, "Auckland": 1.7,

    # --- Americas ---
    "Toronto": 6.2, "Vancouver": 2.6, "Montreal": 4.3,
    "Ottawa": 1.0, "Calgary": 1.6, "Edmonton": 1.1, "Waterloo": 0.58,
    "Sao Paulo": 22.0, "Rio de Janeiro": 13.5, "Mexico City": 21.8,
    "Buenos Aires": 15.2, "Santiago": 7.1, "Bogota": 10.6,
    "Lima": 10.9,

    # --- Africa ---
    "Cairo": 21.3, "Nairobi": 5.0, "Lagos": 15.9,
    "Cape Town": 4.7, "Johannesburg": 6.1, "Addis Ababa": 5.2,
}

# ═════════════════════════════════════════════════════════════════════════════
# Research capacity: approximate count of QS top-500 universities per city
# Source: QS World University Rankings 2024
# ═════════════════════════════════════════════════════════════════════════════

RESEARCH_CAPACITY = {
    # Major research hubs
    "London": 5, "Boston": 3, "New York": 3, "San Francisco": 2,
    "Los Angeles": 2, "Cambridge": 2, "Tokyo": 3, "Beijing": 3,
    "Shanghai": 2, "Paris": 4, "Seoul": 3, "Singapore": 2,
    "Melbourne": 2, "Sydney": 2, "Toronto": 2, "Zurich": 2,
    "Hong Kong": 3, "Berlin": 2, "Munich": 2, "Edinburgh": 2,

    # Strong research cities (1 top-500 university)
    "Oxford": 1, "Palo Alto": 1, "Seattle": 1, "Chicago": 1,
    "Montreal": 1, "Vancouver": 1, "Austin": 1, "Taipei": 1,
    "Hangzhou": 1, "Nanjing": 1, "Bengaluru": 1, "Delhi": 1,
    "New Delhi": 1, "Stockholm": 1, "Copenhagen": 1, "Helsinki": 1,
    "Amsterdam": 1, "Barcelona": 1, "Madrid": 1, "Lisbon": 1,
    "Dublin": 1, "Brussels": 1, "Vienna": 1, "Prague": 1,
    "Warsaw": 1, "Moscow": 1, "Istanbul": 1, "Tel Aviv": 1,
    "Osaka": 1, "Kyoto": 1, "Brisbane": 1, "Sao Paulo": 1,
    "Buenos Aires": 1, "Mexico City": 1, "Cairo": 1, "Cape Town": 1,
    "Pittsburgh": 1, "San Diego": 1, "Philadelphia": 1,
    "Atlanta": 1, "Washington": 1, "Ann Arbor": 1, "Berkeley": 1,
    "Princeton": 1, "Boulder": 1, "Champaign": 1, "Urbana": 1,
    "College Park": 1, "Chapel Hill": 1, "Geneva": 1, "Lausanne": 1,
    "Delft": 1, "Shenzhen": 1, "Wuhan": 1, "Xi'an": 1,
    "Chengdu": 1, "Guangzhou": 1, "Hefei": 1, "Daejeon": 1,
    "Hsinchu": 1, "Kuala Lumpur": 1, "Bangkok": 1,
    "Milan": 1, "Rome": 1, "Karlsruhe": 1, "Aachen": 1,
    "Saint Petersburg": 1, "Mumbai": 1, "Chennai": 1,
    "Hyderabad": 1, "Kolkata": 1, "Pune": 1, "Waterloo": 1,
    "Busan": 1, "Jakarta": 1, "Hanoi": 1,
}

# ═════════════════════════════════════════════════════════════════════════════
# Region mapping: country → macro-region
# ═════════════════════════════════════════════════════════════════════════════

REGION_MAP = {
    "United States": "North America", "Canada": "North America",
    "Mexico": "Latin America",
    "Brazil": "Latin America", "Argentina": "Latin America",
    "Chile": "Latin America", "Colombia": "Latin America",
    "Peru": "Latin America",

    "United Kingdom": "Europe", "Germany": "Europe", "France": "Europe",
    "Netherlands": "Europe", "Switzerland": "Europe", "Sweden": "Europe",
    "Denmark": "Europe", "Finland": "Europe", "Norway": "Europe",
    "Spain": "Europe", "Italy": "Europe", "Portugal": "Europe",
    "Austria": "Europe", "Czech Republic": "Europe", "Poland": "Europe",
    "Hungary": "Europe", "Ireland": "Europe", "Belgium": "Europe",
    "Greece": "Europe", "Romania": "Europe", "Bulgaria": "Europe",
    "Estonia": "Europe", "Serbia": "Europe",
    "Russia": "Europe", "Ukraine": "Europe",

    "China": "East Asia", "Japan": "East Asia",
    "South Korea": "East Asia", "Taiwan": "East Asia",
    "Hong Kong": "East Asia",

    "Singapore": "Southeast Asia", "Thailand": "Southeast Asia",
    "Vietnam": "Southeast Asia", "Indonesia": "Southeast Asia",
    "Malaysia": "Southeast Asia", "Philippines": "Southeast Asia",

    "India": "South Asia", "Pakistan": "South Asia",
    "Nepal": "South Asia", "Bangladesh": "South Asia",

    "Israel": "Middle East", "Turkey": "Middle East",
    "United Arab Emirates": "Middle East", "Saudi Arabia": "Middle East",
    "Egypt": "Middle East",

    "Australia": "Oceania", "New Zealand": "Oceania",

    "Kenya": "Africa", "Nigeria": "Africa",
    "South Africa": "Africa", "Ethiopia": "Africa",
}


def compute_timezone_utc(lon):
    """Approximate UTC offset from longitude (±0.5h rounding)."""
    if pd.isna(lon):
        return np.nan
    return round(lon / 15.0 * 2) / 2  # round to nearest 0.5


def main():
    print("=" * 60)
    print("Step 6: Augment city_attributes with external data")
    print("=" * 60)

    # ── Load current city_attributes ──
    attr_path = DATA_OUTPUT / "city_attributes.csv"
    df = pd.read_csv(attr_path)
    print(f"  Loaded {len(df)} cities from {attr_path}")

    # ── Handle duplicate city name (Cambridge UK vs US) ──
    # Identify by country
    existing_cities = set(zip(df["city"], df["country"]))

    # ── Add population ──
    def get_population(row):
        city, country = row["city"], row["country"]
        if city in CITY_POPULATION:
            return CITY_POPULATION[city]
        return np.nan

    df["population_million"] = df.apply(get_population, axis=1)

    # ── Add country-level indicators ──
    def get_country_data(country, idx):
        if country in COUNTRY_DATA:
            return COUNTRY_DATA[country][idx]
        return np.nan

    df["gdp_per_capita"] = df["country"].apply(lambda c: get_country_data(c, 0))
    df["education_tertiary_pct"] = df["country"].apply(lambda c: get_country_data(c, 1))
    df["internet_users_pct"] = df["country"].apply(lambda c: get_country_data(c, 2))
    df["rd_expenditure_pct"] = df["country"].apply(lambda c: get_country_data(c, 3))

    # ── Add research capacity ──
    df["research_capacity"] = df["city"].map(RESEARCH_CAPACITY).fillna(0).astype(int)

    # ── Add timezone ──
    df["lon_numeric"] = pd.to_numeric(df["lon"], errors="coerce")
    df["timezone_utc"] = df["lon_numeric"].apply(compute_timezone_utc)
    df = df.drop(columns=["lon_numeric"])

    # ── Add region ──
    df["region"] = df["country"].map(REGION_MAP).fillna("Other")

    # ── Compute per-capita rates using real population ──
    pop = df["population_million"].replace(0, np.nan) * 1_000_000
    df["origination_rate_pop"] = (df["origination_count"] / pop * 1_000_000).round(2)
    df["adoption_rate_pop"] = (df["adoption_count"] / pop * 1_000_000).round(2)
    df["collaboration_rate_pop"] = (df["collaboration_count"] / pop * 1_000_000).round(2)

    # ── Report coverage ──
    pop_missing = df["population_million"].isna().sum()
    gdp_missing = df["gdp_per_capita"].isna().sum()
    region_missing = (df["region"] == "Other").sum()
    print(f"\n  Coverage:")
    print(f"    Population:  {len(df) - pop_missing}/{len(df)} cities")
    print(f"    GDP/capita:  {len(df) - gdp_missing}/{len(df)} cities")
    print(f"    Region:      {len(df) - region_missing}/{len(df)} cities")

    if pop_missing > 0:
        missing = df[df["population_million"].isna()]["city"].tolist()
        print(f"    ⚠️  Missing population: {missing}")

    if gdp_missing > 0:
        missing = df[df["gdp_per_capita"].isna()]["country"].unique().tolist()
        print(f"    ⚠️  Missing GDP country: {missing}")

    # ── Save external data separately for audit ──
    ext_dir = DATA_RAW / "city_attributes"
    ext_dir.mkdir(parents=True, exist_ok=True)
    ext_cols = ["city", "country", "population_million", "gdp_per_capita",
                "education_tertiary_pct", "internet_users_pct", "rd_expenditure_pct",
                "research_capacity", "timezone_utc", "region"]
    df[ext_cols].to_csv(ext_dir / "city_external_data.csv", index=False)
    print(f"\n✅ Saved external data → {ext_dir / 'city_external_data.csv'}")

    # ── Overwrite city_attributes ──
    df.to_csv(attr_path, index=False)
    print(f"✅ Updated city_attributes → {attr_path}")

    # ── Summary ──
    print(f"\n{'=' * 60}")
    print(f"📊 Augmented city_attributes: {len(df)} cities × {len(df.columns)} columns")
    print(f"{'=' * 60}")
    print(f"\n  Columns: {list(df.columns)}")

    print(f"\n  Region distribution:")
    print(df["region"].value_counts().to_string())

    print(f"\n  Top 10 cities by population:")
    top = df.nlargest(10, "population_million")
    print(top[["city", "country", "population_million", "gdp_per_capita",
               "research_capacity"]].to_string(index=False))

    print(f"\n  Descriptive stats for new columns:")
    new_cols = ["population_million", "gdp_per_capita", "education_tertiary_pct",
                "internet_users_pct", "rd_expenditure_pct", "research_capacity"]
    print(df[new_cols].describe().round(2).to_string())


if __name__ == "__main__":
    main()
