# Track A v2: top-down narrowing (a from-scratch "Steward" agent)

The identity is unchanged from v1. The agent is our own principled, value-based rule agent (L1). Its economy managers follow TacTex: predict first, then optimize (L2). Knobs are tuned by racing and sequential tests on paired seeds (L3). The agent contains no tapes and no copied route code. We may learn *plan shape* and KPI targets from the champion's behaviour, which the rules allow.

v2 makes four changes. The **gates are now head-to-head from day 1**. The **scope is cut to a minimum viable agent** with an early kill. **Throughput uses measured figures** for champion-grade games. The **shed and turn-order details** are pinned to the interpreter source. Section 7 lists every change.

All numbers were measured on this machine on 2026-09-23 unless marked as an estimate.

## 0. Diagnosis that drives the design

### 0a. Production gap (v1 measurement, kept)

Solo bank against the passive `fallow_finn`, 8 games, seeds 900+:

| agent | solo bank | ladder rating |
|---|---|---|
| our planner `agents/main.py` | 73k | ~500 |
| `refagents/broker_bea` (meta tape) | 164k (manifest) | unknown |
| `submissions/v7_endgame.py` | 170k | ~2640 |
| `pool/farm2945.py` | 173k | ~2065 |

Unit-op census, seed 901, each agent against the passive opponent:

| | champion | planner |
|---|---|---|
| CARE | 410 | 83 |
| COLLECT_FERTILIZER | 372 | 60 |
| HARVEST | 490 | 220 |
| movement share of unit ops | 50% | 64% |
| herd | 6 cows, 6 sheep, 5 geese, steady from day 12 | cows fall from 5 to 2 (escapes) |
| weeds by day 28 | 0 | 15 |

This census is one game against a passive opponent. v2 re-runs it on D1 over 16 seeds, both solo and head-to-head against `v7_endgame` (section 4). It is used only as a **body KPI**, never as a strength measure.

### 0b. New in v2: solo bank is not strength; head-to-head is

- **Local results for `v7_endgame`** (8 seeds × 2 seats per opponent, seeds 5100–5107 and 5200–5207):

  | opponent | ladder rating | wins | mean margin |
  |---|---|---|---|
  | `farm2945` | ~2065 | 0/32 | −4.4k and −4.8k |
  | `hybrid2965` | 2370 | 14/16 | +10.2k |
  | `aurax7_v7` | – | 12/16 | ~0 |
  | `broker_bea` | – | 16/16 | +51k |

  The agent rated 2640 loses every local game to the agent rated 2065. **Win rates here are strongly intransitive.** No single opponent can serve as a rating yardstick, and every per-opponent row in v1 §5 was unsound.
- **Ladder data** (`zero2one/data_audit/raw`, 175k public agent-rows since 09-10, engine 1.32.7):
  - The median final bank is flat at about 93–96k in every rating band from 765 to 3,200.
  - Agents rated 765–1,577 are also lineage-shaped: median 33–37 strawberry plants and a peak crew of 12, the same as the top bands.
  - Median |margin| is $3.4k, and 25% of games are decided by less than $1k.

  So the ladder in the 765–1,577 band is mostly **weaker executions of the same plan**, not a different population. Bank level does not map to rating. Only the win rate against a calibrated population does.
- **Consequence.** Every GO gate in v2 is a win rate or a BT rating against a fixed **gate panel**, both seats, on paired seeds. Solo bank survives only as a 2-minute smoke test and a body KPI.

## 1. Lineage of philosophy (unchanged sources; application narrowed)

**L1, general baseline: a principled rule agent with explicit value functions and greedy task matching.**
- teccles won Halite III with one economic value formula and "ships claim their favourite targets… nearer a target get priority". It was tuned by hand, by A/B runs and with CLOP, and "the key skill… was analysing replays". https://github.com/teccles-halite/halite3-bot
- Lux S2 1st place: a pure-Python agent with forward simulation. https://github.com/ryandy/Lux-S2-public
- Halite IV 4th place: rules plus linear-sum assignment. Its evolutionary tuner failed from "symmetry, overfitting and little noise", and v2's panel is built against exactly that. https://github.com/0Zeta/HaliteIV-Bot
- A rule-based bot built in 3 weeks reached the top 6% in Halite II. https://muetsch.io/halite-a-rule-based-ai-bot.html

