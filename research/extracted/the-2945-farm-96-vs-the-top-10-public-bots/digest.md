<div style="background:linear-gradient(135deg,#0e2a1f 0%,#17472f 58%,#23633f 100%);border-radius:16px;padding:26px 30px 24px;color:#ffffff;">
<div style="font-size:12px;letter-spacing:0.16em;text-transform:uppercase;color:#bfe8cf;font-weight:700;">Kaggriculture &middot; open agent &middot; v9/4</div>
<div style="font-size:34px;font-weight:800;line-height:1.15;margin:10px 0 10px 0;color:#ffffff;">🌾 The 2945 Farm</div>
<div style="font-size:16px;line-height:1.6;color:#e6f4ea;max-width:800px;">My ladder agent, open-sourced in full: the exact file that scored <b>2944.7</b>, every layer explained, the experiments that failed, and the one problem I could not solve.</div>
</div>

| | |
|:--|:--|
| **Live ladder** | **2944.7** for this exact file (submission 56269928), 2956.6 for its predecessor, 128–73 over its first 201 ladder games |
| **vs the 10 top-scoring public notebooks** | **519 – 21** (96.1%) over 270 fresh seeds × both seats, and 80 – 0 in the official engine. The best public notebook scores 2750.2 |
| **vs 17 reactive bots** | **645 of 680** games won (94.9%) in a closed-loop gauntlet |
| **Runtime** | standard library only, about 3 ms per turn on average, CPU |

**To use it:** *Copy & Edit → Save Version → Save & Run All → Submit*, and pick `submission.tar.gz`. The last cell writes it.

[code cell 1: 35 lines]
```
import ast, contextlib, hashlib, io, json, math, os, sys, tarfile, tempfile, time, warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import HTML, Image, display

warnings.filterwarnings("ignore")

# One palette and one quiet chart style for the whole notebook.
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = (
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948")
QUIET = "#cfcdc6"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS, "axes.linewidth": 0.8, "axes.labelcolor": INK2,
    "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlecolor": INK, "axes.titlelocation": "left",
    "axes.titlepad": 26, "axes.labelsize": 10.5, "axes.grid": True, "axes.axisbelow": True,
    "grid.color": GRID, "grid.linewidth": 0.7, "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 9.5, "ytick.labelsize": 9.5,
    "xtick.labelcolor": INK2, "ytick.labelcolor": INK2, "legend.frameon": False, "legend.fontsize": 9.5,
    "font.size": 10.5, "figure.dpi": 110, "lines.linewidth": 2.0, "lines.solid_capstyle": "round",
})


def subtitle(ax, text):
    """Grey line under a left-aligned bold title."""
    ax.annotate(
```

[code cell 2: 34 lines]
```
# Head-to-head results against the agents behind the 10 highest-scoring public notebooks
# (Code tab, 2026-09-19). Several of those notebooks run byte-identical agents, so ten
# notebooks are nine distinct opponents. Method in section 5.
H2H = pd.DataFrame([
    ("Demand-Preserving Turn Sale Timing", "tetsutani", 2750.2, 55, 5, 3446),
    ("First in Line: Stock Into Income", "Alperen Aydın", 2746.0, 54, 6, 3196),
    ("V47 Reactive Market Coordination", "Ahmed Berat Özer", 2686.0, 55, 5, 3698),
    ("V48 Clear the Queue", "Ahmed Berat Özer", 2670.4, 55, 5, 3534),
    ("V38 Smarter Feed, Stronger Margins", "Ahmed Berat Özer", 2625.2, 60, 0, 7379),
    ("V39 Ready Before the Rush", "Ahmed Berat Özer", 2621.2, 60, 0, 7198),
    ("v34 Observed Market Timing", "Ahmed Berat Özer", 2601.6, 60, 0, 10801),
    ("V41 Review Candidate", "Ahmed Berat Özer", 2586.4, 60, 0, 7188),
    ("v31 Production and Sale Priority", "Ahmed Berat Özer", 2575.6, 60, 0, 10929),
], columns=["notebook", "author", "public_score", "wins", "losses", "mean_margin"])

fig, ax = plt.subplots(figsize=(10.4, 4.9))
rate = 100 * H2H.wins / (H2H.wins + H2H.losses)
y = np.arange(len(H2H))[::-1]
ax.barh(y, rate, height=0.62, color=BLUE, zorder=3)
ax.axvline(50, color=INK2, lw=0.9, zorder=4)
for yi, r, w, l in zip(y, rate, H2H.wins, H2H.losses):
    ax.text(r + 1.2, yi, f"{w}–{l}", va="center", color=INK, fontsize=10, fontweight="bold")
ax.set_yticks(y, [f"{n}  ·  {a}  ·  {s:.0f}" for n, a, s in zip(H2H.notebook, H2H.au
```

## Why I'm publishing it

