"""
Step 3a (HF) – Resolve a "raw_location" string for every HF author /
organisation that owns a prominent HF project.

Why this is non-trivial
-----------------------
The Hugging Face Hub API does NOT expose a `location` field on its
user / organisation overview endpoints (verified 2026-04). The HTML
profile page also does not embed it as JSON. We therefore have to
recover author location from external evidence:

  1.  same-name lookup in `github_owner_locations.csv`
      (case-insensitive). Many individuals use the same handle on both
      platforms.
  2.  a small hand-curated dictionary for the highest-volume HF orgs
      (covers ~30% of HF prominent projects with very high precision).
  3.  GitHub API `GET /users/{login}` for the remaining HF authors
      that look like they could be a single person / org on GitHub.
      Skipped automatically when GITHUB_TOKEN is unset or when the
      caller passes --no-github-api.

Output
------
data/raw/huggingface/hf_author_locations.csv with columns:
    author, entity_type, raw_location, source, status, fetched_at

Where `source` ∈ {cached_github, manual, github_api, unmatched} so
downstream stages can reason about confidence.
"""

import argparse
import csv
import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DATA_RAW, DATA_PROCESSED, GITHUB_TOKEN

MASTER = DATA_PROCESSED / "prominent_projects_master.csv"
GH_LOC = DATA_RAW / "github" / "github_owner_locations.csv"
OUT    = DATA_RAW / "huggingface" / "hf_author_locations.csv"

