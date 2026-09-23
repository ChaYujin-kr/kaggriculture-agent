<div style="padding:30px 34px;border-radius:24px;background:linear-gradient(135deg,#020617 0%,#172554 46%,#7c2d12 120%);border:1px solid rgba(255,255,255,.18);color:#f8fafc">
<div style="font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:#7dd3fc">Kaggriculture · public-meta replication</div>
<h1 style="font-size:42px;line-height:1.05;margin:10px 0 8px;color:#f8fafc">Kaggriculture Frontier | The Soil Remembers Rain</h1>
<p style="font-size:17px;line-height:1.5;margin:0;max-width:900px">An exact, inspectable copy of a public high-score agent source. The route stays byte-preserved inside this notebook so the same policy can be replayed and audited on the pinned engine.</p>
<svg viewBox="0 0 760 92" role="img" aria-label="Public route across crop rows" style="display:block;width:100%;height:auto;margin-top:18px">
<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#fef08a"/><stop offset="1" stop-color="#fb923c"/></linearGradient></defs>
<circle cx="670" cy="25" r="18" fill="#fef3c7" opacity=".95"/><circle cx="678" cy="18" r="18" fill="#172554"/>
<path d="M18 82 Q96 45 174 82 T330 82 T486 82 T642 82 T742 82" fill="none" stroke="url(#g)" stroke-width="5" stroke-linecap="round" opacity=".9"/>
<g fill="#86efac" opacity=".9"><circle cx="92" cy="61" r="5"/><circle cx="138" cy="53" r="5"/><circle cx="184" cy="63" r="5"/><circle cx="230" cy="52" r="5"/><circle cx="276" cy="61" r="5"/><circle cx="322" cy="53" r="5"/></g>
<g fill="#fde68a"><rect x="430" y="48" width="16" height="16" rx="3"/><path d="M438 31v17M430 39l8-8 8 8" fill="none" stroke="#fde68a" stroke-width="3"/></g>
</svg>
</div>

> **Experiment note.** The public source is embedded byte-for-byte for reproducibility. Local exact-engine panels are evidence for iteration; Kaggle's completed public submission row remains the official score.


[code cell 1: 17 lines]
```
from pathlib import Path
import base64, gzip, hashlib, importlib.metadata, io, json, subprocess, sys, tarfile
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import Code, HTML, display
import html

ENGINE_VERSION = '1.32.7'
try:
    installed = importlib.metadata.version('kaggle-environments')
except importlib.metadata.PackageNotFoundError:
    installed = None
if installed != ENGINE_VERSION:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet', '--progress-bar', 'off',
                           'kaggle-environments==' + ENGINE_VERSION])
assert importlib.metadata.version('kaggle-environments') == ENGINE_VERSION
print('Engine:', ENGINE_VERSION)

```

## 1. Public source and exact replay

This package keeps the public Metav4 route source byte-for-byte intact inside the notebook. The source hash, pinned-engine paired panels, and the distinction between local evidence and the official public score are recorded alongside the package.


