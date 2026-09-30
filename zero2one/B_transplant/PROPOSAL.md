# Track B — "Brain transplant": clone the champion's decisions into our own body, then beat it where it leaks

One line: keep our own execution code ("body") and train small CPU models ("brain") on unlimited
teacher trajectories from fastsim (the teacher is `v7_endgame`, plus pool agents and the top-team replays). Fix
covariate shift with noise-injected teachers and DAgger. Beat the teacher on the parts it measurably leaks, using
advantage-weighted cloning and exact code for the endgame and shed.

## 1. Lineage of philosophy

**General baseline: supervised imitation of the strongest available policy, then improve it.**
- AlphaStar started from imitation of human replays. That policy alone played "better than 84% of active
  players". RL then used "distillation … to bias exploration towards human strategies", and a latent variable
  encoded the opening. https://deepmind.google/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/
- Kore 2022: the whole agent was supervised on about 200M (observation, plan) tuples from the top five submissions.
  https://github.com/khanhvu207/kore2022
- Lux AI S1: "imitation learning is super powerful. The first place solution has public replays and is much much
  more powerful than 2nd place." https://github.com/Lux-AI-Challenge/Lux-Design-S1/issues/142
- Google Research Football on Kaggle: one author trained on about 333 top-player games (about 1M frames) and got a rating
  over 900 from "2 days of simple supervised learning". He then patched it with "rule-based defending strategies" from
  public kernels. https://flyyufelix.github.io/2020/12/02/google-football-rl.html

**Layer strategy (narrower topic: learn the macro decisions, hand-code the micro).**
- TStarBot1 reduced the action space to 165 macro actions. TStarBot2 used a two-tier "Macro-Micro" hierarchy
  with rule-based controllers, because hard-coded game rules and "trivial decisions" waste learning capacity.
  https://ar5iv.labs.arxiv.org/html/1809.07193 — For us, learning sets *what/when/how much*; our code handles *who walks where*.
- Covariate shift: plain behaviour cloning compounds its errors, and DAgger fixes this by aggregating expert labels on states the
  learner itself visits. https://arxiv.org/abs/1011.0686 — DART injects noise into the *supervisor* instead, so the
  demonstrations include recoveries. It is cheaper than DAgger and cost only about 5% of supervisor reward.
  https://arxiv.org/abs/1703.09327
- Distilling a policy into trees with a DAgger variant matched the oracle policy's performance (VIPER).
  https://arxiv.org/abs/1805.08328 → this justifies GBDT heads on hand-built features.

**Tuning / exceed-the-teacher philosophy.**
- AWR: two supervised regressions (value, then advantage-weighted policy). It works "from purely static datasets".
  https://arxiv.org/abs/1910.00177 — we weight teacher and pool samples by final-margin advantage.
- Expert Iteration: an apprentice imitates a stronger planner, and the planner is then improved using the apprentice.
  https://arxiv.org/abs/1705.08439v4 — here the "planner" is exact code for the endgame and market, placed on top of the cloned prior.
- AlphaStar Unplugged: offline RL on top of a BC prior reached 90% against the BC agent.
  https://arxiv.org/abs/2308.03526
- In-competition source (`research/extracted/kaggriculture-findings-from-zero-to-top-meta/digest.md`): copy a
  schedule only if it is *stable across opponents*, and gate it from both seats. The whole top meta converged to one
  8-cow, 5-sheep, 12-hand plan.

## 2. Core design

**State features (about 180 floats, computed from `obs`):** step, day, and hour (sin/cos); money for both players; own and
opponent tile census (crop × growth stage × watered/fertilized, animals × fed/cared/yield_units, empty, weed, locked);
unlocked quadrants; hires_today; shed and seed counts and per-unit inventory; **projected end-of-day shed total
(shed + all unit inventories + pending harvests)**; market inventory, price, and exact marginal price after selling k
units (from the README price function, e.g. strawberry linear 1.60 above I0, T=100); unlocked-shop multiset (8 shop types ×
count); opponent-bank deltas, including the lineage tag from NOTES E2. Tile heads also take tile (x,y), distance to
the shed and the neighbouring tile state.

