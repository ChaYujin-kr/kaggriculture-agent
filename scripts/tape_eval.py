"""Score candidates on our real ladder boards against open-loop tapes of the opponents we met there.

Tapes are research/ladder_tapes/tape_<ep>.py (one opponent seat of one ladder game, built with
scripts/make_tape_agent.py). Each candidate plays the tape on that game's seed and seat.
- Check: the file that actually played must give back the ladder banks.
- A tape cannot react to us, so absolute wins are an upper bound; the comparison between candidates
  on the same tapes is what counts.

--build N first makes tapes for the N most recent boards (of the selected lineage) that have none,
downloading each replay and deleting it afterwards.

usage: python scripts/tape_eval.py [--md5 H | --not-md5 H] [--min-opp-lb 2300] [--subs a,b] [--build N] [--workers 1] CANDIDATE [CANDIDATE ...]
"""
import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import daily_refresh as dr  # noqa: E402
import fastsim  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAPES = os.path.join(ROOT, "research", "ladder_tapes")
PLAYED = {"shepherd_0925": "submissions/auto_0925_the-shepherds-ledger-herd-safe-sovereign.py",
          "hybrid_resub": "submissions/hybrid2965_tuned.py",
          "shepherd_p6": "submissions/shepherd_p6.py",
          "hybrid_cxd_p8": "submissions/hybrid_cxd_p8.py",
          "ttv1_flags": "submissions/auto_0928_kaggriculture-ttv1.py",
          "ttv1_look10": "submissions/ttv1_look10_rev7500.py",
          "hybrid_tuned": "submissions/hybrid2965_tuned.py",
          "v7_endgame": "submissions/v7_endgame.py"}


def build_tape(r):
    out = os.path.join(TAPES, f"tape_{r['ep']}.py")
    rp = os.path.join(ROOT, "replays", f"episode-{r['ep']}-replay.json")
    fetched = not os.path.exists(rp)
    if fetched:
        dr.run([dr.KAGGLE, "competitions", "replay", str(r["ep"]), "-p", os.path.join(ROOT, "replays")])
    if os.path.exists(rp):
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "make_tape_agent.py"), rp,
                        "--seat", str(1 - r["me_seat"]), "--out", out], capture_output=True)
        if fetched:
            os.remove(rp)
    return os.path.exists(out)


def opp_scores():
    """team name -> score from the newest public leaderboard snapshot in research/ladder/."""
    import csv
    import glob
    snaps = sorted(glob.glob(os.path.join(ROOT, "research", "ladder", "*publicleaderboard*.csv")))
    if not snaps:
        return {}
    return {r["TeamName"]: float(r["Score"]) for r in csv.DictReader(open(snaps[-1], encoding="utf-8"))}


def keep(r, a):
    return (r["sub"] in PLAYED and r.get("seed") and (a.md5 is None or r["openhash_op"] == a.md5)
            and (a.not_md5 is None or r["openhash_op"] != a.not_md5)
            and (a.min_opp_lb is None or a.lb.get(r["opp"], 0) >= a.min_opp_lb))


def play(job):
    cand, tape, seed, seat = job
    me = fastsim.load_agent(os.path.join(ROOT, cand), "me")
    op = fastsim.load_agent(tape, "op")
    return fastsim.play(me, op, seed) if seat == 0 else fastsim.play(op, me, seed)[::-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates", nargs="+")
    ap.add_argument("--md5", default=None, help="only boards whose opponent opening hash matches")
    ap.add_argument("--not-md5", default=None, help="only boards whose opponent opening hash differs")
    ap.add_argument("--subs", default="shepherd_0925,hybrid_resub", help="for --build: which submissions' games")
    ap.add_argument("--min-opp-lb", type=float, default=None,
                    help="only boards whose opponent team is rated at least this on the newest leaderboard snapshot")
    ap.add_argument("--build", type=int, default=0)
    ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args()
    a.lb = opp_scores() if a.min_opp_lb is not None else {}
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    os.makedirs(TAPES, exist_ok=True)

    summ = {}
    for ln in open(os.path.join(ROOT, "research", "ladder", "summaries.jsonl"), encoding="utf-8"):
        r = json.loads(ln)
        if "error" not in r:
            summ[str(r["ep"])] = r
    if a.build:
        have = set(os.listdir(TAPES))
        todo = sorted((r for r in summ.values() if keep(r, a) and r["sub"] in a.subs.split(",")
                       and f"tape_{r['ep']}.py" not in have), key=lambda r: r["ctime"])[-a.build:]
        built = sum(build_tape(r) for r in todo)
        print(f"built {built}/{len(todo)} tapes")
    boards = []
    for f in sorted(os.listdir(TAPES)):
        ep = f[len("tape_"):-3] if f.startswith("tape_") and f.endswith(".py") else None
        r = summ.get(ep)
        if r and keep(r, a):
            boards.append((r, os.path.join(TAPES, f)))
    n = len(boards)
    print(f"{n} boards; ladder record on them {sum(r['rew_me'] > r['rew_op'] for r, _ in boards)}/{n}")

    names = ["(as played)"] + a.candidates
    jobs = [(PLAYED[r["sub"]] if c == "(as played)" else c, t, int(r["seed"]), r["me_seat"])
            for c in names for r, t in boards]
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        res = list(ex.map(play, jobs, chunksize=1))
    for i, c in enumerate(names):
        rs = res[i * n:(i + 1) * n]
        wins = sum(x > y for x, y in rs)
        margin = sum(x - y for x, y in rs) / max(n, 1)
        extra = ""
        if c == "(as played)":
            extra = f"  exact vs ladder {sum(x == r['rew_me'] and y == r['rew_op'] for (x, y), (r, _) in zip(rs, boards))}/{n}"
        print(f"{os.path.basename(c):<48} wins {wins:3d}/{n}  mean margin {margin:+7.0f}{extra}")


if __name__ == "__main__":
    main()
