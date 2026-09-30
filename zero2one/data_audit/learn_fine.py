"""Step 6b' (fine labels) + curriculum (a): how much data does imitation need, per tier; transfer between tiers;
lineage and tier classifiers.  Input: turns/*.parquet (extract.py) + window_replay_seats.parquet (audit.py).

Unit of sampling = one seat-game (719 turns).  Test sets are fixed seat-games held out BY EPISODE, and separately BY
SUBMISSION (no test agent seen in training).  Learning curve: err(N) = a*N^-b + c fitted on the mean curve; CIs by a
cluster bootstrap over test seat-games x training replicates (B=1000).
"""
import os, glob, json, time, warnings
import numpy as np, pandas as pd, lightgbm as lgb
from scipy.optimize import curve_fit
from sklearn.metrics import roc_auc_score
warnings.filterwarnings("ignore")
D = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(D, "figs")
SEED = 20260923
rng = np.random.default_rng(SEED)
t00 = time.time()

def _load(p):
    x = pd.read_parquet(p)
    for c in x.columns:
        if c in ("episode_id",): continue
        if not pd.api.types.is_numeric_dtype(x[c]): x[c] = x[c].astype(str).astype("category")
        elif c != "seat": x[c] = x[c].astype(np.float32)
    return x
T = pd.concat([_load(p) for p in sorted(glob.glob(os.path.join(D, "turns", "part_*.parquet")))], ignore_index=True)
for c in ("y_farmer", "y_hands_mode", "y_market"): T[c] = T[c].astype(str).astype("category")
Fn = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(os.path.join(D, "turns_fine", "part_*.parquet")))], ignore_index=True)
for c in ("y_farmer_fine", "y_hand0_fine"): Fn[c] = Fn[c].astype(str).astype("category")
Fn["step"] = Fn.step.astype(np.float32)
T = T.merge(Fn, on=["episode_id", "seat", "step"], how="inner"); del Fn
W = pd.read_parquet(os.path.join(D, "window_replay_seats.parquet"))
T = T.merge(W[["episode_id", "seat", "sub", "tier", "stream_h136", "win", "r_last"]], on=["episode_id", "seat"], how="inner")
T["key"] = (T.episode_id.astype(np.int64) * 2 + T.seat.astype(np.int64))
LABELS = ["y_farmer", "y_hands_mode", "y_market", "y_farmer_fine", "y_hand0_fine"]
DROP = {"episode_id", "seat", "sub", "tier", "stream_h136", "win", "r_last", "key", "n_sell", "n_buy_seed", "n_buy_animal",
        "n_buy_land", "n_hire", *LABELS}
FEATS = [c for c in T.columns if c not in DROP]
XF = T[FEATS].values.astype(np.float32)
seats = T.drop_duplicates("key")[["key", "episode_id", "seat", "sub", "tier", "stream_h136", "win", "r_last"]].reset_index(drop=True)
OUT = {"n_turn_rows": int(len(T)), "n_seats_by_tier": seats.tier.value_counts().to_dict(),
       "n_subs_by_tier": seats.groupby("tier")["sub"].nunique().to_dict(), "features": FEATS}
print(OUT["n_seats_by_tier"], len(FEATS), flush=True)
idx_by_key = T.groupby("key").indices
PARAMS = dict(objective="multiclass", learning_rate=0.1, num_leaves=63, min_data_in_leaf=40, feature_fraction=0.8,
              bagging_fraction=0.8, bagging_freq=1, lambda_l2=1.0, verbose=-1, num_threads=8, seed=SEED)
ROUNDS = 80

def rows(keys):
    return np.concatenate([idx_by_key[k] for k in keys])

def train_eval(train_keys, test_keys, label, classes):
    tr, te = rows(train_keys), rows(test_keys)
    ymap = {c: i for i, c in enumerate(classes)}
    ytr = np.asarray(T[label].values[tr]); ytr = np.array([ymap.get(v, len(classes) - 1) for v in ytr])
    yte = np.array([ymap.get(v, len(classes) - 1) for v in np.asarray(T[label].values[te])])
    p = dict(PARAMS, num_class=len(classes))
    m = lgb.train(p, lgb.Dataset(XF[tr], ytr), ROUNDS)
    pred = m.predict(XF[te]).argmax(1)
    correct = (pred == yte)
    # per test seat accuracy (for cluster bootstrap)
    keys_te = T.key.values[te]
    per = pd.Series(correct).groupby(keys_te).mean()
    return per.reindex(test_keys).values

