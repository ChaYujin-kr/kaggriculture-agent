"""Opponent lineage mix at a target rating band, from the public episode dataset.

Replays (and so stream hashes) exist for only part of the ladder, and the stored share falls to
~0 for the newest day. So each submission is labelled with the most common stream_h48 over
whatever replays of it are stored, and the mix is then counted over the full episode index
(episodes.csv), which lists every ladder game whether or not its replay was kept.

usage: python scripts/ladder_mix.py [--band 2450 2850] [--since 2026-09-19] [--data data/kaggriculture-episodes]
Writes research/ladder/mix_<band>_<since>.tsv (h48, lineage name if known, share of opponent seats).
Lineage names come from research/ladder/fingerprints_raw.txt (scripts/ladder_fingerprint.py output)
and research/ladder/lineages.tsv.
"""
import argparse
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LADDER = os.path.join(ROOT, "research", "ladder")


def local_names():
    """h48 -> 'lineage (agent file)' from the local fingerprints, via the md5 lineage table."""
    lin = pd.read_csv(os.path.join(LADDER, "lineages.tsv"), sep="\t", comment="#")
    md5_name = {h: n for h, n in zip(lin.hash, lin.lineage) if n != "?"}
    names = {}
    path = os.path.join(LADDER, "fingerprints_raw.txt")
    if not os.path.exists(path):
        return names
    for ln in open(path, encoding="utf-8"):
        f, opp, md5, spend, h48 = ln.split()
        names.setdefault(h48, set()).add(md5_name.get(md5, f[:-3]))
    return {h: " / ".join(sorted(v)) for h, v in names.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--band", type=float, nargs=2, default=(2450, 2850))
    ap.add_argument("--since", default="2026-09-19")
    ap.add_argument("--data", default=os.path.join(ROOT, "data", "kaggriculture-episodes"))
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # team names include CJK; the console default is cp949

    ep =pd.read_csv(os.path.join(a.data, "episodes.csv"))
    ep = ep[(ep.type == "EPISODE_TYPE_PUBLIC") & (ep.state == "COMPLETED") & (ep.create_time >= a.since)]
    sh = pd.read_csv(os.path.join(a.data, "stream_hashes.csv"), usecols=["episode_id", "seat", "stream_h48"])
    teams = pd.read_csv(os.path.join(a.data, "teams.csv"))
    team_name = dict(zip(teams.team_id, teams.team_name))

    # one row per seat: who played, their rating after the game, and who they faced
    seats = []
    for s in (0, 1):
        o = 1 - s
        seats.append(pd.DataFrame({"episode_id": ep.episode_id, "seat": s, "sub": ep[f"sub_{s}"],
                                   "rating": ep[f"rating_{s}"], "opp_sub": ep[f"sub_{o}"],
                                   "opp_team": ep[f"team_{o}"]}))
    seats = pd.concat(seats, ignore_index=True)

    labelled = seats.merge(sh, on=["episode_id", "seat"])
    label = labelled.groupby("sub").stream_h48.agg(lambda x: x.value_counts().index[0])
    label_n = labelled.groupby("sub").size()

    lo, hi = a.band
    band = seats[(seats.rating >= lo) & (seats.rating <= hi)].copy()
    band["opp_h48"] = band.opp_sub.map(label)
    n_all = len(band)
    known = band.dropna(subset=["opp_h48"])
    names = local_names()

    mix = (known.groupby("opp_h48")
           .agg(seats=("episode_id", "size"), subs=("opp_sub", "nunique"),
                teams=("opp_team", lambda x: ", ".join(team_name.get(t, str(t)) for t in x.value_counts().index[:3])))
           .sort_values("seats", ascending=False))
    mix["share"] = mix.seats / len(known)
    mix["lineage"] = [names.get(h, "?") for h in mix.index]
    out = os.path.join(LADDER, f"mix_{int(lo)}-{int(hi)}_{a.since}.tsv")
    mix.reset_index().rename(columns={"opp_h48": "h48"})[["h48", "lineage", "share", "seats", "subs", "teams"]] \
        .to_csv(out, sep="\t", index=False, float_format="%.4f")

    print(f"band {lo:.0f}-{hi:.0f} since {a.since}: {n_all} seats, opponent labelled for {len(known)} "
          f"({len(known) / max(n_all, 1):.0%}); {label_n.size} submissions labelled")
    pd.set_option("display.width", 200)
    print(mix.head(20)[["lineage", "share", "seats", "subs", "teams"]].to_string(float_format=lambda v: f"{v:.3f}"))
    print("wrote", out)


if __name__ == "__main__":
    main()
