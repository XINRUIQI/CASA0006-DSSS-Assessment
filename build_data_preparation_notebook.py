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
    ("step_01_github_discovery.py", "Step 1/13 — GitHub 开放 AI 仓库发现", "原 `step1a_filter_github.py`"),
    ("step_02_huggingface_discovery.py", "Step 2/13 — Hugging Face 项目发现", "原 `step1b_filter_huggingface.py`"),
    ("step_03_merge_candidates.py", "Step 3/13 — 合并 GitHub + HF 候选", "原 `step1c_merge_candidates.py`"),
    ("step_04_github_locations.py", "Step 4/13 — GitHub owner 地理位置", "原 `step3a_fetch_github_locations.py`"),
    ("step_05_hf_author_locations.py", "Step 5/13 — HF 作者地理位置", "原 `step3a_hf_fetch_user_locations.py`"),
    ("step_06_clean_map_locations.py", "Step 6/13 — 清洗并映射城市", "原 `step3b_clean_and_map_locations.py`"),
    ("step_07_geocode_unmatched.py", "Step 7/13 — Nominatim 补地理编码", "原 `step3c_geocode_unmatched.py`"),
    ("step_08_build_city_list.py", "Step 8/13 — 构建城市列表", "原 `step3d_build_city_list.py`"),
    ("step_09_contributors_participation.py", "Step 9/13 — 贡献者与参与事件", "原 `step4_fetch_contributors.py`"),
    ("step_10_hf_derivation_edges.py", "Step 10/13 — HF base_model 衍生边", "原 `step5b_build_hf_derivation_edges.py` · 须在 Step 11 前运行"),
    ("step_11_core_tables.py", "Step 11/13 — 三张核心分析表", "原 `step5_build_core_tables.py`"),
    ("step_12_augment_external.py", "Step 12/13 — 外部社会经济属性", "原 `step6_augment_city_attributes.py`"),
    ("step_13_enrich_attributes.py", "Step 13/13 — 建模用衍生特征", "原 `step6b_enrich_city_features.py`"),
]


def strip_sys_path(src: str) -> str:
    return SYS_PATH_LINE.sub("", src)


def main():
    intro = f"""# 数据准备流水线（Steps 1–13）

本 notebook **整段嵌入** `ELSE/scripts/` 下已重命名的脚本，与终端 `python ELSE/scripts/<文件>.py` 行为一致（需 `config.py`）。

**运行方式：** 在**仓库根目录**打开本 notebook，须**首先**运行下方 **「0. 环境与路径」** 中的代码单元（注入 `sys.path`，否则 `from config import …` 失败），再按需顺序执行各 Step 代码单元。各脚本末尾的 `if __name__ == "__main__": main()` 在 notebook 中需**手动调用** `main()` 或在终端运行对应 `.py` 文件。

| Step | 脚本文件 | 说明 |
|------|----------|------|
"""
    for fn, title, legacy in FILES:
        intro += f"| {title} | `{fn}` | {legacy} |\n"

    intro += """
**依赖：** `ELSE/scripts/config.py`（未嵌入；通过 `sys.path` 加载）。

**离线链（示例）：** 在已有原始 CSV 的前提下，可依次调用 Step 3→6→8→10→11→12→13 的 `main()`。"""
    cells = []

    cells.append({"cell_type": "markdown", "metadata": {}, "source": intro.splitlines(keepends=True)})

    section0_md = """---
## 0. 环境与路径

以下说明与**紧随其后的代码单元**一致；请先阅读，再**运行该代码单元**（不要跳过）。

- **工作目录**：Jupyter 的当前目录应为仓库根目录（与 `ELSE/`、`data/` 同级）。
- **`_ROOT`**：`Path.cwd()`，即项目根。
- **`_SCRIPTS`**：`ELSE/scripts`，内含 `config.py` 与各 `step_*.py`。
- **`sys.path`**：将 `_SCRIPTS` 置于首位后，`import config` 时 `config.PROJECT_ROOT` 仍为「`ELSE` 的上一级」，与终端执行脚本行为一致。

下面代码块内容与下一单元**相同**（便于复制到其它环境或核对）：

```python
from pathlib import Path
import sys

_ROOT = Path.cwd().resolve()
_SCRIPTS = _ROOT / "ELSE" / "scripts"
_CFG = _SCRIPTS / "config.py"
if not _CFG.exists():
    raise RuntimeError(f"请在仓库根目录打开 notebook：找不到 {_CFG}")

_SCRIPTS_STR = str(_SCRIPTS.resolve())
if _SCRIPTS_STR not in sys.path:
    sys.path.insert(0, _SCRIPTS_STR)

print(f"OK: sys.path 已包含 ELSE/scripts，config 自 {_CFG}")
```
"""
    cells.append({"cell_type": "markdown", "metadata": {}, "source": section0_md.splitlines(keepends=True)})

    setup = """# 0. 环境与路径 — 可运行单元（须先执行）
from pathlib import Path
import sys

_ROOT = Path.cwd().resolve()
_SCRIPTS = _ROOT / "ELSE" / "scripts"
_CFG = _SCRIPTS / "config.py"
if not _CFG.exists():
    raise RuntimeError(f"请在仓库根目录打开 notebook：找不到 {_CFG}")

_SCRIPTS_STR = str(_SCRIPTS.resolve())
if _SCRIPTS_STR not in sys.path:
    sys.path.insert(0, _SCRIPTS_STR)

print(f"OK: sys.path 已包含 ELSE/scripts，config 自 {_CFG}")
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
                f"源文件：`ELSE/scripts/{fn}`\n",
                "\n",
                f"执行：`import {mod} as _m; _m.main()` 或在终端 `python ELSE/scripts/{fn}`。\n",
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
