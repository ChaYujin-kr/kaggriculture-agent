# Track C: search in the simulator, then distil it into rules ("Macro-CEM + Rollout Oracle → Decision Tree")

Verdict up front: per-turn deep RL (PPO/IMPALA) **cannot** be built and validated in 4 days on 8 CPUs with no GPU. The version of "RL" that fits the budget searches a **macro-plan space** directly against the real engine: cross-entropy/ES over about 40 macro parameters, plus a rollout oracle at shop-reveal days. It then distils the result into a depth-4 decision tree and a small knob set. All of this runs on top of our own exact executor.

## 1. Lineage of philosophy

**General baseline: "RL where you can afford it, search and rules where you can't."**
- Lux S1 winner (IMPALA+UPGO+TD-λ, frozen-teacher KL): the RL beat their own rules agent within a month, but it trained "overnight most nights" for months on a dual-GPU PC. https://github.com/IsaiahPressman/Kaggle_Lux_AI_2021/blob/main/README.md. **We don't have that compute.**
- Lux S2 winner: a rule-based agent with role dispatch and **multi-step forward simulation** (FUTURE_LEN≈25). https://deepwiki.com/ryandy/Lux-S2-public
- Kore 2022 imitation route: about 200M observations, a transformer, and 2×A100. This is out of reach. https://github.com/khanhvu207/kore2022. (The Kore 1st-place and Halite write-ups on kaggle.com did not render for me, so I make no claims about them.)

