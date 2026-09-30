import json, os, sys, pandas as pd
J = os.environ["CLAUDE_JOB_DIR"] + "/tmp/"
base = pd.DataFrame([json.loads(l) for l in open(J + "band.jsonl")])
base = base[base.cand == "submissions/ttv1_p6.py"].set_index("ep")
d = pd.DataFrame([json.loads(l) for l in open(J + sys.argv[1] if len(sys.argv) > 1 else J + "screen.jsonl")])
d["c"] = d.cand.str.split("/").str[-1].str.replace(".py", "")
out = []
for c, g in d.groupby("c"):
    g = g.set_index("ep"); b = base.loc[g.index]
    w, bw = g.me > g.op, b.me > b.op
    out.append(dict(c=c, n=len(g), wins=int(w.sum()), base=int(bw.sum()), gain=int((w & ~bw).sum()), loss=int((~w & bw).sum()),
                    net=int(w.sum() - bw.sum()), dmargin=round(((g.me - g.op) - (b.me - b.op)).mean()), changed=int((g.me != b.me).sum())))
print(pd.DataFrame(out).sort_values("net", ascending=False).to_string(index=False))
