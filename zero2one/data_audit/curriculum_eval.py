"""Curriculum (b) rating gap -> head-to-head win rate, and evaluation-side sample-size math.

Win-probability scale: fit P(win) = 1/(1+10^(-(r_i - r_j)/s)) on PUBLIC 1.32.7 games in the window, where r is the
seat's PRE-game rating = the rating_after of that submission's previous stored game (only when that game is <= 12 h
old, so we only use well-tracked submissions).  Also an empirical tier x tier win matrix using the submissions'
latest ratings.
"""
import os, json
import numpy as np, pandas as pd
from scipy import stats
from scipy.optimize import minimize_scalar
from scipy.stats import norm
D = os.path.dirname(os.path.abspath(__file__)); FIG = os.path.join(D, "figs")
OUT = {}
S = pd.read_parquet(os.path.join(D, "seats.parquet"))
S = S[(S["type"] == "EPISODE_TYPE_PUBLIC") & (S.state == "COMPLETED") & (S.t >= pd.Timestamp("2026-08-15 01:41", tz="UTC"))]
S = S.sort_values(["sub", "t"])
S["pre"] = S.groupby("sub").rating.shift(1)
S["n_prior"] = S.groupby("sub").cumcount()
S["pre_age_h"] = (S.t - S.groupby("sub").t.shift(1)).dt.total_seconds() / 3600
win = S[(S.day >= "2026-09-13") & (S.day <= "2026-09-22")]
a = win[win.seat == 0].set_index("episode_id"); b = win[win.seat == 1].set_index("episode_id")
E = a[["pre", "pre_age_h", "n_prior", "win", "bank", "margin", "rating"]].join(b[["pre", "pre_age_h", "n_prior", "bank", "rating"]], rsuffix="_1", how="inner")
E_all = E[(E.pre_age_h <= 12) & (E.pre_age_h_1 <= 12) & (E.win != 0.5)].dropna(subset=["pre", "pre_1"])
# converged submissions only: >= 30 earlier stored games (new submissions are under-rated while they climb,
# which makes large pre-game gaps anti-predictive: the low-rated side is often a strong newcomer)
E = E_all[(E_all.n_prior >= 30) & (E_all.n_prior_1 >= 30)]
d = (E.pre - E.pre_1).values; y = E.win.values
def nll(s):
    p = 1 / (1 + 10 ** (-d / s)); p = np.clip(p, 1e-9, 1 - 1e-9)
    return -np.sum(y * np.log(p) + (1 - y) * np.log(1 - p))
fit = minimize_scalar(nll, bounds=(50, 5000), method="bounded")
s_hat = float(fit.x)
# bootstrap CI for s
rng = np.random.default_rng(20260923); bs = []
for _ in range(300):
    ii = rng.integers(0, len(d), len(d)); dd, yy = d[ii], y[ii]
    f = minimize_scalar(lambda s: -np.sum(yy * np.log(np.clip(1 / (1 + 10 ** (-dd / s)), 1e-9, 1)) +
                                          (1 - yy) * np.log(np.clip(1 - 1 / (1 + 10 ** (-dd / s)), 1e-9, 1))),
                        bounds=(50, 5000), method="bounded"); bs.append(f.x)
OUT["elo_scale"] = {"games_used": int(len(d)), "s_hat": s_hat, "s_ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                    "note": "Elo convention has s=400; a larger s means rating gaps translate into smaller win-rate edges",
                    "abs_pre_gap_median": float(np.median(np.abs(d)))}
# calibration table
bins = [-2000, -300, -200, -100, -50, 0, 50, 100, 200, 300, 2000]
E["gap_bin"] = pd.cut(E.pre - E.pre_1, bins)
cal = E.groupby("gap_bin", observed=True).agg(games=("win", "size"), win_rate=("win", "mean"), gap_mean=("pre", lambda s: float(np.mean(s - E.loc[s.index, "pre_1"]))))
cal["pred"] = 1 / (1 + 10 ** (-cal.gap_mean / s_hat))
cal.to_csv(os.path.join(FIG, "winprob_calibration.csv"))
OUT["winprob_calibration"] = cal.reset_index().astype({"gap_bin": str}).round(4).to_dict("records")

