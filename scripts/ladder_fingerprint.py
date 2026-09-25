"""Opening fingerprint of a local agent over its first 48 actions.

Prints: file, md5 openhash (same as ladder_harvest.py), turn-0 spend, stream_h48.
stream_h48 follows the public episode dataset's stream_hashes.csv byte for byte (sha256 over
canonical JSON per action, NUL between turns, 16 hex), so local agents join to ladder seats.

The opening is seed- and seat-independent but can depend on the opponent (hybrid2965 opens
c2b3c0360e against v7 and 14c1ec572a against V53 or herd-safe), so each agent is fingerprinted
against every reference opponent in OPPONENTS and prints one line per (agent, opponent).

usage: python scripts/ladder_fingerprint.py [--workers 3] "research/ladder_pool/*.py"
Known hashes are named in research/ladder/lineages.tsv.
"""
import sys, json, hashlib, glob, os
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPPONENTS = {
    "v7": os.path.join(ROOT, "submissions", "v7_endgame.py"),
    "v53": os.path.join(ROOT, "research", "outputs", "kaggriculture-v53-opening-signature", "v53_agent", "main.py"),
    "herd": os.path.join(ROOT, "research", "pool", "the-shepherds-ledger-herd-safe-sovereign.py"),
}


def stream_h48(actions):
    h = hashlib.sha256()
    for a in actions:
        h.update(json.dumps(a or {}, sort_keys=True, separators=(",", ":")).encode())
        h.update(b"\0")
    return h.hexdigest()[:16]


def fp(job, steps=49, seed=12345):
    path, opp = job
    from kaggle_environments import make
    try:
        env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": steps}, debug=False)
        env.run([path, OPPONENTS[opp]])
        acts = [env.steps[t][0].action for t in range(1, 49)]
        seq = [json.dumps(a, sort_keys=True) for a in acts]
        sp = 3000.0 - env.steps[1][0].observation["farms"][0]["money"]
        return (os.path.basename(path), opp, hashlib.md5("|".join(seq).encode()).hexdigest()[:10], sp,
                stream_h48(acts))
    except Exception as e:
        return os.path.basename(path), opp, "ERR " + repr(e)[:80], None, None


if __name__ == "__main__":
    args = sys.argv[1:]
    workers = 3
    if args[:1] == ["--workers"]:
        workers, args = int(args[1]), args[2:]
    files = [f for p in args for f in glob.glob(p)]
    jobs = [(f, o) for f in files for o in OPPONENTS]
    with ProcessPoolExecutor(workers) as ex:
        for r in ex.map(fp, jobs):
            print(*r, flush=True)