**L2, economy and market: TacTex-05, champion of TAC SCM 2005.** https://www.cs.utexas.edu/~dpardoe/papers/AAAI06.pdf
- Predictive models are kept separate from optimizing managers.
- A greedy scheduler fills the highest-value orders first.
- Endgame: "reserve only as many computers for the final few days as it expects to be able to sell at high prices".
- The constrained input dominates. For us, that input is labor-hours plus shed slots.
- Liquidation into an impact curve is split over turns, following Almgren and Chriss. https://www.smallake.kr/wp-content/uploads/2016/03/optliq.pdf

**L3, Kaggriculture tuning.**
- Fishtest SPSA for continuous knobs.
- **GSPRT for every accept/reject decision**: elo0 = 0, elo1 = +30, α = β = 0.05, pentanomial on seed pairs. https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-Mathematics.html
- irace-style racing for structural variants, where elimination is itself a GSPRT and never a fixed small batch. https://mlopez-ibanez.github.io/irace/

**What is learned from data, and what is not.** The replays and a D1 teacher census of `v7_endgame` give **plan-shape priors** and **KPI targets**:
- herd size by day
- strawberry and wheat tile counts
- quadrant buy days
- hands by day (tapes average 8.9 and peak at 12)
- carrot-finale timing
- CARE, COLLECT and HARVEST counts

No action sequence is copied. v1 said imitation learning "needs scale we lack". B measured about 2,100 labelled teacher games per hour on this machine, so that claim is withdrawn. The reason A does not imitate is **identity** (an own-logic agent), not infeasibility.

## 2. Core design

### State (rebuilt each turn, about 5 ms)

- **Farm model:** per tile, crop age, yield so far, watered and fertilized state. Per animal, next production day, `pending_care_bonus`, `consecutive_unfed`.
- **Exact market model:**
  - `MARKET_PARAMS` curves
  - town drain per product per turn, from the town centre and each unlocked shop instance
  - the interpreter's unit-by-unit lockstep fill: both players' quotes at pre-sell inventory, and buys quoted at post-buy inventory

  On D1 it is checked equal to `market_price` on 1k random states.
- **Opponent flow model (revised).** C pointed out that opponent money deltas mix sales with buys and hires. v2 infers flows from the **public market inventory**: opponent net flow per product = Δinventory − town drain − our own fills. The result is exact per product and nets out their buys.

  Their visible tiles forecast future harvest volume. E5 showed that the pool's own estimator barely matters, so this model is D3 scope and optional. The market layer must pay without it.

### Tactical scheduler (L1, every turn): the "body", built first

**Jobs**, each with a value and a deadline:
- WATER: value is what the crop loses on a second miss
- FEED: two misses cause an escape
- CARE: value is one more unit at the next production (3 milk vs 1, 4 wool vs 1)
- COLLECT_FERTILIZER: about $60–100
- HARVEST: at the yield cap or the animal's `max_held`
- PLANT, BUILD, DIG weed, PICKUP, PLACE, DROP

**Assignment:** greedy on value per travel-turn, nearest unit first (teccles).

**Layout** is fixed:
- Animals sit on a ring next to the shed, so feed pickup and drop are short trips.
- Crops go in contiguous rows swept in a serpentine.

**Body KPIs**, checked every build: CARE, COLLECT and HARVEST counts at ≥ 90% of the teacher census, movement share ≤ 50%, 0 escapes, ≤ 2 weeds.

### Plan (TacTex supply/demand managers), in two tiers

1. **Tier 1 (D1, required): a parametric template** fitted to the teacher census. It is a plan shape with about 12 parameters:
   - cows, sheep and geese by day
   - strawberry block size
   - wheat feed rows
   - quadrant buy days
   - hands curve
   - carrot-finale start

   The template is our own data, applied by our own executor.
2. **Tier 2 (D3, optional): a marginal-NPV project knapsack** that deviates from the template when the shop state or the opponent's supply changes a project's value. Examples are an extra cow and pasture when a milk shop unlocks, or skipping melon.

   Labor for the n-th hire of the day costs $1, 1, 2, 3, 5, 8, …, which is 144 for the 12th and 233 for the 13th (interpreter `_hire_cost = _fib(n_already_today)`, `_fib(0)=_fib(1)=1`). B's "fib(n−1)" and v1's "fib(n)" describe this same sequence under different indexing. v2 states it explicitly.

   Shed usage is charged against the 100-slot cap. If the knapsack loses its race against the template, the template ships.

