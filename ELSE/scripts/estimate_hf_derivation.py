"""
Estimate the share of HF prominent projects that participate in
derivation relationships (base_model graph), and the depth of those
chains.

We already stored each HF object's tags (top-30) in `hf_candidates.csv`
during step 1b. The HF convention encodes derivation as either:
  - `base_model:<owner>/<name>`              (generic / legacy)
  - `base_model:finetune:<owner>/<name>`     (fine-tune)
  - `base_model:quantized:<owner>/<name>`    (quantization)
  - `base_model:adapter:<owner>/<name>`      (LoRA / adapter)
  - `base_model:merge:<owner>/<name>`        (model merge)

This script:
  1. Loads HF prominent models from prominent_projects_master.csv
  2. Parses each model's stored tags to extract base_model edges
  3. Reports descendant share, ancestor share, type breakdown
  4. Walks the resulting directed graph to estimate chain depth
     (multi-level: A -> B -> C -> ...)
  5. Cross-checks against ALL HF candidates (open-AI related, not just
     prominent) to estimate ancestor in-degree more accurately
"""

import sys
import re
from pathlib import Path
from collections import defaultdict, Counter, deque

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "data" / "processed" / "prominent_projects_master.csv"
CAND = ROOT / "data" / "processed" / "project_filtering_result.csv"

REL_PATTERN = re.compile(
    r"^base_model:(?:(finetune|quantized|adapter|merge):)?(.+)$",
    re.IGNORECASE,
)


def parse_base_model_tags(tag_str: str):
    """Return list of (relation, parent_id) tuples from a stored tag string."""
    if not tag_str or pd.isna(tag_str):
        return []
    out = []
    for t in tag_str.split("|"):
        t = t.strip()
        m = REL_PATTERN.match(t)
        if m:
            rel = (m.group(1) or "generic").lower()
            parent = m.group(2).strip()
            if "/" in parent:  # must look like owner/name
                out.append((rel, parent))
    return out