This agent is the end of a chain that ran through this Code tab. My [Public State Router](https://www.kaggle.com/code/thomastschinkel/kaggriculture-93-8-win-rate-public-state-router) became part of the chassis of Ahmed Berat Özer's V25 to V48 series. That series took in yhay81's shop routes, prvsiyan's sheep and tomato projects, Dmitrii Gluzdov's stock reservations and a dozen more ideas. I took V39/V40 from that chain, added my own layers, and grafted in six more from the public V100.24 release. **v9/4 is the result.**

It is far ahead of the public notebooks and still clearly behind the top 10 of the leaderboard (3,000+). Publishing it should raise everyone's baseline and move the discussion to the part of the game nobody has solved in public yet (section 6).

**Contents**
1. The agent: one file, standard library only
2. Watch it play the #1 public notebook (a full season, in this notebook)
3. How it works: a recorded route with reflexes
4. Eight lessons that won games
5. Evidence
6. The problem I could not solve
7. What did not work
8. Five lessons about evaluation
9. Submit

## 1 · The agent: one file, standard library only

The next cell writes `main.py`: 5,760 lines and 856 KB, **byte-for-byte the file behind submission 56269928**. Its input is collapsed to keep this page readable. Click *Code* to expand it. Half of the bytes are a single line, the sale-timing library from lesson 4.5. All upstream Apache-2.0 notices are kept verbatim at the top of the file.

[code cell 5: %%writefile main.py, 5760 lines]

[code cell 6: 23 lines]
```
EXPECTED_SHA256 = "bfee70e9daaebeae0737a880f1df8f1c60d0783c59af620136cc0d28ef482bc7"
# %%writefile uses the platform's line endings; this keeps a local Windows run byte-identical to Kaggle's.
source = Path("main.py").read_bytes().replace(b"\r\n", b"\n")
Path("main.py").write_bytes(source)
digest = hashlib.sha256(source).hexdigest()
assert digest == EXPECTED_SHA256, f"main.py differs from the submitted file: {digest}"

tree = ast.parse(source)
modules = sorted({a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
                 | {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module})
assert set(modules) <= set(sys.stdlib_module_names), modules

# Kaggle's loader executes the file and runs the LAST callable in its namespace (section 8).
namespace = {}
exec(compile(source, "main.py", "exec"), namespace)
entry = [v for v in namespace.values() if callable(v)][-1]
assert entry.__name__ == "agent", entry.__name__
del namespace

lines = source.count(b"\n")
print(f"main.py   {len(source):,} bytes, {lines:,} lines, sha256 {digest[:12]}…  (submission 56269928)")
print(f"imports   {', '.join(modules)}  (standard library only)")
print(f"entry     {entry.__name__}()  = the last callable, which is exactly what Kaggle runs")
```

## 2 · Watch it play the #1 public notebook

The opponent is **tetsutani's [Demand-Preserving Turn Sale Timing](https://www.kaggle.com/code/tetsutani/demand-preserving-turn-sale-timing)**, the highest-scoring public notebook on 2026-09-19 (2750.2). Its output is attached to this notebook as an input. We play four new seeds, alternating seats, in the official `kaggle_environments` engine. The engine is instrumented with an exact **money ledger**: every unit sold or bought and every hire, at the engine's own price. The ledger is a small context manager, and you can copy it into your own harness. If the input is missing (for example in a fork without it), the cell falls back to a mirror match.

The cell first installs `kaggle-environments` 1.32.7, so **Internet must be on**. Kaggle's image still ships 1.29.3, whose Kaggriculture engine is out of date (section 8). Without Internet the games are skipped and the rest of the notebook still runs.

[code cell 8: 120 lines]
```
import subprocess
from importlib.metadata import version


def vtuple(v):
    return tuple(int(x) for x in v.split(".")[:3])


# Kaggle's image ships kaggle-environments 1.29.3, whose Kaggriculture engine predates the current
# rules. Install 1.32.7 (the current release) without touching any other package.
if vtuple(version("kaggle-environments")) < (1, 32, 7):
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--no-deps", "kaggle-environments==1.32.7"],
                   capture_output=True)
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    import kaggle_environments
    from kaggle_environments import make
    import kaggle_environments.envs.kaggriculture.kaggriculture as K
DEMO = vtuple(kaggle_environments.__version__) >= (1, 32, 7)
print("kaggle-environments", kaggle_environments.__version__,
      "" if DEMO else "-> too old and could not be upgraded (Internet off?): skipping the live games")

OURS = str(Path("main.py").resolve())
TETSU_V65 = "95b02b9b7ca124c92844b7c2907b4ceacf2cce7773890cdf32aba84f20eababe"  # sha256 of its main.py


def attached_agents(roots=("/kaggle/input", "../input")):
    """Every main.py under the notebook inputs, also inside .tar.gz archives."""
    for root in map(Path, roots):
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*")):
            if p.name == "main.py":
                yield p.read_bytes(), p
            elif p.name.endswith(".tar.g
```

### A season in 30 frames

Both farms at noon on each day of the first game. **Left: v9/4. Right: the opponent.** Dots are workers: the farmer, plus the hands hired that day, who all vanish at midnight. The shed sits at the centre and is not a tile.

[code cell 10: 78 lines]
```
TILE = {  # key -> (fill, letter, letter colour); letters keep the map readable without colour
    "WHEAT": (YELLOW, "W", INK), "CARROT": (ORANGE, "C", INK), "TOMATO": (RED, "T", "white"),
    "STRAWBERRY": (MAGENTA, "S", INK), "MELON": (GREEN, "M", "white"), "GOOSE": (AQUA, "g", INK),
    "COW": (VIOLET, "c", "white"), "SHEEP": (BLUE, "s", "white"), "COOP": ("#d6ece0", "", INK),
    "PASTURE": ("#d6ece0", "", INK), "WEED": ("#bdb691", "x", INK), "EMPTY": ("#f2ede3", "", INK),
    "LOCKED": ("#dedcd5", "", INK),
}
LEGEND = [("W", "wheat"), ("C", "carrot"), ("T", "tomato"), ("S", "strawberry"), ("M", "melon"),
          ("g", "goose"), ("c", "cow"), ("s", "sheep"), ("x", "weed")]
KEY_OF = {v[1]: k for k, v in TILE.items() if v[1]}


def tile_key(tile):
    if tile is None:
        return "EMPTY"
    if tile == "LOCKED":
        return "LOCKED"
    kind = tile.get("kind")
    if kind == "PLANT":
        return tile.get("crop", "EMPTY")
    if kind in ("COOP", "PASTURE"):
        return tile.get("animal") or kind
    return "WEED" if kind == "WEED" else "EMPTY"


def draw_farm(ax, farm, label):
    n = len(farm["tiles"])
    for yy in range(n):
        for xx in range(n):
            fill, letter, lc = TILE[tile_key(farm["tiles"][yy][xx])]
            ax.add_patch(plt.Rectangle((xx + 0.04, yy + 0.04), 0.92, 0.92, color=fill, lw=0))
            if letter:
                ax.text(xx + 0.5, yy + 0.53, letter, ha="center", va="center", color=lc, fontsize=10.5,
                      
```

### The cash race

The two farms in the animation look almost identical, and that is not a rendering bug. tetsutani's agent and v9/4 descend from the same recorded routes (section 3), so the fields are planted alike. The games are decided by the reflexes: when to sell, which animal to buy, carrot or wheat, how many hands to hire. Both farms put almost every dollar back into land, animals and seeds for the first ten days. After that, the lead builds a few hundred dollars at a time.

[code cell 12: 43 lines]
```
def bank(g):
    b = np.array([[st[0]["observation"]["farms"][p]["money"] for p in (0, 1)] for st in g["env"].steps])
    return np.arange(len(b)) / 24, b[:, g["seat"]], b[:, 1 - g["seat"]]


def cash_race():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.4, 4.3), gridspec_kw={"width_ratios": [1, 1.15]})
    days, ours, theirs = bank(games[0])
    a1.plot(days, theirs / 1000, color=ORANGE, lw=1.8, label=OPP_NAME)
    a1.plot(days, ours / 1000, color=BLUE, lw=2.0, label="v9/4")
    jump = int(np.argmax(np.diff(ours) > 5000))
    L = games[0]["ledger"]
    sold = L[(L.player == games[0]["seat"]) & (L.op == "SELL") & L.step.between(jump - 1, jump + 1)]
    top = sold.groupby("item").amount.sum().idxmax().lower() if len(sold) else "harvest"
    a1.annotate(f"first big sale: {top}", (days[jump + 1], ours[jump + 1] / 1000), xytext=(-8, 26),
                textcoords="offset points", ha="right", color=INK2, fontsize=9.5,
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
    a1.set_xlabel("day")
    a1.set_ylabel("bank ($ thousands)")
    a1.set_xlim(0, 30)
    a1.legend(loc="upper left")
    a1.set_title(f"Bank balance, seed {games[0]['seed']}")
    subtitle(a1, "flat while everything is reinvested, then a steady climb")

    for g in games:
        days, ours, theirs = bank(g)
        eod = [d * 24 + 23 for d in range(len(days) // 24)] + [len(days) - 1]   # end of each day
        lead = (ours[eod] - theirs[eod]) / 1000
        a2.plot(days[eod], lead, color
```

### Where the money comes from

The ledger makes the season readable. Revenue by product for both farms, averaged over the four games, and what each side spent it on. Read it together with the town shops above. Premium books (strawberry, milk, wool, melon) pay well only for whoever sells first, which is what sections 4.4 and 4.5 are about.

[code cell 14: 52 lines]
```
PRODUCTS = ["STRAWBERRY", "MILK", "WOOL", "MELON", "WHEAT", "CARROT", "EGG", "TOMATO", "FERTILIZER"]
COSTS = {"BUY_SEED": "seeds", "BUY_ANIMAL": "animals", "BUY_PRODUCT": "wheat & fertilizer bought",
         "HIRE": "hired hands", "BUY_LAND": "land"}


def money_book():
    rows = []
    for g in games:
        L = g["ledger"]
        for side, p in (("v9/4", g["seat"]), (OPP_NAME, 1 - g["seat"])):
            Lp = L[L.player == p]
            sold = Lp[Lp.op == "SELL"]
            for item in PRODUCTS:
                s = sold[sold["item"] == item]
                rows.append((side, "revenue", item.lower(), s.amount.sum(), len(s)))
            for op, label in COSTS.items():
                rows.append((side, "cost", label, -Lp.loc[Lp.op == op, "amount"].sum(), 0))
    book = pd.DataFrame(rows, columns=["side", "kind", "line", "amount", "units"]).groupby(
        ["side", "kind", "line"], sort=False).sum().reset_index()
    book["amount"] /= len(games)
    book["units"] /= len(games)

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.2, 4.6), gridspec_kw={"width_ratios": [1.35, 1]})
    for ax, kind, order in ((a1, "revenue", [p.lower() for p in PRODUCTS]), (a2, "cost", list(COSTS.values()))):
        sub = book[book.kind == kind]
        y = np.arange(len(order))[::-1]
        for off, side, colour in ((0.2, "v9/4", BLUE), (-0.2, OPP_NAME, ORANGE)):
            vals = sub[sub.side == side].set_index("line").loc[order, "amount"].values
            ax.barh(y + off, vals / 1
```

## 3 · How it works: a recorded route with reflexes

At its core v9/4 is a **route replayer**. The public lineage recorded strong 720-turn action schedules: where every worker walks, what gets planted, what is sold when. The router picks a schedule from the town's first shop unlocks. On top of that sits a stack of **reflexes**. Each is a small layer that reads the public observation, edits one kind of decision, and passes the action on to the next layer. Every layer wraps the previous `agent` and ends with `agent = globals().pop('agent')`. Section 8 explains why that last line matters.

| Layer | What it edits | In one line | From |
|:--|:--|:--|:--|
| Route tapes and shop router | everything | recorded 720-turn schedules, re-selected as shops unlock | yhay81 · Ahmed Berat Özer (V39/V40) |
| Chassis repairs | workers, market | weed repair, sale lead, stock reservations, end-of-season planner, V219 tomato and V233 six-sheep projects | Ahmed · Dmitrii Gluzdov · prvsiyan · aurax7 · tetsutani · lucifer19 |
| OPENING · CTRTABLE | turns 0–8 | cash-safe opening wheat trade, plus two counters keyed on public turn-2 state | v9 |
| RACE · RACEPX · RACEGATE | sale timing | race the rival's premium sales, but never into a glutted book | v9 |
| PREDICT · PREDICT2 | sale timing | forecast rival sales from 451k recorded sale events | v9 |
| COURIER · OVERFLOW · SHEDROOM | cargo | nothing is lost to the midnight shed drop | v9 · Ahmed (V43) · V100.24 |
| CARROT · CARROT2 | planting | wheat becomes carrot where the tile's simulated harvest pays | v9 · V100.24 |
| HERD · HERD2 · COWSWAP | animal purchases | goose, cow or sheep, from a supply-and-demand model of both farms | v9 · V100.24 |
| FERT | fertilizing | carried fertilizer goes on young wheat and carrots | v9 |
| ORDERPRI2 | order of market list | the product most exposed to a rival batch sells first | V100.24 |
| CAPHARV | harvesting | harvest an animal before its cap overflows | V100.24 |
| SL2 · VE1 · VT1 | sheep-expansion labour | one hand instead of two, day 11 instead of 12, nothing wasted on day 29 | v9/4 |

**How v9/3 became v9/4.** Every step below was measured on a fixed panel of recorded games from top players. The numbers are *games flipped*: `+a / −b` means a losses turned into wins and b wins turned into losses. Anything with more flips against than for was rejected (section 7).

| Step | Added | Flipped | Panel |
|:--|:--|:--:|:--|
| sl2 | one hand for the sheep expansion on non-harvest days | +15 / −0 | 188 affected games |
| ve1 | expansion on day 11 in yarn-store towns | +8 / −1 | 150 eligible games |
| vt1 | nothing wasted on the last two days | +3 / −0 | 273 affected games |
| g_co | CARROT2 + ORDERPRI2 | +54 / −10 | 3,296 recorded games |
| c_ch | CAPHARV | +20 / −0 | 1,000 recent top-25 games |
| d_sr | SHEDROOM | +16 / −2 | same 1,000 |
| e_hc | HERD2 + COWSWAP | +10 / −4 | same 1,000 |
| f_lib | sale library rebuilt from the 1,000 new games | +32 / −13 | same 1,000 |

## 4 · Eight lessons that won games

### 4.1 Labour is priced at the margin

Hired hands vanish at midnight. The *n*-th hire of a day costs fib(*n*−1), so the first hands are nearly free and the late ones are not. The route's own crews are hired first, which made the two hands of the six-sheep expansion (prvsiyan's V233 annex) hires **#12 and #13: $144 + $233 = $377 a day**. On days without a wool harvest one hand can do that work. **SL2** keeps one hand on those days, but only when the complete feed-and-care tour provably fits into the day, and it collects fertilizer on the way. In an audited game hires fell from 36 to 23 with all 108 wool and every feed kept. **+15 / −0** in the affected towns.