### Market layer (L2 plus Almgren–Chriss)

- For each product, the quantity to sell each turn maximises revenue given the curve, the drain refill forecast and the opponent flow.
- Premium goods (milk, wool, strawberry) are held while the drain refills their price.
- Premium goods take the earliest of the 10 order slots.
- **Sells stay in front of the buys they fund.** This is closer_cleo's lesson: a hoisted sell can leave a later wheat buy unfunded.
- Wheat and fertilizer are bought in the cheapest forecast window.

### Shed guard, pinned to the interpreter

Four facts from `kaggriculture.py`:
- Unit actions, including a shed DROP, resolve **before** `_process_market` in the same turn (L935–941).
- A DROP is capped at the free room (L401–404).
- SELL draws **only** from the shed (`_commit_unit`).
- The end-of-day drop is also capped, and it discards the overflow.

The rules that follow:
- A DROP and a SELL in the same turn works only if room exists.
- When the shed is full, SELL at turn t and DROP at t+1.
- The guard projects shed + all unit inventories + pending harvests, and holds that total at ≤ 100 − margin by hour 22. It does this by selling one turn ahead and leaving harvestable produce in the field.

This is E6b's lesson, as C asked. E6b failed because it sold from the shed while the overflow sat in units' hands.

### Endgame (TacTex reservation rule plus the documented late-game rules)

- The last useful plant or buy day for each project is computed backward from step 718.
- **VT1** (2945 digest): skip CARE on day 28, because no production refresh follows day 29. On day 29, hire no hands unless wool is waiting.
- **CAPHARV**: harvest before a production that would overflow the held cap.
- Liquidation is split over the final turns to the depth the curves absorb.

Two negative results sit against this. The README records that grafting our planner's late game onto a *tape body* lost at every switch point. E4 records that `v7_endgame` already retuned its late gates. v2 therefore does not claim to beat the tape's endgame. It must beat **its own body's** naive endgame by ablation (GSPRT), and the E4 finding that the lineage bleeds money on days 26 and 28 marks where to look.

### Budget

Under 50 ms per turn against a 1 s `actTimeout`. Stdlib only. On any exception, a fallback feeds and waters.

## 3. Data and compute (re-measured)

| item | measurement |
|---|---|
| champion-grade games, 8 workers | 64 games in 91 s ≈ **0.70 games/s ≈ 2,500 games/h**. v1's 1.9/s mixed in cheap planner games and is withdrawn. |
| realistic 4-day budget | about 25k games/day alongside development, about 100k in total |
| GSPRT cost | elo1 = +30 needs about 500–800 games, about 15 min, so about 3 per hour. Coarse gates use elo1 = +60 at about 150–250 games. |
| gate panel sweep | 14 opponents × 8 seeds × 2 seats = 224 games ≈ 5.5 min |
| ladder dataset | 219k episodes, 391k seat-feature rows, teams snapshot. Cut-offs: **top 50% = 765, top 25% = 1,577, top 12.5% = 2,246** |
| replays | 52 ladder replays (1.6 GB) + 8 top episodes. Used for plan-shape priors only. |

Compute is sufficient if every gate is sequential. Development time remains the binding constraint.

## 4. Four-day build (every evaluation paired: same seeds, both seats)

**Gate panel P, 14 agents:**
- authored references: `rotation_rosa`, `homestead_hana`, `melon_mateo`, `rancher_rita`
- meta-plan references: `broker_bea`, `slotter_silas`, `closer_cleo`
- our planner: `agents/main.py`
- public pool: `v56`, `morewheat`, `farm2945`, `hybrid2965`, `aurax7_v7`, `v7_endgame`

**D1 calibration.** A BT round-robin over P takes about 1.5k games, about 40 min, run in the background. It is anchored by least squares on ladder ratings for the planner (499), `farm2945` (2,065), `hybrid2965` (2,370) and `v7_endgame` (2,640). The fit reports residuals, and the `farm2945` residual will be large. A candidate's "panel rating" is its BT rating from a 224-game panel sweep, with a bootstrap 95% CI.

