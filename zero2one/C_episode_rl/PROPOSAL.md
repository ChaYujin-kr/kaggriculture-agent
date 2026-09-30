# Track C: whole-game-as-one-action RL over a multilingual plan grammar

**Verdict.** One RL action is one 720-turn plan genome θ. A thin deterministic executor runs that plan, and the episode returns one reward. The plan space is not hand-designed: it is **learned from the lineages as languages**. Stage 1 segments each lineage's action stream into phrases, which become the lexicon. Stage 2 fits a shared genome schema, the grammar. Stage 3 passes a recognition test per lineage. Only after that does parameter-space RL (PGPE / OpenAI-ES with common random numbers) start from the fluent prior. The deliverable is a readable plan library plus a selector tree.

The domain already works this way. The champion `aurax7_v7` makes exactly one plan decision: at step 144 it maps the first two shops to one of 41 routes (`_router`, `_R108_SHOP_ROUTES`), and at step 648 it switches to an endgame route. Measured: the 41 routes share an identical prefix of median 144 steps (min 70). We replace the tapes with a learned generative grammar and search that grammar.

## 1. Lineage of philosophy

**General baseline: episode-level RL**
- ES is "invariant to action frequency and delayed rewards, tolerant of extremely long horizons". It needs no value function, and it scales with scalar communication via common random numbers. https://arxiv.org/abs/1703.03864
- PGPE samples parameters once per episode and then keeps the controller deterministic. This gives lower-variance gradients than per-step policy gradients, where variance "increases linearly with the length of the history". The gain is largest with symmetric sampling. https://www.ias.informatik.tu-darmstadt.de/uploads/Publications/Neural-Networks-2010-Sehnke_%5B0%5D.pdf
- Noisy CEM prevents CEM's early collapse; the canonical example is Tetris. https://github.com/corentinpla/Learning-Tetris-Using-the-Noisy-Cross-Entropy-Method
- CMA-ES noise handling re-evaluates candidates and raises the evaluation count when noise dominates. https://cma-es.github.io/apidocs-pycma/cma.optimization_tools.NoiseHandler.html
- PSRO answers mixtures of opponents, because independent RL "can overfit to the other agents' policies". https://arxiv.org/abs/1711.00832
- AlphaStar started from imitation (84% before RL), used main agents plus exploiters, and distilled toward human play. https://deepmind.google/discover/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/
- The Lux S1 winner used a frozen-teacher KL "to stabilize behavior and prevent strategic cycles", on dual GPUs trained overnight for months. That is out of our budget. https://github.com/IsaiahPressman/Kaggle_Lux_AI_2021/blob/main/README.md
- The Lux S2 winner was rules plus forward simulation. https://deepwiki.com/ryandy/Lux-S2-public
- Halite IV 4th place tuned by evolution and then dropped it because of **overfitting and self-play-only opponents**. https://github.com/0Zeta/HaliteIV-Bot

**Narrower topic: Kaggriculture layer strategy**
- "A route is a YAML plan for one 720-turn episode". A route selector plus a micro overlay went 378-22 against its own base. https://github.com/OscarLegoupil/agriculture-agent
- Exact controller, parametric macro policy, population CEM, meta-equilibrium, and a tiny live selector. This stopped at rating ~600 with the learned model unvalidated. https://github.com/sidhulyalkar/kaggriculture
- Macro-PPO with 15 decisions per game and reward `sign(m)+0.05·tanh(m/1e4)`; no results reported. https://github.com/prince22466/Co_AMAP/pull/33
- Per-turn BC+PPO: "improvement over BC remains unconfirmed". https://github.com/atsushi11o7/kaggriculture/pull/16
- Local digests: a single field hash in 144 of 200 top-20 episodes; "nothing observable differs before turn 48" (`what-2600-farms-do-differently`, `findings-from-zero-to-top-meta`).

**Developmental curriculum (mechanism → operation)**