[code cell 17: 19 lines]
```
cost = [1, 1]                       # the engine's hire cost: fib(n-1) for the n-th hire of the day
while len(cost) < 15:
    cost.append(cost[-1] + cost[-2])
fig, ax = plt.subplots(figsize=(10.4, 3.4))
x = np.arange(1, 16)
colors = [BLUE if n in (12, 13) else QUIET for n in x]
ax.bar(x, cost, width=0.7, color=colors, zorder=3)
for n, c in zip(x, cost):
    if n >= 9:
        ax.text(n, c + 8, f"${c}", ha="center", va="bottom", fontsize=9.5,
                color=INK if n in (12, 13) else INK2, fontweight="bold" if n in (12, 13) else "normal")
ax.set_xticks(x, [f"#{n}" for n in x])
ax.set_ylabel("cost of this hire ($)")
ax.set_title("What the n-th hire of a day costs")
subtitle(ax, "fib(n−1) per hire, reset every morning. Blue: the sheep expansion's two hands, after the route's crews")
ax.set_ylim(0, 690)
ax.grid(axis="x", visible=False)
plt.tight_layout()
plt.show()
```

### 4.2 Sheep placed one day earlier harvest five times, not four

Sheep first produce 6 days after placement, then every 3 days, and the season ends after day 29. Placed on day 12, they produce on days 18, 21, 24 and 27. Placed on day 11, they produce on 17, 20, 23, 26 **and 29**. That is a fifth harvest for one more day of feed and labour. **VE1** commits the expansion on day 11 in towns where two of the first three shops are yarn stores. It waits for the route's own land purchase first and checks that the cash covers every purchase the route still plans. The early wool also reaches the shared book before the rival's does: our cash rises about **$850** and the rival's falls about **$1,400** per affected game. **+8 / −1**. On fresh seeds against reactive opponents it beat the day-12 version **24 – 0**.

