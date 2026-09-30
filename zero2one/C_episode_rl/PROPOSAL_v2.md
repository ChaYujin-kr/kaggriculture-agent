# Track C (v2): episode-level parameter search over a closed-loop plan controller

**Verdict.** The unit of learning is still the **whole-game plan**. At step 144, once the first two shops are revealed, a contextual selector draws one parameter vector θ (about 12 dimensions) per episode. A **closed-loop, deterministic controller that is our own code** then runs the game from θ. One episode returns one reward, and the search is PGPE/ES with common random numbers (CRN). That is the track's identity, and it is unchanged from v1.

What changed is everything around it, because the critiques were largely right:
- **The executor is new code.** v1 reused the `agents/main.py` scheduler, the component that capped us at about 500. The v2 executor is a layout-first day-program controller, built and gated before any search runs.
- **θ sets targets and thresholds that the controller tracks every day from live state.** In v1 it was an open-loop calendar.
- **The prior over θ is fitted from observable macro statistics** of every lineage, weighted by outcome. v1 inverted action traces into θ; v2 does not read any action stream. The "be recognised as the lineage" gate is gone.
- **ES gets its gradient from CRN-paired margins over 12 dimensions.** v1 used win counts over 40 dimensions. Win count is used only for acceptance.

Two measurements made today in this track (`zero2one/C_episode_rl/tools/`) drive this revision:

| Probe | Result | Consequence |
|---|---|---|
| `probe_divergence.py`: v7_endgame, same seed, different opponent | Unit actions first diverge at step **151–396**. **2–38%** of turns differ (vs v56: 31–38%). Market actions differ on 4–34% of turns. | v1's "exactly one plan decision at step 144" was **wrong**. The champion is reactive, so an open-loop θ calendar cannot represent it. |
| `probe_crn.py`: v7_endgame with knob `_KNOB_3894_29` changed from 648 to 600, 48 games (2 opponents × 12 seeds × 2 seats), paired by seed, seat and opponent | Per-game margin sd **$9,035**. Paired difference **−$20, sd $79**. **0 of 48 games changed winner.** | Under CRN on a deterministic simulator, the noise of a comparison scales with the size of the perturbation, not with the $9k between-seed sd. A win-count reward would give **zero** gradient, so the critics were right about that. A paired-margin reward does give a gradient. |

Historical evidence: `tuning/log.jsonl` is our own earlier antithetic-CRN ES over the parameters of `agents/main.py`. Over 12 generations the mean margin against its pool rose from **$3.0k to $36.8k**. The search found signal, and the agent still topped out at about 500 because the executor was the ceiling. v2 therefore spends D1–D2 on the executor and D3–D4 on search.

## 1. Lineage of philosophy

**General baseline: episode-level parameter search (kept from v1, with the claims narrowed)**
- ES is invariant to delayed reward and long horizons, and uses CRN. https://arxiv.org/abs/1703.03864
- PGPE samples parameters once per episode and runs a **deterministic** controller that can be closed-loop. Its gradient variance does not grow with horizon length, and symmetric (antithetic) sampling helps. https://www.ias.informatik.tu-darmstadt.de/uploads/Publications/Neural-Networks-2010-Sehnke_%5B0%5D.pdf. v1 misread "one sample per episode" as "open-loop"; PGPE never required that.
- CMA-ES noise handling re-evaluates candidates and raises the evaluation count when noise dominates. https://cma-es.github.io/apidocs-pycma/cma.optimization_tools.NoiseHandler.html
- Halite IV 4th place dropped evolution because of symmetry, overfitting and self-play-only opponents. https://github.com/0Zeta/HaliteIV-Bot. This is why v2 uses fresh-seed SPRT acceptance, a mixed population, and a trust region around the prior.
- PSRO: best-respond to opponent *mixtures*, not to one opponent. https://arxiv.org/abs/1711.00832

