"""v2 check: does DART-style noise on the open-loop teacher desync it? Replace a fraction eps of
unit commands (per turn, per unit) with PASS, steps in [lo,hi). Measure bank vs clean teacher, same seeds."""
import sys, random, time
sys.path.insert(0, r"C:/Users/chauj/Desktop/kagriculture/scripts")
import fastsim
from concurrent.futures import ProcessPoolExecutor
CH = r"C:/Users/chauj/Desktop/kagriculture/submissions/v7_endgame.py"
OPP = r"C:/Users/chauj/Desktop/kagriculture/research/pool/farm2945.py"

def run(job):
    eps, lo, hi, seed = job
    t = fastsim.load_agent(CH, "t"); o = fastsim.load_agent(OPP, "o")
    rng = random.Random(seed * 7 + int(eps * 1000) + lo)
    def noisy(obs):
        a = t(obs)
        st = obs.get("step", 0) if isinstance(obs, dict) else getattr(obs, "step", 0)
        if eps > 0 and lo <= st < hi:
            if rng.random() < eps: a = dict(a, farmer=["PASS"])
            a = dict(a, hands=[["PASS"] if rng.random() < eps else h for h in a.get("hands", [])])
        return a
    r = fastsim.play(noisy, o, seed)
    return eps, lo, hi, seed, r[0], r[1]

if __name__ == "__main__":
    seeds = [11, 22, 33, 44, 55, 66]
    cfgs = [(0.0, 0, 0), (0.05, 0, 720), (0.10, 0, 720), (0.10, 48, 96), (0.10, 300, 348)]
    jobs = [(e, lo, hi, s) for (e, lo, hi) in cfgs for s in seeds]
    with ProcessPoolExecutor(8) as ex: res = list(ex.map(run, jobs))
    for c in cfgs:
        rs = [r for r in res if r[:3] == c]
        me = sum(r[4] for r in rs) / len(rs); op = sum(r[5] for r in rs) / len(rs)
        w = sum(r[4] > r[5] for r in rs)
        print(c, f"teacher {me:,.0f} opp {op:,.0f} wins {w}/{len(rs)}")
