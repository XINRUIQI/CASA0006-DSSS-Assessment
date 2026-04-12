"""
Step 3b – Clean raw location strings and map them to a unified city system.

Pipeline
--------
1. Load raw locations from GitHub owners + HF authors
2. Text normalisation (lowercase, strip emoji/symbols, expand abbreviations)
3. Filter out invalid locations (remote, earth, worldwide, etc.)
4. Match to a curated city dictionary (city → country, lat, lon)
5. Assign confidence labels (high / medium / low)
6. Save location_mapping.csv

The city dictionary is built from a bundled world-cities reference.
For geocoding fallback, we use the free Nominatim API (rate-limited).
"""

import csv
import re
import sys
import time
import unicodedata
from pathlib import Path
from typing import Optional, Dict, Tuple

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DATA_RAW, DATA_PROCESSED

# ── Invalid location patterns ──────────────────────────────────────────────────
INVALID_PATTERNS = [
    r"^remote",
    r"^worldwide",
    r"^earth$",
    r"^earth,",
    r"^planet earth",
    r"^internet",
    r"^global",
    r"^online",
    r"^everywhere",
    r"^anywhere",
    r"^home",
    r"^mars",
    r"^moon",
    r"^space",
    r"^heaven",
    r"^hell",
    r"^localhost",
    r"^127\.0\.0",
    r"^/dev/null",
    r"^null",
    r"^n/?a$",
    r"^none$",
    r"^unknown",
    r"^planet\s",
    r"^the\s+cloud",
    r"^metaverse",
    r"^cyberspace",
    r"^virtual",
    r"^\.$",
    r"^-$",
]
INVALID_RE = re.compile("|".join(INVALID_PATTERNS), re.IGNORECASE)

# ── Common abbreviation expansions ─────────────────────────────────────────────
ABBREVIATIONS = {
    "sf": "San Francisco",
    "sf bay area": "San Francisco",
    "bay area": "San Francisco",
    "silicon valley": "San Francisco",
    "nyc": "New York",
    "ny": "New York",
    "new york city": "New York",
    "la": "Los Angeles",
    "dc": "Washington",
    "washington dc": "Washington",
    "washington d.c.": "Washington",
    "washington, d.c.": "Washington",
    "philly": "Philadelphia",
    "hk": "Hong Kong",
    "ldn": "London",
    "bj": "Beijing",
    "sh": "Shanghai",
    "gz": "Guangzhou",
    "sz": "Shenzhen",
    "spb": "Saint Petersburg",
    "st. petersburg": "Saint Petersburg",
    "st petersburg": "Saint Petersburg",
    "ist": "Istanbul",
    "cdmx": "Mexico City",
    "mexico city": "Mexico City",
    "ciudad de mexico": "Mexico City",
    "mumbai": "Mumbai",
    "bombay": "Mumbai",
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "bangalore, india": "Bengaluru",
    "calcutta": "Kolkata",
    "madras": "Chennai",
    "saigon": "Ho Chi Minh City",
    "são paulo": "Sao Paulo",
    "sao paulo": "Sao Paulo",
    "rio de janeiro": "Rio de Janeiro",
    "muc": "Munich",
    "münchen": "Munich",
    "munich": "Munich",
    "köln": "Cologne",
    "cologne": "Cologne",
    "praha": "Prague",
    "wien": "Vienna",
    "zürich": "Zurich",
    "zurich": "Zurich",
    "genève": "Geneva",
    "montreal": "Montreal",
    "montréal": "Montreal",
    "tky": "Tokyo",
    "seoul": "Seoul",
    "taipei": "Taipei",
    "sgp": "Singapore",
}

# ── Curated top-200 global cities dictionary ───────────────────────────────────
# city_name_lower → (canonical_name, country, lat, lon)
CITY_DICT: Dict[str, Tuple[str, str, float, float]] = {}


