# Critique by track B (transplant) of tracks A (narrowing) and C (episode RL)

I checked each proposal against the README, `experiments/NOTES.md`, the extracted digests and two URLs that C cites.
Note on sources: `research/rules.txt` holds Kaggle's legal competition rules, not the game mechanics. The mechanics
are in the README, NOTES and the digests (for example `the-2945-farm-.../digest.md` §4.3 on CARE).

## Track A: from-scratch "Steward"

### Fatal or near-fatal
1. **The gates measure solo bank, but games are decided by head-to-head margin, and A's own data shows these differ.**
   A notes that `broker_bea` banks 164k solo and still loses 0/8 to `farm2945`. `farm2945` also out-banks v7 solo
   (173k vs 170k) while rating 575 points lower. Yet the D1 and D2 GO/KILL gates are solo ≥110k and ≥140k. An agent can
   pass every early gate and still lose to the whole lineage band, which is exactly the broker_bea outcome. The first
   head-to-head gate against the lineage comes on D3.
2. **A's win-rate table and its D4 gate disagree.** The table puts top 12.5% (2,246) at ≥74% vs `farm2945`. The D4 GO
   gate is ≥50% vs `farm2945`, which under A's own Elo mapping is about 2,065, or roughly top 16%. The top-25% row,
   "≥6% vs farm2945", means 4 wins in 64 games and cannot be told apart from 0–10% at that sample size.
3. **The scope does not fit 4 days.** D1 alone includes a world model, an exact market model checked on 1k interpreter
   states, a job scheduler, a champion-shaped template and a BT calibration round-robin. D2 adds a knapsack, hiring,
   the market layer and the shed guard. The target is to more than double solo output (73k to 140k) in 2 days. The
   tape lineage's micro was refined by many public authors over weeks; the digests list dozens of +N/−0 patches
   (CAPHARV, SL2, VT1 and others). Fairness note: `agents/main.py` got about one day of work on 09-21 (682 lines), so
   its rating of 500 is weak evidence that a scratch planner hits a wall.

### Serious
- **"IL needs scale we lack" is stale.** A counts 52 replays and ignores fastsim. B measured about 2,100 labelled
  teacher games per hour on this machine. The "200M tuples on 2×A100" example (Kore) is about neural nets on
  raw observations, not GBDT heads over a macro action set.
- **The diagnosis comes from one census on one seed (901) against a passive opponent.** The op-mix KPIs (CARE 410 vs 83)
  are useful, but they say nothing about the market-race and reactive layers that decide games between near-clones
  (9 of 10 games decided by under $1k).
- **SPRT and SPSA arrive only on D4.** SPSA on 15 knobs plus SPRT at elo1 = +30 needs about 1–2k games per accept.
  That is feasible, but leaves no room if D3 lands late. And the 40-game reversal lesson applies to the D3 racing
  eliminations every 16 paired games.
- **The Elo mapping is not transitive in a one-lineage ladder.** The BT calibration run is the right fix, but every
  gate in §5 is derived before that calibration exists.
- **Small mechanic detail:** the n-th hire costs fib(n−1) according to the 2945 digest, while A (and the README) write fib(n).
  This is harmless, but the labor price feeds the knapsack.

### Is it 0-to-1?
Yes. A is the cleanest 0-to-1 of the three: its own code, with replays used only as priors. Its risk is the floor,
not the provenance.

## Track C: whole-game RL over a plan grammar

### Fatal or near-fatal
1. **The executor is the component that already failed.** C reuses the scheduler from `agents/main.py`. A's census
   shows that scheduler is the bottleneck: 73k solo, 64% movement, cows escaping, 15 weeds by day 28. The README
   also records that switching the tape's late game to our planner lost at every switch point (−7k at day 27). If the
   executor cannot turn a plan into production, searching over plans cannot help. C's own KILL gate on D2 (< 15% vs
   farm2945) names this wall, but gives no reason to expect it to pass.
2. **The lexicon is the tape under another name, and the anti-copy check does not catch it.** The 41 routes contain
   only 1,077 distinct unit-day programs out of 12,236, and 300 of them cover 72%. Data this redundant compresses far
   below 10% of the tape bytes, so the MDL cap is satisfied by near-lossless memorisation. The recognition test goes
   further and rewards being classified as the lineage. The stated goal is "own core logic, not a fork of the tape
   lineage", and the recognition test optimises the opposite.
3. **Replaying phrases runs into the known desync failure.** The README says raw tapes score $0 against a live
   opponent because the farm desyncs, and "only the reactive layers carry a tape agent's strength". Phrases with
   tile-pattern preconditions are shorter tapes, with the same problem at every phrase boundary.
