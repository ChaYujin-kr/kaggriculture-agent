# Critique of Track D (Weirdo Zoo), by Track A (narrowing)

Reviewer stance: Track A believes the fastest route to ladder strength in 4 days is a single agent that best-responds to a known, near-static population, with every accept or reject made by a sequential test. D's archive of diverse farms is judged against that standard. Every number below was re-measured on 2026-09-23 unless it is cited to a file.

Scripts I re-ran (read-only; all outputs are quoted here):
- the `data_audit/raw` pairwise stats, with a rating-controlled logit
- `.venv/.../kaggriculture/kaggriculture.py` (engine 1.32.7) for the market and shed mechanics
- `submissions/v7_endgame.py` L1197-1300

---

## 1. Fatal flaws

### F1. D's two headline "weird" signals are a layer our champion already runs

D §0 says that "the seat with more tomato plants wins 64%" and "the larger peak crew wins 64.5%" set the descriptor axes, and it presents tomato as uncontested revenue that the meta ignores.

- **What `v7_endgame.py` already does.** L1197-1300 hold `EXP-155 / V219: a finite late tomato investment with dedicated, observed workers`. When a PIZZA_SHOP or FARMERS_MARKET unlocks, it:
  - buys land
  - buys `['BUY_SEED','TOMATO',10]`
  - hires 1-3 extra crop workers
- **The ladder data carries that layer's exact fingerprint.** Among the 1.32.7 seats rated at least 2300 (09-13..09-22):
  - 16.7% of seats have any tomato at all, and 2,322 of those seats have **exactly 10** tomato plants. The next most common count is 2, with 35 seats.
  - In the 430 games where tomato counts differ, the seat with more tomato also has the larger peak crew 66% of the time. Crew is tied in another 19%.
  - Of the 1,970 games where crew differs, 1,622 differ by exactly **one** hand.
- **What this means.** Both signals mostly measure one thing: whether the V219 reactive layer fired. That layer is a lineage feature. It is not a deviation from the lineage, and our champion already has it.
- **I replicated D's numbers**, so they are not fabricated:
  - crew: 64.5%, n = 1,970
  - tomato: 64.0%, n = 430
  - within the same opening (same h48): crew 64.7% (n = 312), tomato 84% (n = 50)
  - with a rating-gap control, both stay significant: crew β = 0.48, p = 1e-18; tomato β = 0.38, p = 0.001
- **The problem is the interpretation.** The "right direction" D wants the zoo to find is a place the champion already occupies. The graft body's "side plot on unused tiles (tomato, egg, carrot niche)" plus "extra hands" genes largely re-implement V219. Worse, they compete with V219 for the same spare land, worker indices and 10 order slots.

### F2. The go/kill gates cannot tell a real gain from noise

Assume a graft gene with no real effect wins 50% against the O mix.

| Gate | Chance one null candidate passes | Chance that at least one passes across the candidates D will test |
|---|---|---|
| D2: ≥ 56% at 64 games | 19% | 98.6% for 20 candidates; about 100% for 50 |
| D3: ≥ 58% at 128 games | 3.2% | 15% across the top-5 cells |

So the D2 GO gate is almost guaranteed to fire. D2 KILL ("no graft elite > 52% at 64 games") is almost guaranteed *not* to fire.

