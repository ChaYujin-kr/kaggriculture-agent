"""Census of the opponents our submission actually meets: lineage tag (from their opening spend),
result, and margin.

usage: python scripts/opponent_census.py --submission 56481388 [--count 12]
"""
import argparse
import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KAGGLE = os.path.join(ROOT, ".venv", "Scripts", "kaggle.exe")
DEST = os.path.join(ROOT, "replays")

TAGS = [(2000, "all-in open (other family)"),      # spends nearly the whole $3000 on turn 0
        (450, "cow_open (top-2 branch)"),           # BUY_ANIMAL COW + small wheat buy ~ $540
        (60, "wheat_open (2945/hybrid forks)"),     # wheat round trip, $60-450
        (-1e9, "quiet_open (aurax7 branch)")]       # ~$0 net


def env():
    e = dict(os.environ)
    for ln in open(os.path.join(ROOT, ".env"), encoding="utf-8-sig"):
        m = re.match(r"^(KAGGLE_\w+)=(.+)$", ln.strip())
        if m and m.group(2).strip():
            e[m.group(1)] = m.group(2).strip()
    return e


def run(args):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env())


def tag_for(spend):
    for threshold, name in TAGS:
        if spend >= threshold:
            return name
    return "?"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--submission", required=True)
    ap.add_argument("--count", type=int, default=12)
    ap.add_argument("--me", default="Yujin Cha")
    a = ap.parse_args()
    out = run([KAGGLE, "competitions", "episodes", a.submission, "-v"]).stdout
    eps = [ln.split(",")[0] for ln in out.splitlines() if re.match(r"^\d+,", ln)][: a.count]
    print(f"{len(eps)} episodes for submission {a.submission}")
    rows = []
    for e in eps:
        path = os.path.join(DEST, f"episode-{e}-replay.json")
        if not os.path.exists(path):
            run([KAGGLE, "competitions", "replay", e, "-p", DEST])
        if not os.path.exists(path):
            continue
        rep = json.load(open(path, encoding="utf-8"))
        teams = rep["info"]["TeamNames"]
        steps = rep["steps"]
        me = 0 if teams[0] == a.me else 1
        final = [steps[-1][p].get("reward") or 0 for p in (0, 1)]
        spend = 3000.0 - steps[1][0]["observation"]["farms"][1 - me]["money"]
        rows.append((teams[1 - me], spend, final[me], final[1 - me]))
    print(f"\n{'opponent':<26} {'spend':>6} {'lineage':<28} {'us':>8} {'them':>8}  result")
    wins = 0
    mix = {}
    for opp, spend, mine, theirs in rows:
        t = tag_for(spend)
        mix[t] = mix.get(t, 0) + 1
        wins += mine > theirs
        print(f"{opp[:26]:<26} {spend:6.0f} {t:<28} {mine:8.0f} {theirs:8.0f}  "
              f"{'WIN ' if mine > theirs else 'loss'} ({mine - theirs:+.0f})")
    print(f"\nrecord {wins}/{len(rows)}   lineage mix: {mix}")


if __name__ == "__main__":
    main()
