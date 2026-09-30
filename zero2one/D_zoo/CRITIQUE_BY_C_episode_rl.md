# Critique of Track D (Weirdo Zoo), by the C_episode_rl advocate

Written 2026-09-23. I checked the mechanic claims against the interpreter
(`.venv/Lib/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py` + `kaggriculture.json`).
`research/rules.txt` is the legal rulebook only and has no game mechanics. I re-ran D's ladder statistics from
`zero2one/data_audit/raw` (read only) and ran one new endogeneity test on `data_audit/turns/*.parquet`.
The scripts are in my scratchpad; nothing in `data_audit/` was modified.

## What I verified and found correct

- **D's pairwise numbers reproduce exactly.** Same filter (engine 1.32.7, 09-13..09-22, both seats rated >= 2300,
  7,741 games). Larger peak crew wins 64.5% (n = 1,970). More tomato wins 64.0% (n = 430). 35.5% of decided games
  are within $1k. D says 38.6%, which is close enough.
- **Hire cost is `farmHandCostMult * fib(n)` with default mult 1** (L690-708, json L69). Hands expire every day (L880).
- **Shed capacity is 100, and the end-of-day drop discards overflow** (L850-858).
- **Monoculture facts.** No seat in the turn sample owns a chicken (geese are the only egg source), median tomato
  plants are 0, and median herd at step 480 is 8 cows, 6 sheep and 3 geese.
- **Citations.** The MAP-Elites, CMA-ME/pyribs, POET, Go-Explore, PSRO and AlphaStar references say what D says
  they say. I spot-checked the AlphaStar exploiter wording and the Halite IV warning, which is the same README I
  cited myself.

## Fatal flaws

### F1. The headline lever, "labor intensity", is an outcome of winning. The data show early extra labor loses.
D states that crew is "partly endogenous" and then makes it descriptor axis 1 anyway, with 8 bins. I timed it.
For each of 1,047 replayed games with a peak-crew difference, I took the first step at which the running peak crew
of the two seats differs:

| First step the crews differ | n | Bigger crew wins |
|---|---|---|
| by step 144 (day 6) | 147 | **34%** |
| 145-300 | 178 | 56% |
| 301-500 | 173 | 75% |
| after 500 | 549 | 67% |

The median divergence is **step 507, which is day 21**. Most of the 64.5% "crew effect" is a winning farm hiring
one more hand late in the game, because it has more to harvest. Among the 1,622 of 1,970 pairs that differ at all,
the difference is **exactly 1 hand**. Where a seat chose a bigger crew *early*, which is the only case where crew is
a decision, it won **34%**.

Hands are close to free: the 13th hire of a day costs $233, and a whole 12-hand day costs $376. If more labor paid,
the monoculture would already hire it. An 8-bin labor axis centred on 12 therefore spends about one third of the
archive on a direction the data mark as harmful (more than 13 hands early) or as pure outcome (late).

### F2. The "niche" story has two data errors, and the full-sample statistic points the other way.
- **Wheat is in the niche basket, but wheat is the meta's biggest crop** (median 163 PLANT actions, versus 33
  strawberry). Carrot (31) is in the meta too. The "niche share" axis mixes feed wheat with real niches, so a
  farm moves along it simply by buying less wheat on the market.
- **"Farms planting >= 260 tiles win 71% (n = 58)" is a cherry-picked tail.** Over the full pairwise sample, the seat
  with **more** `tiles_planted` **wins only 46.7%** (n = 3,346), and 44.3% within the same h48 line (n = 510).
  Note also that `plants_*` counts PLANT *orders*, retries included (`features.py` L76-80). It is not a tile count.
- **"Buy land before day 6: 65% (n = 37)"** has an SE of about 8 pp. It is noise-level, and it rests on post-game
  ratings, since the >= 2300 filter uses `rating_N`, the rating *after* the game.
- **Tomato (64%, n = 430)** is the only candidate that survives the same-lineage check (84%, n = 50). Tomato
  demand exists only through PIZZA_SHOP and FARMERS_MARKET plus 1/day from the town centre, so the effect is
  conditional on shops. Both seats see the same shops, and the reactive layer that plants tomato is a lineage
  trait. It is a real lead, but for **one gene**, not for a 384-cell archive.

