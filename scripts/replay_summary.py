"""Summarize downloaded ladder replays: who played, final money, and each side's farm trajectory.

usage: python scripts/replay_summary.py replays/*.json [--me TEAMNAME] [--days]
"""
import argparse
import glob
import json
from collections import Counter


def mix(tiles):
    c = Counter()
    for row in tiles:
        for t in row:
            if t is None or t == "LOCKED":
                continue
            if t.get("kind") == "PLANT":
                c[t["crop"][:3]] += 1
            elif t.get("animal"):
                c[t["animal"][:3]] += 1
            else:
                c[t["kind"][:4]] += 1
    return " ".join(f"{k}:{v}" for k, v in sorted(c.items()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--days", action="store_true", help="print per-3-day trajectory")
    a = ap.parse_args()
    files = [f for p in a.files for f in glob.glob(p)]
    for f in sorted(files):
        r = json.load(open(f, encoding="utf-8"))
        names = r.get("info", {}).get("TeamNames") or ["?", "?"]
        steps = r["steps"]
        final = [s.get("reward") for s in steps[-1]]
        status = [s.get("status") for s in steps[-1]]
        print(f"== {f.split('episode-')[-1][:9]}  {names}  final={final} status={status}")
        if a.days:
            for d in list(range(0, 30, 3)) + [29]:
                i = min(d * 24, len(steps) - 1)
                obs = steps[i][0]["observation"]
                line = f"  d{d:2d} "
                for p in range(2):
                    fm = obs["farms"][p]
                    line += f"| P{p} ${fm['money']:7.0f} q{len(fm['unlocked_quadrants'])} {mix(fm['tiles'])} "
                print(line)


if __name__ == "__main__":
    main()
