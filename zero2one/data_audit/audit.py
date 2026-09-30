"""Data audit, tasks 1-5: inventory, tiers, stratified sampling, representativeness, lineage.

Run build_seats.py first. Writes results_audit.json + figure CSVs into ./figs and samples into ./samples.
"""
import os, json
import numpy as np, pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

D = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(D, "raw")
FIG = os.path.join(D, "figs"); os.makedirs(FIG, exist_ok=True)
SMP = os.path.join(D, "samples"); os.makedirs(SMP, exist_ok=True)
SEED = 20260923
OUT = {}
WIN_START, WIN_END = "2026-09-13", "2026-09-22"   # 10 full UTC days, data ends 2026-09-22 22:12
OUR_TEAM = 16934238

S = pd.read_parquet(os.path.join(D, "seats.parquet"))
S = S[S.state == "COMPLETED"]

# ---------------------------------------------------------------- 1. inventory
inv = {}
eps = S.drop_duplicates("episode_id")
inv["episodes_total"] = int(eps.shape[0])
inv["episodes_by_type"] = eps["type"].value_counts().to_dict()
inv["seat_rows"] = int(S.shape[0])
inv["episodes_with_replay"] = int(eps.has_replay.sum())
inv["seats_by_engine_version_replay_only"] = S.engine_version.value_counts().to_dict()
pub = S[S["type"] == "EPISODE_TYPE_PUBLIC"]
inv["public_episodes_by_day"] = pub.drop_duplicates("episode_id").day.value_counts().sort_index().to_dict()
inv["distinct_submissions"] = int(pub["sub"].nunique())
inv["distinct_teams"] = int(pub["team"].nunique())
cov = pd.read_csv(os.path.join(R, "per_submission_coverage.csv"))
inv["per_submission_coverage_note"] = ("episodes_indexed equals that submission's row count in agents.csv, so 'coverage' is the "
                                       "share of its INDEXED games that have a stored replay, not its share of true ladder games.")
inv["coverage_quantiles"] = cov.coverage.quantile([.05, .25, .5, .75, .95]).round(4).to_dict()
inv["episodes_indexed_per_sub_quantiles"] = cov.episodes_indexed.quantile([.5, .75, .9, .99, 1]).to_dict()
# crawl concentration: share of seat-rows held by the top-k submissions
cnt = pub.groupby("sub").size().sort_values(ascending=False)
inv["seat_share_top_k_subs"] = {k: float(cnt.head(k).sum() / cnt.sum()) for k in (50, 100, 300, 1000)}
inv["n_subs_with_ge_100_seats"] = int((cnt >= 100).sum())
inv["subs_median_seats"] = float(cnt.median())
cov.merge(cnt.rename("seats").reset_index().rename(columns={"sub": "submission_id"}), how="left").to_csv(
    os.path.join(FIG, "coverage_per_submission.csv"), index=False)
pub.drop_duplicates("episode_id").groupby(["day"]).agg(
    episodes=("episode_id", "size"), replay_share=("has_replay", "mean")).to_csv(os.path.join(FIG, "episodes_by_day.csv"))

# analysis population: public, engine 1.32.7 (replay says so, or time after cutover when no replay)
post = pub[pub.engine_inferred.isin(["1.32.7", "1.32.7*"])].copy()
inv["post_cut_public_episodes"] = int(post.episode_id.nunique())
win = post[(post.day >= WIN_START) & (post.day <= WIN_END)].copy()
inv["window"] = [WIN_START, WIN_END]
inv["window_episodes"] = int(win.episode_id.nunique())
inv["window_episodes_with_replay"] = int(win[win.has_replay].episode_id.nunique())
inv["window_submissions"] = int(win["sub"].nunique()); inv["window_teams"] = int(win["team"].nunique())

# recent window vs all post-cut data (older part = 08-15..09-12)
old = post[post.day < WIN_START]
feat_cont = ["rating", "bank", "peak_crew", "total_hires", "first_land_day", "tiles_planted",
             "plants_carrot", "plants_melon", "plants_strawberry", "plants_tomato", "plants_wheat"]
