import json, os, pandas as pd
d = pd.DataFrame([json.loads(l) for l in open(os.environ["CLAUDE_JOB_DIR"] + "/tmp/band.jsonl")])
d["c"] = d.cand.str.replace("submissions/", "").str.replace(".py", "")
d["w"] = d.me > d.op; d["m"] = d.me - d.op
lin = {}
for ln in open("research/ladder/lineages.tsv", encoding="utf-8"):
    if not ln.startswith(("#", "hash")):
        h, n, *_ = ln.rstrip("\n").split("\t"); lin[h] = n[:14]
d["lin"] = d.h.map(lin).fillna("other")
print(d.groupby("c").agg(n=("w", "size"), wins=("w", "sum"), rate=("w", "mean"), margin=("m", "mean")).round(3).sort_values("rate"))
full = d.groupby("c").ep.nunique(); full = full[full == d.ep.nunique()].index
print("complete cands:", list(full))
f = d[d.c.isin(full)]
print(f.pivot_table(index="c", columns="lin", values="w", aggfunc="mean").round(2))
print(f.groupby("lin").ep.nunique().to_dict())
for a, b in [("ttv1_p6", "ttv1_p8"), ("shepherd_p6", "shepherd_p8"), ("hybrid_cxd_p6", "hybrid_cxd_p8"), ("ttv1_raw", "ttv1_p6"), ("shepherd_p6", "ttv1_p6"), ("hybrid_cxd_p8", "ttv1_p6"), ("ttv1_raw", "shepherd_p6")]:
    x = d[d.c == a].set_index("ep"); y = d[d.c == b].set_index("ep"); i = x.index.intersection(y.index)
    if len(i):
        x, y = x.loc[i], y.loc[i]
        print(f"{a} -> {b}: n={len(i)} wins {x.w.sum()}->{y.w.sum()} (+{(~x.w & y.w).sum()}/-{(x.w & ~y.w).sum()}), dmargin {(y.m - x.m).mean():+.0f}, boards changed {(x.me != y.me).sum()}")