4. **The ES signal is too weak for the budget.**
   - Each perturbation gets about 16 games, and the reward is mainly the win count. For small θ steps, most
     antithetic pairs will flip no result, so the gradient estimate is mostly zero or noise, with sd around $9k per game.
   - Block-ES over 5 blocks for about 90 iterations gives each block about 18 updates.
   - The only in-competition precedent C cites for learned macro search is sidhulyalkar. I checked the repo: the
     learned model is explicitly unpromoted ("contains no promoted learned weights yet"), and the only rating it
     reports is the entry value of 600, which the README calls "not evidence".
   - The OscarLegoupil 378-22 result is route-selector+micro against its own plain v4 base in a local round-robin.
     The repo reports no ladder score, so it is no evidence about the 2,000+ band.
5. **Day 1 is overloaded.** It covers a trace logger, a lineage classifier, TP-dip segmentation plus Sequitur, a
   genome schema, a compiler and an executor skeleton. D2 then needs to invert traces into θ, an ill-posed inverse
   problem, and pass recognition tests b1–b3 and c (TOST over 384 games). RL cannot start before D3.

### Serious
- **The claim that the champion "makes exactly one plan decision" (the route at step 144) is contradicted by
  measurement.** B's probe found v7 unit actions diverge across seeds and opponents anywhere from step 151 to 459,
  and 9–18% of turns differ, 3–15% of market turns. The README says the strength lives in those reactive layers.
  A 40-dimensional calendar genome does not represent them.
- **The developmental-linguistics layer is decorative.** Each row maps to an ordinary engineering step: "live
  exposure" means use fastsim, and "sensitive period" means freeze the grammar. None of it changes a design decision
  or adds measurable value, but it adds build time (the lineage classifier and the b2/b3 detector tests).
- **The gates cannot be measured at the planned sample sizes.** "≥6% vs farm2945" for top 25% has the same problem as
  in A. The ">50% over 800 games vs v7" target is sound, but the D3 "+8 pp after 12 iterations" gate is measured on the
  same noisy population the ES is overfitting to.
- **The objective is a win-count reward against pool clones.** This is the Halite IV overfitting mode C itself cites.
  The PSRO-lite population weights come from a 14-game census.
- **C's throughput figure is 3,700 games/h, while A's is 6,700/h.** Both are plausible, but an overnight ES run takes
  all 8 cores and freezes every other evaluation.

### Is it 0-to-1?
Only partly. The genome and selector are our own, but the executor emits lineage phrases, and the pass criterion is
being recognised as the lineage.

## Where the rivals' attacks on B are fair
- **C: "per-turn BC+PPO never beat BC".** B does not run PPO. B's route past the teacher is exact endgame and shed code
  plus AWR weighting, not on-policy RL. The remaining risk is that DAgger labels from an 85% open-loop teacher are
  noisy. B's own proposal lists this as risk #1.
- **A: "the scale we lack".** B generates its data with fastsim, so this does not apply. But A's census point is valid:
  B's body, which does the routing and logistics, faces the same micro problem as A's scheduler. The D1 oracle gate
  (the body reaches ≥95% of the teacher's bank when executing the teacher's own intents) is where B could fail the same way.

## Ideas worth stealing
From A:
- Use the op-mix census as body KPIs in B's D1 oracle test: CARE and COLLECT counts, movement share ≤ 50%, 0 escapes,
  ≤ 2 weeds.
- Check the market model against the interpreter on 1k random states before trusting the market-head features.
- Assign units by greedy value per travel-turn, nearest unit first.
- Use the TacTex reservation rule and Almgren–Chriss splitting for B's exact liquidation code.
- Add a GSPRT stopping rule (elo0 = 0, elo1 = +30) on top of the 200-game paired gates, to save compute.
- Run a BT calibration round-robin on D1 to re-derive the win-rate gates.
- Use the project knapsack as a fallback prior when H1 capex confidence is low.
- From the 2945 digest (CAPHARV, VT1, SL2): skip CARE on day 28, hire no hands on day 29 unless there is wool, and
  harvest before tonight's production when stored yield would overflow.

From C:
- Use the 1,077 unit-day programs as B's intent vocabulary. Top-300 coverage of 72% is a ready-made label space for H2/H3.
- Condition the opening latent z on the shops revealed by step 144, not on predicted ones, since shops cannot be
  predicted (13.4% vs 12.5% random).
- Use common random numbers with antithetic pairs, and TOST equivalence for the oracle test (body vs teacher).
- Weight the evaluation population by the ladder census (11 fork, 2 aurax7, 1 other).
- Run a small ES over only B's few post-hoc scalars (AWR β, DART ε, switch day, shed margin), where a low-dimensional
  search has enough signal.
- Hold the shed invariant (shed plus hands ≤ margin by hour 22). This matches NOTES E6b: the leak is produce in
  units' hands.
