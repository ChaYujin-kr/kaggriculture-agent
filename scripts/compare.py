"""Evaluate several candidate agents against the same opponent pool and seeds.

usage: python scripts/compare.py --cands a.py b.py --opps x.py y.py --seeds 4 [--seed0 700]
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import league  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cands", nargs="+", required=True)
    ap.add_argument("--opps", nargs="+", required=True)
    ap.add_argument("--seeds", type=int, default=4)
    ap.add_argument("--seed0", type=int, default=700)
    a = ap.parse_args()
    seeds = list(range(a.seed0, a.seed0 + a.seeds))
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as pool:
        for c in a.cands:
            t = time.time()
            out = league.evaluate(c, a.opps, seeds, pool=pool)
            print(f"### {os.path.basename(c)}  ({time.time() - t:.0f}s)")
            print(league.summarize(out), flush=True)