def classes_of(label, keys, k=20):
    vc = T[label].values[rows(keys)]
    s = pd.Series(vc).value_counts()
    top = list(s.index[:k - 1]) + (["__other"] if len(s) > k - 1 else [])
    return top

def power(N, a, b, c): return a * N ** (-b) + c

def fit_curve(Ns, err):
    try:
        p, _ = curve_fit(power, np.array(Ns, float), np.array(err), p0=[0.5, 0.5, min(err) * 0.9],
                         bounds=([0, 0.01, 0], [10, 3, 1]), maxfev=20000)
        return p
    except Exception:
        return None

def n_for(p, frac):
    a, b, c = p
    acc_inf = 1 - c
    gap = (1 - frac) * acc_inf          # acc(N) >= frac * acc_inf  <=>  a N^-b <= (1-frac) acc_inf
    return (a / gap) ** (1 / b) if gap > 0 else np.inf

def n_within(p, pp):
    a, b, c = p
    return (a / pp) ** (1 / b)

def learning_curve(name, pool_keys, test_keys, label, Ns, reps, classes=None):
    classes = classes or classes_of(label, pool_keys)
    res = {}
    for N in Ns:
        if N > len(pool_keys): continue
        res[N] = []
        for r in range(reps.get(N, 1)):
            tk = list(np.random.default_rng(SEED + 17 * N + r).choice(pool_keys, N, replace=False))
            res[N].append(train_eval(tk, test_keys, label, classes))
        print(f"  {name} N={N} acc={np.mean([x.mean() for x in res[N]]):.4f} t={time.time() - t00:.0f}s", flush=True)
    Ns_ok = sorted(res)
    mean_acc = [float(np.mean([x.mean() for x in res[N]])) for N in Ns_ok]
    p = fit_curve(Ns_ok, [1 - a for a in mean_acc])
    # cluster bootstrap: resample test seats, pick one replicate per N
    B = 30 if SMOKE else 1000; bs = {"n95": [], "n99": [], "n_within_1pp": [], "acc_inf": []}
    nt = len(test_keys); brng = np.random.default_rng(SEED)
    for _ in range(B):
        ii = brng.integers(0, nt, nt)
        accs = [res[N][brng.integers(0, len(res[N]))][ii].mean() for N in Ns_ok]
        q = fit_curve(Ns_ok, [1 - a for a in accs])
        if q is None: continue
        bs["n95"].append(n_for(q, 0.95)); bs["n99"].append(n_for(q, 0.99)); bs["n_within_1pp"].append(n_within(q, 0.01))
        bs["acc_inf"].append(1 - q[2])
    ci = {k: [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 50)), float(np.nanpercentile(v, 97.5))] for k, v in bs.items()}
    out = {"label": label, "classes": classes, "Ns": Ns_ok, "mean_acc": mean_acc,
           "sd_acc_over_reps": [float(np.std([x.mean() for x in res[N]])) for N in Ns_ok],
           "fit_a_b_c": None if p is None else [float(x) for x in p],
           "acc_inf": None if p is None else float(1 - p[2]),
           "N95": None if p is None else float(n_for(p, 0.95)), "N99": None if p is None else float(n_for(p, 0.99)),
           "N_within_1pp": None if p is None else float(n_within(p, 0.01)), "bootstrap_ci_2.5_50_97.5": ci,
           "n_test_seats": len(test_keys), "majority_class_acc": float((T[label].values[rows(test_keys)] == classes[0]).mean())}
    # per-N CIs of accuracy (bootstrap over test seats, mean over reps)
    lo, hi = [], []
    for N in Ns_ok:
        m = np.mean(np.vstack(res[N]), axis=0)
        bb = [m[brng.integers(0, nt, nt)].mean() for _ in range(500)]
        lo.append(float(np.percentile(bb, 2.5))); hi.append(float(np.percentile(bb, 97.5)))
    out["acc_ci_lo"], out["acc_ci_hi"] = lo, hi
    return out, res

curves = {}; lc_rows = []
def record(name, out):
    curves[name] = out
    for N, a, l, h in zip(out["Ns"], out["mean_acc"], out["acc_ci_lo"], out["acc_ci_hi"]):
        fitted = None if out["fit_a_b_c"] is None else 1 - power(N, *out["fit_a_b_c"])
        lc_rows.append(dict(curve=name, N=N, acc=a, ci_lo=l, ci_hi=h, fitted_acc=fitted, acc_inf=out["acc_inf"]))