def prep(df):
    df = df.copy(); df["first_land_day"] = df.first_land_day.fillna(31); return df
win = prep(win); old = prep(old); post = prep(post)
drift = []
for c in feat_cont:
    a, b = win[c].dropna(), old[c].dropna()
    ks = stats.ks_2samp(a, b)
    drift.append(dict(feature=c, mean_recent=a.mean(), mean_older=b.mean(), median_recent=a.median(),
                      median_older=b.median(), ks_D=ks.statistic, p=ks.pvalue))
drift = pd.DataFrame(drift); drift.to_csv(os.path.join(FIG, "recent_vs_older_drift.csv"), index=False)
inv["recent_vs_older"] = drift.round(4).to_dict("records")
h48_old = set(old.stream_h48.dropna()); h48_rec = win.stream_h48.dropna()
inv["share_recent_seats_whose_h48_line_seen_before_window"] = float(h48_rec.isin(h48_old).mean())
OUT["inventory"] = inv

# ---------------------------------------------------------------- 2. tiers
lb = pd.read_csv([os.path.join(R, "lb", f) for f in os.listdir(os.path.join(R, "lb"))][0])
QS = {"G1": 0.875, "G2": 0.75, "G3": 0.5}
def cuts(x):
    return {"G1_min": float(np.quantile(x, 0.875)), "G2_min": float(np.quantile(x, 0.75)), "G3_min": float(np.quantile(x, 0.5))}
# latest rating per submission (from all post-cut public games, rating right after its most recent game)
last = post.sort_values("t").groupby("sub").agg(r_last=("rating", "last"), t_last=("t", "last"), team=("team", "last"),
                                                  n_games=("episode_id", "size"))
active_subs = last[last.index.isin(win["sub"])]
team_best = active_subs.groupby("team").r_last.max()
active_teams = set(win.team)
lb_active = lb[lb.TeamId.isin(active_teams)]
tiers = {
    "leaderboard_all_teams": cuts(lb.Score), "leaderboard_teams_active_in_window": cuts(lb_active.Score),
    "episodes_active_submissions_latest_rating": cuts(active_subs.r_last),
    "episodes_active_teams_best_sub_latest_rating": cuts(team_best),
    "episodes_seat_rating_rating_N_in_window": cuts(win.rating),
}
tiers["n"] = {"leaderboard_all_teams": len(lb), "leaderboard_teams_active_in_window": len(lb_active),
              "active_submissions": len(active_subs), "active_teams": len(team_best), "window_seats": len(win)}
# reconcile: leaderboard score vs episode team-best latest rating
j = lb.set_index("TeamId").Score.to_frame().join(team_best.rename("data_best"), how="inner")
tiers["reconcile_lb_vs_data"] = {"teams_joined": len(j), "spearman": float(stats.spearmanr(j.Score, j.data_best)[0]),
                                 "median_lb_minus_data": float((j.Score - j.data_best).median()),
                                 "mad_abs_diff": float((j.Score - j.data_best).abs().median())}
# PRIMARY cut points: quantiles of the latest rating over submissions active in the window (unit = submission,
# same unit we tier seat-games by). The all-teams leaderboard quantiles are dominated by dormant teams (half the board
# sits below ~770 and those teams barely play), so they would leave G4 with ~300 window seat-games; the active-team
# leaderboard quantiles agree with the primary cuts to within ~6 points for G1/G2.
C = tiers["episodes_active_submissions_latest_rating"]
tiers["leaderboard_all_teams_tier_counts_if_used"] = None
def tier_of(r):
    return np.where(r >= C["G1_min"], "G1", np.where(r >= C["G2_min"], "G2", np.where(r >= C["G3_min"], "G3", "G4")))
tiers["primary"] = "episodes_active_submissions_latest_rating"
tiers["rule"] = ("seat-game tier = tier of the submission's latest observed rating (strength of the code), "
                 "sensitivity: tier of the seat's own post-game rating_N")
