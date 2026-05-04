"""
Step 1b – Discover and filter open-AI-related projects on Hugging Face.

Strategy
--------
1. Use the Hugging Face Hub API (`huggingface_hub` library) to list:
   - Models
   - Datasets
   - Spaces
   that were created within the study window (2022-01 to 2025-12).
2. For each object, collect metadata (downloads, likes, pipeline_tag,
   tags, author, etc.).
3. Apply open-AI relevance rules (pipeline_tag match + tag/keyword match)
   and record evidence & confidence.
4. Apply prominence threshold (downloads / likes).
5. Save results to  data/raw/huggingface/hf_candidates.csv
"""

import csv
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    HF_TOKEN,
    DATA_RAW,
    TIME_START,
    TIME_END,
    AI_INCLUDE_KEYWORDS,
    AI_WEAK_KEYWORDS,
    AI_EXCLUDE_KEYWORDS,
    HF_AI_PIPELINE_TAGS,
    HF_PROMINENCE,
)

try:
    from huggingface_hub import HfApi
except ImportError:
    print("❌ Please install huggingface_hub:  pip install huggingface_hub")
    sys.exit(1)

api = HfApi(token=HF_TOKEN or None)

START_DT = datetime.strptime(TIME_START, "%Y-%m-%d")
END_DT = datetime.strptime(TIME_END, "%Y-%m-%d")


