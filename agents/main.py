"""Kaggriculture agent: market-aware tile planner + greedy task scheduler.

Standard library only. Tunable knobs live in PARAMS so they can be optimized by self-play.
"""
import math

# ---------------------------------------------------------------- game constants
CROPS = {
    "WHEAT":      {"seed": 10, "first": 2, "mxd": 4, "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20, "first": 2, "mxd": 3, "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50, "first": 8, "mxd": 8, "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first": 10, "mxd": 10, "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80, "first": 10, "mxd": 12, "interval": 0, "max_yield": 6, "ongoing": False},
}
ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP", "first": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"cost": 400, "structure": "PASTURE", "first": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}
PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
MARKET_PARAMS = {
    "WHEAT":      (25, 10000, 400, "sqrt", 0.80, "log", 0.20),
    "CARROT":     (35, 10000, 450, "hinge", 1.00, "sqrt", 0.70),
    "TOMATO":     (60, 10000, 200, "hinge", 0.40, "sqrt", 0.60),
    "STRAWBERRY": (120, 10000, 100, "sqrt", 0.70, "linear", 1.60),
    "MELON":      (250, 10000, 300, "log", 0.20, "sq", 3.60),
    "EGG":        (50, 10000, 332, "hinge", 0.40, "log", 0.20),
    "MILK":       (160, 10000, 122, "sqrt", 0.60, "linear", 1.60),
    "WOOL":       (200, 10000, 105, "log", 0.20, "sq", 3.20),
    "FERTILIZER": (100, 10000, 200, "linear", 0.40, "linear", 0.40),
}
SHOPS = {
    "BAKERY": ["EGG", "WHEAT"],
    "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"],
    "YARN_STORE": ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
    "PET_CAFE": ["CARROT"],
    "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"],
    "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}
LAND_PRICES = [1000, 2000, 4000]
SHED_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]
TPD = 24
LAST_DAY = 29
LAST_STEP = 718  # last step whose actions are processed
SHED_CAP = 100
MOVES = {(0, -1): "NORTH", (0, 1): "SOUTH", (1, 0): "EAST", (-1, 0): "WEST"}

# ---------------------------------------------------------------- tunable params
PARAMS = {
    "hands_max": 12,
    "unit_turns": 20.0,        # useful actions per unit per day for hiring estimate
    "capital_rate": 0.02,      # per-day charge on upfront cost when ranking options
    "labor_cost": 4.0,         # $ per unit-action when ranking options
    "min_score": 5.0,          # minimum per-tile-day score to use a tile
    "land_buffer": 400,        # money kept after buying land
    "land_last_day": 20,
    "reserve_frac": {"WHEAT": 0.7, "CARROT": 0.6, "TOMATO": 0.6, "STRAWBERRY": 0.5, "MELON": 0.2,
                     "EGG": 0.7, "MILK": 0.5, "WOOL": 0.5, "FERTILIZER": 0.4},
    "demand_growth": 0.5,      # weight on expected future shop unlocks
    "animal_labor": 5.0,
    "crop_labor": 2.0,
    "drop_carry": 12,          # carried items that trigger a DROP trip
}

G = {}


def _reset():
    G.clear()
    G["plan"] = {}
    G["last_step"] = -1


# ---------------------------------------------------------------- market model
def _shape(func, x, T):
    x = max(0.0, x)
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return math.sqrt(x)
    if func == "log":
        return math.log(1.0 + x)
    if func == "hinge":
        u = x / T
        return u + 8.0 * max(0.0, u - 1.0) ** 2
    return x


def price_at(item, inv):
    base, I0, T, bf, bt, af, at = MARKET_PARAMS[item]
    if inv < I0:
        p = base + bt * base / _shape(bf, T, T) * _shape(bf, I0 - inv, T)
    else:
        p = base - at * base / _shape(af, T, T) * _shape(af, inv - I0, T)
    return max(1, int(round(p)))


