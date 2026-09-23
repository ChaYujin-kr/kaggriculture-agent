"""Greedy search over the thresholds that scripts/knob_screen.py found live, scored by mirror duels
against the current champion.

The ladder is full of near-clones of the champion, so "beats the champion in a mirror" is the signal
that matters; mirrors are also paired (same seed, both seats), which keeps the noise down.

usage: python scripts/tune_thresholds.py --live research/live_thresholds.json --seeds 8 --workers 2 --top 30
Best -> tuning/best_thresholds.json, log -> tuning/thresholds_log.jsonl
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


def values_for(v):
    """Candidate settings around the current value."""
    if isinstance(v, float):
        return [round(v * 0.7, 4), round(v * 1.3, 4)]
    if abs(v) <= 4:
        return [v - 1, v + 1]
    if abs(v) <= 24:
        return [v - 2, v + 2]
    return [int(v * 0.8), int(v * 1.2)]


def result(out):
    rs = [r for v in out.values() for r in v]
    w = sum(1 for r in rs if r[0] > r[1]) + 0.5 * sum(1 for r in rs if r[0] == r[1])
    return w, len(rs), statistics.mean(r[0] - r[1] for r in rs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default=os.path.join(ROOT, "research", "pool_knobs", "champ_knobs.py"))
    ap.add_argument("--champion", default=os.path.join(ROOT, "submissions", "hybrid2965_tuned.py"))
    ap.add_argument("--live", default=os.path.join(ROOT, "research", "live_thresholds.json"))
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--seed0", type=int, default=30000)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--out", default=os.path.join(ROOT, "tuning", "best_thresholds.json"))
    a = ap.parse_args()
    live = {k: d for k, d in json.load(open(a.live)).items() if d.get("live")}
    ranked = sorted(live.items(), key=lambda kv: -abs(kv[1]["delta"]))[: a.top]
    print(f"{len(live)} live thresholds; tuning the {len(ranked)} with the largest effect", flush=True)
    seeds = list(range(a.seed0, a.seed0 + a.seeds))
    pool = ProcessPoolExecutor(max_workers=a.workers)
    log = open(os.path.join(ROOT, "tuning", "thresholds_log.jsonl"), "a")
    best, best_w, best_m = {}, None, None
    base = league.evaluate(a.agent, [a.champion], seeds, params={"flags": {}}, pool=pool)
    best_w, n, best_m = result(base)
    print(f"baseline (identical code) {best_w}/{n} margin {best_m:+.0f}", flush=True)
    for k, d in ranked:
        for v in values_for(d["default"]):
            trial = dict(best)
            trial[k] = v
            t = time.time()
            out = league.evaluate(a.agent, [a.champion], seeds, params={"flags": trial}, pool=pool)
            w, n, m = result(out)
            keep = (w, m) > (best_w, best_m)
            log.write(json.dumps({"knob": k, "value": v, "wins": w, "games": n, "margin": round(m),
                                  "keep": keep, "secs": round(time.time() - t)}) + "\n")
            log.flush()
            print(f"{k:<22} {str(d['default']):>8} -> {str(v):>8}  {w:4.1f}/{n} margin {m:+8.0f}"
                  f"  {'KEEP' if keep else ''}", flush=True)
            if keep:
                best, best_w, best_m = trial, w, m
                json.dump(best, open(a.out, "w"), indent=1)
    print("best thresholds:", best, f"{best_w}/{n}")
    pool.shutdown()


if __name__ == "__main__":
    main()
