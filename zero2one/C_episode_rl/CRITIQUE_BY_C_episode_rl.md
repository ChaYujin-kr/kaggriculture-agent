# Critique of tracks A and B, by the C_episode_rl advocate

Written 2026-09-23. I checked every mechanic claim below against the interpreter source, not against
`research/rules.txt`. That file (230 lines) turned out to be the legal competition rules only and contains no
game mechanics. The interpreter source is
`.venv/Lib/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py` plus `kaggriculture.json`.

## What I verified and found correct (so as not to attack straw men)

- **Town drain (A).** Each shop instance drains 1 per product every 4 turns, 2 for single-product shops. That is
  6/day or 12/day. The town centre drains 1/day (`_town_consume`, L728–749).
- **CARE bonus (A).** `pending_care_bonus` accrues +1 on each cared-and-fed day and is consumed on the next fed
  production day, capped by `max_held` (L825–830). A cow (interval 2) gives 3 milk and a sheep (interval 3) gives
  4 wool.
- **Opponent tiles are public (A).** `farms` is shared across players and `private` is per player (L261–271).
- **Replays hold both seats' private observations and the seed (B).** Checked on
  `replays/episode-111543076-replay.json`: `observation.private` is present for both seats, and `info.seed` is set.
- **B's citations.** DART's "decreases the supervisor's cumulative reward by 5%" is quoted correctly. The GRF blog
  says "~333 games (around 1 million frames)… 2 days… rating of over 900".
- **Hands expire at end of day** (`farm["hands"] = []`, L880). Hire costs are fib(n) per day, so both rivals'
  labor models are right.

## Track A (top-down narrowing, "Steward")

**Fatal flaws**
1. **The plan is the one that already failed here, with a shorter deadline.** The README says our scratch planner
   "reached ~80k… could not close that gap in the time available". A measures that same planner at 73k solo and
   commits to 110k by D1 and 140k by D2. That means building from scratch, in two days:
   - a world model
   - a market model
   - a value-scored job scheduler
   - a layout planner
   - a project knapsack
   - hiring
   - a shed guard

   Nothing in A explains why this attempt closes in 48 hours a gap that the previous one did not close at all. The
   op-mix diagnosis (CARE 83 vs 410, escapes, weeds) is excellent. But it describes the symptom. It does not show
   that the fix is quick.
2. **The central proxy is contradicted by A's own table.** `farm2945` makes 173k solo and v7 makes 170k, yet they
   are rated ~2065 and ~2640 on the ladder. `broker_bea` makes 164k solo and goes 0/8 against `farm2945`. So among
   competent agents, solo bank does not predict the head-to-head result. Every day after D2 depends on a market
   and opponent layer that A's timeline only starts on D3. Yet A's gates D1–D2 and its solo-bank "proxies" for the
   percentile targets (100k, 140k, 165k) all rest on solo bank.

**Serious issues**
- **Evaluation power.** The D2 and D3 gates use 64 games. At p≈0.25 the standard error is about 5.4 pp. With
  per-game sd ≈ $9k, the D3 test "mean margin ≥ −10k" has an SE of about ±$1.1k, which is fine. But the win-rate
  arms are the same size as the 40-game trials that reversed in NOTES. The "≥6% vs farm2945" row for top 25% cannot
  be told apart from 2–3% with fewer than about 300 games.
- **Throughput is overstated.** A quotes 1.9 games/s from a mixed batch that includes planner-vs-starter games
  (1.4 s each). Champion-grade games run at about 1.0 games/s (my measurement: 48 games in 46 s). So "250k
  games / 40 SPRT runs" is really about 130k games and about 20 runs. That is still enough, but compute is not
  "free".
- **The endgame reservation will lose on day 1 of testing unless it beats a known negative result.** The README
  says: "Replacing a tape agent's late game with our planner: every switch point lost (day 27 switch: −7k)". A
  proposes a hand-built liquidation schedule. The published tape endgame is already the thing to beat, and `v7_endgame` already
  retuned it (E4, 71/80 against the pool).
- **The opponent supply model is optimistic.** "Their money deltas confirm what they actually sold" ignores their
  buys and hires. E5 shows the pool's own sales estimator is weak enough that it "only steers a small sale-timing
  layer".
- **The market and shed mechanics are right in outline, but one detail is missing.** SELL draws only from the shed
  (`_commit_unit`). A shed drop is capped at the free room (L401–409). So "units DROP mid-day when the projection
  nears the cap" only helps if the same turn's order list sells from the shed first. This is E6b's lesson
  restated, and it should be written into the design explicitly.
- **The staged targets are calibrated only against lineage agents** (`farm2945`, `hybrid2965`, v7) and the
  planner. The top-50% and top-25% cut-offs (765 and 1,577) sit in a non-lineage population that A never samples.
  A's D1 BT round-robin should include the refagents, and A's gates should cite it.
- **Mapping Kaggle ratings through an Elo-400 logistic is unverified** (Kaggle uses a Gaussian skill model). This
  applies to all three tracks, C included.

**Is it 0-to-1?** Yes, fully. It is the most honestly "own logic" of the three.

**Ideas worth stealing**
- The op-mix KPI census as an executor gate for C's D2: CARE, COLLECT_FERTILIZER and HARVEST counts, movement share
  ≤ 50%, 0 escapes, ≤ 2 weeds.
- An 8-game solo bank against `fallow_finn` as a 2-minute smoke test before any paired run.
- GSPRT acceptance in the style of Fishtest (elo0 = 0, elo1 = +30) instead of C's fixed 400–800-game gates. It
  stops early on clear results and saves ES-iteration budget.
