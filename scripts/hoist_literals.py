"""Expose an agent's hard-coded decision thresholds as tunable module constants.

Most of a tape agent's real decisions are numeric literals inside comparisons (`if price > 30`).
This rewrites each such literal into a module-level `_KNOB_n` constant with the same value, so the
generated file behaves identically but every threshold can now be overridden by the tuner.

usage: python scripts/hoist_literals.py --agent research/pool/hybrid2965.py --out research/pool_knobs/hybrid2965_knobs.py
Writes a sidecar <out>.map.json: {knob: {"value": v, "line": n, "context": "..."}}
"""
import argparse
import ast
import json
import os


def collect(tree):
    """Numeric literals used on either side of a comparison, inside a function."""
    hits = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(fn):
            if not isinstance(node, ast.Compare):
                continue
            for side in [node.left] + list(node.comparators):
                if (isinstance(side, ast.Constant) and isinstance(side.value, (int, float))
                        and not isinstance(side.value, bool) and abs(side.value) > 1):
                    hits.append(side)
    # deepest/last first so earlier offsets stay valid while we patch
    hits.sort(key=lambda n: (n.lineno, n.col_offset), reverse=True)
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=400)
    a = ap.parse_args()
    src = open(a.agent, encoding="utf-8").read()
    lines = src.splitlines(keepends=True)
    tree = ast.parse(src)
    hits = collect(tree)
    seen = set()
    mapping = {}
    n = 0
    for node in hits:
        key = (node.lineno, node.col_offset)
        if key in seen or len(mapping) >= a.limit:
            continue
        seen.add(key)
        name = f"_KNOB_{node.lineno}_{node.col_offset}"
        line = lines[node.lineno - 1]
        if node.end_lineno != node.lineno:
            continue
        lines[node.lineno - 1] = line[:node.col_offset] + name + line[node.end_col_offset:]
        mapping[name] = {"value": node.value, "line": node.lineno,
                         "context": line.strip()[:120]}
        n += 1
    # appended, not prepended: the file may start with __future__ imports, and these names are only
    # read when the agent runs, which is always after import
    footer = ["", "", "# Thresholds hoisted from comparisons by scripts/hoist_literals.py (values unchanged).",
              "# The base agent's logic is identical; only these names are now tunable."]
    footer += [f"{k} = {v['value']!r}" for k, v in mapping.items()]
    out_src = "".join(lines) + "\n".join(footer) + "\n"
    compile(out_src, a.out, "exec")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(out_src)
    json.dump(mapping, open(a.out + ".map.json", "w"), indent=1)
    print(f"hoisted {n} thresholds -> {a.out}")


if __name__ == "__main__":
    main()
