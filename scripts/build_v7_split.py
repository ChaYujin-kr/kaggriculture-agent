"""Build v7 variants whose endgame bulk sales are split across the remaining turns.

From day 27 (step 648) v7's route 2 tape issues SELL 1000 orders, which dump the whole shed stock of a
product in one turn. V53 sells tens of units per turn instead. On 2026-09-25 a v7_endgame vs V53 game
(seed 23000) showed v7 dumping WHEAT/CARROT/MILK/FERTILIZER by the thousand from step 671 on.

The wrapper appended here leaves the rest of the agent untouched. Once a product gets its first bulk
SELL (qty >= BULK) inside [FROM, LAST), it is sold at ceil(stock * PACE / turns_left) per turn on every
later turn until LAST, where the existing terminal liquidation sells what is left. PACE 1 spreads the
stock evenly; PACE 2 front-loads it into the first half of the remaining turns.

Result (2026-09-25, seeds 23000-23005, 12 games per pairing): splitting made v7 worse.
Own score fell by about 1000 against both V53 and hybrid; v7 still lost 0/12 to V53, and the
margin went from -4939 to -6194 (pace 1) or -6063 (pace 2). v7's gap to V53 is not in endgame
selling. Kept as a record of the negative result.

usage: python scripts/build_v7_split.py [--pace 1 2] [--src submissions/v7_endgame.py]
Writes submissions/v7_split_p<pace>.py.
"""
import argparse
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WRAPPER = '''

# --------------------------------------------------------------------------------------------
# MODIFIED by Yujin Cha (2026-09): endgame sale splitting (scripts/build_v7_split.py).
# From step _SPLIT_FROM, a product whose tape issues a bulk SELL (>= _SPLIT_BULK) is sold in
# slices of ceil(stock * _SPLIT_PACE / turns_left) per turn instead of all at once.
# --------------------------------------------------------------------------------------------
_SPLIT_FROM = 648
_SPLIT_LAST = 718
_SPLIT_BULK = 500
_SPLIT_PACE = {pace}
_SPLIT_PARENT = agent
_SPLIT_STATE = {{}}
del agent


def agent(observation, configuration=None):
    action = _SPLIT_PARENT(observation, configuration)
    try:
        step = _step_of(observation)
        if not (_SPLIT_FROM <= step < _SPLIT_LAST) or not isinstance(action, dict):
            return action
        player = _int(_get(observation, "player", 0))
        selling = _SPLIT_STATE.setdefault(player, set())
        if step == _SPLIT_FROM:
            selling.clear()
        view = _View(observation, player, _IMPL.chassis.cfg)
        projected = _IMPL.chassis._projected_shed(action, view)
        left = _SPLIT_LAST - step + 1
        market = []
        for o in action.get("market") or []:
            if o and o[0] == "SELL" and len(o) >= 3 and o[1] in PRODUCTS:
                if _int(o[2]) >= _SPLIT_BULK:
                    selling.add(o[1])
                if o[1] in selling:
                    continue
            market.append(o)
        for item in PRODUCTS:
            have = int(projected.get(item, 0))
            if item in selling and have > 0 and len(market) < _IMPL.chassis.cfg["max_orders"]:
                market.append(["SELL", item, min(have, -(-have * _SPLIT_PACE // left))])
        return dict(action, market=market)
    except Exception:
        return action
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pace", type=int, nargs="+", default=[1, 2])
    ap.add_argument("--src", default=os.path.join(ROOT, "submissions", "v7_endgame.py"))
    a = ap.parse_args()
    src = open(a.src, encoding="utf-8").read()
    for pace in a.pace:
        out = os.path.join(ROOT, "submissions", f"v7_split_p{pace}.py")
        open(out, "w", encoding="utf-8").write(src + WRAPPER.format(pace=pace))
        print("wrote", out)


if __name__ == "__main__":
    main()
