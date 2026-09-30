"""Step 6a: stream replays out of one parquet shard and turn them into per-turn state/action rows.

Pairing: observation at steps[t] with the action recorded at steps[t+1] (steps[0].action is a dummy PASS; the opening
buys appear at steps[1]), t = 0..718.  One row group holds ~2 replays, so we read row group by row group and parse with
orjson in a small worker pool (RAM is 8 GB: 4 workers).  Output: turns/part_*.parquet.
"""
import os, sys, glob
import numpy as np, pandas as pd, pyarrow.parquet as pq, orjson
from multiprocessing import Pool

D = os.path.dirname(os.path.abspath(__file__))
SHARD = os.path.join(D, "raw", "replays_2026-09f.parquet")
OUTD = os.path.join(D, "turns"); os.makedirs(OUTD, exist_ok=True)
SEED = 20260923

CROPS = ["WHEAT", "CARROT", "TOMATO", "MELON", "STRAWBERRY"]
ANIMALS = ["COW", "SHEEP", "GOOSE", "CHICKEN"]
PRODUCTS = ["CARROT", "EGG", "FERTILIZER", "MELON", "MILK", "STRAWBERRY", "TOMATO", "WHEAT", "WOOL"]
SHED = ["CARROT", "COW", "EGG", "FERTILIZER", "GOOSE", "MELON", "MILK", "SHEEP", "STRAWBERRY", "TOMATO", "WHEAT", "WOOL"]
FARMER_CAT = {"NORTH": "MOVE", "SOUTH": "MOVE", "EAST": "MOVE", "WEST": "MOVE", "WATER": "WATER", "HARVEST": "HARVEST",
              "PLANT": "PLANT", "FEED": "ANIMAL", "CARE": "ANIMAL", "COLLECT_FERTILIZER": "COLLECT", "FERTILIZE": "FERTILIZE",
              "PICKUP": "CARRY", "DROP": "CARRY", "PLACE": "CARRY", "DIG": "BUILD", "PASS": "PASS"}
KIND_CODE = {"LOCKED": 0, None: 1, "PLANT": 2, "PASTURE": 3, "COOP": 4, "WEED": 5}
CROP_CODE = {c: i + 1 for i, c in enumerate(CROPS + ANIMALS)}


def fcat(a):
    if not a: return "PASS"
    v = a[0] if isinstance(a, list) else str(a)
    if v.startswith("BUILD"): return "BUILD"
    return FARMER_CAT.get(v, "OTHER")


def mlabel(market):
    if not market: return "NONE"
    f = set()
    for m in market:
        if not m: continue
        v = m[0]
        f.add("SELL" if v == "SELL" else "HIRE" if v == "HIRE" else "BUY")
    return "+".join(sorted(f)) if f else "NONE"


def farm_feats(farm, day, pre):
    d = {}
    tiles = farm["tiles"]
    cnt = dict.fromkeys(["locked", "empty", "weed", "plant", "pasture", "coop"], 0)
    pc = dict.fromkeys(CROPS, 0); ac = dict.fromkeys(ANIMALS, 0)
    watered = unw = fert = yld = age = 0; fed = cared = fav = ayld = 0
    for row in tiles:
        for c in row:
            if c == "LOCKED": cnt["locked"] += 1; continue
            if c is None: cnt["empty"] += 1; continue
            k = c.get("kind")
            if k == "PLANT":
                cnt["plant"] += 1; pc[c.get("crop")] = pc.get(c.get("crop"), 0) + 1
                watered += bool(c.get("watered_today")); unw += c.get("consecutive_unwatered", 0) > 0
                fert += c.get("fertilized_until_day", -1) >= day; yld += c.get("yield_units", 0)
                age += day - c.get("planted_day", day)
            elif k in ("PASTURE", "COOP"):
                cnt["pasture" if k == "PASTURE" else "coop"] += 1
                an = c.get("animal")
                if an: ac[an] = ac.get(an, 0) + 1
                fed += bool(c.get("fed_today")); cared += bool(c.get("cared_today")); fav += bool(c.get("fertilizer_available"))
                ayld += c.get("yield_units", 0)
            elif k == "WEED": cnt["weed"] += 1
    for k, v in cnt.items(): d[f"{pre}t_{k}"] = v
    for k in CROPS: d[f"{pre}p_{k}"] = pc.get(k, 0)
    for k in ANIMALS: d[f"{pre}a_{k}"] = ac.get(k, 0)
    np_ = max(cnt["plant"], 1)
    d.update({f"{pre}plant_watered_frac": watered / np_, f"{pre}plant_unwatered": unw, f"{pre}plant_fert": fert,
              f"{pre}plant_yield": yld, f"{pre}plant_age_mean": age / np_, f"{pre}anim_fed": fed, f"{pre}anim_cared": cared,
              f"{pre}anim_fert_avail": fav, f"{pre}anim_yield": ayld,
              f"{pre}money": farm.get("money", 0.0), f"{pre}hands": len(farm.get("hands") or []),
              f"{pre}hires_today": farm.get("hires_today", 0), f"{pre}quadrants": len(farm.get("unlocked_quadrants") or [])})
    return d


