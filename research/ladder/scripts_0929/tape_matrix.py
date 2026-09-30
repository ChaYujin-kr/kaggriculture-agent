"""Per-board results of candidates vs ladder tapes (>= min opp lb). Writes jsonl rows: ep, opp, lb, lin, cand, me, op."""
import json, os, sys
from concurrent.futures import ProcessPoolExecutor
ROOT = r"C:\Users\chauj\Desktop\kagriculture"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import tape_eval as te

def main():
    out, minlb, cands = sys.argv[1], float(sys.argv[2]), sys.argv[3:]
    lb = te.opp_scores()
    lin = {}
    for ln in open(os.path.join(ROOT, "research/ladder/lineages.tsv"), encoding="utf-8"):
        if not ln.startswith(("#", "hash")):
            h, name, *_ = ln.rstrip("\n").split("\t"); lin[h] = name[:24]
    summ = {}
    for ln in open(os.path.join(ROOT, "research/ladder/summaries.jsonl"), encoding="utf-8"):
        r = json.loads(ln)
        if "error" not in r: summ[str(r["ep"])] = r
    boards = []
    for f in sorted(os.listdir(te.TAPES)):
        if not (f.startswith("tape_") and f.endswith(".py")): continue
        r = summ.get(f[5:-3])
        if r and r["sub"] in te.PLAYED and r.get("seed") and lb.get(r["opp"], 0) >= minlb:
            boards.append((r, os.path.join(te.TAPES, f)))
    done = set()
    if os.path.exists(out):
        for ln in open(out): d = json.loads(ln); done.add((d["ep"], d["cand"]))
    jobs, meta = [], []
    for c in cands:
        for r, t in boards:
            if (r["ep"], c) in done: continue
            jobs.append((c, t, int(r["seed"]), r["me_seat"]))
            meta.append(dict(ep=r["ep"], opp=r["opp"], lb=lb.get(r["opp"]), lin=lin.get(r["openhash_op"], "other"),
                             h=r["openhash_op"], sub=r["sub"], lad_me=r["rew_me"], lad_op=r["rew_op"], cand=c))
    print(len(boards), "boards,", len(jobs), "jobs", flush=True)
    with ProcessPoolExecutor(max_workers=4) as ex, open(out, "a") as f:
        for m, (x, y) in zip(meta, ex.map(te.play, jobs, chunksize=1)):
            m.update(me=x, op=y); f.write(json.dumps(m) + "\n"); f.flush()

if __name__ == "__main__":
    main()
