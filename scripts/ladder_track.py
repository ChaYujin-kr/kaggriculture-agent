"""Track our active submissions on the ladder: score snapshot, fresh replays, win rate by time and opponent lineage.

Appends each score to research/ladder/score_track.tsv, refreshes eps_<id>.csv, runs ladder_harvest.py for new games,
then prints a report per active submission.
usage: python scripts/ladder_track.py [--no-fetch]
"""
import csv, io, json, os, subprocess, sys
from datetime import datetime, timezone
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, "research", "ladder")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from ladder_harvest import KAGGLE, SUBS, env  # noqa: E402

ACTIVE = ["56633420", "56612456"]   # ttv1_flags (2026-09-28 07:30 UTC), shepherd_p6 (2026-09-27 15:17 UTC)


def kaggle(*args):
    return subprocess.run([KAGGLE, *args], capture_output=True, text=True, env=env(), timeout=600).stdout


def snapshot():
    out = kaggle("competitions", "submissions", "kaggriculture", "-v")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    path = os.path.join(S, "score_track.tsv")
    new = not os.path.exists(path)
    with open(path, "a", encoding="utf-8") as f:
        if new:
            f.write("utc\tsub\tname\tscore\n")
        for row in csv.DictReader(io.StringIO(out)):
            if row["ref"] in ACTIVE:
                f.write(f"{now}\t{row['ref']}\t{SUBS[row['ref']]}\t{row['publicScore']}\n")
    for sub in ACTIVE:
        with open(os.path.join(S, f"eps_{sub}.csv"), "w", encoding="utf-8") as f:
            f.write(kaggle("competitions", "episodes", sub, "-v"))
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "ladder_harvest.py"), "12"], env=env())


def lineage_map():
    lin = {}
    for ln in open(os.path.join(S, "lineages.tsv"), encoding="utf-8"):
        if not ln.startswith(("#", "hash")):
            h, name, *_ = ln.rstrip("\n").split("\t")
            lin[h] = name[:24]
    return lin


def report():
    rows = [json.loads(l) for l in open(os.path.join(S, "summaries.jsonl"), encoding="utf-8")]
    names = [SUBS[s] for s in ACTIVE]
    d = pd.DataFrame([r for r in rows if "error" not in r and r["sub"] in names]).drop_duplicates("ep")
    lb = sorted(f for f in os.listdir(S) if "publicleaderboard" in f)[-1]
    lb = pd.read_csv(os.path.join(S, lb), encoding="utf-8-sig")
    d["opp_lb"] = d.opp.map(dict(zip(lb.TeamName, lb.Score)))
    d["win"] = d.rew_me > d.rew_op
    d["margin"] = d.rew_me - d.rew_op
    d["t"] = pd.to_datetime(d.ctime)
    d["lin"] = d.openhash_op.map(lineage_map()).fillna("other")
    pd.set_option("display.width", 220)
    print(open(os.path.join(S, "score_track.tsv"), encoding="utf-8").read())
    for s, g in d.groupby("sub"):
        g = g.sort_values("t").copy()
        print(f"===== {s}: {len(g)} games, win {g.win.mean():.2f}, last game {g.t.max()}")
        g["blk"] = g.t.dt.floor("6h")
        print(g.groupby("blk").agg(n=("win", "size"), win=("win", "mean"), opp_lb=("opp_lb", "median")).round(2))
        g = g[g.opp_lb > 1900]
        print(g.groupby("lin").agg(n=("win", "size"), win=("win", "mean"), margin=("margin", "median"),
                                   opp_lb=("opp_lb", "median")).sort_values("n", ascending=False).round(2))


if __name__ == "__main__":
    if "--no-fetch" not in sys.argv:
        snapshot()
    report()
