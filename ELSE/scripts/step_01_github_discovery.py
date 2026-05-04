"""
Step 1a – Discover and filter open-AI-related GitHub repositories.

Strategy
--------
1. Use the GitHub Search API to find repos matching AI-related keywords,
   created within the study window (2022-01 to 2025-12).
2. For each candidate repo, collect metadata (stars, forks, topics,
   description, owner location, created_at, etc.).
3. Apply the open-AI relevance rule (keyword match on name + description +
   topics) and record match evidence & confidence.
4. Apply the prominence threshold (stars / forks).
5. Save results to  data/raw/github/github_candidates.csv

Rate-limit handling
-------------------
- The Search API allows 30 requests/min (authenticated) with up to 1000
  results per query.  We split queries by creation-date month to stay under
  the 1000-result cap, and sleep between pages to respect rate limits.
"""

import time
import csv
import re
import sys
import requests
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    GITHUB_TOKEN,
    DATA_RAW,
    TIME_START,
    TIME_END,
    AI_INCLUDE_KEYWORDS,
    AI_WEAK_KEYWORDS,
    AI_EXCLUDE_KEYWORDS,
    GITHUB_PROMINENCE,
)

HEADERS = {"Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

SEARCH_URL = "https://api.github.com/search/repositories"
PER_PAGE = 100
MAX_PAGES = 10  # 1000 results per query slice

# We search with a curated set of high-signal queries (each is a GitHub search
# string).  Using too many keywords at once hits the query-length limit, so we
# group them into batches.
SEARCH_QUERIES = [
    "llm OR large-language-model OR language-model",
    "transformer OR attention-mechanism",
    "gpt OR chatgpt OR instruction-tuning",
    "diffusion OR stable-diffusion OR latent-diffusion",
    "text-generation OR code-generation OR image-generation",
    "generative-ai OR text-to-image OR text-to-video",
    "multimodal OR vision-language OR clip",
    "ai-agent OR autonomous-agent OR rag OR retrieval-augmented-generation",
    "embedding OR sentence-embedding OR vector-database OR semantic-search",
    "natural-language-processing OR nlp OR question-answering OR summarization",
    "computer-vision OR object-detection OR image-segmentation",
    "speech-recognition OR automatic-speech-recognition OR text-to-speech",
    "deep-learning OR neural-network OR reinforcement-learning",
    "open-weight OR llama OR mistral OR falcon OR qwen OR deepseek",
    "quantization OR gguf OR vllm OR model-serving OR model-inference",
    "whisper OR segment-anything OR stable-audio",
    "fine-tuning OR rlhf OR prompt-engineering",
    "mlops OR onnx OR tensorrt",
]


def _generate_half_year_windows(start: str, end: str):
    """Yield (start_date, end_date) for each ~6-month window within [start, end]."""
    sd = date.fromisoformat(start)
    ed = date.fromisoformat(end)
    cur = sd
    while cur <= ed:
        half_end = date(cur.year, 6, 30) if cur.month <= 6 else date(cur.year, 12, 31)
        win_end = min(half_end, ed)
        yield cur.isoformat(), win_end.isoformat()
        nxt = win_end + timedelta(days=1)
        if nxt > ed:
            break
        cur = nxt


def _wait_for_rate_limit(response: requests.Response):
    """Sleep until the rate-limit window resets if we've run out of quota."""
    remaining = int(response.headers.get("X-RateLimit-Remaining", 1))
    if remaining == 0:
        reset_ts = int(response.headers.get("X-RateLimit-Reset", 0))
        sleep_sec = max(reset_ts - int(time.time()), 1) + 2
        print(f"  ⏳ Rate-limited. Sleeping {sleep_sec}s …")
        time.sleep(sleep_sec)


def _match_ai_relevance(name, desc, topics):
    """
    Check whether a repo is open-AI-related.
    Returns (is_relevant: bool, evidence: str, confidence: str).
    """
    text = f"{name} {desc} {' '.join(topics)}".lower()
    # normalise separators so "text_generation" matches "text-generation"
    text_norm = re.sub(r"[_/.]", "-", text)

    matched = []
    for kw in AI_INCLUDE_KEYWORDS:
        kw_lower = kw.lower()
        if kw_lower in text_norm:
            matched.append(kw_lower)

    if not matched:
        return False, "", "none"

    # Exclude false positives
    for ex in AI_EXCLUDE_KEYWORDS:
        if ex.lower() in text_norm:
            return False, f"excluded:{ex}", "none"

    # If only weak keywords matched, require a second confirming signal
    strong = [m for m in matched if m not in AI_WEAK_KEYWORDS]
    if not strong and len(matched) < 2:
        # Allow "agent" if description has AI context words
        ai_context = re.search(
            r"(?i)\b(ai|artificial.intelligence|llm|language.model|gpt|autonom|coding|code.gen|reasoning)\b",
            text_norm,
        )
        if ai_context:
            matched.append(f"context:{ai_context.group()}")
        else:
            return False, f"weak-only:{matched}", "low"

    confidence = "high" if len(matched) >= 2 or strong else "medium"
    evidence = "; ".join(sorted(set(matched)))
    return True, evidence, confidence


def _is_prominent(stars: int, forks: int) -> bool:
    s = stars >= GITHUB_PROMINENCE["stars_min"]
    f = forks >= GITHUB_PROMINENCE["forks_min"]
    if GITHUB_PROMINENCE["logic"] == "or":
        return s or f
    return s and f


def search_github():
    """Run all search queries and collect unique repos."""
    seen_ids = set()
    rows = []

    total_queries = len(SEARCH_QUERIES)

    for qi, query in enumerate(SEARCH_QUERIES, 1):
        windows = list(_generate_half_year_windows(TIME_START, TIME_END))
        for wi, (ws, we) in enumerate(windows):
            q = f"{query} created:{ws}..{we}"
            print(f"[{qi}/{total_queries}] window {wi+1}/{len(windows)}: {q[:80]}…")

            for page in range(1, MAX_PAGES + 1):
                params = {
                    "q": q,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": PER_PAGE,
                    "page": page,
                }
                resp = requests.get(SEARCH_URL, headers=HEADERS, params=params)
                _wait_for_rate_limit(resp)

                if resp.status_code == 403:
                    print("  ⚠️  403 – sleeping 60s")
                    time.sleep(60)
                    resp = requests.get(SEARCH_URL, headers=HEADERS, params=params)

                if resp.status_code != 200:
                    print(f"  ⚠️  HTTP {resp.status_code}, skipping page")
                    break

                data = resp.json()
                items = data.get("items", [])
                if not items:
                    break

                for repo in items:
                    rid = repo["id"]
                    if rid in seen_ids:
                        continue
                    seen_ids.add(rid)

                    name = repo.get("name", "")
                    desc = repo.get("description") or ""
                    topics = repo.get("topics", [])
                    stars = repo.get("stargazers_count", 0)
                    forks = repo.get("forks_count", 0)

                    is_ai, evidence, confidence = _match_ai_relevance(
                        name, desc, topics
                    )

                    rows.append(
                        {
                            "project_id": f"gh_{rid}",
                            "platform": "GitHub",
                            "repo_full_name": repo.get("full_name", ""),
                            "project_name": name,
                            "description": desc[:500],
                            "topics": "|".join(topics),
                            "language": repo.get("language") or "",
                            "stars": stars,
                            "forks": forks,
                            "watchers": repo.get("watchers_count", 0),
                            "open_issues": repo.get("open_issues_count", 0),
                            "created_at": repo.get("created_at", ""),
                            "updated_at": repo.get("updated_at", ""),
                            "pushed_at": repo.get("pushed_at", ""),
                            "owner_login": repo.get("owner", {}).get("login", ""),
                            "owner_type": repo.get("owner", {}).get("type", ""),
                            "license": (repo.get("license") or {}).get(
                                "spdx_id", ""
                            ),
                            "homepage": repo.get("homepage") or "",
                            "html_url": repo.get("html_url", ""),
                            "open_ai_related": int(is_ai),
                            "ai_evidence": evidence,
                            "ai_confidence": confidence,
                            "prominent_flag": int(
                                is_ai and _is_prominent(stars, forks)
                            ),
                        }
                    )

                time.sleep(2.5)  # respect rate limit

    return rows


def save_csv(rows, path):
    if not rows:
        print("⚠️  No rows to save.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"✅ Saved {len(rows)} rows → {path}")


def reevaluate():
    """Re-evaluate AI relevance on an existing github_candidates.csv
    using the current keyword rules. No API calls needed."""
    import pandas as pd

    print("=" * 60)
    print("Step 1a [re-evaluate]: update flags with current keywords")
    print("=" * 60)

    gh_path = DATA_RAW / "github" / "github_candidates.csv"
    df = pd.read_csv(gh_path, dtype=str).fillna("")

    old_ai = (df["open_ai_related"] == "1").sum()
    old_prom = (df["prominent_flag"] == "1").sum()

    for idx, row in df.iterrows():
        name = row["project_name"]
        desc = row["description"]
        topics = row["topics"].split("|") if row["topics"] else []
        stars = int(row["stars"]) if row["stars"] else 0
        forks = int(row["forks"]) if row["forks"] else 0

        is_ai, evidence, confidence = _match_ai_relevance(name, desc, topics)
        df.at[idx, "open_ai_related"] = str(int(is_ai))
        df.at[idx, "ai_evidence"] = evidence
        df.at[idx, "ai_confidence"] = confidence
        df.at[idx, "prominent_flag"] = str(int(is_ai and _is_prominent(stars, forks)))

    df.to_csv(gh_path, index=False)

    new_ai = (df["open_ai_related"] == "1").sum()
    new_prom = (df["prominent_flag"] == "1").sum()
    print(f"\n  open_ai_related: {old_ai} → {new_ai} ({new_ai - old_ai:+d})")
    print(f"  prominent_flag:  {old_prom} → {new_prom} ({new_prom - old_prom:+d})")


def main():
    print("=" * 60)
    print("Step 1a: GitHub open-AI project discovery")
    print("=" * 60)

    if "--reevaluate" in sys.argv:
        reevaluate()
        return

    if not GITHUB_TOKEN:
        print(
            "⚠️  GITHUB_TOKEN not set. Requests will be severely rate-limited.\n"
            "   export GITHUB_TOKEN='ghp_…' before running."
        )

    rows = search_github()

    out_path = DATA_RAW / "github" / "github_candidates.csv"
    save_csv(rows, out_path)

    # Summary
    total = len(rows)
    ai_yes = sum(1 for r in rows if r["open_ai_related"])
    prominent = sum(1 for r in rows if r["prominent_flag"])
    print(f"\n📊 Summary: {total} repos collected")
    print(f"   open_ai_related = 1 : {ai_yes}")
    print(f"   prominent_flag  = 1 : {prominent}")


if __name__ == "__main__":
    main()
