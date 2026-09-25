"""Replay our own ladder games locally, on the real seed and seats, and check the banks to the coin.

The local engine is deterministic for a fixed seed and agent pair, and it matches the ladder
(discussion 742856). So a game replays exactly once both agent files are the ones that played it.
That checks two things at once: that fastsim is faithful, and which local file the opponent really was.

Inputs: research/ladder/summaries.jsonl (ladder_harvest.py: seed, seats, both banks, opponent
opening md5) and research/ladder/fingerprints_raw.txt (ladder_fingerprint.py: md5 per local file).
  pass 1  for each opponent opening md5, take one game and try every local file with that opening
          until one reproduces both banks exactly
  pass 2  replay up to --per-group more games of that md5 with the file found
Writes research/ladder/replay_check.jsonl (one line per replayed game) and prints a summary.

usage: python scripts/ladder_replay.py [--per-group 15] [--workers 3]
"""
import argparse
import collections
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fastsim  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LADDER = os.path.join(ROOT, "research", "ladder")
OUT = os.path.join(LADDER, "replay_check.jsonl")
OURS = {"v7_endgame": "submissions/v7_endgame.py",
        "v7_base": "research/pool/aurax7_v7.py",
        "hybrid_tuned": "submissions/hybrid2965_tuned.py"}
POOLS = ("research/ladder_pool", "research/pool", "submissions")


def local_path(name):
    for d in POOLS:
        p = os.path.join(ROOT, d, name)
        if os.path.exists(p):
            return p
    return None


def replay(job):
    """job = (episode row, opponent file) -> (my bank, their bank, exact)"""
    ep, opp = job
    me = fastsim.load_agent(os.path.join(ROOT, OURS[ep["sub"]]), "me")
    op = fastsim.load_agent(opp, "opp")
    seed = int(ep["seed"])
    r = fastsim.play(me, op, seed) if ep["me_seat"] == 0 else fastsim.play(op, me, seed)[::-1]
    return r[0], r[1], r[0] == ep["rew_me"] and r[1] == ep["rew_op"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-group", type=int, default=15)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

    rows = [json.loads(l) for l in open(os.path.join(LADDER, "summaries.jsonl"), encoding="utf-8")]
    eps = [r for r in rows if "error" not in r and r.get("seed") is not None and r["sub"] in OURS]
    cands = collections.defaultdict(set)
    for ln in open(os.path.join(LADDER, "fingerprints_raw.txt"), encoding="utf-8"):
        f, _, md5, _, _ = ln.split()
        p = local_path(f)
        if p:
            cands[md5].add(p)
    groups = collections.defaultdict(list)
    for e in eps:
        if e["openhash_op"] in cands:
            groups[e["openhash_op"]].append(e)
    print(f"{len(eps)} ladder games, {sum(map(len, groups.values()))} with a local candidate, {len(groups)} opening groups")

    log = open(OUT, "w", encoding="utf-8")
    found = {}
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        # pass 1: identify the exact opponent file per opening group
        probes = [(md5, g[0], sorted(cands[md5])) for md5, g in groups.items()]
        jobs = [(ep, f) for _, ep, files in probes for f in files]
        print(f"pass 1: {len(jobs)} probe games")
        results = dict(zip([(ep["ep"], f) for ep, f in jobs], ex.map(replay, jobs, chunksize=1)))
        for md5, ep, files in probes:
            hits = [f for f in files if results[(ep["ep"], f)][2]]
            found[md5] = hits[0] if hits else None
            for f in files:
                my, their, exact = results[(ep["ep"], f)]
                log.write(json.dumps({"pass": 1, "ep": ep["ep"], "sub": ep["sub"], "md5": md5, "opp_file": os.path.basename(f),
                                      "ladder": [ep["rew_me"], ep["rew_op"]], "local": [my, their], "exact": exact}) + "\n")
            print(f"  {md5} ({len(groups[md5])} games): "
                  + (f"exact = {os.path.basename(found[md5])}" if found[md5] else f"no exact match among {len(files)} files"))

        # pass 2: replay more games of each identified group
        jobs = [(ep, found[md5]) for md5, g in groups.items() if found[md5] for ep in g[1:1 + a.per_group]]
        print(f"pass 2: {len(jobs)} games")
        stats = collections.Counter()
        for (ep, f), (my, their, exact) in zip(jobs, ex.map(replay, jobs, chunksize=1)):
            same_outcome = (my > their) == (ep["rew_me"] > ep["rew_op"])
            stats["games"] += 1
            stats["exact"] += exact
            stats["outcome"] += same_outcome
            log.write(json.dumps({"pass": 2, "ep": ep["ep"], "sub": ep["sub"], "md5": ep["openhash_op"], "opp_file": os.path.basename(f),
                                  "ladder": [ep["rew_me"], ep["rew_op"]], "local": [my, their], "exact": exact,
                                  "same_outcome": same_outcome}) + "\n")
    log.close()
    n = max(stats["games"], 1)
    print(f"pass 2: {stats['exact']}/{stats['games']} exact to the coin ({stats['exact'] / n:.0%}), "
          f"{stats['outcome']}/{stats['games']} same winner ({stats['outcome'] / n:.0%})")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
