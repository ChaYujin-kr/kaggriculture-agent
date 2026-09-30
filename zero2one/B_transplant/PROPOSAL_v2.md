# Track B v2 — "Brain transplant": learn the champion's day-level plan, execute it with our own body

One line: we transplant *what the strong agents decide each day* (herd, land, crop and structure mix, hires,
sell-reserve policy), learned as state-conditioned day-level targets from the champion, the pool and the top-2
replays. We do **not** transplant *what they do each turn*. Our own closed-loop body (the `agents/main.py`
scheduler, rebuilt against teacher KPIs) turns those targets into unit actions. The teacher also serves as a dense
per-day diagnostic that shows where the body leaks, and our code owns the levers the tape lineage cannot reach
(units' hands, harvest timing).

The identity is unchanged: supervised imitation first, then improvement. What changes is the *grain* of the
imitation. v1 cloned per-turn intents. v2 clones one plan vector per day plus a reactive market policy, which are
the only parts of the teacher that are actually state-conditioned.

## Changes from v1

| # | v1 | v2 | Why (verified) |
|---|---|---|---|
| 1 | Per-turn/per-tile heads (H2 tile use, H3 harvest) with `step` as a feature | **Day-level plan heads** (evaluated at hour 0 and at each shop unlock) plus a per-turn **market head** only | Accepted (A, C): v7 is open-loop. `probe_teacher.py` shows 82–91% of turns identical across seeds. Per-turn step→action heads would recompress the route library, which is a fork by distillation. |
| 2 | DART noise on the teacher plus DAgger shadow labels | **Removed.** Covariate shift is handled by a closed-loop body chasing coarse targets, plus an OOD guard | Accepted and **measured today** (`tools/probe_noise.py`, v7 vs farm2945, 6 seeds). Clean: $84.2k. 5% unit→PASS noise over the whole game: **$16.5k**. 10%: **$1.1k**. 10% over just 2 days: $75.4k (steps 48–96) and $81.8k (300–348). The noisy teacher does not *recover*, it collapses, so DART data would teach failure. Shadow labels from a tape are state-blind. |
| 3 | Opening latent z fixed at step 0 | Plan heads are **re-evaluated at every shop unlock**. The unlocked-shop multiset is a first-class input | Accepted (A, C). `v7_endgame._router` picks a route from the first two shops at `step>=144` (`_KNOB_936_13=144`) and switches to route 2 at `step>=648`. v1's "teacher cannot react to shop RNG" was **false**, and the step-151 divergence is that router. |
| 4 | AWR on final margin | **Dropped from the core.** Source filtering plus a "stable across opponents" admission test (from A); AWR only as a D4 ablation | Accepted: sd ≈ $9k, and 9/10 near-clone games are decided by < $1k, so final-margin weights mostly encode seed luck. |
| 5 | "Exceed the teacher" via the day-26/28 endgame, the shed guard and shop conditioning | Only **one** lever is kept: control of units' hands against shed overflow (the E6 failure was architectural). The top-2-branch herd plan family is a second, gated hypothesis. The endgame is not claimed as an edge | Accepted: the E4 gates are inside `v7_endgame` (71/80 vs pool), and v7_endgame already carries the E182 last-seven-turn planner plus a step-718 projected-shed liquidation. E6a/E6b gave no gain. But E6b failed *because* "SELL only draws from the shed, but the overflow is produce still in the units' hands" (NOTES). A body we own decides when hands harvest and DROP; a layer on a tape cannot. |
| 6 | Mechanic: "2 misses kill plants and animals" | Plants: a plant **must be watered on its planting day**, or it becomes a weed at the first refresh. Animals: 2 missed days | Accepted, verified in `kaggriculture.py`: `_new_plant` sets `"consecutive_unwatered": 1  # planting day counts as unwatered`, and the refresh converts to WEED at `>= 2`. Animals start at `consecutive_unfed: 0`. |
| 7 | Oracle gate ≥95% on D1, fallback = per-unit op cloning | Staged oracle gates (D1 ≥ 60%, D2 ≥ 80%), with the fallback **removed**. If the body cannot execute, the track is killed and not turned into a fork | Accepted (A): our planner executed at 73k vs 170k solo (CARE 83 vs 410, fertilizer 60 vs 372). 95% on day 1 was fantasy, and per-unit op cloning is a straighter fork. |
| 8 | Agreement-% gates (H2 ≥ 90%, H4 ≥ 80%) | **Plug-in regret**: the bank of (body + predicted plan) ÷ the bank of (body + teacher's logged plan). Market head: per-class recall and money-weighted error | Accepted (C): the labels are imbalanced, so majority-class guessing passes agreement gates. |
| 9 | 64–200-game gates, and inconsistent final thresholds (≥ 50% vs ≥ 55%) | **400-game** stage gates, a **1,000-game** final gate, one-sided 95%, one stated threshold per gate, Elo mapping recomputed | Accepted (C). Games are cheap: 1,000 games × 2.3 s ÷ 8 cores ≈ 5 min. |
| 10 | Latency "1–3 ms" for per-tile heads; 230k-node export | Day heads run ≈ 40×/game; the market head runs per product per turn with ≤ 100 trees of depth ≤ 5. Export < 1 MB, measured on D2 | Accepted (A, C): per-tile evaluation was understated about 100×. The per-tile heads no longer exist. |
| Stolen | — | A: oracle execution gate as a diagnostic that separates body loss from plan loss; per-day op-mix KPIs; stability-across-opponents admission. C: shop-conditioned re-planning at every unlock; exact replay traces (both seats' private obs plus seed) for the top-2 branch; pure-Python tree export | These fit the transplant philosophy: the teacher gives targets and diagnostics, and we own the execution. |

**Rebutted (partly):** "Not 0-to-1 / fork by distillation." The brief explicitly allows *learning from* the
champion's behaviour and replays. v1 deserved the critique because its per-turn heads would have learned
step→action. In v2 the learned artifact is about 40 plan decisions per game plus a market policy. Routing,
task assignment, logistics, water/feed/care obligations, harvest timing and the endgame are all our code, and no
route tape, knob table or reactive layer from the lineage is imported. The honest residue is that for days 0–5 the
champion's plan is identical across seeds, so the learned opening *is* a constant schedule copied from the prior. It
has the same status as the public "8 cows, 5 sheep, 12 hands" meta: a plan shape, not a program.

## 1. Lineage of philosophy

**General baseline: supervised imitation of the strongest available policy, then improve it.**
- AlphaStar: an imitation-only policy beat 84% of players, and a latent variable encoded the strategy
  (https://deepmind.google/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/).
- Kore 2022: a whole agent trained with supervised learning on about 200M (obs, plan) tuples from top submissions (https://github.com/khanhvu207/kore2022). Its label was a *plan*, which is the grain v2 adopts.
- Lux S1: "imitation learning is super powerful" (https://github.com/Lux-AI-Challenge/Lux-Design-S1/issues/142).
- A caveat accepted from the critiques: GRF supervised learning reached > 900 with GPUs over 2 days
  (https://flyyufelix.github.io/2020/12/02/google-football-rl.html), and the Kaggriculture BC+PPO PR calls its gain
  over BC "unconfirmed". These show that BC gives a *floor*, not a top rank.

**Layer strategy (narrower): learn the macro decisions, hand-code the micro.**
- TStarBot1 (165 macro actions) and TStarBot2 (Macro-Micro, rule-based controllers): https://ar5iv.labs.arxiv.org/html/1809.07193.
  v2 applies this at a coarser level than v1. The macro layer is *daily*, because that is where the teacher's
  decisions vary with state: shop routes and herd/hire curves.
- Covariate shift (DAgger, https://arxiv.org/abs/1011.0686) assumes an expert that can be queried on any state. A tape
  is not such an expert, and our noise test shows it collapses off-trajectory. v2 therefore handles shift the TStarBot way,
  with a closed-loop controller under coarse targets, and not the DAgger way.
- VIPER (https://arxiv.org/abs/1805.08328): small trees can distil a policy, which justifies GBDT heads on hand-built features.

**Tuning / exceed-the-teacher philosophy.**
- Expert Iteration (https://arxiv.org/abs/1705.08439v4), reinterpreted: the "planner" that improves on the apprentice
  is exact code for the one mechanic where the tape lineage is structurally blind (produce in hands at the end-of-day drop).
- In-competition source (`research/extracted/kaggriculture-findings-from-zero-to-top-meta/digest.md`): copy a schedule only if it is
  *stable across opponents*, and gate it from both seats. v2 adopts this as its data-admission rule.

## 2. Core design

**Plan vector (label, one per day d and one per shop-unlock event):** land purchased by day d; herd {goose, cow, sheep}
purchases; hires today (0–13); tile allocation targets by crop (5) and by COOP/PASTURE; fertilizer and CARE coverage
targets; per-product *shed reserve* (units held back from selling at end of day) and the day's sell volume. All of it
is extracted from the teacher's logged actions and daily tile census. There are no unit coordinates and no turn indices.

**State features (about 90 floats, day-level):** day; own and opponent money; own tile census (crop × stage, animals ×
fed/cared/yield, empty/weed/locked); quadrants; herd; hands; shed plus hand inventories; market inventory and price per
product; unlocked-shop multiset; opponent lineage tag (NOTES E2); opponent bank delta over the last day. `step` is
never a feature of any head, only `day`, so no head can learn an intra-day tape.

**Learned heads (LightGBM on 8 CPU cores, exported to pure-Python if/else):**
| Head | Evaluated | Output |
|---|---|---|
| P1 Capex | day start and each shop unlock | land yes/no; herd buys by type; hires today |
| P2 Allocation | same | target tile mix by crop and structure for the next day |
| P3 Reserve | same | per-product sell volume for the day, and the shed reserve |
| M Market (reactive) | each turn, per product with stock | SELL bucket {0, 1–2, 3–5, 6–10, 11–25, all}, conditioned on price, marginal price after k units, inventory and the opponent's inferred sales |

The market head is the only per-turn learned piece. It is also the one layer of v7 that measurably varies with
state (market actions differ in 3–15% of turns across seeds).

**Data admission (stability test, from A and the meta digest):** a plan component is learned from state only if,
across ≥ 5 opponents × 2 seats at a fixed shop state, its per-day variance is explained by our features (held-out R² >
0.5). Otherwise it is stored as a constant prior per (day, shop state), which is honest about what is and is not a
learned decision.

**Body (our code: `agents/main.py`'s scheduler, rebuilt, about 800 lines):**
- Target-chasing. Each day's plan becomes a queue of tile projects (buy land, build, plant X, buy animal).
  Hard obligations come first: water **on the planting day** and before the second missed refresh; feed before the second
  missed day; then CARE, then COLLECT_FERTILIZER. Greedy min-distance unit assignment with a 2-turn lookahead.
- **KPI-diff debugging (A's idea).** For every oracle run, compare against the teacher per day: CARE count, fertilizer
  collected, fraction of unit-turns spent moving, escapes/weeds, and hands idle. The body is fixed in the order of the
  largest dollar gap. Known gaps to close first: CARE 83 → 410, fertilizer 60 → 372, movement 64% → 50%.
- **Hands-aware shed control (the edge hypothesis).** Projected end-of-day total = shed + every unit's hands +
  mature yields scheduled for harvest before the drop. If it exceeds 100, the body delays harvest (the produce stays on
  the tile) or routes hands to DROP and sell earlier in the day. The measured leak is $889–$7,450 per game (E6).
- **Endgame.** We port no lineage code. Our own rules: stop planting when a crop cannot mature by step 718, and liquidate
  by step 718 on a greedy marginal-price schedule. The README records that swapping our late game into the tape *lost*
  (−7k at day 27), so the endgame is a **risk**, not an edge. It gets its own oracle comparison (body days 0–26 +
  teacher-like liquidation rules vs ours).
- The OOD guard: if > 30% of day features fall outside the training range (a quantile check), P1–P3 fall back to the
  constant prior for the current shop state.

## 3. Data & compute (measured on this machine)

- fastsim runs one game in 2.1–2.4 s on a single core. `tools/probe_teacher.py` logs **about 2,100 teacher games/h** on 8 workers.
- **Open-loop measurement (v1, still valid):** unit actions are identical across seeds and opponents up to steps 151–459,
  and 82–91% of turns are identical. That is exactly why v2 labels days, not turns.
- **Noise measurement (new, `tools/probe_noise.py`, v7 in seat 0 vs farm2945, 6 seeds):** clean $84.2k; 5% of unit commands
  → PASS all game $16.5k; 10% → $1.1k; 10% in steps 48–96 $75.4k; 10% in steps 300–348 $81.8k. The teacher has no recovery
  behaviour to imitate. The same sample went **0/6 against farm2945 even when clean**, so win rates against single anchors
  are noisy and seat-dependent, which is why all gates use ≥ 400 paired games.
- Day-level dataset: 2k teacher games plus 16 pool agents × 100 seeds × 2 seats (≈ 3,200 games, ≈ 1.6 h) give ≈ 150k
  (state, plan) rows. That is minutes on LightGBM (installed: `lightgbm 4.7.0`, `xgboost`, `sklearn`, `numpy` are in `.venv`).
  Market rows: ≈ 5M (subsample to 1M).
- Replays: 52 episodes, 104 seats with private obs and seed. Top-2-branch plan vectors come from the replays directly
  (day-level extraction needs no re-simulation). With so few seats, they only serve as the alternative plan family (§6).
- Runtime: P1–P3 ≈ 40 calls/game. The market head uses ≤ 7 products × 720 turns × 100 trees × depth 5, which is well under 10 ms/turn
  in pure Python. Export < 1 MB. Both are measured on D2 against `actTimeout` 1 s.

## 4. Four-day build plan (fastsim, same seeds, both seats, win count first)

| Day | Build | GO/KILL gate |
|---|---|---|
| D1 09-24 | Plan extractor (teacher logs and replays → daily plan vectors) and the KPI harness. Body v0 = the `main.py` scheduler adapted to consume a plan. Log 3.2k games (≈ 1.6 h in the background). | **Oracle-1:** body + the teacher's logged plan, on 20 seeds × 2 seats vs farm2945, reaches **≥ 60%** of the teacher's bank → GO. **KILL** if < 45%, because then the transplant adds nothing over our 43% planner. Also: oracle-1 wins ≥ 85% of 400 games vs `main.py` (**top-50% gate**). |
| D2 09-25 | KPI-diff fixes (CARE, fertilizer, movement); train P1–P3 and M; stability admission; pure-Python export and timing. | **Oracle-2 ≥ 80%** of the teacher's bank. **Plug-in regret:** the student plan loses ≤ 10% bank vs the logged plan. **Top-25% gate:** ≥ 99% vs `main.py` and ≥ 6% vs farm2945 (400 games). KILL the learned heads (keep the constant prior) if regret > 20% after two retrains. |
| D3 09-26 | Shop-unlock re-planning; top-2-branch plan family as a selectable prior; hands-aware shed control; our endgame vs a liquidation oracle. | **Top-12.5% gate:** ≥ 33% vs hybrid2965 **and** ≥ 70% vs farm2945 (400 games each). Each lever is kept only if it gains ≥ +3 pp in wins over 400 paired games (one-sided 95%). |
| D4 09-27 | AWR-by-daily-net-worth ablation; retrain on student-state days (with the constant-prior fallback labels); packaging and timing; the final match. | **Final:** vs `v7_endgame` over **1,000** paired games (500 seeds × 2 seats); the *beat-the-champion* claim needs ≥ 526 wins (one-sided 95%). Pool win count ≥ the champion's over 16 × 50 × 2. Max turn time < 100 ms. |

D5–D7 are a buffer for the cross-track battle and fresh-seed re-validation.

## 5. Staged targets → win rates

Leaderboard (9,883 teams): top 50% ≥ 766, top 25% ≥ 1,577, top 12.5% ≥ 2,246. The anchors are `main.py` ≈ 499,
farm2945 ≈ 2,065, hybrid2965 2,370 and v7 ≈ 2,640. The mapping uses Elo-logistic odds, P = 1/(1+10^((R_opp−R)/400)). This is an
**assumption**: the ladder is dominated by one lineage and is non-transitive, so each gate uses two anchors.

| Target | Rating | Required result (v1 errors fixed) |
|---|---|---|
| Top 50% | 766 | ≥ 82% vs `main.py` (so the gate is ≥ 85%) and ≥ 90% vs each `research/refagents/*.py` |
| Top 25% | 1,577 | ≥ 99% vs `main.py` **and** ≥ 6% vs farm2945 (v1's "20% vs farm2945" equals 1,824, and was mislabelled) |
| Top 12.5% | 2,246 | ≥ 74% vs farm2945 **and** ≥ 33% vs hybrid2965 (v1's "40% vs farm2945" equals only 1,995, and was wrong) |
| Beat champion | > 2,640 | ≥ 526/1,000 vs `v7_endgame` |

Honest odds: top 50% is likely if Oracle-1 passes, top 25% is plausible, and top 12.5% needs Oracle-2 ≥ 80%. Beating the
champion needs the hands-aware shed lever or the top-2 plan family to pay; I rate that ≤ 15%.

## 6. Top-5 risks and mitigations

1. **The body cannot execute** (the historical 73k vs 170k gap). → This is the first thing measured (Oracle-1 on D1), with
   KPI-diff debugging to find fixes in dollar order. There is a hard KILL below 45%, and no fallback into op cloning.
2. **The learned plan is "just the tape in day form."** → `step` is excluded, the stability admission separates learned
   components from constant priors and reports them, and the plan is re-evaluated at shop unlocks. If P1–P3 add nothing
   over the constant prior (D2 regret test), we say so and ship the prior. The originality then lives in the body.
3. **Covariate shift without DAgger.** → Coarse targets plus a closed-loop body plus the OOD fallback. D4 retrains on
   student-visited days, labelled by the constant prior, so the heads never extrapolate silently.
4. **No real edge over the teacher.** → The only claimed lever is architectural (hands), and it is tested at +3 pp over 400 games.
   The top-2 plan family (more cows and geese, which won their head-to-head by $14k) is the second option. If neither pays, the final gate is
   reported as failed, not re-tuned on small samples.
5. **Low-power evaluation / non-transitive anchors.** → 400–1,000 paired games per gate (≈ 2–5 min each), fresh seeds for
   re-validation, and two anchors per stage. Our own noise sample (0/6 clean vs farm2945 in one seat) shows why.

**Why this track still beats the alternatives:** it is the only route that uses the strongest agent's decisions *as data*
and still ships our own execution code. Its gates tell us on day 1 whether the bottleneck is plan or execution, a
question none of our past work could answer. Its data is cheap (about 2,100 games/h), and it needs no RL credit assignment over 720
turns on a 4-core laptop CPU.