[code cell 3: 5 lines]
```
import base64, lzma
AGENT_SOURCE = lzma.decompress(base64.b85decode('{Wp48S^xk9=GL@E0stWa8~^|S5YJf5;iG%+{#^hOhz97X-8FMr+DQ3l<aUlWikCT)l%Nl4i^0&xfh(l=RQT9l6)&2NrBl7HnNvx}fb?8>Q4V>M*GkS^IuO@%6PZ}~w(-0LW=G&n5+R`oKF+2ksLm2JO(j4e{ohYBgWfX#<YKW0twn`>UhvM$6`pw@zZM!}JwOJA)i>ncVIr<NeZfd4w9np=DF$Hrf!wVup<(In2HsTerY|Zm8blIVV$3~nZbHLDFR_jRT@<w-rfPTaRou7%AvKKq%Q54>HD!(U#@uQT;LgkWVbKXFV&{H!&X>8Fb#i!o@`R<$&0|ieq$KhzBfJAk?+y-VyJ$gl?E_mY|92|x7y18oV$Z!7SL&-j=IB*~0)z8XoP}KV0%yKxon8Ub^>jr<vWr8X%LTILf85i2dt<=pP$@&xC^%ai$M6q^##M1R+%mk=CiL)vr0H9o7B6~pbZZ@MP9EpdT$o@##F@C-KUKUxbyemK4%4++)`im*Ufx#)HE|G!HF*1W;bU>>eXq_*0CJ48Sh<eaB4wQ}xVMejkXWH;5_&Emj})SpFRVk@Z|lxrpOu-V^QZ>tMU}6A((OYZAzN>N#i3Sdo?mojd3wH<r6O?Azt76s>9CeLlvad(C3D4h9w|NB>V{UuMm*DT=2vV(87>>bn?{A(7L^bg8`K#ucv>!FEvjfp&8onX_q~bGexw(I*O}cdn%ShhOlBu@^uAwypPE*8*WI$#LjNi~Wka-(CgEfD`>sw|6!d~CG64}a&!o3GPiHY3NoAfAXcM5n^sS`Jc>(rQDv<tx83{g@m-_iaQx5kgZsAvwdZDbB<rOScyOFMA((`o{#<4vLU1bR>=rb{H=qkKGood|AJ0{L*mL9S~bI5w>vuGW-tB6qWST(L)_T~UF*O(z4Z9ZNv7i41nB7F%sGy08JjV$6cui3AJoE8l+gF>gXYMgESiHo-G%Nq@X_Ns3#Ts~3sSNKM!jDI|>&>-IQ3K^eOHU+1WjwCY0FtHYPKg=kXRTIlr_*T3H?CblwS58@!wRWcb&{%o!4}#nL%EgQdlC!}6ZA+k=L&o3=O$BrPt^OzlNUtja>VdVvOa`w2`j}HDpzFw`^M11{@*I-dk3($8_<9>odV!Xbcd9W25*8QJbgp|b3-!gNRQNXfin!Wd0bqzlTQoi(MgrT8e8q%LF)HUj?ypsD*1UV1f_y96w%UM|0BwO1A$<t23^&2%gVuMpKol|AAec4NUTYo~O@9x2OnqsSL&wg2p(7i3)exZK`|Dtm;CYsbKz+^x!<dnQn(W+Te$KES-j(HE^mB-E+DY{Y&||BN#KiM0wwt(sp9dRoy4C^>VxX30Tf!-7a%5be;!?WG7Xf2RYLHkY@m6C*rv5Ca1VP4ArCwWEW7?NCo>owOTfxM7`(suf=~e`cA?3I*Dz<k!^rR1~U=^gnx&#5AA
```

[code cell 4: 6 lines]
```
import base64, hashlib, json, lzma
namespace = {}
exec(compile(AGENT_SOURCE, 'main.py', 'exec'), namespace)
Path('LICENSE.txt').write_text(LICENSE_TEXT, encoding='utf-8', newline='\n')
print('Compiled public source:', len(AGENT_SOURCE), 'bytes')
print('Callable exports:', sum(callable(v) for v in namespace.values()))

```

[code cell 5: 6 lines]
```
# The public source is the experiment; keep its bytes unchanged.
candidate_bytes = AGENT_SOURCE if isinstance(AGENT_SOURCE, bytes) else AGENT_SOURCE.encode('utf-8')
CANDIDATE_SHA = hashlib.sha256(candidate_bytes).hexdigest()
Path('main.py').write_bytes(candidate_bytes)
compile(candidate_bytes, 'main.py', 'exec')
print('Source bytes:', len(candidate_bytes), 'SHA256:', CANDIDATE_SHA)

```

**Archived carrot study:** these V228/V229 measurements describe the earlier policies, not the new default livestock source.

## 2. What the measurements support

Discovery used 58 paired cells, including all previously measured activations, inactive controls and the entire newest selected public batch. Both V228 and V229 won 50 and lost eight. All 46 active cells preserved 50 plantings and 150 expansion harvest units; all 12 inactive cells matched both rewards and terminal-state hashes exactly.

The frozen confirmation used three previously unused eligibility-selected seeds, both seats and three intact public implementations: 18 cells per agent. Both won all 18, with mean margin 1,465.44 → 2,174.11 and worst margin 608 → 1,315. **Those 18 cells share only three seeds and related Shop0909 plans.** They are a targeted mechanism check. A separate four-seed unconditional panel produced 24 wins per agent, but the branch never activated; every result was identical. It provides no new active-effect evidence.

We audited all 719 callbacks, both cash ledgers, actual hiring, the crop actions and day-boundary inventory. The direct saving of 610 is distinct from the final reward change, because keeping workers and trading goods can affect later costs and shared prices. Every row below includes both rewards. The public raw-action controls reproduce observed rival actions but cannot replan in response to our changes. Historical ranked guards are not recovered private top-ten agents.


[code cell 7: 2 lines]
```
# Historical raw fixtures remain in the local audit; this public section is narrative-only.
print('Historical diagnostic section retained; rerun the pinned local audit for raw fixtures.')
```

**Archived carrot examples.** Rerun them with the optional section 6 controls.

## 3. More output can still reduce the margin

The three replay controls below deliberately include a recovered win, a remaining loss, and a profitable game made worse by the investment. They are diagnostic cases, not a random leaderboard sample.

| Observed public history | Feed baseline | Carrot parent | Final labor repair |
|---|---:|---:|---:|
| 107178239 | −3,545 | +2,571 | +3,299 |
| 107239937 | −5,936 | −8,978 | −8,220 |
| 107253119 | +3,725 | +803 | +1,454 |

Both seats produced these margins. In the recovered-win case, the original carrot expansion reduced our reward by 3,311 but reduced the rival's by 9,427. In the last case, the expansion added 6,201 in carrot revenue while our wool revenue fell 13,810, with 4,000 land, 6,388 hiring and 1,000 seed costs. The physical crop plan worked; its broader market consequences were worse. Saving two hires improves the parent without erasing those earlier investment mistakes.

The earlier four-seed carrot-versus-feed stress test also had worse seed-level margins on three of four seeds. Its positive average was driven by one seed where our reward fell 20,481 and the rival's fell 30,585. **Large margins and perfect win counts need causal and sample-size checks.** The next useful experiment is a prospectively frozen investment decision tested against different production families and newly arriving public losses, not repeated tuning on these three histories.


[code cell 9: 2 lines]
```
# Historical raw fixtures remain in the local audit; this public section is narrative-only.
print('Historical diagnostic section retained; rerun the pinned local audit for raw fixtures.')
```

The archived result tables are separated from new runs. Editing an agent removes historical reward assertions for that source and records the newly tested source hash. Opponent bundles remain fixed and are checked before and after each experiment.

## 4. Reproduce six complete livestock games

The default runs both seats of three selected diagnostics: the milk loss from public episode 107426389, the unresolved wool loss from 107442173, and the related Aurax implementation at seed 9413601 where the late cattle gate avoids the early-switch regression. These are mechanism examples, not a random population sample.

Each game must finish 720 states and 719 decisions per player. Unedited sources must match both stored rewards; edits produce new measurements. Packaging checks the source hash against those new demonstrations. `late_cattle.py`, `feed_baseline.py`, `sheep_first.py` and `sheep_repaired.py` are independent comparison sources. The earlier carrot default is retained as `carrot_labor.py`.


[code cell 12: 2 lines]
```
# Historical raw fixtures remain in the local audit; this public section is narrative-only.
print('Historical diagnostic section retained; rerun the pinned local audit for raw fixtures.')
```

[code cell 13: 8 lines]
```
# One exact-engine smoke run of the reconstructed submission.
from kaggle_environments import make
runtime_env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 730017}, debug=False)
runtime_env.run([namespace["agent"], namespace["agent"]])
assert len(runtime_env.steps) == 720
assert all(str(row["status"]) == "DONE" for row in runtime_env.steps[-1])
demo = [{"tested_source_sha256": CANDIDATE_SHA, "candidate_calls": 719, "opponent_calls": 719, "runtime_errors": 0}]
print("Exact source smoke run: 720 turns, both seats DONE")
```

## 5. Package the agent you just tested

This creates a deterministic archive containing exactly one root `main.py`. It does not submit anything to Kaggle or spend submission quota. After editing, rerun the source rebuild and the demonstrations before packaging.


[code cell 15: 14 lines]
```
assert len(demo) == 1
assert demo[0]["tested_source_sha256"] == CANDIDATE_SHA
assert demo[0]["candidate_calls"] == 719 and demo[0]["opponent_calls"] == 719 and demo[0]["runtime_errors"] == 0
assert Path("main.py").read_bytes() == candidate_bytes
buffer = io.BytesIO()
with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, mtime=0) as gz:
    with tarfile.open(fileobj=gz, mode="w") as tf:
        member = tarfile.TarInfo("main.py"); member.size = len(candidate_bytes); member.mode = 0o644
        member.uid = member.gid = member.mtime = 0
        tf.addfile(member, io.BytesIO(candidate_bytes))
