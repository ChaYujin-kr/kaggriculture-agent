# Critique by track A (narrowing) of tracks B (transplant) and C (episode RL)

Sources checked: both proposals, `experiments/NOTES.md`, `README.md`, the interpreter
(`.venv/.../kaggle_environments/envs/kaggriculture/kaggriculture.py`, since `research/rules.txt` holds
only the legal rules and no game mechanics), `research/pool/aurax7_v7.py`,
`zero2one/B_transplant/tools/probe_teacher.py`, two digests, and two cited URLs.

## A shared mechanic error (B and C; A's text is loose on this too)

`_new_plant` sets `consecutive_unwatered: 1`, with the comment "planting day counts as unwatered".
A crop that is not watered on the day it is planted **turns into a weed at the first refresh**.
B ("water/feed before the second missed refresh (2 misses kill plants and animals)") and C ("Plants
weed, and animals escape, after 2 missed days") both schedule against a one-day grace period that
fresh plantings do not have. Animals start at `consecutive_unfed: 0`, so they do get the grace
day. Any executor that prioritises by "second miss" will lose new plantings. A has to fix this in
its own WATER deadline as well.

---

## Track B: brain transplant (clone v7 with GBDT heads)

### Fatal flaws
1. **The teacher is a tape, so the clone is a tape. This is not 0-to-1.** B measured it itself: v7's
   unit actions are identical across seeds and opponents up to step 151–459, and 82–91% of turns
   are identical. With `step` among the features, a GBDT reaches its agreement targets (H2 ≥ 90%,
   H4 ≥ 80%) by learning step → action. In other words, it memorises the route library in a
   different file format. The "opening latent z" that the student fixes at step 0 is the route id.
   The user allowed learning *from* the champion's behaviour, but a policy whose labels come from
   one tape and whose inputs let it index that tape is a fork by distillation.
2. **DART and DAgger cannot work on an open-loop teacher.** DART helps only if the noised supervisor
   *recovers*, and a tape keeps playing its script. If 5–15% of intents are dropped, the later tape
   actions refer to tiles that were never planted or animals that were never bought. The README
   records that replayed tapes "score $0 against a live opponent, because the farm desyncs". B's
   own risk #1 concedes that shadow labels may be "nonsense", and the proposed fix (a validity
   filter) removes exactly the off-trajectory states that DAgger exists to cover. Covariate shift
   is therefore left unsolved.
3. **The D1 oracle gate asks the body to do what our planner could not.** To pass, a 700-line
   greedy min-distance body must turn macro intents into ≥ 95% of the teacher's bank. The measured
   gap between `agents/main.py` and the champion (73k vs 170k solo) is almost entirely *execution*:
   CARE 83 vs 410, COLLECT_FERTILIZER 60 vs 372, movement share 64% vs 50%, cows escaping, and 15
   weeds. The champion's routes hold hand-packed unit routings that a tile-intent abstraction
   throws away. If the gate fails, the fallback is "per-unit op classes", which means cloning each
   unit's tape step by step and makes flaw 1 worse. B has to solve A's whole problem (the body)
   before its learning adds anything, and it has less time left to do it.

### Serious issues
- **"The teacher cannot react to shop RNG" is false.** `aurax7_v7._router` fires at `step>=144`
  and picks one of 41 routes from `_R108_SHOP_ROUTES` keyed by the unlocked shops. It fires again
  at `step>=648` for the endgame. The divergence B measured from step 151 onwards *is* that
  reaction. The planned edge from a "shop-conditioned market head" is mostly already in the teacher.
- **The "leaks" B plans to exploit have already been worked.** The day-26/28 losses (E4) were
  measured before the endgame retune. `v7_endgame` includes the fix (40/48 mirror, 71/80 vs
  pool). E6a (capacity beliefs) and E6b (sell-down guard) both gave no gain. The hands-aware shed
  guard is a sound idea, but it is untested and worth at most $0.9–7.5k in some games. That is a
  weak basis for a "floor = champion, ceiling above it" claim.
- **AWR over final margin has no credit assignment.** Every one of 720 turns shares one episodic
  return with sd ≈ $9k, and the multi-teacher pool is near-clones (9/10 ladder games are decided by
  < $1k). The advantage weights will mostly encode seed luck.
- **Size and latency are unverified.** 6 heads × 300 trees × depth 7 is up to about 230k decision
  nodes. Exported as Python if/else, that is roughly 5–10 MB of source, and the size cap is
  "unknown" by B's own admission. Pool agents are about 1 MB. The tile heads run per tile (up to
  100 tiles) per turn, so the "1–3 ms" figure understates cost by about 100×.
- **Training data volume is understated.** 3k games × 720 turns × 100 tiles is about 216M tile
  rows for H2. That is feasible only with heavy subsampling on an i5-8265U (4 physical cores),
  with 3–5 GB on disk, and "minutes per head" has not been measured.