# latest-rating gap fit (strength proxy; attenuated by rating noise)
Wl = pd.read_parquet(os.path.join(D, "window_seats.parquet"))
p0 = Wl[Wl.seat == 0].set_index("episode_id"); p1 = Wl[Wl.seat == 1].set_index("episode_id")
L = p0[["r_last", "win"]].join(p1[["r_last"]], rsuffix="_1", how="inner"); L = L[L.win != 0.5]
dl, yl = (L.r_last - L.r_last_1).values, L.win.values
fl = minimize_scalar(lambda s: -np.sum(yl * np.log(np.clip(1 / (1 + 10 ** (-dl / s)), 1e-9, 1)) +
                                       (1 - yl) * np.log(np.clip(1 - 1 / (1 + 10 ** (-dl / s)), 1e-9, 1))), bounds=(50, 5000), method="bounded")
OUT["elo_scale_latest_rating_gap"] = {"games_used": int(len(dl)), "s_hat": float(fl.x)}
OUT["elo_scale_all_pre_ratings_unfiltered_games"] = int(len(E_all))
# tiers (from audit) and adjacent-tier gaps
A = json.load(open(os.path.join(D, "results_audit.json")))
C = A["tiers"]["episodes_active_submissions_latest_rating"]
Wn = pd.read_parquet(os.path.join(D, "window_seats.parquet"))
last = Wn.drop_duplicates("sub")[["sub", "r_last", "tier"]]
cent = last.groupby("tier").r_last.median().to_dict()
def p_win(gap, s=s_hat): return 1 / (1 + 10 ** (-gap / s))
steps = {}
for hi, lo in (("G1", "G2"), ("G2", "G3"), ("G3", "G4"), ("G1", "G3"), ("G1", "G4")):
    gap = cent[hi] - cent[lo]
    steps[f"{lo}->{hi}"] = {"median_rating_lo": cent[lo], "median_rating_hi": cent[hi], "gap": gap,
                            "p_lower_beats_higher_fitted": p_win(-gap), "p_lower_beats_higher_elo400": p_win(-gap, 400)}