- **The archive makes this worse.** MAP-Elites keeps the maximum of noisy evaluations per cell, so every elite is a winner's-curse draw. Flageat & Cully, "Uncertain Quality-Diversity" (https://arxiv.org/abs/2302.00463, opened), state the problem directly: "the limitation of MAP-Elites in uncertain domains". D cites neither this paper nor any fix for it, such as re-evaluating elites or deep-grid averaging.
- **The effect sizes involved are small.** Graft genes move margins by about $1k (D's own §5). NOTES E4 shows a real, submitted improvement moving pool wins from 65/80 to 71/80, about +7.5 pp. A 5 pp effect needs about 400 games at 2 SE.
- **So the racing schedule is mostly selection on noise.** It screens at 4 games, promotes the top 20% to 16 games, and the top 5% to 64.
- **What would fix it.** Only D4's accept rule (BT at least champion + 30, with the CI lower bound above the champion) is sound. D should replace D2 and D3 with a GSPRT, at elo1 = +30 to +60, on seeds the search never saw.

### F3. The compute budget is overstated by about 2-5x, and QD needs budget most

D §3 turns "2-3.5 games/s" into 8-12k games/h, about 150k/day, and about 20k evaluations per day.

- **The 2-3.5/s figure is fastsim with cheap agents.** Track A measured champion-grade games at **0.70 games/s** on 8 workers (A v2 §3).
- **D's own single-core table agrees with A:**
  - v7 vs `farm2945` costs 6.1 s per game, which is about 1.3 games/s on 8 cores.
  - The graft body is v7 plus a layer, and 40% of its opponent weight is the v7 mirror.
- **A realistic budget:**
  - 2.5-4.7k games/h, or 40-75k games/day at 16 h
  - fewer if development shares the cores
  - about **6-10k evaluations/day** at 7 games each, and far fewer with honest racing
- **Spread over the grid,** a 384-cell archive gets about 15-25 evaluations per cell per day. That is too few for QD's stepping-stone benefit, which needs many generations, to appear inside 4 days.

---

## 2. Serious issues

### S1. Diversity does not buy win rate against a fixed population

- **What the ladder is.** For 4 days the ladder is a near-static population: 11/14 fork-family at our rating (NOTES ladder census).
- **What BT pays for.** BT rewards the expected win rate against that population. That makes the objective a **best response to an empirical mixture**, which is a single-objective search. D's O-mix fitness is exactly that. The archive, novelty weight and gallery add cost without adding any win rate.
- **Where D's cited sources apply.** PSRO, AlphaStar leagues and POET matter when opponents *adapt*, or when you need a robust Nash mixture. Neither applies to a single submission rated against a ladder that will not re-train in 4 days.
- **The intransitivity point cuts the other way.** v7 goes 0/32 against `farm2945`, but `farm2945`-like agents are rare at our rating. The result is a warning about panel choice, not an argument for population search.

### S2. The wild body is pure cost in a 4-day window

- **What D itself expects.** Scratch farms lose to the meta by more than $100k. Its wild archetype makes 41.7k solo, against v7's 156.8k.
- **What the repo's history shows.** Our own planner took days to reach 73-80k.
- **What D1 would have to deliver.** A new 600-line executor that clears ≥ 50k solo, *plus*:
  - the graft
  - the descriptor extractor
  - the replay-measured sell schedule
  - the gallery

  This is more than Track A v2 was told to cut to.
- **POET-style transfer is implausible here.** "Niche genes" that are optimal for a labor-rich, product-poor 40k farm do not carry over to v7's labor-constrained, shed-constrained schedule.
- **Recommendation:** drop the wild body entirely.

### S3. The descriptor axes are mislabeled or endogenous

- **Niche share.** D calls wheat, carrot, egg and tomato "under-served". The meta median plants **163 wheat and 31 carrot** (D's own §0), and v7 keeps 5 geese for eggs (A v2 §0a census). Only tomato is under-served, and the lineage's V219 layer already serves it when shops appear (F1). The axis mostly measures how much wheat and carrot a farm sells, which is standard meta.
- **Labor intensity** is endogenous. Hires follow the amount of work available, and D concedes this. Using it as a behaviour axis puts products of success, not choices, into separate cells.
- **Measurement noise.** Descriptors are measured from play on random seeds with random shop draws (NOTES E0: shop unlocks are unpredictable). The same genome therefore lands in different cells on different seeds. Flageat & Cully treat this descriptor noise as a separate failure mode, and D has no mitigation.

### S4. The observational evidence is weaker than §7's rhetoric

- **Collider bias.** "Off the top-5 openings vs on them wins 52.6%" (n = 2,329, SE about 1.0 pp) comes from a sample filtered to both seats rated at least 2300. An off-meta seat only survives that filter if it is strong. The comparison also counts any fork whose first 48 steps differ, including the aurax7/top-2 branch, as "off-meta".
- **Post-hoc tails.** "Farms planting 260 or more tiles win 71%" (n = 58) and "land before day 6 wins 65%" (n = 37) have SE of about 6-8 pp and were chosen after looking at the data.
- **§7 drops the caveat.** It cites "64% pairwise wins" as support for weirdness. §0 correctly says these are "not proven levers", and F1 shows they are mostly the lineage's own layer.

### S5. The front-run exploiter is real mechanics with limited headroom, and its gate is mirror-biased

- **The mechanics are correct.** Price depends on cumulative inventory. Town drain is tiny:
  - the town centre takes 1 unit per product per 24 steps
  - each shop instance takes 1 unit per 4 steps (2 for single-product shops)

  Selling k units just before a predictable dump therefore moves revenue from the clone to us, and it needs no inventory purchase. This is not the E1/E5 denial pattern, and D deserves credit for seeing that.
- **Limit: the mirror.** In the mirror (weight 0.4), "the clone's schedule" is our own tape. Front-running it means moving our own sell gates, which E4 already retuned (696→556, 648→518).
- **Limit: the pool already reacts.** Pool agents infer our sales and adjust a sale-timing layer (E5). An earlier sale invites an earlier response, and the equilibrium tends toward "sell early". That gives up the drain refill that shops pay for holding.
- **Limit: the shed.** SELL draws only from the shed, and a DROP is capped at the free room and resolves before the market in the same turn. Front-running needs goods already in the shed a turn early. That adds shed pressure exactly where E6 measured a $0.9-7.5k leak, and E6b showed the guard does not fix that leak.
- **The gate itself.** D3's "≥ 58% vs lineage proxies" is dominated by the v7 mirror. There, a consistent +$500 margin nudge can flip many games decided by < $1k without generalising: E4 gained 40/48 in the mirror but only +6/80 against the pool.

### S6. The graft body's neutrality and desync risk are understated

- **The desync history.** README: raw tapes "score $0 against a live opponent, because the farm desyncs".
- **V219 shows how much protection one layer needs.** It checks the native route's future `BUY_LAND`, `PLANT TOMATO` and `HIRE` indices, the 10-order cap and liquidity before acting.
- **What D would be adding.** The graft adds hires (which shift hand indices and fib hire costs), side-plot seed buys, and changes to lots and floors, all at once. It also only verifies neutrality with the *neutral* genome on 8 seeds.
- **What is needed.** Bit-identity when all genes are neutral says nothing about desync once they are not. Each gene needs its own tape-fidelity check: the share of steps where the native tape action was issued unchanged, across many seeds.

### S7. Citation misuse

- **Minimax Exploiter** (https://arxiv.org/abs/2311.17190, opened) is a game-theoretic *RL* exploiter. It is "data efficient" relative to competitive self-play RL. It gives no support to a "small budget" for D's CMA-ES exploiter.
- **The AlphaStar main exploiter** was built to find flaws in a *learning* main agent. The ladder here does not learn within the window.
- **The Battlecode 2021 and Halite IV cautions** cited by D argue for A's approach: master the meta economy, and use sequential tests.

### S8. The accept rule and counter-probe are underspecified

- **The counter-probe** ("reject if a CMA-ES counter found in 1 h has a genome that already exists on the ladder") has no operational definition of "exists on the ladder". Rejecting on it would also discard candidates for ladder risks that BT already prices in.
- **The "no opponent below 35%" rule** conflicts with the measured v7 0/32 against `farm2945`. The champion itself fails it. As written, the rule is unsatisfiable for any v7 graft.

---

## 3. Ideas Track A would steal

1. **A front-run term in A's market layer.** A already builds opponent flow from market-inventory differencing (A v2 §2). Adding "sell k premium units one turn before the forecast opponent dump, when the drain will not refill before our own planned sale" is a transfer that needs no purchase. A would gate it by GSPRT against the pool, not the mirror.
2. **Reactive finite tomato investment, V219-style, as a Tier-2 knapsack project** in A. It is triggered by PIZZA_SHOP or FARMERS_MARKET unlocks. The data shows the seat that fires it wins about 64%, rising to 84% within the same opening (n = 50).
3. **The liquidation start step and shed reserve as explicit SPSA knobs in A's endgame.** NOTES records a last-day gap of $3.5-13.3k against top teams, the largest measured lever, alongside the shed-overflow leak.
4. **A counter-probe as a robustness check.** Run a short CMA-ES exploiter against A's final candidate, drawing only on ladder-plausible knobs (for example, v7's gate knobs). If a cheap counter exists, report it as a risk. Do not use it to veto.
5. **Behaviour descriptors as KPI telemetry,** not as a search objective: hand-hours per day, the revenue-weighted mean sale step against the lineage's, and niche revenue share. This extends A's body-KPI gates.
6. **A daily gallery-style JSON of candidate KPIs** so the main session can see progress. A would use it without the novelty ranking.

---

## 4. Verdict

- **Drop:** the wild body, the archive and novelty.
- **What survives:** D's graft body plus the exploiter phase, which amounts to targeted layer tuning on v7. That has value, but only with:
  - GSPRT gates on unseen seeds
  - the pool weighted above the mirror
  - per-gene tape-fidelity checks
  - an explicit merge with the existing V219 tomato layer instead of a duplicate side plot
- **As proposed,** D's D2 and D3 gates will report success on noise with near certainty (F2), and its motivating evidence points back into the lineage (F1).