def _parse_created_at(obj) -> Optional[datetime]:
    """Extract and parse created_at from a HF Hub object."""
    created = getattr(obj, "created_at", None) or getattr(obj, "lastModified", None)
    if isinstance(created, str):
        try:
            created = datetime.fromisoformat(created.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None
    if isinstance(created, datetime) and created.tzinfo is not None:
        created = created.replace(tzinfo=None)
    return created


def _in_window(created: Optional[datetime]) -> bool:
    if created is None:
        return False
    if created.tzinfo is not None:
        created = created.replace(tzinfo=None)
    return START_DT <= created <= END_DT


def _match_ai_relevance(
    model_id: str, tags: List[str], pipeline_tag: Optional[str], card_data_tags: List[str]
):
    """
    Returns (is_relevant, evidence, confidence).
    """
    all_tags = [t.lower() for t in tags + card_data_tags]
    text = f"{model_id} {' '.join(all_tags)}".lower()
    text_norm = re.sub(r"[_/.]", "-", text)

    matched = []

    # pipeline_tag is a strong signal on HF
    if pipeline_tag and pipeline_tag.lower() in [t.lower() for t in HF_AI_PIPELINE_TAGS]:
        matched.append(f"pipeline:{pipeline_tag}")

    for kw in AI_INCLUDE_KEYWORDS:
        if kw.lower() in text_norm:
            matched.append(kw.lower())

    if not matched:
        return False, "", "none"

    for ex in AI_EXCLUDE_KEYWORDS:
        if ex.lower() in text_norm:
            return False, f"excluded:{ex}", "none"

    strong = [m for m in matched if m not in AI_WEAK_KEYWORDS and not m.startswith("pipeline:")]
    pipeline_match = any(m.startswith("pipeline:") for m in matched)

    if pipeline_match:
        confidence = "high"
    elif strong:
        confidence = "high" if len(strong) >= 2 else "medium"
    else:
        confidence = "low"

    evidence = "; ".join(sorted(set(matched)))
    return True, evidence, confidence


def _is_prominent(downloads: int, likes: int) -> bool:
    d = downloads >= HF_PROMINENCE["downloads_min"]
    li = likes >= HF_PROMINENCE["likes_min"]
    if HF_PROMINENCE["logic"] == "or":
        return d or li
    return d and li


def _safe_str(val) -> str:
    if val is None:
        return ""
    return str(val)


def collect_models() -> list[dict]:
    """Iterate over HF models and collect candidates."""
    print("📦 Fetching models …")
    rows = []
    count = 0
    for model in api.list_models(
        sort="downloads",
        limit=None,
        full=True,
        cardData=True,
    ):
        created = _parse_created_at(model)

        if not _in_window(created):
            # Models are sorted by downloads desc; once we've passed the window
            # we still continue because creation date isn't monotonic with downloads.
            count += 1
            if count > 200000:
                break
            continue

        model_id = getattr(model, "modelId", "") or getattr(model, "id", "")
        tags = list(getattr(model, "tags", []) or [])
        pipeline_tag = _safe_str(getattr(model, "pipeline_tag", None))
        card_tags = list(getattr(model, "cardData", {}).get("tags", []) if getattr(model, "cardData", None) else [])
        downloads = getattr(model, "downloads", 0) or 0
        likes = getattr(model, "likes", 0) or 0
        author = model_id.split("/")[0] if "/" in model_id else ""

        is_ai, evidence, confidence = _match_ai_relevance(
            model_id, tags, pipeline_tag, card_tags
        )

        rows.append(
            {
                "project_id": f"hf_model_{model_id.replace('/', '__')}",
                "platform": "HuggingFace",
                "hf_type": "model",
                "hf_id": model_id,
                "project_name": model_id.split("/")[-1] if "/" in model_id else model_id,
                "author": author,
                "pipeline_tag": pipeline_tag,
                "tags": "|".join(tags[:30]),
                "downloads": downloads,
                "likes": likes,
                "created_at": _safe_str(created),
                "open_ai_related": int(is_ai),
                "ai_evidence": evidence,
                "ai_confidence": confidence,
                "prominent_flag": int(is_ai and _is_prominent(downloads, likes)),
            }
        )
        count += 1
        if count % 5000 == 0:
            print(f"  … scanned {count} models, kept {len(rows)} candidates")

    print(f"  ✔ Models done: {len(rows)} candidates from {count} scanned")
    return rows


def collect_datasets() -> list[dict]:
    """Iterate over HF datasets and collect candidates."""
    print("📦 Fetching datasets …")
    rows = []
    count = 0
    for ds in api.list_datasets(
        sort="downloads",
        limit=None,
        full=True,
    ):
        created = _parse_created_at(ds)

        if not _in_window(created):
            count += 1
            if count > 200000:
                break
            continue

        ds_id = getattr(ds, "id", "")
        tags = list(getattr(ds, "tags", []) or [])
        downloads = getattr(ds, "downloads", 0) or 0
        likes = getattr(ds, "likes", 0) or 0
        author = ds_id.split("/")[0] if "/" in ds_id else ""

        is_ai, evidence, confidence = _match_ai_relevance(ds_id, tags, None, [])

        rows.append(
            {
                "project_id": f"hf_dataset_{ds_id.replace('/', '__')}",
                "platform": "HuggingFace",
                "hf_type": "dataset",
                "hf_id": ds_id,
                "project_name": ds_id.split("/")[-1] if "/" in ds_id else ds_id,
                "author": author,
                "pipeline_tag": "",
                "tags": "|".join(tags[:30]),
                "downloads": downloads,
                "likes": likes,
                "created_at": _safe_str(created),
                "open_ai_related": int(is_ai),
                "ai_evidence": evidence,
                "ai_confidence": confidence,
                "prominent_flag": int(is_ai and _is_prominent(downloads, likes)),
            }
        )
        count += 1
        if count % 5000 == 0:
            print(f"  … scanned {count} datasets, kept {len(rows)} candidates")

    print(f"  ✔ Datasets done: {len(rows)} candidates from {count} scanned")
    return rows


def collect_spaces() -> list[dict]:
    """Iterate over HF Spaces and collect candidates."""
    print("📦 Fetching Spaces …")
    rows = []
    count = 0
    for sp in api.list_spaces(
        sort="likes",
        limit=None,
        full=True,
    ):
        created = _parse_created_at(sp)

        if not _in_window(created):
            count += 1
            if count > 100000:
                break
            continue

        sp_id = getattr(sp, "id", "")
        tags = list(getattr(sp, "tags", []) or [])
        likes = getattr(sp, "likes", 0) or 0
        author = sp_id.split("/")[0] if "/" in sp_id else ""

        is_ai, evidence, confidence = _match_ai_relevance(sp_id, tags, None, [])

        rows.append(
            {
                "project_id": f"hf_space_{sp_id.replace('/', '__')}",
                "platform": "HuggingFace",
                "hf_type": "space",
                "hf_id": sp_id,
                "project_name": sp_id.split("/")[-1] if "/" in sp_id else sp_id,
                "author": author,
                "pipeline_tag": "",
                "tags": "|".join(tags[:30]),
                "downloads": 0,
                "likes": likes,
                "created_at": _safe_str(created),
                "open_ai_related": int(is_ai),
                "ai_evidence": evidence,
                "ai_confidence": confidence,
                "prominent_flag": int(
                    is_ai and likes >= HF_PROMINENCE["likes_min"]
                ),
            }
        )
        count += 1
        if count % 5000 == 0:
            print(f"  … scanned {count} spaces, kept {len(rows)} candidates")

    print(f"  ✔ Spaces done: {len(rows)} candidates from {count} scanned")
    return rows


def save_csv(rows: list[dict], path: Path):
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


def main():
    print("=" * 60)
    print("Step 1b: Hugging Face open-AI project discovery")
    print("=" * 60)

    all_rows = []
    all_rows.extend(collect_models())
    all_rows.extend(collect_datasets())
    all_rows.extend(collect_spaces())

    out_path = DATA_RAW / "huggingface" / "hf_candidates.csv"
    save_csv(all_rows, out_path)

    total = len(all_rows)
    ai_yes = sum(1 for r in all_rows if r["open_ai_related"])
    prominent = sum(1 for r in all_rows if r["prominent_flag"])
    print(f"\n📊 Summary: {total} HF objects collected")
    print(f"   open_ai_related = 1 : {ai_yes}")
    print(f"   prominent_flag  = 1 : {prominent}")


if __name__ == "__main__":
    main()
