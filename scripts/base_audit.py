"""Audit how an agent uses hires, fertilizer and ongoing crops (to find gaps an extra-hands layer could fill).

usage: python scripts/base_audit.py <agent.py> [opponent] [seed]
"""
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fastsim  # noqa: E402

CROPS = {"TOMATO": (8, 1), "STRAWBERRY": (10, 2)}

a_path = sys.argv[1]
b_path = sys.argv[2] if len(sys.argv) > 2 else a_path
seed = int(sys.argv[3]) if len(sys.argv) > 3 else 701
inner = fastsim.load_agent(a_path, "audit")

hire_hours = Counter()
ops = Counter()
fert_sold = 0
events = Counter()          # production events on ongoing crops: fertilized&watered vs not
idle_hands = Counter()
hands_per_day = defaultdict(int)
last_day_seen = [-1]


def wrapped(obs):
    act = inner(obs)
    try:
        _audit(obs, act)
    except Exception as e:  # auditing must never change the game
        errors[type(e).__name__ + ": " + str(e)[:80]] += 1
    return act


errors = Counter()


def _audit(obs, act):
    global fert_sold
    me = obs["farms"][obs["player"]]
    day, hour = obs["day"], obs["hour"]
    for o in act.get("market", []):
        if o[0] == "HIRE":
            hire_hours[hour] += 1
        if o[0] == "SELL" and o[1] == "FERTILIZER":
            fert_sold += min(int(o[2]), obs["private"]["shed"].get("FERTILIZER", 0))
    units = [act.get("farmer", ["PASS"])] + list(act.get("hands", []))
    for i, a in enumerate(units):
        ops[a[0] if a else "NONE"] += 1
        if i > 0 and (not a or a[0] == "PASS"):
            idle_hands[hour] += 1
    hands_per_day[day] = max(hands_per_day[day], len(me["hands"]))
    if hour == 23:  # inspect end-of-day production events for ongoing crops
        for row in me["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "PLANT" and t["crop"] in CROPS:
                    first, iv = CROPS[t["crop"]]
                    k = day - t["planted_day"] - (first - 1)
                    if k >= 0 and k % iv == 0 and k // iv < 4:
                        fert = t.get("fertilized_until_day", -1) >= day
                        # watering can still happen this last turn; count current state
                        key = ("fert" if fert else "nofert") + ("+water" if t["watered_today"] else "-dry")
                        events[(t["crop"], key)] += 1


res = fastsim.play(wrapped, fastsim.load_agent(b_path, "opp"), seed)
print("result", res)
print("hire orders by hour:", dict(sorted(hire_hours.items())))
print("hands per day:", [hands_per_day[d] for d in range(30)])
print("idle hand-turns by hour:", dict(sorted(idle_hands.items())), "total", sum(idle_hands.values()))
print("ops:", dict(ops.most_common()))
print("fertilizer sold:", fert_sold)
print("ongoing-crop production events (at hour 23):", dict(sorted(events.items())))
print("audit errors:", dict(errors))