| Finding (URL) | Operation here |
|---|---|
| Bilingual newborns discriminate their two languages and prefer both equally (Byers-Heinlein 2010) https://www.sciencedaily.com/releases/2010/02/100216142330.htm | **Stage 0**: learn to *discriminate* lineages from coarse "prosody" (step-1 bank, daily op-type rhythm) before any vocabulary. |
| Differentiated systems from the start; mixing is context-sensitive (Genesee 1989) https://eric.ed.gov/?id=EJ385564 | One shared grammar (genome schema) plus a separate lexicon and prior per lineage. Every trace carries a lineage tag. |
| Word segmentation from transitional probabilities after 2 min of exposure (Saffran 1996, via Aslin primer) https://sites.socsci.uci.edu/~lpearl/courses/readings/Aslin2017_StatLearning.pdf | Segment unit action streams at dips in transitional probability, then build hierarchy with Sequitur (digram uniqueness, linear time) https://en.wikipedia.org/wiki/Sequitur_algorithm. CompILE covers the latent-segment variant https://arxiv.org/abs/1812.01483 |
| Proficiency tracks the *relative* input per language (Hoff 2012) https://eric.ed.gov/?id=EJ971194 | Explicit doses (below). We expect fluency only where input is large. |
| Live exposure teaches; recorded exposure does not (Kuhl) https://www.newswise.com/articles/social-interaction-plays-key-role-in-how-infants-learn-language | Learn from **live fastsim play** of each lineage against reacting opponents, never from replayed tapes. Measured locally: raw tapes score $0 against a live opponent (README). |
| Sensitive periods; perceptual narrowing at 8–10 months; bilingual upbringing alters the windows (Werker & Hensch 2015) http://canadianslp.blogspot.com/2018/05/critical-periods-in-speech-perception.html | The grammar is plastic in Stages 1–2 and **frozen** before RL. RL moves θ only inside a trust region anchored to the fluent prior (the "brake"). |
| Code-switching marks competence (Yow et al. 2018) https://www.cambridge.org/core/services/aop-cambridge-core/content/view/DE93C61F10B151AD5EC248E8D0EB5006/S1366728917000335a.pdf/div-class-title-code-switching-as-a-marker-of-linguistic-competence-in-bilingual-children-div.pdf | Switching lineage mid-game is allowed only at phrase or day boundaries, and only when the live state lies inside the other lineage's state envelope at that step. |

**Tuning philosophy.** Win count first and margin only as a tie-break (reward as in prince22466). Paired seeds, both seats, antithetic pairs. Every keep is re-validated on fresh seeds, because in NOTES 40-game wins reversed at 80 games.

## 2. Core design

**Languages and doses.** Dose is the share of generated training traces.
- **L1, aurax7 family** (v4, v5, v7, `v7_endgame`, plus 53 of our ladder replays): **50%**.
- **L2, fork family** (farm2945, thomas-2944, hybrid2965, master-v3, v54fork, v55, v56, morewheat, bestrank, clonerace, demandpres; `rescue7` is byte-identical to `morewheat`): **35%**. L2 shares L1's 41-route library but differs in opening (step-1 spend $157 vs $0), router and reactive layers. **L1 and L2 are dialects**, and we state that openly.
- **L3, top-2 branch** (opens COW+5 WHEAT, runs more cows and geese; 8 top episodes plus tape sparring agents): **10%**. This is "recorded input" only, so it feeds the herd block prior and is not a fluency gate.
- **L4, refagents** (rancher_rita, melon_mateo, broker_bea, …): **5%**, used as a contrast class.

**Lexicon (measured).** The 41 routes contain 12,236 unit-day programs, of which 1,077 are distinct. The top 300 cover 72%. Sub-day phrases from TP-dip segmentation plus Sequitur should compress further. Phrases are stored with preconditions, as a relative tile pattern plus a unit role.

