"""Adversarial market layer for a tape-driven base agent (original work, Yujin Cha).

Two independent mechanisms, both off by default:

* feed denial ("wheat squeeze") — buy wheat early to raise the shared wheat price, which every
  animal-keeping opponent must pay for feed, then sell the hoard back once the price has moved;
* opponent lineage tagging — the opponent's actions are hidden but their bank is public, so their
  opening spend identifies which family they belong to (the top ladder branch opens by buying a cow).

The layer only ever appends or reorders market orders; unit actions are passed through untouched, and
any exception returns the base action unchanged.
"""

ADV = {
    "squeeze_on": False,
    "squeeze_from": 0,          # first step to buy on
    "squeeze_to": 48,           # last step to buy on
    "squeeze_qty": 6,           # wheat bought per turn
    "squeeze_cash_floor": 900,  # never spend below this
    "squeeze_max_total": 60,    # total extra wheat to accumulate
    "squeeze_price_cap": 45,    # stop buying above this price
    "unload_from": 240,         # start selling the hoard back
    "unload_qty": 8,
    "tag_only": True,           # record the opponent tag without acting on it
    # --- inference poisoning -------------------------------------------------------------------
    # Rival agents recover our sales from `sold = -(inventory delta) - town draw - their own sales`.
    # A 1-unit buy costs ~nothing (buy is quoted at post-buy inventory, sell at pre-sell, so a round
    # trip nets zero against an unchanged market) but shifts the inventory they are differencing.
    "noise_on": False,
    "noise_from": 120,
    "noise_to": 690,
    "noise_every": 7,           # turns between injections
    "noise_qty": 1,
    "noise_items": ("WHEAT", "FERTILIZER"),  # only these two can be bought back
    "noise_cash_floor": 1500,
}

_S = {"step": -1, "bought": 0, "sold": 0, "tag": None, "opp_open_spend": None}


def opponent_tag(obs, step):
    """Identify the opponent's family from their opening spend (bank is public, actions are not)."""
    if step != 1 or _S["tag"] is not None:
        return _S["tag"]
    me = obs["player"]
    opp_money = float(obs["farms"][1 - me]["money"])
    spend = 3000.0 - opp_money
    _S["opp_open_spend"] = spend
    # top ladder branch opens BUY_ANIMAL COW (400) + a small wheat buy; our lineage round-trips wheat
    _S["tag"] = "cow_open" if spend >= 300 else ("wheat_open" if spend >= 60 else "quiet_open")
    return _S["tag"]


def layer(obs, base):
    P = ADV
    step = obs.get("step", 0) if hasattr(obs, "get") else obs["step"]
    if step <= _S["step"]:  # new episode in the same process
        _S.update(step=-1, bought=0, sold=0, tag=None, opp_open_spend=None)
    _S["step"] = step
    opponent_tag(obs, step)

    if P["noise_on"] and P["noise_from"] <= step <= P["noise_to"] and step % P["noise_every"] == 0:
        market = list(base.get("market") or [])
        me = obs["player"]
        cash = float(obs["farms"][me]["money"])
        shed_total = sum((obs["private"].get("shed") or {}).values())
        item = P["noise_items"][(step // P["noise_every"]) % len(P["noise_items"])]
        price = float(obs["market"]["prices"].get(item, 25))
        if len(market) < 10 and cash - price * P["noise_qty"] > P["noise_cash_floor"] and shed_total < 95:
            market.insert(0, ["BUY_PRODUCT", item, P["noise_qty"]])
            out = dict(base)
            out["market"] = market[:10]
            base = out

    if not P["squeeze_on"] or P["tag_only"]:
        return base

    me = obs["player"]
    farm = obs["farms"][me]
    market = list(base.get("market") or [])
    price = float(obs["market"]["prices"].get("WHEAT", 25))
    shed = (obs["private"].get("shed") or {})
    cash = float(farm["money"])

    if (P["squeeze_from"] <= step <= P["squeeze_to"] and _S["bought"] < P["squeeze_max_total"]
            and price <= P["squeeze_price_cap"] and len(market) < 10):
        qty = min(P["squeeze_qty"], P["squeeze_max_total"] - _S["bought"],
                  int(max(0.0, cash - P["squeeze_cash_floor"]) // max(1.0, price)))
        room = 100 - sum(shed.values())
        qty = min(qty, max(0, room - 5))
        if qty > 0:
            market.insert(0, ["BUY_PRODUCT", "WHEAT", qty])  # slot 0: win the per-unit race
            _S["bought"] += qty
    elif step >= P["unload_from"] and _S["sold"] < _S["bought"] and len(market) < 10:
        # the hoard is fungible with feed wheat; only release what the base is not already selling
        planned = sum(int(o[2]) for o in market if len(o) >= 3 and o[0] == "SELL" and o[1] == "WHEAT")
        qty = min(P["unload_qty"], _S["bought"] - _S["sold"], max(0, shed.get("WHEAT", 0) - planned - 10))
        if qty > 0:
            market.append(["SELL", "WHEAT", qty])
            _S["sold"] += qty

    out = dict(base)
    out["market"] = market[:10]
    return out
