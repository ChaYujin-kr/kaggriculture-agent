# Track A: top-down narrowing (a from-scratch "Steward" agent)

The design narrows in three steps. The general layer is a principled, value-based rule agent. The economy layer adds TacTex-style predict-then-optimize managers. The Kaggriculture layer tunes with paired racing and SPRT. All numbers below were measured on this machine on 2026-09-23 unless marked as an estimate.

## 0. Diagnosis that drives the design (measured)

Solo bank against a passive opponent (`fallow_finn`), 8 games each, seeds 900+:

| agent | solo bank | ladder rating |
|---|---|---|
| our planner `agents/main.py` | **73k** | ~500 |
| `refagents/broker_bea` (meta tape, used as a reference) | 164k (manifest) | unknown |
| `submissions/v7_endgame.py` | **170k** | ~2640 |
| `pool/farm2945.py` | **173k** | ~2065 |

The gap is mostly in **production**, not in the market. A census of one game (seed 901, both agents against the passive opponent) shows what each agent's units did:

| | champion | our planner |
|---|---|---|
| CARE | 410 | 83 |
| COLLECT_FERTILIZER | 372 | 60 |
| HARVEST | 490 | 220 |
| movement share of all unit ops | 50% | 64% |
| herd | steady 6 cows, 6 sheep, 5 geese from day 12 | cows fell 5→2 (escapes) |
| weeds by day 28 | 0 | 15 |
| land | 3 quadrants | 4 (bought SE for $4k) |

CARE is worth a lot: a cared cow gives 3 milk per production instead of 1, and a sheep 4 wool instead of 1 (research/extracted/the-2945-farm digest). All of the planner's shortfall is mechanical and can be fixed by engineering.

## 1. Lineage of philosophy