### F3. The exploiter's core mechanic is misread.
D §2.4 says "market orders settle one unit at a time, the first unit gets the best price." The interpreter says
otherwise (`_process_market`, L592-640): **both players are quoted the same pre-commit inventory for each unit
index**, in lockstep. Within a turn there is no first mover; a simultaneous sale gives both seats identical
prices unit by unit.

Front-running therefore works only *across* turns, and it is not new:
- The lineage already carries a front-run / sales-ledger layer. E5 used it as the attack surface.
- My divergence probe measured v7's market actions differing on **4-34% of turns** depending on the opponent. B's
  "82-91% open-loop" describes unit actions, not the market layer.

So a "sell one turn before the clone's dump" gene enters an arms race against a reactive estimator that already
exists. It is not a free transfer against a fixed schedule. The idea is still better than E1/E5, because a pure
reordering costs us nothing. But D1-D3 has no gate that checks whether the clone reacts to it.

### F4. The accept rule cannot be met at this budget unless the gain is large.
The D4 rule is BT >= champion + 30 with the 95% lower bound above the champion. +30 Elo is about 54.3%, so the CI
half-width must be below about 4.3 pp. That needs roughly **500+ effective games for the candidate**.

The planned round-robin gives each candidate 26 opponents x 16 = 416 games. Most of those are against pool agents
that are **not** the ladder: the ladder is a monoculture, and farm2945 at ~2065 is rare at our rating. The BT
half-width is therefore about 35-40 Elo. The rule accepts only a true gain of about +40 or more. D's own estimate
is that graft genes "move margins by about $1k", which is a +5 to +15 Elo effect. **The expected outcome of D4 is
"reject", and the reason is statistical power, not the quality of the weirdo.**

## Serious issues

1. **Throughput is overstated about 2x.** D uses 8-12k games/h (from 2-3.5 games/s). Its own table gives v7 vs
   farm2945 at 6.1 s/game/core, which is about 1.3 games/s on 8 cores. I measured 1.04 games/s for champion-grade
   pairings. The graft body costs at least as much as v7, and 40% of the opponent mix is a v7 mirror, so every
   game runs v7 twice. Realistic numbers are about 4-5k games/h. At 7 games per evaluation and 70% of cores on the
   graft, that is about **8-10k evaluations/day, not 20k**.

2. **The fitness signal ignores the one noise fact we measured.** Per-game margin sd is $9k, while the paired
   difference against the *parent on the same seed* is **$79** for a late knob (my `probe_crn.py`, 0/48 winners
   flipped). D pairs seeds but still scores *absolute* win rate plus a 0.05 tanh margin term. A 4-game screen has
   a win-rate SE of about 25 pp, so the screen is a coin flip. Graft cells should be scored by **paired delta
   against the neutral genome** (CRN), with the margin term dominant. Win count belongs only in the final SPRT.

3. **For a single submission, QD buys nothing that CMA-ES does not.** Only the argmax cell is submitted (two final
   submissions at most). The graft genome has about 8 low-deceptive dimensions: lots, floors, extra hands, side
   plot, liquidation step and shed reserve. Novelty search and archives pay off on *deceptive* landscapes. The
   deception D cites ("every scratch farm loses by $100k") applies to the **wild** body, which D itself says will
   not be submitted. On the graft, a 384-cell archive divides roughly 9k evaluations/day into about 23 evaluations
   per cell. That is below the racing ladder's own 64-game bar.

4. **Most graft genes are knobs we have already tuned.** Liquidation start and the late gates are the E4
   submission (`tuning/best_endgame.json`: 556/518). The shed reserve is E6a/E6b, both measured **no gain**
   because the leak is produce *in hands*, not shed stock. Market lot and floor tuning is `thresholds_log.jsonl`,
   166 runs. The new genes are the side plot, extra hands and front-run. F1 and F2 cover the first two, F3 the
   last.

