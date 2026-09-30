# Track D: Weirdo Zoo (괴짜 동물원)

**One line:** grow a quality-diversity archive of deliberately strange farms, let them fight the clone meta and each other, then turn the best-placed weirdos into AlphaStar-style exploiters of the one dominant lineage. The zoo publishes a daily gallery of its strangest farms.

## 0. Why weirdness is worth a track (measured today)

Source: `data_audit/raw` (episode_features + stream_hashes, engine 1.32.7, 09-13..09-22, both seats rated >= 2300; 15,482 seat-games).

- **The monoculture is literal.** Median high-rated farm: 12 melon, 33 strawberry, 31 carrot, 163 wheat, **0 tomato**, land on day 6, peak crew 12. The 5%-95% range of melon and strawberry is 12-12 and 33-33. Two h48 lines hold 50% of seats.
- **Deviating in the right direction wins.** Pairwise within a game (ties excluded):
  - The seat with the **larger peak crew wins 64.5%** (n = 1,970 games).
  - The seat with **more tomato plants wins 64%** (n = 430).
  - A seat *off* the top-5 opening lines, facing a seat *on* one, wins 52.6% (n = 2,329, 405 lines).
  - Small tails are also positive: farms planting 260 or more tiles win 71% (n = 58), and farms buying land before day 6 win 65% (n = 37).
- **Caveat:** these are observational. Crew is partly endogenous (a winning farm has more work to hire for), and tomato partly reacts to pizza and farmers-market unlocks. They set the **descriptor axes**. They are not proven levers.
- **Win rates are intransitive** (Track A): `v7_endgame` (~2640) goes 0/32 locally against `farm2945` (~2065). Intransitivity is exactly where a population search beats a single hill-climb.
- **Respect E1/E5.** Market attacks cost us more than the opponent, and being different also helps the opponent: if we leave milk alone, the clone gets the milk reservoir to itself. The zoo therefore never rewards *denial*. It rewards **uncontested revenue** (tomato, egg, and carrot shop demand the meta ignores) and **timing edges** against a predictable schedule. B measured the lineage as 82-91% open-loop.

## 1. Philosophy lineage (URLs opened)

| Idea | Source | What we take |
|---|---|---|
| MAP-Elites "illuminates search spaces" and returns an elite per behaviour niche | https://arxiv.org/abs/1504.04909 | The archive *is* the zoo. One elite per cell. |
| CVT-MAP-Elites keeps the cell count fixed as descriptor dimensions grow | https://arxiv.org/abs/1610.05729 | Fallback if the 3-D grid is too sparse |
| CMA-ME "more than doubl[es]" MAP-Elites; official code is pyribs (CPU, `pip install ribs`) | https://arxiv.org/abs/1912.02400, https://pyribs.org/ | Search engine, no new optimizer code |
| Novelty search: deceptive objectives trap fitness-only search | https://www.cs.swarthmore.edu/~meeden/DevelopmentalRobotics/lehman_ecj11.pdf | "Beat v7" is deceptive: every scratch farm loses by $100k+, so early selection is by novelty and uncontested revenue, not wins |
| POET: stepping stones transfer between problems | https://arxiv.org/abs/1901.01753 | Genes found in the wild body transfer into the graft body (section 2) |
| Go-Explore: archive, return, then explore | https://arxiv.org/abs/1901.10995 | Emitters restart from archived elites, not from scratch |
| AlphaStar league: exploiters "expos[e] its flaws, rather than maximising their own win rate against all players"; main exploiters vs main agents, league exploiters vs the whole league | https://deepmind.google/discover/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/, https://proceedings.neurips.cc/paper_files/paper/2023/file/94796017d01c5a171bdac520c199d9ed-Paper-Conference.pdf | Phase 4: main exploiter vs the dominant lineage, league check vs the pool |
| Minimax Exploiter: data-efficient counter-strategies | https://arxiv.org/abs/2311.17190 | Exploiter budget stays small |
| PSRO: independent RL "can overfit to the other agents' policies" | https://arxiv.org/abs/1711.00832 | Fitness is a mixture over opponents, never one opponent |
| Off-meta precedent: Lux 2021's RL agent won a sprint prize with "scorched earth" resource denial, until a rule change removed it | https://github.com/IsaiahPressman/Kaggle_Lux_AI_2021/blob/main/README.md | Off-meta wins exist. Here, though, denial is measured to be net-negative (E1), so we pursue niches instead |
| Warning: Halite IV 4th dropped evolutionary tuning over "symmetry, overfitting and little noise" | https://github.com/0Zeta/HaliteIV-Bot | Both seats, paired seeds, fresh-seed revalidation |
| Warning: Battlecode 2021 was won by mastering the economy meta, not by defying it | https://blog.stoneztao.com/posts/bc21/ | We do not assume the weirdo wins, and gates decide |
| RoShamBo: pattern predictors (Iocaine Powder) top a field where some bots are predictable | https://homepage.kranzky.com/roshambo/Index.html | A near-open-loop clone has a schedule we can front-run |

