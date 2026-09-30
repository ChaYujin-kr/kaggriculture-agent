"""Step 0: build the per-seat analysis table from the community dataset CSVs.

Output: seats.parquet (one row per PUBLIC episode-seat), with outcome, ratings,
features, lineage hashes, engine version and time.
"""
import pandas as pd, numpy as np, os
D = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(D, "raw")

e = pd.read_csv(os.path.join(R, "episodes.csv"))
e["t"] = pd.to_datetime(e.create_time, utc=True, format="ISO8601")
rows = []
for s in (0, 1):
    o = 1 - s
    x = pd.DataFrame({
        "episode_id": e.episode_id, "seat": s, "type": e["type"], "state": e.state, "t": e.t,
        "sub": e[f"sub_{s}"], "team": e[f"team_{s}"], "bank": e[f"bank_{s}"], "rating": e[f"rating_{s}"],
        "opp_sub": e[f"sub_{o}"], "opp_team": e[f"team_{o}"], "opp_bank": e[f"bank_{o}"], "opp_rating": e[f"rating_{o}"],
    })
    rows.append(x)
S = pd.concat(rows, ignore_index=True)
S["day"] = S.t.dt.strftime("%Y-%m-%d")
S["win"] = np.where(S.bank > S.opp_bank, 1.0, np.where(S.bank < S.opp_bank, 0.0, 0.5))
S["margin"] = S.bank - S.opp_bank

f = pd.read_csv(os.path.join(R, "episode_features.csv"))
f = f.drop(columns=["final_money", "elbow_day"])  # outcome-derived, keep out
h = pd.read_csv(os.path.join(R, "stream_hashes.csv"))
S = S.merge(f, on=["episode_id", "seat"], how="left").merge(h, on=["episode_id", "seat"], how="left")
S["has_replay"] = S.engine_version.notna()
# engine: from replay when present; otherwise infer from time (cutover 2026-08-15 01:41 UTC)
cut = pd.Timestamp("2026-08-15 01:41", tz="UTC")
S["engine_inferred"] = S.engine_version.fillna(pd.Series(np.where(S.t >= cut, "1.32.7*", "<1.32.7*"), index=S.index))
S.to_parquet(os.path.join(D, "seats.parquet"), index=False)
print(S.shape, S.has_replay.mean())