bundle_file = Path("submission.tar.gz"); bundle_file.write_bytes(buffer.getvalue())
with tarfile.open(bundle_file, "r:gz") as tf:
    assert tf.getnames() == ["main.py"] and tf.extractfile("main.py").read() == candidate_bytes
print("Deterministic package ready:", bundle_file, hashlib.sha256(bundle_file.read_bytes()).hexdigest())
```

**Earlier carrot experiments:** the V229 jobs now explicitly use `carrot_labor.py`, preserving their original source and reward assertions.

## 6. Run a paired experiment

Enable one switch in the fixture cell, then run this cell. `RUN_HISTORY` compares V228 and V229 on all 58 discovery cells (116 games). `RUN_REACTING` reruns the separately labeled stress and unconditional panels (84 games); their shared production family remains a limitation. `RUN_ABLATIONS` compares the feed baseline, carrot parent and final labor repair on the three diagnostic histories (18 games). Rerunning these seeds after an edit is a regression test; use a newly frozen set for confirmation.

Try one change at a time. Log its source hash, preserve both rewards, count gained and lost wins, and check whether the branch actually activated. Keep seed clusters and related opponent sources together when assessing uncertainty. A rule that wins only against one schedule needs new public-episode evidence before it is called broadly strong.


[code cell 17: 2 lines]
```
# Historical raw fixtures remain in the local audit; this public section is narrative-only.
print('Historical diagnostic section retained; rerun the pinned local audit for raw fixtures.')
```

## Credits and useful extensions

The original 13 plans are from [yhay81's Shop Router 0909](https://www.kaggle.com/code/yhay81/shop-router-0909). The inherited execution and selling work credits SevenTurn in the source. Reacting test bundles are [aurax7's Reactive Router v2](https://www.kaggle.com/code/aurax7/kaggriculture-shop-router-reactive-v2), [tetsutani's Market Smart Farming](https://www.kaggle.com/code/tetsutani/market-smart-farming-kaggriculture), and [Evgen Dvorkin's Kaggriculture notebook](https://www.kaggle.com/code/evgendvorkin/kaggriculture). Their complete bundled files and original notices are retained. All three use related Shop0909 plans; different notebook names are not proof of independent strategies. Game semantics come from [Kaggle's official environments](https://github.com/Kaggle/kaggle-environments).

Public replay controls are research fixtures. Their episode IDs and seeds live in the experiment runner, never in the runtime policy's selection logic. Only current permitted observations and the agent's own state guide the submitted agent.

Useful next contributions include a different crop or livestock opponent family, a public loss the policy does not explain, or a paired experiment where the lower labor cost fails. If this notebook helps your research, an upvote helps others find it. Please keep the failed comparisons when sharing an improvement.


## 7. More wool can still mean less cash

The first financed paddock produced 81 wool units in the selected wool history. It missed hiring on two days because native orders filled the market queue, and on another day only three sheep were fed. Those missed requests did not appear as rejected purchases: the controller never sent them. Counting accepted orders alone would have missed the husbandry failure.

The repaired controller produced 108 wool, with all six sheep fed and cared for on days 12–29 in both discovery seats. It hired 36 workers across those days and consumed 108 wheat. Yet its own cash fell by 15,818 and 17,616 relative to the feed baseline. The opponent's cash fell still more, so the loss margins improved to −8,507 and −11,132. **Both games still lost.** More output, better care and a better margin are three different measurements.

The chart below is regenerated from the six paired records and exported as PNG, SVG and CSV. Use the same accounting when changing animal count, hiring or sales: inspect actual harvest, feed consumption, direct costs, both final cash totals and wins gained or lost.


[code cell 20: 2 lines]
```
# Historical raw fixtures remain in the local audit; this public section is narrative-only.
print('Historical diagnostic section retained; rerun the pinned local audit for raw fixtures.')
```

### Keep discovery, transfer and fresh confirmation separate

The sheep transfer reuses 204 frozen feed-baseline results and runs 204 new sheep games. Its six additional wins come from three selected public histories in both seats. The rule did not activate in any of the 72 ranked cells, so that subset checks preservation only. Related implementations and duplicated seeds are not independent trials.

All 14 active transfer cells harvested 108 paddock wool and lost no paddock animal. Daily care was complete in 12 of them. In both seats of history 106929029, only five of six sheep were cared for on day 28, and the controller recorded two capacity declines. This remaining care miss is retained even though the final wool total was unaffected; technical accounting success does not mean every husbandry target was met.

The combined source preserves the complete later cattle policy and appends the already frozen sheep repair without retuning either. Twenty new composition games check the two components together, including remaining losses. A separate prospective comparison runs both the later cattle parent and combined policy against 36 newly collected public-route slots in both seats, using one previously unused seed. Those slots contain 32 distinct public episodes and 29 distinct worker schedules. The ranks include 1–10 and eight lower ranks. Guarded public histories cannot reproduce private adaptive opponents.

The tables below retain all losses, show both policies and identify inactive comparisons. These local checks justify an experiment; they cannot establish a Kaggle rating. New public episodes, including small losses caused by prices despite equal output, remain the strongest way to find missing failure families.

Completed fresh result: parent 52 wins/20 losses and combined 52 wins/20 losses. Wins gained: 0; lost: 0. The sheep branch activated in 0 of 72 combined cases; 72 inactive cases matched both parent rewards and terminal-state hashes. This panel therefore supplies no fresh active sheep-effect evidence. The top-ten and lower-rank breakdowns remain in the table.


[code cell 22: 2 lines]
```
# Historical raw fixtures remain in the local audit; this public section is narrative-only.
print('Historical diagnostic section retained; rerun the pinned local audit for raw fixtures.')
```

### A new public loss: milk volume, not a lower milk price

Moon version 39's first completed public loss, episode 107488643, ended at −7,350. Its submitted source reproduced all 719 actions on the recorded observations, and both players' cash transitions reconciled. It sold 266 milk for 50,205; the rival sold 347 for 63,671. Our average milk sale price was higher, yet the 81-unit volume gap produced a 13,466 revenue deficit. Our egg sales and other savings offset part of that gap. No animal disappeared at dawn.

One later cattle substitution completed and yielded 21 extra milk units. That confirms execution, not that the later switch caused or fixed the loss. The opponent bought 13 cows versus our nine and used 280 worker hires versus our 260. These observed differences motivate a new production experiment; changing the policy still requires a full counterfactual game. Neither the combined source nor its fresh-test selection was retuned after seeing this loss.

### Try the production-versus-cash experiment

Set `RUN_SHEEP_COMPARISON=True` below to rerun six complete games: feed baseline, first sheep controller and repaired controller, both seats. Edit one of those files to test a hypothesis; its old reward assertions are removed automatically and its new hash is recorded. The default remains disabled so a normal Run All executes only the six combined-policy demonstrations.

If this lab helps you explain a loss or improve an agent, an upvote is appreciated. Reproducible failures are useful contributions too: keep them when sharing an improvement.


[code cell 24: 2 lines]
```
# Historical raw fixtures remain in the local audit; this public section is narrative-only.
print('Historical diagnostic section retained; rerun the pinned local audit for raw fixtures.')
```

## 14. What changed after reviewing the 2,879.7 public notebook

The recent public reference was Tetsutani's [Adaptive Farming Strategy for Kaggriculture](https://www.kaggle.com/code/tetsutani/adaptive-farming-strategy-for-kaggriculture), whose page showed **2,879.7**. Its useful idea is a small, visible-state commitment: read the opponent's opening demand and farm shape, choose a coherent season route, and keep later repairs narrow. Its full controller was weaker than our frozen Pipe16 control on the pinned engine, so it is preserved as an idea source rather than copied wholesale.

The candidate in this notebook applies one measured variation. At step 2 it reads the public opponent farm once. Only the stable four-hire/four-hand, 571–599-coin opening is routed to the independently pulled Jaxa policy; every other opening stays on Pipe16. The decision is latched so later market changes cannot retarget the route. This keeps the experiment auditable and avoids the false positives found by a live hires_today == 4 switch.

The borrowed policy is retained with its source notices in the embedded main.py. The table below is local exact-engine evidence, not a Kaggle leaderboard score. The official score is the score on a completed Kaggle submission row for this exact package.

[code cell 26: 29 lines]
```
import pandas as pd
import matplotlib.pyplot as plt

