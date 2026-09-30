"""Step 6a': fine-grained labels for the same turns as extract.py: the farmer's exact verb (+ crop/animal argument,
e.g. NORTH, PLANT:WHEAT, BUILD_PASTURE) and the first hired hand's exact verb.  Output: turns_fine/part_*.parquet
with (episode_id, seat, step, y_farmer_fine, y_hand0_fine).
"""
import os, sys, glob
import pandas as pd, pyarrow.parquet as pq, orjson
from multiprocessing import Pool
D = os.path.dirname(os.path.abspath(__file__))
SHARD = os.path.join(D, "raw", "replays_2026-09f.parquet")
OUTD = os.path.join(D, "turns_fine"); os.makedirs(OUTD, exist_ok=True)

def fine(a):
    if not a: return "PASS"
    if not isinstance(a, list): return str(a)[:20]
    v = str(a[0])
    if v in ("PLANT", "PLACE", "BUILD_PASTURE", "BUILD_COOP") and len(a) > 1 and isinstance(a[1], str):
        return f"{v}:{a[1]}"
    return v

def parse(rg):
    t = pq.ParquetFile(SHARD).read_row_group(rg)
    out = []
    for i in range(t.num_rows):
        eid = t.column("episode_id")[i].as_py()
        steps = orjson.loads(t.column("replay_json")[i].as_py())["steps"]
        for seat in (0, 1):
            for s in range(len(steps) - 1):
                act = steps[s + 1][seat].get("action") or {}
                hands = act.get("hands") or []
                out.append((eid, seat, s, fine(act.get("farmer")), fine(hands[0]) if hands else "NONE"))
    return pd.DataFrame(out, columns=["episode_id", "seat", "step", "y_farmer_fine", "y_hand0_fine"])

if __name__ == "__main__":
    done = {os.path.basename(p) for p in glob.glob(os.path.join(OUTD, "*.parquet"))}
    todo = [int(os.path.basename(p)[5:-8]) for p in sorted(glob.glob(os.path.join(D, "turns", "part_*.parquet")))
            if os.path.basename(p) not in done]
    print(len(todo), flush=True)
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 2) as pool:
        for n, (g, df) in enumerate(zip(todo, pool.imap(parse, todo, chunksize=4))):
            df.to_parquet(os.path.join(OUTD, f"part_{g:06d}.parquet"), index=False)
            if n % 200 == 0: print(n, flush=True)