**Narrower topic: plans as the action (Kaggriculture)**
- OscarLegoupil: "a route is a YAML plan for one 720-turn episode", plus a selector. **Corrected per B:** the 378-22 is against its own base in a local round-robin; there is no ladder evidence. It is cited for the design pattern only.
- sidhulyalkar: exact controller, parametric macro policy, population CEM. **Corrected per B:** its learned model was never promoted, and the 600 is its entry rating. It is cited as a warning, not as support.
- prince22466 reward `sign(m)+0.05·tanh(m/1e4)`. v2 keeps it for **acceptance** only. Gradients use `tanh(m/1e4)` on CRN pairs, because the sign term does not move under small perturbations (probe above).

**Developmental framing: trimmed to what is operational.** Both critics called the linguistics table decorative, and for four of its seven rows that was true. Those rows are dropped:
- Newborn discrimination: E2's bank tag already solves it.
- Saffran/Sequitur segmentation: too costly for D1 and not needed.
- Kuhl live exposure: it only meant "use fastsim".
- Differentiated systems: absorbed into the prior below.

Three rows remain, each tied to a concrete operation:

| Finding | Operation |
|---|---|
| Proficiency tracks relative input (Hoff 2012) https://eric.ed.gov/?id=EJ971194 | The **prior** over θ is a mixture fitted from each lineage's macro statistics. Weights are dose × outcome (AWR-style exp(margin/β), stolen from B), not dose alone. The top-2 branch (more cows and geese, won its head-to-head by $14k) therefore gets real weight even with few samples. |
| Sensitive period, then narrowing (Werker & Hensch 2015) | The prior is **frozen** before search. ES runs inside a trust region, with the Mahalanobis distance to the prior ≤ r, and r is widened only after an SPRT accept. This is the anti-overfitting brake against a 16-agent pool. |
| Code-switching at boundaries marks competence (Yow et al. 2018) | θ may be re-selected **only at event boundaries**: a shop unlock, a land purchase, and day 20. This is a small, bounded amount of mid-game adaptation, on top of the daily closed-loop tracking. |

## 2. Core design

### 2.1 Controller: layout-first day programs, our own code

This is a new build in `zero2one/C_episode_rl/`. Nothing is imported from `agents/main.py`.

1. **Layout compiler** (runs at step 0 and on each land buy). A fixed geometry is derived from θ:
   - The animal ring sits on tiles adjacent to the shed, so feed pickup and drops are 1–2 moves.
   - Crops are planted in contiguous blocks swept in serpentine order.
   - A wheat feed row is sized to the herd target.
   - Geometry is our own. The only thing taken from the lineage is the *shape statistic*: tiles per crop per phase and animals per type.
2. **Daily planner** (hour 0, plus event triggers). It rebuilds the day from **live state** and θ:
   - Obligations: WATER every plant, FEED every animal, CARE every animal whose next production falls in the season, COLLECT_FERTILIZER, and HARVEST when yield is at cap or the animal is at `max_held`.
   - Projects that move the farm toward θ's targets: plant, build, buy animal, buy land.
   - Each hired unit gets one **unit-day program** from a small template grammar:
     - `RING(k)`: feed, care and collect around k stalls
     - `SWEEP(block, WATER[+FERT])`
     - `HARVEST_SWEEP(block)`
     - `PLANT_WATER(block)`, which plants and waters on the same day
     - `LOGISTICS`: pickup, place and drop
     - `BUILD`
   - Template families come from the census of 12,236 unit-day programs in the 41 routes (1,077 distinct; the top 300 cover 72%). This is used as a **list of what kinds of days exist**. No recorded coordinates or sequences are stored.
   - Hires: n units while the day's labour need exceeds capacity and the marginal job value exceeds fib(n); θ caps the number of hands.
