"""Round-robin a directory of agents on the fast simulator (both seats per seed) and rank them.

usage: python scripts/roundrobin.py research/pool --seeds 3 [--seed0 2000]
Ranking = total wins (ties count 0.5), then mean margin.
"""
import argparse
import glob
import itertools
import os
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import league  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--seed0", type=int, default=2000)
    a = ap.parse_args()
    agents = sorted(glob.glob(os.path.join(a.dir, "*.py")))
    names = [os.path.basename(p)[:-3] for p in agents]
    jobs, keys = [], []
    for (i, pa), (j, pb) in itertools.combinations(enumerate(agents), 2):
        for s in range(a.seed0, a.seed0 + a.seeds):
            for swap in (False, True):
                jobs.append((pa, None, pb, None, s, swap))
                keys.append((i, j))
    t = time.time()
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as ex:
        res = list(ex.map(league.run_pair, jobs, chunksize=1))
    wins, margin, games = defaultdict(float), defaultdict(float), defaultdict(int)
    h2h = defaultdict(float)
    for (i, j), (mi, mj) in zip(keys, res):
        w = 1.0 if mi > mj else 0.5 if mi == mj else 0.0
        wins[i] += w
        wins[j] += 1 - w
        h2h[(i, j)] += w
        h2h[(j, i)] += 1 - w
        margin[i] += mi - mj
        margin[j] += mj - mi
        games[i] += 1
        games[j] += 1
    order = sorted(range(len(agents)), key=lambda k: (-wins[k], -margin[k]))
    per_pair = 2 * a.seeds
    print(f"{len(jobs)} games in {time.time() - t:.0f}s  (per pair {per_pair})")
    print(f"{'agent':<12} {'wins':>6} {'games':>5} {'margin/g':>9}  | " + " ".join(f"{names[k][:6]:>6}" for k in order))
    for k in order:
        row = " ".join(f"{h2h[(k, m)]:6.1f}" if m != k else "     -" for m in order)
        print(f"{names[k]:<12} {wins[k]:6.1f} {games[k]:5d} {margin[k] / games[k]:+9.0f}  | {row}")
