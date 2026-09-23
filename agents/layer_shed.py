"""Shed-overflow guard (original work, Yujin Cha).

At the end of each day every unit's inventory is dropped into the shed, and anything past the
100-item cap is destroyed. Late in the season the base agent walks into that cap: measured runs lose
up to ~15 milk, 10 wool and 6 strawberry in a single game (~$7k) on the day-28 drop.

This layer only appends SELL orders, and only when the projected end-of-day drop would overflow: it
sells the cheapest goods first so the expensive harvest still fits, never touches unit actions, and
leaves the wheat the animals still need.
"""

SHED = {
    "on": True,
    "cap": 100,
    "margin": 4,          # keep this much headroom
    "from_day": 20,       # only bother once production is heavy
    "from_hour": 18,      # late enough that the day's harvest is mostly in
    "feed_reserve": 1.0,  # wheat per animal to keep for tomorrow's feeding
    "min_price": 2,       # never dump at the floor
    "max_new_orders": 3,
}

_ORDER = ["WHEAT", "FERTILIZER", "EGG", "CARROT", "TOMATO", "WOOL", "MELON", "MILK", "STRAWBERRY"]


def layer(obs, base):
    P = SHED
    if not P["on"]:
        return base
    day, hour = obs["day"], obs["hour"]
    if day < P["from_day"] or hour < P["from_hour"]:
        return base
    priv = obs["private"]
    shed = dict(priv.get("shed") or {})
    carried = {}
    for inv in priv.get("inventories") or []:
        for k, v in (inv or {}).items():
            carried[k] = carried.get(k, 0) + v
    projected = sum(shed.values()) + sum(carried.values())
    room = P["cap"] - P["margin"] - projected
    if room >= 0:
        return base

    market = list(base.get("market") or [])
    planned = {}
    for o in market:
        if o and o[0] == "SELL" and len(o) >= 3:
            planned[o[1]] = planned.get(o[1], 0) + max(0, int(o[2]))
    me = obs["player"]
    animals = sum(1 for row in obs["farms"][me]["tiles"] for t in row
                  if isinstance(t, dict) and t.get("animal"))
    prices = obs["market"]["prices"]
    need = -room
    added = 0
    for item in _ORDER:
        if need <= 0 or added >= P["max_new_orders"] or len(market) >= 10:
            break
        have = shed.get(item, 0) - planned.get(item, 0)
        if item == "WHEAT" and day < 29:
            have -= int(animals * P["feed_reserve"])
        if have <= 0 or prices.get(item, 0) < P["min_price"]:
            continue
        qty = min(have, need)
        market.append(["SELL", item, qty])
        need -= qty
        added += 1
    out = dict(base)
    out["market"] = market[:10]
    return out