def _build_city_dict():
    """Build a lookup dictionary from the bundled cities reference CSV,
    or fall back to a hardcoded top-200 list."""
    global CITY_DICT

    ref_path = DATA_RAW / "city_attributes" / "world_cities_reference.csv"
    if ref_path.exists():
        df = pd.read_csv(ref_path, dtype=str)
        for _, row in df.iterrows():
            key = str(row.get("city", "")).strip().lower()
            if key:
                CITY_DICT[key] = (
                    str(row.get("city", "")),
                    str(row.get("country", "")),
                    float(row.get("lat", 0)),
                    float(row.get("lon", 0)),
                )
        print(f"  Loaded {len(CITY_DICT)} cities from {ref_path}")
        return

    # Hardcoded top cities (abbreviated for space; covers major tech hubs)
    top_cities = [
        ("San Francisco", "United States", 37.7749, -122.4194),
        ("New York", "United States", 40.7128, -74.0060),
        ("Los Angeles", "United States", 34.0522, -118.2437),
        ("Seattle", "United States", 47.6062, -122.3321),
        ("Boston", "United States", 42.3601, -71.0589),
        ("Chicago", "United States", 41.8781, -87.6298),
        ("Austin", "United States", 30.2672, -97.7431),
        ("Washington", "United States", 38.9072, -77.0369),
        ("Atlanta", "United States", 33.7490, -84.3880),
        ("Denver", "United States", 39.7392, -104.9903),
        ("San Diego", "United States", 32.7157, -117.1611),
        ("Portland", "United States", 45.5152, -122.6784),
        ("San Jose", "United States", 37.3382, -121.8863),
        ("Philadelphia", "United States", 39.9526, -75.1652),
        ("Dallas", "United States", 32.7767, -96.7970),
        ("Houston", "United States", 29.7604, -95.3698),
        ("Miami", "United States", 25.7617, -80.1918),
        ("Minneapolis", "United States", 44.9778, -93.2650),
        ("Pittsburgh", "United States", 40.4406, -79.9959),
        ("Raleigh", "United States", 35.7796, -78.6382),
        ("Salt Lake City", "United States", 40.7608, -111.8910),
        ("Phoenix", "United States", 33.4484, -112.0740),
        ("Detroit", "United States", 42.3314, -83.0458),
        ("Ann Arbor", "United States", 42.2808, -83.7430),
        ("Boulder", "United States", 40.0150, -105.2705),
        ("Palo Alto", "United States", 37.4419, -122.1430),
        ("Mountain View", "United States", 37.3861, -122.0839),
        ("Sunnyvale", "United States", 37.3688, -122.0363),
        ("Cupertino", "United States", 37.3230, -122.0322),
        ("Redmond", "United States", 47.6740, -122.1215),

        ("London", "United Kingdom", 51.5074, -0.1278),
        ("Cambridge", "United Kingdom", 52.2053, 0.1218),
        ("Oxford", "United Kingdom", 51.7520, -1.2577),
        ("Edinburgh", "United Kingdom", 55.9533, -3.1883),
        ("Manchester", "United Kingdom", 53.4808, -2.2426),
        ("Bristol", "United Kingdom", 51.4545, -2.5879),

        ("Paris", "France", 48.8566, 2.3522),
        ("Lyon", "France", 45.7640, 4.8357),
        ("Toulouse", "France", 43.6047, 1.4442),
        ("Grenoble", "France", 45.1885, 5.7245),

        ("Berlin", "Germany", 52.5200, 13.4050),
        ("Munich", "Germany", 48.1351, 11.5820),
        ("Hamburg", "Germany", 53.5511, 9.9937),
        ("Frankfurt", "Germany", 50.1109, 8.6821),
        ("Cologne", "Germany", 50.9375, 6.9603),
        ("Stuttgart", "Germany", 48.7758, 9.1829),
        ("Heidelberg", "Germany", 49.3988, 8.6724),

        ("Amsterdam", "Netherlands", 52.3676, 4.9041),
        ("Rotterdam", "Netherlands", 51.9244, 4.4777),
        ("Delft", "Netherlands", 52.0116, 4.3571),
        ("Eindhoven", "Netherlands", 51.4416, 5.4697),

        ("Zurich", "Switzerland", 47.3769, 8.5417),
        ("Geneva", "Switzerland", 46.2044, 6.1432),
        ("Lausanne", "Switzerland", 46.5197, 6.6323),

        ("Stockholm", "Sweden", 59.3293, 18.0686),
        ("Gothenburg", "Sweden", 57.7089, 11.9746),
        ("Copenhagen", "Denmark", 55.6761, 12.5683),
        ("Helsinki", "Finland", 60.1699, 24.9384),
        ("Oslo", "Norway", 59.9139, 10.7522),

        ("Madrid", "Spain", 40.4168, -3.7038),
        ("Barcelona", "Spain", 41.3874, 2.1686),
        ("Lisbon", "Portugal", 38.7223, -9.1393),
        ("Rome", "Italy", 41.9028, 12.4964),
        ("Milan", "Italy", 45.4642, 9.1900),
        ("Turin", "Italy", 45.0703, 7.6869),

        ("Vienna", "Austria", 48.2082, 16.3738),
        ("Prague", "Czech Republic", 50.0755, 14.4378),
        ("Warsaw", "Poland", 52.2297, 21.0122),
        ("Krakow", "Poland", 50.0647, 19.9450),
        ("Budapest", "Hungary", 47.4979, 19.0402),
        ("Bucharest", "Romania", 44.4268, 26.1025),
        ("Dublin", "Ireland", 53.3498, -6.2603),
        ("Brussels", "Belgium", 50.8503, 4.3517),
        ("Athens", "Greece", 37.9838, 23.7275),

        ("Moscow", "Russia", 55.7558, 37.6173),
        ("Saint Petersburg", "Russia", 59.9343, 30.3351),

        ("Istanbul", "Turkey", 41.0082, 28.9784),
        ("Ankara", "Turkey", 39.9334, 32.8597),

        ("Tel Aviv", "Israel", 32.0853, 34.7818),
        ("Jerusalem", "Israel", 31.7683, 35.2137),
        ("Haifa", "Israel", 32.7940, 34.9896),

        ("Dubai", "United Arab Emirates", 25.2048, 55.2708),
        ("Abu Dhabi", "United Arab Emirates", 24.4539, 54.3773),
        ("Riyadh", "Saudi Arabia", 24.7136, 46.6753),

        ("Beijing", "China", 39.9042, 116.4074),
        ("Shanghai", "China", 31.2304, 121.4737),
        ("Shenzhen", "China", 22.5431, 114.0579),
        ("Hangzhou", "China", 30.2741, 120.1551),
        ("Guangzhou", "China", 23.1291, 113.2644),
        ("Chengdu", "China", 30.5728, 104.0668),
        ("Nanjing", "China", 32.0603, 118.7969),
        ("Wuhan", "China", 30.5928, 114.3055),
        ("Xi'an", "China", 34.3416, 108.9398),
        ("Hefei", "China", 31.8206, 117.2272),
        ("Suzhou", "China", 31.2990, 120.5853),
        ("Dalian", "China", 38.9140, 121.6147),
        ("Tianjin", "China", 39.3434, 117.3616),
        ("Hong Kong", "China", 22.3193, 114.1694),

        ("Tokyo", "Japan", 35.6762, 139.6503),
        ("Osaka", "Japan", 34.6937, 135.5023),
        ("Kyoto", "Japan", 35.0116, 135.7681),
        ("Nagoya", "Japan", 35.1815, 136.9066),
        ("Tsukuba", "Japan", 36.0835, 140.0766),

        ("Seoul", "South Korea", 37.5665, 126.9780),
        ("Busan", "South Korea", 35.1796, 129.0756),
        ("Daejeon", "South Korea", 36.3504, 127.3845),

        ("Taipei", "Taiwan", 25.0330, 121.5654),
        ("Hsinchu", "Taiwan", 24.8138, 120.9675),

        ("Singapore", "Singapore", 1.3521, 103.8198),

        ("Bengaluru", "India", 12.9716, 77.5946),
        ("Mumbai", "India", 19.0760, 72.8777),
        ("New Delhi", "India", 28.6139, 77.2090),
        ("Delhi", "India", 28.7041, 77.1025),
        ("Hyderabad", "India", 17.3850, 78.4867),
        ("Chennai", "India", 13.0827, 80.2707),
        ("Pune", "India", 18.5204, 73.8567),
        ("Kolkata", "India", 22.5726, 88.3639),

        ("Jakarta", "Indonesia", -6.2088, 106.8456),
        ("Bangkok", "Thailand", 13.7563, 100.5018),
        ("Kuala Lumpur", "Malaysia", 3.1390, 101.6869),
        ("Ho Chi Minh City", "Vietnam", 10.8231, 106.6297),
        ("Hanoi", "Vietnam", 21.0278, 105.8342),
        ("Manila", "Philippines", 14.5995, 120.9842),

        ("Sydney", "Australia", -33.8688, 151.2093),
        ("Melbourne", "Australia", -37.8136, 144.9631),
        ("Brisbane", "Australia", -27.4698, 153.0251),
        ("Perth", "Australia", -31.9505, 115.8605),
        ("Canberra", "Australia", -35.2809, 149.1300),
        ("Auckland", "New Zealand", -36.8485, 174.7633),

        ("Toronto", "Canada", 43.6532, -79.3832),
        ("Vancouver", "Canada", 49.2827, -123.1207),
        ("Montreal", "Canada", 45.5017, -73.5673),
        ("Ottawa", "Canada", 45.4215, -75.6972),
        ("Calgary", "Canada", 51.0447, -114.0719),
        ("Edmonton", "Canada", 53.5461, -113.4938),
        ("Waterloo", "Canada", 43.4643, -80.5204),

        ("Sao Paulo", "Brazil", -23.5505, -46.6333),
        ("Rio de Janeiro", "Brazil", -22.9068, -43.1729),
        ("Mexico City", "Mexico", 19.4326, -99.1332),
        ("Buenos Aires", "Argentina", -34.6037, -58.3816),
        ("Santiago", "Chile", -33.4489, -70.6693),
        ("Bogota", "Colombia", 4.7110, -74.0721),
        ("Lima", "Peru", -12.0464, -77.0428),

        ("Cairo", "Egypt", 30.0444, 31.2357),
        ("Nairobi", "Kenya", -1.2921, 36.8219),
        ("Lagos", "Nigeria", 6.5244, 3.3792),
        ("Cape Town", "South Africa", -33.9249, 18.4241),
        ("Johannesburg", "South Africa", -26.2041, 28.0473),
    ]

    for city, country, lat, lon in top_cities:
        CITY_DICT[city.lower()] = (city, country, lat, lon)

    print(f"  Built hardcoded city dictionary: {len(CITY_DICT)} cities")


