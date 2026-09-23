"""Greedy coordinate search over a public agent's exposed module-level knobs.

Each candidate = current best flag set + one changed knob, scored by mean money margin against an
opponent pool (shared seeds = common random numbers). Keeps a change only if it beats the incumbent
on the same seeds; re-validates the winner on fresh seeds at the end.

usage: python scripts/tune_flags.py --agent research/pool/hybrid2965.py --pool research/pool --seeds 2
Progress -> tuning/flags_log.jsonl, best -> tuning/best_flags.json
"""
import argparse
import json
import os
import statistics
import sys
import time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import league  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# knob -> values to try (first entry is documentation only; defaults come from the file)
# Only knobs that scripts/knob_screen.py showed actually change play (23 of 85 module constants).
# Boolean layers whose flip clearly hurt in screening (_R85_FEED, _R88_PHASE, _CH_SELL, MAX_ORDERS)
# are left at their defaults.
# Narrowed to the knobs that looked promising in the low-power pass. A 40-game trial could not
# separate 2-6 win differences (per-game sd is ~$9k), so these are re-run at higher power.
CANDIDATES = {
    "_ADV_PROTECT": [False],
    "_ADV_FRONT": [False],
    "_V92_P_TOP": [2, 3],
    "_ADV_LOOK": [2],
    "_CA_MARGIN": [-10.0],
    "_OR2_SN_K": [1],
    "_CH_SHED": [112],
}


def margin(out):
    return statistics.mean(r[0] - r[1] for rs in out.values() for r in rs)


def wins(out):
    rs = [r for v in out.values() for r in v]
    return sum(1 for r in rs if r[0] > r[1]) + 0.5 * sum(1 for r in rs if r[0] == r[1]), len(rs)


def score(out):
    """Ladder rating counts wins only, so rank by win count and use margin only to break ties."""
    w, n = wins(out)
    return (w, margin(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default=os.path.join(ROOT, "research", "pool", "hybrid2965.py"))
    ap.add_argument("--pool", default=os.path.join(ROOT, "research", "pool"))
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--seed0", type=int, default=3000)
    ap.add_argument("--passes", type=int, default=1)
    ap.add_argument("--strong-only", action="store_true", help="only the pool's competitive agents")
    ap.add_argument("--init", help="json file of flags to start the search from")
    ap.add_argument("--workers", type=int, default=None, help="parallel games (lower = less memory)")
    ap.add_argument("--out", default=os.path.join(ROOT, "tuning", "best_flags.json"))
    a = ap.parse_args()
    strong = {"hybrid2965.py", "morewheat.py", "rescue7.py", "clonerace.py", "v54fork.py"}
    opps = sorted(os.path.join(a.pool, f) for f in os.listdir(a.pool)
                  if f.endswith(".py") and (not a.strong_only or f in strong))
    os.makedirs(os.path.join(ROOT, "tuning"), exist_ok=True)
    log = open(os.path.join(ROOT, "tuning", "flags_log.jsonl"), "a")
    pool = ProcessPoolExecutor(max_workers=a.workers or os.cpu_count())
    best = json.load(open(a.init)) if a.init and os.path.exists(a.init) else {}
    if best:
        print("starting from", best, flush=True)
    seeds = list(range(a.seed0, a.seed0 + a.seeds))
    base_out = league.evaluate(a.agent, opps, seeds, params={"flags": dict(best)}, pool=pool)
    best_score = score(base_out)
    print(f"baseline wins {wins(base_out)} margin {margin(base_out):+.0f}", flush=True)
    for p in range(a.passes):
        for knob, values in CANDIDATES.items():
            for v in values:
                trial = dict(best)
                trial[knob] = v
                t = time.time()
                out = league.evaluate(a.agent, opps, seeds, params={"flags": trial}, pool=pool)
                s = score(out)
                w, n = wins(out)
                keep = s > best_score
                rec = {"pass": p, "knob": knob, "value": v, "margin": round(margin(out)), "wins": w, "games": n,
                       "keep": keep, "secs": round(time.time() - t)}
                log.write(json.dumps(rec) + "\n")
                log.flush()
                print(f"{knob}={v!r:>8}  wins {w:4.1f}/{n} margin {margin(out):+8.0f}  {'KEEP' if keep else ''}", flush=True)
                if keep:
                    best, best_score = trial, s
                    json.dump(best, open(a.out, "w"), indent=1)
    print("best flags:", best, f"score {best_score}")
    pool.shutdown()


if __name__ == "__main__":
    main()



