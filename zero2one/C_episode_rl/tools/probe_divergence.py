"""Probe: how open-loop is v7_endgame? Record its actions (seat 0) across opponents/seeds,
report first divergent step and share of differing turns (unit vs market)."""
import json, sys, os
from multiprocessing import Pool
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.chdir(ROOT)

def run(args):
    opp, seed = args
    import fastsim
    base = fastsim.load_agent("submissions/v7_endgame.py", f"v7_{opp}_{seed}")
    log = []
    def rec(obs):
        a = base(obs)
        log.append(json.dumps({"u": [a.get("farmer"), a.get("hands")], "m": a.get("market")}, sort_keys=True, default=str))
        return a
    r = fastsim.play(rec, fastsim.load_agent(f"research/pool/{opp}.py", f"o_{opp}_{seed}"), seed)
    return opp, seed, r, log

def cmp(a, b):
    n = min(len(a), len(b)); first = None; du = dm = 0
    for i in range(n):
        x, y = json.loads(a[i]), json.loads(b[i])
        if x["u"] != y["u"]:
            du += 1; first = i if first is None else first
        if x["m"] != y["m"]:
            dm += 1
    return first, du / n, dm / n

if __name__ == "__main__":
    jobs = [(o, s) for s in (11, 12) for o in ("farm2945", "aurax7_v7", "v56")]
    with Pool(6) as p:
        res = p.map(run, jobs)
    d = {(o, s): (r, l) for o, s, r, l in res}
    for (o, s), (r, _) in d.items():
        print("game", o, s, [round(x) for x in r])
    for s in (11, 12):
        for o in ("aurax7_v7", "v56"):
            print(f"same seed {s}: farm2945 vs {o}: first_unit_div, unit_diff, mkt_diff =", cmp(d[("farm2945", s)][1], d[(o, s)][1]))
    for o in ("farm2945", "aurax7_v7", "v56"):
        print(f"same opp {o}: seed 11 vs 12:", cmp(d[(o, 11)][1], d[(o, 12)][1]))