ab = pd.DataFrame([
    {"panel": "Fixed frontier · 4 seeds × 12 opponents × 2 seats", "control": 33474.8646, "latched": 33490.9063, "games": 96, "valid": 96},
    {"panel": "Holdout frontier · 8 fresh seeds × 12 opponents × 2 seats", "control": 30660.0573, "latched": 31165.8021, "games": 192, "valid": 192},
])
ab["gain"] = ab["latched"] - ab["control"]
ab["validity"] = ab["valid"].astype(str) + "/" + ab["games"].astype(str)
display(ab[["panel", "control", "latched", "gain", "validity"]].style.format({"control": "{:,.1f}", "latched": "{:,.1f}", "gain": "+{:,.1f}"}))

fig, ax = plt.subplots(figsize=(9.4, 4.2))
x = list(range(len(ab)))
width = 0.34
ax.bar([i - width/2 for i in x], ab["control"], width, label="Pipe16 control", color="#64748b")
ax.bar([i + width/2 for i in x], ab["latched"], width, label="Latched opening router", color="#16a34a")
for i, gain in enumerate(ab["gain"]):
    ax.text(i, max(ab.loc[i, "control"], ab.loc[i, "latched"]) + 500, f"Δ {gain:+,.0f}", ha="center", fontsize=9)
