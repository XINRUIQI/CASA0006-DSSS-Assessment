"""
Step 1c – Merge GitHub and Hugging Face candidates into a unified
           project filtering result table.

Outputs
-------
data/processed/project_filtering_result.csv      – all candidates with flags
data/processed/prominent_projects_master.csv      – only prominent_flag == 1
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DATA_RAW, DATA_PROCESSED

GH_PATH = DATA_RAW / "github" / "github_candidates.csv"
HF_PATH = DATA_RAW / "huggingface" / "hf_candidates.csv"


def _align_to_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing columns and reorder to the unified schema."""
    cols = _unified_cols()
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    return df[cols]


def _load_github(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    df = df.rename(
        columns={
            "repo_full_name": "full_id",
            "stars": "metric_stars",
            "forks": "metric_forks",
        }
    )
    df["metric_downloads"] = ""
    df["metric_likes"] = ""
    df["hf_type"] = ""
    return _align_to_schema(df)


def _load_hf(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    df = df.rename(
        columns={
            "hf_id": "full_id",
            "downloads": "metric_downloads",
            "likes": "metric_likes",
        }
    )
    df["metric_stars"] = ""
    df["metric_forks"] = ""
    return _align_to_schema(df)


def _unified_cols() -> list[str]:
    return [
        "project_id",
        "platform",
        "full_id",
        "project_name",
        "hf_type",
        "tags",
        "metric_stars",
        "metric_forks",
        "metric_downloads",
        "metric_likes",
        "created_at",
        "open_ai_related",
        "ai_evidence",
        "ai_confidence",
        "prominent_flag",
    ]


def main():
    print("=" * 60)
    print("Step 1c: Merge GitHub + HuggingFace candidates")
    print("=" * 60)

    frames = []
    if GH_PATH.exists():
        gh = _load_github(GH_PATH)
        print(f"  GitHub candidates : {len(gh)}")
        frames.append(gh)
    else:
        print(f"  ⚠️  {GH_PATH} not found – skipping GitHub")

    if HF_PATH.exists():
        hf = _load_hf(HF_PATH)
        print(f"  HF candidates     : {len(hf)}")
        frames.append(hf)
    else:
        print(f"  ⚠️  {HF_PATH} not found – skipping HuggingFace")

    if not frames:
        print("❌ No candidate files found. Run step1a / step1b first.")
        return

    merged = pd.concat(frames, ignore_index=True)

    # Ensure flag columns are numeric
    for col in ["open_ai_related", "prominent_flag"]:
        merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0).astype(int)

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    # Full result
    full_path = DATA_PROCESSED / "project_filtering_result.csv"
    merged.to_csv(full_path, index=False)
    print(f"\n✅ Full result  : {len(merged)} rows → {full_path}")

    # Prominent-only subset
    prominent = merged[merged["prominent_flag"] == 1].copy()
    prom_path = DATA_PROCESSED / "prominent_projects_master.csv"
    prominent.to_csv(prom_path, index=False)
    print(f"✅ Prominent only: {len(prominent)} rows → {prom_path}")

    # Summary
    print("\n📊 Breakdown:")
    print(merged.groupby(["platform", "open_ai_related", "prominent_flag"]).size()
          .unstack(fill_value=0).to_string())

    ai_conf = merged[merged["open_ai_related"] == 1]["ai_confidence"].value_counts()
    print(f"\n📊 AI confidence distribution (open_ai_related=1):\n{ai_conf.to_string()}")


if __name__ == "__main__":
    main()