**VT1** handles the last two days. No production refresh follows day 29, so feeding and caring on that day buy nothing. On day 29 the expansion hires no hand unless wool is waiting, and then only one hand that harvests. On day 28 it skips CARE, because that care would be banked after the last production has already happened. **+3 / −0.**

[code cell 19: 21 lines]
```
fig, ax = plt.subplots(figsize=(10.4, 2.9))
for yy, placed, label in ((1, 12, "placed day 12 (before)"), (0, 11, "placed day 11 (VE1)")):
    prod = list(range(placed + 6, 30, 3))
    ax.plot([placed, 29.4], [yy, yy], color=GRID, lw=6, solid_capstyle="round", zorder=1)
    ax.scatter([placed], [yy], s=90, facecolor=SURFACE, edgecolor=INK2, lw=1.6, zorder=3)
    ax.scatter(prod, [yy] * len(prod), s=150, color=BLUE, zorder=4, edgecolor=SURFACE, linewidth=2)
    for d in prod:
        ax.text(d, yy + 0.3, str(d), ha="center", va="bottom", fontsize=9.5, color=INK)
    ax.text(29.9, yy, f"{len(prod)} wool harvests", va="center", fontsize=10.5, color=INK, fontweight="bold")
    ax.text(9.6, yy, label, va="center", ha="right", fontsize=10.5, color=INK2)
ax.set_xlim(5, 33.5)
ax.set_ylim(-0.6, 1.8)
ax.set_yticks([])
ax.set_xticks(range(10, 30, 2))
ax.set_xlabel("day (the season ends after day 29)")
ax.spines["left"].set_visible(False)
ax.grid(False)
ax.set_title("One day earlier is one more harvest")
subtitle(ax, "open circle: sheep placed · filled: production day (6 days after placement, then every 3 days)")
plt.tight_layout()
plt.show()
```