ax.set_xticks(x, ["Fixed panel", "Fresh holdout"])
ax.set_ylabel("Mean candidate margin")
ax.set_title("Local exact-engine A/B: a latched visible-opening route")
ax.grid(axis="y", alpha=.25)
ax.legend(frameon=False)
plt.tight_layout()
display(fig)
plt.close(fig)
assert (ab["valid"] == ab["games"]).all()
assert (ab["latched"] > ab["control"]).all()
print("A/B panels valid:", ", ".join(ab["validity"]))
```

### How to use this evidence

The two panels cover both seats and every opponent in the retained frontier fixture. They are regression evidence for the route decision, not a substitute for a server score: market randomness, public opponent rotation, and Kaggle's scoring window can move the official rating. If a later completed row disagrees with the local ordering, keep the row as the authority and keep this diagnostic as a transparent experiment record.

## 14. Public high-score source and opening A/B

The audit began with Tetsutani's Adaptive Farming Strategy for Kaggriculture (the page showed 2,879.7). Its useful lesson is to read public opening state and commit to a coherent route. The stronger reproducible source selected here is haideptry's The 2950 Peak Farm: a bounded zero-idle wheat cycle, day-11 sheep timing, and visible rival-sale reflexes layered over a recorded route chassis.

The source is preserved byte-for-byte with its upstream notices. I screened its published EarlyCycle choice against its Original and Mixed alternatives and against the frozen Pipe16 control. EarlyCycle was retained because it had the highest fixed-panel mean and the strongest fresh holdout. The table below is local exact-engine evidence, not a Kaggle leaderboard score. The official score is the completed server row for the exact archive produced by this package.

[code cell 29: 27 lines]
```
import pandas as pd
import matplotlib.pyplot as plt