- irace-style racing over structural variants. This fits C's selection of ≤ 8 plans.
- TacTex reservation or backward induction from step 718 to set C's "stop-plant day" and liquidation genes
  analytically, rather than by ES.
- A project-level NPV knapsack as a better compiler for C's genome θ → day calendar.
- A D1 Bradley-Terry calibration round-robin that includes the refagents.

## Track B (brain transplant)

**Fatal flaws**
1. **It clones a tape, and B's own probe proves it.** `probe_teacher.py` shows that v7's unit actions are
   identical across seeds and opponents up to step 151–459, and that 82–91% of turns are identical. GBDT heads
   trained on this learn the route library, indexed by step and shop features. That is a lossy recompression of
   the public lineage, not a policy. What follows from that:
   - The ceiling is the teacher.
   - The expected ladder outcome of "97% of v7" against a field of near-clones is coin flips minus the copy error.
     B concedes this in its risk 3: 9 of 10 games are decided by less than $1k.
   - It hardly meets the user's "own core logic, not a fork" requirement. The body is ours, but every decision the
     brain makes is the champion's.
2. **The DAgger and DART repair step does not work on an open-loop teacher.** A tape teacher queried off its own
   trajectory emits its next scripted action whatever the state is. B's own risk 1 says these "may be nonsense".
   The validity filter only removes illegal or no-op labels, and legal-but-wrong labels survive. DART noise
   injected into a tape desyncs the farm, and the README records that "raw tapes score $0 against a live
   opponent". The recoveries then come only from the thin reactive layers. So the covariate-shift fix that B's
   whole lineage (Ross 2011, Laskey 2017) rests on is unavailable in exactly the regime B targets.
3. **"Beat it where it leaks" targets leaks that are already patched, or that past attempts failed to close.**
   - Days 26–28 are the E4 leak, but `v7_endgame` is the post-E4 retune (71/80 against the pool, submitted).
   - The shed guard was tried in E6a and E6b with no gain. B's hand-projection version is untested.
   - Swapping in our own late game lost at every switch point (README, day-27 switch: −7k).

   So none of B's three stated sources of edge over the teacher is backed by evidence.

**Serious issues**
- **The oracle gate is ambiguous.** "The body executing the teacher's own logged intents" is a tape replay at
  intent level. Replayed in the same seed and pairing, it tests the abstraction. But whenever our body's routing
  differs, the teacher's intent timeline (open-loop) drifts from the state. Passing the oracle therefore does not
  predict how the student will do once its own heads choose the intents.
- **Evaluation power.** The top-12.5% gate uses 64 games. The final gate, "≥55% over 200 games (SE 3.5%)", is 1.4
  SE above 50%, which is not significant. With sd ≈ $9k and a near-clone field, 200 games cannot separate
  a 52% agent from a 48% one.
- **The gate labels do not match the Elo mapping.** B's "top 25%: ≥20% vs farm2945 (≈1,830 equivalent)" is a
  1,830 gate, not a 1,577 gate. Under B's own logistic, 1,577 corresponds to about 6%. B's gates are stricter than
  its labels, and B is then likely to KILL too early. Like A, B never samples the non-lineage population where the
  765 and 1,577 cut-offs sit.
- **Label imbalance.** H2 is dominated by "leave", and H4 by "0". The agreement targets (H2 ≥ 90%, H4 ≥ 80%) can
  be met by predicting the majority class. B needs per-class recall or bank-weighted metrics.
- **Multi-teacher AWR blends route families.** B mitigates this with an opening latent z, but z is fixed at step 0,
  while the champion's real plan switch happens at step 144 (the shop router) and at step 648.
- **Budget.** 3k logged games ≈ 85 min at 0.59 games/s, and 5k games ≈ 5 GB. That is fine. The pure-Python tree
  export costs: 6 heads × 300 trees × depth 7, with the tile head evaluated for up to 100 tiles per turn, is about
  30k tree walks per turn, or tens of ms. Still inside the 1 s limit, but B's "1–3 ms" figure is per head call,
  not per turn.

**Is it 0-to-1?** Only nominally. The execution code is ours, but the strategy is distilled from the tape lineage.

**Ideas worth stealing**
- **The oracle test, adapted to C.** Invert the teacher into θ_L1, compile it, execute it, and require ≥ 95% of the
  teacher's bank on the same seeds. This is a sharper D2 gate than C's "≥40% vs farm2945".
- **`probe_teacher.py` and the open-loop statistics.** The first divergence at step 151–459 gives C's
  lexicon-segmentation boundaries, and confirms the step-144 selector as the main branch point.
- **Replays include both seats' private observations and the seed.** C can extract L3 (top-2 branch) unit-level
  traces exactly for the lexicon without live play. That upgrades L3 from "prosody only".
- A shop-conditioned market head: react to revealed shops at every unlock, not only at step 144.
- AWR-style margin weighting when C fits plan priors from multiple lineages.
- Pure-Python export of a small tree for C's depth-3 selector.

## Cross-cutting points that also hit my own track (for fairness)

- All three tracks use Elo-400 anchors on Kaggle ratings, and all three calibrate mostly against lineage agents.
  A D1 round-robin that includes the refagents is needed by everyone.
- The negative results in the README (late-game swap, E6a/E6b shed guard) apply to C's endgame and shed genes
  too. C should let ES discover these genes and gate them by SPRT, not assume they are gains.
- C's executor faces A's fatal flaw 1, because it reuses the scheduler from `agents/main.py`. The mitigation has
  to be phrase-first emission plus A's op-mix KPIs as a hard gate.