### 4.3 Care is most of what an animal makes

FEED keeps an animal alive, but CARE is where most of the output comes from. Every day an animal is both fed and cared for banks one bonus unit, paid out at its next production. A cared cow gives **3 milk** per production instead of 1, a sheep **4 wool** instead of 1, and a goose **2 eggs** instead of 1. There are two catches. An animal that goes unfed on its production day loses the whole bank. And stored product stops growing at 6 (cow, sheep) or 4 (goose). **CAPHARV** handles the second catch. When a worker is about to care for an animal (or collect its fertilizer) whose stored yield would overflow at tonight's production, and nobody harvests that tile later in the day, it harvests instead and sells the saved units. **+20 / −0** on 1,000 recent top-25 games.

### 4.4 Your market list is an order book

Both players' market lists run in lockstep: order #1 of each list first, one unit at a time from each side at the same quote, then order #2, and so on, up to 10 orders a turn. The position of an order in your list therefore decides who sells into whose glut:

| slot | you | rival | what happens |
|:--:|:--|:--|:--|
| 1 | `SELL MILK 6` | `SELL WHEAT 30` | your 6 milk sell at the pre-glut price |
| 2 | `SELL WHEAT 20` | `SELL MILK 12` | the rival's milk sells into your units |

**ORDERPRI2** estimates the rival's unsold stock from public information only: their tile harvests and their recovered sales. It moves the product most exposed to a rival batch to the front, and when all ten slots are full it swaps out the weakest order.

### 4.5 Premium books fall off a cliff, so race

Prices are set by market inventory. Staples barely move when a farm floods them. Strawberries, milk, wool and melons fall to the **$1 floor** after 60 to 160 units of surplus, less than one field's worth. The first seller of a lot takes the price and the second sells into the crash.