**L1, the general baseline: a principled rule agent with explicit value functions and greedy task matching. Learned policies only when there is GPU scale.**
- Halite III winner (teccles): *"kept my bot relatively principled"*. It scores every target with one economic formula, then *"Ships claim their favourite targets… nearer a target get priority"*. It was tuned by hand, by local and online A/B runs, and with CLOP, and *"the key skill… was analysing replays"*. https://github.com/teccles-halite/halite3-bot
- Lux AI S2, 1st of 646 teams: a pure-Python agent with a forward-simulation horizon (`FUTURE_LEN`). https://github.com/ryandy/Lux-S2-public
- Halite IV, 4th place: *"100% rule-based bot with lots of parameters"*, with task scoring solved as a linear-sum assignment. Their evolutionary tuner failed from *"symmetry, overfitting and little noise"*. https://github.com/0Zeta/HaliteIV-Bot
- A rule-based bot built in 3 weeks reached the top 6% in Halite II. https://muetsch.io/halite-a-rule-based-ai-bot.html
- The exceptions need compute we do not have. The Lux S1 RL winner trained on *"an 8-core/16-thread dual-GPU system"* for months (https://github.com/IsaiahPressman/Kaggle_Lux_AI_2021). Kore imitation learning used about 200M tuples on 2×A100 (https://github.com/khanhvu207/kore2022). We have no GPU and 52 replays.

**L2, the economy and market layer: TacTex-05, champion of TAC SCM 2005** (https://www.cs.utexas.edu/~dpardoe/papers/AAAI06.pdf)
- The agent separates **predictive models** (supplier, demand, offer acceptance) from **optimizing managers**. The Supply Manager minimizes input cost; the Demand Manager maximizes profit over a rolling 10-day window. They exchange only projections: component use, and inventory plus *replacement cost*.
- A **greedy scheduler** fills the highest-value orders first. It reserves capacity for *predicted* future demand by simulating it.
- **Endgame:** *"reserve only as many computers for the final few days as it expects to be able to sell at high prices"*. Inventory thresholds fall linearly to 0 before the game ends.
- An ablation found that most of the value came from the model of the constrained input. For us, the constrained input is **labor-hours plus shed slots**.
- Selling into an impact curve follows Almgren and Chriss (https://www.smallake.kr/wp-content/uploads/2016/03/optliq.pdf): split a liquidation over time to trade impact against risk.

**L3, Kaggriculture tuning: race, then SPRT on paired seeds**
- Fishtest uses SPSA with win-minus-loss finite differences and per-axis scales. It accepts changes by GSPRT, which *"stop[s] as quickly as possible"* once the evidence is significant. https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-Mathematics.html
- irace samples configurations, races them with statistical elimination across *instances* (for us, seeds × opponents × seats), and resamples near the survivors. https://mlopez-ibanez.github.io/irace/
- This fits our own history: 40-game trials fooled us, and per-game sd is about $9k.

**How the layers combine:** L1 supplies value-scored jobs with greedy matching. L2 supplies predicted prices and supply and a labor/shed "supply manager" that sets the targets. L3 races the structural variants, then applies SPSA and an SPRT gate to the knobs.

## 2. Core design

**State (rebuilt each turn, about 5 ms):**
- Farm model: per tile, crop age, yield so far, watered and fertilized state. Per animal, next production day, `pending_care_bonus`, `consecutive_unfed`.
- Exact market model: the `MARKET_PARAMS` curves, the town drain per product per turn (town centre 1/day; each shop instance 6/day, or 12 for single-product shops), and the unit-by-unit concurrent fill.
- Opponent supply model: their tiles are public, so their harvest volume by product and day can be predicted. Their `money` deltas confirm what they actually sold.

**Strategic manager (the TacTex supply/demand managers), daily at hour 0 and on each shop unlock:**
- It runs a greedy marginal-NPV knapsack over **projects**, such as "cow + pasture", "sheep + pasture", "goose + coop", "4-tile strawberry block", "wheat feed row", "melon block", "carrot finale" and "buy NE/SW".
- Each project has:
  - capex (seed, animal or land price, plus build ops)
  - daily ops (water, feed, CARE, collect, harvest)
  - wheat feed
  - output units on each future day
  - a price taken from the market model after projected supply from us and the opponent, minus the town drain
- Labor costs the marginal hire, fib(n)/24 per op. Shed usage is charged against the 100-slot cap.
- The priors and warm start come from the replay census (champion: 6 cows / 6 sheep / 5 geese, 33 strawberries, 3 quadrants, a wheat feed loop, a carrot finale). We learn a **plan shape**, not an action tape.

**Tactical scheduler (L1), every turn:**
- The job list carries a value and a deadline for each job:
  - WATER: deadline end of day; the value is what the crop loses if it misses a second day
  - FEED
  - CARE: the price of one more unit at the next production
  - COLLECT_FERTILIZER: about $60–100
  - HARVEST: when yield reaches the cap, or the animal's `max_held`
  - PLANT, BUILD, DIG weed, PICKUP, PLACE, DROP
- Units are assigned by greedy value per travel-turn, with the nearest unit first (teccles).
- Layout is fixed by the planner. Animals sit on a ring of tiles next to the shed, so feed pickup and drop are short trips. Crops go in contiguous rows swept in a serpentine.
- Crew: hire n at hour 0 while the marginal job value exceeds fib(n). KPI: productive ops ≥ 65% of all unit ops.

**Market layer (L2 and Almgren–Chriss):**
- For each product, choose the quantity to sell each turn to maximize revenue, given the curve and the forecast of drain plus opponent supply. Premium goods (milk, wool, strawberry) are held while drain refills the price.
- Premium goods go first in the order slots. Wheat and fertilizer are bought in the cheapest forecast window.
- **Shed constraint:** shed plus unit inventories must not exceed 100. Units DROP mid-day when the projection nears the cap. The E6 leak came from produce still held in units' hands.

**Endgame (the TacTex reservation rule):**
- The last useful plant or purchase day for each project comes backward from step 718, the last step whose actions execute.
- In the final day, CARE is only worth doing where a production still falls inside the season.
- A liquidation schedule sells down to what the final-day curves absorb. Our lineage gains $8.2k on the final day, where top teams gain $3.5–13.3k.

**Budget:** under 50 ms per turn against a 1 s `actTimeout`. On any exception, a fallback feeds and waters.

## 3. Data and compute (measured)

| item | measurement |
|---|---|
| one fastsim game, single thread | 2.3 s (champion vs `farm2945`), 1.4 s (planner vs starter) |
| 8-worker `compare.py` throughput | 120 mixed games in 64 s ≈ **1.9 games/s ≈ 6,700 games/h** |
| data | 52 ladder replays (1.6 GB) + 8 top episodes (258 MB), 16 pool agents, 10 reference-ladder agents |
| leaderboard snapshot 2026-09-23 | 9,883 teams: **top 50% = 765, top 25% = 1,577, top 12.5% = 2,246** |

Compute is not the bottleneck. Four days hold about 250k games, which covers roughly 40 SPRT runs at 2k games each. Development time is the bottleneck. The replays are used for plan-shape priors and op-mix KPIs only; no model training.

## 4. Four-day build (all evaluations paired: same seeds, both seats)

| day | build | GO gate | KILL |
|---|---|---|---|
| D1 (09-24) | world and market model (price function checked equal to the interpreter on 1k random states); job scheduler; fixed champion-shaped template; BT calibration round-robin of pool + reference agents, anchored on 499 / 2065 / 2370 / 2640 | solo ≥ 110k (16 seeds), 0 escapes, ≤ 2 weeds, productive ops ≥ 60% | solo < 95k |
| D2 | strategic knapsack, hiring, market layer, shed guard | solo ≥ 140k; ≥ 95% vs planner; ≥ 60% vs `broker_bea` (64 games) | solo < 125k: stop, hand off to the other tracks |
| D3 | opponent supply model, endgame reservation; racing over 8–16 structural variants (elimination every 16 paired games) | ≥ 25% vs `farm2945` or mean margin ≥ −10k (64 games); solo ≥ 160k | < 10% vs `farm2945` |
| D4 | SPSA on about 15 continuous knobs; SPRT accept (elo0 = 0, elo1 = +30, α = β = 0.05) on a fresh seed range, against a *population* | ≥ 50% vs `farm2945`, ≥ 35% vs `hybrid2965` | none: D4 decides the final choice |

Evaluations use the existing `scripts/compare.py` and `roundrobin.py`. Code lives only in `zero2one/A_narrowing/`.

## 5. Staged targets as win rates

Win rates are expected values from an Elo-400 logistic, **an estimate** to be recalibrated by the D1 BT fit. Anchors are ladder ratings from the README. `broker_bea` is estimated at about 1,100–1,500: it beat the planner 7/8 and lost 0/8 to `farm2945`.

| target | rating | vs planner (499) | vs `broker_bea` | vs `farm2945` (2065) | vs `hybrid2965` (2370) | vs v7 (2640) |
|---|---|---|---|---|---|---|
| top 50% | 765 | ≥ 82% | ≥ 30% | ~1% | – | – |
| top 25% | 1,577 | ≥ 99% | ≥ 60–85% | ≥ 6% | ~2% | – |
| top 12.5% | 2,246 | 100% | ≥ 95% | ≥ 74% | ≥ 33% | ≥ 9% |
| beat the champion | > 2,640 | | | | | ≥ 50% |

Solo-bank proxies: top 50% ≈ 100k+, top 25% ≈ 140k+, top 12.5% ≈ 165k+ with a competitive market layer. `broker_bea` shows that 164k solo still loses 0/8 head-to-head to `farm2945`.

## 6. Top 5 risks and mitigations

1. **The labor-packing gap (73k → 170k) does not close in 2 days.** Build the layout-first scheduler; track the op-mix census against the champion every build; use the D2 KILL gate.
2. **The rating mapping is wrong.** Run the D1 BT calibration on the known anchors and re-derive the gates.
3. **Overfitting a one-lineage pool.** Races use a population (pool, reference ladder, planner, mirror), both seats, and a fresh validation seed range. This follows the Halite IV lesson about symmetry and overfitting.
4. **Head-to-head market losses despite good production.** This is `broker_bea`'s failure mode. The market layer uses the exact curves and slot order, and carries in the E4 and E6 findings.
5. **Timeouts and crashes on the ladder.** Keep a hard 50 ms budget, stdlib only, a try/except fallback, and a 2k-game crash soak on D4.

**Why this beats the other routes.** RL, imitation learning and "transplant" routes need scale we lack. The published wins came from dual-GPU months or 2×A100 with about 200M tuples; we have no GPU, 52 replays, and 7 days. PPO-to-heuristic distillation spends days on training infrastructure before it produces a single better game. The diagnosis above is explicit (CARE, escapes, weeds, movement waste), so direct engineering pays from day 1. Rule-based agents won Halite III and Lux S2 outright. Every step here has a measurable gate, and the design keeps our evaluation tooling and findings (E4 endgame, E6 shed, labor costs).

**Honest expectation:** top 25% is likely by D3, and top 12.5% is possible by D4. Beating the champion head-to-head in 4 days is unlikely (<15%).
