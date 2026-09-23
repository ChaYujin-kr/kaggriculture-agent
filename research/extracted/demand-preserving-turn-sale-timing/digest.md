<style>
:root{
  --ink:#173322; --ink2:#2c4839; --muted:#64776b; --line:#d7e5dc;
  --green:#247a4b; --teal:#218b9b; --gold:#b47b18; --violet:#835ca4;
  --paper:#fcfefc; --paper2:#f2f8f4;
  --shadow:0 10px 28px rgba(20,60,38,.07);
}
.jp-RenderedHTMLCommon p,.jp-RenderedHTMLCommon li,.rendered_html p,.rendered_html li{line-height:1.7}
.jp-RenderedHTMLCommon h2,.rendered_html h2,h2{
  color:var(--ink)!important;background:linear-gradient(90deg,#fff,#f4faf6 58%,#eef7f3);
  border:1px solid #d2e2d8!important;border-left:6px solid var(--green)!important;border-radius:18px;
  padding:13px 18px 13px 22px!important;margin-top:1.85em!important;margin-bottom:.85em!important;
  letter-spacing:-.018em;box-shadow:0 8px 24px rgba(20,60,38,.05)
}
.jp-RenderedHTMLCommon h2::before,.rendered_html h2::before,h2::before{
  content:"Strategy note";display:inline-block;margin-right:11px;padding:4px 9px;font-size:10px;font-weight:800;
  letter-spacing:.14em;text-transform:uppercase;color:#fff;background:linear-gradient(135deg,var(--green),#35a664);
  border-radius:999px;vertical-align:middle
}
code{background:rgba(102,129,112,.12)!important;padding:.12em .34em;border-radius:6px}
pre,.jp-OutputArea-output pre,.output_subarea pre{border:1px solid var(--line);border-radius:15px;padding:14px;background:#fbfdfb!important}
blockquote{border-left:4px solid var(--gold)!important;padding:12px 16px!important;border-radius:0 12px 12px 0;background:#fffaf0}
.kg-hero{position:relative;box-sizing:border-box;margin:6px 0 24px;padding:31px;border-radius:30px;overflow:hidden;
 background:radial-gradient(circle at 84% 12%,rgba(118,255,182,.25),transparent 23%),radial-gradient(circle at 73% 88%,rgba(63,196,255,.15),transparent 28%),linear-gradient(135deg,#07271d 0%,#103b30 43%,#123b4a 100%);
 color:#f6fff9;border:1px solid rgba(255,255,255,.12);box-shadow:0 18px 42px rgba(6,31,20,.18)}
.kg-hero::before{content:"";position:absolute;inset:0;background:linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px);background-size:26px 26px;mask-image:linear-gradient(180deg,rgba(0,0,0,.7),transparent 92%);pointer-events:none}
.kg-hero-grid{position:relative;z-index:1;display:grid;grid-template-columns:minmax(0,1.45fr) minmax(310px,.9fr);gap:24px;align-items:stretch}
.kg-kicker{font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:#a6ebc0;font-weight:800}
.kg-hero h1{font-size:46px;line-height:1.02;margin:10px 0 12px;color:#fff!important;letter-spacing:-.045em}
.kg-hero-copy{margin-top:10px;padding:14px 16px;border-radius:16px;background:rgba(2,18,12,.34);border:1px solid rgba(255,255,255,.12)}
.kg-hero-copy p{font-size:17px;line-height:1.62;margin:0;color:#f5fff8!important}
.kg-chip-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:18px}.kg-chip{border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.08);color:#effcf4;padding:7px 11px;border-radius:999px;font-size:12px;font-weight:700}
.kg-stat-row{display:grid;grid-template-columns:repeat(3,minmax(100px,1fr));gap:9px;margin-top:17px}.kg-stat{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);border-radius:17px;padding:11px 12px}.kg-stat .v{display:block;color:#fff;font-weight:900;font-size:23px}.kg-stat .k{display:block;color:#cde7d8;font-size:11.5px;line-height:1.3}
.kg-art{background:linear-gradient(180deg,rgba(4,20,14,.42),rgba(10,30,21,.56));border-radius:24px;padding:14px;border:1px solid rgba(255,255,255,.14)}
.kg-art .label{font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:#a8ecc2;font-weight:800;margin:2px 0 8px 4px}
.kg-prose{position:relative;background:linear-gradient(145deg,var(--paper),var(--paper2));color:var(--ink2);border:1px solid var(--line);border-radius:18px;padding:17px 18px;margin:12px 0 15px;box-shadow:var(--shadow)}
.kg-prose::before{content:"";position:absolute;left:0;top:0;bottom:0;width:5px;border-radius:18px 0 0 18px;background:linear-gradient(180deg,var(--green),#56b07a)}
.kg-prose .lead{font-size:15px;line-height:1.67}.kg-prose .micro{font-size:13px;color:var(--muted)}
.kg-roadmap{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:11px;margin:14px 0 8px}.kg-road{position:relative;border:1px solid var(--line);border-radius:20px;padding:17px 15px 15px;box-shadow:var(--shadow);overflow:hidden;background:linear-gradient(145deg,#fcfefc,#f3f8f5)}
.kg-road .n{display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:13px;background:linear-gradient(135deg,var(--green),#35a664);color:#fff;font-weight:900}.kg-road.teal .n{background:linear-gradient(135deg,var(--teal),#2aa8bd)}.kg-road.gold .n{background:linear-gradient(135deg,var(--gold),#dba128)}.kg-road.violet .n{background:linear-gradient(135deg,var(--violet),#a37bc4)}
.kg-road .t{display:block;margin-top:13px;font-weight:800;color:var(--ink);font-size:15px}.kg-road .d{display:block;margin-top:6px;color:#53695d;line-height:1.52;font-size:13.5px}
.kg-grid{display:grid;grid-template-columns:repeat(2,minmax(240px,1fr));gap:12px;margin:14px 0}.kg-card{border:1px solid var(--line);border-radius:19px;padding:17px;box-shadow:var(--shadow);background:#fff;color:var(--ink)}.kg-card b{display:block;margin:5px 0}.kg-card span{color:#53695d;font-size:13.5px;line-height:1.52}.kg-card .eyebrow{font-size:10px;letter-spacing:.13em;text-transform:uppercase;font-weight:800}.kg-card.green{border-top:5px solid var(--green)}.kg-card.teal{border-top:5px solid var(--teal)}.kg-card.gold{border-top:5px solid var(--gold)}.kg-card.violet{border-top:5px solid var(--violet)}
.kg-note{border:1px solid var(--line);border-left:5px solid var(--green);border-radius:16px;padding:15px 17px;margin:14px 0;box-shadow:var(--shadow);background:linear-gradient(135deg,#eef9f2,#fbfdfb);color:var(--ink)}.kg-note.gold{border-left-color:var(--gold);background:linear-gradient(135deg,#fff7e5,#fffdf8)}.kg-note.teal{border-left-color:var(--teal);background:linear-gradient(135deg,#ebf8fa,#fbfefe)}.kg-note .title{font-weight:800;margin-bottom:5px}.kg-note .body{color:#486052;line-height:1.62;font-size:14px}
.kg-flow{background:#fff;border:1px solid var(--line);border-radius:22px;padding:13px;margin:15px 0;box-shadow:var(--shadow);overflow-x:auto}
.kg-terminal{background:linear-gradient(135deg,#0d2a1e,#12362a);color:#eaf8ef;border:1px solid #326247;border-radius:18px;padding:17px 19px;margin:14px 0;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;line-height:1.8;box-shadow:0 10px 24px rgba(8,33,22,.16)}
.kg-terminal b{color:#9be5b7}.kg-terminal .dim{color:#a9c9b5}
.kg-caption{font-size:13px;color:#607468;margin-top:6px}
/* Force notebook tables into a light, high-contrast surface even when Kaggle/Jupyter uses dark mode. */
.jp-RenderedHTMLCommon table,.jp-OutputArea-output table,.output_html table,.rendered_html table,table.dataframe,.kgvt,.forest-table{background:#ffffff!important;color:#203a2c!important;border-color:#d6e3da!important;color-scheme:light!important}
.jp-RenderedHTMLCommon table thead,.jp-OutputArea-output table thead,.output_html table thead,.rendered_html table thead,table.dataframe thead,.kgvt thead,.forest-table thead{background:#edf5f0!important;color:#173322!important}
.jp-RenderedHTMLCommon table th,.jp-OutputArea-output table th,.output_html table th,.rendered_html table th,table.dataframe th,.kgvt th,.forest-table th{background:#edf5f0!important;color:#173322!important;border-color:#d6e3da!important}
.jp-RenderedHTMLCommon table tbody,.jp-RenderedHTMLCommon table tr,.jp-RenderedHTMLCommon table td,.jp-OutputArea-output table tbody,.jp-OutputArea-output table tr,.jp-OutputArea-output table td,.output_html table tbody,.output_html table tr,.output_html table td,.rendered_html table tbody,.rendered_html table tr,.rendered_html table td,table.dataframe tbody,table.dataframe tr,table.dataframe td,.kgvt tbody,.kgvt tr,.kgvt td,.forest-table tbody,.forest-table tr,.forest-table td{background:#ffffff!important;color:#203a2c!important;border-color:#e2ebe5!important}
.jp-RenderedHTMLCommon table tbody tr:nth-child(even) td,.jp-OutputArea-output table tbody tr:nth-child(even) td,.output_html table tbody tr:nth-child(even) td,.rendered_html table tbody tr:nth-child(even) td,table.dataframe tbody tr:nth-child(even) td,.kgvt tbody tr:nth-child(even) td,.forest-table tbody tr:nth-child(even) td{background:#f7faf8!important}
.jp-RenderedHTMLCommon table tbody tr:hover td,.jp-OutputArea-output table tbody tr:hover td,.output_html table tbody tr:hover td,.rendered_html table tbody tr:hover td,table.dataframe tbody tr:hover td,.kgvt tbody tr:hover td,.forest-table tbody tr:hover td{background:#edf7f1!important;color:#173322!important}
@media(max-width:920px){.kg-roadmap{grid-template-columns:repeat(2,minmax(0,1fr))}.kg-hero-grid{grid-template-columns:1fr}}
@media(max-width:700px){.kg-hero{padding:22px}.kg-hero h1{font-size:37px}.kg-roadmap,.kg-grid{grid-template-columns:1fr}.kg-stat-row{grid-template-columns:1fr 1fr 1fr}}
</style>

<div class="kg-hero"><div class="kg-hero-grid"><div>
<div class="kg-kicker">Kaggriculture · exact late-season candidate · production-loader checked</div>
<h1>🌿 Hybrid Productive Opening + Late-Season Seed Discipline</h1>
<div class="kg-hero-copy"><p><b>A deterministic public-state controller built on the strongest of the three attached results, with one measured late-season spending correction.</b> The inherited <code>HybridOpening</code>, demand-preserving market closure, storage/race/rescue stack, and endgame logic remain intact. The added guard stops <code>BUY_SEED</code> orders from day 27 hour 16 onward, preserving cash when the remaining season makes late replenishment unattractive.</p></div>
<div class="kg-chip-row"><span class="kg-chip">720 turns</span><span class="kg-chip">single main.py</span><span class="kg-chip">HybridOpening</span><span class="kg-chip">late seed guard</span><span class="kg-chip">loader verified</span></div>
</div></div></div>


## Read the notebook in four passes
<div class="kg-roadmap"><div class="kg-road"><span class="n">01</span><span class="t">Keep the strongest attached base</span><span class="d">The inherited route, storage, race, cleanup, transfer rescue, closeout, HybridOpening, and queue-completion layers remain intact.</span></div><div class="kg-road teal"><span class="n">02</span><span class="t">Preserve the productive opening</span><span class="d">The temporary WHEAT cycle still matures, restores the pasture, and returns to the established whole-season controller.</span></div><div class="kg-road gold"><span class="n">03</span><span class="t">Stop late seed replenishment</span><span class="d">From day 27 hour 16 onward, new seed purchases are suppressed while every non-seed market order keeps its original slot and order.</span></div><div class="kg-road violet"><span class="n">04</span><span class="t">Verify exact bytes</span><span class="d">The exact one-file archive reconstructed here is loader checked and run for a complete 720-turn season.</span></div></div>


## 1. Selected mechanism: a bounded late-season seed cutoff
<div class="kg-prose"><div class="lead">The selected change is deliberately narrow: after the inherited controller has decided the full action, <code>BUY_SEED</code> market slots are replaced with no-ops from day 27 hour 16 onward. The threshold was chosen inside one visible timing family; earlier cutoffs were rejected because they produced seed-level losses. All farming actions and all other market orders remain untouched.</div><div class="micro">This is a late-capital allocation wrapper around the inherited controller, not a replacement for its route or production policy.</div></div>


## 2. The inherited production stack remains intact
<div class="kg-prose"><div class="lead">The exact source retains the established route chassis, public race/reservation handling, storage-pressure logic, crop and livestock production, HybridOpening completion, demand-preserving market compaction, transfer rescues, terminal cleanup, tomato-work scheduling guard, delayed opening completion, and queue closure. The new layer changes only late <code>BUY_SEED</code> orders.</div><div class="micro">The archived <code>main.py</code> bytes below are the runtime source of truth.</div></div>


[code cell 5: 25 lines]
```
import pandas as pd

route_rules = pd.DataFrame([
    ("Production chassis", "inherited", "public observation + frozen route tables", "run the established farm, market, storage, race, rescue, and closeout stack"),
    ("Hybrid opening purchase", "step 0", "selected mode = HybridOpening", "append BUY_SEED WHEAT 1 without replacing inherited opening orders"),
    ("Temporary WHEAT route", "steps 2–6", "idle hand on the opening tape", "walk west, plant WHEAT, and water the temporary crop"),
    ("Pasture delay", "step 29 + step 52", "temporary crop still occupies the future pasture site", "keep the crop alive for the extra growth refresh"),
    ("Mature harvest + restore", "steps 84–91", "observed crop and worker position", "water, harvest, rebuild pasture, return, and DROP"),
    ("Mixed SELL accounting", "step ≥ 144", "earlier singleton compatible SELLs", "deduct already-scheduled inventory before compacting a later SELL run"),
    ("Queue closure", "same-turn market list", "projected shed + executable cash SELLs", "zero impossible sales and fill only existing holes with later executable sales"),
    ("Late seed discipline", "day 27, hour ≥ 16", "remaining season horizon", "suppress only BUY_SEED slots; preserve every other market order and slot"),
    ("Tomato crew guard", "days 19 / 21 / 23", "observed tomato water state", "skip selected redundant watering hires"),
], columns=["layer", "condition", "signal", "purpose"])

safety_rules = pd.DataFrame([
    ("Selected mode", "H
```

[code cell 6: 13 lines]
```
from IPython.display import HTML, display

def _kg_table(frame, title):
    html = frame.to_html(index=False, escape=True).replace('class="dataframe"','class="kgvt"')
    display(HTML(
        '<div style="background:#fff!important;border:1px solid #d5e3da;border-radius:17px;padding:14px 16px;overflow-x:auto;color:#173322!important;color-scheme:light">'
        f'<div style="font-size:11px;letter-spacing:.12em;text-transform:uppercase;font-weight:800;color:#176b42;margin-bottom:9px">{title}</div>'
        '<style>.kgvt{border-collapse:collapse;width:100%;font-size:12.8px;background:#fff!important;color:#203a2c!important}.kgvt thead,.kgvt th{background:#edf5f0!important;color:#173322!important}.kgvt th,.kgvt td{padding:9px 10px;border-bottom:1px solid #e2ebe5!important}.kgvt tbody,.kgvt tr,.kgvt td{background:#fff!important;color:#203a2c!important}.kgvt tbody tr:nth-child(even) td{background:#f7faf8!important}</style>'
        + html + '</div>'
    ))

_kg_table(route_rules, "Public routing and closure checkpoints")
_kg_table(safety_rules, "Bounded market and execution guards")
```

## 3. Four layers, one conservative composite
<div class="kg-grid"><div class="kg-card green"><div class="eyebrow">Production controller</div><b>The inherited farm and market stack remains the backbone.</b><span>Storage pressure, race handling, capital, repair, livestock, rescue, timing, and closeout continue unchanged underneath the wrappers.</span></div><div class="kg-card teal"><div class="eyebrow">Mature hybrid opening</div><b>Idle early labor still becomes a temporary WHEAT cycle that is allowed to finish.</b><span>The crop is watered through the extra refresh, harvested, the pasture is rebuilt, and delivery returns to the inherited flow.</span></div><div class="kg-card gold"><div class="eyebrow">Late seed discipline</div><b>Day-27 seed replenishment ends at hour 16.</b><span>The guard removes only BUY_SEED slots and leaves farming actions, sales, buys, and market order positions otherwise unchanged.</span></div><div class="kg-card violet"><div class="eyebrow">Exact artifact</div><b>The candidate archive is reconstructed and run as a file-path submission.</b><span>Production callable selection and a full 720-turn season are checked below.</span></div></div>


## 4. Freeze the exact single-file submission
<div class="kg-prose"><div class="lead">This notebook reconstructs the exact selected <code>submission.tar.gz</code>. The archive contains one runtime file at root: <code>main.py</code>. Embedded archive bytes, extracted source hash, production entrypoint, late-seed guard symbols, and executed season are checked below.</div></div>


[code cell 9: 23 lines]
```
import base64, hashlib, io, tarfile, py_compile
from pathlib import Path

VARIANT = "hybrid_opening_late_seed_hour16_strongest_attached"
EXPECTED_ARCHIVE_SHA256 = "59d8cb0e2c5d1387e0984c0fbf3ddf35b2c236300919742027fde80c8a9bb425"
EXPECTED_MAIN_SHA256 = "9c0a8921aa49fba080d53deee3c9fe8db7a8e2b02881e9adda4090af73e9c187"
EXPECTED_MEMBERS = ["main.py"]
ARCHIVE_B64 = """H4sIAAAAAAAC/+S9d1/qTLcwfP72UwRRDtVNLwIK0pXedb8bCCRAICSYhK5+9ndKKsXtdV/nPL+3eJcNYWbNmjVrVp/JgmS4u+Xuv/43/9zgL+j3o3/Bn+FfX8jjD/jUZ/LzkDfo/i/C/V//B/5WokQKYMj/+v/nn5lI8YslLzISTYxIjmIoUqLviQUprQSayO+GAkNVljTHcBNiSIo04SAWzJamXAtSmNMSIYIfWFriOYLh1jQn8cKOIEcjfsVJsMuY2d5dmYmGJACwk9090QIgpCkNWotLeiTRFFFllrTLEzwaa8RzksCzLC3cEXWaFEVmAoagWJrY8GBgQSSolQAbQmBjRhAl8EmgaYIidyIh8cSSJTnJSWzAuAIBJkZMSWFNg2Y8BzCgwZwFEuC6mdKkRIwEfumEoDhCAG14ASMJYXAAxSUpInJAMBTNMmsAEv6OOt8RVdCHBsBxn9WQZUZEiZbItZ9YCjy1GkkMoA/sLBNNP7nmlBEJ8F9SkgRmuIIUEeiVSDtRB0YSCRG05SZgSBm0yK+EEQ0eMyxLcDRNiQRECUIFhAArB0a7I9KMSA4Bufgl/E6yBM2tGQBoARbJRdGAzBT4RNBbQB/4M8sMEUFYnqQgXUUeTYcURlMIHGAo0uzYBVEHIoOm4LIW+RHouSRHc3IC+yx4ihkzI4SB6CS8bm/Q5Y64vO47oiIwoAlorcwTkkSgNVgv5GQiMKMViygtroYLBiw6aLSO/PLdK3Nv+yKENQlGnNIu753bSXC8xIxokRjSLL+xgRVbiQjvdYRgyR3gEwC6nkxlql1iAljBib4QVrxiCFFiLPALQE16SXgiXicx5QVmDx773cQvuGAAbcLjtTmJVKVVL2Tq4EOyXq800frkM/U0GIFcInpSYHZodPCF4MfgIyDbmGFpOMFMt+ryhHyAkjwLMAELgzld2Uj0+4rmRnhnMAKANdwRuym5C3t+iVN+6RJ4wBwCoKfH4xKZxRKsrY4StlMaogGDIW1b3xFlXsKklSCfkSuJh+wCFpHdwf5JbW3uAfLgR1ESwfpzc5p1ysg4wQ4QpSEgIA9YdCWQ2xDYObQkriSSY5wAylJYi8yOxByfBmMJDEPk2NWe4td3hIYyACQw
```

### Production loader boundary
<div class="kg-prose"><div class="lead">Load the reconstructed source exactly as a Kaggle submission and verify that the final callable is <code>agent</code>. The checks also confirm the inherited HybridOpening / demand-preserving closure symbols and the new day-27 hour-16 seed cutoff are present in the exact evaluated bytes.</div></div>


[code cell 11: 28 lines]
```
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import hashlib, sys, contextlib, io
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    from kaggle_environments.agent import get_last_callable
source_path = Path("main.py").resolve(); source = source_path.read_text(encoding="utf-8")
spec = spec_from_file_location("submission_agent", source_path); submission_agent = module_from_spec(spec); sys.modules[spec.name] = submission_agent
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()): spec.loader.exec_module(submission_agent)
assert callable(submission_agent.agent)
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()): production_entry = get_last_callable(source, path=str(source_path))
assert callable(production_entry) and production_entry.__name__ == "agent"
assert hashlib.sha256(source_path.read_bytes()).hexdigest() == EXPECTED_MAIN_SHA256
assert "_ALT_MODE = 'HybridOpening'" in source
assert "V13V_SKIP_DAYS = (19, 21, 23)" in source
assert "[['BUY_SEED','WHEAT',1]]" in source
assert "for step in range(53,58):" in source
assert "zip(range(84,92), commands)" in source
assert "def _e334_compact_mixed" in source
assert "_E335_ORIGINAL_COMPACT=_e334_compact_mixed" in source
assert "def _ow_guard_opening" in source
assert "def _ow_gate_delayed_cycle" in source
assert "def _ow_close_queue" in source
assert "def _es_cut_dead_
```

## 5. Watch one exact 720-turn production-path season
<div class="kg-prose"><div class="lead">Run the reconstructed submission through the file-path loader used by Kaggle Environments. The season must finish all 720 turns with both players <code>DONE</code> and contain real farming and market activity; an effectively all-PASS replay is a hard failure.</div></div>


[code cell 13: 169 lines]
```
from collections import Counter
from pathlib import Path
import contextlib, io, math, base64
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import HTML, Image, display

with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    from kaggle_environments import make

viz_env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 1144452272}, debug=False)
production_path = str(Path("main.py").resolve())
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    viz_env.run([production_path, production_path])
assert len(viz_env.steps) == 720
assert int(viz_env.steps[-1][0].observation.step) == 719
assert [str(s.status) for s in viz_env.steps[-1]] == ["DONE", "DONE"]

nonpass_unit_actions = 0
market_order_count = 0
for frame in viz_env.steps[1:]:
    for record in frame:
        action = record.get("action") if isinstance(record, dict) else getattr(record, "action", None)
        if not isinstance(action, dict):
            continue
        farmer = action.get("farmer", ["PASS"])
        if isinstance(farmer, list) and farmer and farmer[0] != "PASS":
            nonpass_unit_actions += 1
        for hand in action.get("hands", []) or []:
            if isinstance(hand, list) and hand and hand[0] != "PASS":
                nonpass_unit_actions += 1
        market_order_count += len(action.get("market", []) or [])

assert nonpass_unit_actions > 0, "produc
```

## 6. Evidence board — one executed season, four views
<div class="kg-prose"><div class="lead">A single self-play run is a behavior and packaging audit, not a strength estimate. These views confirm that the frozen composite executes the full season and expose workload, market movement, capacity, and action mix without changing the agent.</div></div>


[code cell 15: 10 lines]
```
daily_total=np.array(daily_farm_actions)+np.array(daily_market_orders)
fig,axes=plt.subplots(2,2,figsize=(10.8,7.6))
ax=axes[0,0]; ax.plot(days,daily_total,linewidth=2.4,marker="o",markersize=3,color=PALETTE[0]); ax.fill_between(days,daily_total,alpha=.08,color=PALETTE[0]); _forest_axes(ax,"1 · When activity peaked","Day","Observed actions"); ax.grid(axis="y",alpha=.20)
ax=axes[0,1]
for pdt in products: ax.plot(days,daily_prices[pdt],linewidth=1.8,label=pdt.title())
_forest_axes(ax,"2 · What shared prices did","Day","Market price"); ax.legend(frameon=False,ncol=2,fontsize=7.8); ax.grid(axis="y",alpha=.18)
ax=axes[1,0]; ax.plot(days,daily_hands,linewidth=2,label="Hands"); ax.plot(days,daily_plants,linewidth=2,label="Plants"); ax.plot(days,daily_pastures,linewidth=2,label="Pastures"); _forest_axes(ax,"3 · What the farm became","Day","Count"); ax.legend(frameon=False,ncol=3,fontsize=8); ax.grid(axis="y",alpha=.18)
ax=axes[1,1]; mf=pd.DataFrame(mix.items(),columns=["category","actions"]).sort_values("actions"); ax.barh(mf["category"],mf["actions"],color=PALETTE[1],alpha=.88); _forest_axes(ax,"4 · Where attention went","Actions",""); ax.grid(axis="x",alpha=.18); ax.grid(axis="y",alpha=0)
fig.suptitle("One executed season · workload, market, capacity, attention",fontsize=16,fontweight="bold",color=FOREST,y=.995); fig.tight_layout(rect=[0.02,0.01,.99,.96],h_pad=2.4,w_pad=1.8); _show_fig(fig)
peak_idx=int(np.argmax(daily_total)); _show_kpis([("Peak activity",f"Day {int(days[peak_idx]
```

## 7. Three trends expose the timing
<div class="kg-prose"><div class="lead">The overview compresses the season. These traces restore the day-by-day rhythm: farm workload versus market orders, visible shared prices, and the relationship between farm capacity and bank.</div></div>

[code cell 17: 3 lines]
```
fig,ax=plt.subplots(figsize=(10.6,4.4)); ax.plot(days,daily_farm_actions,linewidth=2.4,marker="o",markersize=3,label="Farm actions",color=PALETTE[0]); _forest_axes(ax,"Workload · when was the controller busiest?","Day","Farm actions"); ax.grid(axis="y",alpha=.2)
ax2=ax.twinx(); ax2.plot(days,daily_market_orders,linewidth=2,marker="s",markersize=2.8,label="Market orders",color=PALETTE[1]); ax2.set_ylabel("Market orders",color=MUTED,fontsize=9); ax2.tick_params(colors=MUTED,labelsize=8); ax2.spines["top"].set_visible(False); ax2.spines["right"].set_color(GRID)
h1,l1=ax.get_legend_handles_labels(); h2,l2=ax2.get_legend_handles_labels(); ax.legend(h1+h2,l1+l2,frameon=False,ncol=2,fontsize=8.5,loc="upper center",bbox_to_anchor=(.5,-.14)); fig.subplots_adjust(bottom=.2); _show_fig(fig)
```

[code cell 18: 3 lines]
```
fig,ax=plt.subplots(figsize=(10.6,4.3))
for pdt in products: ax.plot(days,daily_prices[pdt],linewidth=2,label=pdt.title())
_forest_axes(ax,"Market · how did the visible quotes evolve?","Day","Market price"); ax.legend(frameon=False,ncol=4,fontsize=8.4,loc="upper left"); ax.grid(axis="y",alpha=.2); _show_fig(fig)
```

[code cell 19: 2 lines]
```
fig,ax=plt.subplots(figsize=(10.6,4.4)); ax.plot(days,daily_hands,linewidth=2.1,label="Hands"); ax.plot(days,daily_plants,linewidth=2.1,label="Plants"); ax.plot(days,daily_pastures,linewidth=2.1,label="Pastures"); _forest_axes(ax,"Capacity · what did the farm build and keep?","Day","Count"); ax.legend(frameon=False,ncol=3,fontsize=8.5,loc="upper left"); ax.grid(axis="y",alpha=.2)
ax2=ax.twinx(); ax2.plot(days,daily_bank,linewidth=2.0,color=PALETTE[2],alpha=.85,label="Bank"); ax2.set_ylabel("Bank",color=MUTED,fontsize=9); ax2.tick_params(colors=MUTED,labelsize=8); ax2.spines["top"].set_visible(False); ax2.spines["right"].set_color(GRID); _show_fig(fig)
```

## 8. Phase ledger — six-day operating windows
<div class="kg-prose"><div class="lead">Six-day blocks provide a compact diagnostic view of workload and market activity. They are descriptive only; the controller still acts from the live observation on every turn.</div></div>

[code cell 21: 9 lines]
```
windows=[("BLOCK 1",1,6),("BLOCK 2",7,12),("BLOCK 3",13,18),("BLOCK 4",19,24),("BLOCK 5",25,30)]
rows=[]
for label,d0,d1 in windows:
    sl=slice(d0-1,d1)
    start_bank=daily_bank[d0-2] if d0>1 else float(viz_env.steps[0][0].observation.farms[0]["money"])
    end_bank=daily_bank[d1-1]
    rows.append({"window":label,"days":f"{d0}–{d1}","bank Δ":end_bank-start_bank,"farm actions":int(sum(daily_farm_actions[sl])),"market orders":int(sum(daily_market_orders[sl])),"peak hands":int(max(daily_hands[sl])),"peak plants":int(max(daily_plants[sl]))})
ledger=pd.DataFrame(rows); _show_table(ledger,"Six-day ledger · workload and capacity",formats={"bank Δ":lambda x:f"{x:+,.0f}","farm actions":lambda x:f"{x:,}","market orders":lambda x:f"{x:,}"})
x=np.arange(len(ledger)); w=.36; fig,ax=plt.subplots(figsize=(10.6,4.2)); ax.bar(x-w/2,ledger["farm actions"],w,label="Farm actions",alpha=.9); ax.bar(x+w/2,ledger["market orders"],w,label="Market orders",alpha=.78); _forest_axes(ax,"Workload by six-day window · diagnostic view","Season window","Observed actions"); ax.set_xticks(x,ledger["window"]); ax.legend(frameon=False,ncol=2,loc="upper right",fontsize=8.5); ax.grid(axis="y",alpha=.2); ax.grid(axis="x",alpha=0); _show_fig(fig)
```

## 9. Inside the composite
<div class="kg-terminal"><span class="dim">selected opening mode: <code>HybridOpening</code></span><br><b>step 0</b> appends <code>BUY_SEED WHEAT 1</code><br>&nbsp;&nbsp;↓<br><b>steps 2–6</b> reuse an idle hand to walk west, plant WHEAT, and water it<br>&nbsp;&nbsp;↓<br><b>step 29 / step 52</b> keep the temporary crop alive; if the crop is missing, restore the pasture action instead<br>&nbsp;&nbsp;↓<br><b>steps 84–91</b> return to the site → WATER → HARVEST → rebuild pasture → return → DROP<br>&nbsp;&nbsp;↓<br><b>step ≥ 144 market lists</b> preserve executable demand while closing only genuine SELL holes<br>&nbsp;&nbsp;↓<br><b>day 27 · hour ≥ 16</b> replace only <code>BUY_SEED</code> market slots with no-ops<br>&nbsp;&nbsp;↓<br><b>the inherited controller</b> continues with the established route, storage, race, repair, livestock, timing, rescue, and closeout stack</div>


## 10. What remains deliberately simple
<div class="kg-grid"><div class="kg-card green"><div class="eyebrow">Single runtime</div><b>One <code>main.py</code> owns the complete submission.</b><span>No external Dataset or network call is required.</span></div><div class="kg-card teal"><div class="eyebrow">Selected branch</div><b><code>HybridOpening</code> stays fixed in the exact source.</b><span>The late-seed rule is a wrapper around the existing policy, not a new route family.</span></div><div class="kg-card gold"><div class="eyebrow">Bounded correction</div><b>The new layer touches only late <code>BUY_SEED</code> orders.</b><span>It does not use seed identity, opponent identity, archive identity, or hidden state.</span></div><div class="kg-card violet"><div class="eyebrow">Production QA</div><b>The archived file must resolve to <code>agent</code>.</b><span>A 720-turn file-path replay must also contain real actions and market orders.</span></div></div>


## 11. Submission boundary
<div class="kg-prose"><div class="lead">The charts and animation are notebook-only diagnostics. The uploaded artifact is the exact reconstructed <code>submission.tar.gz</code>, containing only <code>main.py</code> at archive root. Final checks verify archive bytes and re-run production callable selection on the archived source.</div></div>


[code cell 25: 25 lines]
```
import hashlib, tarfile, contextlib, io
from pathlib import Path
from kaggle_environments.agent import get_last_callable

with tarfile.open(archive, "r:gz") as tf:
    members = tf.getnames()
    assert members == EXPECTED_MEMBERS
    archived = tf.extractfile("main.py").read()
    assert archived == Path("main.py").read_bytes()
    assert hashlib.sha256(archived).hexdigest() == EXPECTED_MAIN_SHA256

assert hashlib.sha256(archive.read_bytes()).hexdigest() == EXPECTED_ARCHIVE_SHA256
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    archived_entry = get_last_callable(archived.decode("utf-8"), path="archived_main.py")
assert callable(archived_entry)
assert archived_entry.__name__ == "agent", f"unexpected archived entrypoint: {archived_entry.__name__}"

print("variant:", VARIANT)
print("files:", ", ".join(members))
print("internet required: NO")
print("external Dataset required: NO")
print("archive SHA-256:", EXPECTED_ARCHIVE_SHA256)
print("archive byte check: PASS")
print("archived production entrypoint:", archived_entry.__name__)
print("production loader gate: PASS")

```

## Takeaways
<div class="kg-grid"><div class="kg-card green"><div class="eyebrow">Production entrypoint</div><b>The archived file resolves to <code>agent</code> under Kaggle's callable-selection rule.</b><span>The final wrapper keeps the production entrypoint stable despite the long inherited source lineage.</span></div><div class="kg-card teal"><div class="eyebrow">Strong attached base</div><b>The candidate retains the attached base's mature HybridOpening and demand-preserving market closure.</b><span>The whole-season route remains inherited; the new layer is deliberately narrow.</span></div><div class="kg-card gold"><div class="eyebrow">Additional correction</div><b>Late seed replenishment is suppressed from day 27 hour 16 onward.</b><span>Every non-seed market order keeps its inherited position and order.</span></div><div class="kg-card violet"><div class="eyebrow">Artifact integrity</div><b>The notebook reconstructs the exact evaluated candidate bytes.</b><span>Source, archive, entrypoint, and executed-season checks are built into the artifact.</span></div></div>
