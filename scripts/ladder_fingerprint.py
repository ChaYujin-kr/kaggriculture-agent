"""Opening fingerprint of a local agent: md5 over its first 48 actions, same as ladder_harvest.py.

usage: python scripts/ladder_fingerprint.py "research/ladder_pool/*.py"
Known hashes are named in research/ladder/lineages.tsv.
"""
import sys, json, hashlib, glob, os
from concurrent.futures import ProcessPoolExecutor

V7 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "submissions", "v7_endgame.py")


def fp(path, steps=49, seed=12345):
    from kaggle_environments import make
    try:
        env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": steps}, debug=False)
        env.run([path, V7])
        seq = [json.dumps(env.steps[t][0].action, sort_keys=True) for t in range(1, 49)]
        sp = 3000.0 - env.steps[1][0].observation["farms"][0]["money"]
        return os.path.basename(path), hashlib.md5("|".join(seq).encode()).hexdigest()[:10], sp
    except Exception as e:
        return os.path.basename(path), "ERR " + repr(e)[:80], None


if __name__ == "__main__":
    files = [f for p in sys.argv[1:] for f in glob.glob(p)]
    with ProcessPoolExecutor(6) as ex:
        for r in ex.map(fp, files):
            print(*r, flush=True)
