"""Find every module-level numeric/bool constant in an agent file and screen which ones actually
change play. Dead knobs waste tuning budget, so this runs one cheap perturbation per knob.

usage: python scripts/knob_screen.py --agent research/pool/hybrid2965.py --seeds 1
Writes research/live_knobs.json: {knob: {"default":v, "live":bool, "delta":float}}
"""
import argparse
import ast
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import league  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {"_R37_PRICE_FLOOR", "_R37_HINGE_GAIN", "_RELEASE_ERRORS"}  # engine constants / counters


def constants(path):
    """Module-level `NAME = <number|bool>` assignments (tapes and structures are skipped)."""
    tree = ast.parse(open(path, encoding="utf-8").read())
    out = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        t = node.targets[0]
        if not isinstance(t, ast.Name) or not t.id.isupper() and not t.id.lstrip("_").isupper():
            continue
        try:
            v = ast.literal_eval(node.value)
        except Exception:
            continue
        if isinstance(v, bool) or (isinstance(v, (int, float)) and abs(v) < 1e7):
            if t.id not in SKIP:
                out[t.id] = v
    return out


def perturb(v):
    if isinstance(v, bool):
        return not v
    if isinstance(v, int):
        return v + max(1, abs(v) // 4)
    return round(v * 1.3 + 0.1, 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default=os.path.join(ROOT, "research", "pool", "hybrid2965.py"))
    ap.add_argument("--opp", default=os.path.join(ROOT, "research", "pool", "morewheat.py"))
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--seed0", type=int, default=4100)
    a = ap.parse_args()
    consts = constants(a.agent)
    print(f"{len(consts)} module-level constants found", flush=True)
    seeds = list(range(a.seed0, a.seed0 + a.seeds))
    pool = ProcessPoolExecutor(max_workers=os.cpu_count())
    base = league.evaluate(a.agent, [a.opp], seeds, params={"flags": {}}, pool=pool)
    base_scores = [r[0] for rs in base.values() for r in rs]
    print("baseline", base_scores, flush=True)
    live = {}
    for k, v in consts.items():
        nv = perturb(v)
        out = league.evaluate(a.agent, [a.opp], seeds, params={"flags": {k: nv}}, pool=pool)
        sc = [r[0] for rs in out.values() for r in rs]
        delta = sum(s - b for s, b in zip(sc, base_scores)) / len(sc)
        live[k] = {"default": v, "trial": nv, "live": sc != base_scores, "delta": round(delta)}
        print(f"{k:<28} {str(v):>8} -> {str(nv):>8}  {'LIVE' if sc != base_scores else 'dead '}"
              f"  delta {delta:+9.0f}", flush=True)
    json.dump(live, open(os.path.join(ROOT, "research", "live_knobs.json"), "w"), indent=1)
    n = sum(1 for d in live.values() if d["live"])
    print(f"{n}/{len(live)} knobs change play")
    pool.shutdown()


if __name__ == "__main__":
    main()