3. **Per-turn repair.** A program step is checked before it is emitted. If it is invalid (a weed spawned, a crop died, not enough money, a tile is occupied), the unit takes the most urgent nearest job in deadline order. Unmet hard obligations pre-empt everything.
4. **Mechanics, verified in the interpreter** (`kaggriculture.py`, lines 222 and 777–818):
   - `consecutive_unwatered` starts at **1**, because the planting day counts as unwatered. A **fresh plant turns to weed if it is not watered on its planting day.** Established plants and animals fail after **2** missed days. **v1's statement was wrong for fresh plants, and A was right.** Hence `PLANT_WATER` is one program and never two.
   - The fertiliser bonus applies only on watered days.
   - The CARE bonus is consumed only on a fed production day.
5. **Market (state feedback).**
   - Premium goods are sold on a per-product ladder of lot size and minimum price ratio (from θ) against the live price, using the exact price function.
   - At most 10 orders per turn, SELLs first.
   - Wheat for feed is bought in the cheapest window.
6. **Shed invariant.** (shed + inventories in units' hands) ≤ margin by hour 22. Produce is routed to the shed and sold down before the end-of-day drop. NOTES E6a/E6b showed that lowering the cap alone does nothing, because the leak is produce in hands.
7. **Endgame (exact code).**
   - The stop-plant day per crop is derived backward from step 718.
   - CARE runs only while a production is still in the season.
   - A final-day liquidation schedule sells across turns. Top teams gain $3.5–13.3k on the final day, where our lineage gains $8.2k.

### 2.2 Genome θ: about 12 dimensions, each an observable statistic

| Block | Genes |
|---|---|
| Herd | target cows, sheep and geese at the day-12 plateau (3) |
| Crops | strawberry block size, the ratio of wheat feed row to herd, and the size of the melon/carrot finale (3) |
| Labour | hands cap, and the marginal-value hire threshold (2) |
| Land | buy day for the second quadrant (1) |
| Market | premium hold ratio: the sell price over the reference below which we hold (1) |
| Endgame | liquidation start step, and stop-plant slack in days (2) |

Every gene is a **measurable property of a farm**, such as herd count by day, tile counts by crop, hands per day, the day a land purchase happens, or the price at which sales happen. That makes v1's ill-posed "invert traces into θ" a plain measurement. Per-unit routing is **not** in θ; routing belongs to the controller. This answers A's point that "the genome cannot express per-unit routing": it is not supposed to.

### 2.3 Prior and selector: learning from data without copying

- **Macro-stat logger.** Farms are public in `obs`. We log each pool agent's per-day herd, crop tiles, quadrants, hand count and money, both seats, for all 16 pool agents and 10 reference agents. We also extract the same statistics from the 52 ladder replays and the 8 top episodes.
- **Prior.** For each shop cluster, a Gaussian mixture over θ weighted by lineage dose × exp(margin/β). The clusters come from the first two revealed shops and are merged to 3–4 by demand vector. Conditioning uses only **revealed** shops, because the third unlock is unpredictable (13.4% vs 12.5%).
- **Selector.** At step 144 it maps (shop cluster, opponent tag) to a θ mean. The opponent tag is **E2's step-1 bank tag, reused as is** ($0 / $157 / $540); it is not re-solved, as A pointed out. The selector is the policy that ES improves (contextual PGPE).
- **Anti-clone checks**, reported rather than optimised:
  - The submission contains no tape bytes and no recorded coordinates.
  - The exact prefix match of our action stream against the nearest of the 41 routes is expected to be under 24 steps.
  - The share of our unit-day programs that exactly equal a recorded one is logged. **Being classified as the lineage is no longer a gate.** v1's recognition test (a)–(c) is deleted, and the MDL cap is no longer needed.

### 2.4 Search: low-dimensional contextual ES

- **Algorithm.** Separable CMA-ES, or antithetic ES with rank weighting. d = 12 global dimensions, plus per-cluster offsets **only if** the global run shows signal.
- **Gradient reward.** Paired `tanh(m/1e4)`, where m is the margin against the same (seed, seat, opponent) as the mirror candidate. Each iteration uses 6 antithetic pairs × 16 CRN slots, which is 8 seeds × 2 seats with the opponent drawn per slot from the population, plus the center: about 208 games, 4 minutes on 6 cores.
- **Acceptance.** Win count first, margin as the tie-break, on a **fresh** seed range. GSPRT with elo0 = 0, elo1 = +30 and α = β = 0.05 (the Fishtest rule, as in A). The trust-region radius r grows only after an accept.
- **Population.**
  - 50% from the ladder census (fork 11/14, aurax7 2/14, other 1/14), 50% uniform over families. The census has only 14 games (A's point), so it cannot carry the whole weight.
  - The census is replaced by `data_audit`'s larger one if that track produces it.
  - Frozen snapshots of our own θ, and one exploiter θ trained against our current center (PSRO-lite).
- **Budget split.** ES may use 6 of the 8 threads. 2 threads stay free for development and gate evaluation. This answers B's point that ES "freezes all other evaluation".

## 3. Data and compute (measured today)

| Item | Value |
|---|---|
| fastsim, 1 game, 1 thread | 1.5–2.3 s for champion-grade agents |
| Throughput | 8 processes: 1.04 games/s (my run); A measured 1.9 games/s on a lighter mix. **Planning figure: 0.8 games/s on 6 threads**, about 2,900 games/h |
| Probe: divergence | 6 games in 70 s. v7 unit actions differ on 2–38% of turns across opponents at a fixed seed |
| Probe: CRN noise | Paired-difference sd **$79** vs per-game sd **$9,035** (48 pairs, late-game knob). 0/48 winners flipped |
| Data | 52 ladder replays (1.6 GB), 8 top episodes, 16 pool + 10 reference agents, 41 routes (census only) |
| ES capacity | about 4 min per iteration, so about 15 per hour. An overnight run of about 12 h is **about 170 iterations at d = 12**. v1 had about 90 at d = 40 split into 5 blocks, about 18 updates per block. |

The $79 paired sd was measured on a late-game knob. Early-game perturbations diverge chaotically, so their paired sd will be larger, somewhere between $79 and the $9k ceiling. **This is measured on D2 on our own controller before ES starts** (the "noise audit", §4). If the paired sd of a 1σ θ step is above $4k, the iteration size doubles, or ES is dropped for racing (irace-style) over 16 prior samples.

## 4. Four-day build (all evaluations paired: same seeds, both seats)

| Day | Build | GO | KILL |
|---|---|---|---|
| D1 09-24 | Macro-stat logger (pool + replays), about 1 h of compute in the background. Layout compiler. Daily planner with RING, SWEEP, PLANT_WATER, HARVEST_SWEEP and LOGISTICS. Per-turn repair. A fixed θ taken from the prior mean | Solo ≥ **110k** against `fallow_finn` (16 seeds), 0 escapes, ≤ 2 weeds, movement share ≤ 60%. KPI census (CARE, collect, harvest) against the champion | Solo < **90k**: the controller has failed; hand the prior table and selector to A/B and stop |
| D2 09-25 | Market ladder, shed invariant, endgame liquidation, hire rule. Prior mixture per shop cluster, and the selector. **Noise audit**: paired sd for 1σ steps in each gene. BT round-robin anchors, reused from A's run if it exists | Solo ≥ **140k**. ≥ 90% vs planner (64 games). Margin-probit P(win) vs `farm2945` ≥ 10% over 128 games | Solo < 120k: submit nothing from C and hand over the components |
| D3 09-26 | ES daytime run (about 6 h, about 90 iterations at 4 min each), then overnight continuation. PSRO-lite exploiter | Center gains ≥ **+$2k** paired margin vs the population on **fresh** seeds by iteration 40. ≥ 20% win count vs `farm2945` (128 games) | No gain by iteration 60: freeze the prior-mean θ plus the selector, and use the rest of the time for executor KPIs |
| D4 09-27 | Continue ES. Per-cluster offsets only if D3 showed signal. SPRT accept on fresh seeds. 800-game validation vs the population and `v7_endgame`. Timing and crash soak (2k games, < 50 ms per turn) | §5 thresholds | |

09-28 to 09-30 is buffer. Submitting is the user's decision.

## 5. Staged targets as win rates

The cut-offs come from the leaderboard snapshot that A and B each downloaded: top 50% = 765, top 25% = 1,577, top 12.5% = 2,246. Anchors: planner 499, `farm2945` ~2,065, `hybrid2965` 2,370, v7 ~2,640. Win rates use an Elo-400 logistic and are recalibrated by the BT round-robin.

**Small win rates are estimated by a margin probit**, P̂ = Φ(mean margin / sd) from paired games, because counting to 6% cannot be resolved (B's point). Counts are used from 20% upward.

| Target | vs planner | vs `broker_bea` | vs `farm2945` | vs `hybrid2965` | vs `v7_endgame` | Solo proxy |
|---|---|---|---|---|---|---|
| Top 50% | ≥ 82% (count) | ≥ 30% | – | – | – | ≥ 100k |
| Top 25% | ≥ 99% | ≥ 60% | P̂ ≥ 6% | – | – | ≥ 140k |
| Top 12.5% | 100% | ≥ 95% | ≥ 74% (count, 128+) | ≥ 33% | P̂ ≥ 9% | ≥ 165k |
| Beat the champion | – | – | – | – | > 50% over 800 games, SPRT | |

We also report the census-weighted and the uniform population win rates, because this ladder of near-clones is not transitive.

## 6. Risks and why this route

1. **The controller does not close 73k → 140k in two days.** This is the biggest risk and the one A and B both named. Mitigations:
   - D1–D2 build nothing else, and ES is not built until the controller passes.
   - Hard KILL gates at 90k and 120k.
   - The KPI census against the champion is taken every build (movement share, CARE, escapes, weeds).
2. **Search noise.** Mitigations: CRN-paired margin gradients (measured sd $79 on a late knob), d = 12, the D2 noise audit with an irace fallback, win-count SPRT on fresh seeds, and a trust region around the prior.
3. **Overfitting to the pool** (Halite IV). Mitigations: a 50/50 census/uniform population, a PSRO-lite exploiter, fresh-seed acceptance, and a trust region.
4. **Closed-loop tracking still misses reactivity** (market front-running, the opponent's shop race). Mitigation: θ switching at event boundaries, and a check that the pool's `front_run` and market-ledger estimator cannot exploit our sell ladder (from v1's b3; A asked to keep it).
5. **The Elo mapping is wrong.** Mitigations: BT round-robin anchors, and the margin probit for small win rates.

**Honest odds, revised down:**
- Top 50%: about 55%, conditional only on D1 passing.
- Top 25%: about 30%.
- Top 12.5%: about 12%.
- Beating v7 head-to-head in 4 days: under 5%.

**Why this route rather than A or B.**
- A **hand-values** projects (NPV knapsack) and tunes about 15 knobs with SPSA. C instead **learns the plan distribution** from outcome-weighted lineage statistics and searches it per shop context. The unit of choice is the whole plan, which the 41-route meta shows is where the strength lies, whereas A's unit is an individual knob.
- B clones per-turn decisions of a teacher whose actions change on up to 38% of turns with the opponent (probe above). Its oracle gate has to survive that.
- C's learning signal needs neither a value function nor per-turn labels. CRN on a deterministic simulator makes its paired comparisons more than 100× less noisy than raw games, as measured today.
- The deliverable is readable: a table of shop cluster → θ, and a controller of about 800 lines.

## Changes from v1

**Accepted (verified):**
1. **The executor was the planner scheduler, which is the proven bottleneck** (A and B). It is replaced by a new layout-first day-program controller with repair, which gets two full build days and hard KILL gates at solo 90k and 120k. Supporting evidence: our own old ES (`tuning/log.jsonl`) moved the planner's margin from $3.0k to $36.8k and still capped near 500.
2. **v1 was open-loop by construction** (A and B), and the claim of "one plan decision at step 144" was wrong. My probe measured 2–38% of v7's turns changing with the opponent, first divergence at step 151–396, which is consistent with B's 9–18%. θ is now a set of targets tracked in closed loop, plus re-selection at event boundaries.
3. **The fresh-plant weed mechanic** (A). Verified at `kaggriculture.py:222` (`consecutive_unwatered: 1`, "planting day counts as unwatered") and `:783`. A fresh plant dies after one missed watering. Hence the `PLANT_WATER` program.
4. **The recognition test (a)–(c) was a clone's acceptance test** (A and B). It is deleted, together with the MDL cap, Sequitur and phrase replay. The lexicon is now a census of template *families*. No recorded sequences or coordinates are stored.
5. **Win-count ES has no signal** (A and B). Measured: 0 of 48 winners flipped under a real knob change. The gradient now comes from CRN-paired `tanh(m/1e4)`, d fell from 40 to 12, and win count is used only for SPRT acceptance.
6. **D1 and D2 were overloaded** (A and B). D1 is now the controller plus a passive logger. The classifier is not re-solved; E2's tag is reused (A).
7. **"Invert traces into θ" was ill-posed** (A). Every gene is now an observable farm statistic, so extracting the prior is measurement.
8. **The D2 gate of ≥ 40% vs `farm2945` was a top-12.5% bar** (A). D2 now gates on solo ≥ 140k and a margin probit ≥ 10%.
9. **≥ 6% cannot be measured by counting** (B). Small win rates are now estimated by the margin probit.
10. **Population weights rested on a 14-game census** (A and B). The mix is now 50% census and 50% uniform, and it is upgraded if `data_audit` supplies a larger census.
11. **ES froze the machine** (B). It is now capped at 6 of 8 threads.
12. **Weak external precedents** (B). The OscarLegoupil and sidhulyalkar citations are now labelled "pattern only" and "warning".
13. **Linguistics was decorative** (A and B). Four rows are dropped. Three remain, each tied to an operation.

**Stolen ideas:**
- From A: a solo-bank ladder with KPI census gates (CARE, collect, harvest, movement share, escapes, weeds); Fishtest GSPRT acceptance; the BT round-robin calibration; `broker_bea` as a mid-rating anchor; and the irace racing fallback.
- From B: AWR-style outcome weighting of the demonstration data, applied here to the θ prior; the shed + hands ≤ margin invariant by hour 22; and the rule that ES runs only over a few dimensions, where a low-dimensional search has signal.

**Rebutted (with evidence):**
- **"ES signal-to-noise is hopeless at this budget"** (A, fatal 4). It is true for a win-count reward and false for a CRN-paired margin reward. Measured: the paired sd is $79 against a per-game sd of $9,035. Precedent: our own antithetic-CRN ES improved margin more than 10-fold in 12 generations. The residual risk (early-game chaos raising the paired sd) is measured on D2, and there is a fallback if it is too high.
- **"Mimicking aurax7 has no value; that family lost both its games at 2640"** (A). Agreed, and the design no longer mimics anything. The prior is outcome-weighted across all lineages, including the top-2 branch that won by $14k.
- **"The step-144 router is a clone of the tape selector"** (implied by B). The router decision at step 144 is real; A verified `_router` and `_R108_SHOP_ROUTES`. Conditioning a plan on the revealed shops is the natural decision point of this game, not copying: any agent must commit its layout around then. What v1 got wrong was claiming that the router was the *only* decision, and that is now fixed.