**Learned heads (LightGBM, exported to pure-Python if/else, so the submission has no dependencies):**
| Head | When | Label (from the teacher's logged action) |
|---|---|---|
| H1 Capex | hour 0 plus event triggers | BUY_LAND yes/no; BUY_ANIMAL {goose,cow,sheep}×n; hires today (0–13) |
| H2 Tile use | an empty/weed tile is available | PLANT crop ∈ {5} / BUILD_COOP / BUILD_PASTURE / leave |
| H3 Harvest/ops | a mature plant or an animal with yield | harvest now vs wait; FERTILIZE yes/no |
| H4 Market | every turn, per product | SELL bucket {0,1–2,3–5,6–10,11–25,all}; BUY_PRODUCT wheat/fert n |

**Body (our code, target about 700 lines):**
- Intents → units by greedy min-distance assignment. Hard obligations come first: water/feed before the second missed
  refresh (2 misses kill plants and animals), then CARE, then COLLECT_FERTILIZER.
- Logistics: PICKUP seeds/fert → PLACE; DROP when adjacent to the shed.
- **Shed guard.** If the projected end-of-day total exceeds 100, sell from the shed and hold harvests in the field. NOTES
  E6/E6b showed the leak ($889–$7,450 per game) is produce in unit hands, so the guard projects the hands too.
- Market orders are capped at 10 per turn and ordered by quote priority.
- **Endgame is exact code:** stop planting when a crop cannot mature by step 718, and liquidate everything by step 718
  (the last executing step) with a greedy marginal-price schedule across turns. The top teams gain $3.5k–$13.3k on the last day
  against our $8.2k (NOTES).

**Exceeding the teacher:**
1. AWR weights over the multi-teacher data (v7 plus 15 pool agents plus the top-team replays). An opening latent z
   (AlphaStar) keeps route families from being blended; the student fixes z at step 0.
2. The market head is conditioned on the shop state. The teacher is about 85% open-loop (see §3) and cannot react to shop
   RNG, which cannot be predicted (NOTES: 13.4% vs 12.5%) but can be reacted to.
3. Exact endgame and shed code replaces the teacher from day 27, where the champion loses −$1.5k on day 26 and
   −$1.3k on day 28 (NOTES E4).

## 3. Data & compute (measured today on this machine)

- One fastsim game (v7_endgame vs v56 or aurax7_v7) takes **2.1–2.4 s** on a single core.
- A teacher logging run (`zero2one/B_transplant/tools/probe_teacher.py`, 12 games on 8 workers) ran at **0.59 games/s**, about
  **2,100 labelled games/h**. That is about 1.5M turn samples/h, or about 13M unit-actions/h: each game has about 6.4k unit ops
  (about 9 hands on average, 13 at most) and about 1,100 market orders.
- **Teacher open-loop measurement:** v7's unit actions are identical across seeds and opponents up to step 151–459, and
  82–91% of all turns are identical (market 85–97%). This makes the teacher easy to fit, but it also means DAgger labels off
  its trajectory may be meaningless. Hence DART plus a validity filter (§6).
- Replays: 52 ladder episodes, 1.6 GB (about 31 MB each). They contain both seats' private observations, actions and seed, so they give
  104 top-rated seat trajectories that can be re-simulated exactly. The daily Kaggle episode sets hold about 650 episodes/day
  but are about 21 GB/day (`research/episodes/manifest.csv`), which is optional and filtered to top teams only.
- Storage: about 180 float32 × 720 × 2 seats ≈ 1 MB/game, so 5,000 games ≈ 5 GB (hours can be subsampled ×4).
  Training is 8-core LightGBM (`pip install lightgbm`, CPU wheel), expected at minutes per head; the time is measured on Day 1.
- Limits: `actTimeout` is 1 s, and the overage bank was 57.6 s at step 5 in a replay. A pure-Python tree evaluation (6 heads × 300 trees
  × depth 7) takes about 1–3 ms. Model JSON is under 3 MB inside `submission.tar.gz`. The size cap must be confirmed on the
  competition page; it is not in rules.txt.

## 4. Four-day build plan (all gates: fastsim, same seeds, both seats, win count first)

| Day | Build | GO/KILL gate |
|---|---|---|
| D1 09-24 | Featurizer, intent extractor (unit op + position → tile intent) and body v0. Log 3k teacher games (v7 against 15 pool agents × 100 seeds × 2 seats), 30% with DART ε-noise (drop or delay 5–15% of macro intents). | **Oracle test:** the body executing the *teacher's own* logged intents must reach ≥ 95% of the teacher's bank on 20 seeds. Below 90% means the abstraction loses information, so KILL the macro design and switch to per-unit op classes. |
| D2 09-25 | Train H1–H4 (plain BC), student v1. | Held-out agreement: H2 ≥ 90%, H4 bucket ≥ 80%. v1 wins ≥ 90% vs `agents/main.py` (**top-50% gate**). KILL if the bank is < 70% of the teacher's after 2 retrains. |
| D3 09-26 | 2–3 DAgger/DART rounds (1k student games with shadow-teacher labels, ≈30 min, plus retraining ≈10 min). Add AWR weights, the z latent, and replay data. | ≥ 20% vs `farm2945` (**top-25% gate**), then ≥ 40% vs `farm2945` and ≥ 30% vs `hybrid2965` over 64 games (**top-12.5% gate**). |
| D4 09-27 | Endgame/shed takeover, shop-conditioned market, and a sweep of AWR β, ε and the switch day (80-game screen, then 200-game re-validation). Export to pure Python; timing and packaging test. | ≥ 50% vs `v7_endgame` over 200 fresh paired games, and a pool win count ≥ the champion's. Max per-turn time < 100 ms. |

D5–D7 are a buffer for the cross-track battle.

## 5. Staged targets → win rates

Leaderboard CSV downloaded today: 9,883 teams. The cut-offs are **top 50% ≥ 766, top 25% ≥ 1,577, top 12.5% ≥ 2,246**
(top 5% ≥ 2,542). Anchors:

| Agent | Rating | Percentile |
|---|---|---|
| `agents/main.py` | ≈ 499 | below the median |
| `farm2945` unmodified | ≈ 2,065 | about rank 1,580, top 16% |
| `hybrid2965` unmodified | 2,370 | about rank 940, top 9.5% |
| v7 champion | ≈ 2,640 | about rank 270, top 2.7% |

Most pool agents are in the 2,000–2,600 lineage band. The win rates below assume Elo-like logistic odds (an unverified
assumption about Kaggle's rating):

| Target | Required result |
|---|---|
| Top 50% | ≥ 90% vs `main.py` and every `research/refagents` agent |
| Top 25% | ≥ 20% vs `farm2945` (≈ 1,830 equivalent) |
| Top 12.5% | ≥ 40% vs `farm2945` and ≥ 30% vs `hybrid2965` (2,370 − 124 ⇒ 33%) |
| Final | ≥ 55% vs `v7_endgame` over 200 games (the win-rate SE is about 3.5%) |

## 6. Top-5 risks and mitigations

1. **The teacher is a tape, not a state-conditioned expert.** Its shadow labels on student states may be nonsense.
   → Use macro labels, which are less trajectory-bound, and DART noise so its reactive layers show recoveries. Keep a shadow label only if it is
   legal and not a no-op in the student's state.
2. **The abstraction loses the micro edge** (one-turn market race, routing). → The D1 oracle gate measures this before
   any learning happens. H4 reproduces the teacher's order sequence within the turn.
3. **Near-clone ladder** (9 of 10 games decided by < $1k): a 97% copy just flips coins. → The edge comes from measured leaks
   (liquidation, shed overflow, days 26/28), not from matching the teacher.
4. **Low-power evaluation.** Per-game sd is about $9k, and 40-game "wins" have reversed before. → Win count, 200 paired games,
   and fresh validation seeds.
5. **Runtime and packaging.** LightGBM may be missing on Kaggle. → Export to pure Python, and keep a heuristic fallback if a head throws an error.
   Timing is tested at D4.

**Why this beats the other routes:** a scratch planner already capped out at about 500 here, and PPO on CPU in 4 days
over a 720-turn, 10-unit, multi-order action space is unrealistic (TStarBot needed macro actions even with a GPU).
Supervised cloning reaches teacher-level play in hours (GRF: 2 days of SL gave 900; AlphaStar SL alone beat more than 84% of players).
Its data is effectively unlimited (about 2,100 labelled games/h, measured). It is the only route whose *floor* is the
champion's behaviour, while its body and brain remain our own code.