win = win.join(last.r_last, on="sub")
win["tier"] = tier_of(win.r_last); win["tier_seat"] = tier_of(win.rating)
CL = tiers["leaderboard_all_teams"]
tl = np.where(win.r_last >= CL["G1_min"], "G1", np.where(win.r_last >= CL["G2_min"], "G2", np.where(win.r_last >= CL["G3_min"], "G3", "G4")))
tiers["leaderboard_all_teams_tier_counts_if_used"] = pd.Series(tl).value_counts().sort_index().to_dict()
tiers["agreement_sub_latest_vs_seat_rating"] = float((win.tier == win.tier_seat).mean())
tiers["window_seat_counts_by_tier"] = win.tier.value_counts().sort_index().to_dict()
tiers["window_sub_counts_by_tier"] = win.groupby("tier")["sub"].nunique().to_dict()
tiers["window_replay_seat_counts_by_tier"] = win[win.has_replay].tier.value_counts().sort_index().to_dict()
# our team
ours_lb = lb[lb.TeamId == OUR_TEAM]
ours = {"leaderboard": ours_lb[["Rank", "Score", "SubmissionCount"]].to_dict("records"),
        "leaderboard_percentile_from_top": float(ours_lb.Rank.iloc[0] / len(lb)) if len(ours_lb) else None,
        "episode_data": post[post.team == OUR_TEAM].groupby("sub").agg(games=("episode_id", "size"), last_rating=("rating", "last")).reset_index().to_dict("records")}
ours["tier_by_leaderboard_score"] = str(tier_of(np.array([ours_lb.Score.iloc[0]]))[0]) if len(ours_lb) else None
ours["tier_if_2640"] = str(tier_of(np.array([2640.0]))[0])
ours["tier_by_leaderboard_score_allteams_cuts"] = "G2" if CL["G2_min"] <= ours_lb.Score.iloc[0] < CL["G1_min"] else "see cuts"
ours["active_percentile_of_2640"] = float((active_subs.r_last >= 2640).mean())
ours["active_percentile_of_lb_score"] = float((active_subs.r_last >= ours_lb.Score.iloc[0]).mean())
tiers["our_team"] = ours
OUT["tiers"] = tiers
# rating histograms for figures
bins = np.arange(-300, 3301, 50)
hist = pd.DataFrame({"bin_lo": bins[:-1],
                     "leaderboard_teams": np.histogram(lb.Score, bins)[0],
                     "active_submissions_latest": np.histogram(active_subs.r_last, bins)[0],
                     "window_seat_rating": np.histogram(win.rating, bins)[0]})
hist.to_csv(os.path.join(FIG, "tier_rating_histogram.csv"), index=False)

# ---------------------------------------------------------------- 3. stratified sampling
N_PER_TIER = 400
popR = win[win.has_replay].copy()          # features/hashes need a replay
popR["w_sub"] = 1.0 / popR.groupby("sub")["sub"].transform("size")   # equal total weight per submission
rng = np.random.default_rng(SEED)
samples = {}
for g in ["G1", "G2", "G3", "G4"]:
    P = popR[popR.tier == g]
    naive = P.sample(n=min(N_PER_TIER, len(P)), random_state=SEED)
    # submission-first: shuffle games within each sub, random sub order; take round k = the k-th game of every sub,
    # so every submission contributes 1 game before any contributes 2 (equal-submission design)
    Q = P.assign(_u=rng.random(len(P)))
    Q["_k"] = Q.groupby("sub")["_u"].rank(method="first")
    sub_order = pd.Series(rng.random(Q["sub"].nunique()), index=Q["sub"].unique())
    Q["_s"] = Q["sub"].map(sub_order)
    two = Q.sort_values(["_k", "_s"]).head(N_PER_TIER).drop(columns=["_u", "_k", "_s"])
    samples[(g, "naive")] = naive; samples[(g, "sub_first")] = two
    naive.to_csv(os.path.join(SMP, f"sample_{g}_naive.csv"), index=False)
    two.to_csv(os.path.join(SMP, f"sample_{g}_sub_first.csv"), index=False)