OUT["tier_medians_latest_rating"] = cent
OUT["tier_steps"] = steps
OUT["gap_for_30pct_win_fitted"] = float(s_hat * np.log10(7 / 3)); OUT["gap_for_30pct_win_elo400"] = float(400 * np.log10(7 / 3))
# empirical tier x tier win matrix (latest-rating tiers), window games
e2 = Wn.merge(Wn[["episode_id", "seat", "tier"]].rename(columns={"seat": "oseat", "tier": "otier"}), on="episode_id")
e2 = e2[e2.seat != e2.oseat]
m = e2[e2.win != 0.5].groupby(["tier", "otier"]).agg(games=("win", "size"), win_rate=("win", "mean")).reset_index()
m.to_csv(os.path.join(FIG, "tier_vs_tier_winrate.csv"), index=False)
OUT["tier_vs_tier_winrate"] = m.round(4).to_dict("records")
# finer ladder: 100-point rating bands of latest rating, win rate vs band+100/+200 (empirical)
e2["band"] = (e2.r_last // 100) * 100
e2 = e2.merge(Wn[["episode_id", "seat", "r_last"]].rename(columns={"seat": "oseat", "r_last": "or_last"}), on=["episode_id", "oseat"])
e2["gap_last"] = e2.or_last - e2.r_last
gg = e2[(e2.win != 0.5)].copy(); gg["gap_bin"] = pd.cut(gg.gap_last, [-2000, -400, -300, -200, -100, -50, 50, 100, 200, 300, 400, 2000])
emp = gg.groupby("gap_bin", observed=True).agg(games=("win", "size"), win_rate=("win", "mean")).reset_index()
emp.to_csv(os.path.join(FIG, "winrate_vs_latest_rating_gap.csv"), index=False)
OUT["winrate_vs_opponent_latest_gap"] = emp.astype({"gap_bin": str}).round(4).to_dict("records")

# ---------------- evaluation sample size
# close-rated games: |latest-rating gap| < 50 (window), overall and with both seats in G1
q0 = Wl[Wl.seat == 0].set_index("episode_id"); q1 = Wl[Wl.seat == 1].set_index("episode_id")
Q = q0[["r_last", "bank", "margin", "tier"]].join(q1[["r_last", "bank", "tier"]], rsuffix="_1", how="inner")
close = Q[(Q.r_last - Q.r_last_1).abs() < 50]
G1c = close[(close.tier == "G1") & (close.tier_1 == "G1")]
def rsd(x): return float((np.percentile(x, 75) - np.percentile(x, 25)) / 1.349)
ok = G1c[(G1c.bank > 20000) & (G1c.bank_1 > 20000)]
ev = {"close_games_all": int(len(close)), "close_games_G1": int(len(G1c)),
      "sd_bank_close_all": float(pd.concat([close.bank, close.bank_1]).std()),
      "sd_bank_close_G1": float(pd.concat([G1c.bank, G1c.bank_1]).std()),
      "sd_margin_close_all": float(close.margin.std()), "sd_margin_close_G1": float(G1c.margin.std()),
      "robust_sd_margin_close_G1_IQR": rsd(G1c.margin), "sd_margin_close_G1_no_crash_banks": float(ok.margin.std()),
      "sd_bank_close_G1_no_crash": float(pd.concat([ok.bank, ok.bank_1]).std()),
      "share_G1_close_games_with_a_bank_below_20k": float(1 - len(ok) / max(len(G1c), 1)),
      "median_abs_margin_close_G1": float(G1c.margin.abs().median()),
      "share_close_G1_decided_by_lt_1k": float((G1c.margin.abs() < 1000).mean())}
za, zb = norm.ppf(0.975), norm.ppf(0.8)
def n_h2h(p1): return ((za * 0.5 + zb * np.sqrt(p1 * (1 - p1))) / (p1 - 0.5)) ** 2
def n_two_prop(p0, p1):
    pb = (p0 + p1) / 2
    return ((za * np.sqrt(2 * pb * (1 - pb)) + zb * np.sqrt(p0 * (1 - p0) + p1 * (1 - p1))) / (p1 - p0)) ** 2
def n_mean(sd, delta): return ((za + zb) * sd / delta) ** 2
sdm = ev["sd_margin_close_G1_no_crash_banks"]
ev["winrate"] = {"h2h_A_vs_B_detect_55pct_games": n_h2h(0.55), "h2h_A_vs_B_detect_60pct_games": n_h2h(0.60),
                 "two_arms_vs_pool_+5pp_from_50_games_per_arm": n_two_prop(0.5, 0.55),
                 "two_arms_vs_pool_+10pp_from_50_games_per_arm": n_two_prop(0.5, 0.60)}
ev["margin"] = {"sd_used": sdm,
                "h2h_mean_margin_$1k_games": n_mean(sdm, 1000), "h2h_mean_margin_$2k_games": n_mean(sdm, 2000),
                "two_arms_vs_same_opponents_seeds_rho0_$1k_games_per_arm": 2 * n_mean(sdm, 1000),
                "two_arms_vs_same_opponents_seeds_rho0_$2k_games_per_arm": 2 * n_mean(sdm, 2000),
                "two_arms_paired_rho0.5_$1k_games_per_arm": 2 * (1 - 0.5) * n_mean(sdm, 1000),
                "two_arms_paired_rho0.5_$2k_games_per_arm": 2 * (1 - 0.5) * n_mean(sdm, 2000),
                "with_repo_sd_9000_h2h_$1k": n_mean(9000, 1000), "with_repo_sd_9000_h2h_$2k": n_mean(9000, 2000)}
OUT["eval_sample_size"] = ev
json.dump(OUT, open(os.path.join(D, "results_curriculum_eval.json"), "w"), indent=1, default=str)
print(json.dumps(OUT, indent=1, default=str)[:6000])