NS = [25, 50, 100, 200, 400, 800]
REPS = {25: 2, 50: 2, 100: 2, 200: 1, 400: 1, 800: 1}
SMOKE = os.environ.get("SMOKE") == "1"
if SMOKE:
    NS = [5, 10, 20]; REPS = {5: 1, 10: 1, 20: 1}; ROUNDS = 10

# ---------------- splits per tier: by episode and by submission
def split_by_episode(keys_df, n_test, seed):
    eps = keys_df.episode_id.unique(); r = np.random.default_rng(seed); r.shuffle(eps)
    te_eps, cnt = [], 0
    for e in eps:
        te_eps.append(e); cnt += (keys_df.episode_id == e).sum()
        if cnt >= n_test: break
    te = keys_df[keys_df.episode_id.isin(te_eps)]; tr = keys_df[~keys_df.episode_id.isin(te_eps)]
    return list(tr.key), list(te.key)

def split_by_sub(keys_df, n_test, seed):
    subs = keys_df["sub"].unique(); r = np.random.default_rng(seed); r.shuffle(subs)
    te_s, cnt = [], 0
    for s in subs:
        te_s.append(s); cnt += (keys_df["sub"] == s).sum()
        if cnt >= n_test: break
    te = keys_df[keys_df["sub"].isin(te_s)]
    tr = keys_df[~keys_df["sub"].isin(te_s) & ~keys_df.episode_id.isin(te.episode_id)]
    return list(tr.key), list(te.key)

splits = {}
for g in ["G1", "G2", "G3", "G4"]:
    kd = seats[seats.tier == g]
    splits[(g, "episode")] = split_by_episode(kd, 150, SEED)
    splits[(g, "sub")] = split_by_sub(kd, 150, SEED + 1)
OUT["split_sizes"] = {f"{g}|{s}": [len(v[0]), len(v[1])] for (g, s), v in splits.items()}


# fine-grained farmer verb (G1, by episode and by submission), first hand's verb (G1 by sub), per-tier fine curves
for sp in ("episode", "sub"):
    tr, te = splits[("G1", sp)]
    o, _ = learning_curve(f"G1_farmerfine_by{sp}", tr, te, "y_farmer_fine", NS, REPS); record(f"G1_farmerfine_by{sp}", o)
tr, te = splits[("G1", "sub")]
o, _ = learning_curve("G1_hand0fine_bysub", tr, te, "y_hand0_fine", NS, REPS); record("G1_hand0fine_bysub", o)
fixed = classes_of("y_farmer_fine", seats.key.tolist())
for g in ["G2", "G3", "G4"]:
    tr, te = splits[(g, "sub")]
    o, _ = learning_curve(f"{g}_farmerfine_bysub", tr, te, "y_farmer_fine", [25, 50, 100, 200, 400, 800], {25: 1, 50: 1, 100: 1, 200: 1, 400: 1, 800: 1}, fixed)
    record(f"{g}_farmerfine_bysub", o)
NT = 200; trans = {}
for gs in ["G1", "G2", "G3", "G4"]:
    tr = splits[(gs, "sub")][0]
    tk = list(np.random.default_rng(SEED).choice(tr, min(NT, len(tr)), replace=False))
    for gt in ["G1", "G2", "G3", "G4"]:
        trans[(gs, gt)] = float(np.mean(train_eval(tk, splits[(gt, "sub")][1], "y_farmer_fine", fixed)))
    print("transfer(fine) from", gs, {k[1]: round(v, 4) for k, v in trans.items() if k[0] == gs}, flush=True)
tm = pd.Series(trans).unstack(); tm.index.name = "train_tier"
tm.to_csv(os.path.join(FIG, "transfer_matrix_farmerfine_acc.csv"))
OUT["transfer_matrix_N200_farmerfine_acc"] = tm.round(4).to_dict()
pd.DataFrame(lc_rows).to_csv(os.path.join(FIG, "learning_curves_fine.csv"), index=False)
OUT["imitation_curves"] = curves
OUT["runtime_s"] = time.time() - t00
json.dump(OUT, open(os.path.join(D, "results_learn_fine.json"), "w"), indent=1, default=str)
print("done", time.time() - t00)
