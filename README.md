# Kaggriculture Agent

Work on Kaggle's [Kaggriculture](https://www.kaggle.com/competitions/kaggriculture) simulation
competition: a two-player, 30-day (720-turn) farming-economy game where the agent with the larger
final bank wins. Final standings come from a single Bradley-Terry fit over every episode played
between still-active submissions, run two weeks after the 2026-09-30 deadline.

## What is here

| Path | What it does |
| --- | --- |
| `agents/main.py` | Our own agent: market-aware tile planner + greedy task scheduler |
| `agents/layer_fert.py` | Gap-filling layer (fertilizer/water) for a tape-driven base agent |
| `scripts/fastsim.py` | Headless match runner on the official interpreter — same results, ~20x faster |
| `scripts/league.py`, `compare.py`, `roundrobin.py` | Paired evaluation (same seeds, both seats) |
| `scripts/tune.py` | Evolution-strategy tuning of our agent's PARAMS |
| `scripts/knob_screen.py` | Finds which of an agent's constants actually change play |
| `scripts/hoist_literals.py` | Rewrites hard-coded thresholds into tunable module constants |
| `scripts/tune_thresholds.py`, `tune_flags.py` | Greedy search over those knobs, scored by win count |
| `scripts/replay_summary.py`, `replay_actions.py`, `clone_diff.py` | Ladder replay analysis |
| `scripts/make_tape_agent.py` | Turns a replay seat into a sparring agent |
| `scripts/daily_refresh.py` | Daily: pull new public agents, duel the champion, submit if better |

Setup: `python -m venv .venv`, `.venv\Scripts\pip install -r requirements.txt`, then put a Kaggle
API token in `.env` (`KAGGLE_API_TOKEN=...`; git-ignored).

## What the game rewards (measured, not assumed)

- Animals produce one fertilizer per day for free; fertilizer sells near $100 at base.
- Labor is cheap: the n-th hire of a day costs fib(n), so ~10 hands cost $143/day.
- Each product's market is a limited reservoir. Melon has no shop demand, so ~160 units drive it to
  the floor; wheat and eggs absorb large volumes. Milk and strawberry pay best when shops unlock.
- Step 718 is the last step whose actions execute, and the last day's harvest is not auto-dropped,
  so everything must be dropped and sold before it.
- Shop unlocks are unpredictable: knowing the first two shops predicts the third with 13.4%
  accuracy (random = 12.5%), so agents can only react to shops, never anticipate them.

## Results

| Submission | Ladder rating |
| --- | --- |
| Our planner v1 / v2 | 437 / 499 |
| Public "2945 Farm" (unmodified) | ~2065 |
| Public "2965 Master Hybrid" (unmodified) | 2370 |
| Same + our knob search (8 constants) | **2642** |
| Public "shop-router-reactive-v7" (current champion) | pending |

## What did not work, and why

- **Our own planner.** It reached ~80k against the built-in baselines but lost to the public tape
  agents by ~110k. Scratch-built planning could not close that gap in the time available.
- **Replacing a tape agent's late game with our planner.** Every switch point lost to the unmodified
  base (day 27 switch: -7k), so the tape's endgame is genuinely better than ours.
- **An extra hired hand for fertilizer gap-filling.** The base already fertilizes 80% of production
  days; the hand's wages (-2.5k) exceeded what it added.
- **Low-power tuning.** Per-game sd is ~$9k, so 40-game trials "found" improvements that reversed at
  80 games. Every keep is now re-validated on fresh seeds before it is submitted.
- **Raising the sheep-to-cow conversion cap.** The conversion's gate conditions never fire in play.
- **Raw tape sparring partners.** Replayed top-team tapes score $0 against a live opponent, because
  the farm desyncs; only the reactive layers carry a tape agent's strength.

## Notes on the competition's meta

The public scene is one lineage: a shared library of 41 recorded 720-turn routes plus reactive
layers. Ladder opponents at our rating are near-clones — in ten episodes, three opponents matched
our actions exactly for the first 121 steps, and nine of ten games were decided by under $1,000.
The top two teams are the same lineage as each other (identical for six steps) but a different
branch from ours, and the one that ran more cows and geese won their head-to-head by $14k, almost
all of it in milk and eggs.

All public agents used here are Apache-2.0 with their upstream notices retained; submissions that
are unmodified public code say so in the submission message.
