"""Lineage-weighted gauntlet: score agents against the pool in research/gauntlet.json.

Each pool agent is played on every seed from both seats. A lineage's win rate is the mean over its
agents, and the score is the lineage win rates weighted by their ladder share at the target band.
A candidate passes when it holds every wall lineage (win rate >= --wall-min) and, given a
baseline, outscores it by --margin.

Game results are cached per (agent file, opponent file, seed) in research/ladder/gauntlet_cache.json,
keyed by file content, so re-scoring the champion or changing the pool only plays the new games.

usage: python scripts/gauntlet.py CANDIDATE [CANDIDATE ...] [--baseline PATH] [--seeds 3] [--workers 2]
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
    if os.path.exists(CACHE):
        return json.load(open(CACHE, encoding="utf-8"))
    return {}


def save_cache(cache):
    tmp = CACHE + ".tmp"
    json.dump(cache, open(tmp, "w", encoding="utf-8"))
    os.replace(tmp, CACHE)


def score(path, seeds, workers, config=None, log=print):
    """Returns {"score", "lineages": {name: win rate}, "agents": {file: (wins, games, margin)}, "walls_ok"}."""
    cfg = config or json.load(open(CONFIG, encoding="utf-8"))
    cache = load_cache()
    me = file_hash(path)
    opps = [(name, os.path.join(ROOT, a)) for name, l in cfg["lineages"].items() for a in l["agents"]]
    todo = sorted({(opp, s) for _, opp in opps for s in seeds
                   if f"{me}:{file_hash(opp)}:{s}" not in cache})
    if todo:
        log(f"  {os.path.basename(path)}: playing {2 * len(todo)} games ({len(opps) * len(seeds) * 2 - 2 * len(todo)} cached)")
        jobs = [(path, None, opp, None, s, swap) for opp, s in todo for swap in (False, True)]
        res = []
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for r in ex.map(league.run_pair, jobs, chunksize=1):
                res.append(r)
                if len(res) % 12 == 0 or len(res) == len(jobs):
                    log(f"    {len(res)}/{len(jobs)} games")
        for i, (opp, s) in enumerate(todo):
            cache[f"{me}:{file_hash(opp)}:{s}"] = [list(res[2 * i]), list(res[2 * i + 1])]
        save_cache(cache)

    agents, lineages = {}, {}
    for name, opp in opps:
        rs = [r for s in seeds for r in cache[f"{me}:{file_hash(opp)}:{s}"]]
        w = sum(1 for a, b in rs if a > b) + 0.5 * sum(1 for a, b in rs if a == b)
        agents[os.path.relpath(opp, ROOT)] = (w, len(rs), sum(a - b for a, b in rs) / len(rs))
        lineages.setdefault(name, []).append(w / len(rs))
    lineages = {k: sum(v) / len(v) for k, v in lineages.items()}
    total = sum(l["share"] for l in cfg["lineages"].values())
    s = sum(cfg["lineages"][k]["share"] * wr for k, wr in lineages.items()) / total
    return {"score": s, "lineages": lineages, "agents": agents}


def verdict(res, cfg, wall_min, baseline=None, margin=0.0):
    """(passed, reasons) for a scored candidate against the walls and an optional baseline score."""
    reasons = [f"wall {w}: {res['lineages'][w]:.0%} < {wall_min:.0%}"
               for w in cfg.get("walls", []) if res["lineages"][w] < wall_min]
    if baseline is not None and res["score"] < baseline["score"] + margin:
        reasons.append(f"score {res['score']:.1%} does not beat baseline {baseline['score']:.1%} + {margin:.0%}")
    return not reasons, reasons


def report(path, res):
    print(f"\n{os.path.basename(path)}: weighted score {res['score']:.1%}")
    for k, wr in res["lineages"].items():
        print(f"  {k:<15} {wr:5.0%}")
    for a, (w, n, m) in res["agents"].items():
        print(f"    {os.path.basename(a):<50} {w:4.1f}/{n}  margin {m:+6.0f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates", nargs="+")
    ap.add_argument("--baseline", help="agent to beat, e.g. the current champion")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--seed0", type=int, default=SEED0)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--wall-min", type=float, default=0.5)
    ap.add_argument("--margin", type=float, default=0.0)
    a = ap.parse_args()
    # line buffering: runs go to a log file in the background, and progress should show as it happens
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    cfg = json.load(open(CONFIG, encoding="utf-8"))
    seeds = list(range(a.seed0, a.seed0 + a.seeds))

    base = None
    if a.baseline:
        base = score(a.baseline, seeds, a.workers, cfg)
        report(a.baseline, base)
    for c in a.candidates:
        res = score(c, seeds, a.workers, cfg)
        report(c, res)
        ok, why = verdict(res, cfg, a.wall_min, base, a.margin)
        print("  PASS" if ok else "  FAIL: " + "; ".join(why))


if __name__ == "__main__":
    main()
