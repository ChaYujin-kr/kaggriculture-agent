"""Curriculum (c): place local sparring agents on the ladder by lineage.

Each local agent plays the first 136 turns (vs itself, 2 seeds, both seats) on the official interpreter; its action
stream is hashed exactly like the dataset's stream_hashes.csv (canonical JSON per action, NUL between turns, steps[0]
skipped, first 16 hex).  A hash that matches ladder seats in the recent window tells us which ladder line the agent
runs and at what rating that line's seats sit.  Output: figs/sparring_map.csv
"""
import os, sys, glob, json, hashlib, time
import pandas as pd, numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts")); sys.path.insert(0, ROOT)
os.chdir(ROOT)
import fastsim as F
D = os.path.dirname(os.path.abspath(__file__))
CUTS = (24, 48, 100, 136)

def run_prefix(path, seed, T=136):
    a0 = F.load_agent(path, f"a{seed}0"); a1 = F.load_agent(path, f"a{seed}1")
    cfg = F.O(F.DEFAULT_CFG); cfg["seed"] = seed
    env = F.O(configuration=cfg, info={}, done=False)
    state = [F.O(observation=F.O(step=0), action=None, reward=0, status="ACTIVE") for _ in range(2)]
    F.K.interpreter(state, env)
    agents = [a0, a1]; hs = [hashlib.sha256(), hashlib.sha256()]; out = [{}, {}]
    for step in range(T):
        for s in state: s.observation["step"] = step
        for i, s in enumerate(state):
            o = s.observation; obs0 = state[0].observation
            view = F.O(player=i, step=step, day=obs0.day, hour=obs0.hour, farms=obs0.farms, market=obs0.market,
                       town=obs0.town, private=o.private)
            try:
                s.action = agents[i](view)
            except Exception:
                s.action = {"farmer": ["PASS"], "hands": [], "market": []}
        for i, s in enumerate(state):
            hs[i].update(json.dumps(json.loads(json.dumps(s.action or {})), sort_keys=True, separators=(",", ":")).encode())
            hs[i].update(b"\0")
            if step + 1 in CUTS: out[i][f"h{step + 1}"] = hs[i].hexdigest()[:16]
        F.K.interpreter(state, env)
    return out

AGENTS = (sorted(glob.glob("research/pool/*.py")) + sorted(glob.glob("research/refagents/*.py")) +
          ["research/refagents/top_meta/main.py", "agents/archive/v1.py", "agents/archive/v2.py", "agents/main.py"] +
          sorted(glob.glob("submissions/*.py")))
W = pd.read_parquet(os.path.join(D, "window_replay_seats.parquet"))
H = pd.read_csv(os.path.join(D, "raw", "stream_hashes.csv"), usecols=["episode_id", "seat", "stream_h24", "stream_h48", "stream_h100", "stream_h136"])
W = W.merge(H[["episode_id", "seat", "stream_h24", "stream_h100"]], on=["episode_id", "seat"], how="left")
rows = []
for p in AGENTS:
    t0 = time.time()
    try:
        res = run_prefix(p, 1001) + run_prefix(p, 2002)
    except Exception as ex:
        rows.append(dict(agent=p, error=repr(ex)[:200])); continue
    r = dict(agent=p, secs=round(time.time() - t0, 1))
    for c in CUTS:
        vals = sorted({x.get(f"h{c}") for x in res})
        r[f"distinct_h{c}_over_4_seats"] = len(vals)
        col = f"stream_h{c}"
        m = W[W[col].isin(vals)]
        r[f"ladder_seats_h{c}"] = len(m)
        if len(m):
            r[f"ladder_subs_h{c}"] = m["sub"].nunique()
            r[f"median_sub_rating_h{c}"] = float(m.drop_duplicates("sub").r_last.median())
            r[f"tier_mix_h{c}"] = json.dumps(m.drop_duplicates("sub").tier.value_counts().to_dict())
            r[f"win_rate_h{c}"] = float(m.win.mean())
    r["h48"] = "|".join(sorted({x.get("h48") for x in res})); r["h136"] = "|".join(sorted({x.get("h136") for x in res}))
    rows.append(r); print(p, r.get("ladder_seats_h48"), r.get("ladder_seats_h136"), r.get("median_sub_rating_h136"), flush=True)
pd.DataFrame(rows).to_csv(os.path.join(D, "figs", "sparring_map.csv"), index=False)