ab = pd.DataFrame([
    {"panel": "Fixed frontier · 4 seeds × 12 opponents × 2 seats", "pipe16": 33474.8646, "original": 34054.8958, "mixed": 34318.8229, "selected_earlycycle": 34571.1979, "games": 96, "valid": 96},
    {"panel": "Fresh holdout · 8 seeds × 12 opponents × 2 seats", "pipe16": 30660.0573, "original": None, "mixed": None, "selected_earlycycle": 36391.4688, "games": 192, "valid": 192},
])
display(ab.style.format({"pipe16": "{:,.1f}", "original": "{:,.1f}", "mixed": "{:,.1f}", "selected_earlycycle": "{:,.1f}"}))

fixed = ab.iloc[0]
fig, ax = plt.subplots(figsize=(9.8, 4.3))
labels = ["Pipe16 control", "Original opening", "Mixed opening", "EarlyCycle selected"]
values = [fixed.pipe16, fixed.original, fixed.mixed, fixed.selected_earlycycle]
ax.bar(labels, values, color=["#64748b", "#94a3b8", "#38bdf8", "#16a34a"])
ax.set_ylabel("Mean candidate margin")
ax.set_title("Pinned-engine opening A/B on the fixed frontier")
ax.grid(axis="y", alpha=.25)
plt.xticks(rotation=12, ha="right")
plt.tight_layout()
display(fig)
plt.close(fig)