def demand_per_day(item, shops, days_ahead=0.0):
    d = 0.0 if item == "FERTILIZER" else 1.0
    for s in shops:
        prods = SHOPS.get(s, [])
        if item in prods:
            d += 6.0 * (2 if len(prods) == 1 else 1)
    if len(shops) < 8 and days_ahead > 0:
        per_unlock = sum(6.0 * (2 if len(p) == 1 else 1) for p in SHOPS.values() if item in p) / len(SHOPS)
        extra = min(8 - len(shops), days_ahead / 3.0) * per_unlock * 0.5
        d += PARAMS["demand_growth"] * extra
    return d


# ---------------------------------------------------------------- helpers
def dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def nearest_shed(pos):
    return min(SHED_TILES, key=lambda s: (dist(pos, s), s))


def step_toward(pos, tgt):
    dx, dy = tgt[0] - pos[0], tgt[1] - pos[1]
    if dx:
        return MOVES[(1 if dx > 0 else -1, 0)]
    if dy:
        return MOVES[(0, 1 if dy > 0 else -1)]
    return "PASS"


def crop_remaining(t, day):
    cd = CROPS[t["crop"]]
    age = day - t["planted_day"]
    if not cd["ongoing"]:
        ws = (cd["mxd"] + 1) // 2
        start = max(age, ws) + (1 if t.get("watered_today") and age >= ws else 0)
        extra = max(0, cd["mxd"] - start + 1)
        return min(cd["max_yield"], t.get("yield_units", 0) + extra)
    produced = 0
    if age >= cd["first"]:
        produced = min(4, (age - cd["first"]) // cd["interval"] + 1)
    return (4 - produced) + t.get("yield_units", 0)


def animal_rate(a):
    ad = ANIMALS[a]
    return (1.0 + ad["interval"]) / ad["interval"]


# ---------------------------------------------------------------- option valuation
def crop_option(c, day, ctx):
    cd = CROPS[c]
    if cd["ongoing"]:
        ks = [cd["first"] + j * cd["interval"] for j in range(4)]
        ks = [k for k in ks if day + k <= LAST_DAY]
        if not ks:
            return None
        units = len(ks)
        occ = min(ks[-1] + 1, LAST_DAY + 1 - day)
        t_h = (ks[0] + ks[-1]) / 2.0
    else:
        a = min(cd["mxd"], LAST_DAY - day)
        if a < cd["first"]:
            return None
        ws = (cd["mxd"] + 1) // 2
        units = min(cd["max_yield"], 1 + max(0, a - ws + 1))
        occ = max(a, 1)
        t_h = a
    p = ctx["exp_price"](c, units / 2.0, t_h)
    profit = units * p - cd["seed"]
    labor = PARAMS["crop_labor"]
    score = profit / occ - PARAMS["capital_rate"] * cd["seed"] - PARAMS["labor_cost"] * labor
    return {"kind": "CROP", "name": c, "score": score, "cost": cd["seed"], "units": units,
            "product": c, "labor": labor}


def animal_option(a, day, ctx):
    ad = ANIMALS[a]
    d0 = day + 1  # realistic placement day
    first_ev = d0 + ad["first"] - 1
    if first_ev > LAST_DAY - 1:
        return None
    events = len(range(first_ev, LAST_DAY, ad["interval"]))
    units = min(ad["max_held"], ad["first"]) + (events - 1) * (1 + ad["interval"])
    live = LAST_DAY - d0
    if live <= 0:
        return None
    H = live
    p_prod = ctx["exp_price"](ad["product"], units / 2.0, H / 2.0)
    p_fert = ctx["exp_price"]("FERTILIZER", live / 2.0, H / 2.0)
    p_wheat = ctx["wheat_cost"]
    value = units * p_prod + live * p_fert - live * p_wheat - ad["cost"]
    labor = PARAMS["animal_labor"]
    score = value / live - PARAMS["capital_rate"] * ad["cost"] - PARAMS["labor_cost"] * labor
    return {"kind": "ANIMAL", "name": a, "score": score, "cost": ad["cost"], "units": units,
            "product": ad["product"], "fert": live, "labor": labor}


def free_tiles_remaining(tiles, plan):
    """True if the current land still has unused, unplanned empty tiles."""
    cnt = 0
    for y, row in enumerate(tiles):
        for x, t in enumerate(row):
            if t is None and (x, y) not in plan:
                cnt += 1
    return cnt > 3


# ---------------------------------------------------------------- main agent
def _act(obs, step):
    P = PARAMS
    me_id = obs["player"]
    farms = obs["farms"]
    me, opp = farms[me_id], farms[1 - me_id]
    priv = obs["private"]
    shed = dict(priv.get("shed", {}) or {})
    seeds = dict(priv.get("seeds", {}) or {})
    invs = [dict(i or {}) for i in (priv.get("inventories") or [{}])]
    day = step // TPD
    hour = step % TPD
    tiles = me["tiles"]
    n = len(tiles)
    money = float(me["money"])
    mkt_inv = obs["market"]["inventory"]
    prices = obs["market"]["prices"]
    shops = list((obs.get("town") or {}).get("unlocked_shops", []) or [])
    plan = G["plan"]
    last_day = day >= LAST_DAY

    units_pos = [tuple(me["farmer"])] + [tuple(h) for h in me.get("hands", [])]
    while len(invs) < len(units_pos):
        invs.append({})

    # ---------------- committed supply (mine + opponent visible) per product
    committed = {p: 0.0 for p in PRODUCTS}
    n_animals = {a: 0 for a in ANIMALS}
    my_animals = 0
    for fi, farm in enumerate(farms):
        for row in farm["tiles"]:
            for t in row:
                if not isinstance(t, dict):
                    continue
                k = t.get("kind")
                if k == "PLANT":
                    committed[t["crop"]] += crop_remaining(t, day)
                elif t.get("animal"):
                    a = t["animal"]
                    days_left = max(0, LAST_DAY - day)
                    committed[ANIMALS[a]["product"]] += t.get("yield_units", 0) + animal_rate(a) * days_left
                    committed["FERTILIZER"] += days_left
                    if fi == me_id:
                        n_animals[a] += 1
                        my_animals += 1
    for p in PRODUCTS:
        committed[p] += shed.get(p, 0) + sum(i.get(p, 0) for i in invs)

    feed_need_h = my_animals * max(0, LAST_DAY - day)

    def exp_price(item, extra, days_ahead):
        inv = mkt_inv[item] + committed[item] + extra - demand_per_day(item, shops, days_ahead) * days_ahead
        return price_at(item, inv)

    wheat_cost = price_at("WHEAT", mkt_inv["WHEAT"] - feed_need_h / 2.0
                          - demand_per_day("WHEAT", shops, 5) * 5)
    ctx = {"exp_price": exp_price, "wheat_cost": wheat_cost}

    # ---------------- plan empty tiles
    for key in list(plan.keys()):
        x, y = key
        t = tiles[y][x]
        pk = plan[key]
        if pk["kind"] == "CROP" and isinstance(t, dict) and t.get("kind") == "PLANT":
            del plan[key]
        elif pk["kind"] == "ANIMAL" and isinstance(t, dict) and t.get("animal"):
            del plan[key]
        elif pk["kind"] == "CROP" and pk["day"] != day and t is None:
            del plan[key]  # stale crop plan -> re-plan today

    spend = money - 50 - wheat_cost * my_animals * 1.5
    for pk in plan.values():
        if pk["kind"] == "CROP" and seeds.get(pk["name"], 0) <= 0:
            spend -= pk["cost"]
        elif pk["kind"] == "ANIMAL":
            spend -= pk["cost"]

    free = []
    for y in range(n):
        for x in range(n):
            t = tiles[y][x]
            if (x, y) in plan:
                continue
            if t is None or (isinstance(t, dict) and t.get("kind") == "WEED"):
                free.append((x, y))
            elif isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE") and not t.get("animal"):
                free.append((x, y))
    free.sort(key=lambda p: (dist(p, nearest_shed(p)), p))

    if free and hour <= 20 and not last_day:
        for pos in free:
            t = tiles[pos[1]][pos[0]]
            opts = []
            if isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE"):
                for a, ad in ANIMALS.items():
                    if ad["structure"] == t["kind"]:
                        o = animal_option(a, day, ctx)
                        if o:
                            opts.append(o)
            else:
                for c in CROPS:
                    o = crop_option(c, day, ctx)
                    if o:
                        opts.append(o)
                for a in ANIMALS:
                    o = animal_option(a, day, ctx)
                    if o:
                        opts.append(o)
            opts = [o for o in opts if o["score"] >= P["min_score"] and o["cost"] <= spend]
            if not opts:
                continue
            best = max(opts, key=lambda o: o["score"])
            plan[pos] = {"kind": best["kind"], "name": best["name"], "cost": best["cost"], "day": day}
            spend -= best["cost"]
            committed[best["product"]] += best["units"]
            if best["kind"] == "ANIMAL":
                committed["FERTILIZER"] += best["fert"]
                my_animals += 1

    # ---------------- task generation
    tasks = []
    seeds_left = dict(seeds)
    endgame = last_day

    def add(pos, op, prio, need=None, args=()):
        tasks.append({"pos": pos, "op": op, "prio": prio, "need": need, "args": list(args)})

    unfed = 0
    animals_needed_in_shed = {a: 0 for a in ANIMALS}
    for y in range(n):
        for x in range(n):
            t = tiles[y][x]
            pos = (x, y)
            if t == "LOCKED":
                continue
            pk = plan.get(pos)
            if t is None:
                if pk and not endgame:
                    if pk["kind"] == "CROP" and hour <= 21:
                        c = pk["name"]
                        if seeds_left.get(c, 0) > 0:
                            seeds_left[c] -= 1
                            add(pos, "PLANT", 50, args=[c])
                    elif pk["kind"] == "ANIMAL":
                        add(pos, "BUILD_" + ANIMALS[pk["name"]]["structure"], 45)
                continue
            k = t.get("kind")
            if k == "WEED":
                if pk or not endgame:
                    add(pos, "DIG", 30 if pk else 12)
                continue
            if k == "PLANT":
                cd = CROPS[t["crop"]]
                age = day - t["planted_day"]
                cu = t.get("consecutive_unwatered", 0)
                yu = t.get("yield_units", 0)
                if not cd["ongoing"]:
                    ws = (cd["mxd"] + 1) // 2
                    ready = age >= cd["first"] and yu > 0 and (
                        age > cd["mxd"] or (age == cd["mxd"] and t["watered_today"]) or endgame)
                    if not t["watered_today"] and not ready:
                        if cu >= 1:
                            add(pos, "WATER", 90)
                        elif ws <= age <= cd["mxd"]:
                            add(pos, "WATER", 60)
                    if ready:
                        add(pos, "HARVEST", 70 if t["crop"] == "MELON" else 55)
                else:
                    if not t["watered_today"] and cu >= 1 and not endgame:
                        add(pos, "WATER", 90)
                    if yu > 0 and (yu >= 2 or t.get("max_lifespan_step", -1) >= 0 or day >= LAST_DAY - 1):
                        add(pos, "HARVEST", 50)
                continue
            if k in ("COOP", "PASTURE"):
                a = t.get("animal")
                if not a:
                    want = pk["name"] if pk and pk["kind"] == "ANIMAL" else None
                    if want and not endgame:
                        animals_needed_in_shed[want] += 1
                        add(pos, "PLACE", 65, need=want, args=[want])
                    continue
                ad = ANIMALS[a]
                yu = t.get("yield_units", 0)
                if not t["fed_today"] and not endgame:
                    unfed += 1
                    add(pos, "FEED", 95 if t.get("consecutive_unfed", 0) >= 1 else 70, need="WHEAT")
                if not t["cared_today"] and not endgame:
                    add(pos, "CARE", 40)
                if t.get("fertilizer_available"):
                    add(pos, "COLLECT_FERTILIZER", 38)
                if yu > 0 and (yu * 2 >= ad["max_held"] or day >= LAST_DAY - 1):
                    add(pos, "HARVEST", 45)

    # pickups at the shed for inventory-requiring tasks
    carried_wheat = sum(i.get("WHEAT", 0) for i in invs)
    shed_wheat = shed.get("WHEAT", 0)
    if unfed > carried_wheat and shed_wheat > 0:
        need = unfed - carried_wheat
        per = max(4, min(15, need))
        k = 0
        while need > 0 and k < 6 and shed_wheat > 0:
            q = min(per, shed_wheat, need + 2)
            add("SHED", "PICKUP", 75, args=["WHEAT", q])
            shed_wheat -= q
            need -= q
            k += 1
    for a in ANIMALS:
        carried = sum(i.get(a, 0) for i in invs)
        avail = shed.get(a, 0)
        todo = animals_needed_in_shed[a] - carried
        for _ in range(max(0, min(todo, avail))):
            add("SHED", "PICKUP", 66, args=[a, 1])

    # DROP trips: heavy inventories, shed-capacity pressure, and final liquidation
    shed_total = sum(shed.values())
    carried_total = 0
    for ui, inv in enumerate(invs[:len(units_pos)]):
        c = sum(v for kk, v in inv.items() if kk not in ANIMALS)
        carried_total += c
    for ui, inv in enumerate(invs[:len(units_pos)]):
        c = sum(v for kk, v in inv.items() if kk not in ANIMALS and kk != "WHEAT")
        if c <= 0:
            continue
        d = dist(units_pos[ui], nearest_shed(units_pos[ui]))
        if endgame and step >= LAST_STEP - d - 3:
            add("SHED", "DROP", 200, args=[ui])
        elif c >= P["drop_carry"] or (hour >= 18 and shed_total + carried_total > SHED_CAP - 5) or endgame:
            add("SHED", "DROP", 58 if not endgame else 80, args=[ui])

    # ---------------- assignment (global greedy on priority - distance)
    unit_inv = [dict(i) for i in invs[:len(units_pos)]]
    pairs = []
    for ti, tk in enumerate(tasks):
        for ui, up in enumerate(units_pos):
            if tk["op"] == "DROP" and tk["args"][0] != ui:
                continue
            if tk["need"] and unit_inv[ui].get(tk["need"], 0) <= 0:
                continue
            tgt = nearest_shed(up) if tk["pos"] == "SHED" else tk["pos"]
            d = dist(up, tgt)
            if tk["pos"] != "SHED" and step + d > LAST_STEP:
                continue
            pairs.append((tk["prio"] - 2.0 * d, ti, ui, tgt))
    pairs.sort(key=lambda z: (-z[0], z[2], z[1]))
    used_t, used_u = set(), set()
    need_used = {}
    actions = [["PASS"] for _ in units_pos]
    for score, ti, ui, tgt in pairs:
        if ti in used_t or ui in used_u:
            continue
        tk = tasks[ti]
        if tk["need"]:
            key = (ui, tk["need"])
            if need_used.get(key, 0) >= unit_inv[ui].get(tk["need"], 0):
                continue
            need_used[key] = need_used.get(key, 0) + 1
        used_t.add(ti)
        used_u.add(ui)
        pos = units_pos[ui]
        if pos == tgt:
            if tk["op"] == "DROP":
                actions[ui] = ["DROP"]
            elif tk["op"] == "PICKUP":
                actions[ui] = ["PICKUP", tk["args"][0], tk["args"][1]]
            else:
                actions[ui] = [tk["op"]] + tk["args"]
        else:
            actions[ui] = [step_toward(pos, tgt)]

    # idle units drift toward the shed so they are central next turn
    for ui, pos in enumerate(units_pos):
        if ui not in used_u:
            s = nearest_shed(pos)
            if dist(pos, s) > 2:
                actions[ui] = [step_toward(pos, s)]

    # dropping this turn? account for items entering the shed before market orders
    dropping = {}
    for ui, a in enumerate(actions):
        if a[0] == "DROP" and units_pos[ui] in SHED_TILES:
            for kk, v in unit_inv[ui].items():
                dropping[kk] = dropping.get(kk, 0) + v

    # ---------------- market orders
    orders = []
    cash = money
    stock = dict(shed)
    for kk, v in dropping.items():
        stock[kk] = stock.get(kk, 0) + v
    wheat_keep = 0 if endgame else my_animals * 2
    pressure = sum(stock.values()) + (carried_total if hour >= 20 else 0) > SHED_CAP - 10
    sell_list = []
    for item in PRODUCTS:
        q = stock.get(item, 0)
        if item == "WHEAT":
            q -= wheat_keep
        if q <= 0:
            continue
        inv = mkt_inv[item]
        base = MARKET_PARAMS[item][0]
        floor_p = 1 if (endgame or day >= LAST_DAY - 1) else base * P["reserve_frac"].get(item, 0.5)
        k = 0
        while k < q and price_at(item, inv + k) >= floor_p:
            k += 1
        if pressure and k < q:
            k = q if item != "WHEAT" else k
        if k > 0:
            sell_list.append((item, k))
            cash += sum(price_at(item, inv + j) for j in range(k))
    for item, k in sell_list:
        orders.append(["SELL", item, k])

    # hires
    if hour <= 2 and not (endgame and hour > 0):
        work = len([t for t in tasks if t["pos"] != "SHED"]) * 1.6 + my_animals * 4 + len(plan) * 2
        need_units = int(math.ceil(work / P["unit_turns"]))
        target = max(0, min(P["hands_max"], need_units - 1))
        have = len(units_pos) - 1
        a, b = 1, 1
        for _ in range(me.get("hires_today", 0)):
            a, b = b, a + b
        while have < target and len(orders) < 8:
            if cash < a + 20:
                break
            orders.append(["HIRE"])
            cash -= a
            a, b = b, a + b
            have += 1

    # land
    nq = len(me.get("unlocked_quadrants", ["NW"]))
    if nq < 4 and day <= P["land_last_day"] and len(orders) < 10:
        lp = LAND_PRICES[nq - 1]
        if cash >= lp + P["land_buffer"] and not free_tiles_remaining(tiles, plan):
            orders.append(["BUY_LAND"])
            cash -= lp

    # animals for empty structures
    space = SHED_CAP - sum(stock.values())
    for a in ANIMALS:
        carried = sum(i.get(a, 0) for i in invs)
        want = animals_needed_in_shed[a] - carried - shed.get(a, 0)
        # also pre-buy for planned animal tiles being built this turn
        want += sum(1 for pos, pk in plan.items() if pk["kind"] == "ANIMAL" and pk["name"] == a
                    and isinstance(tiles[pos[1]][pos[0]], dict) is False and tiles[pos[1]][pos[0]] is None
                    and any(ac[0].startswith("BUILD") and units_pos[ui] == pos for ui, ac in enumerate(actions)))
        want = min(want, space)
        if want > 0 and len(orders) < 10 and not endgame:
            cnt = min(want, int(cash // ANIMALS[a]["cost"]))
            if cnt > 0:
                orders.append(["BUY_ANIMAL", a, cnt])
                cash -= cnt * ANIMALS[a]["cost"]
                space -= cnt

    # seeds for planned crop tiles
    need_seeds = {}
    for pos, pk in plan.items():
        if pk["kind"] == "CROP":
            need_seeds[pk["name"]] = need_seeds.get(pk["name"], 0) + 1
    for c, cnt in need_seeds.items():
        buy = cnt - seeds.get(c, 0)
        if buy > 0 and len(orders) < 10 and hour <= 21 and not endgame:
            buy = min(buy, int(cash // CROPS[c]["seed"]))
            if buy > 0:
                orders.append(["BUY_SEED", c, buy])
                cash -= buy * CROPS[c]["seed"]

    # wheat for feeding
    if my_animals > 0 and not endgame and len(orders) < 10:
        have_w = shed.get("WHEAT", 0) + carried_wheat
        target_w = my_animals * 2 if hour < 12 else my_animals * 3
        short = target_w - have_w
        if short > 0 and space > 0:
            q = min(short, space, int(cash // max(1, prices.get("WHEAT", 25) + 5)))
            if q > 0:
                orders.append(["BUY_PRODUCT", "WHEAT", q])

    return {"farmer": actions[0], "hands": actions[1:], "market": orders[:10]}


# kaggle-environments uses the LAST function defined in the file as the agent,
# so `agent` must stay at the bottom.
def agent(obs, config=None):
    step = obs.get("step", 0) if hasattr(obs, "get") else obs["step"]
    if step == 0 or step < G.get("last_step", -1) or "plan" not in G:
        _reset()
    G["last_step"] = step
    try:
        return _act(obs, step)
    except Exception:  # never crash: a crashed agent loses the episode
        return {"farmer": ["PASS"], "hands": [], "market": []}
