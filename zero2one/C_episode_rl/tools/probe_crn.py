"""Probe: variance of per-game margin vs variance of the CRN-paired difference between two
nearby parameter settings (same seed, seat, opponent). Decides whether low-dim ES has signal."""
import os, sys, statistics as st
from multiprocessing import Pool
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts")); os.chdir(ROOT)
KNOB = ("_KNOB_3498_54", 14)

def run(job):
    arm, opp, seed, seat = job
    import fastsim
    flags = {KNOB[0]: KNOB[1]} if arm else None
    me = fastsim.load_agent("submissions/v7_endgame.py", f"m{arm}{opp}{seed}{seat}", flags=flags)
    op = fastsim.load_agent(f"research/pool/{opp}.py", f"o{arm}{opp}{seed}{seat}")
    r = fastsim.play(me, op, seed) if seat == 0 else fastsim.play(op, me, seed)[::-1]
    return job, r[0] - r[1]

if __name__ == "__main__":
    jobs = [(a, o, s, t) for a in (0, 1) for o in ("farm2945", "v56") for s in range(3000, 3012) for t in (0, 1)]
    with Pool(8) as p:
        res = dict(p.map(run, jobs))
    m0 = [res[(0,) + k[1:]] for k in res if k[0] == 0]
    d = [res[(1,) + k[1:]] - res[(0,) + k[1:]] for k in res if k[0] == 0]
    print("n", len(m0), "margin mean", round(st.mean(m0)), "sd", round(st.stdev(m0)), "win", sum(x > 0 for x in m0))
    print("paired diff mean", round(st.mean(d)), "sd", round(st.stdev(d)), "zero diffs", sum(abs(x) < 1 for x in d))
    print("arm1 wins", sum(res[(1,) + k[1:]] > 0 for k in res if k[0] == 0))
