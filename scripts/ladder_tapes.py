"""Turn the opponents of our ladder games into tape agents, one per game, for replay on the same seed.

A tape repeats what the opponent actually did on the ladder. Its farm actions do not depend on us, so on the
game's own seed it is a close stand-in for the private fork we met; only market prices react to our play.
Check: our submitted file against its tape on that seed should give back the ladder banks.

Writes research/ladder/tapes/<ep>.py and research/ladder/tapes/index.jsonl (ep, sub, opp, seed, our seat, banks).
usage: python scripts/ladder_tapes.py --hash 36a9cf3f07 [--min-lb 0] [--threads 6]
"""
import argparse, base64, json, os, subprocess, sys, zlib
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ladder_harvest import KAGGLE, ME, ROOT, env  # noqa: E402
from make_tape_agent import TEMPLATE  # noqa: E402

S = os.path.join(ROOT, "research", "ladder")
OUT = os.path.join(S, "tapes")
RP = os.path.join(S, "rp_tapes")


def build(row):
    ep = row["ep"]
    dst = os.path.join(OUT, f"{ep}.py")
    if os.path.exists(dst):
        return row
    path = os.path.join(RP, f"episode-{ep}-replay.json")
    if not os.path.exists(path):
        subprocess.run([KAGGLE, "competitions", "replay", ep, "-p", RP], capture_output=True, env=env(), timeout=600)
    if not os.path.exists(path):
        return None
    r = json.load(open(path, encoding="utf-8"))
    steps = r["steps"]
    seat = 1 - r["info"]["TeamNames"].index(ME)
    tape = [steps[i][seat].get("action") for i in range(1, len(steps))]
    blob = base64.b64encode(zlib.compress(json.dumps(tape).encode("utf-8"), 9)).decode("ascii")
    open(dst, "w", encoding="utf-8").write(TEMPLATE.format(team=row["opp"], seat=seat, episode=ep,
                                                           bank=row["rew_op"], blob=blob))
    os.remove(path)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hash", nargs="*", default=[], help="opponent opening hashes to keep (default: all)")
    ap.add_argument("--subs", nargs="*", default=["shepherd_0925", "hybrid_resub"])
    ap.add_argument("--threads", type=int, default=6)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(RP, exist_ok=True)
    rows, seen = [], set()
    for ln in open(os.path.join(S, "summaries.jsonl"), encoding="utf-8"):
        r = json.loads(ln)
        if "error" in r or r["ep"] in seen or r["sub"] not in a.subs or r.get("seed") is None:
            continue
        if a.hash and r["openhash_op"] not in a.hash:
            continue
        seen.add(r["ep"])
        rows.append(r)
    idx_path = os.path.join(OUT, "index.jsonl")
    have = {json.loads(l)["ep"] for l in open(idx_path, encoding="utf-8")} if os.path.exists(idx_path) else set()
    print(len(rows), "games", flush=True)
    with ThreadPoolExecutor(a.threads) as ex, open(idx_path, "a", encoding="utf-8") as idx:
        for r in ex.map(build, rows):
            if r and r["ep"] not in have:
                idx.write(json.dumps({k: r[k] for k in ("ep", "sub", "opp", "seed", "me_seat", "rew_me", "rew_op",
                                                         "openhash_op", "ctime")}) + "\n")
                idx.flush()


if __name__ == "__main__":
    main()
