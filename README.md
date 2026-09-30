# Kaggriculture Agent

Work on Kaggle's [Kaggriculture](https://www.kaggle.com/competitions/kaggriculture) simulation
competition: a two-player, 30-day (720-turn) farming-economy game where the agent with the larger
final bank wins. Final standings come from a single Bradley-Terry fit over every episode played
between still-active submissions, run for about two weeks after the 2026-09-30 deadline.

## Write-ups

- **[Kaggriculture Field Notes](https://claude.ai/artifact/BYMHh4TorbGE6sY7PouutP)**: the game, how
  it is scored, the ladder's lineages, our evaluation tools and the measurements behind the final pair.
- **[Kaggriculture Retrospective](https://claude.ai/artifact/Jo6pavKahQu6zJc78KgX7G)**: the ten days
  told from the commit log and all 13 submissions, with the lessons we keep.

## What is here

| Path | What it does |
| --- | --- |
| `agents/main.py` | Our own agent: market-aware tile planner + greedy task scheduler |
| `agents/layer_fert.py` | Gap-filling layer (fertilizer/water) for a tape-driven base agent |
| `scripts/fastsim.py` | Headless match runner on the official interpreter: same results, ~20x faster |
| `scripts/league.py`, `compare.py`, `roundrobin.py` | Paired evaluation (same seeds, both seats) |
| `scripts/gauntlet.py` | Lineage-weighted pool (`research/gauntlet.json`) with walls a candidate must hold |
| `scripts/tape_eval.py` | Replays candidates against tapes of the opponents on our real ladder boards |
| `scripts/make_tape_agent.py` | Turns one seat of a replay into an open-loop tape agent |
| `scripts/tune.py` | Evolution-strategy tuning of our agent's PARAMS |
| `scripts/knob_screen.py` | Finds which of an agent's constants actually change play |
| `scripts/hoist_literals.py` | Rewrites hard-coded thresholds into tunable module constants |
| `scripts/tune_thresholds.py`, `tune_flags.py` | Greedy search over those knobs, scored by win count |
| `scripts/ladder_fingerprint.py`, `ladder_mix.py` | Name opponents by opening hash; measure the lineage mix by rating band |
| `scripts/ladder_harvest.py`, `ladder_track.py` | Harvest our ladder games; track the active pair by time and opponent lineage |
| `scripts/ladder_replay.py` | Replays our ladder games locally on their real seeds and seats |
| `scripts/replay_summary.py`, `replay_actions.py`, `clone_diff.py` | Ladder replay analysis |
| `scripts/highlight_gif.py`, `pixel_sprites.py` | Renders a replay as an animated GIF with our own 16x16 pixel art |
| `scripts/daily_refresh.py` | Daily: pull new public agents, duel the champion, gate on the gauntlet (dry-run) |

Setup: `python -m venv .venv`, `.venv\Scripts\pip install -r requirements.txt` (pins
`kaggle-environments==1.32.7`, the ladder's engine), then put a Kaggle API token in `.env`
(`KAGGLE_API_TOKEN=...`; git-ignored).

## What the game rewards (measured, not assumed)

- Animals produce one fertilizer per day for free; fertilizer sells near $100 at base.
- Labor is cheap: the n-th hire of a day costs fib(n), so ~10 hands cost $143/day.
- Each product's market is a limited reservoir. Melon has no shop demand, so ~160 units drive it to
  the floor; wheat and eggs absorb large volumes. Milk and strawberry pay best when shops unlock.
- Step 718 is the last step whose actions execute, and the last day's harvest is not auto-dropped,
  so everything must be dropped and sold before it.
- Shop unlocks are unpredictable: knowing the first two shops predicts the third with 13.4%
  accuracy (random = 12.5%), so agents can only react to shops, never anticipate them.
- Against 2300+ teams our losses were level on money through day 15 and opened up in the selling
  phase from day 18. Selling ahead of the agent's own plan (`_S738_LOOK`) recovered part of it;
  following the stronger farms into tomatoes made things worse, because both farms share one market.

## Results

Ratings on 2026-09-30. A retired submission's rating froze when it left the pair, and the ladder
deflated in the last week, so late ratings are lower than the same agent would have had on 09-22.

| Submission | Date | Ladder rating |
| --- | --- | --- |
| Our planner v1 / v2 | 09-21 | 437 / 499 |
| Public "2945 Farm" (unmodified) | 09-21 | 2065 |
| Public "2965 Master Hybrid" (unmodified) | 09-22 | 2369 |
| Same + our knob search (8 constants) | 09-22 | **2644.5** (our peak) |
| Public "shop-router-reactive-v7", unmodified / + endgame gates | 09-23 | 1664 / 1631 |
| The Shepherd's Ledger + knobs (auto-submitted) | 09-25 | 1962 |
| hybrid2965 resubmitted | 09-25 | 1830 |
| hybrid + counter-D, `_V92_P_TOP` 8 / Shepherd's Ledger, `_V92_P_TOP` 6 | 09-27 | 1802 / 1653 |
| **harvest-ledger (ttv1) + knobs** (final pair) | 09-28 | 1953 |
| **Same + `_S738_LOOK=10`, `_CXTB_MIN_REVENUE=7500`** (final pair) | 09-30 | climbing from 600 |

The last submission beat its parent on replayed ladder tapes by +15 wins and 0 losses over 340
boards, 152 of them held out from the choice.

## What did not work, and why

- **Our own planner.** It reached ~80k against the built-in baselines but lost to the public tape
  agents by ~110k. The gap was execution (83 CARE actions against the champion's 410), and a
  from-scratch effort started on 09-23 did not close it before the deadline.
- **Replacing a tape agent's late game with our planner.** Every switch point lost to the unmodified
  base (day 27 switch: -7k), so the tape's endgame is genuinely better than ours.
- **An extra hired hand for fertilizer gap-filling.** The base already fertilizes 80% of production
  days; the hand's wages (-2.5k) exceeded what it added.
- **Low-power tuning.** Per-game sd is ~$9k, so 40-game trials "found" improvements that reversed at
  80 games. Every keep is now re-validated on fresh seeds before it is submitted.
- **Picking by a pool that lacked the ladder's lineages.** v7 beat everything locally and lost about
  1,000 rating points on the ladder to V52/V53 near-clones, which the pool did not contain.
- **Trusting local copies of an opponent lineage.** Public cha22 files lost every game to the
  Shepherd's Ledger; the ladder versions beat it in 72% of 93 games.
- **Splitting v7's day-27 bulk sales into slices.** Its own score fell by about 1,000.
- **Raising the sheep-to-cow conversion cap.** The conversion's gate conditions never fire in play.
- **Tapes on a different seed.** A replayed tape scores $0 on another seed because the farm
  desyncs. On the game's own seed it reproduces the ladder exactly, which is what `tape_eval.py` uses.

## Notes on the competition's meta

The public scene is a set of forks: recorded 720-turn routes plus reactive layers, shared between
authors. We name lineages by an md5 over each agent's actions on turns 1-48. In the 2450-2850 band
(games 09-19..09-23) hybrid2965 was 28.5% of opponents, the a-wonderful-life/cha22 family 27.1%,
V52/V53 10.3% and the 2945 family 10.0%; about 23% stayed unnamed. The lineages form a cycle
(v7 beats hybrid, hybrid beats V53, V53 beats v7), and the top 23 teams run private agents.

All public agents used here are Apache-2.0 with their upstream notices retained; submissions that
are unmodified public code say so in the submission message.