- **The cited evidence does not transfer.** GRF (checked): the SL agent used about 333 games / 1M
  frames on 2080Ti/1080 GPUs for about 2 days and reached ">900", well below the top. That is not
  "teacher-level in hours on CPU". The Kaggriculture PR B relies on (atsushi11o7 #16) says
  improvement over BC is "unconfirmed". The Lux S1 and Kore successes cloned *reactive* experts
  with GPU training.
- **The plan is too full.** D1 contains the featurizer, the intent extractor, body v0, 3k logged
  games and the oracle test. D3 expects the top-12.5% gate (≥ 40% vs farm2945) after two DAgger
  rounds.
- **Evaluation.** The D2 gates on agreement percentages are proxies with no known link to winning.
  The final gate says ≥ 50% over 200 games in §4 but ≥ 55% in §5. With SE ≈ 3.5 pp, neither is
  decisive against the champion.

### Ideas worth stealing
- **An oracle or ablation gate for execution quality.** A should run its scheduler on the
  *champion's* project plan (herd, crop blocks, hire curve read from logs) to separate scheduler
  loss from planner loss on D1.
- **`probe_teacher.py`-style logging** (about 2,100 games/h) to pull plan-shape priors (herd
  timing, hires per day, sell-bucket sizes by product and shop state) and per-day op-mix KPIs for
  A's knapsack warm start. This uses the data but copies no action tape.
- **Projected end-of-day shed total including unit hands and pending harvests.** A already plans
  this, and B's formulation is precise.
- **The "stable across opponents" criterion** (findings digest) for accepting any plan-shape
  prior.
- **Shadow-agreement diagnostics:** log where A's macro choices differ from v7 in similar states,
  and use the differences as hypotheses for races. They are not labels.

---

## Track C: episode-level ES over a "multilingual plan grammar"

### Fatal flaws
1. **The executor is the planner that hit the wall.** C copies "the scheduler from
   `agents/main.py`" as its fallback executor. That component delivers 73k solo against the
   champion's 170k, with CARE 5× lower, escapes and weeds. ES over a 40-dim genome cannot fix
   execution the genome does not control. C's own D2 KILL ("< 15% vs farm2945: executor failure,
   same wall as the planner at 500") is the likely outcome, because nothing in D1–D2 works on the
   executor.
2. **"Fluency" measures cloning, and the phrases are tape.** The lexicon is 1,077 distinct unit-day
   programs cut from the 41 recorded routes, emitted "phrase-first". The recognition tests (b1–b3, c)
   pass when we are *indistinguishable from aurax7 or a fork*, which is a fork's acceptance
   criterion, not a 0-to-1 one. The MDL cap (≤ 10% of tape bytes; pool files are about 1 MB) still
   allows about 100 KB of verbatim phrases. Being mistaken for aurax7 also has no value in itself:
   the census shows the aurax7 family lost both of its games at 2640, by 11k–20k.
3. **Open-loop by construction.** C compiles θ into a day calendar at step 144 and runs it
   "deterministically". The README records that tapes without their reactive layers score $0
   live, and that only the reactive layers carry a tape agent's strength. C's design moves the
   strength back into an open-loop script.
4. **The ES signal-to-noise ratio does not support the budget.** Each iteration is 16 antithetic
   pairs × 16 games. With a win-count reward, the win-rate SE per perturbation arm is about
   12 pp, while a σ-step probably changes win probability by a few pp. Block rotation over 5 blocks
   across about 90 overnight iterations gives about 18 noisy updates per block. The D3 GO gate
   ("+8 pp after 12 iterations") cannot be resolved at that sample size. This is the Halite IV
   failure and our own 40-game reversal, repeated.

### Serious issues
- **D1 is impossible.** It includes a trace logger, a lineage classifier, TP-dip segmentation plus
  Sequitur, the lexicon, the genome schema, the compiler and an executor skeleton. D2 adds
  "invert traces into θ", an inverse problem with no stated method: the tapes encode per-unit
  routing that a 40-dim genome cannot express.
- **Redundant work.** The E2 step-1 bank tag already separates lineages cleanly ($0 / $157 / $540).
  A leave-one-agent-out classifier as the D1 GO gate spends a day re-solving a solved problem,
  whose downstream use (E3) is still deferred.
- **The developmental-linguistics layer is decorative.** Each citation maps to something trivial
  (for example "live exposure" becomes "log from fastsim") or to a constraint that works against
  winning (a "brake" toward the clone prior). None of it adds a mechanism for beating v7.
- **The D2 gate is at top-12.5% level on day 2.** ≥ 40% vs farm2945 for the first inverted genome
  is set far too high, so the KILL is the expected branch.
- **The population is thin.** The PSRO weights (11/14 fork, 2/14 aurax7) come from a 14-game census.
  There are also minor inconsistencies (53 vs 52 replays, and the cutoffs are borrowed from A
  without verification).
- **Correct points, to be fair:** the step-144 and 648 router claim is right (`_router` in
  `aurax7_v7.py`), the CRN and antithetic design is sound, and C states its odds honestly.

### Ideas worth stealing
- **The shop-conditioned plan selector at the day-6 unlock**, as in v7's router. A's strategic
  knapsack should re-solve at each shop unlock (it does), and A can precompute a small table of
  project-mix priors per first-two-shops cluster, tuned offline.
- **CRN plus antithetic ± perturbations** in A's SPSA step, with the reward
  `sign(m) + 0.05·tanh(m/1e4)` (win count first, margin as a tie-break).
- **A census-weighted population gate** (fork-heavy mix) instead of a single-opponent gate.
- **The unit-day program census as an efficiency KPI.** Compare the distinct-program count and
  movement share of A's units against the champion.
- **Test b3, "can the pool's front_run or sales estimator exploit us?"**, turned into a check that
  A's sell schedule is not predictable to the pool's market-ledger estimator.
- **A shed invariant held by hour 22 including hands**, though E6a warns that a lower cap alone
  gave nothing. The fix is to route produce to the shed, not to shrink the cap.

---

## Bottom line
Both rivals end up borrowing their competence from the tape lineage. B distils v7's tape into
trees, and C replays tape phrases through a genome. Both still depend on an execution layer of the
same kind that capped us at ~500, and neither gives it any dedicated build time. A attacks that
layer directly, using measured deficits (CARE, fertilizer collection, escapes, weeds, movement
share) as day-1 KPIs. A should nevertheless adopt B's oracle-style execution gate and C's
shop-cluster selector and CRN tuning.
