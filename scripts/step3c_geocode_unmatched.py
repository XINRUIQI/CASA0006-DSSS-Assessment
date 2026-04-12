"""
Step 3c – Geocode unmatched locations via Nominatim (free, 1 req/sec).

Takes the `location_mapping.csv` from step3b, finds rows where
matched_city is empty but cleaned_location is not, and tries to
geocode them with OpenStreetMap Nominatim.

Then re-matches geocoded results to the nearest city in our dictionary.

Output: updates data/processed/location_mapping.csv in place.
"""

import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DATA_PROCESSED

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "CASA0006-Research/1.0 (academic project)"}

MAX_UNIQUE_QUERIES = 2000

# ── Non-English → English normalisation maps ───────────────────────────────────
COUNTRY_NORM = {
    "中国": "China", "中华人民共和国": "China",
    "日本": "Japan",
    "대한민국": "South Korea", "한국": "South Korea",
    "Deutschland": "Germany", "Bundesrepublik Deutschland": "Germany",
    "République française": "France",
    "Italia": "Italy",
    "España": "Spain",
    "Россия": "Russia", "Российская Федерация": "Russia",
    "Brasil": "Brazil",
    "Türkiye": "Turkey",
    "Ελλάς": "Greece",
    "Österreich": "Austria",
    "Schweiz/Suisse/Svizzera/Svizra": "Switzerland",
    "Suisse": "Switzerland", "Schweiz": "Switzerland",
    "Nederland": "Netherlands",
    "Polska": "Poland",
    "Česko": "Czech Republic", "Česká republika": "Czech Republic",
    "Magyarország": "Hungary",
    "România": "Romania",
    "Україна": "Ukraine",
    "ישראל": "Israel",
    "ایران": "Iran",
    "مصر": "Egypt",
    "السعودية": "Saudi Arabia",
    "الإمارات العربية المتحدة": "United Arab Emirates",
    "台灣": "Taiwan", "臺灣": "Taiwan",
    "香港": "China",
    "Việt Nam": "Vietnam",
    "ประเทศไทย": "Thailand",
    "Suomi / Finland": "Finland", "Suomi": "Finland",
    "Sverige": "Sweden",
    "Norge": "Norway",
    "Danmark": "Denmark",
    "Éire / Ireland": "Ireland", "Éire": "Ireland",
    "Belgique - België": "Belgium", "België / Belgique / Belgien": "Belgium",
    "México": "Mexico",
    "Perú": "Peru",
    "भारत": "India",
    "Pilipinas": "Philippines",
    "Ísland": "Iceland",
    "Lietuva": "Lithuania", "Latvija": "Latvia", "Eesti": "Estonia",
    "Slovensko": "Slovakia", "Slovenija": "Slovenia",
    "Hrvatska": "Croatia", "Србија": "Serbia", "България": "Bulgaria",
    "საქართველო": "Georgia",
    "Қазақстан": "Kazakhstan", "Беларусь": "Belarus",
    "پاکستان": "Pakistan",
    "نेपाल": "Nepal", "नेपाल": "Nepal",
    "বাংলাদেশ": "Bangladesh",
    "Maroc ⵍⵎⵖⵔⵉⴱ المغرب": "Morocco",
    "ኢትዮጵያ": "Ethiopia",
    "မြန်မာ": "Myanmar",
    "Crna Gora / Црна Гора": "Montenegro",
    "Oʻzbekiston": "Uzbekistan",
    "العراق": "Iraq",
    "Κύπρος - Kıbrıs": "Cyprus",
}

