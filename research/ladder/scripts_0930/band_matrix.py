import json, os, sys
from concurrent.futures import ProcessPoolExecutor
ROOT = r"C:\Users\chauj\Desktop\kagriculture"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import tape_eval as te
B = os.path.join(ROOT, os.environ.get("OUT", "research/ladder/band_tapes_0930"))
def main():
    out, cands = sys.argv[1], sys.argv[2:]
    idx = [json.loads(l) for l in open(os.path.join(B, "index.jsonl"))]
    done = set()
    if os.path.exists(out):
        for ln in open(out): d = json.loads(ln); done.add((d["ep"], d["cand"]))
    jobs, meta = [], []
    for c in cands:
        for r in idx:
            if (r["ep"], c) in done: continue
            jobs.append((c, os.path.join(B, f"tape_{r['ep']}.py"), int(r["seed"]), 1 - r["seat"]))
            meta.append(dict(r, cand=c))
    print(len(jobs), "jobs", flush=True)
    with ProcessPoolExecutor(max_workers=4) as ex, open(out, "a") as f:
        for m, (x, y) in zip(meta, ex.map(te.play, jobs, chunksize=1)):
            m.update(me=x, op=y); f.write(json.dumps(m) + "\n"); f.flush()
if __name__ == "__main__":
    main()
