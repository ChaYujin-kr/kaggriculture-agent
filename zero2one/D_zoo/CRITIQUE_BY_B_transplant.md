# Critique of Track D (Weirdo Zoo), by Track B (transplant)

Reviewer stance: B's view is that in a near zero-sum 2-player market full of clones, you win by taking the strongest
known plan and executing it better. Diversity pays only when it shows up as wins against the clones. I re-ran D's
headline statistics, read the engine (`kaggle_environments/envs/kaggriculture/kaggriculture.py`, 1.32.7) and read
`submissions/v7_endgame.py`. Every claim below comes from one of those or from a URL I opened.

## Verdict

- D's **graft body** is a legitimate, cheap experiment. In practice it is structured knob-tuning on v7, run through a
  diversity archive.
- D's **wild body**, **exploiter phase** and **"weirdness wins" thesis** rest on evidence that mostly disappears on
  inspection. The front-run exploit is already in our champion and is currently switched off.
- The gates are too weak for the number of candidates the archive produces, so D will produce false positives.

## FATAL flaws

### F1. The exploiter phase re-invents a layer the champion already has, and that layer is disabled

The claim that selling before the clone's dump is a new, untested edge is wrong. `v7_endgame.py` already contains
these layers:

- `front_run`, described in the file as "sell before the opponent's scheduled SELL", with
  `FRONT_RUN_ITEMS = ("MILK","WOOL","STRAWBERRY","MELON")`. These are exactly D's §2.4 targets.
- `sell_lead`, which sells next step's lots one step early.
- A "Same-Turn Race Escalator" and "2-Turn Advance Sales + Front-Loading", both named in the header.

The shipped settings (line 931) have `'sell_lead': True, 'front_run': False`.

This means:

