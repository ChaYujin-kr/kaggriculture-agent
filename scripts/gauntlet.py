"""Lineage-weighted gauntlet: score agents against the pool in research/gauntlet.json.

Each pool agent is played on every seed, from both seats (or, with --seats 1, one seat alternating by seed). A lineage's win rate is the mean over its
agents, and the score is the lineage win rates weighted by their ladder share at the target band.
"climb" lineages (met on the way up from 600) are played too but left out of the weighted score.
A candidate passes when it holds every wall lineage (each of its agents at or above that wall's
minimum; --wall-min for walls given as a plain list) and, given a baseline, outscores it by more
than --margin.

Game results are cached per (agent file, opponent file, seed, seat) in research/ladder/gauntlet_cache.json,
keyed by file content, so re-scoring the champion or changing the pool only plays the new games.

usage: python scripts/gauntlet.py CANDIDATE [CANDIDATE ...] [--baseline PATH] [--seeds 6] [--seats 1|2] [--workers 3]
"""
import argparse
import hashlib
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import league  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "research", "gauntlet.json")
CACHE = os.path.join(ROOT, "research", "ladder", "gauntlet_cache.json")
SEED0 = 23000


def file_hash(path):
    return hashlib.sha1(open(path, "rb").read()).hexdigest()[:16]


def load_cache():
    """{"me:opp:seed:swap": [my, their]}. Older caches kept both seats under "me:opp:seed"."""
    if not os.path.exists(CACHE):
        return {}
    cache = {}
    for k, v in json.load(open(CACHE, encoding="utf-8")).items():
        if k.count(":") == 2:
            cache[f"{k}:0"], cache[f"{k}:1"] = v[0], v[1]
        else:
            cache[k] = v
    return cache


def seat_plan(seeds, seats):
    """(seed, swap) pairs to play. Outcomes cluster by seed and the seat barely matters, so with
    seats=1 each seed is played once, alternating seats, which buys twice the seeds per game."""
    if seats == 2:
        return [(s, swap) for s in seeds for swap in (0, 1)]
    return [(s, s % 2) for s in seeds]


def save_cache(cache):
    tmp = CACHE + ".tmp"
    json.dump(cache, open(tmp, "w", encoding="utf-8"))
    os.replace(tmp, CACHE)


def score(path, seeds, workers, config=None, log=print, seats=2):
    """Returns {"score", "lineages": {name: win rate}, "worst": {name: weakest agent}, "agents": {file: (wins, games, margin)}}."""
    cfg = config or json.load(open(CONFIG, encoding="utf-8"))
    cache = load_cache()
    me = file_hash(path)
    pool = {**cfg["lineages"], **cfg.get("climb", {}).get("lineages", {})}
    opps = [(name, os.path.join(ROOT, a)) for name, l in pool.items() for a in l["agents"]]
    plan = seat_plan(seeds, seats)
    key = lambda opp, s, swap: f"{me}:{file_hash(opp)}:{s}:{swap}"
    todo = sorted({(opp, s, swap) for _, opp in opps for s, swap in plan if key(opp, s, swap) not in cache})
    if todo:
        log(f"  {os.path.basename(path)}: playing {len(todo)} games ({len(opps) * len(plan) - len(todo)} cached)")
        jobs = [(path, None, opp, None, s, bool(swap)) for opp, s, swap in todo]
        res = []
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for r in ex.map(league.run_pair, jobs, chunksize=1):
                res.append(r)
                if len(res) % 12 == 0 or len(res) == len(jobs):
                    log(f"    {len(res)}/{len(jobs)} games")
        for (opp, s, swap), r in zip(todo, res):
            cache[key(opp, s, swap)] = list(r)
        save_cache(cache)

    agents, lineages = {}, {}
    for name, opp in opps:
        rs = [cache[key(opp, s, swap)] for s, swap in plan]
        w = sum(1 for a, b in rs if a > b) + 0.5 * sum(1 for a, b in rs if a == b)
        agents[os.path.relpath(opp, ROOT)] = (w, len(rs), sum(a - b for a, b in rs) / len(rs))
        lineages.setdefault(name, []).append(w / len(rs))
    worst = {k: min(v) for k, v in lineages.items()}
    lineages = {k: sum(v) / len(v) for k, v in lineages.items()}
    total = sum(l["share"] for l in cfg["lineages"].values())
    s = sum(l["share"] * lineages[k] for k, l in cfg["lineages"].items()) / total
    return {"score": s, "lineages": lineages, "worst": worst, "agents": agents}


def verdict(res, cfg, wall_min, baseline=None, margin=0.0):
    """(passed, reasons) for a scored candidate against the walls and an optional baseline score.

    A wall is held only if every agent of that lineage is held: averaging let a 0/6 against V53
    hide behind a 6/6 against the weaker K0013 V46 of the same lineage."""
    walls = cfg.get("walls", [])
    if not isinstance(walls, dict):
        walls = dict.fromkeys(walls, wall_min)
    reasons = [f"wall {w}: worst agent {res['worst'][w]:.0%} < {m:.0%}"
               for w, m in walls.items() if res["worst"][w] < m]
    if baseline is not None and res["score"] <= baseline["score"] + margin:
        reasons.append(f"score {res['score']:.1%} does not beat baseline {baseline['score']:.1%} + {margin:.0%}")
    return not reasons, reasons


def report(path, res, cfg=None):
    climb = set((cfg or {}).get("climb", {}).get("lineages", {}))
    print(f"\n{os.path.basename(path)}: weighted score {res['score']:.1%}")
    for k, wr in res["lineages"].items():
        tag = "  [climb, not in score]" if k in climb else ""
        print(f"  {k:<15} {wr:5.0%}  (worst agent {res['worst'][k]:.0%}){tag}")
    for a, (w, n, m) in res["agents"].items():
        print(f"    {os.path.basename(a):<50} {w:4.1f}/{n}  margin {m:+6.0f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates", nargs="+")
    ap.add_argument("--baseline", help="agent to beat, e.g. the current champion")
    # 3 seeds flipped the champion's hybrid and V53 results from 2/6 to 8/12 once 3 more were
    # added: outcomes cluster by seed, so fewer than 6 is noise
    ap.add_argument("--seeds", type=int, default=6)
    ap.add_argument("--seed0", type=int, default=SEED0)
    ap.add_argument("--seats", type=int, choices=(1, 2), default=2,
                    help="1: one game per seed, alternating seats (half the games per seed)")
    # ~320 MB per worker with two 1 MB agents loaded; 3 fit in the ~1.1 GB this laptop has free
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--wall-min", type=float, default=0.5)
    ap.add_argument("--margin", type=float, default=0.0)
    a = ap.parse_args()
    # line buffering: runs go to a log file in the background, and progress should show as it happens
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    cfg = json.load(open(CONFIG, encoding="utf-8"))
    seeds = list(range(a.seed0, a.seed0 + a.seeds))

    base = None
    if a.baseline:
        base = score(a.baseline, seeds, a.workers, cfg, seats=a.seats)
        report(a.baseline, base, cfg)
    for c in a.candidates:
        res = score(c, seeds, a.workers, cfg, seats=a.seats)
        report(c, res, cfg)
        ok, why = verdict(res, cfg, a.wall_min, base, a.margin)
        print("  PASS" if ok else "  FAIL: " + "; ".join(why))


if __name__ == "__main__":
    main()
