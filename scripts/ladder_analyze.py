"""Win rate of our submissions by opponent rating band, time window and opening type (research/ladder/)."""
import json, glob, os, sys
import pandas as pd, numpy as np
from collections import Counter

S = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "ladder")
rows = [json.loads(l) for l in open(os.path.join(S, "summaries.jsonl"), encoding="utf-8")]
rows = {r["ep"]: r for r in rows if "error" not in r}
d = pd.DataFrame(rows.values())
lb = pd.read_csv(sorted(glob.glob(os.path.join(S, "*publicleaderboard*.csv")))[-1])
score = dict(zip(lb.TeamName, lb.Score))
d["opp_lb"] = d.opp.map(score)
d["win"] = d.rew_me > d.rew_op
d["margin"] = d.rew_me - d.rew_op
d["hour"] = pd.to_datetime(d.ctime).dt.floor("3h")


def tag(sp):
    return "allin" if sp >= 2000 else "cow" if sp >= 450 else "wheat" if sp >= 60 else "quiet"


d["optag"] = d.spend0_op.map(tag)
d["band"] = pd.cut(d.opp_lb, [0, 1500, 2000, 2300, 2500, 2700, 4000])
pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 30)
print(d.groupby("sub").agg(n=("win", "size"), win=("win", "mean"), me=("rew_me", "median"),
                           op=("rew_op", "median"), opp_lb=("opp_lb", "median"), missing_lb=("opp_lb", lambda x: x.isna().sum())))
print("\n== win rate by opponent current-LB band")
print(d.pivot_table(index="band", columns="sub", values="win", aggfunc=["mean", "size"], observed=False).round(2))
print("\n== by time window")
print(d.pivot_table(index="hour", columns="sub", values="win", aggfunc=["mean", "size"]).round(2))
print("\n== opening tag of opponents")
print(d.pivot_table(index="optag", columns="sub", values="win", aggfunc=["mean", "size"]).round(2))
print("\n== our own score level (money) by opponent band")
print(d.pivot_table(index="band", columns="sub", values=["rew_me", "rew_op"], aggfunc="median", observed=False).round(0))
d.to_pickle(os.path.join(S, "d.pkl"))