Rating results are also shown as **census-weighted win rates**, using C's weights: fork family 11/14, aurax7 2/14, other 1/14.

| day | build | GO gate | KILL |
|---|---|---|---|
| D1 (09-24) | Teacher census of `v7_endgame` (16 seeds, solo and vs itself) giving plan shape and KPI targets; market model check on 1k states; body (world model, jobs, assignment, layout); Tier-1 template; naive sell-down; panel calibration in the background | Smoke: solo ≥ 110k (8 seeds, 2 min). KPIs: CARE/COLLECT/HARVEST ≥ 90% of teacher, movement ≤ 50%, 0 escapes, ≤ 2 weeds. Head-to-head: GSPRT (elo1 = +60) passes vs the planner and vs `rancher_rita`. | Solo < 95k or KPIs < 75% of teacher at end of D1: fix the body only on D2 morning. If still failing at D2 noon, stop and hand the body KPIs and census to B and C. |
| D2 (09-25) | Market layer (split liquidation, slot order, funded buys), hiring by marginal job value, shed guard, endgame reservation plus VT1/CAPHARV, ablation of each | Panel rating ≥ 900 with lower CI ≥ 765 (**top-50% gate**). GSPRT (elo1 = +60) vs `broker_bea` shows ≥ 50%. | Panel rating < 700 at end of D2: stop and hand off. |
| D3 (09-26) | Tier-2 knapsack vs template; opponent flow model; racing of 6–8 structural variants (layout ring vs rows, sell-hold policy, hands curve, knapsack on/off) with GSPRT elimination only | Panel rating ≥ 1,577 with lower CI ≥ 1,400 (**top-25% gate**); census-weighted win rate ≥ 25% | No variant beats the D2 best by GSPRT: freeze D2 and spend D4 on SPSA only |
| D4 (09-27) | SPSA over about 10–12 continuous knobs against the panel mixture; GSPRT accept on a fresh seed range; 2k-game crash and timing soak | Panel rating ≥ 2,246 (**top-12.5% gate**). Stretch: GSPRT vs `v7_endgame` ≥ 50% on 800 fresh games (**beat champion**). | none: D4 selects the final candidate |

D5–D7 are a buffer for the cross-track battle.

**Cut order if behind schedule.** Drop in this order: the opponent flow model, then the Tier-2 knapsack (the template ships), then SPSA (race only). The body, market layer, shed guard and endgame are never cut.