**Narrower topic (Kaggriculture itself): layer strategy inherited**
- Per-turn PPO attempted in this competition (atsushi11o7): a transformer over 35 action slots, BC then PPO in JAX. Self-play "policy collapses", the reward is too sparse ("majority of updates within 720 steps had almost no usable learning signals"), and the author's own conclusion is **"improvement over BC remains unconfirmed."** https://github.com/atsushi11o7/kaggriculture/pull/13, /pull/15, /pull/16, https://raw.githubusercontent.com/atsushi11o7/kaggriculture/main/src/kaggriculture/policy/README.md
- Macro PPO (prince22466): PPO picks one of 5 herd thresholds once per day on days 3–17 (about 15 decisions per game, 45 features), with reward `sign(margin)+0.05·tanh(margin/1e4)`. https://github.com/prince22466/Co_AMAP/pull/33. This is effectively a contextual bandit, and black-box search solves that more cheaply.
- "Do not ask ML to relearn deterministic mechanics": an exact execution controller, a parametric macro policy, population CEM, and a once-a-day macro selector. https://github.com/sidhulyalkar/kaggriculture. **This is the architecture we adopt.**
- Public field: a pure-RL neural agent costs 225 s per game (local digest `every-community-agent-one-arena`). The 7-turn-rescue agent (historical LB 2800+) runs up to 128 simulations in the last 7 turns (local digest). **Runtime search is proven to fit the 1 s limit.**
- Front-running and trace ideas decay about 30–40 ELO per day (https://github.com/zansued/kaggriculture-ai-agent). Adaptive macro decisions are better than frozen tapes.

**Tuning philosophy**
- ES/CEM with **common random numbers** is invariant to delayed rewards and long horizons and parallelises trivially. https://arxiv.org/abs/1703.03864. Our version: same seeds for every candidate, both seats.
- Rolling-horizon evolution over **macro-actions** with a forward model and short rollouts. https://arxiv.org/abs/2103.15090
- Distillation: VIPER / Q-DAgger extracts small decision trees from an oracle, weighting states by Q-gap. https://arxiv.org/abs/1805.08328. Our oracle is a fastsim rollout, not a DNN.
- House rule, learned the hard way (NOTES.md): sd is about $9k per game, and 40-game "wins" reversed at 80 games. Win count comes first, and every gate is re-checked on a fresh seed range.

## 2. Core design (all own code)

**State.** Only public obs plus own private data. Derived features:
- Day and hour; which shops are unlocked (one draw every 3 days, with replacement, at most 8).
- **Exact demand drain per product**: each shop instance takes 1 unit per product every 4 turns (2 units for a single-product shop), and the town centre takes 1 unit per product per day.
- Market inventories and the exact `market_price()` curve (copied from the engine).
- Own herd, crops, shed stock and cash; the opponent's herd, crops and land (farms are public). The opponent's bank at step 1 gives the lineage tag (E2a).

**L1 Macro plan θ (about 40 numbers, decided at hour 0 each day):**
- Herd-target schedule for cows, sheep and geese by day (animal costs 400/500/300; cows yield from day 8 every 2 days, sheep from day 6 every 3, geese from day 4 every day; +1 yield for care on a fed production day).
- Land-purchase days: NE $1k, SW $2k, SE $4k.
- Crop mix per quadrant (wheat/carrot/tomato/strawberry/melon).
- Hire curve (n-th hire costs fib(n)).
- Per-product reservation fraction and a feed buffer (unfed animals escape after 2 days).

θ is warm-started by **macro-distilling the champion**. From our replays and champion self-play we log macro events only, not the tape. Example, replay 112292352 (bank $149k): cows 2 and sheep 2 on day 0, land on days 6 and 11, sheep ramp over days 7–11, hires 5 rising to 12. That fingerprint is about 15 events plus a hire curve, so it fits θ.

**L2 Exact executor (deterministic, no learning):**
- Greedy/Hungarian assignment of farmer and hands to tile tasks by Manhattan cost (water, harvest, fertilize, feed, care, collect fertilizer, DIG weeds).
- **Shed-aware carrying**: capacity is 100, and end-of-day overflow is *discarded*. E6 measured this leak at $0.9–7.4k per game. The executor schedules DROP and SELL before the carried stock overflows.

**L3 Market controller:**
- Sells when the marginal price exceeds the reservation price.
- The reservation price comes from known drain plus a forecast of opponent supply (from their visible herd and crops).
- Respects 10 orders per turn and the per-unit lockstep with seat-0 priority.

**Endgame:** step 718 is the last step whose actions execute. Rollout search over steps 690–718 uses a cloned engine state (deepcopy 0.3 ms, engine step about 0.1 ms) and 64–128 sims, following the 7-turn-rescue precedent. The target is the $3.5–13.3k last-day gap measured against the top teams.

**Context decisions (the distilled part).** At days 3, 6, 9, 12 and 15 (shop reveals) a depth-≤4 tree picks one of 6 macro options: +cows, +sheep, +geese, buy land, shift crops to shop-demanded products, or hold.

## 3. Data & compute (measured on this machine today)

| Measurement | Value |
|---|---|
| fastsim, pass vs pass (engine only) | **0.072 s/game** |
| fastsim, v7_endgame vs v55 | **2.06 s/game** (3 seeds) |
| fastsim, agents/main.py mirror | 2.50 s/game |
| deepcopy of engine state | 0.31 ms |
| cores | 8 |

- Realistic throughput is about **3.5 games/s**, which is roughly 12k games/hour or about 150k games per 12 h night.
- CEM with 24 candidates × 8 seeds × 2 seats = 384 games per generation takes about 110 s, so about 30 generations per hour.
- Rollout oracle: a branch re-runs the game from step 0 with a fixed seed (engine and opponents are deterministic), about 2 s per branch. 6 options × 6 seeds × 5 reveal days × 150 games = 27k games, about 2.2 h.
- Replays: 52 files, 1.6 GB, used only for macro fingerprints and last-day liquidation stats.
- Needs: `pip install scikit-learn` (offline tree fitting only; the tree is exported as if/else). No torch.

## 4. Four-day build plan (Sep 24–27; Sep 28–30 reserved for ladder)

All gates are paired: same seeds, both seats, Wilson 95% lower bound, and fresh seeds for confirmation.

- **D1: L2 executor, L3 market, θ interface, fingerprint extractor.** Also download the Kaggriculture Episodes `teams.csv` to pin the ladder percentiles.
  - **G1 (macro-replay test):** θ set to the champion's fingerprint reaches ≥80% of the champion's bank on the same seeds against the same opponent (10 seeds), and wins ≥90% of 20 games against `agents/main.py`.
  - **KILL** if under 70% of the champion's bank. That would mean the executor is the bottleneck, which is what killed the old planner.
- **D2: overnight CEM** against the opponent mix {v7_endgame, hybrid2965, farm2945, v55, self}. Fitness = wins + 0.2·tanh(margin/10k).
  - **G2:** ≥50% against farm2945 over 80 games.
  - **KILL** if <25%.
- **D3: rollout oracle labels, VIPER tree, and runtime endgame search.**
  - **G3:** ≥55% against hybrid2965 and ≥35% against v7_endgame (80 games each). Max turn time under 300 ms.
- **D4: re-run CEM on continuous knobs with the tree frozen, then validate** on 160 fresh games per opponent.
  - **G4:** ≥50% against v7_endgame, then hand off.

## 5. Staged targets → win rates (estimates, to be calibrated on D1 with teams.csv)

Known ratings: agents/main.py v2 ≈ 499, farm2945 unmodified ≈ 2065, hybrid2965 unmodified ≈ 2370, v7 lineage ≈ 2640. I assume a logistic 400-point/10× scale. I estimate from the public lineage's spread that top 50% ≈ 1700, top 25% ≈ 2150 and top 12.5% ≈ 2500; this estimate is unverified.

| Target | Required local result |
|---|---|
| Top 50% | ≥95% vs main.py and ≥15% vs farm2945 |
| Top 25% | ≥55% vs farm2945 and ≥30% vs hybrid2965 |
| Top 12.5% | ≥70% vs farm2945, ≥60% vs hybrid2965 and ≥35% vs v7_endgame |
| Final goal | >50% vs v7_endgame over 160 games (both seats, fresh seeds) |

## 6. Top 5 risks and mitigations

1. **Executor efficiency gap.** This is the old failure: our planner finished $110k behind the tape agents. Mitigation: gate G1 runs first and isolates execution from strategy. If G1 fails, the track stops on D1.
2. **CEM overfits the seed set or the opponent pool.** Mitigation: rotate seeds each generation, keep a held-out seed range, and include a mirror opponent.
3. **Low statistical power** (sd about $9k). Mitigation: count wins, use 80–160 paired games, use Wilson bounds, and never accept a 40-game result.
4. **Rollout oracle assumes the opponent stays fixed.** Mitigation: label with 3 opponents and keep only labels where all 3 agree on the best option. Q-gap weighting stops close calls from reaching the tree.
5. **1 s act timeout during runtime search.** Mitigation: a hard 250 ms budget, anytime search, and falling back to the tree's choice.

## Why this beats the other two routes

- It is the only route whose learning signal is the **real engine and the real win condition** rather than imitation targets. BC on tapes desyncs: raw tapes score $0 against a live opponent (NOTES).
- It fits the **measured** budget of about 150k games per night, where per-turn PPO needs a GPU and was still unconfirmed over BC in this very competition.
- The output is readable rules plus about 40 knobs, which the existing CEM/knob tooling can keep tuning after submission.
- It has the cheapest kill test (G1 on D1), so we lose at most a day if the premise is wrong.