CITY_NORM = {
    "成都市": "Chengdu", "昌平区": "Beijing", "深圳市": "Shenzhen",
    "广州市": "Guangzhou", "武汉市": "Wuhan", "南京市": "Nanjing",
    "西安市": "Xi'an", "合肥市": "Hefei", "苏州市": "Suzhou",
    "大连市": "Dalian", "天津市": "Tianjin", "杭州市": "Hangzhou",
    "上海市": "Shanghai", "北京市": "Beijing", "重庆市": "Chongqing",
    "长沙市": "Changsha", "哈尔滨市": "Harbin", "济南市": "Jinan",
    "青岛市": "Qingdao", "郑州市": "Zhengzhou",
    "شهر تهران": "Tehran", "القاهرة": "Cairo",
    "서울": "Seoul",
    "東京都": "Tokyo", "大阪市": "Osaka", "京都市": "Kyoto",
    "台北": "Taipei", "新竹": "Hsinchu",
    "Москва": "Moscow", "Санкт-Петербург": "Saint Petersburg",
    "München": "Munich", "Köln": "Cologne",
    "Zürich": "Zurich", "Genève": "Geneva",
    "Praha": "Prague", "Wien": "Vienna",
    "Αθήνα": "Athens", "İstanbul": "Istanbul",
    "لاہور": "Lahore",
    "София": "Sofia",
    "کراچی ڈویژن": "Karachi",
    "काठमाडौँ महानगरपालिका": "Kathmandu",
    "اسلام آباد": "Islamabad",
    "Львів": "Lviv",
    "广东省": "Guangzhou",
    "沈阳市": "Shenyang",
    "昆明市": "Kunming",
    "Wrocław": "Wroclaw",
    "Thành phố Hồ Chí Minh": "Ho Chi Minh City",
    "Thành phố Hà Nội": "Hanoi",
    "København": "Copenhagen",
    "Београд": "Belgrade",
    "珠海市": "Zhuhai",
    "አዲስ አበባ أديس أبابا": "Addis Ababa",
    "长春市": "Changchun",
    "Nürnberg": "Nuremberg",
    "دبي": "Dubai",
    "厦门市": "Xiamen",
}


def geocode_nominatim(query):
    """Return (city, country, lat, lon) or None."""
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
        "accept-language": "en",
    }
    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None
        results = resp.json()
        if not results:
            return None
        r = results[0]
        addr = r.get("address", {})
        city = (addr.get("city")
                or addr.get("town")
                or addr.get("village")
                or addr.get("state")
                or addr.get("county")
                or "")
        country = addr.get("country", "")
        lat = float(r.get("lat", 0))
        lon = float(r.get("lon", 0))
        if city:
            return (city, country, lat, lon)
    except Exception:
        pass
    return None


def main():
    print("=" * 60)
    print("Step 3c: Geocode unmatched locations (Nominatim)")
    print("=" * 60)

    path = DATA_PROCESSED / "location_mapping.csv"
    df = pd.read_csv(path, dtype=str).fillna("")

    unmatched = df[(df["matched_city"] == "") & (df["cleaned_location"] != "")]
    print(f"  Total rows: {len(df)}")
    print(f"  Unmatched with cleaned_location: {len(unmatched)}")

    if len(unmatched) == 0:
        print("  Nothing to geocode.")
        return

    # Get unique queries, sorted by frequency
    query_counts = unmatched["cleaned_location"].value_counts()
    unique_queries = query_counts.head(MAX_UNIQUE_QUERIES).index.tolist()
    print(f"  Unique queries to geocode: {len(unique_queries)}\n")

    cache = {}
    success = 0
    for i, q in enumerate(unique_queries, 1):
        result = geocode_nominatim(q)
        cache[q] = result
        status = f"→ {result[0]}, {result[1]}" if result else "→ (no result)"
        if result:
            success += 1
        if i % 50 == 0 or i <= 5:
            print(f"  [{i}/{len(unique_queries)}] '{q[:40]}' {status}")
        time.sleep(1.1)  # Nominatim rate limit

    print(f"\n  Geocoded successfully: {success}/{len(unique_queries)}")

    # Apply geocoding results and normalise non-English names in a single pass
    updated, fixed_c, fixed_m = 0, 0, 0
    for idx, row in df.iterrows():
        city = row["matched_city"]
        country = row["country"]

        if city == "" and row["cleaned_location"] in cache:
            result = cache[row["cleaned_location"]]
            if result:
                city, country, lat, lon = result
                df.at[idx, "matched_city"] = city
                df.at[idx, "country"] = country
                df.at[idx, "lat"] = str(lat)
                df.at[idx, "lon"] = str(lon)
                df.at[idx, "confidence"] = "medium"
                updated += 1

        if country in COUNTRY_NORM:
            df.at[idx, "country"] = COUNTRY_NORM[country]
            fixed_c += 1
        if city in CITY_NORM:
            df.at[idx, "matched_city"] = CITY_NORM[city]
            fixed_m += 1

    print(f"\n  Normalised {fixed_c} country names, {fixed_m} city names to English")

    df.to_csv(path, index=False)
    print(f"✅ Updated {updated} rows, saved → {path}")

    # Summary
    matched = df[df["matched_city"] != ""]
    print(f"\n📊 After geocoding + normalisation:")
    print(f"   Matched:   {len(matched)} / {len(df)}")
    print(f"   Unmatched: {len(df) - len(matched)}")


if __name__ == "__main__":
    main()
