"""Paired hold-out report: each candidate vs ttv1_p6 on 09-30 band tapes and on own boards unseen on 09-29."""
import json, os, pandas as pd
L = r"C:\Users\chauj\Desktop\kagriculture\research\ladder"
BASE = "ttv1_p6"
def load(p):
    d = pd.DataFrame([json.loads(l) for l in open(p)]) if os.path.exists(p) else pd.DataFrame()
    if len(d): d["c"] = d.cand.str.split("/").str[-1].str.replace(".py", "")
    return d
old = set(load(os.path.join(L, "own2300_matrix_0929.jsonl")).ep.astype(str))
sets = {"band_0930": load(os.path.join(L, "holdout_band_0930.jsonl")),
        "own_new": load(os.path.join(L, "holdout_own_0930.jsonl"))}
if len(sets["own_new"]): sets["own_new"] = sets["own_new"][~sets["own_new"].ep.astype(str).isin(old)]
rows = []
for name, d in list(sets.items()) + [("total", pd.concat([v for v in sets.values() if len(v)]))]:
    if not len(d): continue
    b = d[d.c == BASE].drop_duplicates("ep").set_index("ep")
    for c, g in d.groupby("c"):
        g = g.drop_duplicates("ep").set_index("ep"); i = g.index.intersection(b.index); g, bb = g.loc[i], b.loc[i]
        w, bw = g.me > g.op, bb.me > bb.op
        rows.append(dict(set=name, c=c, n=len(i), wins=int(w.sum()), base=int(bw.sum()), gain=int((w & ~bw).sum()),
                         loss=int((~w & bw).sum()), dmargin=round(((g.me - g.op) - (bb.me - bb.op)).mean())))
print(pd.DataFrame(rows).to_string(index=False))