**Why this attempt differs from the planner that stalled near 80k.**
1. The planner searched tile plans on about a day of work (B's fairness note). v2 **fixes the plan shape from the teacher census** and spends D1 entirely on execution.
2. The failure modes are itemised and measurable: CARE 83 vs 410, escapes, weeds, 64% movement. Each has a KPI gate.
3. The downside is capped. A hard kill at D2 noon or at D2 end limits the loss to 1.5–2 days, and the body KPIs and census tooling transfer to B's oracle test and C's executor.

## 5. Staged targets

The v1 per-opponent Elo table is **withdrawn**. Its rows contradicted its own D4 gate, the ">= 6% vs farm2945" row could not be measured at its sample size, and the measured 0/32 of v7 against `farm2945` shows no single-opponent yardstick is valid.

| target | ladder rating | v2 criterion |
|---|---|---|
| top 50% | ≥ 765 | panel rating ≥ 900, lower CI ≥ 765 |
| top 25% | ≥ 1,577 | panel rating ≥ 1,577, lower CI ≥ 1,400; census-weighted win rate ≥ 25% |
| top 12.5% | ≥ 2,246 | panel rating ≥ 2,246, lower CI ≥ 2,000 |
| beat the champion | – | GSPRT (elo0 = 0, elo1 = +30) accepts vs `v7_endgame` on fresh seeds, both seats |

Caveat: the panel is lineage-heavy. The ladder data suggests that suits the 765–1,577 band, which is lineage-shaped. The anchors carry large residuals under intransitivity, so every reported rating comes with its CI and the anchor residuals.

## 6. Top 5 risks and mitigations

1. **The body does not reach teacher-level execution in time.** This is the main risk and the reason the planner failed. Mitigations: plan shape fixed from the census; KPI gates on D1; kill at D2 noon; body tooling reusable by other tracks.
2. **Good production, lost head-to-head.** This is `broker_bea`'s failure mode (it loses 16/16 to v7 by 51k). Mitigations: the gates are head-to-head from D1; exact market model; funded slot order; the shed rule pinned to the interpreter.
3. **Calibration error from intransitivity.** Mitigations: a 14-agent panel with authored agents at the low end; least-squares anchors with reported residuals; census-weighted win rates alongside; CIs on every gate.
4. **Overfitting and low power.** Mitigations: GSPRT for every accept/reject, including racing eliminations; fresh validation seeds; a panel mixture rather than a single opponent; both seats. This follows Halite IV and our 40-game reversal.
5. **Timeouts and crashes on the ladder.** Mitigations: a 50 ms budget, stdlib only, try/except with a feed-and-water fallback, and a 2k-game soak on D4.

**Why this route rather than B or C.** A is the cleanest "0 to 1": our own logic, readable, with no learned policy and no grammar derived from the tapes. The diagnosis is explicit and mechanical, so each engineering day maps to a KPI.

B and C both still depend on a working executor, and on teacher or phrase fidelity from an open-loop tape lineage. A stakes everything on that executor directly, with the earliest kill of the three tracks.

**Honest expectation (lowered from v1):**

| outcome | probability |
|---|---|
| top 50% by D2 | about 55% |
| top 25% by D3 | about 30% |
| top 12.5% by D4 | about 12% |
| beating `v7_endgame` head-to-head in 4 days | < 5% |

## 7. Changes from v1

**Accepted (verified):**
- **Solo bank is not a gate** (B, C). Verified by v7 0/32 vs `farm2945`, and by ladder banks flat at 93–96k across bands. All GO gates are now head-to-head or panel-BT from D1. Solo bank is kept as a smoke test and KPI only.
- **The v1 win-rate table was inconsistent and unmeasurable** (B, C). Withdrawn and replaced by panel-BT gates with CIs (§5).
- **Scope does not fit 4 days** (B, C). The build is cut to body plus template on D1, with the knapsack and opponent model optional. The cut order is explicit, and D1/D2 kills are added.
- **Throughput overstated** (C). Re-measured at 0.70 games/s champion-grade; budgets and GSPRT counts recomputed.
- **Low-power racing** (B, C). All eliminations and accepts now use GSPRT. The fixed 16- and 64-game batches are removed.
- **One-game census** (B). Re-run on D1 over 16 seeds, solo and head-to-head, and used only as body KPIs.
- **Opponent sales from money deltas are confounded** (C). Replaced by public market-inventory differencing, and demoted to optional (E5).
- **Shed turn-order detail** (C). Verified in interpreter L935–941 and L401–404 plus `_commit_unit`. The rule is sell one turn ahead, then drop.
- **Endgame negative result** (C). v2 claims only to beat its own naive endgame by ablation, and imports VT1 and CAPHARV.
- **Imitation-learning scale claim wrong** (B). Withdrawn. The reason for not imitating is identity, not feasibility.
- **Calibration before the BT fit** (B). The gates are defined in panel-BT units; no Elo mapping is needed before D1.

**Rejected or clarified:**
- **"Hire cost is fib(n−1), not fib(n)"** (B, minor). Same sequence, different indexing: `_fib(0)=_fib(1)=1` and cost `= _fib(n_already_today)`, so hires cost 1, 1, 2, 3, 5, … (12th = 144). v1 was correct under standard indexing; v2 states the sequence explicitly.
- **"A repeats the approach that already failed, with no reason it would work now"** (C). Partly rejected. The prior attempt was about one day of plan search. v2 fixes the plan from the teacher census, puts itemised, measured execution defects behind KPI gates, and caps the loss with a D2-noon kill. The residual risk is accepted as risk #1.
- **"Low-band cut-offs sit in a non-lineage population that A never samples"** (C). Largely rejected on evidence. Ladder agents rated 765–1,577 show the same plan signature (median 33–37 strawberries, peak crew 12) as the top bands. The panel also adds four authored low-end agents to resolve that range.

**Ideas taken from rivals:**
- the oracle-style teacher census as the D1 plan-shape source (B)
- census-weighted population win rates (C)
- D1 BT round-robin including the refagents (B, C)
- funded sell/buy slot order (closer_cleo, via the refagent manifest)
