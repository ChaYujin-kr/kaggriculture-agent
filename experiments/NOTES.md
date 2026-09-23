# Experiment notebook

Free-form experiments on top of the current champion (`research/pool/aurax7_v7.py`). Nothing here is
submitted unless it beats the champion on fresh seeds against the public pool.

Evaluation contract for every entry below: same seeds for both arms, both seats, win count first and
margin only as a tie-break, and a separate validation seed range before any claim is believed.

---

## E1 — Feed denial ("wheat squeeze")

**Idea.** The market is shared. Animals eat one wheat per day and most agents top up by buying wheat
from the market, where the price rises as inventory falls (`sqrt`, below-target 0.80, T=400). Buying
wheat early should raise the opponent's feed bill. The competition discussion reports a real case of
an opponent's sheep starving after a rival bought 14-19 wheat at turn 0.

**Cost to us.** We also buy wheat, so the squeeze raises our own bill too; we can resell later at the
inflated price, which recovers part of it (buy price is quoted at post-buy inventory, sell at
pre-sell, so a round trip against an unchanged market nets zero — the profit only comes from the
opponent paying more in between).

**Status.** Implemented in `agents/layer_adversary.py` (`squeeze_*` settings). **Failed: 0/24.**
Buying 6 wheat/turn over steps 0-48 lost 1.7k-4.0k per game against every opponent including the
mirror. The squeeze raises our own feed bill at the same time, and our lineage buys more wheat than
the opponents do, so we pay for the attack twice. Not pursued further.

---

## E2 — Opponent lineage fingerprint

**Idea.** Opponent actions are hidden, but their bank is public, so their opening spend is
recoverable from their money at step 1-2. The top-2 ladder teams open with `BUY_ANIMAL COW 1` +
`BUY_PRODUCT WHEAT 5` (~$525 spent); our lineage opens with a wheat buy/sell round trip (~$0-40
spent). That is a clean separator for "is this the top-2 branch or a clone of us".

**Use.** Log it first (E2a), then condition behaviour on it (E2b) only if the log shows the tag is
reliable.

**Status.** Logging implemented (`tag_only` mode).

---

## E5 — Poisoning the opponent's inference ("unpredictable move")

**Idea.** The ladder opponents are not learners, so there is nothing to surprise — but they *do*
infer our sales from the shared market: `our sales = -(inventory delta) - town draw - their sales`.
A 1-unit `BUY_PRODUCT` costs almost nothing (buy quoted at post-buy inventory, sell at pre-sell) yet
shifts the quantity they are differencing, which should mistime their front-running.

**Result. Failed: 10/24 against a 15/24 baseline on the same seeds.** Injecting one unit every 7
turns (steps 120-690) lost ground against every opponent, worst in the mirror (0/6). Two reasons:
the cash and price impact is not actually free, and these agents keep farming their tape regardless
of what their estimator concludes — the estimator only steers a small sale-timing layer.

**Read-across.** The market is close to zero-sum here: every deviation we tried costs us more than
it denies the opponent. Attacks that work in multiplayer (where a third party absorbs the cost) do
not carry over to a two-player shared market.

---

## E3 — Counter-agent against the top-2 branch

Deferred until E2 shows the tag is reliable and E1/E4 show whether market aggression pays at all.

---

## E4 — Endgame focus (from the margin curve)

Measured margin per day against three pool opponents (mean over 6 games each): we gain ~$1,000/day
through days 10-19, stall at days 20-24, and **lose** ground on day 26 (-$1,504) and day 28
(-$1,291). The endgame liquidation is where the champion leaks. Being tuned separately in
`tuning/best_endgame.json`.

---

## Results log

| date | experiment | setup | result |
| --- | --- | --- | --- |
| 2026-09-23 | E0 timing check | champion vs morewheat, per-turn wall clock | mean 1.5 ms, max 75 ms vs a 1 s limit — no timeout risk, so "slow agent skips turns" is ruled out |
| 2026-09-23 | E0 shop RNG | 200k seeds, predict 3rd shop from first two | 13.4% vs 12.5% random — shop unlocks cannot be anticipated, only reacted to |
| 2026-09-23 | E2a lineage tag | opponent bank at step 1, 4 opponents + 2 top-2 tapes | clean separation: our lineage spends $0, public forks $157, the top-2 branch $540 — the tag is reliable |
| 2026-09-23 | E1 wheat squeeze | 6 wheat/turn, steps 0-48, vs 4 opponents x 3 seeds x 2 seats | 0/24, -1.7k to -4.0k per game |
| 2026-09-23 | E5 inference noise | 1 unit every 7 turns, steps 120-690, same setup | 10/24 vs 15/24 baseline |
