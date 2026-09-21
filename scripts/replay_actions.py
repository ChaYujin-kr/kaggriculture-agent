"""Compare both players' behavior in a replay: unit-op mix, hands per day, sales by product.

usage: python scripts/replay_actions.py replays/episode-XXX-replay.json
"""
import json
import sys
from collections import Counter, defaultdict

r = json.load(open(sys.argv[1], encoding="utf-8"))
steps = r["steps"]
names = r.get("info", {}).get("TeamNames", ["P0", "P1"])
for p in range(2):
    ops = Counter()
    hands_by_day = defaultdict(int)
    sold = Counter()
    revenue = Counter()
    bought = Counter()
    for i in range(1, len(steps)):
        act = steps[i][p].get("action") or {}
        prev_obs = steps[i - 1][0]["observation"]
        day = (i - 1) // 24
        fa = act.get("farmer") or []
        if fa:
            ops[fa[0]] += 1
        for h in act.get("hands") or []:
            if h:
                ops[h[0]] += 1
        hands_by_day[day] = max(hands_by_day[day], len(act.get("hands") or []))
        for o in act.get("market") or []:
            if o and o[0] == "SELL":
                # executed quantity = drop in this player's shed item (approx; ignores same-turn drops)
                before = (steps[i - 1][p]["observation"].get("private") or {}).get("shed", {}).get(o[1], 0)
                q = min(int(o[2]), before) if before else int(o[2])
                sold[o[1]] += q
                revenue[o[1]] += q * prev_obs["market"]["prices"].get(o[1], 0)
            elif o and o[0] in ("BUY_SEED", "BUY_ANIMAL", "BUY_PRODUCT"):
                bought[f"{o[0][4:]}:{o[1]}"] += int(o[2])
            elif o and o[0] in ("HIRE", "BUY_LAND"):
                bought[o[0]] += 1
    total_ops = sum(ops.values())
    moves = sum(ops[m] for m in ("NORTH", "SOUTH", "EAST", "WEST"))
    print(f"=== {names[p]}  final ${steps[-1][p]['reward']}")
    print(f"  unit ops {total_ops}, moves {moves} ({moves / max(1, total_ops):.0%}), pass {ops['PASS']}")
    print("  ops:", dict(ops.most_common(14)))
    print("  hands/day:", [hands_by_day[d] for d in range(30)])
    print("  sold (approx units @ pre-turn price):",
          {k: (v, round(revenue[k] / max(1, v))) for k, v in sold.most_common()})
    print("  bought:", dict(bought.most_common()))