# power analysis (documented): one-sample shift detection vs a (large) population; two-sample for tier contrasts
from scipy.stats import norm
def n_one(d, alpha, power=0.8): return ((norm.ppf(1 - alpha / 2) + norm.ppf(power)) / d) ** 2
def n_two(d, alpha, power=0.8): return 2 * ((norm.ppf(1 - alpha / 2) + norm.ppf(power)) / d) ** 2
m_tests = 14
OUT["power_analysis"] = {
    "n_per_tier_chosen": N_PER_TIER, "seed": SEED,
    "one_sample_d0.2_alpha0.05": n_one(0.2, 0.05), "one_sample_d0.2_bonferroni14": n_one(0.2, 0.05 / m_tests),
    "two_sample_per_group_d0.2_alpha0.05": n_two(0.2, 0.05), "two_sample_per_group_d0.25_bonf14": n_two(0.25, 0.05 / m_tests),
    "ks_note": "KS ~ t-test efficiency ~0.64-0.9 for location shifts; n=400 detects d~0.2-0.25 at 80% power after multiplicity control",
    "ks_crit_D_n400_alpha0.05": float(1.358 / np.sqrt(400)),
}

# ---------------------------------------------------------------- 4. representativeness
KS_FEATS = feat_cont
CAT_FEATS = ["lineage_h48", "lineage_h136", "day"]
def lineage_cat(pop, col, k=10):
    top = pop[col].value_counts().head(k).index
    return lambda s: s.where(s.isin(top), "other")
def wecdf_ks(sample, pop_vals, pop_w):
    """one-sample KS of sample vs weighted population ECDF (pop treated as known distribution)."""
    s = np.sort(sample.dropna().values); n = len(s)
    ok = ~np.isnan(pop_vals); pv, pw = pop_vals[ok], pop_w[ok]
    o = np.argsort(pv); pv, pw = pv[o], np.cumsum(pw[o]) / pw.sum()
    grid = np.unique(np.concatenate([s, pv]))
    Fp = np.concatenate([[0], pw])[np.searchsorted(pv, grid, side="right")]
    Fs = np.searchsorted(s, grid, side="right") / n
    Dst = np.max(np.abs(Fs - Fp))
    return Dst, float(stats.kstwo.sf(Dst, n))
def chi_vs(sample_cats, pop_cats, pop_w):
    pw = pd.Series(pop_w, index=pop_cats.index).groupby(pop_cats).sum(); pw = pw / pw.sum()
    obs = sample_cats.value_counts().reindex(pw.index, fill_value=0)
    exp = pw * obs.sum()
    small = exp < 5
    if small.any():
        obs = pd.concat([obs[~small], pd.Series({"_pooled": obs[small].sum()})])
        exp = pd.concat([exp[~small], pd.Series({"_pooled": exp[small].sum()})])
    obs, exp = obs[exp > 0], exp[exp > 0]
    chi = stats.chisquare(obs, exp * obs.sum() / exp.sum())
    return float(chi.statistic), float(chi.pvalue), int(len(obs) - 1)
def hhi(s):
    p = s.value_counts(normalize=True); return float((p ** 2).sum())

rep_rows = []; conc_rows = []
for g in ["G1", "G2", "G3", "G4"]:
    P = popR[popR.tier == g].copy()
    for col, name in (("stream_h48", "lineage_h48"), ("stream_h136", "lineage_h136")):
        P[name] = lineage_cat(P, col)(P[col])
    for design in ("naive", "sub_first"):
        X = samples[(g, design)].copy()
        for col, name in (("stream_h48", "lineage_h48"), ("stream_h136", "lineage_h136")):
            X[name] = lineage_cat(P, col)(X[col])
        conc_rows.append(dict(tier=g, design=design, n=len(X), distinct_subs=X["sub"].nunique(), hhi=hhi(X["sub"]),
                              eff_n_subs=1 / hhi(X["sub"]), pop_distinct_subs=P["sub"].nunique(),
                              pop_eff_n_subs_unweighted=1 / hhi(P["sub"])))
        for ref, w in (("crawled_unweighted", np.ones(len(P))), ("submission_weighted", P.w_sub.values)):
            for c in KS_FEATS:
                Dst, p = wecdf_ks(X[c], P[c].values.astype(float), w)
                rep_rows.append(dict(tier=g, design=design, reference=ref, feature=c, test="KS", stat=Dst, p=p,
                                     sample_mean=X[c].mean(), pop_mean=np.average(P[c].fillna(P[c].mean()), weights=w)))
            for c in CAT_FEATS:
                st, p, dof = chi_vs(X[c], P[c], w)
                rep_rows.append(dict(tier=g, design=design, reference=ref, feature=c, test=f"chi2(df={dof})", stat=st, p=p))
            # win rate vs population (binomial)
            pw = float(np.average(P.win, weights=w)); k = int((X.win == 1).sum()); nn = int((X.win != 0.5).sum())
            rep_rows.append(dict(tier=g, design=design, reference=ref, feature="win", test="binom", stat=k / nn,
                                 p=float(stats.binomtest(k, nn, pw).pvalue), sample_mean=k / nn, pop_mean=pw))