GH_API_USER = "https://api.github.com/users/{}"
HEADERS = {
    "User-Agent": "casa0006-dsss/1.0",
    "Accept": "application/vnd.github+json",
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

REQUEST_TIMEOUT = 15
SLEEP_BETWEEN   = 0.05

# ── Manual dictionary ─────────────────────────────────────────────────────────
# Hand-curated locations for the highest-volume HF authors.  Locations are
# written in the same free-form style as GitHub's `location` field so that
# step3b's cleaner / matcher accepts them without modification.
#
# Locations are written using the *closest known top-150 metro* rather
# than the literal head-office city, so that step3b's matcher can map
# them to a city in the curated city list. For example, "Menlo Park"
# and "Cupertino" become "San Francisco, CA, USA" (same Bay Area FUA);
# "Seongnam" becomes "Seoul, South Korea"; "Darmstadt" becomes
# "Frankfurt, Germany"; etc. This is consistent with the FUA-level
# spatial unit used elsewhere in the project.
#
MANUAL_HF_LOCATIONS = {
    # ── corporate research labs (US) ───────────────────────────────────────
    "google":              "San Francisco, CA, USA",
    "google-bert":         "San Francisco, CA, USA",
    "google-t5":           "San Francisco, CA, USA",
    "google-research":     "San Francisco, CA, USA",
    "googlefonts":         "San Francisco, CA, USA",
    "facebook":            "San Francisco, CA, USA",
    "facebookresearch":    "San Francisco, CA, USA",
    "FacebookAI":          "San Francisco, CA, USA",
    "meta-llama":          "San Francisco, CA, USA",
    "meta-music":          "San Francisco, CA, USA",
    "microsoft":           "Redmond, WA, USA",
    "Microsoft":           "Redmond, WA, USA",
    "nvidia":              "San Francisco, CA, USA",
    "NVIDIA":              "San Francisco, CA, USA",
    "intel":               "San Francisco, CA, USA",
    "Intel":               "San Francisco, CA, USA",
    "ibm":                 "New York, NY, USA",
    "IBM":                 "New York, NY, USA",
    "ibm-granite":         "New York, NY, USA",
    "amazon":              "Seattle, WA, USA",
    "AmazonScience":       "Seattle, WA, USA",
    "salesforce":          "San Francisco, CA, USA",
    "Salesforce":          "San Francisco, CA, USA",
    "apple":               "San Francisco, CA, USA",
    "Apple":               "San Francisco, CA, USA",
    "openai":              "San Francisco, CA, USA",
    "OpenAI":              "San Francisco, CA, USA",
    "anthropic":           "San Francisco, CA, USA",
    "Anthropic":           "San Francisco, CA, USA",
    "huggingface":         "New York, NY, USA",
    "HuggingFaceH4":       "New York, NY, USA",
    "huggingface-projects":"New York, NY, USA",

    # ── AI startups ────────────────────────────────────────────────────────
    "stabilityai":         "London, UK",
    "mistralai":           "Paris, France",
    "kyutai":              "Paris, France",
    "black-forest-labs":   "Frankfurt, Germany",
    "cohereai":            "Toronto, Canada",
    "CohereForAI":         "Toronto, Canada",
    "cohere":              "Toronto, Canada",
    "ai21labs":            "Tel Aviv, Israel",
    "ai21":                "Tel Aviv, Israel",
    "togethercomputer":    "San Francisco, CA, USA",
    "perplexity-ai":       "San Francisco, CA, USA",
    "deepseek-ai":         "Hangzhou, China",
    "Qwen":                "Hangzhou, China",
    "alibaba":             "Hangzhou, China",
    "Alibaba-NLP":         "Hangzhou, China",
    "baichuan-inc":        "Beijing, China",
    "baichuanai":          "Beijing, China",
    "01-ai":               "Beijing, China",
    "MoonshotAI":          "Beijing, China",
    "tencent":             "Shenzhen, China",
    "Tencent":             "Shenzhen, China",
    "internlm":            "Shanghai, China",
    "OpenGVLab":           "Shanghai, China",
    "shanghai-ai-lab":     "Shanghai, China",
    "ZhipuAI":             "Beijing, China",
    "THUDM":               "Beijing, China",
    "BAAI":                "Beijing, China",
    "IDEA-CCNL":           "Shenzhen, China",
    "IDEA-Research":       "Shenzhen, China",
    "fnlp":                "Shanghai, China",
    "FreedomIntelligence": "Shenzhen, China",
    "lmsys":               "San Francisco, CA, USA",
    "berkeley-nest":       "San Francisco, CA, USA",
    "stanfordnlp":         "San Francisco, CA, USA",
    "allenai":             "Seattle, WA, USA",
    "AllenAI":             "Seattle, WA, USA",
    "EleutherAI":          "New York, NY, USA",
    "bigscience":          "Paris, France",
    "bigcode":             "Paris, France",
    "Helsinki-NLP":        "Helsinki, Finland",
    "sentence-transformers":"Frankfurt, Germany",
    "naver-clova-ix":      "Seoul, South Korea",
    "naver":               "Seoul, South Korea",
    "kakaobrain":          "Seoul, South Korea",
    "snunlp":              "Seoul, South Korea",
    "rinna":               "Tokyo, Japan",
    "cyberagent":          "Tokyo, Japan",
    "elyza":               "Tokyo, Japan",
    "pfnet":               "Tokyo, Japan",
    "stockmark":           "Tokyo, Japan",
    "sambanova":           "San Francisco, CA, USA",
    "snowflake":           "San Francisco, CA, USA",
    "Snowflake":           "San Francisco, CA, USA",
    "databricks":          "San Francisco, CA, USA",
    "DataBricks":          "San Francisco, CA, USA",
    "deepmind":            "London, UK",
    "DeepMind":            "London, UK",
    "Tsinghua":            "Beijing, China",
    "BUPT":                "Beijing, China",
    "PKU":                 "Beijing, China",
    "openbmb":             "Beijing, China",
    "OpenMed":             "Boston, MA, USA",
    "MedARC":              "Boston, MA, USA",
    "argilla":             "Madrid, Spain",
    "vinai":               "Hanoi, Vietnam",
    "VietAI":              "Hanoi, Vietnam",
    "skywork":             "Beijing, China",
    "MBZUAI":              "Abu Dhabi, UAE",
    "ServiceNow":          "Montreal, Canada",
    "ServiceNow-AI":       "Montreal, Canada",
    "kfkas":               "Seoul, South Korea",
    "MaziyarPanahi":       "Paris, France",
    "TheBloke":            "London, UK",
    "bartowski":           "Toronto, Canada",
    "unsloth":             "San Francisco, CA, USA",
    "lmstudio-community":  "Seattle, WA, USA",
    "mradermacher":        "Hamburg, Germany",
    "timm":                "London, UK",
    "rwightman":           "London, UK",
    "ggml-org":            "Sofia, Bulgaria",
    "openchat":            "Beijing, China",
    "BlinkDL":             "Hangzhou, China",
    "RWKV":                "Hangzhou, China",
    "OpenAccess-AI-Collective":"San Francisco, CA, USA",
    "WizardLMTeam":        "Beijing, China",
    "WizardLM":            "Beijing, China",
    "Open-Orca":           "San Francisco, CA, USA",
    "NousResearch":        "Los Angeles, CA, USA",
    "RedHatAI":            "Raleigh, NC, USA",
    "AI-MO":               "Paris, France",
    "OpenLLMSG":           "Singapore",
    "AISingapore":         "Singapore",
    "answerdotai":         "San Francisco, CA, USA",
    "AnswerDotAI":         "San Francisco, CA, USA",
    "BAAI-DCAI":           "Beijing, China",
    "DAMO-NLP-SG":         "Singapore",
    "BlackForestLabs":     "Frankfurt, Germany",
    "Felladrin":           "Sao Paulo, Brazil",
    "stable-diffusion-art":"London, UK",
    "lllyasviel":          "San Francisco, CA, USA",
    "Linaqruf":            "Jakarta, Indonesia",
    "ckpt":                "Tokyo, Japan",
    "JosephusCheung":      "Hong Kong, China",
    "yiyixu":              "San Francisco, CA, USA",
    "Salesforce-Research": "San Francisco, CA, USA",
    "ml-foundations":      "Seattle, WA, USA",
    "DiscoResearch":       "Berlin, Germany",
    "VAGOsolutions":       "Munich, Germany",
    "LeoLM":               "Munich, Germany",
    "occiglot":            "Munich, Germany",
    "jondurbin":           "Boston, MA, USA",
    "PrunaAI":             "Paris, France",
    "AIDC-AI":             "Hangzhou, China",
    "OpenBMB":             "Beijing, China",
    "ZJU-Fanlab":          "Hangzhou, China",
    "moondream":           "Seattle, WA, USA",
    "vikhyatk":            "San Francisco, CA, USA",
    "x-flux":              "Moscow, Russia",
    "yandex":              "Moscow, Russia",
    "lab-mit":             "Boston, MA, USA",
    "MIT-IBM":             "Boston, MA, USA",
    "MIT":                 "Boston, MA, USA",
    "harvard-nlp":         "Boston, MA, USA",
    "princeton-nlp":       "New York, NY, USA",
    "uw-nlp":              "Seattle, WA, USA",
    "cmu-lti":             "Pittsburgh, PA, USA",
    "ucl":                 "London, UK",
    "ox-it":               "Oxford, UK",
    "cambridgeltl":        "Cambridge, UK",
    "epfl-llm":            "Lausanne, Switzerland",
    "BSC-LT":              "Barcelona, Spain",
    "PlanTL-GOB-ES":       "Madrid, Spain",
    "deepset":             "Berlin, Germany",
    "TU-Vienna":           "Vienna, Austria",

    # ── second-pass additions (after running step3a once and inspecting
    #    the highest-volume unmatched HF authors) ──────────────────────────
    "optimum-intel-internal-testing": "San Francisco, CA, USA",
    "zai-org":                "Beijing, China",
    "multimodalart":          "New York, NY, USA",
    "trl-internal-testing":   "New York, NY, USA",
    "peft-internal-testing":  "New York, NY, USA",
    "HuggingFaceTB":          "New York, NY, USA",
    "HuggingFaceM4":          "New York, NY, USA",
    "lerobot":                "New York, NY, USA",
    "Comfy-Org":              "San Francisco, CA, USA",
    "LiquidAI":               "Boston, MA, USA",
    "tiiuae":                 "Abu Dhabi, UAE",
    "PaddlePaddle":           "Beijing, China",
    "Baidu":                  "Beijing, China",
    "BAAI-DCAI":              "Beijing, China",
    "laion":                  "Hamburg, Germany",
    "LAION":                  "Hamburg, Germany",
    "Salesforce-AI":          "San Francisco, CA, USA",
    "ServiceNow-AI":          "Montreal, Canada",
    "Snowflake-AI":           "San Mateo, CA, USA",
    "neuralmagic":            "Boston, MA, USA",
    "AdaptLLM":               "Hong Kong, China",
    "ZJU-LMS":                "Hangzhou, China",
    "FudanNLP":               "Shanghai, China",
    "Skywork":                "Beijing, China",
    "InstantX":               "Beijing, China",
    "BlinkDL_AI":             "Hangzhou, China",
    "OpenBuddy":              "Singapore",
    "OrionStarAI":            "Beijing, China",
    "shenzhi-wang":           "Beijing, China",
    "Mihaiii":                "Bucharest, Romania",
    "second-state":           "San Francisco, CA, USA",
    "second-state-coreml":    "San Francisco, CA, USA",
    "Gryphe":                 "Amsterdam, Netherlands",
    "LDJnr":                  "Toronto, Canada",
    "argmaxinc":              "San Francisco, CA, USA",
    "OuteAI":                 "Vilnius, Lithuania",
    "PygmalionAI":            "San Francisco, CA, USA",
    "MaartenGr":              "Amsterdam, Netherlands",
    "BeIR":                   "Darmstadt, Germany",
    "intfloat":               "Beijing, China",
    "moka-ai":                "Beijing, China",
    "Salesforce-research":    "San Francisco, CA, USA",
    "h2oai":                  "Mountain View, CA, USA",
    "H2OAI":                  "Mountain View, CA, USA",
    "shibing624":             "Beijing, China",
    "uer":                    "Beijing, China",
    "fnlp":                   "Shanghai, China",
    "ckiplab":                "Taipei, Taiwan",
    "uitnlp":                 "Ho Chi Minh City, Vietnam",
    "uonlp":                  "Hanoi, Vietnam",
    "AntGroup":               "Hangzhou, China",
    "ant-design":             "Hangzhou, China",
    "PKU-Alignment":          "Beijing, China",
    "PKU-YuanGroup":          "Beijing, China",
    "USC-GVL":                "Los Angeles, CA, USA",
}


def _load_existing_output(path: Path) -> dict:
    if not path.exists():
        return {}
    df = pd.read_csv(path, dtype=str).fillna("")
    return {row["author"]: dict(row) for _, row in df.iterrows()}


def _load_github_loc_index() -> dict:
    if not GH_LOC.exists():
        return {}
    df = pd.read_csv(GH_LOC, dtype=str).fillna("")
    idx = {}
    for _, row in df.iterrows():
        login = row["login"].strip()
        if not login:
            continue
        loc = row["location"].strip()
        idx[login.lower()] = {
            "login_canonical": login,
            "location": loc,
            "type": (row.get("type") or "").strip() or "User",
        }
    return idx


def _query_github_user(login: str):
    """Return (location, entity_type, status)."""
    try:
        r = requests.get(GH_API_USER.format(login), headers=HEADERS,
                         timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        return ("", "unknown", f"err:{type(exc).__name__}")

    if r.status_code == 404:
        return ("", "unknown", "http:404")
    if r.status_code in (401, 403):
        # rate limit or auth issue
        remaining = r.headers.get("X-RateLimit-Remaining")
        return ("", "unknown", f"http:{r.status_code}:rl={remaining}")
    if r.status_code != 200:
        return ("", "unknown", f"http:{r.status_code}")

    try:
        d = r.json()
    except ValueError:
        return ("", "unknown", "json")

    loc = (d.get("location") or "").strip()
    kind = "organization" if d.get("type") == "Organization" else "user"
    return (loc, kind, "ok")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-github-api", action="store_true",
                        help="Skip the GitHub /users/{login} fallback")
    parser.add_argument("--gh-budget", type=int, default=4500,
                        help="Max GitHub /users/{login} calls per run")
    args = parser.parse_args()

    print("=" * 64)
    print("Step 3a (HF): resolve HF author / org locations")
    print("=" * 64)

    if not MASTER.exists():
        print(f"❌ Missing {MASTER}. Run step1c first.")
        return

    df = pd.read_csv(MASTER, dtype=str)
    hf = df[df["platform"] == "HuggingFace"].copy()
    hf["author"] = hf["full_id"].fillna("").str.split("/").str[0]
    authors = sorted({a for a in hf["author"] if a})

    print(f"  HF prominent rows : {len(hf)}")
    print(f"  Unique HF authors : {len(authors)}")

    gh_idx = _load_github_loc_index()
    print(f"  GH login index    : {len(gh_idx)}")
    print(f"  Manual dictionary : {len(MANUAL_HF_LOCATIONS)} entries")
    print(f"  GitHub token      : {'set' if GITHUB_TOKEN else 'NOT set (skip API)'}")

    # ── Resolve in order: cached → manual → github_api ────────────────────────
    cached = _load_existing_output(OUT)
    print(f"  Already in OUT    : {len(cached)}")

    # Stats
    n_cached_hit = 0
    n_cached_loc = 0
    n_manual = 0
    n_github_cached = 0
    n_github_api = 0
    n_unmatched = 0
    n_github_calls = 0

    rows_out = {}
    for a in authors:
        # Reuse previous run if status was 'ok' or it was 'manual'/'cached_github'
        prev = cached.get(a)
        if prev and prev.get("status") in ("ok", "manual"):
            rows_out[a] = prev
            n_cached_hit += 1
            if prev.get("raw_location"):
                n_cached_loc += 1
            continue

        # Manual dictionary first (very high precision)
        if a in MANUAL_HF_LOCATIONS:
            rows_out[a] = {
                "author": a,
                "entity_type": "organization",
                "raw_location": MANUAL_HF_LOCATIONS[a],
                "source": "manual",
                "status": "manual",
                "fetched_at": "",
            }
            n_manual += 1
            continue

        # Same-name GitHub cache lookup
        gh = gh_idx.get(a.lower())
        if gh and gh["location"]:
            rows_out[a] = {
                "author": a,
                "entity_type": "organization" if gh["type"] == "Organization" else "user",
                "raw_location": gh["location"],
                "source": "cached_github",
                "status": "ok",
                "fetched_at": "",
            }
            n_github_cached += 1
            continue

        # GitHub API fallback
        if args.no_github_api or not GITHUB_TOKEN or n_github_calls >= args.gh_budget:
            rows_out[a] = {
                "author": a,
                "entity_type": "unknown",
                "raw_location": "",
                "source": "unmatched",
                "status": "skipped",
                "fetched_at": "",
            }
            n_unmatched += 1
            continue

        loc, kind, status = _query_github_user(a)
        n_github_calls += 1
        if status == "ok" and loc:
            rows_out[a] = {
                "author": a,
                "entity_type": kind,
                "raw_location": loc,
                "source": "github_api",
                "status": "ok",
                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            n_github_api += 1
        else:
            rows_out[a] = {
                "author": a,
                "entity_type": kind,
                "raw_location": "",
                "source": "github_api",
                "status": status,
                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            n_unmatched += 1

        if n_github_calls % 100 == 0:
            print(f"  … github_api calls so far: {n_github_calls}")

        time.sleep(SLEEP_BETWEEN)

    # ── Write ─────────────────────────────────────────────────────────────────
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["author", "entity_type", "raw_location",
                  "source", "status", "fetched_at"]
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for a in sorted(rows_out):
            w.writerow({k: rows_out[a].get(k, "") for k in fieldnames})

    # ── Summary ───────────────────────────────────────────────────────────────
    total = len(rows_out)
    with_loc = sum(1 for r in rows_out.values() if r["raw_location"])
    print("\n" + "=" * 64)
    print("Summary")
    print("=" * 64)
    print(f"  Total authors written       : {total}")
    print(f"    cached previous           : {n_cached_hit}")
    print(f"    resolved via manual dict  : {n_manual}")
    print(f"    resolved via GH cache     : {n_github_cached}")
    print(f"    resolved via GH API call  : {n_github_api}")
    print(f"    unmatched                 : {n_unmatched}")
    print(f"  GitHub API calls made       : {n_github_calls}")
    print(f"  → with non-empty location   : {with_loc} ({with_loc/total*100:.1f}%)")
    print(f"\n✅ Wrote → {OUT}")


if __name__ == "__main__":
    main()
