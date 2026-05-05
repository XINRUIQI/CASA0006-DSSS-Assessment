#!/usr/bin/env python3
"""Regenerate Data_Preparation_Pipeline.ipynb from ELSE/scripts/step_*.py (full source)."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "ELSE" / "scripts"
OUT = ROOT / "Data_Preparation_Pipeline.ipynb"

SYS_PATH_LINE = re.compile(
    r"^sys\.path\.insert\(0,\s*str\(Path\(__file__\)\.resolve\(\)\.parent\)\)\s*\n",
    re.MULTILINE,
)

FILES = [
    ("step_01_github_discovery.py", "Step 1/13 — GitHub open AI repository discovery", "formerly `step1a_filter_github.py`"),
    ("step_02_huggingface_discovery.py", "Step 2/13 — Hugging Face project discovery", "formerly `step1b_filter_huggingface.py`"),
    ("step_03_merge_candidates.py", "Step 3/13 — Merge GitHub + HF candidates", "formerly `step1c_merge_candidates.py`"),
    ("step_04_github_locations.py", "Step 4/13 — GitHub owner geolocation", "formerly `step3a_fetch_github_locations.py`"),
    ("step_05_hf_author_locations.py", "Step 5/13 — HF author geolocation", "formerly `step3a_hf_fetch_user_locations.py`"),
    ("step_06_clean_map_locations.py", "Step 6/13 — Clean and map cities", "formerly `step3b_clean_and_map_locations.py`"),
    ("step_07_geocode_unmatched.py", "Step 7/13 — Nominatim geocoding for unmatched", "formerly `step3c_geocode_unmatched.py`"),
    ("step_08_build_city_list.py", "Step 8/13 — Build city list", "formerly `step3d_build_city_list.py`"),
    ("step_09_contributors_participation.py", "Step 9/13 — Contributors and participation events", "formerly `step4_fetch_contributors.py`"),
    ("step_10_hf_derivation_edges.py", "Step 10/13 — HF base_model derivation edges", "formerly `step5b_build_hf_derivation_edges.py` · run before Step 11"),
    ("step_11_core_tables.py", "Step 11/13 — Three core analytical tables", "formerly `step5_build_core_tables.py`"),
    ("step_12_augment_external.py", "Step 12/13 — External socioeconomic attributes", "formerly `step6_augment_city_attributes.py`"),
    ("step_13_enrich_attributes.py", "Step 13/13 — Derived features for modeling", "formerly `step6b_enrich_city_features.py`"),
]


def strip_sys_path(src: str) -> str:
    return SYS_PATH_LINE.sub("", src)


def main():
    intro = f"""# Data preparation pipeline (Steps 1–13)

This notebook **embeds in full** the renamed scripts under `ELSE/scripts/`, matching terminal `python ELSE/scripts/<file>.py` (requires `config.py`).

**How to run:** Open this notebook from the **repository root**. **First** run the code cell under **0. Environment and paths** below (injects `sys.path`; otherwise `from config import …` fails), then run each Step cell in order as needed. The `if __name__ == "__main__": main()` at the end of each script must be **invoked manually** as `main()` in the notebook, or run the corresponding `.py` in the terminal.

| Step | Script | Notes |
|------|--------|-------|
"""
    for fn, title, legacy in FILES:
        intro += f"| {title} | `{fn}` | {legacy} |\n"

    intro += """
**Dependencies:** `ELSE/scripts/config.py` (not embedded; loaded via `sys.path`).

**Offline chain (example):** With raw CSVs already present, you can call `main()` for Steps 3→6→8→10→11→12→13 in order."""
    cells = []

    cells.append({"cell_type": "markdown", "metadata": {}, "source": intro.splitlines(keepends=True)})

    section0_md = """---
## 0. Environment and paths

The following matches the **code cell immediately below**; read it, then **run that cell** (do not skip).

- **Working directory:** Jupyter's current directory should be the repo root (sibling of `ELSE/`, `data/`).
- **`_ROOT`:** `Path.cwd()`, i.e. project root.
- **`_SCRIPTS`:** `ELSE/scripts`, containing `config.py` and each `step_*.py`.
- **`sys.path`:** After inserting `_SCRIPTS` first, `import config` still resolves `config.PROJECT_ROOT` to the parent of `ELSE`, same as running scripts from the terminal.

The block below duplicates the next cell (handy for copy/paste or cross-check):

```python
from pathlib import Path
import sys

_ROOT = Path.cwd().resolve()
_SCRIPTS = _ROOT / "ELSE" / "scripts"
_CFG = _SCRIPTS / "config.py"
if not _CFG.exists():
    raise RuntimeError(f"Open notebook from repo root: {_CFG} not found")

_SCRIPTS_STR = str(_SCRIPTS.resolve())
if _SCRIPTS_STR not in sys.path:
    sys.path.insert(0, _SCRIPTS_STR)

print(f"OK: sys.path includes ELSE/scripts, config from {_CFG}")
```
"""
    cells.append({"cell_type": "markdown", "metadata": {}, "source": section0_md.splitlines(keepends=True)})

    setup = """# 0. Environment and paths — runnable cell (run first)
from pathlib import Path
import sys

_ROOT = Path.cwd().resolve()
_SCRIPTS = _ROOT / "ELSE" / "scripts"
_CFG = _SCRIPTS / "config.py"
if not _CFG.exists():
    raise RuntimeError(f"Open notebook from repo root: {_CFG} not found")

_SCRIPTS_STR = str(_SCRIPTS.resolve())
if _SCRIPTS_STR not in sys.path:
    sys.path.insert(0, _SCRIPTS_STR)

print(f"OK: sys.path includes ELSE/scripts, config from {_CFG}")
"""
    cells.append({"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": setup.splitlines(keepends=True)})

    for fn, title, legacy in FILES:
        path = SCRIPTS / fn
        text = path.read_text(encoding="utf-8")
        text = strip_sys_path(text)
        mod = fn.replace(".py", "")
        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "---\n",
                f"## {title}\n",
                "\n",
                f"**{legacy}**\n",
                "\n",
                f"Source: `ELSE/scripts/{fn}`\n",
                "\n",
                f"Run: `import {mod} as _m; _m.main()` or in terminal `python ELSE/scripts/{fn}`.\n",
            ],
        })
        cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": text.splitlines(keepends=True),
        })

    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11.0"},
        },
        "nbformat": 4,
        "nbformat_minor": 4,
    }
    OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
    print("Wrote", OUT, "cells:", len(cells))


if __name__ == "__main__":
    main()