**Genome θ (the shared grammar, ~40 dimensions).**
- Opening phrase id.
- Land-buy days (3).
- Herd targets for cow, sheep and goose at days 6, 12 and 18 (9).
- Crop-mix simplex per phase (3×5).
- Hands/day curve (3 knots). The tapes average 8.9 hands per day, max 12; the n-th hire costs fib(n).
- Sell ladder per premium good: lot size and minimum price ratio (8). Premium goods have `above_target>1` and floor fast.
- Endgame: stop-plant day per crop, liquidation start, final drop step (4).
- Shed guard (1).

**Decision structure.**
1. **Selector**, the single action. At step 144 it maps the context to plan k. Context is the opponent tag from their step-1 bank (E2) plus the demand vector of the first two shops. Shop unlocks are unpredictable (13.4% vs 12.5%), so we only condition on shops already revealed.
2. **Compiler.** θ becomes a day calendar: tile layout, plantings, buys, hires and sell orders.
3. **Executor.** Deterministic and per turn. It emits a lexicon phrase when its precondition matches; otherwise it assigns jobs greedily, reusing the scheduler from `agents/main.py` copied into this track. Constraints it respects:
   - WATER and FEED once per day. Plants weed, and animals escape, after 2 missed days.
   - FERTILIZE only on watered days. CARE banks a bonus.
   - COLLECT_FERTILIZER once per animal per day.
   - At most 10 market orders per turn, SELLs first. Orders fill one unit at a time, quoted at the pre-sell price.
   - Buy wheat for feed.

**Shed.** The cap is 100 items, and end-of-day overflow is discarded; E6 measured $0.9–7.5k lost per game. The executor holds the invariant (shed + inventories in hand) ≤ 92 by hour 22. It sells or skips harvests when the invariant would break, because the leak is produce still in units' hands.

**Endgame.** Step 718 is the last step that executes, and the last day's harvest is not auto-dropped. Genes schedule the final drop-and-sell. Top teams gain $3.5–13.3k on the final day against our $8.2k.

## 3. Data and compute (measured today)

| Item | Value |
|---|---|
| fastsim, 1 game, 1 thread | 1.5 s (v7 vs aurax7), 2.3 s (v7 vs v54fork) |
| 8 processes, 48 champion-grade games | 46.2 s → **1.04 games/s ≈ 3,700/h**. The i5-8265U has 4 physical cores, 8 threads. |
| Replays | 52 ladder episodes (1.6 GB, 53 seats ours); 8 top episodes; 41 routes × 719 steps |
| Per-game sd | ~$9k |

**Budget.**
- One ES iteration is 16 antithetic pairs × 8 CRN seeds × 2 seats = 512 games ≈ 8 min. An overnight run of 12 h is about 90 iterations.
- With d≈40 and only 32 samples per iteration, we run **block-ES**: blocks of 8–10 dimensions (labor, herd, crops, sell, endgame) in rotation.
- Gates use 400–800 paired games (7–13 min). To detect ±10 pp at 50%, we need about 400 paired games per arm.

## 4. Four-day build (all evaluations paired: same seeds, both seats)

| Day | Build | GO | KILL |
|---|---|---|---|
| D1 09-24 | Trace logger (15 pool agents × 32 seeds × 2 seats ≈ 20 min); lineage classifier; segmentation and lexicon; genome, compiler, executor skeleton | Leave-one-agent-out lineage accuracy ≥ 90% | < 75%: recognition test (a) falls back to the bank signature only |
| D2 09-25 | Invert L1 traces into θ_L1 per shop cluster; **L1 native test** | Recognition (a)–(c) pass; ≥ 40% vs farm2945 | < 15% vs farm2945: executor failure (same wall as the planner at 500). Stop RL and hand the lexicon and classifier to tracks A/B |
| D3 09-26 | L2 fluency and test; start ES from the L1/L2 mixture. Population weights from the ladder census: fork 11/14, aurax7 2/14, other 1/14; plus frozen self-snapshots and one exploiter (PSRO-lite) | +8 pp population win rate after 12 iterations, on fresh seeds | No gain after 24 iterations: submit the fluent L1 selector only |
| D4 09-27 | Overnight ES; per-shop-cluster crop fine-tune; distil to ≤ 8 plans plus a depth-3 selector tree (YAML); 800-game validation vs pool and `v7_endgame` | §5 thresholds | |

