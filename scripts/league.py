"""Parallel head-to-head evaluation on the fast simulator (both seats per seed).

usage: python scripts/league.py agents/main.py agents/archive/v1.py starter --seeds 8
"""
import argparse
import os
import statistics
import sys
import time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fastsim  # noqa: E402

_CACHE = {}


def _agent(path, tag, params):
    return fastsim.load_agent(path, tag, params)


def run_pair(job):
    """job = (agent_path, params, opp_path, opp_params, seed, swap) -> (my, opp)"""
    a_path, a_params, b_path, b_params, seed, swap = job
    a = _agent(a_path, "me", a_params)
    b = _agent(b_path, "opp", b_params)
    if swap:
        r = fastsim.play(b, a, seed)
        return r[1], r[0]
    r = fastsim.play(a, b, seed)
    return r[0], r[1]


def evaluate(agent_path, opponents, seeds, params=None, workers=None, pool=None):
    """Returns {opp: [(my, their), ...]} for each opponent over seeds x both seats."""
    jobs, keys = [], []
    for opp in opponents:
        opp_path, opp_params = (opp if isinstance(opp, tuple) else (opp, None))
        for s in seeds:
            for swap in (False, True):
                jobs.append((agent_path, params, opp_path, opp_params, s, swap))
                keys.append(opp_path if not opp_params else f"{opp_path}*")
    ex = pool or ProcessPoolExecutor(max_workers=workers or os.cpu_count())
    try:
        res = list(ex.map(run_pair, jobs))
    finally:
        if pool is None:
            ex.shutdown()
    out = {}
    for k, r in zip(keys, res):
        out.setdefault(k, []).append(r)
    return out


def summarize(out):
    lines = []
    for opp, rs in out.items():
        mine = [r[0] for r in rs]
        wins = sum(1 for r in rs if r[0] > r[1]) + 0.5 * sum(1 for r in rs if r[0] == r[1])
        margin = statistics.mean(r[0] - r[1] for r in rs)
        lines.append(f"vs {os.path.basename(str(opp)):<14} win {wins:4.1f}/{len(rs):<3} mean {statistics.mean(mine):8.0f} "
                     f"min {min(mine):7.0f}  margin {margin:+8.0f}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("agent")
    ap.add_argument("opponents", nargs="+")
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--seed0", type=int, default=100)
    a = ap.parse_args()
    t = time.time()
    out = evaluate(a.agent, a.opponents, list(range(a.seed0, a.seed0 + a.seeds)))
    print(summarize(out))
    print(f"{sum(len(v) for v in out.values())} games in {time.time() - t:.0f}s")


if __name__ == "__main__":
    main()