- The lineage already front-runs by one step.
- The mirror opponent (0.4 of D's O mix) does the same.
- Someone in the lineage had the front-run hook and turned it off.

NOTES E5 also says the opponents run an estimator of our sales that "steers a small sale-timing layer". So D3 is
searching a dimension that has already been explored and tuned, and D's plan has no account of why it was turned
off. **D3 needs to be replaced by a single A/B of `front_run: True` (400 paired games).** It is not a CMA-ES phase.

### F2. The market mechanic D3 relies on is misstated

D writes: "Market orders settle one unit at a time, the first unit gets the best price". The engine's
`_process_market` is a **per-unit lockstep**. For the i-th unit, both players are quoted at the same pre-commit
inventory ("Both players see the same pre-commit inventory for this unit"), and then both commit.

- Within a turn, neither player has priority.
- Front-running only works one or more **turns** earlier.
- Selling earlier gives up the town drain in between: shops consume every 4 steps, the town center every 24.

"Premium goods crash under `above_target` > 1" is true only for inventory **above** I0 = 10,000, which is the glut
side. The move therefore trades a guaranteed early-sale discount against the chance of beating a dump. The lineage
has already priced that trade-off with `sell_lead`.

### F3. The D2 gate will pass pure noise with near certainty (multiple comparisons in a 384-cell archive)

The D2 GO rule is ">= 1 graft elite >= 56% vs the O mix at 64 games".

- A true-50% elite reaches 36/64 or more with probability ≈ 19%.
- Racing sends the top 5% to 64 games. With 20k evaluations/day that is ≥ 20 such elites.
- P(at least one passes) = 1 − 0.81^20 ≈ **98%**.

D3 is only somewhat better. A 58% threshold at 128 games gives a true-50% agent ≈ 3% per cell, so about 15% across
5 cells, and the parents were already selected on those same opponents.

MAP-Elites archives are known to fill with lucky evaluations when fitness and descriptors are noisy:

- Flageat & Cully, *Fast and stable MAP-Elites in noisy domains*, https://arxiv.org/abs/2006.14253
- *Uncertain Quality-Diversity*, https://arxiv.org/abs/2302.00463. MAP-Elites "struggles significantly" under
  uncertainty. Both URLs opened.

D's descriptors are **measured from play**, so a single elite can also land in different cells on different seeds.
The 4-game screen has an SE of about 25 pp, so it is essentially random selection.

**Fix:** use re-evaluated archive entries (deep-grid or re-sampling), and replace the D2/D3 gates with one held-out
test on fresh seeds with a Bonferroni-corrected threshold. Across ~20 candidates that means ≥ 400 games at ≥ 55%.

## SERIOUS issues

### S1. The "deviation wins" evidence is a ±1-hand effect and a lineage route, not weirdness

I reproduced D's numbers on `data_audit/raw` (1.32.7, window 09-13..22, both ratings ≥ 2300, 7,741 games):

- Crew claim: 64.5%, n = 1,970 (confirmed).
- Tomato claim: 64%, n = 430 (confirmed).

The distributions show what the effect actually is:

- **82% of crew differences are exactly 1 hand** (1,622 of 1,970), and 97% are ≤ 2. The median `peak_crew` is 12 in
  every tier (tier means 11.9–12.3, `figs/tier_feature_effect_sizes.csv`). The data supports "a 13th hand
  sometimes", nothing beyond that. The sign of the crew difference correlates with the rating gap (r = 0.21), and it
  is plausibly endogenous: more mature produce leads to one more hire.
- **Tomato differences are mostly exactly 10 plants** (179 of 430). That is a discrete *lineage* route reacting to
  PIZZA_SHOP or FARMERS_MARKET, not an off-meta niche. The clones already sell tomato when a shop demands it, so the
  niche is not "uncontested".
- "Off the top-5 lines wins 52.6%" at n = 2,329 is 2.5 SE, and "off-line" here usually means another h48 prefix
  inside the same family.

In short, the data says that *slightly better execution within the meta* wins. That is B's thesis.

### S2. The labor axis is mostly infeasible (fib hire cost, hands vanish daily)

`_end_of_day` sets `farm["hands"] = []` and `hires_today = 0`, and the n-th hire of the day costs `fib(n)`.

| Crew | Cost per day |
|---|---|
| 12 | $376 |
| 13th hand alone | +$233 |
| 16 | ≈ $2.6k |
| 20 ("Twenty-Hand Circus") | ≈ $17.7k, or ≈ $500k per season |

Banks are ≈ $100k. So an 8-bin labor axis "relative to 12" has about 2–3 bins that can actually be filled
(roughly 10–15 hands). The 384-cell grid is closer to 100 reachable cells, and CVT will waste centroids.

### S3. The niche-share descriptor mislabels wheat and carrot as under-served

The meta plants a median of **163 wheat** and 31 carrot, and it buys wheat for feed. Tomato demand exists only
through the town center (1 unit per 24 steps, about 30 per game) plus randomly unlocked shops. Egg demand exists
only through BAKERY, BRUNCH_SPOT and the town center.

"Uncontested revenue" is therefore small and depends on shop RNG. NOTES E0 found shop draws unpredictable (13.4% vs
12.5%). The descriptor should split by *actual market competition*, measured from replays, not by fixed product
lists.

### S4. The graft's "neutral = bit-identical" test is necessary but not sufficient; non-neutral genes desync the tape through engine couplings D does not list

- **Hand spawn.** `_spawn_hand` places each new hand on the least-occupied shed-access tile given *current*
  positions. An extra hire changes where every later tape hand spawns, so its recorded moves hit different tiles.
- **Atomic PLANT validation.** If PLANT requests for a crop exceed seeds that turn, **all** PLANT requests for that
  crop are dropped, including the tape's. A side plot of carrot or wheat shares the tape's seed pool.
- **Shared shed (100).** Side-plot produce fills the same shed. This makes the known E6 overflow leak
  ($889–$7,450 per game) *worse* for premium produce.
- **Order slots.** There are `maxMarketOrdersPerTurn` = 10 slots, and graft orders compete with the tape's.

There is also a weakness in the seed pairing. Weed spawn draws from one RNG per day, shared across both farms, and
consumes one draw per empty tile of player 0. A seat-0 genome that changes its empty-tile count therefore
re-randomizes the opponent's weeds. The effect is small (p = 0.005), but paired seeds are not perfect CRN.

### S5. The only known "weirdo that beats v7" is 575 rating points below it

D cites `farm2945` (0/32 for v7) as proof that intransitivity rewards population search. It shows the opposite:

- BT pays for average wins against a field that is ≈ 80% clones (census: 11 of 14 fork-family).
- An exploiter of v7 that loses to the rest sits at 2065.

A weirdo only helps if it beats the *clones*, and nothing in D's data shows a weird farm doing that.

### S6. The 4-day scope does not fit

D1 alone contains:

- the genome schema
- `zoo_graft.py`
- a 600-line `zookeeper.py`
- a descriptor extractor
- a gallery writer
- a replay-derived lineage sell schedule

**pyribs is not installed** (`import ribs` fails). CMA-ES also handles D's integer and "never" genes poorly (land
days, herd counts).