09-28 to 09-30 is buffer. Submitting is the user's decision.

**Recognition test (the gate before RL).**
- **(a) Lineage classifier.** Features: step-1 bank, per-day op-type counts, visible opponent farm composition at days 6/12/18/24, and exact-prefix length against the lineage trie. Prefixes under 48 steps are uninformative, so we require the lineage's typical ~144 steps. Pass: our mean P(target) ≥ the 25th percentile of held-out genuine members, and top-1 = target in ≥ 90% of games.
- **(b) Pool detectors.** We inspected the pool: the agents contain no kin detector. They have only a `front_run` hook (off by default) and a market-ledger estimator of opponent sales. So we test three things:
  - b1: our E2 tagger labels us as the target.
  - b2: the pool estimator's daily inferred-sales series against us matches the series against a genuine member (KS p > 0.05).
  - b3: `front_run`, fed the target's tape, gains the same margin against us as against a member (±$500).
- **(c) Seat-swap.** 6 opponents × 32 seeds × 2 seats. TOST equivalence on paired margin within ±$1.5k, and win rate within ±6 pp.
- **Anti-memorisation.** Lexicon plus grammar must be ≤ 10% of the tape bytes (an MDL-style check), and no phrase may exceed 48 steps except the opening chunk.

## 5. Staged targets → win rates

The cut-offs come from track A's leaderboard snapshot (9,883 teams: top 50% = 765, top 25% = 1,577, top 12.5% = 2,246); I have not verified them. Anchors: planner 499, farm2945 ~2065, hybrid2965 2370, v7 ~2640. Win rates use the Elo-400 logistic.

| Target | vs planner | vs farm2945 | vs hybrid2965 | vs v7_endgame |
|---|---|---|---|---|
| Top 50% | ≥ 82% | – | – | – |
| Top 25% | ≥ 99% | ≥ 6% (and mean margin ≥ −$6k) | ≥ 1% | – |
| Top 12.5% | 100% | ≥ 74% | ≥ 33% | ≥ 9% |
| Beat champion | – | – | – | > 50% over 800 games |

The ladder is mostly clones, so win rates are not transitive. We report the census-weighted population win rate alongside each row.

## 6. Risks and why this route

1. **Executor quality.** Our scratch planner stalled at ~500. Mitigation: phrase-first emission, with phrase coverage tracked (% of steps), and the D2 KILL gate.
2. **Noise and overfitting.** Halite IV evolution overfit, and our own 40-game reversals did too. Mitigation: CRN, antithetic pairs, block-ES, fresh-seed gates, and a PSRO population rather than a single opponent.
3. **A copy passes the recognition test trivially.** Mitigation: the MDL cap and the phrase-length limit.
4. **Multilingual claim is weak.** L1 and L2 are dialects, and L3 has no live speaker. Mitigation: state this openly; L3 only seeds the herd prior.
5. **The Elo mapping may be off.** Mitigation: re-anchor with a D1 round-robin and use population-weighted gates.

**Honest odds.** Top 25% is plausible if D2 passes. Top 12.5% is possible. Beating v7 head-to-head in 4 days is under 15%.

**Why this route.** Track B clones a per-turn policy. Per-turn BC+PPO in this very competition never beat BC, and per-step noise grows with the 720-step horizon. Here the learning signal is one sample per episode (the PGPE argument). The search space is the grammar the strongest agents actually use, and the output is a readable plan library plus selector rules, not a black box.