## 2. Design

### 2.1 Genome (18 genes) and two bodies

| Gene group | Genes |
|---|---|
| Land | day for quadrant 2, 3, 4 (or never) |
| Plot | tile shares for wheat, carrot, tomato, strawberry, melon, pasture, coop |
| Herd | cow, sheep, goose targets plus a buy day |
| Labor | hands per day, as a curve over 3 knots (fib cost: the n-th hire costs fib(n)) |
| Care | CARE and fertilizer priority (animals give 1 free fertilizer/day, ~$100) |
| Market | lot size and minimum price ratio per premium product; front-run offset versus the lineage sell schedule |
| Endgame | liquidation start step (<= 718), shed reserve (capacity 100, overflow discarded) |

The **same genome** is expressed by two bodies:

- **Wild body `zookeeper.py`** (new code, about 600 lines). It is a day-program executor:
  - Once per day it turns genes into a tile plan.
  - Greedy unit-to-job matching: water, feed, harvest, CARE, collect fertilizer, plant, DROP before the shed fills.
  - Step-718 liquidation.
  - Plays all 18 genes.

  **Honest expectation:** scratch farms are far weaker. Measured today, seed 7 against the passive opponent: `rancher_rita` 41.7k, `v7_endgame` 156.8k. The ref league has every scratch archetype losing to the meta by $100k+. The wild body is for **discovery and the gallery**, not for submission.
- **Graft body `zoo_graft.py`**. It is a layer on `v7_endgame`, the same pattern as `agents/layer_fert.py`, that expresses only the genes a layer can touch without desyncing the tape:
  - market lots, floors and front-run offset
  - extra hands (count and jobs)
  - a side plot on unused tiles (tomato, egg, carrot niche)
  - liquidation step and shed reserve

  With the neutral genome it must be **bit-identical** to v7. This is where a competitive weirdo can come from in 4 days. Wild elites seed its niche genes, which is POET transfer.

### 2.2 Behaviour descriptors (measured from play, not read from genes)

The grid is 8 x 8 x 6 = 384 cells.

1. **Labor intensity:** hand-hours per day relative to the meta's crew of 12.
2. **Niche share:** the share of revenue from products the meta under-serves (tomato, egg, carrot, wheat), against the premium four (milk, wool, strawberry, melon).
3. **Sell timing:** the revenue-weighted mean sale step minus the lineage's, which includes the liquidation share after step 696.

"Capex timing" is a tie-break field shown in the gallery. Novelty is the k-NN distance in (1, 2, 3) plus capex. If fewer than 25% of cells are filled, we switch to CVT with 256 centroids.

### 2.3 Fitness: noise-aware racing

- **Opponent set O,** weighted by the ladder census:
  - `v7_endgame` (mirror, our fork family): 0.4
  - `aurax7_v7`: 0.2
  - `farm2945`: 0.15
  - `hybrid2965`: 0.15
  - `v54fork`: 0.1
- **Fitness** = win rate + 0.05 * tanh(margin / $10k), paired seeds, both seats. Wins dominate because BT pays for wins and 38.6% of high-rated games are within $1k.
- **Racing:** 4 games to screen, then the top 20% go to 16 games and the top 5% to 64. At a per-game sd of about $9k, 64 paired games give a win-rate SE of about 6 pp. That is enough to separate 60% from 50%, not 52% from 50%. No claim below 128 fresh-seed games.
- **Wild body in D2:** a wild farm's fitness is its bank against the mix plus a 0.3 novelty weight, because its win rate is 0 everywhere (the deceptive plateau).

### 2.4 Exploiter phase (main exploiter)

1. Take the top 5 graft cells by fitness.
2. Measure the dominant lineage's **sale schedule** from replays: per-turn market-inventory drops for milk, wool and strawberry in `10f7cb32`/`b9faeb92` games.
3. Seed the front-run gene there. Market orders settle one unit at a time, the first unit gets the best price, and premium goods crash under `above_target` > 1. Selling a few units *one turn before* the clone's dump takes the high price and leaves the clone the crash, with no inventory bought (unlike E1/E5).
4. Run pyribs CMA-ES inside each cell against the lineage proxies only (v7, aurax7_v7, v54fork).

### 2.5 Robustness (league check)

- Round-robin with fresh seeds (5000+): 16 pool agents + champion + 10 elites, both seats, 16 games per pair.
- A BT fit anchored on ladder ratings (farm2945 2065, hybrid2965 2370, v7 2640).
- **Accept** if BT >= champion + 30 with the 95% CI lower bound above the champion, and no opponent below 35%.
- **Plus a counter-probe:** run a 1-hour CMA-ES exploiter *against the weirdo*. If it finds a counter with a genome that already exists on the ladder, reject the weirdo.

### 2.6 Daily gallery ("오늘의 괴짜 농장")