[code cell 21: 25 lines]
```
def price_cliff():
    glut = np.arange(0, 251)
    fig, ax = plt.subplots(figsize=(10.4, 3.9))
    series = [("WHEAT", YELLOW), ("MELON", GREEN), ("MILK", VIOLET), ("STRAWBERRY", MAGENTA), ("WOOL", BLUE)]
    for item, colour in series:
        p = K.MARKET_PARAMS[item]
        price = np.array([K.market_price(item, p["I0"] + g) for g in glut])
        floor = int(np.argmax(price <= 1)) if (price <= 1).any() else None
        label = f"{item.lower()} (\\${p['base']} base" + (f", \\$1 after {floor} units)" if floor else ", never floors)")
        ax.plot(glut, price / p["base"] * 100, color=colour, lw=2.0, label=label)
    ax.set_xlabel("units sold above the market's equilibrium inventory")
    ax.set_ylabel("sell price, % of base")
    ax.set_ylim(-3, 105)
    ax.set_xlim(0, 250)
    ax.legend(loc="upper right")
    ax.set_title("The price cliff: premium goods hit the $1 floor, wheat shrugs")
    subtitle(ax, "from the engine's own price function (kaggriculture.market_price); town shops drain the surplus slowly")
    plt.tight_layout()
    plt.show()


if hasattr(K, "market_price") and hasattr(K, "MARKET_PARAMS"):
    price_cliff()
else:
    print("This engine version has no market_price(); the chart needs kaggle-environments 1.32.7.")
```

Rival sales are public if you look for them. Every turn, **rival_sold = inventory′ − inventory + town_draw − own_sold**, which is exact above the $1 floor. **RACE** watches that signal and pulls the route's own planned sales of the same product forward, up to 40 turns ahead and starting on day 8. **RACEPX** and **RACEGATE** keep it from racing into a book that already trades below base. **PREDICT** goes one step further: it matches the rival's recent sales against a library of **451k sale events from 1,000 recent top-25 games** and sells just before the best-matching recorded streams say the rival will.

### 4.6 The shed has 100 slots, and midnight shreds the rest

At the end of every day all cargo that workers carry drops into the shed, and anything past 100 items is destroyed. **OVERFLOW** (ported from Ahmed's V43) sells, at hour 23, exactly the shed stock the drop would destroy. **SHEDROOM** does the same for spare goods at hours 22–23. **COURIER** walks premium cargo to the shed before midnight so it sells today rather than tomorrow. These layers break ties: SHEDROOM flipped 18 games, and every one of them was decided by less than about $1,000 (**+16 / −2**).

### 4.7 Carrot or wheat? Ask the tile, not the price

A watered wheat plant yields 4 units and a carrot yields 3 for $10 more seed. A simple price ratio ("carrot when it is worth 1.8× wheat") fires far too rarely. **CARROT2** (from V100.24) instead simulates the route's own future visits to each tile. Will someone water it? Will someone harvest it before it decays? It swaps `PLANT WHEAT` for `PLANT CARROT` only where 3 carrots − $20 beats 4 wheat − $10 at the prices ahead, and it keeps two days of wheat for the herd. Together with ORDERPRI2 this was **+54 / −10** over 3,296 recorded games. Replayed against my previous version's real ladder opponents, the record went from 80–25 to **95–10**.

### 4.8 The opening had six dollars of slack

Every route tape opened with a wheat round trip and then ran days 0–9 with about **$6** of spare cash. Against openings that dump wheat into the same market slots, that round trip ended turn 1 up to $75 short. Wheat and hire orders then failed, the herd went hungry, and by days 5–8 the strawberry orders failed too: 18–21 plants instead of 33, a loss of $20k–65k. v9 replaced it with a cash-safe trade, checked against 6,648 recorded openings, and v9/3 settled on **BUY 20 / SELL 15** at turn 0 (+107 / −0 on the replay panel).

## 5 · Evidence

### 5.1 Head-to-head against the top-scoring public notebooks (fresh, 2026-09-19)

The top chart. I took the 10 highest-scoring public notebooks in the Code tab, extracted each `main.py` byte-exactly from its current version and loaded it with Kaggle's own last-callable rule. Ten notebooks turned out to be nine distinct agents: two pairs are byte-identical, and one "decompressed" copy of V48 plays move-for-move like V48. Each opponent played **30 fresh seeds × both seats**. Each seed's eight shop unlocks were drawn at random and forced identically for every opponent (common random numbers), and games ran on a C++ re-implementation of the engine for speed.

| Opponent | Best public score of this agent | v9/4 W–L | Mean margin |
|:--|--:|:--:|--:|
| Demand-Preserving Turn Sale Timing (tetsutani) | 2750.2 | 55–5 | +3,446 |
| First in Line: Stock Into Income (Alperen Aydın) | 2746.0 | 54–6 | +3,196 |
| V47 Reactive Market Coordination (Ahmed Berat Özer) | 2686.0 | 55–5 | +3,698 |
| V48 Clear the Queue (Ahmed Berat Özer) | 2670.4 | 55–5 | +3,534 |
| V38 Smarter Feed, Stronger Margins (Ahmed Berat Özer) | 2625.2 | 60–0 | +7,379 |
| V39 Ready Before the Rush (Ahmed Berat Özer) | 2621.2 | 60–0 | +7,198 |
| v34 Observed Market Timing (Ahmed Berat Özer) | 2601.6 | 60–0 | +10,801 |
| V41 Review Candidate (Ahmed Berat Özer) | 2586.4 | 60–0 | +7,188 |
| v31 Production and Sale Priority (Ahmed Berat Özer) | 2575.6 | 60–0 | +10,929 |
| **Total** | | **519–21** | |

In this game, swapping seats usually replays the same game (26 of the 30 seeds gave identical results in both seats), so read the table as **270 independent seeds: 258 won, 9 lost, 3 split**.

### 5.2 Confirmation in the official engine

The C++ simulator is fast, but it is not the real engine. So I replayed the four strongest matchups in `kaggle_environments` itself, with its own shop draws: 10 new seeds × both seats against each opponent. **v9/4 won all 80 games**, 20–0 against each of Demand-Preserving, First in Line, V47 and V48, by +$2.0k to +$2.1k on average. Here too, swapping seats replayed the same game on 9 of 10 seeds, so read it as 40 of 40 seeds. Section 2 plays four more of these games live, in this notebook.

### 5.3 Closed loop against 17 reactive bots (2026-09-18)

Public V40, V41, V46, V47 and V48, both V100.24 variants, shop-router-reactive-v7, pipe-7, pipe-8, shop-router-0913, master-engine-v53, best-agent and four more bots: **645 of 680** games won, 20 seeds × both seats each. The weakest matchups were V100.24 (32/40 and 34/40), V47 (34/40) and V48 (34/40).

### 5.4 The live ladder

This exact file climbed to **2944.7** (submission 56269928, 2026-09-16) and went **128–73** over its first 201 ladder games. It won every recorded game against the public V43 opening (14–0) and the V45 opening (11–0), and only 4 of 26 against *adaptive* farms that open with cows or four hired hands. That cluster is the subject of the next section. A fresh submission of the same file on 2026-09-18 was at 2908 and still climbing when I published this: a rating depends on the field it climbs through (section 8).

## 6 · The problem I could not solve

v9/4 beats every public notebook, yet against seven of today's top-10 teams it went **0 – 36** on the ladder (September 15–17). I replayed 24 of those losses in the engine with an exact ledger (both players' real action streams) to see where the money went. **We lead until day 10**, because the melon race is ours, **and lose it all after day 11.**