The wild body is expected to lose by more than $100k and to reach 41.7k solo against v7's 156.8k. It still takes 30%
of the cores during the only overnight run. From a win-rate standpoint, that is compute spent on the gallery.

### S7. Throughput is overstated for D's own opponent mix

- D measures v7 vs farm2945 at 6.1 s/game single-core, which is ≈ 1.3 games/s on 8 cores.
- With 0.3 of the mix on farm2945 and hybrid2965, realistic throughput is ≈ 1.5–2 games/s, or ≈ 6k/h, not 8–12k/h.
- At about 7 games per evaluation, that is ≈ 13k evaluations over 16 h, spread across about 100 feasible cells and 2
  bodies.

### S8. The mirror carries 0.4 of the fitness weight

Beating a copy of yourself is the most overfittable target. PSRO, which D itself cites, warns about exactly this.
The mirror should be a gate ("no worse than 48%"), not 40% of the objective.

## What D gets right, and what B would steal

1. **Graft layer with a neutral-genome bit-identity test.** This is a clean harness for any lever. B's hands-aware
   shed control could be tested as a graft on v7 *before* B's body exists, which separates "is the lever real" from
   "can our body execute".
2. **Racing evaluation (4 → 16 → 64 games), with a final fresh-seed gate.** B spends 400 games on every gate. Racing
   lets B screen retrains and plan-family variants cheaply before paying for 400.
3. **Opponent mix weighted by the ladder census.** B's anchors are `main.py`, farm2945 and hybrid2965. B should add
   the census-weighted mix (fork-family plus aurax7-family) as the main win-rate objective and keep the anchors only
   for the Elo mapping.
4. **The counter-probe:** a short search for an exploiter *against the candidate*, rejecting it if the counter already
   exists on the ladder. This is a cheap robustness test for B's final candidate.
5. **Measure the lineage's per-turn sale schedule from replays.** B's market head M needs exactly this as a feature
   (the opponent's expected SELL next step). The `front_run` A/B from F1 belongs in B's D3 lever list.
6. **The 13th hand (S1).** The one real, cheap signal in D's data. B's P1 capex head already outputs hires/day. B
   should test crew 12 vs 13 as a gated +3 pp lever.
7. **Using the gallery as a diagnostic.** B's plan does not need it, but per-product revenue breakdowns per candidate
   are a better KPI-diff view than bank alone.

## Minimum changes that would make D credible

- Drop the wild body from the critical path.
- Collapse D3 into an A/B of `front_run`.
- Cut the labor axis to 10–15 hands.
- Use re-evaluated archive entries, and one Bonferroni-corrected fresh-seed gate of ≥ 400 games.
- Make the mirror a floor, not 40% of fitness.
- Install and smoke-test pyribs on D1 morning, or use plain MAP-Elites with Gaussian mutation, which needs no new
  dependency.