def main():
    print("=" * 64)
    print("HF derivation graph estimator")
    print("=" * 64)

    df = pd.read_csv(MASTER, dtype=str)
    hf = df[df["platform"] == "HuggingFace"].copy()
    hf_models = hf[hf["hf_type"] == "model"].copy()
    print(f"\nHF prominent objects total: {len(hf)}")
    print(f"  models  : {len(hf_models)}")
    print(f"  datasets: {(hf['hf_type']=='dataset').sum()}  (datasets/spaces have no base_model field)")
    print(f"  spaces  : {(hf['hf_type']=='space').sum()}")

    # ── Parse descendant relations (model -> base_model) ──────────────────────
    edges = []   # list of (child_id, parent_id, relation)
    child_relations = defaultdict(list)   # child -> [(rel, parent), ...]
    for _, row in hf_models.iterrows():
        child = row["full_id"]
        rels = parse_base_model_tags(row["tags"])
        if not rels:
            continue
        # Some models repeat the same parent under both generic and typed form
        # → de-duplicate (parent, relation), preferring typed over generic
        seen_parents = {}
        for rel, parent in rels:
            if parent not in seen_parents or seen_parents[parent] == "generic":
                seen_parents[parent] = rel
        for parent, rel in seen_parents.items():
            edges.append((child, parent, rel))
            child_relations[child].append((rel, parent))

    print("\n" + "─" * 64)
    print("1. Descendant share among HF prominent MODELS")
    print("─" * 64)
    has_parent = sum(1 for _ in child_relations)
    print(f"  Models declaring at least one base_model: {has_parent} "
          f"({has_parent/len(hf_models)*100:.1f}% of {len(hf_models)})")

    # By relation type (count each child once, by its dominant relation)
    rel_count = Counter()
    for c, rels in child_relations.items():
        # dominant: first non-generic, else generic
        non_generic = [r for r, _ in rels if r != "generic"]
        rel_count[non_generic[0] if non_generic else "generic"] += 1
    print("  Breakdown by relation type:")
    for r, n in rel_count.most_common():
        print(f"    {r:10s} : {n:5d} ({n/has_parent*100:5.1f}% of descendants)")

    multi_parent = sum(1 for c, rels in child_relations.items() if len({p for _, p in rels}) > 1)
    print(f"  Models with multiple distinct parents (e.g. merges): {multi_parent} ({multi_parent/has_parent*100:.1f}% of descendants)")

    # ── Ancestor share: among prominent models, who is referenced by others ──
    print("\n" + "─" * 64)
    print("2. Ancestor share — within prominent set only")
    print("─" * 64)
    parent_indegree = Counter(p for _, p, _ in edges)
    prominent_ids = set(hf_models["full_id"])
    prom_ancestors = {p for p in parent_indegree if p in prominent_ids}
    print(f"  Distinct parents referenced by ≥1 prominent descendant: {len(parent_indegree)}")
    print(f"    of which are themselves prominent: {len(prom_ancestors)} "
          f"({len(prom_ancestors)/len(hf_models)*100:.1f}% of {len(hf_models)} prominent models)")

    # ── Cross-check using ALL open-AI-related HF candidates ──────────────────
    print("\n" + "─" * 64)
    print("3. Cross-check against ALL open-AI HF candidates (broader graph)")
    print("─" * 64)
    if CAND.exists():
        cand = pd.read_csv(CAND, dtype=str, usecols=["platform","hf_type","full_id","tags","open_ai_related","prominent_flag"])
        cand_hf_models = cand[(cand["platform"]=="HuggingFace") & (cand["hf_type"]=="model") & (cand["open_ai_related"]=="1")]
        print(f"  Open-AI HF model candidates (any prominence): {len(cand_hf_models)}")

        all_edges = []
        all_child_rel = defaultdict(list)
        for _, row in cand_hf_models.iterrows():
            child = row["full_id"]
            rels = parse_base_model_tags(row["tags"])
            if not rels:
                continue
            seen = {}
            for rel, parent in rels:
                if parent not in seen or seen[parent] == "generic":
                    seen[parent] = rel
            for parent, rel in seen.items():
                all_edges.append((child, parent, rel))
                all_child_rel[child].append((rel, parent))

        all_indegree = Counter(p for _, p, _ in all_edges)
        # how often each prominent model is referenced as parent in the broader graph
        prom_ancestor_full = sum(1 for p in prominent_ids if p in all_indegree)
        print(f"  Prominent models referenced as base_model by ≥1 open-AI candidate: "
              f"{prom_ancestor_full} ({prom_ancestor_full/len(hf_models)*100:.1f}% of prominent)")
        print(f"  Top 15 ancestors (in-degree among open-AI HF model candidates):")
        for p, k in all_indegree.most_common(15):
            mark = "★" if p in prominent_ids else " "
            print(f"    {mark} {p:60s}  in-deg={k}")

        # Total share that "participates" in derivation graph (either child or parent),
        # within prominent models
        prom_in_graph = (set(child_relations.keys()) | set(p for p in prominent_ids if p in all_indegree))
        print(f"\n  → Prominent HF models participating in derivation graph "
              f"(as descendant OR as ancestor): {len(prom_in_graph)} "
              f"({len(prom_in_graph)/len(hf_models)*100:.1f}% of {len(hf_models)} prominent models)")

        # ── Multi-level depth analysis on the broader graph ──────────────────
        print("\n" + "─" * 64)
        print("4. Multi-level chain depth (broader open-AI HF graph)")
        print("─" * 64)
        # parent_of: child -> set of parents
        parent_of = defaultdict(set)
        for c, p, _ in all_edges:
            parent_of[c].add(p)

        nodes = set(parent_of.keys()) | {p for ps in parent_of.values() for p in ps}
        print(f"  Graph nodes (children + parents): {len(nodes)}")
        print(f"  Graph edges                     : {len(all_edges)}")

        # depth(node) = longest chain length from node walking up parents
        # iterative memoization with cycle protection
        depth_memo = {}

        def depth(n, stack):
            if n in depth_memo:
                return depth_memo[n]
            if n in stack:
                return 0   # cycle guard
            parents = parent_of.get(n, set())
            if not parents:
                depth_memo[n] = 0
                return 0
            stack.add(n)
            best = 0
            for p in parents:
                d = depth(p, stack) + 1
                if d > best:
                    best = d
            stack.discard(n)
            depth_memo[n] = best
            return best

        for n in list(nodes):
            depth(n, set())

        depth_dist = Counter(depth_memo.values())
        print("  Distribution of chain depth (= #edges to root from each node):")
        for d in sorted(depth_dist):
            print(f"    depth = {d} : {depth_dist[d]:6d} nodes")

        multi_level_nodes = sum(v for d, v in depth_dist.items() if d >= 2)
        print(f"  Nodes whose chain depth ≥ 2 (i.e. grandchild or deeper): {multi_level_nodes}")

        # Show some example deep chains
        deepest = sorted(depth_memo.items(), key=lambda x: -x[1])[:10]
        print("\n  Examples of deepest nodes (chain length):")
        for n, d in deepest:
            if d == 0:
                continue
            chain = [n]
            cur = n
            visited = set([cur])
            while True:
                parents = parent_of.get(cur, set())
                if not parents:
                    break
                # pick the parent with largest depth to reconstruct longest chain
                nxt = max(parents, key=lambda x: depth_memo.get(x, 0))
                if nxt in visited:
                    break
                visited.add(nxt)
                chain.append(nxt)
                cur = nxt
                if len(chain) > 10:
                    break
            print(f"    depth={d}: " + " → ".join(chain))


if __name__ == "__main__":
    main()