rep = pd.DataFrame(rep_rows)
# multiple-testing correction within each (tier, design, reference) family
rep["p_holm"] = np.nan; rep["p_bh"] = np.nan
for key, idx in rep.groupby(["tier", "design", "reference"]).groups.items():
    rep.loc[idx, "p_holm"] = multipletests(rep.loc[idx, "p"], method="holm")[1]
    rep.loc[idx, "p_bh"] = multipletests(rep.loc[idx, "p"], method="fdr_bh")[1]
rep["reject_fdr05"] = rep.p_bh < 0.05
rep.to_csv(os.path.join(FIG, "representativeness_tests.csv"), index=False)
verdict = (rep.groupby(["tier", "design", "reference"])
           .apply(lambda d: {"representative": bool(~d.reject_fdr05.any()),
                             "failing_features": d[d.reject_fdr05].feature.tolist()}).to_dict())
OUT["representativeness"] = {f"{k[0]}|{k[1]}|vs_{k[2]}": v for k, v in verdict.items()}
conc = pd.DataFrame(conc_rows); conc.to_csv(os.path.join(FIG, "sample_concentration.csv"), index=False)
OUT["sample_concentration"] = conc.round(4).to_dict("records")

# ---------------------------------------------------------------- 4b. tiers vs each other (sub_first samples)
T = pd.concat([samples[(g, "sub_first")].assign(tier=g) for g in ["G1", "G2", "G3", "G4"]])
eff_rows = []
for c in KS_FEATS + ["win", "margin"]:
    groups = [T[T.tier == g][c].dropna() for g in ["G1", "G2", "G3", "G4"]]
    kw = stats.kruskal(*groups)
    n_tot = sum(len(x) for x in groups)
    eps2 = (kw.statistic - 4 + 1) / (n_tot - 4)
    row = dict(feature=c, kw_H=kw.statistic, kw_p=kw.pvalue, epsilon2=eps2,
               **{f"median_{g}": float(x.median()) for g, x in zip(["G1", "G2", "G3", "G4"], groups)},
               **{f"mean_{g}": float(x.mean()) for g, x in zip(["G1", "G2", "G3", "G4"], groups)})
    for a, b in (("G1", "G2"), ("G2", "G3"), ("G3", "G4"), ("G1", "G4")):
        xa, xb = T[T.tier == a][c].dropna(), T[T.tier == b][c].dropna()
        mw = stats.mannwhitneyu(xa, xb)
        row[f"mwu_p_{a}{b}"] = mw.pvalue
        row[f"cliffs_delta_{a}{b}"] = 2 * mw.statistic / (len(xa) * len(xb)) - 1
    eff_rows.append(row)
eff = pd.DataFrame(eff_rows)
eff["kw_p_holm"] = multipletests(eff.kw_p, method="holm")[1]
pw_cols = [c for c in eff.columns if c.startswith("mwu_p_")]
flat = multipletests(eff[pw_cols].values.ravel(), method="fdr_bh")[1].reshape(eff[pw_cols].shape)
for i, c in enumerate(pw_cols): eff[c + "_bh"] = flat[:, i]
eff.to_csv(os.path.join(FIG, "tier_feature_effect_sizes.csv"), index=False)
OUT["tier_contrasts"] = eff.round(5).to_dict("records")
# lineage mix across tiers (h48, h136): chi-square contingency on top lines of the pooled sample
lin_tests = {}
for col in ("stream_h48", "stream_h136"):
    top = T[col].value_counts().head(12).index
    tab = pd.crosstab(T[col].where(T[col].isin(top), "other"), T.tier)
    chi = stats.chi2_contingency(tab)
    lin_tests[col] = {"chi2": float(chi[0]), "p": float(chi[1]), "dof": int(chi[2]),
                      "cramers_v": float(np.sqrt(chi[0] / (tab.values.sum() * (min(tab.shape) - 1))))}
