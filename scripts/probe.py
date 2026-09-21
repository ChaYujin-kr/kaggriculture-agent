"""Play one fast game and report our agent's op mix, market orders and farm trajectory.

usage: python scripts/probe.py [agent] [opponent] [seed]
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fastsim  # noqa: E402

a_path = sys.argv[1] if len(sys.argv) > 1 else "agents/main.py"
b_path = sys.argv[2] if len(sys.argv) > 2 else "starter"
seed = int(sys.argv[3]) if len(sys.argv) > 3 else 101

inner = fastsim.load_agent(a_path, "probe")
ops, orders, traj = Counter(), Counter(), []


def wrapped(obs):
    act = inner(obs)
    for a in [act["farmer"]] + act["hands"]:
        ops[a[0]] += 1
    for o in act["market"]:
        orders[o[0] + (":" + o[1] if len(o) > 1 else "")] += (o[2] if len(o) > 2 else 1)
    if obs["hour"] == 12 and obs["day"] % 3 == 0:
        f = obs["farms"][obs["player"]]
        mix = Counter()
        for row in f["tiles"]:
            for t in row:
                if isinstance(t, dict):
                    mix[(t.get("crop") or t.get("animal") or t["kind"])[:4]] += 1
        traj.append(f"d{obs['day']:2d} ${f['money']:7.0f} q{len(f['unlocked_quadrants'])} hands={len(f['hands'])} "
                    f"shed={sum(obs['private']['shed'].values())} {dict(mix)}")
    return act


res = fastsim.play(wrapped, fastsim.load_agent(b_path, "opp"), seed)
print("result", res)
print("\n".join(traj))
tot = sum(ops.values())
mv = sum(ops[m] for m in ("NORTH", "SOUTH", "EAST", "WEST"))
print(f"ops {tot}, moves {mv / tot:.0%}:", dict(ops.most_common()))
print("orders:", dict(orders.most_common()))