5. **The side plot runs into the shed leak.** Extra tomato, egg or carrot output lands in the same 100-capacity
   shed, and the end-of-day drop that discards overflow is where E6 measured a $0.9-7.5k/game leak. Niche revenue
   competes with premium stock for shed room unless it is sold the same day. The graft needs a "sold before hour 22"
   invariant (B's rule), and D does not have one.

6. **"Uncontested" revenue is small, but some of it is real, and D does not rank it.** From the price curves:
   - Tomato is T = 200 (above sqrt 0.6). Selling 200 units above I0 cuts the price 60%, so it is worth **at most
     about $9k/season**, and less without PIZZA or FARMERS_MARKET.
   - Egg is the deep sink: above **log 0.2** at T = 332, so 332 units cost only 20% of a $50 base. But each goose
     eats about 1 wheat/day (about $25-30), which leaves roughly $15-25 net per egg.

   A two-row price-curve NPV table would pick the niche in an hour. It does not need a MAP-Elites archive.

7. **D1 is overloaded.** Genome schema, the graft layer, a **600-line wild executor**, a descriptor extractor, a
   gallery writer and a replay-derived sell schedule are all due in one day. The wild executor alone is the
   component my track gives two days and hard gates (110k/140k). D gates it at 50k solo and says it is not
   competitive. It costs D1 and 30% of D2's cores with no ranking payoff.

8. **The bit-identical neutral graft is the right test, but its failure mode is soft.** Extra HIRE orders change the
   fib position of the tape's own hires if they are placed before them. They also change `money`, which the
   reactive layers read, and extra hands spawn on the same shed-access tiles (L534-540). The neutral test passes by
   construction (zero genes). The **non-neutral** test is the one that matters: the fraction of v7's own unit
   actions that change when only the side plot is on. D has no gate for that.

9. **The opponent weights are weakly grounded.** O is built from a 14-game census; `data_audit` now has thousands
   of lineage-tagged seats. farm2945 gets 0.15 weight because of a local 0/32 intransitivity, but it is rare at our
   rating. Optimising against it can cost wins against clones, which is the PSRO overfit D itself cites.

10. **pyribs is not installed** (Python 3.13.5; `import ribs` fails). The install is probably fine, but it is an
    unbudgeted D1 dependency (numba and scipy wheels on 3.13/Windows).

## Where D is right, and my track should concede

- A **graft on the champion** is the only 4-day path in any proposal where the floor is the champion rather than a
  scratch controller. C's own D1-D2 risk (73k to 140k in two days) is larger than any risk in D's graft branch.
- D respects E1/E5 better than earlier drafts: it rewards reordering and uncontested revenue, never denial.

## Ideas I would steal for C

1. **Niche genes in θ.** Add a tomato share (conditioned on PIZZA_SHOP/FARMERS_MARKET being revealed, which fits
   C's shop-cluster selector) and a goose/egg count sized by the log-0.2 egg curve. These are the only "weird"
   directions with data support (tomato: 84% within the same lineage, n = 50).
2. **Replay-measured lineage sell schedule** as a feature for C's market ladder, with a gate that measures whether
   the clone's front-run layer reacts.
3. **The neutral-genome bit-identity test** for any layer or θ change, plus an action-diff rate for non-neutral
   genomes.
4. **The counter-probe:** a short exploiter run *against* the candidate, rejecting it if the counter already exists
   on the ladder. This is stronger than C's PSRO-lite, which only trains against our own centre.
5. **Racing** (4 -> 16 -> 64) as the evaluation schedule for C's irace fallback, but with CRN paired deltas.
6. **A behaviour-descriptor archive as a diagnostic, not an optimiser.** Log every ES candidate's (sell timing,
   niche share, capex day) into a heatmap. The search stays a single CMA-ES, but we can see where it went.
7. **The daily gallery JSON and heatmap**, as a cheap visibility layer over C's ES logs, one per day.

## What would make D sound (constructive)

- Drop labor intensity as an axis, or restrict it to **hands before day 6**, and expect it to be negative.
  Replace it with **tomato + egg share**, and take wheat out of the niche basket.
- Score graft cells by the **paired delta vs neutral on identical seeds**. Use win count only in the final SPRT,
  with a pre-registered minimum detectable effect that matches the 416-game power.
- Cut the wild body entirely, or run it only on Kaggle notebooks for the gallery. Spend D1 on the graft plus the
  action-diff gate.
- Test F3 directly: turn on the front-run gene against v7 and log whether v7's sale timing moves. If it moves,
  the gene is an arms race, not an exploit.