[code cell 25: 26 lines]
```
phase = pd.Series({"days 0–10": 7.8, "days 11–19": -9.3, "days 20–29": -10.1})
product = pd.Series({"tomato": -6.0, "wool": -3.3, "egg": -2.7, "carrot": -2.5, "strawberry": -1.7,
                     "milk": 1.5, "melon": 2.4, "fertilizer": 2.6}).sort_values()
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.2, 3.9), gridspec_kw={"width_ratios": [1, 1.5]})
for ax, s in ((a1, phase), (a2, product)):
    y = np.arange(len(s))[::-1]
    ax.barh(y, s.values, height=0.6, color=[BLUE if v > 0 else RED for v in s.values], zorder=3)
    ax.axvline(0, color=INK2, lw=0.9, zorder=4)
    for yi, v in zip(y, s.values):
        inside = abs(v) > 4                       # long bars carry their label inside
        x = v - (0.3 if v > 0 else -0.3) if inside else v + (0.25 if v > 0 else -0.25)
        ha = ("right" if v > 0 else "left") if inside else ("left" if v > 0 else "right")
        ax.text(x, yi, f"{v:+.1f}k".replace("-", "−"), va="center", ha=ha, fontsize=9.5,
                color="white" if inside else INK, fontweight="bold" if inside else "normal")
    ax.set_yticks(y, s.index)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("v9/4 minus winner, $ thousands per game")
    lim = max(abs(s.values)) + 3.6
    ax.set_xlim(-lim, lim)
a1.set_title("By phase")
subtitle(a1, "net −11.6k per game")
a2.set_title("By product (revenue)")
subtitle(a2, "24 live losses to top teams, exact engine ledger")
plt.tight_layout()
plt.show()
```

The biggest single hole is **tomatoes**. The farms that beat us buy about **9 tomato seeds from day ~12** and hold about 10 tomato tiles on day 20. We buy 1.6, and the first on day 18. They sell 71 tomatoes at $114 each. We sell 7, at $316, because nobody else is selling into that book.

Every tomato program I built lost:

* a tomato overlay on the route's wheat tiles from day 13: **0 gained / 85 lost**
* a 20-tile tomato patch on new land: **0 / 56**, because the crews cannot water 20 more tiles
* loosening the gate of the existing tomato project: **+4 / −11**

The route tape is the constraint. Its workers are busy from dawn to dusk, so a tomato program needs a different *labour* plan, not just a different crop choice. The adaptive farms don't replay a tape. They plan the crew around the crops.

**If you have a tomato program that works on top of a route tape, or you know why the adaptive farms win the second half, I would love to hear it in the comments.**

## 7 · What did not work

Negative results are the cheapest thing I can give you. Each of these cost me hours.

| Idea | Result |
|:--|:--|
| Tomato overlay on the route's wheat tiles (day 13) | 0 gained / 85 lost |
| 20-tile tomato patch on new land | 0 / 56. Labour-bound, not land-bound |
| Hold premium goods back for a better price (reservation wrapper) | −$7.5k to −$34k per game. The tape's logic breaks when its sales are overridden |
| Rebase all v9 layers onto public V48 | 497 vs 506 of 840 panel games |
| Let an adaptive planner take over the farm after day 12 or day 18 | 6–24 and 7–23, against 24–6 for the tape |
| A from-scratch, demand-driven planner (v10, three days of work) | live score 990–1,578, against 2,945 for the tape |
| Skip the day-11 strawberries when no berry shop is open | −$1.5k a game. The berries I didn't sell were sold by the rival |
| Extra hands to fertilize young wheat | $144+ a day per hand, more than the extra wheat earns |
| Sheep expansion in towns with only one yarn store | −$11k to −$17k for us, only −$2k to −$3k for the rival |

