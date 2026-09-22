"""Diff near-clone ladder games: where do the two players' actions first diverge, and which market
orders differ afterwards? Also estimates per-product sale revenue for both sides.

usage: python scripts/clone_diff.py --me "Yujin Cha" replays/episode-*.json [--show 12]
"""
import argparse
import glob
import json
from collections import Counter


def norm(act):
    act = act or {}
    return (json.dumps(act.get("farmer")), json.dumps(act.get("hands")), json.dumps(act.get("market")))


def revenue(steps, p):
    rev = Counter()
    for i in range(1, len(steps)):
        prev = steps[i - 1]
        act = steps[i][p].get("action") or {}
        prices = prev[0]["observation"]["market"]["prices"]
        shed = (prev[p]["observation"].get("private") or {}).get("shed", {})
        for o in act.get("market") or []:
            if o and o[0] == "SELL":
                q = min(int(o[2]), shed.get(o[1], 0))
                rev[o[1]] += q * prices.get(o[1], 0)
    return rev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--me", default="Yujin Cha")
    ap.add_argument("--show", type=int, default=10)
    a = ap.parse_args()
    files = [f for p in a.files for f in glob.glob(p)]
    for f in sorted(files):
        r = json.load(open(f, encoding="utf-8"))
        names = r["info"]["TeamNames"]
        me = names.index(a.me)
        op = 1 - me
        steps = r["steps"]
        fin = [steps[-1][0]["reward"], steps[-1][1]["reward"]]
        first = None
        diffs = []
        for i in range(1, len(steps)):
            am, ao = steps[i][me].get("action"), steps[i][op].get("action")
            if norm(am) != norm(ao):
                if first is None:
                    first = i - 1
                mm = (am or {}).get("market") or []
                mo = (ao or {}).get("market") or []
                if mm != mo and len(diffs) < a.show:
                    diffs.append(f"    step {i - 1:3d} (d{(i - 1) // 24} h{(i - 1) % 24:2d}) me={mm}  opp={mo}")
        rm, ro = revenue(steps, me), revenue(steps, op)
        delta = {k: round(rm[k] - ro[k]) for k in set(rm) | set(ro) if abs(rm[k] - ro[k]) >= 1}
        print(f"== {f.split('episode-')[-1][:9]} vs {names[op]:<22} me {fin[me]:.0f} opp {fin[op]:.0f} "
              f"(diff {fin[me] - fin[op]:+.0f})  first divergence step {first}")
        print(f"    est. sale revenue delta (me-opp): {dict(sorted(delta.items(), key=lambda kv: kv[1]))}")
        for d in diffs:
            print(d)


if __name__ == "__main__":
    main()
