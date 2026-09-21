"""Evolution-strategy tuning of agents/main.py PARAMS by self-play on the fast simulator.

Each generation samples antithetic perturbations of the current mean (in a normalized [0,1] box),
scores every candidate by mean money margin against an opponent pool on shared seeds (common random
numbers), and moves the mean along the rank-weighted perturbations.

usage: python scripts/tune.py --gens 15 --pop 8 --seeds 5
Progress is appended to tuning/log.jsonl; the latest mean is written to tuning/best_params.json.
"""
import argparse
import json
import os
import random
import statistics
import sys
import time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import league  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT = os.path.join(ROOT, "tuning", "agent_snapshot.py")  # frozen copy so agents/main.py can change meanwhile
OUT = os.path.join(ROOT, "tuning")

PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
# name -> (low, high, is_int)
SPACE = {
    "hands_max": (6, 16, True),
    "unit_turns": (10.0, 24.0, False),
    "capital_rate": (0.0, 0.08, False),
    "labor_cost": (0.0, 10.0, False),
    "min_score": (-10.0, 30.0, False),
    "land_buffer": (0, 5000, True),
    "land_last_day": (10, 24, True),
    "demand_growth": (0.0, 1.5, False),
    "animal_labor": (2.0, 8.0, False),
    "crop_labor": (0.5, 4.0, False),
    "drop_carry": (5, 25, True),
    "dist_w": (0.5, 4.0, False),
    "sticky": (0.0, 30.0, False),
    "weed_prio": (0.0, 40.0, False),
    "labor_util": (0.5, 1.2, False),
    "wheat_keep": (2.5, 6.0, False),
    "wheat_buy": (1.0, 2.5, False),
}
for p in PRODUCTS:
    SPACE[f"reserve_frac.{p}"] = (0.05, 1.0, False)


def defaults():
    import importlib.util
    spec = importlib.util.spec_from_file_location("agent_defaults", AGENT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.PARAMS


def to_params(z):
    out = {}
    for (name, (lo, hi, is_int)), v in zip(SPACE.items(), z):
        v = lo + min(1.0, max(0.0, v)) * (hi - lo)
        v = int(round(v)) if is_int else round(v, 4)
        if "." in name:
            k, sub = name.split(".")
            out.setdefault(k, {})[sub] = v
        else:
            out[name] = v
    return out


def from_params(P):
    z = []
    for name, (lo, hi, _) in SPACE.items():
        if "." in name:
            k, sub = name.split(".")
            v = P[k][sub]
        else:
            v = P[name]
        z.append((v - lo) / (hi - lo))
    return z


def score(out):
    return statistics.mean(r[0] - r[1] for rs in out.values() for r in rs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gens", type=int, default=15)
    ap.add_argument("--pop", type=int, default=8, help="even; antithetic pairs")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--sigma", type=float, default=0.12)
    ap.add_argument("--lr", type=float, default=0.6)
    ap.add_argument("--opponents", nargs="+",
                    default=[os.path.join(ROOT, "agents", "archive", "v1.py"),
                             os.path.join(ROOT, "agents", "archive", "v2.py"), AGENT])
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    best_path = os.path.join(OUT, "best_params.json")
    mean = from_params(json.load(open(best_path)) if a.resume and os.path.exists(best_path) else defaults())
    dim = len(mean)
    rng = random.Random(12345)
    pool = ProcessPoolExecutor(max_workers=os.cpu_count())
    log = open(os.path.join(OUT, "log.jsonl"), "a")
    for gen in range(a.gens):
        t0 = time.time()
        seeds = [rng.randrange(10**6) for _ in range(a.seeds)]
        eps = []
        for _ in range(a.pop // 2):
            e = [rng.gauss(0, 1) for _ in range(dim)]
            eps += [e, [-x for x in e]]
        cands = [[m + a.sigma * x for m, x in zip(mean, e)] for e in eps]
        fits = []
        for z in cands + [mean]:
            out = league.evaluate(AGENT, a.opponents, seeds, params=to_params(z), pool=pool)
            fits.append(score(out))
        base = fits[-1]
        fits = fits[:-1]
        order = sorted(range(len(fits)), key=lambda i: fits[i])
        ranks = [0.0] * len(fits)
        for r, i in enumerate(order):
            ranks[i] = r / (len(fits) - 1) - 0.5
        step = [sum(ranks[i] * eps[i][d] for i in range(len(eps))) / len(eps) for d in range(dim)]
        mean = [min(1.0, max(0.0, m + a.lr * a.sigma * s * 2)) for m, s in zip(mean, step)]
        rec = {"gen": gen, "mean_fit": base, "best_cand": max(fits), "cand_avg": statistics.mean(fits),
               "secs": round(time.time() - t0), "params": to_params(mean)}
        log.write(json.dumps(rec) + "\n")
        log.flush()
        json.dump(to_params(mean), open(best_path, "w"), indent=1)
        print(f"gen {gen:2d}  mean-fit {base:+8.0f}  cand best {max(fits):+8.0f} avg {statistics.mean(fits):+8.0f}"
              f"  ({rec['secs']}s)", flush=True)
    pool.shutdown()


if __name__ == "__main__":
    main()