## 8 · Five lessons about evaluation

**1. Kaggle runs the *last* callable, not `agent`.** The loader executes `main.py` and takes `[v for v in namespace.values() if callable(v)][-1]`. Redefining `agent` later in the file doesn't move it, because a dict keeps the key's original position. V47's real entry point is `_y_agent_shopherd` and V48's is `_e335_agent`. My local harness imported `agent` by name, so for every public file from V46 on it silently evaluated a stale inner bot. Every layer in this file ends with `agent = globals().pop('agent')`, which re-inserts the name at the end. The check in section 1 uses Kaggle's own rule.

**2. Frozen replays flatter you.** Across five promotions my replay panel rose from 589 to 648 wins per 1,000 games, while the live score went 2956.6 → 2944.7. A recorded opponent can't react. If your agent starves it, for example by making one of its purchases fail, the replay keeps playing its recorded moves into nothing and your "win" is an artifact. Filter panels to games where the frozen opponent keeps at least 95% of its recorded score, and trust closed-loop games against reactive bots more.

**3. Identical code, different scores.** The V47 agent sits byte-for-byte in two public notebooks, scored 2686.0 in one and 2579.3 in the other. V39 scored 2621.2 and 2581.0. A single submission's rating moves about ±100 with its matchmaking luck, so don't chase ±30. Decide on head-to-head data.

**4. Every sale is also denial.** Premium books are shared. When I removed 103 strawberries from a route, I lost $5.5k of revenue *and the rival gained $5.5k*, because they sold into the book I left empty. Most "sell less, sell better" ideas lose for this reason.

**5. Check which engine your notebook runs.** Kaggle's notebook image still ships `kaggle-environments` **1.29.3**, and its Kaggriculture engine is older than the current rules. On it, a mirror match of the #1 public agent ends with **$2 per farm**. On 1.32.7 the same agent banks about $100k. If your notebook plays its test games with Internet off, check the version it prints. Section 2 installs 1.32.7 with `pip install --no-deps` before it plays.

## 9 · Submit

The cell below packs the verified `main.py` into `submission.tar.gz` (deterministic: fixed timestamps, one member) and checks the archive round-trips byte-exactly. After *Save & Run All* the version has two output files: `submission.tar.gz` and `main.py`. Either one is a valid submission, and **Submit** on the notebook page sends it to the ladder. A new submission starts around 600 and needs a day or so of games to climb.

[code cell 30: 15 lines]
```
import gzip
source = Path("main.py").read_bytes()
assert hashlib.sha256(source).hexdigest() == EXPECTED_SHA256
buffer = io.BytesIO()
with tarfile.open(fileobj=buffer, mode="w", format=tarfile.GNU_FORMAT) as tar:
    info = tarfile.TarInfo("main.py")
    info.size, info.mtime, info.mode = len(source), 0, 0o644
    tar.addfile(info, io.BytesIO(source))
Path("submission.tar.gz").write_bytes(gzip.compress(buffer.getvalue(), mtime=0))
with tarfile.open("submission.tar.gz") as tar:
    assert tar.getnames() == ["main.py"]
    assert tar.extractfile("main.py").read() == source
print("submission.tar.gz", f"{Path('submission.tar.gz').stat().st_size:,} bytes",
      "sha256", hashlib.sha256(Path("submission.tar.gz").read_bytes()).hexdigest()[:12] + "…")
print("outputs:", sorted(p.name for p in Path(".").iterdir() if p.is_file()))
```

## Credits and license

This agent is built on the public Code tab. Thank you to:

* **Ahmed Berat Özer**: the V25–V48 series. This agent's chassis is V39/V40, plus his V43 overflow sale.
* **Yusuke Hayashi (yhay81)**: Shop Router 0908 / 0909 / 0913, the action schedules and shop-pair routing.
* **prvsiyan**: the Frontier notebooks. The finite tomato investment (V221B, adapted by Ahmed as V219), the cattle transfer (V231) and the six-sheep expansion (V233).
* **Dmitrii Gluzdov**: *Two Coins, One Sheep* stock reservations and the seven-turn terminal rescue.
* **aurax7**: Reactive Router sale timing and shed projection.
* **tetsutani**: market, room and repair mechanisms, and the opponent in section 2.
* **lucifer19** (Harvest Nocturne), **leoprovorov** (Mirror Counter), **destbreso** (X-ray Your Agent), **Steven Lee Hans** (Lord Momo feed-versus-value idea).
* The public **V100.24** release: CARROT2, ORDERPRI2, CAPHARV, SHEDROOM, HERD2 and COWSWAP. Its layers are labelled "Claude … layer" in the source.
* **Kaggle** for `kaggle-environments` (Apache-2.0).

Released under **Apache-2.0**, like everything it is built on. Every upstream notice is kept verbatim at the top of `main.py`.

---

If this saved you time, an upvote helps others find it. I read and answer every comment, and I especially want to hear about **section 6**. Good luck on the ladder! 🌾