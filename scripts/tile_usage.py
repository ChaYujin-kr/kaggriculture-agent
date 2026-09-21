"""Find tiles a (tape-driven) agent never occupies, across seeds and seats, plus empty-tile counts per day.

usage: python scripts/tile_usage.py <agent.py> <opponent.py> --seeds 6
Writes research/tile_usage.json: {"never_used": [[x, y], ...], "first_use_step": {"x,y": step}}.
"""
import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fastsim  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(job):
    a_path, b_path, seed, swap = job
    a = fastsim.load_agent(a_path, "a")
    b = fastsim.load_agent(b_path, "b")
    first_use = {}
    unlocked_empty = {}
    me_seat = 1 if swap else 0

    def watch(obs):
        act = a(obs)
        try:
            tiles = obs["farms"][obs["player"]]["tiles"]
            empties = 0
            for y, row in enumerate(tiles):
                for x, t in enumerate(row):
                    if isinstance(t, dict) and t.get("kind") != "WEED":
                        first_use.setdefault(f"{x},{y}", obs["step"])
                    elif t is None:
                        empties += 1
            if obs["hour"] == 12:
                unlocked_empty[obs["day"]] = empties
        except Exception:
            pass
        return act

    res = fastsim.play(b, watch, seed) if swap else fastsim.play(watch, b, seed)
    return first_use, unlocked_empty, res[me_seat]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("agent")
    ap.add_argument("opp")
    ap.add_argument("--seeds", type=int, default=6)
    a = ap.parse_args()
    jobs = [(a.agent, a.opp, 900 + s, sw) for s in range(a.seeds) for sw in (False, True)]
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as ex:
        results = list(ex.map(run, jobs))
    first = {}
    for fu, _, _ in results:
        for k, v in fu.items():
            first[k] = min(v, first.get(k, 10**9))
    never = [[x, y] for y in range(10) for x in range(10) if f"{x},{y}" not in first]
    print("scores:", [round(r[2]) for r in results])
    print("never-used tiles:", len(never), never)
    days = sorted(results[0][1])
    avg_empty = {d: round(sum(r[1].get(d, 0) for r in results) / len(results), 1) for d in days}
    print("avg empty unlocked tiles at noon by day:", avg_empty)
    json.dump({"never_used": never, "first_use_step": first},
              open(os.path.join(ROOT, "research", "tile_usage.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
