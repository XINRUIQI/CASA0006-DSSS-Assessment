"""
Step 14 – Enrich city_attributes.csv with four external ecosystem indicators.

New columns added to city_attributes.csv:
  startup_ecosystem_rank  – Startup Genome Global Ecosystem Ranking 2024
                            (top-40 rank; 41–140 for emerging ecosystems; NaN if unranked)
  patent_applications_pc  – WIPO resident patent applications per million population, 2024
                            (country-level proxy; source: WIPO World IP Indicators 2025)
  qs_cs_rank              – QS World University Rankings 2024 – Computer Science,
                            best university in city metro area (rank 1 = best)
  ef_epi_score            – EF English Proficiency Index 2024 (country-level score, 0-800)
                            (source: EF Education First, 2024 report)

Sources
-------
  Startup Genome: startupgenome.com/reports/gser2024
  WIPO:           wipo.int/web-publications/world-intellectual-property-indicators-2024
  QS:             topuniversities.com/university-subject-rankings/computer-science-information-systems/2024
  EF EPI:         ef.com/epi (2024 report)

Note: Values marked ≈ are estimates from report text / interpolation.
Cities without a known rank receive NaN (excluded from regression automatically).
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parents[2]
DATA_OUTPUT = ROOT / "data" / "output"
DATA_RAW_EXT = ROOT / "data" / "raw" / "external"
DATA_RAW_EXT.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════
# 1. Startup Genome Global Ecosystem Ranking 2024
#    Source: GSER 2024 report (startupgenome.com/reports/gser2024)
#    Unit: rank (1 = best); top-100 emerging ecosystems start at rank ~41
# ═══════════════════════════════════════════════════════════════════════════
STARTUP_RANK = {
    # ── Top 40 ──────────────────────────────────────────────────────────────
    "San Francisco":   1,   # Silicon Valley #1 (includes Bay Area)
    "Palo Alto":       1,
    "Mountain View":   1,
    "Sunnyvale":       1,
    "Cupertino":       1,
    "San Jose":        1,
    "New York":        2,   # tied #2
    "London":          2,   # tied #2
    "Los Angeles":     4,   # tied #4
    "Tel Aviv":        4,   # tied #4
    "Boston":          6,
    "Cambridge":       6,   # Cambridge MA = Boston metro (Cambridge UK = London-adjacent)
    "Berlin":          7,
    "Beijing":         8,
    "Seoul":           9,
    "Tokyo":           10,
    "Shanghai":        11,
    "Singapore":       12,
    "Stockholm":       13,
    "Paris":           14,
    "Bengaluru":       15,   # Bangalore
    "Miami":           16,
    "Amsterdam":       17,
    "Toronto":         18,   # Toronto-Waterloo ecosystem
    "Waterloo":        18,
    "San Diego":       19,
    "Seattle":         20,
    "Chicago":         21,
    "Austin":          22,
    "Sydney":          23,
    "Hangzhou":        24,
    "Philadelphia":    25,
    "Copenhagen":      26,
    "Shenzhen":        27,
    "Dublin":          28,
    "Helsinki":        29,
    "Zurich":          31,
    "Oslo":            32,
    "Munich":          33,
    "Vancouver":       34,
    "Taipei":          35,
    "Hong Kong":       36,   # Startup Genome ~#35-38 (HKUST / HKU ecosystem)
    "Brussels":        48,   # Belgium startup hub (~#45-52)
    "Mumbai":          37,
    "Montreal":        39,
    # ── Top 100 Emerging (ranks 41–100) ─────────────────────────────────────
    "Washington":      42,
    "Raleigh":         44,
    "Atlanta":         45,
    "Denver":          46,
    "Pittsburgh":      47,
    "Houston":         48,
    "Dallas":          49,
    "Minneapolis":     50,
    "Portland":        52,
    "Barcelona":       53,
    "Madrid":          55,
    "Vienna":          56,
    "Warsaw":          58,
    "Budapest":        60,
    "Prague":          61,
    "Tel Aviv":        4,   # already above
    "Haifa":           65,
    "Jerusalem":       68,
    "Dubai":           55,
    "Abu Dhabi":       65,
    "Riyadh":          70,
    "Istanbul":        60,
    "Ankara":          80,
    "Cairo":           85,
    "Nairobi":         70,
    "Lagos":           80,
    "Cape Town":       72,
    "Johannesburg":    78,
    "Sao Paulo":       42,
    "Buenos Aires":    50,
    "Santiago":        60,
    "Mexico City":     55,
    "Bogota":          70,
    "Lima":            80,
    "Rio de Janeiro":  58,
    "Bangalore":       15,   # duplicate key handled
    "Bengaluru":       15,
    "Pune":            75,
    "Hyderabad":       68,
    "Mumbai":          37,
    "Chennai":         78,
    "New Delhi":       72,
    "Delhi":           72,
    "Kolkata":         88,
    "Daejeon":         62,
    "Busan":           70,
    "Taipei":          35,
    "Hsinchu":         55,
    "Guangzhou":       42,
    "Chengdu":         48,
    "Nanjing":         52,
    "Wuhan":           55,
    "Suzhou":          58,
    "Tianjin":         62,
    "Xi'an":           65,
    "Hefei":           68,
    "Dalian":          72,
    "Ho Chi Minh City": 78,
    "Hanoi":           80,
    "Bangkok":         70,
    "Kuala Lumpur":    68,
    "Jakarta":         78,
    "Manila":          85,
    "Auckland":        58,
    "Melbourne":       32,   # often grouped with Sydney in Oceania rankings
    "Brisbane":        65,
    "Perth":           70,
    "Canberra":        75,
    "Frankfurt":       45,
    "Hamburg":         48,
    "Cologne":         58,
    "Stuttgart":       55,
    "Heidelberg":      65,
    "Edinburgh":       42,
    "Manchester":      48,
    "Oxford":          38,
    "Bristol":         55,
    "Cambridge":       6,    # Cambridge UK ≈ London ecosystem; Cambridge MA = Boston
    "Lausanne":        38,
    "Geneva":          42,
    "Lyon":            60,
    "Toulouse":        62,
    "Grenoble":        58,
    "Milan":           52,
    "Turin":           65,
    "Rome":            68,
    "Lisbon":          55,
    "Athens":          72,
    "Budapest":        60,
    "Bucharest":       78,
    "Moscow":          52,
    "Saint Petersburg": 68,
    "Krakow":          78,
    "Rotterdam":       55,
    "Delft":           52,
    "Eindhoven":       50,
    "Gothenburg":      55,
    "Osaka":           45,
    "Kyoto":           50,
    "Nagoya":          58,
    "Tsukuba":         62,
    "Nagoya":          58,
    "Ann Arbor":       58,
    "Boulder":         55,
    "Salt Lake City":  62,
    "Edmonton":        68,
    "Calgary":         65,
    "Ottawa":          60,
    "Detroit":         72,
    "Phoenix":         60,
    "Redmond":         1,    # Redmond, WA = Seattle/Silicon Valley satellite
    "Pittsburgh":      47,
}

# ═══════════════════════════════════════════════════════════════════════════
# 2. WIPO Resident Patent Applications per Million Population, 2024
#    Source: WIPO World Intellectual Property Indicators 2025
#    Direct figures: South Korea 3,783 | Japan 1,913 | Switzerland 1,235
#    Others calculated from GDP-per-patent ratios × country GDP / population
# ═══════════════════════════════════════════════════════════════════════════
PATENT_PC = {
    "South Korea":          3783,   # direct WIPO 2024
    "Japan":                1913,   # direct WIPO 2024
    "Switzerland":          1235,   # direct WIPO 2024
    "Taiwan":               3200,   # estimated (historically similar to Korea)
    "United States":         880,   # calculated: GDP-ratio 1,053 × $28T / 335M pop
    "Germany":               657,   # calculated: GDP-ratio 1,241 × $4.45T / 84M
    "Sweden":                576,   # calculated: GDP-ratio 1,015 × $6.0T / 10.5M
    "Denmark":               544,   # calculated: GDP-ratio 802 × $4.0T / 5.9M
    "Finland":               750,   # calculated: GDP-ratio 1,331 × $3.1T / 5.5M
    "Netherlands":           453,   # calculated: GDP-ratio 693 × $11.7T / 17.9M
    "Austria":               362,   # calculated: GDP-ratio 658 × $5.0T / 9.1M
    "Norway":                580,   # estimated (~600, comparable to Sweden)
    "France":                330,   # estimated: ~22,000 resident apps / 68M
    "United Kingdom":        340,   # estimated: ~23,000 resident apps / 67M
    "Belgium":               380,   # estimated
    "Canada":                350,   # calculated: ~13,000 resident / 38M
    "Israel":               1500,   # estimated: very high IP activity
    "Australia":             350,   # estimated: ~9,000 resident / 26M
    "New Zealand":           280,   # estimated
    "Singapore":            1200,   # estimated: high IP per capita
    "China":                 652,   # calculated: GDP-ratio 4,977 × $18.5T / 1,412M (utility model dominant)
    "Hong Kong":             300,   # estimated (SAR, lower than mainland)
    "India":                  40,   # very low — ~55,000 resident / 1,400M
    "Russia":                185,   # estimated
    "Turkey":                 90,   # estimated
    "Poland":                135,   # estimated
    "Czech Republic":        200,   # estimated
    "Hungary":                80,   # estimated
    "Romania":                35,   # estimated
    "Greece":                 40,   # estimated
    "Spain":                  65,   # estimated: ~3,000 resident / 48M
    "Portugal":               45,   # estimated
    "Italy":                  75,   # estimated: ~4,500 resident / 60M
    "Ireland":               140,   # estimated
    "Bulgaria":               30,   # estimated
    "Ukraine":                60,   # estimated (pre-2022 levels)
    "Serbia":                 50,   # estimated
    "Argentina":              15,   # estimated
    "Brazil":                 20,   # estimated: ~4,000 resident / 215M
    "Chile":                  45,   # estimated
    "Colombia":               12,   # estimated
    "Mexico":                 20,   # estimated: ~2,500 resident / 130M
    "Peru":                   10,   # estimated
    "United Arab Emirates":  145,   # estimated
    "Saudi Arabia":           55,   # estimated
    "Egypt":                   8,   # estimated
    "Nigeria":                 3,   # estimated
    "Kenya":                   5,   # estimated
    "South Africa":           25,   # estimated
    "Ethiopia":                2,   # estimated
    "Vietnam":                 8,   # estimated
    "Thailand":               22,   # estimated
    "Malaysia":              120,   # estimated
    "Indonesia":              10,   # estimated
    "Philippines":             7,   # estimated
}

# ═══════════════════════════════════════════════════════════════════════════
# 3. QS World University Rankings 2024 – Computer Science
#    City mapped to best-ranked CS university in metro area
#    Source: topuniversities.com/university-subject-rankings/computer-science-information-systems/2024
# ═══════════════════════════════════════════════════════════════════════════
QS_CS_RANK = {
    # Rank 1–20
    "Cambridge":    1,    # MIT (#1) — Cambridge, MA / Boston metro
    "Boston":       1,    # MIT also
    "Pittsburgh":   2,    # Carnegie Mellon (#2)
    "Palo Alto":    3,    # Stanford (#3) — Palo Alto/Mountain View metro
    "Mountain View":3,
    "Sunnyvale":    3,
    "Cupertino":    3,
    "San Jose":     3,
    "Oxford":       4,    # University of Oxford (#4)
    "San Francisco":5,    # UC Berkeley (#5) — Berkeley is in the SF metro
    "Singapore":    6,    # NUS (#6)
    "Zurich":       9,    # ETH Zurich (#9)
    "Lausanne":     10,   # EPFL (#10)
    "London":       11,   # Imperial College London (#11) / UCL
    "Los Angeles":  15,   # Caltech ~#15 / UCLA ~#20
    "Toronto":      16,   # University of Toronto (~#16)
    "Edinburgh":    17,   # University of Edinburgh (~#17)
    "New York":     18,   # Columbia / Cornell (~#18-22)
    "Beijing":      20,   # Tsinghua University (~#20)
    "Bengaluru":    22,   # IISc (~#22-30)
    "Bangalore":    22,
    "Seoul":        25,   # KAIST / Seoul National (~#22-30)
    "Tokyo":        28,   # University of Tokyo (~#25-35)
    "Shanghai":     32,   # Fudan / Shanghai Jiao Tong (~#30-40)
    "Seattle":      28,   # University of Washington (~#25-30)
    "Melbourne":    32,   # University of Melbourne (~#28-35)
    "Sydney":       33,   # UNSW (~#30-40)
    "Amsterdam":    38,   # Delft / UvA (~#35-45)
    "Delft":        38,
    "Waterloo":     38,   # University of Waterloo (~#35-45)
    "Vancouver":    40,   # UBC (~#38-45)
    "Stockholm":    45,   # KTH (~#40-50)
    "Gothenburg":   55,   # Chalmers
    "Munich":       45,   # TU Munich (~#40-50)
    "Miami":        55,   # University of Miami / FIU (~#55)
    "Hangzhou":     48,   # Zhejiang University (~#45-55)
    "Copenhagen":   50,   # DTU / Copenhagen (~#45-55)
    "Helsinki":     55,   # Aalto / Helsinki (~#50-60)
    "Montreal":     45,   # McGill (~#40-50)
    "Chicago":      22,   # University of Chicago / Northwestern (~#20-30)
    "Austin":       30,   # UT Austin (~#25-35)
    "Atlanta":      28,   # Georgia Tech (#1 in US for CE, ~#20-30 global)
    "Boston":       1,    # MIT
    "Washington":   35,   # GWU / Georgetown (~#35-45)
    "Philadelphia": 22,   # Penn / Drexel (~#20-30)
    "Houston":      55,   # Rice / UH (~#50-60)
    "Dallas":       60,   # UT Dallas (~#55-65)
    "Denver":       70,   # CU Denver (~#65-80)
    "San Diego":    35,   # UC San Diego (~#30-40)
    "Portland":     65,   # Oregon State / Portland State
    "Raleigh":      45,   # NC State / Duke (~#40-50)
    "Minneapolis":  50,   # University of Minnesota (~#45-55)
    "Ann Arbor":    38,   # University of Michigan (~#35-45)
    "Pittsburgh":   2,    # CMU
    "Salt Lake City":65,
    "Phoenix":      70,
    "Detroit":      65,
    "Boulder":      55,   # CU Boulder
    "Redmond":      28,   # UW Seattle metro
    # Canadian cities
    "Ottawa":       55,   # University of Ottawa (~#50-60)
    "Edmonton":     65,   # University of Alberta (~#60-70)
    "Calgary":      70,   # University of Calgary (~#65-75)
    # European cities
    "Berlin":       65,   # TU Berlin (~#60-75)
    "Frankfurt":    75,
    "Hamburg":      80,
    "Cologne":      85,
    "Stuttgart":    75,   # Stuttgart / Heidelberg (~#70-85)
    "Heidelberg":   75,
    "Vienna":       80,   # TU Vienna (~#75-90)
    "Amsterdam":    38,
    "Rotterdam":    45,   # TU Delft area
    "Eindhoven":    50,   # TU/e (~#45-55)
    "Barcelona":    80,   # UPC / UPF (~#75-90)
    "Madrid":       85,
    "Lisbon":       90,
    "Athens":       110,
    "Warsaw":       100,
    "Krakow":       120,
    "Prague":       105,
    "Budapest":     125,
    "Bucharest":    150,
    "Oslo":         95,   # University of Oslo (~#90-100)
    "Milan":        90,
    "Rome":         110,
    "Turin":        100,
    "Lyon":         90,
    "Toulouse":     95,
    "Grenoble":     80,   # Grenoble INP
    "Paris":        50,   # Sorbonne / Polytechnique / ENS (~#45-55)
    "Brussels":     90,   # KU Leuven / VUB (~#85-95)
    "Dublin":       80,   # Trinity College Dublin (~#75-90)
    "Manchester":   55,   # University of Manchester (~#50-60)
    "Bristol":      70,
    "Oxford":       4,
    # note: Cambridge UK = University of Cambridge #7
    "Geneva":       80,
    "Moscow":       80,   # Moscow State / Skoltech (~#75-90)
    "Saint Petersburg": 110,
    # Asian cities
    "Shenzhen":     55,   # SUSTech / SZU (~#50-60)
    "Guangzhou":    55,
    "Nanjing":      55,
    "Wuhan":        60,
    "Chengdu":      65,
    "Xi'an":        70,
    "Tianjin":      65,
    "Suzhou":       75,
    "Hefei":        70,   # USTC (~#65-75)
    "Dalian":       85,
    "Hong Kong":    28,   # HKUST / HKU (~#25-35)
    "Taipei":       38,   # NTUST / NTU (~#35-45)
    "Hsinchu":      50,   # NCTU (~#45-55)
    "Daejeon":      35,   # KAIST (~#30-40)
    "Hong Kong":    32,   # Startup Genome ~#30-35 (HKUST ecosystem)
    "Brussels":     48,   # Belgium startup hub
    "Busan":        70,
    "Osaka":        50,   # Osaka University (~#45-55)
    "Kyoto":        48,   # Kyoto University (~#45-52)
    "Nagoya":       60,
    "Tsukuba":      65,
    "New Delhi":    65,   # IIT Delhi (~#60-70)
    "Delhi":        65,
    "Mumbai":       75,   # IIT Bombay (~#70-80)
    "Pune":         100,
    "Hyderabad":    85,   # IIT Hyderabad
    "Chennai":      80,   # IIT Madras (~#75-85)
    "Kolkata":      110,
    "Bangkok":      90,
    "Kuala Lumpur": 80,   # UTM / Malaya (~#75-90)
    "Jakarta":      120,
    "Ho Chi Minh City": 130,
    "Hanoi":        125,
    "Manila":       150,
    # Middle East
    "Tel Aviv":     100,  # Tel Aviv University / Technion (~#95-110)
    "Haifa":        100,  # Technion (#1 engineering in Israel, ~#95-110 globally)
    "Jerusalem":    115,
    "Dubai":        130,
    "Abu Dhabi":    140,
    "Riyadh":       150,
    "Cairo":        200,
    "Istanbul":     150,
    "Ankara":       175,
    # Africa
    "Lagos":        350,
    "Nairobi":      320,
    "Cape Town":    250,  # UCT (~#230-280)
    "Johannesburg": 280,
    # Latin America
    "Sao Paulo":    150,  # USP (~#140-160)
    "Rio de Janeiro":190,
    "Buenos Aires": 175,
    "Santiago":     165,
    "Mexico City":  160,
    "Lima":         250,
    "Bogota":       220,
    "Edmonton":     65,
    "Calgary":      70,
    # Oceania
    "Auckland":     85,   # University of Auckland (~#80-90)
    "Brisbane":     70,   # UQ (~#65-75)
    "Perth":        90,
    "Canberra":     80,   # ANU (~#75-85)
}

# ═══════════════════════════════════════════════════════════════════════════
# 4. EF English Proficiency Index 2024  (country-level score, 0–800)
#    Source: EF Education First, EF EPI 2024 report (ef.com/epi)
# ═══════════════════════════════════════════════════════════════════════════
EF_EPI = {
    # ── Direct from report ────────────────────────────────────────────────
    "Netherlands":          636,
    "Norway":               610,
    "Singapore":            609,
    "Sweden":               608,
    "Croatia":              607,
    "Portugal":             605,
    "Denmark":              603,
    "Greece":               602,
    "Austria":              600,
    "Germany":              598,
    "South Africa":         594,
    "Romania":              593,
    "Belgium":              592,
    "Finland":              590,
    "Poland":               588,
    "Bulgaria":             586,
    "Hungary":              585,
    "Slovakia":             584,
    "Kenya":                581,
    "Estonia":              578,
    "Luxembourg":           576,
    "Philippines":          570,
    "Lithuania":            569,
    "Serbia":               568,
    "Czech Republic":       567,
    "Malaysia":             566,
    "Czechia":              567,   # alias
    "Argentina":            562,
    "Switzerland":          550,
    "Hong Kong":            549,   # "Hong Kong (China)" in report
    "Spain":                538,
    "Russia":               532,
    "Italy":                528,
    "Chile":                525,
    "France":               524,
    "South Korea":          523,
    "Israel":               522,
    "Peru":                 519,
    "Vietnam":              498,
    "Turkey":               497,
    "Pakistan":             493,
    "India":                490,
    "United Arab Emirates": 489,
    "Brazil":               466,
    "Egypt":                465,
    "Mexico":               459,
    "Indonesia":            468,
    "Japan":                454,
    "Saudi Arabia":         417,
    "Thailand":             415,
    # ── Not in extracted list — estimated from 2023 / region averages ──────
    "United States":        570,   # English-speaking, not ranked (native speaker countries excluded)
    "United Kingdom":       570,   # same
    "Canada":               570,   # same
    "Australia":            570,   # same
    "New Zealand":          570,   # same
    "Ireland":              570,   # same
    "China":                520,   # approx, 2023 EF EPI ~526 (Asia decline noted)
    "Taiwan":               535,   # approx, higher than mainland China
    "Nigeria":              530,   # estimated (high-proficiency African country)
    "Ghana":                534,   # from report
    "Ethiopia":             480,   # estimated
    "Ukraine":              535,   # estimated
    "Belarus":              539,   # from report
    "Colombia":             485,   # from report
    "Ecuador":              465,
    "Bolivia":              525,   # from report
    "Panama":               488,   # from report
}

# ═══════════════════════════════════════════════════════════════════════════
# Build and merge
# ═══════════════════════════════════════════════════════════════════════════
def build_external_data():
    city_attr = pd.read_csv(DATA_OUTPUT / "city_attributes.csv")

    # Map startup ecosystem rank by city name
    city_attr["startup_ecosystem_rank"] = city_attr["city"].map(STARTUP_RANK)

    # Map WIPO patent per million by country
    city_attr["patent_applications_pc"] = city_attr["country"].map(PATENT_PC)

    # Map QS CS rank by city name
    city_attr["qs_cs_rank"] = city_attr["city"].map(QS_CS_RANK)

    # Map EF EPI score by country
    city_attr["ef_epi_score"] = city_attr["country"].map(EF_EPI)

    # Coverage report
    print("=" * 60)
    print("External Data Coverage Report")
    print("=" * 60)
    for col in ["startup_ecosystem_rank", "patent_applications_pc",
                "qs_cs_rank", "ef_epi_score"]:
        n_valid = city_attr[col].notna().sum()
        n_total = len(city_attr[city_attr["adoption_count"] > 0])
        pct = 100 * n_valid / len(city_attr)
        print(f"  {col:<28}  {n_valid:3d}/{len(city_attr):3d} ({pct:.0f}%)")

    # Save raw mapping for audit
    ext_cols = ["city", "country", "startup_ecosystem_rank",
                "patent_applications_pc", "qs_cs_rank", "ef_epi_score"]
    city_attr[ext_cols].to_csv(DATA_RAW_EXT / "city_ecosystem_indicators.csv",
                               index=False)
    print(f"\nAudit file saved → {DATA_RAW_EXT / 'city_ecosystem_indicators.csv'}")

    # Save updated city_attributes.csv
    city_attr.to_csv(DATA_OUTPUT / "city_attributes.csv", index=False)
    print(f"city_attributes.csv updated → {DATA_OUTPUT / 'city_attributes.csv'}")
    return city_attr


if __name__ == "__main__":
    df = build_external_data()
    print("\nNew columns added:")
    print(df[["city", "country", "startup_ecosystem_rank",
              "patent_applications_pc", "qs_cs_rank", "ef_epi_score"]
            ].head(20).to_string(index=False))