OUT["tier_lineage_mix_test"] = lin_tests

# ---------------------------------------------------------------- 5. lineage structure per tier (full window population)
lin_rows = []; lin_sum = {}
for col in ("stream_h48", "stream_h136"):
    for g in ["G1", "G2", "G3", "G4"]:
        P = popR[popR.tier == g]
        vc = P[col].value_counts(); vw = P.groupby(col).w_sub.sum().sort_values(ascending=False) / P.w_sub.sum()
        p = vc / vc.sum()
        lin_sum[f"{g}|{col}"] = {"seats": len(P), "distinct_lines": int(vc.size),
                                 "lines_with_ge_1pct": int((p >= 0.01).sum()),
                                 "top1_share": float(p.iloc[0]), "top5_share": float(p.head(5).sum()),
                                 "top1_share_subweighted": float(vw.iloc[0]), "top5_share_subweighted": float(vw.head(5).sum()),
                                 "eff_n_lines": float(1 / (p ** 2).sum()),
                                 "singleton_share": float((vc == 1).sum() / vc.sum())}
        for line in vc.head(10).index:
            d = P[P[col] == line]
            lin_rows.append(dict(cut=col, tier=g, line=line, seats=len(d), share=len(d) / len(P),
                                 share_subweighted=float(vw.get(line, 0)), n_subs=d["sub"].nunique(), n_teams=d.team.nunique(),
                                 win_rate=d.win.mean(), mean_margin=d.margin.mean(), mean_rating=d.rating.mean(),
                                 mean_bank=d.bank.mean(), mean_sub_latest=d.r_last.mean()))
lin = pd.DataFrame(lin_rows)
# where else does each G1 top line appear (share of that line's window seats per tier)
allc = popR.groupby(["stream_h136", "tier"]).size().unstack(fill_value=0)
lin.to_csv(os.path.join(FIG, "lineage_shares_per_tier.csv"), index=False)
allc2 = popR.groupby(["stream_h48", "tier"]).size().unstack(fill_value=0)
g1top = lin[(lin.tier == "G1")]
g1top = g1top.assign(tier_spread=[ (allc if r.cut == "stream_h136" else allc2).loc[r.line].to_dict() for r in g1top.itertuples()])
OUT["lineage_summary"] = lin_sum
OUT["lineage_top_G1"] = g1top.round(4).to_dict("records")
# team names for G1 top lines
teams = pd.read_csv(os.path.join(R, "teams.csv")).set_index("team_id").team_name
names = {}
for r in g1top[g1top.cut == "stream_h136"].head(6).itertuples():
    tm = popR[popR.stream_h136 == r.line].team.value_counts().head(5)
    names[r.line] = [(teams.get(t, str(t)), int(n)) for t, n in tm.items()]
OUT["lineage_top_G1_h136_teams"] = names

# save tier table for later steps
popR[["episode_id", "seat", "sub", "team", "tier", "tier_seat", "r_last", "rating", "opp_rating", "win", "margin", "bank",
      "stream_h48", "stream_h136", "day", "w_sub"]].to_parquet(os.path.join(D, "window_replay_seats.parquet"), index=False)
win[["episode_id", "seat", "sub", "team", "tier", "r_last", "rating", "opp_rating", "win", "margin", "bank", "opp_bank", "has_replay"]].to_parquet(
    os.path.join(D, "window_seats.parquet"), index=False)
json.dump(OUT, open(os.path.join(D, "results_audit.json"), "w"), indent=1, default=str)
print(json.dumps({k: OUT[k] for k in ("tiers",)}, indent=1, default=str)[:4000])
