"""Fertilizer/water gap-filling layer on top of a tape-driven base agent (original work, Yujin Cha).

The base agent's actions are never altered except where it idles (PASS):
  * our own extra hands, hired after the base's hires each day, get full control;
  * base units that PASS may do a *stationary* useful action on their current tile (never move,
    so the base agent's recorded move sequences stay aligned).
Useful actions: fertilize strawberry/tomato production days the base left unfertilized, water
fertilized production days / plants about to weed, and spend surplus fertilizer on wheat in its
bonus window. Any exception returns the base action unchanged.
"""

LAYER = {
    "extra_hands": 1,        # our own hands per day
    "hire_hour": 5,          # hire after the base's own hires (it hires at hours 0-3)
    "first_day": 10,
    "last_day": 27,
    "fert_wheat": True,
    "wheat_min_price": 30,
    "fert_reserve": 4,       # fertilizer kept for ongoing crops before using it on wheat
    "stationary": True,
    "rescue_hour": 19,       # from this hour water any plant that would weed tonight
}

_ONGOING = {"TOMATO": (8, 1), "STRAWBERRY": (10, 2)}
_SHED = [(4, 4), (5, 4), (4, 5), (5, 5)]
_MOVES = {(0, -1): "NORTH", (0, 1): "SOUTH", (1, 0): "EAST", (-1, 0): "WEST"}
_L = {"day": -1, "ours": 0, "base_hands": 0}


def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _toward(p, t):
    dx, dy = t[0] - p[0], t[1] - p[1]
    if dx:
        return _MOVES[(1 if dx > 0 else -1, 0)]
    if dy:
        return _MOVES[(0, 1 if dy > 0 else -1)]
    return "PASS"


def _events(t):
    first, iv = _ONGOING[t["crop"]]
    return [t["planted_day"] + first - 1 + j * iv for j in range(4)]


def layer(obs, base):
    P = LAYER
    step = obs["step"] if "step" in obs else obs.get("step", 0)
    day, hour = step // 24, step % 24
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    tiles = me["tiles"]
    hands = [tuple(h) for h in me.get("hands", [])]
    invs = priv.get("inventories") or [{}]
    shed = priv.get("shed", {}) or {}

    if day != _L["day"]:
        _L.update(day=day, ours=0, base_hands=0)
    # our hands are the last `ours` entries; if the base hired after us, stop using them (safety)
    n_ours = _L["ours"] if len(hands) >= _L["base_hands"] + _L["ours"] else 0
    if n_ours and len(hands) != _L["base_hands"] + _L["ours"]:
        n_ours = 0
    base_hand_acts = list(base.get("hands") or [])
    n_base = len(hands) - n_ours

    # ---- tasks
    tasks = []
    fert_need = 0
    for y, row in enumerate(tiles):
        for x, t in enumerate(row):
            if not (isinstance(t, dict) and t.get("kind") == "PLANT"):
                continue
            fud = t.get("fertilized_until_day", -1)
            if t["crop"] in _ONGOING:
                evs = [e for e in _events(t) if day <= e <= 28]
                if any(e <= day + 2 and fud < e for e in evs):
                    fert_need += 1
                    tasks.append(((x, y), "FERTILIZE", 60))
                if not t["watered_today"] and fud >= day and day in evs and hour >= 10:
                    tasks.append(((x, y), "WATER", 70))
            elif (P["fert_wheat"] and t["crop"] == "WHEAT" and day - t["planted_day"] == 2 and fud < day
                  and obs["market"]["prices"].get("WHEAT", 25) >= P["wheat_min_price"]):
                tasks.append(((x, y), "FERT_WHEAT", 30))
            if not t["watered_today"] and t.get("consecutive_unwatered", 0) >= 1 and hour >= P["rescue_hour"]:
                tasks.append(((x, y), "WATER", 80))
    fert_avail = shed.get("FERTILIZER", 0) + sum(i.get("FERTILIZER", 0) for i in invs)
    wheat_ok = fert_avail > fert_need + P["fert_reserve"]

    out_hands = base_hand_acts[:n_base]
    while len(out_hands) < n_base:
        out_hands.append(["PASS"])
    farmer = base.get("farmer") or ["PASS"]
    claimed = set()

    def op_for(kind):
        return "FERTILIZE" if kind in ("FERTILIZE", "FERT_WHEAT") else kind

    def usable(kind, inv):
        if kind == "FERTILIZE":
            return inv.get("FERTILIZER", 0) > 0
        if kind == "FERT_WHEAT":
            return wheat_ok and inv.get("FERTILIZER", 0) > 0
        return True

    # ---- stationary help from idle base units (farmer idx 0, base hands 1..n_base)
    if P["stationary"]:
        units = [(0, tuple(me["farmer"]), farmer)] + [(i + 1, hands[i], out_hands[i]) for i in range(n_base)]
        for idx, pos, act in units:
            if act and act[0] != "PASS":
                continue
            inv = invs[idx] if idx < len(invs) else {}
            for tpos, kind, pr in sorted(tasks, key=lambda z: -z[2]):
                if tpos == pos and (tpos, kind) not in claimed and usable(kind, inv):
                    claimed.add((tpos, kind))
                    if idx == 0:
                        farmer = [op_for(kind)]
                    else:
                        out_hands[idx - 1] = [op_for(kind)]
                    break

    # ---- our own hands: full control
    ours = []
    for k in range(n_ours):
        hidx = n_base + k
        pos = hands[hidx]
        inv = invs[hidx + 1] if hidx + 1 < len(invs) else {}
        best, best_sc = None, None
        for tpos, kind, pr in tasks:
            if (tpos, kind) in claimed or not usable(kind, inv):
                continue
            sc = pr - 2 * _dist(pos, tpos)
            if best_sc is None or sc > best_sc:
                best, best_sc = (tpos, kind), sc
        if best is None and inv.get("FERTILIZER", 0) == 0 and fert_need > 0 and shed.get("FERTILIZER", 0) > 0:
            s = min(_SHED, key=lambda q: _dist(pos, q))
            ours.append(["PICKUP", "FERTILIZER", min(6, shed["FERTILIZER"])] if pos == s else [_toward(pos, s)])
            continue
        if best is None:
            ours.append(["PASS"])
            continue
        claimed.add(best)
        ours.append([op_for(best[1])] if pos == best[0] else [_toward(pos, best[0])])

    market = list(base.get("market") or [])
    if (hour == P["hire_hour"] and P["first_day"] <= day <= P["last_day"] and fert_need + len(tasks) > 0
            and _L["ours"] < P["extra_hands"] and len(market) < 10):
        _L["base_hands"] = len(hands)
        want = P["extra_hands"] - _L["ours"]
        for _ in range(min(want, 10 - len(market))):
            market.append(["HIRE"])
            _L["ours"] += 1

    return {"farmer": farmer, "hands": out_hands + ours, "market": market}