def parse_episode(rg):
    pf = pq.ParquetFile(SHARD)
    t = pf.read_row_group(rg)
    out = []
    for i in range(t.num_rows):
        eid = t.column("episode_id")[i].as_py()
        r = orjson.loads(t.column("replay_json")[i].as_py())
        steps = r["steps"]
        T = len(steps)
        for seat in (0, 1):
            rows = []
            for s in range(T - 1):
                ob = steps[s][seat]["observation"]
                act = steps[s + 1][seat].get("action") or {}
                day, hour = ob.get("day", 0), ob.get("hour", 0)
                farms = ob["farms"]
                me, op = farms[seat], farms[1 - seat]
                row = {"episode_id": eid, "seat": seat, "step": s, "day": day, "hour": hour}
                row.update(farm_feats(me, day, ""))
                row["opp_money"] = op.get("money", 0.0); row["opp_hands"] = len(op.get("hands") or [])
                row["opp_quadrants"] = len(op.get("unlocked_quadrants") or [])
                opp_plants = sum(1 for rr in op["tiles"] for c in rr if isinstance(c, dict) and c.get("kind") == "PLANT")
                row["opp_plants"] = opp_plants
                pv = ob.get("private") or {}
                for k in SHED: row[f"shed_{k}"] = (pv.get("shed") or {}).get(k, 0)
                for k in CROPS: row[f"seed_{k}"] = (pv.get("seeds") or {}).get(k, 0)
                carry = {}
                for inv in pv.get("inventories") or []:
                    for k, v in inv.items(): carry[k] = carry.get(k, 0) + v
                for k in PRODUCTS: row[f"carry_{k}"] = carry.get(k, 0)
                mk = (ob.get("market") or {}).get("prices") or {}
                for k in PRODUCTS: row[f"price_{k}"] = mk.get(k, 0)
                row["n_shops"] = len(((ob.get("town") or {}).get("unlocked_shops")) or [])
                fx, fy = (me.get("farmer") or [0, 0])[:2]
                try:
                    c = me["tiles"][fy][fx]
                except Exception:
                    c = "LOCKED"
                row["fpos_x"], row["fpos_y"] = fx, fy
                if isinstance(c, dict):
                    row["under_kind"] = KIND_CODE.get(c.get("kind"), 6); row["under_crop"] = CROP_CODE.get(c.get("crop") or c.get("animal"), 0)
                    row["under_watered"] = int(bool(c.get("watered_today"))); row["under_yield"] = c.get("yield_units", 0)
                    row["under_age"] = day - c.get("planted_day", c.get("placed_day", day))
                else:
                    row["under_kind"] = KIND_CODE.get(c, 6) if not isinstance(c, dict) else 6; row["under_crop"] = 0
                    row["under_watered"] = 0; row["under_yield"] = 0; row["under_age"] = 0
                # labels
                row["y_farmer"] = fcat(act.get("farmer"))
                hands = act.get("hands") or []
                hc = [fcat(h) for h in hands]
                row["y_hands_mode"] = max(set(hc), key=hc.count) if hc else "NONE"
                row["y_market"] = mlabel(act.get("market"))
                mk_list = act.get("market") or []
                row["n_sell"] = sum(1 for m in mk_list if m and m[0] == "SELL")
                row["n_buy_seed"] = sum(1 for m in mk_list if m and m[0] == "BUY_SEED")
                row["n_buy_animal"] = sum(1 for m in mk_list if m and m[0] == "BUY_ANIMAL")
                row["n_buy_land"] = sum(1 for m in mk_list if m and m[0] == "BUY_LAND")
                row["n_hire"] = sum(1 for m in mk_list if m and m[0] == "HIRE")
                rows.append(row)
            out.append(pd.DataFrame(rows))
        del r, steps
    return pd.concat(out, ignore_index=True) if out else None


def main():
    W = pd.read_parquet(os.path.join(D, "window_replay_seats.parquet"))
    ids = pq.read_table(SHARD, columns=["episode_id"]).column(0).to_pandas()
    pf = pq.ParquetFile(SHARD)
    rg_of = {}
    k = 0
    for g in range(pf.num_row_groups):
        n = pf.metadata.row_group(g).num_rows
        for j in range(n): rg_of[int(ids.iloc[k + j])] = g
        k += n
    x = W[W.episode_id.isin(ids)]
    comp = x.groupby("episode_id").tier.agg(lambda s: "".join(sorted(s)))
    rng = np.random.default_rng(SEED)
    want = set(comp[comp.str.contains("G1") | comp.str.contains("G2")].index)
    g3 = comp[comp.str.contains("G3") & ~comp.index.isin(want)].index.values
    want |= set(rng.choice(g3, size=min(600, len(g3)), replace=False))
    g4 = comp[(comp == "G4G4")].index.values
    want |= set(rng.choice(g4, size=min(150, len(g4)), replace=False))
    rgs = sorted({rg_of[e] for e in want})
    done = {int(os.path.basename(p)[5:-8]) for p in glob.glob(os.path.join(OUTD, "part_*.parquet"))}
    todo = [g for g in rgs if g not in done]
    print(f"episodes wanted {len(want)}, row groups {len(rgs)}, todo {len(todo)}", flush=True)
    pd.Series(sorted(want)).to_csv(os.path.join(D, "turns_selected_episodes.csv"), index=False)
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 4) as pool:
        for n, (g, df) in enumerate(zip(todo, pool.imap(parse_episode, todo, chunksize=2))):
            if df is not None:
                df.to_parquet(os.path.join(OUTD, f"part_{g:06d}.parquet"), index=False)
            if n % 100 == 0: print(n, flush=True)


if __name__ == "__main__":
    main()
