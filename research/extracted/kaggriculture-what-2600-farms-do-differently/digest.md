*By [Georgy Mamarin](https://www.kaggle.com/georgymamarin)*

What the top of the board does, set against the middle of the same window: what they plant, when they
buy land, how big a crew they run. The page reruns on each new dataset version and reports which of
those the two bands actually differ on, which some days is none of them. Then the same comparison for
your own submission. Both read my
[Kaggriculture Episodes](https://www.kaggle.com/datasets/georgymamarin/kaggriculture-episodes)
dataset: every finished [Kaggriculture](https://www.kaggle.com/competitions/kaggriculture)
game in full, 720 turns, both players, every action.

[code cell 1: 460 lines]
```
# Reads the dataset in place: on Kaggle from /kaggle/input, locally from the staging copy.
import gc, glob, json, os, textwrap, warnings
from datetime import timezone

# DejaVu, matplotlib's default font, has no CJK glyphs: a Japanese team name prints a
# warning per glyph and draws as boxes. The names fall back below; the warning goes here.
warnings.filterwarnings("ignore", message="Glyph")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow.dataset as pads
from IPython.display import Markdown, display

hits = (glob.glob("/kaggle/input/**/episodes.csv", recursive=True)
        + glob.glob("../episodes_dataset/episodes.csv")
        + glob.glob("../../episodes_dataset/episodes.csv"))
if not hits:
    raise FileNotFoundError("episodes.csv not found — attach the kaggriculture-episodes dataset")
BASE = os.path.dirname(hits[0])

eps = pd.read_csv(f"{BASE}/episodes.csv")
agents = pd.read_csv(f"{BASE}/agents.csv")
try:                                                      # ids are unreadable on charts
    teams = pd.read_csv(f"{BASE}/teams.csv")
except FileNotFoundError:                                 # older dataset version
    teams = pd.DataFrame(columns=["team_id", "team_name", "ladder_score", "last_submission"])
NAME = dict(zip(teams.team_id, teams.team_name))
def name_of(tid):
    # Chart-safe names: Latin and Cyrillic render everywhere, anything past that
    # (CJK and friends) becomes "team <id>" instead of tofu boxes on the axis.
    n 
```

<a id="s11"></a>
## Your submission against the ladder

The part worth forking. Put your own submission id in the cell below and you get a personal
report: where your best game lands in the whole field, and how your strategy fingerprint
compares with the record holder's. That is one farm rather than the band above, and single names
at the top turn over within hours, so treat it as a reference point. Find
your id in `episodes.csv`, or leave the default to see the record holder's own report.

Before spending a real submission slot, dry-run the agent: destbreso's
[benchmark](https://www.kaggle.com/datasets/destbreso/kaggriculture-benchmark-matchups) replays
45k recorded pairings seed for seed, and his
[Measure Your Agent](https://www.kaggle.com/code/destbreso/kaggriculture-measure-your-agent)
harness tells you what a local score can and cannot promise about the ladder.

[code cell 3: 1 lines]
```
SUBMISSION_ID = int(top_subs.index[0])   # TWEAK THIS: your submission id from episodes.csv
```

[code cell 4: 79 lines]
```
mine = ladder_r[ladder_r.sub_0.eq(SUBMISSION_ID) | ladder_r.sub_1.eq(SUBMISSION_ID)].copy()
mine["my_seat"] = mine.sub_1.eq(SUBMISSION_ID).astype(int)
mine["my_bank"] = np.where(mine.my_seat.eq(1), mine.bank_1, mine.bank_0)
if mine.empty or mine.my_bank.isna().all():
    display(Markdown(
        f"No replayed ladder games for submission **{SUBMISSION_ID}** yet — the crawler usually "
        f"catches up within a day. Check the id in `episodes.csv` or try tomorrow."))
else:
    best = mine.loc[mine.my_bank.idxmax()]
    my_team = name_of(best.team_1 if best.my_seat else best.team_0)
    pct = (ladder.winner_bank < best.my_bank).mean()

    fig, ax = plt.subplots(figsize=(8.2, 3.4))
    ax.hist(ladder.winner_bank, bins=30, color="#D8D2C4")
    ax.axvline(best.my_bank, color=C_ACC, lw=2.6)
    ax.axvline(ladder.winner_bank.median(), color=C_MID, lw=1.6, ls="--")
    ax.annotate(f"you: {fmt(best.my_bank)}", xy=(best.my_bank, ax.get_ylim()[1] * .82),
                xytext=(8, 0), textcoords="offset points", color=C_ACC, weight="bold", fontsize=10)
    ax.annotate(f"median win {fmt(ladder.winner_bank.median())}",
                xy=(ladder.winner_bank.median(), ax.get_ylim()[1] * .55),
                xytext=(8, 0), textcoords="offset points", color=C_MID, fontsize=9.5)
    ax.set_xlabel("winner's final bank"); ax.set_ylabel("games")
    ax.xaxis.set_major_formatter(lambda v, _: f"{v/1000:.0f}k" if v else "0")
    ax.set_title(f"{my_team}: best game against the whole ladder")
  
```

[code cell 5: 56 lines]
```
# ---- poster: the ladder at a glance, opening the data half of the page ----
lb = teams.dropna(subset=["ladder_score"]).sort_values("ladder_score", ascending=False)
if lb.empty:      # no names yet: fall back to the ratings recorded in the episodes
    last = agents.sort_values("episode_id").groupby("team_id").rating_after.last()
    lb = (last.reset_index().rename(columns={"rating_after": "ladder_score"})
          .assign(team_name=lambda d: d.team_id.map(lambda t: f"team {t}"))
          .sort_values("ladder_score", ascending=False))
top5 = lb.head(5).iloc[::-1]
ladder0 = eps[eps.type.eq("EPISODE_TYPE_PUBLIC") & eps.state.eq("COMPLETED")]
banks = ladder0[["bank_0", "bank_1"]].max(axis=1).dropna()

fig = plt.figure(figsize=(8.2, 3.9))
fig.patch.set_facecolor("#FBF7EE")
fig.text(.015, .97, "The Kaggriculture ladder", fontsize=19, weight="bold",
         color="#2B241D", va="top")
fig.text(.015, .845,
         f"{len(eps):,} episodes · {len(replay_ids):,} full replays · {len(lb):,} teams",
         fontsize=11, color="#6B6152", va="top")
# The snapshot date is the one number readers must not miss: give it its own badge.
_lag_h = (pd.Timestamp.now(tz="UTC") - AS_OF).total_seconds() / 3600
_badge = "#00795F" if _lag_h <= 24 else "#B84A00"
fig.text(.985, .975, f"data through {AS_OF:%b %d · %H:%M UTC}",
         fontsize=12, weight="bold", color="white", ha="right", va="top",
         bbox=dict(boxstyle="round,pad=0.45", facecolor=_badge, edgecolor="none"))
gs = fig.add_gridspec
```

**A live report, not a snapshot.** It re-runs on a schedule with the dataset, so every number in
the text below is computed at run time. Come back tomorrow and the ladder you see will be the
ladder as it is tomorrow.

<div class="alert alert-info" style="border-left: 5px solid #2196f3; padding: 12px 16px; border-radius: 4px;">
<b>Two companions, two jobs.</b> This one is about the data and the state of the ladder. My guide
<a href="https://www.kaggle.com/code/georgymamarin/kaggriculture-visualized-what-every-crop-pays">Kaggriculture, Visualized</a>
is about the game itself, with every rule and price curve drawn out plus a starter bot. Read that
one first if the mechanics are new to you.
</div>

**Built on this data, by the community:** a [replayable benchmark](https://www.kaggle.com/datasets/destbreso/kaggriculture-benchmark-matchups) of 45k matchups with resolved seeds (CC0), an [agent-testing harness](https://www.kaggle.com/code/destbreso/kaggriculture-measure-your-agent), a [no-OOM replay reader](https://www.kaggle.com/code/lucashmateo/kaggriculture-replays-no-oom-3-dataframes), and a [research series on openings, lineages and noise](https://www.kaggle.com/code/destbreso/everyone-is-playing-the-same-opening) — by destbreso and Lucas Mateo. The dataset stopped being a solo project; this page stays its daily pulse.

### In this notebook

Above: the fresh cohort at the top of the board and your own submission against it. Below,
the season in depth.

**Part I — the data.** Know what you are standing on before you quote it.
- [1. What is in the dataset today](#s1) — size, coverage, and how fast the corpus grows

**Part II — the ladder.** Nine views of the same 30-day season, from every recorded win down to pure luck.
- [2. The ladder right now](#s2) — every recorded win on one chart
- [3. The shape of a big game](#s3) — top coin curves against a median game
- [4. Strategy fingerprints](#s4) — crew, land and crops: leaders vs the mid-ladder
- [5. What separates a big bank from a small one](#s5) — measured across every replayed game
- [6. The market they create together](#s6) — every episode's price swings, then one game up close
- [7. How fast the bar is moving](#s7) — the meta clock, and who moved this week
- [8. Who beats whom](#s8) — head-to-head win rates the ratings hide
- [9. How much of this is luck](#s9) — same bot, different games
- [10. The openings they share](#s10) — byte-identical lines, measured by stream hashes

Plus [the honest caveats](#s12) behind every chart, and the [takeaways](#s13).

**Want this for your own bot?** Fork, put your submission id in the one marked line near the top,
and the personal report reruns for you: where your best game lands in the whole field, and how
your strategy compares with the record holder's.

# Part I — the data

<a id="s1"></a>
## 1. What is in the dataset today

Before the strategy talk, the shape of the data itself: how much of the ladder is captured, how
deep the replay coverage goes, and how fast the corpus grows. Column-level docs live on the
[dataset page](https://www.kaggle.com/datasets/georgymamarin/kaggriculture-episodes).

[code cell 9: 36 lines]
```
n_subs = pd.unique(agents.submission_id).size
n_teams = pd.unique(agents.team_id).size
val_share = eps.type.eq("EPISODE_TYPE_VALIDATION").mean()
cover = eps.has_replay.mean()
span_h = (eps.end.max() - eps.end.min()).total_seconds() / 3600

summary = pd.DataFrame({
    "metric": ["episodes", "with full replay", "ladder games", "validation (self-play)",
               "submissions seen", "teams seen", "ladder time covered"],
    "value": [f"{len(eps):,}", f"{len(replay_ids):,} ({cover:.0%})", f"{len(ladder):,}",
              f"{eps.type.eq('EPISODE_TYPE_VALIDATION').sum():,} ({val_share:.0%})",
              f"{n_subs:,}", f"{n_teams:,}",
              f"{span_h:.0f} hours" if span_h <= 72 else f"{span_h / 24:.1f} days"],
})
display(summary.style.hide(axis="index").set_properties(**{"font-size": "13px"})
        .set_table_styles([{"selector": "th", "props": [("font-size", "13px")]}]))

fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.2))
freq1, width1, unit1 = ("1h", 0.032, "hour") if span_h <= 72 else ("1D", 0.8, "day")
by_t = eps.set_index("end").resample(freq1).size()
axes[0].bar(by_t.index, by_t.values, width=width1, color=C_ACC)
axes[0].set_title(f"Episodes recorded per {unit1}"); axes[0].set_ylabel("episodes")
axes[0].xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b %d\n%H:%M"))
axes[0].tick_params(axis="x", labelsize=8)
games = agents.groupby("submission_id").size().sort_values(ascending=False)
axes[1].hist(games.values, bins=min(20, games.nunique()), col
```

[code cell 10: 17 lines]
```
# Copy-paste loaders — the three safe ways into this dataset, smallest first.
# (1) Most questions never need the replays: episode_features.csv is one row
#     per seat with the behavior already parsed out.
# (2) One game out of the multi-GB corpus, without loading the rest. The glob
#     matches both layouts: the single replays.parquet and the monthly shards
#     (replays_2026-08.parquet, ...) that replace it.
demo_id = int(ladder_r.episode_id.iloc[-1])
demo_row = pads.dataset(sorted(glob.glob(f"{BASE}/replays*.parquet"))).scanner(
    filter=pads.field("episode_id") == demo_id,
    columns=["replay_json"], batch_size=1).head(1)
demo = json.loads(demo_row.column("replay_json")[0].as_py())
print(f"episode {demo_id}: {len(demo['steps'])} steps, "
      f"{len(demo_row.column('replay_json')[0].as_py()) / 1e6:.0f} MB of JSON, "
      f"loaded alone in a fraction of a second")
del demo, demo_row; gc.collect()
# (3) A whole month as a plain DataFrame, once the monthly shards land:
#     pd.read_parquet(f"{BASE}/replays_2026-08.parquet")
```

# Part II — the ladder

<a id="s2"></a>
## 2. The ladder right now

Winners' final banks across the recorded ladder games, one dot per episode. The spread is the
story of this competition: the same board and the same rules produce farms that differ by an
order of magnitude.

[code cell 13: 19 lines]
```
fig, ax = plt.subplots(figsize=(8.2, 3.6))
ax.scatter(ladder.end, ladder.winner_bank, s=22, alpha=.55, color=C_ACC, edgecolors="white", lw=.4)
rec = ladder.loc[ladder.winner_bank.idxmax()]
ax.annotate(f"record: {fmt(rec.winner_bank)}", xy=(rec.end, rec.winner_bank),
            xytext=(10, 6), textcoords="offset points", fontsize=10, weight="bold", color=C_TOP)
ax.set_yscale("log")
ax.yaxis.set_major_formatter(lambda v, _: f"{v/1000:g}k" if v >= 1000 else f"{v:g}")
ax.set_ylabel("winner's final bank (log)"); ax.set_xlabel("episode end time (UTC)")
ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b %d\n%H:%M"))
ax.tick_params(axis="x", labelsize=8.5)
ax.set_title(f"Same rules, {ladder.winner_bank.max() / ladder.winner_bank.median():.0f}x spread "
             "between median and record")
plt.tight_layout(); plt.show()

q = ladder.winner_bank.quantile([.25, .5, .9])
display(Markdown(
    f"The winner's bank across recorded games: **{fmt(q[.25])}** at p25, **{fmt(q[.5])}** median, "
    f"**{fmt(q[.9])}** at p90. The record of **{fmt(rec.winner_bank)}** is "
    f"**{rec.winner_bank / q[.5]:.1f}×** the median win; section 6 tracks how fast that gap moves."))
```

<a id="s3"></a>
## 3. The shape of a big game

Coin curves of the biggest wins on record against a median game. Top games share a silhouette:
the bank stays near zero deep into the season while everything is reinvested, then compounding
takes over once the farm is built.

[code cell 15: 35 lines]
```
def money_curve(row, seat):
    return [s[0]["observation"]["farms"][seat]["money"]
            for s in load_replay(row.episode_id)["steps"]]

fig, ax = plt.subplots(figsize=(8.2, 3.8))
elbows, seen_teams = {}, set()
for rank, (sub, bank) in enumerate(top_subs.items()):
    row = ladder_r[ladder_r.winner_sub.eq(sub) & ladder_r.winner_bank.eq(bank)].iloc[0]
    seat = 0 if row.bank_0 >= row.bank_1 else 1
    money = money_curve(row, seat)
    team = name_of(row.team_1 if seat else row.team_0)
    if team in seen_teams:                     # same team, another submission
        team = f"{team} (2nd sub)"
    seen_teams.add(team)
    ax.plot(money, lw=2.4, color=[C_TOP, C_ACC, C_LOW][rank],
            label=f"{team}: {fmt(bank)}")
    cross = next((t for t, m in enumerate(money) if m > bank * .1), None)
    if cross is not None:
        elbows[rank + 1] = cross // 24

med_row = ladder_r.loc[(ladder_r.winner_bank - ladder_r.winner_bank.median()).abs().idxmin()]
seat = 0 if med_row.bank_0 >= med_row.bank_1 else 1
ax.plot(money_curve(med_row, seat), lw=2.4, color=C_MID, ls="--",
        label=f"a median game: {fmt(med_row.winner_bank)}")
ax.legend(fontsize=9.5, frameon=False, loc="upper left")
ax.set_xlabel("turn (24 turns = one in-game day)"); ax.set_ylabel("coins in the bank")
ax.yaxis.set_major_formatter(lambda v, _: f"{v/1000:.0f}k" if v else "0")
ax.set_title("Top farms stay near zero, then compound")
plt.tight_layout(); plt.show()

if elbows:
    display(Markdown(
        
```

<a id="s4"></a>
## 4. Strategy fingerprints

Replays store actions, not just scores, so you can compare bots by what they do. Those
fingerprints already sit in `episode_features.csv`, one row per seat for every episode that has
a replay, and section 1 prints how deep that coverage runs, so you rarely need to open a replay
yourself. The cell below is the method behind the crew, land and crop columns; bank shape and
prices get measured in sections 3 and 6. It stays open on purpose: it defines exactly what
`peak_crew` or `first_land_day` mean, and it is where to start if you want to measure something
I did not. Leaders against the middle of the ladder:

[code cell 17: 19 lines]
```
def fingerprint(episode_id, seat):
    # Hires are read from the farm state (hires_today), not from submitted HIRE
    # orders — bots keep sending orders the engine rejects once money runs short.
    crops, first_land, peak_crew, hires_by_day = {}, None, 0, {}
    for t, step in enumerate(load_replay(episode_id)["steps"]):
        farm = step[0]["observation"]["farms"][seat]
        day = t // 24
        hires_by_day[day] = max(hires_by_day.get(day, 0), farm["hires_today"])
        peak_crew = max(peak_crew, len(farm["hands"]))
        a = step[seat].get("action") or {}
        for order in (a.get("market") or []):
            if isinstance(order, list) and order and order[0] == "BUY_LAND" and first_land is None:
                first_land = day
        for unit in [a.get("farmer") or []] + list(a.get("hands") or []):
            if isinstance(unit, list) and unit and unit[0] == "PLANT" and len(unit) > 1:
                crops[unit[1]] = crops.get(unit[1], 0) + 1
    return {"hires / day": sum(hires_by_day.values()) / max(1, len(hires_by_day)),  # CSV: total_hires
            "peak crew": peak_crew,
            "first land (day)": first_land, "plants": crops}
```

[code cell 18: 38 lines]
```
rows = []
for rank, (sub, bank) in enumerate(top_subs.items()):
    row = ladder_r[ladder_r.winner_sub.eq(sub) & ladder_r.winner_bank.eq(bank)].iloc[0]
    seat = 0 if row.bank_0 >= row.bank_1 else 1
    rows.append({"who": name_of(row.team_1 if seat else row.team_0), "bank": bank,
                 **(fingerprint_row(row.episode_id, seat) or {})})
mid_pool = ladder_r[ladder_r.winner_bank.between(*ladder_r.winner_bank.quantile([.45, .55]))]
mid = (mid_pool.iloc[0] if len(mid_pool)
       else ladder_r.loc[(ladder_r.winner_bank - ladder_r.winner_bank.median()).abs().idxmin()])
seat = 0 if mid.bank_0 >= mid.bank_1 else 1
rows.append({"who": f"{name_of(mid.team_1 if seat else mid.team_0)} (mid-ladder)",
             "bank": mid.winner_bank, **(fingerprint_row(mid.episode_id, seat) or {})})

fp = pd.DataFrame(rows)
fp["top crop"] = fp.plants.map(lambda d: max(d, key=d.get).title() if d else "—")
fp["plantings"] = fp.plants.map(lambda d: sum(d.values()))
display(fp[["who", "bank", "hires / day", "peak crew", "first land (day)",
            "plantings", "top crop"]]
        .style.hide(axis="index")
        .format({"bank": "{:,.0f}", "hires / day": "{:.1f}", "first land (day)": "{:.0f}"},
                na_rep="—")
        .set_properties(**{"font-size": "13px"})
        .set_table_styles([{"selector": "th", "props": [("font-size", "13px")]}]))

lead, base = fp.iloc[0], fp.iloc[-1]
crops_top = [c for c in fp["top crop"][:3].tolist() if c != "—"]
uniq_crops = list(dict.fromkeys(cro
```

<a id="s5"></a>
## 5. What actually separates a big bank from a small one

The fingerprints above describe single games. With `episode_features.csv` we can ask the blunter
question across every replayed episode at once: which measurable choices track a large final
bank, and which ones only feel important?

One column is deliberately missing from this chart. `elbow_day` correlates with the bank at 0.8,
but it is derived from the bank itself (the day a farm crosses a tenth of its own final total),
so a weak farm crosses its small tenth early and a strong one crosses late. That is arithmetic,
not strategy, and including it would be the most confident wrong claim in this notebook.

[code cell 20: 34 lines]
```
feat = pd.read_csv(f"{BASE}/episode_features.csv")
feat = feat[feat.final_money > 0]
CROP_COLS = [c for c in feat.columns
             if c.startswith("plants_") and c[7:].upper() in
             {"CARROT", "MELON", "STRAWBERRY", "TOMATO", "WHEAT"}]
CAND = ["total_hires", "peak_crew", "tiles_planted", "first_land_day"] + CROP_COLS
rho = (feat[CAND + ["final_money"]].corr(method="spearman")["final_money"]
       .drop("final_money").sort_values())

fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.8))
labels = [c.replace("plants_", "plants: ").replace("_", " ") for c in rho.index]
axes[0].barh(range(len(rho)), rho.values, height=.7,
             color=[C_TOP if v > 0 else C_LOW for v in rho.values])
axes[0].set_yticks(range(len(rho)), labels, fontsize=9)
axes[0].axvline(0, color="#2B241D", lw=.8)
axes[0].set_xlabel("rank correlation with final bank")
axes[0].set_title(f"Labor leads, land timing does not (n={len(feat):,})")

top_feat = rho.abs().idxmax()
axes[1].scatter(feat[top_feat], feat.final_money, s=9, alpha=.25, color=C_ACC, edgecolors="none")
axes[1].set_xlabel(top_feat.replace("_", " ")); axes[1].set_ylabel("final bank")
axes[1].yaxis.set_major_formatter(lambda v, _: f"{v/1000:.0f}k" if v else "0")
axes[1].set_title(f"{top_feat.replace('_', ' ').title()} against the outcome")
plt.tight_layout(); plt.show()

best_crop = max(CROP_COLS, key=lambda c: rho.get(c, 0))
display(Markdown(
    f"Across **{len(feat):,}** seats the strongest signal is **{top_feat.replace('_', ' ')}**
```

<a id="s6"></a>
## 6. The market they create together

Prices are shared between the two players of an episode, and `episode_features.csv` records
every episode's low and high for all nine goods. First the whole corpus, so you can see which
markets actually move; then one game up close, where you can watch them being moved.

[code cell 22: 48 lines]
```
feat_p = pd.read_csv(f"{BASE}/episode_features.csv").drop_duplicates("episode_id")
feat_p = feat_p[feat_p.episode_id.isin(ladder_r.episode_id)]
# Cells share one namespace: a bare `rows` here once shadowed section 4's `rows`
# that the personal report reads, so everything local to this cell wears mkt_.
mkt_goods = sorted({c[len("price_"):-len("_min")] for c in feat_p.columns
                    if c.startswith("price_") and c.endswith("_min")})
# The market opens with the same order book every episode, so turn 0 of any replay
# supplies the opening price for every good.
base_replay = load_replay(ladder_r.episode_id.iloc[-1])
mkt_base = {g.lower(): p for g, p in
            base_replay["steps"][0][0]["observation"]["market"]["prices"].items()}
del base_replay; gc.collect()

mkt_rows = []
for g in mkt_goods:
    mkt_lo = feat_p[f"price_{g}_min"] / mkt_base[g]
    mkt_hi = feat_p[f"price_{g}_max"] / mkt_base[g]
    mkt_rows.append({"good": g, "lo_p10": mkt_lo.quantile(.1), "lo_med": mkt_lo.median(),
                     "hi_med": mkt_hi.median(), "hi_p90": mkt_hi.quantile(.9)})
mkt_rng = pd.DataFrame(mkt_rows)
mkt_rng["band"] = mkt_rng.hi_med - mkt_rng.lo_med    # width of the median episode's price ride
mkt_rng = mkt_rng.sort_values("band")

fig, ax = plt.subplots(figsize=(8.2, 4.2))
mkt_y = np.arange(len(mkt_rng))
ax.hlines(mkt_y, mkt_rng.lo_p10, mkt_rng.hi_p90, color=C_ACC, lw=2, alpha=.35)
ax.hlines(mkt_y, mkt_rng.lo_med, mkt_rng.hi_med, color=C_ACC, lw=7)
ax.axvline(1, colo
```

[code cell 23: 23 lines]
```
rec_r = ladder_r.loc[ladder_r.winner_bank.idxmax()]
replay = load_replay(rec_r.episode_id)
prices = {p: [s[0]["observation"]["market"]["prices"][p] for s in replay["steps"]]
          for p in ("MELON", "WHEAT")}
base_price = {p: prices[p][0] for p in prices}

fig, ax = plt.subplots(figsize=(8.2, 3.4))
for p, c in (("MELON", C_TOP), ("WHEAT", C_MID)):
    ax.plot(prices[p], lw=2.2, color=c, label=f"{p.title()} price")
    ax.axhline(base_price[p], color=c, lw=.9, ls=":")
ax.set_xlabel("turn"); ax.set_ylabel("market price")
ax.set_title(f"Prices inside the biggest replayed game (episode {rec_r.episode_id})")
ax.legend(fontsize=9.5, frameon=False); plt.tight_layout(); plt.show()

mel, whe = prices["MELON"], prices["WHEAT"]
wheat_note = (" Wheat climbing that far above base usually means animal farms buying feed faster "
              "than the town supplies it." if max(whe) > base_price["WHEAT"] * 1.4 else "")
display(Markdown(
    f"In this game melon starts at **{base_price['MELON']}**, bottoms at **{min(mel)}** and peaks "
    f"at **{max(mel)}**, a swing of {(max(mel) - min(mel)) / base_price['MELON']:.0%} of its base "
    f"price. Wheat runs **{min(whe)}–{max(whe)}** against a base of **{base_price['WHEAT']}**."
    f"{wheat_note} Both lines are a strategy log: you can see when a farm dumps and when it "
    f"trickles."))
```

[code cell 24: 50 lines]
```
# The Aug 15 balance patch (engine 1.32.7: hinge scarcity pricing for tomato,
# carrot and egg), measured instead of announced. Self-unlocking: episode_features
# gains engine_version as the nightly backfill re-parses the corpus; until it
# covers enough of both sides of the patch, this stays a status line.
eng_f = pd.read_csv(f"{BASE}/episode_features.csv")
eng_ok = ("engine_version" in eng_f.columns
          and eng_f.engine_version.notna().mean() >= 0.95
          and eng_f.episode_id.isin(ladder_r.episode_id).any())
if not eng_ok:
    fill = (eng_f.engine_version.notna().mean()
            if "engine_version" in eng_f.columns else 0.0)
    display(Markdown(
        f"`engine_version` currently covers **{fill:.0%}** of feature rows; the "
        f"before/after chart of the Aug 15 balance patch computes itself once "
        f"coverage passes 95%."))
else:
    eng = eng_f.drop_duplicates("episode_id")
    eng = eng[eng.episode_id.isin(set(ladder_r.episode_id))].copy()
    eng["post"] = eng.engine_version.astype(str) >= "1.32.7"
    if eng.post.nunique() < 2 or eng.post.mean() in (0.0, 1.0):
        display(Markdown("The corpus does not yet hold games on both sides of the patch."))
    else:
        eng_goods = sorted({c[len("price_"):-4] for c in eng.columns
                            if c.startswith("price_") and c.endswith("_max")})
        eng_rows = []
        for g_ in eng_goods:
            for post, grp in eng.groupby("post"):
                eng_rows.append({"goo
```

<a id="s7"></a>
## 7. How fast the bar is moving

The number every competitor wants: how much the ladder improves while you sleep. Median
winning bank per time slice, against the record so far. Skip a few days and this is the gap you
come back to. Below the clock: the movers, teams whose rating travelled furthest over the last
seven days of recorded games.

[code cell 26: 63 lines]
```
# Prefer the collector's own daily series: it covers the whole history at one row per
# day, while re-deriving it here would re-scan every episode on every run.
DAILY = None
try:
    DAILY = pd.read_csv(f"{BASE}/daily_stats.csv", parse_dates=["date"])
except FileNotFoundError:
    pass

span_d6 = (ladder.end.max() - ladder.end.min()).total_seconds() / 86400
freq6 = "2h" if span_d6 <= 3 else ("6h" if span_d6 <= 10 else ("1D" if span_d6 <= 30 else "3D"))
by_h = (ladder.set_index("end").winner_bank
        .resample(freq6).agg(["median", "max", "count"]).dropna())
solid = by_h[by_h["count"] >= 2]
if len(solid) >= 4:
    by_h = solid
fig, ax = plt.subplots(figsize=(8.2, 3.4))
if DAILY is not None and len(DAILY) >= 3:
    # Order-statistic 95% CI for each day's median, computed from the raw games:
    # rank n/2 +- 1.96*sqrt(n)/2. No distribution assumed, which matters for a
    # quantity with a heavy right tail.
    ci_rows = []
    for ci_day, ci_g in ladder.set_index("end").winner_bank.resample("1D"):
        ci_v = ci_g.sort_values().to_numpy()
        ci_n = len(ci_v)
        if ci_n >= 8:
            ci_lo = int(max(0, np.floor(ci_n / 2 - 1.96 * np.sqrt(ci_n) / 2)))
            ci_hi = int(min(ci_n - 1, np.ceil(ci_n / 2 + 1.96 * np.sqrt(ci_n) / 2)))
            ci_rows.append((ci_day, ci_v[ci_lo], ci_v[ci_hi]))
    if ci_rows:
        ci_d, ci_l, ci_h = zip(*ci_rows)
        ax.fill_between(ci_d, ci_l, ci_h, color=C_ACC, alpha=.18, lw=0,
                        label="95% C
```

[code cell 27: 43 lines]
```
# The week's movers: each team's latest rating against its own rating seven days
# earlier. Thresholds keep one lucky game from reading as a move. All names local
# to this cell wear wk_ (cells share one namespace; see the v27 lesson).
wk_ag = (agents.dropna(subset=["rating_after", "team_id"])
         .merge(ladder[["episode_id", "end"]], on="episode_id")
         .sort_values("end"))
wk_now = wk_ag.end.max()
wk_cur = wk_ag[wk_ag.end > wk_now - pd.Timedelta(days=7)]
wk_old = wk_ag[(wk_ag.end <= wk_now - pd.Timedelta(days=7))
               & (wk_ag.end > wk_now - pd.Timedelta(days=14))]
wk_a = wk_cur.groupby("team_id").agg(games=("rating_after", "size"),
                                     r_new=("rating_after", "last"))
wk_b = wk_old.groupby("team_id").agg(prior=("rating_after", "size"),
                                     r_old=("rating_after", "last"))
wk_m = wk_a.join(wk_b, how="inner")
wk_m = wk_m[(wk_m.games >= 5) & (wk_m.prior >= 3)]
wk_m["delta"] = wk_m.r_new - wk_m.r_old

if len(wk_m) < 4:
    display(Markdown("The corpus does not yet hold two comparable weeks of games for enough "
                     "teams; this chart will appear as the archive grows."))
else:
    wk_show = pd.concat([wk_m.nlargest(5, "delta"), wk_m.nsmallest(3, "delta")])
    wk_show = wk_show[~wk_show.index.duplicated()].sort_values("delta")
    fig, ax = plt.subplots(figsize=(8.2, .52 * len(wk_show) + 1.2))
    wk_c = [C_TOP if d > 0 else C_MID for d in wk_show.delta]
    ax.barh([name_of(t)
```

<a id="s8"></a>
## 8. Who beats whom

Ratings compress everything into one number, and that hides the interesting part: matchups don't
have to be transitive. Head-to-head win rates between the busiest teams; read a row as the row
team's share of wins against the column team.

[code cell 29: 44 lines]
```
lad = ladder.dropna(subset=["team_0", "team_1"]).copy()
lad["winner_team"] = np.where(lad.bank_0 >= lad.bank_1, lad.team_0, lad.team_1)
busiest = (pd.concat([lad.team_0, lad.team_1]).value_counts().head(6).index.tolist())
mat = pd.DataFrame(np.nan, index=busiest, columns=busiest, dtype=float)
counts = pd.DataFrame(0, index=busiest, columns=busiest, dtype=int)
for a in busiest:
    for b in busiest:
        if a == b:
            continue
        games = lad[((lad.team_0.eq(a) & lad.team_1.eq(b))
                     | (lad.team_0.eq(b) & lad.team_1.eq(a)))]
        if len(games):
            mat.loc[a, b] = games.winner_team.eq(a).mean()
            counts.loc[a, b] = len(games)

labels = [(n if len(n) <= 20 else n[:19] + "…")
          for n in (name_of(t) for t in busiest)]
fig, ax = plt.subplots(figsize=(7.4, 5.4))
im = ax.imshow(mat.values, cmap="PuOr", vmin=0, vmax=1)
ax.set_xticks(range(len(busiest)), labels, rotation=45, ha="right", fontsize=9)
ax.set_yticks(range(len(busiest)), labels, fontsize=9)
for i in range(len(busiest)):
    for j in range(len(busiest)):
        v, n = mat.values[i, j], counts.values[i, j]
        if not np.isnan(v):
            ax.text(j, i, f"{v:.0%}\n({n})", ha="center", va="center", fontsize=8.5,
                    color="white" if abs(v - .5) > .3 else "#2B241D")
        elif i != j:
            ax.text(j, i, "—", ha="center", va="center", fontsize=9, color="#8A8073")
ax.set_title("Win rate, row team vs column team (games)")
ax.grid(False)
```

<a id="s9"></a>
## 9. How much of this is luck

Same bot, different games: how wide is its spread? This decides how many submissions you need
before believing a result, and whether that one great game was skill or a lucky matchup.
A useful floor for reading the chart: in
[destbreso's weed-spawn ablation](https://www.kaggle.com/code/destbreso/kaggriculture-the-free-experiment-you-already-ran)
the environment alone moves a bank by a few hundred coins, while the spreads below run in the
tens of thousands. Nearly everything you see here is matchup, not dice.

[code cell 31: 26 lines]
```
per_sub = (agents[agents.episode_id.isin(ladder.episode_id)]
           .groupby("submission_id").final_bank
           .agg(["count", "median", "std"]).query("count >= 4 and median > 0").dropna())
per_sub["cv"] = per_sub["std"] / per_sub["median"]
fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.3))
axes[0].scatter(per_sub["median"], per_sub["cv"], s=30, alpha=.65, color=C_LOW,
                edgecolors="white", lw=.5)
axes[0].set_xlabel("median bank"); axes[0].set_ylabel("spread / median")
axes[0].xaxis.set_major_formatter(lambda v, _: f"{v/1000:.0f}k" if v else "0")
axes[0].set_title("Do stronger bots score more consistently?")
top_ids = per_sub["median"].nlargest(6).index
lad_agents = agents[agents.episode_id.isin(ladder.episode_id)]
box = [lad_agents[lad_agents.submission_id.eq(s)].final_bank.values for s in top_ids]
axes[1].boxplot(box, widths=.6)
axes[1].set_xticks(range(1, len(top_ids) + 1),
                   [name_of(lad_agents[lad_agents.submission_id.eq(s)].team_id.iloc[0])[:9]
                    + f"\n…{str(s)[-3:]}" for s in top_ids])
axes[1].set_title("Spread of the top six"); axes[1].set_ylabel("final bank")
axes[1].yaxis.set_major_formatter(lambda v, _: f"{v/1000:.0f}k" if v else "0")
axes[1].tick_params(axis="x", rotation=45, labelsize=8)
plt.tight_layout(); plt.show()

display(Markdown(
    f"Across submissions with at least four games, the typical spread is "
    f"**{per_sub.cv.median():.0%}** of the median bank (worst: **{per_sub.cv.max():.0%}**). "
    
```

<a id="s10"></a>
## 10. The openings they share

Two seats with the same stream hash at turn N played byte-identical actions for N straight
turns: a shared opening is an observation, not a similarity threshold. Two honest limits, both
measured by destbreso: nothing observable differs before turn 48, so early agreement is partly
the engine's determinism rather than evidence of copying, and the full-game hash identifies the
episode rather than the agent, so lineage lives in the prefixes, never in `stream_h719` alone.
The hashes ship in the dataset's `stream_hashes.csv`, proposed by
[destbreso in the dataset discussion](https://www.kaggle.com/datasets/georgymamarin/kaggriculture-episodes/discussion/734833).
This section computes itself only when stream-hash coverage clears its 95% gate: on a partial,
time-ordered slice these rates would measure the nightly hash backfill, not the meta.

[code cell 33: 63 lines]
```
# Self-unlocking: one status line until stream-hash coverage passes the gate.
op_hits = glob.glob(f"{BASE}/stream_hashes.csv")
op_h = pd.read_csv(op_hits[0]) if op_hits else pd.DataFrame(columns=["episode_id", "seat"])
OP_GATE = 0.95
op_cov = op_h.episode_id.nunique() / max(1, len(eps))
if op_cov < OP_GATE:
    display(Markdown(
        f"`stream_hashes.csv` covers **{op_h.episode_id.nunique():,}** of **{len(eps):,}** stored "
        f"episodes so far (**{op_cov:.0%}**). The collector backfills more every night; these "
        f"charts appear on the first scheduled run after coverage passes {OP_GATE:.0%}."))
else:
    op_pref = [24, 100, 200, 400, 719]
    op = op_h[op_h.episode_id.isin(set(ladder_r.episode_id))].merge(
        ladder_r[["episode_id", "team_0", "team_1", "end"]], on="episode_id", how="left")
    op["team"] = np.where(op.seat.eq(0), op.team_0, op.team_1)

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(8.2, 3.4))
    op_share = []
    for op_t in op_pref:
        op_col = op[f"stream_h{op_t}"].dropna()
        op_vc = op_col.value_counts()
        op_share.append((op_col.map(op_vc) > 1).mean())
    axL.plot(op_pref, [s * 100 for s in op_share], marker="o", lw=2.2, color=C_ACC)
    axL.set_xlabel("agree for this many turns"); axL.set_ylabel("% of seats in a shared line")
    axL.set_title("How long the field stays identical")

    op_top = op.stream_h100.value_counts().idxmax()
    op_hit = op.assign(hit=op.stream_h100.eq(op_top))
    op_day = op_hit.set_in
```

<a id="s12"></a>
## Before you quote these numbers

The honest edges of this snapshot, so the charts above don't overclaim:

- Fingerprints read one best game per submission: a sketch of a strategy at its peak, not its
  average behavior.
- The corpus is a crawl, not a census. Episodes are discovered through pairings, so a brand-new
  submission can lag behind the ladder by a few hours; section 1 prints the exact replay
  coverage.
- Head-to-head cells stand on a handful of games. The count is printed inside every cell; a 100%
  built on two games is an anecdote, not a verdict.
- Spread estimates use submissions with four or more games each, a modest per-bot sample even
  on a mature ladder; treat them as order-of-magnitude.
- Daily time series mix real change with crawler drift: which submissions the crawl services
  shifts over time, so day-over-day movement partly reflects the lens, not the ladder
  (destbreso measures the split with a fixed panel of teams).
- The two banks of one episode share its market and weather and correlate at +0.73, so
  cross-episode comparisons of raw banks carry shared-world variance; within-episode margins
  are the cleaner ruler ([measured here](https://www.kaggle.com/code/destbreso/kaggriculture-what-kind-of-game-is-this)).
- A submission's consecutive games are serially correlated (matchmaking chains opponents), so
  win-rate confidence intervals built on "n independent games" are narrower than the truth;
  [Know Your Noise](https://www.kaggle.com/code/destbreso/kaggriculture-know-your-noise)
  measures by how much.
- Validation (self-play) episodes are excluded from every strength comparison; section 1 shows
  their share of the raw data.

[code cell 35: 33 lines]
```
lead_row = fp.iloc[0]
elbow_txt = ("" if not elbows else
             (f"day **{min(elbows.values())}**"
              if min(elbows.values()) == max(elbows.values())
              else f"day **{min(elbows.values())}–{max(elbows.values())}**"))
land_txt = ("no land purchase at all" if pd.isna(lead_row["first land (day)"])
            else f"land on day **{lead_row['first land (day)']:.0f}**")
crop_txt = (f"and the biggest wins all lead with {uniq_crops[0]}" if len(uniq_crops) == 1
            else "while the biggest wins disagree on which crop to lead with")
display(Markdown(textwrap.dedent(f'''
<a id="s13"></a>
## Takeaways ({AS_OF:%b %d, %Y} snapshot)

1. The ladder's spread is wide: the record win of **{fmt(rec.winner_bank)}** is
   **{rec.winner_bank / q[.5]:.1f}×** the median win of **{fmt(q[.5])}**.
2. Big games share one silhouette: reinvest almost everything, then compound. The leaders cross
   a tenth of their final bank around in-game {elbow_txt}.
3. The record holder's measurable edge is labor and land: a crew of
   **{lead_row['peak crew']:.0f}** and {land_txt}, {crop_txt}.
4. Market prices inside a game are their own strategy log: in the biggest replayed game melon swung
   **{(max(prices["MELON"]) - min(prices["MELON"])) / base_price["MELON"]:.0%}** of its base price
   and wheat ran **{min(prices["WHEAT"])}–{max(prices["WHEAT"])}**.

The [dataset]({"https://www.kaggle.com/datasets/georgymamarin/kaggriculture-episodes"}) and this
notebook both refresh daily, so 
```