`D_zoo/gallery/YYYY-MM-DD.json` holds the following for the 10 weirdest elites (max novelty and fitness > 0.3) and the top 5 by fitness:

- `id`, `nickname` (for example "Tomato Hermit", "Twenty-Hand Circus", "Last-Turn Dumper")
- `body`, `genes`, `descriptors`
- `revenue_by_product`, `win_rate_by_opponent`, `margin_ci`
- `novelty_rank`
- a 2-sentence `story`: what is strange, and whom it beats
- `best_seed`, for a replay

Also produced each day:

- `heatmap.json`, the archive grid with fitness per cell
- `leaderboard.json`, BT over the zoo

The main session renders them.

## 3. Compute plan (measured 09-23, single core, one game including load)

| Pairing | s/game |
|---|---|
| PASS vs PASS | 0.7 |
| rancher_rita (scratch-class body) vs PASS | 0.9 |
| v7 vs PASS | 2.6 |
| v7 vs farm2945 | 6.1 |

- The opponent is the cost, as the arena notebook also found: "the cost is the agents". With 8 cores at the measured 2-3.5 games/s, that is about **8-12k games/hour**, or about **150k games/day** at 16 h.
- Racing averages about 7 games per evaluation, so the budget is **about 20k evaluations/day**. An overnight CMA-ME of 3 emitters x batch 24 fits comfortably.
- Kaggle CPU notebooks run seed shards of the round-robin (4 cores each, 12 h). They are an addition, not a dependency.

## 4. Four-day build plan with gates

| Day | Build | GO | KILL |
|---|---|---|---|
| D1 09-24 | genome schema; `zoo_graft.py`; `zookeeper.py` v0; descriptor extractor; gallery writer; replay-measured lineage sell schedule | graft with neutral genome bit-identical to v7 on 8 seeds; wild solo >= 50k; gallery JSON validates | graft cannot be neutral: drop the graft body, and the zoo becomes gallery plus niche map only |
| D2 09-25 | CMA-ME on both bodies (graft 70% of cores); overnight | >= 25% cells filled; >= 1 graft elite >= 56% vs the O mix at 64 games | no graft elite > 52% at 64 games: stop the search and hand the niche map to A/B/C |
| D3 09-26 | exploiter phase, top 5 cells | >= 58% vs lineage proxies, 128 fresh-seed games | front-run gene converges to 0 and no exploiter beats its parent cell |
| D4 09-27 | league round-robin, counter-probe, candidate packaged for the main session | section 2.5 accept rule | fails: publish the gallery; the champion stays |

## 5. Staged targets (cut-offs as in Track A: 765 / 1,577 / 2,246)

- **Graft weirdo:** it inherits the champion's body (~2640), so top 12.5% is met by construction. The real target is **BT above the champion** (the D4 accept rule). A reasonable prior is 30-35%, since most graft genes only move margins by about $1k, which is exactly the size of the games that flip.
- **Wild weirdo:** panel BT >= 900 is top 50% (likely by D3). >= 1,577 is top 25% (possible only if the executor reaches about 120k solo). Top 12.5% is not expected in 4 days.

## 6. Top 5 risks

1. **The wild executor is too weak for its fitness to mean anything.** Mitigation: its fitness is bank plus novelty. The graft body carries the competitive load.
2. **Noise tricks us.** At $9k sd, a 52% "exploit" is invisible. Mitigation: racing, paired seeds, both seats, and only 128+ fresh-seed games count.
3. **The graft layer desyncs the tape.** The README notes that tapes break when the farm diverges. Mitigation: side-plot genes use only tiles the tape never touches, verified on D1, and unsafe genes are clamped to 0.
4. **Niche revenue is small or helps the opponent.** Tomato's T is 200 with the hinge knee, so the pie is finite. Mitigation: fitness is relative (win rate), so helping the opponent is penalized automatically.
5. **The exploiter overfits the proxies.** The ladder has about 11 effective h48 lines, and the proxies cover the two biggest. Mitigation: a league check against all 16, plus the counter-probe.

## 7. Why this beats A, B and C

- **A and B, and C's lineage prior, all start inside the monoculture.** They imitate, narrow, or learn the grammar of the same 41 routes. They can at best become a better clone, in a ladder where clone-vs-clone games are coin flips decided by under $1k.
- **D is the only track whose objective rewards distance from the meta.** It is also the only one with an explicit **exploiter** aimed at the dominant lineage, and ladder data says deviation in labor and niche crops correlates with 64% pairwise wins.
- **D is cheap.** It reuses the champion's body, pyribs, and the existing paired harness, and it shares nothing on the critical path with A, B or C.
- **D's outputs help the others either way:**
  - a descriptor-space map of where uncontested revenue lives, which A and C can use as plan targets
  - a counter-probe that stress-tests their candidates
  - a gallery that makes the search visible every day, even if no weirdo is ever submitted