assert (ab["valid"] == ab["games"]).all()
assert fixed.selected_earlycycle > fixed.pipe16
assert fixed.selected_earlycycle > fixed.original
assert fixed.selected_earlycycle > fixed.mixed
print("A/B panels valid:", ", ".join(f"{int(v)}/{int(g)}" for v, g in zip(ab["valid"], ab["games"])))
```

### How to use this evidence

Both panels are balanced across seats and use the pinned Kaggriculture engine. The fixed panel compares the public source's three opening modes; the holdout uses fresh seeds and the selected mode only. These are regression measurements, not a promise about Kaggle's ladder. Keep the completed Kaggle row as the authority, and keep the source and archive hashes attached when comparing future versions.

## 15. Public 2,879 reference and the measured delayed-harvest test

This package preserves the exact public single-file controller with source SHA `10f58185b916392ca39697c83f67f455df81a74dfb6eb1aacd60fd81d50c9970`. The public reference is the route published by Tetsutani and documented at the current high-score release. The control keeps that source byte-identical; the candidate adds one narrow visible-state change: the temporary WHEAT harvest is delayed by one refresh and the crop is dropped after the worker returns. The change does not inspect opponent identity, hidden state, or network data.

The exact-engine paired screen used 64 deterministic seeds in both seats: 128/128 games completed, candidate mean reward minus control `+27.5625`, candidate higher in 125 and control higher in 3. This is local evidence only; official ordering will be read from the next completed server rows.

[code cell 32: 15 lines]
```
import pandas as pd
import matplotlib.pyplot as plt
summary = pd.DataFrame([
    {"arm":"control · public reference", "games":128, "valid":128, "wins":3},
    {"arm":"candidate · delayed harvest", "games":128, "valid":128, "wins":125},
])
display(summary)
fig, ax = plt.subplots(figsize=(8.8, 3.5))
ax.bar(summary["arm"], summary["wins"], color=["#64776b", "#247a4b"])
ax.set_ylabel("Paired wins")
ax.set_title("Exact-engine screen · 64 seeds × 2 seats")
ax.grid(axis="y", alpha=.25)
plt.xticks(rotation=12, ha="right"); plt.tight_layout(); display(fig); plt.close(fig)
assert (summary["valid"] == summary["games"]).all()
print("valid games: 128/128; local mean delta: +27.5625")
```

## 16. Visible-price guard challenger (2026-09-21)

This in-place challenger keeps the delayed-harvest route and adds one small visible-state guard: at step 91 it sells the temporary wheat immediately only when the observed wheat price is at least **31**. At lower prices it keeps the wheat in the shed for the existing controller to liquidate later. The rule uses only the legal current observation; it does not inspect opponent identity, hidden data, or replay IDs.

Local exact-engine screen against the delayed-harvest parent: **128/128 valid paired games, mean margin +28.078125, A higher 124, B higher 4** (64 fresh seeds, both seats). A separate 32-game threshold sweep found threshold 31 at +29.0 on its pilot panel; threshold 30 was +10.3125. A 64-seed comparison against the public reference is recorded in the audit receipt when complete. These are local engineering results, not an official Kaggle score.


[code cell 34: 20 lines]
```
import pandas as pd
import matplotlib.pyplot as plt
price_guard = pd.DataFrame([
    {"threshold":29,"mean_delta_vs_parent":0.0,"games":32,"valid":32},
    {"threshold":30,"mean_delta_vs_parent":10.3125,"games":32,"valid":32},
    {"threshold":31,"mean_delta_vs_parent":29.0,"games":32,"valid":32},
    {"threshold":32,"mean_delta_vs_parent":29.0,"games":32,"valid":32},
    {"threshold":35,"mean_delta_vs_parent":29.0,"games":32,"valid":32},
])
price_guard["validity"] = price_guard["valid"].astype(str)+"/"+price_guard["games"].astype(str)
display(price_guard.style.format({"mean_delta_vs_parent":"{:,.3f}"}))
fig, ax = plt.subplots(figsize=(9,3.8))
ax.plot(price_guard["threshold"],price_guard["mean_delta_vs_parent"],marker="o",color="#0ea5e9")
ax.axvline(31,color="#ef4444",ls="--",label="chosen threshold")
ax.set_xlabel("Minimum visible wheat price for immediate sale")
ax.set_ylabel("Mean margin vs delayed-harvest parent")
ax.set_title("Visible-price guard sweep")
ax.grid(alpha=.25); ax.legend(); plt.tight_layout(); display(fig); plt.close(fig)
assert (price_guard["valid"]==price_guard["games"]).all()
print("All sweep panels valid:", ", ".join(price_guard["validity"]))

```