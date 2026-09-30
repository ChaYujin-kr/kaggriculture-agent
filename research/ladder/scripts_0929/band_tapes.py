"""Build tapes of 2300-2399 teams' recent ladder games from the community parquet. Writes tapes + index.jsonl."""
import base64, glob, json, os, sys, zlib, hashlib
import pandas as pd, pyarrow.dataset as ds
ROOT = r"C:\Users\chauj\Desktop\kagriculture"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from make_tape_agent import TEMPLATE
RAW = os.path.join(ROOT, "zero2one/data_audit/raw/fresh0929")
OUT = os.path.join(ROOT, "research/ladder/band_tapes")
LO, HI, PER, SINCE = float(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
os.makedirs(OUT, exist_ok=True)
lb = pd.read_csv(sorted(glob.glob(os.path.join(ROOT, "research/ladder/*publicleaderboard-2026-09-29*.csv")))[-1])
band = lb[(lb.Score >= LO) & (lb.Score < HI)]
score = dict(zip(band.TeamId, band.Score)); tname = dict(zip(band.TeamId, band.TeamName))
e = pd.read_csv(os.path.join(RAW, "episodes.csv"))
e = e[e.type.str.contains("PUBLIC") & (e.create_time >= SINCE)]
seats = pd.concat([e.assign(seat=s, sub=e[f"sub_{s}"], team=e[f"team_{s}"], rating=e[f"rating_{s}"]) for s in (0, 1)])
seats = seats[seats.team.isin(score)]
best = seats.groupby(["team", "sub"]).rating.max().reset_index().sort_values("rating").drop_duplicates("team", keep="last")
seats = seats.merge(best[["team", "sub"]], on=["team", "sub"])
pick = seats.sort_values("create_time").groupby("team").tail(PER)
print(len(band), "band teams;", seats.team.nunique(), "with games;", len(pick), "boards", flush=True)
want = dict(zip(pick.episode_id, zip(pick.seat, pick.team)))
import pyarrow.parquet as pq
idx = open(os.path.join(OUT, "index.jsonl"), "a")
n = 0
def rows():
    for f in sorted(glob.glob(os.path.join(RAW, "replays_*.parquet"))):
        pf = pq.ParquetFile(f)
        ids = pf.read(columns=["episode_id"]).column(0).to_pylist()
        rg, k = [], 0
        for i in range(pf.metadata.num_row_groups):
            m = pf.metadata.row_group(i).num_rows
            if any(x in want for x in ids[k:k + m]): rg.append(i)
            k += m
        for i in rg:
            t = pf.read_row_group(i, columns=["episode_id", "replay_json"])
            for ep, rj in zip(t.column(0).to_pylist(), t.column(1).to_pylist()):
                if ep in want: yield ep, rj
done = set()
for ep, rj in rows():
        if ep in done: continue
        done.add(ep)
        r = json.loads(rj); steps = r["steps"]; seat, team = want[ep]
        if len(steps) < 700: continue
        tape = [steps[i][seat].get("action") for i in range(1, len(steps))]
        rew = [steps[-1][p].get("reward") or 0 for p in (0, 1)]
        blob = base64.b64encode(zlib.compress(json.dumps(tape).encode(), 9)).decode()
        open(os.path.join(OUT, f"tape_{ep}.py"), "w", encoding="utf-8").write(
            TEMPLATE.format(team=tname[team], seat=seat, episode=ep, bank=rew[seat], blob=blob))
        oh = hashlib.md5("|".join(json.dumps(steps[t][seat].get("action") or {}, sort_keys=True) for t in range(1, 49)).encode()).hexdigest()[:10]
        idx.write(json.dumps(dict(ep=str(ep), team=tname[team], lb=score[team], seat=seat, seed=r["info"].get("seed"),
                                  bank=rew[seat], bank_other=rew[1 - seat], h=oh)) + chr(10)); idx.flush(); n += 1
print("wrote", n)