# ── Text cleaning ──────────────────────────────────────────────────────────────

def _strip_emoji(text):
    """Remove emoji and other non-Latin/CJK symbols."""
    return "".join(
        c for c in text
        if unicodedata.category(c)[0] in ("L", "M", "N", "P", "Z")
    )


def clean_location(raw: str) -> Optional[str]:
    """Normalise a raw location string. Returns None if invalid."""
    if not raw or not raw.strip():
        return None

    text = raw.strip()
    text = _strip_emoji(text)
    text = text.strip(" ,.-;:!?")

    if len(text) < 2:
        return None

    if INVALID_RE.search(text):
        return None

    return text


def match_city(cleaned: str) -> Optional[Tuple[str, str, float, float, str]]:
    """
    Try to match a cleaned location string to the city dictionary.
    Returns (city, country, lat, lon, confidence) or None.
    """
    if not cleaned:
        return None

    lower = cleaned.lower().strip()

    # 1. Direct abbreviation lookup
    if lower in ABBREVIATIONS:
        expanded = ABBREVIATIONS[lower].lower()
        if expanded in CITY_DICT:
            city, country, lat, lon = CITY_DICT[expanded]
            return (city, country, lat, lon, "high")

    # 2. Exact match
    if lower in CITY_DICT:
        city, country, lat, lon = CITY_DICT[lower]
        return (city, country, lat, lon, "high")

    # 3. Try first part before comma (e.g. "London, UK" → "london")
    parts = [p.strip() for p in lower.split(",")]
    for part in parts:
        part_clean = part.strip()
        if part_clean in ABBREVIATIONS:
            part_clean = ABBREVIATIONS[part_clean].lower()
        if part_clean in CITY_DICT:
            city, country, lat, lon = CITY_DICT[part_clean]
            return (city, country, lat, lon, "high")

    # 4. Try parts split by "/" or "&"
    for sep in ["/", "&", " - ", " and "]:
        if sep in lower:
            sub_parts = [p.strip() for p in lower.split(sep)]
            for sp in sub_parts:
                if sp in ABBREVIATIONS:
                    sp = ABBREVIATIONS[sp].lower()
                if sp in CITY_DICT:
                    city, country, lat, lon = CITY_DICT[sp]
                    return (city, country, lat, lon, "medium")

    # 5. Substring search: check if any city name appears in the text
    for key, (city, country, lat, lon) in CITY_DICT.items():
        if len(key) >= 4 and key in lower:
            return (city, country, lat, lon, "medium")

    return None


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Step 3b: Clean locations & map to cities")
    print("=" * 60)

    _build_city_dict()

    # --- Collect raw locations ---
    records = []

    # GitHub owners
    gh_loc_path = DATA_RAW / "github" / "github_owner_locations.csv"
    if gh_loc_path.exists():
        gh = pd.read_csv(gh_loc_path, dtype=str).fillna("")
        for _, row in gh.iterrows():
            records.append({
                "entity_id": row["login"],
                "entity_type": "github_" + (row.get("type", "User")).lower(),
                "raw_location": row["location"],
                "platform": "GitHub",
            })
        print(f"  GitHub owner records: {len(gh)}")

    # HF authors – extract unique authors from prominent HF projects
    hf_path = DATA_RAW / "huggingface" / "hf_candidates.csv"
    if hf_path.exists():
        hf = pd.read_csv(hf_path, dtype=str).fillna("")
        hf_prom = hf[hf["prominent_flag"] == "1"]
        hf_authors = hf_prom[["author"]].drop_duplicates()
        for _, row in hf_authors.iterrows():
            author = row["author"]
            if author:
                records.append({
                    "entity_id": author,
                    "entity_type": "hf_author",
                    "raw_location": "",  # HF API doesn't expose user location
                    "platform": "HuggingFace",
                })
        print(f"  HF author records: {len(hf_authors)}")

    print(f"  Total raw records: {len(records)}\n")

    # --- Clean and match ---
    results = []
    stats = {"total": 0, "empty": 0, "invalid": 0, "matched": 0, "unmatched": 0}

    for rec in records:
        stats["total"] += 1
        raw = rec["raw_location"]

        if not raw.strip():
            stats["empty"] += 1
            results.append({**rec, "cleaned_location": "",
                            "matched_city": "", "country": "",
                            "lat": "", "lon": "", "confidence": "none"})
            continue

        cleaned = clean_location(raw)
        if cleaned is None:
            stats["invalid"] += 1
            results.append({**rec, "cleaned_location": raw,
                            "matched_city": "", "country": "",
                            "lat": "", "lon": "", "confidence": "none"})
            continue

        match = match_city(cleaned)
        if match:
            city, country, lat, lon, conf = match
            stats["matched"] += 1
            results.append({**rec, "cleaned_location": cleaned,
                            "matched_city": city, "country": country,
                            "lat": lat, "lon": lon, "confidence": conf})
        else:
            stats["unmatched"] += 1
            results.append({**rec, "cleaned_location": cleaned,
                            "matched_city": "", "country": "",
                            "lat": "", "lon": "", "confidence": "low"})

    # --- Save ---
    out_path = DATA_PROCESSED / "location_mapping.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_out = pd.DataFrame(results)
    df_out.to_csv(out_path, index=False)
    print(f"✅ Saved {len(results)} rows → {out_path}")

    # --- Summary ---
    print(f"\n📊 Location matching summary:")
    print(f"   Total:     {stats['total']}")
    print(f"   Empty:     {stats['empty']}")
    print(f"   Invalid:   {stats['invalid']}")
    print(f"   Matched:   {stats['matched']}")
    print(f"   Unmatched: {stats['unmatched']}")

    if stats["matched"] > 0:
        df_matched = df_out[df_out["matched_city"] != ""]
        city_counts = df_matched["matched_city"].value_counts()
        print(f"\n📊 Top 20 cities by entity count:")
        print(city_counts.head(20).to_string())

        conf_dist = df_matched["confidence"].value_counts()
        print(f"\n📊 Confidence distribution:")
        print(conf_dist.to_string())


if __name__ == "__main__":
    main()
