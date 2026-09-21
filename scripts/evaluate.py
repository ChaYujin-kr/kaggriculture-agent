"""Play local matches and report scores.

usage: python scripts/evaluate.py [agent_path] [opponent ...] [--games N]
Opponents: built-in names (random, starter, pass) or paths to .py agents.
"""
import argparse
import os
import statistics
import sys
import time
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def play(args):
    agent_path, opp, seed, swap = args
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"seed": seed}, debug=True)
    agents = [agent_path, opp] if not swap else [opp, agent_path]
    env.run(agents)
    final = env.steps[-1]
    me, other = (0, 1) if not swap else (1, 0)
    return opp, final[me].reward or 0.0, final[other].reward or 0.0, final[me].status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("agent", nargs="?", default=os.path.join(ROOT, "agents", "main.py"))
    ap.add_argument("opponents", nargs="*", default=["starter"])
    ap.add_argument("--games", type=int, default=4)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args()

    jobs = [(a.agent, opp, 1000 + g, g % 2 == 1) for opp in a.opponents for g in range(a.games)]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        results = list(ex.map(play, jobs))
    for opp in a.opponents:
        rs = [r for r in results if r[0] == opp]
        mine = [r[1] for r in rs]
        theirs = [r[2] for r in rs]
        wins = sum(1 for r in rs if r[1] > r[2])
        bad = [r[3] for r in rs if r[3] != "DONE"]
        print(f"vs {os.path.basename(opp):<12} win {wins}/{len(rs)}  me mean {statistics.mean(mine):9.0f} "
              f"(min {min(mine):7.0f})  opp mean {statistics.mean(theirs):9.0f}  {'ERR ' + str(bad) if bad else ''}")
    print(f"{len(jobs)} games in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    sys.exit(main())
