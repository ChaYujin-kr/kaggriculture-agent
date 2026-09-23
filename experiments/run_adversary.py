"""Run the adversarial layer (E1 feed denial / E2 lineage tag) on top of the champion.

usage: python experiments/run_adversary.py [--mode tag|squeeze] [--seeds 6] [--workers 3]
Each arm plays the same seeds in both seats against the same opponents (paired comparison).
"""
import argparse
import importlib.util
import os
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import fastsim  # noqa: E402

CHAMP = os.path.join(ROOT, "research", "pool", "aurax7_v7.py")
POOL = [os.path.join(ROOT, "research", "pool", f) for f in
        ("aurax7_v7.py", "morewheat.py", "clonerace.py", "hybrid2965.py")]


def load_layer(settings, tag):
    spec = importlib.util.spec_from_file_location(f"adv_{tag}", os.path.join(ROOT, "agents", "layer_adversary.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.ADV.update(settings)
    return mod


def play(job):
    settings, opp_path, seed, swap, tag = job
    base = fastsim.load_agent(CHAMP, f"c{tag}")
    mod = load_layer(settings, tag)

    def agent(obs):
        b = base(obs)
        try:
            return mod.layer(obs, b)
        except Exception:
            return b

    opp = fastsim.load_agent(opp_path, f"o{tag}")
    r = fastsim.play(opp, agent, seed) if swap else fastsim.play(agent, opp, seed)
    mine, theirs = (r[1], r[0]) if swap else (r[0], r[1])
    return os.path.basename(opp_path), mine, theirs, mod._S.get("tag"), mod._S.get("opp_open_spend")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="tag", choices=["tag", "squeeze", "noise"])
    ap.add_argument("--seeds", type=int, default=6)
    ap.add_argument("--seed0", type=int, default=25000)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--set", nargs="*", default=[], help="ADV overrides k=v")
    a = ap.parse_args()
    settings = {"tag_only": a.mode != "squeeze", "squeeze_on": a.mode == "squeeze", "noise_on": a.mode == "noise"}
    for kv in a.set:
        k, v = kv.split("=", 1)
        settings[k] = int(v) if v.lstrip("-").isdigit() else v
    jobs = [(settings, opp, s, swap, f"{i}{s}{swap}")
            for i, opp in enumerate(POOL)
            for s in range(a.seed0, a.seed0 + a.seeds) for swap in (False, True)]
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        res = list(ex.map(play, jobs))
    by_opp = {}
    for opp, mine, theirs, tag, spend in res:
        by_opp.setdefault(opp, []).append((mine, theirs, tag, spend))
    print(f"mode={a.mode} settings={settings}")
    for opp, rows in by_opp.items():
        w = sum(1 for r in rows if r[0] > r[1]) + 0.5 * sum(1 for r in rows if r[0] == r[1])
        tags = {}
        for r in rows:
            tags[r[2]] = tags.get(r[2], 0) + 1
        spends = [r[3] for r in rows if r[3] is not None]
        print(f"  vs {opp:<16} wins {w:4.1f}/{len(rows)}  margin "
              f"{statistics.mean(r[0] - r[1] for r in rows):+8.0f}  tag {tags} "
              f"opening spend median {statistics.median(spends) if spends else '-':.0f}")


if __name__ == "__main__":
    main()

