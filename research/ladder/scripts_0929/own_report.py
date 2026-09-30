import json, os, pandas as pd
J = os.environ["CLAUDE_JOB_DIR"] + "/tmp/"
base = pd.DataFrame([json.loads(l) for l in open(J + "m2300.jsonl")]); base = base[base.cand == "submissions/ttv1_p6.py"].set_index("ep")
d = pd.DataFrame([json.loads(l) for l in open(J + "own_screen.jsonl")]); d["c"] = d.cand.str.split("/").str[-1].str.replace(".py", "")
for c, g in d.groupby("c"):
    g = g.set_index("ep"); b = base.loc[g.index]; w, bw = g.me > g.op, b.me > b.op
    print(f"{c:<22} n={len(g)} wins {w.sum()} vs base {bw.sum()} (+{(w&~bw).sum()}/-{(~w&bw).sum()}) dmargin {((g.me-g.op)-(b.me-b.op)).mean():+.0f} changed {(g.me!=b.me).sum()}")
