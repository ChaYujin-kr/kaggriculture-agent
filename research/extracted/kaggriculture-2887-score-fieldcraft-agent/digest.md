<div style="background:#102c28;color:#f4f7ec;padding:36px 32px;border-radius:18px;border-bottom:6px solid #d5b46b;">
<p style="color:#d5b46b;letter-spacing:3px;font-size:12px;font-weight:700;">KAGGRICULTURE · PUBLIC AGENT + MATCH LAB</p>
<h1 style="color:#ffffff;font-size:44px;line-height:1.1;margin:12px 0;">Fieldcraft</h1>
<p style="font-size:19px;color:#d9e7de;">From a working farm to a submission you can run.</p>
<p style="margin:24px 0 0;"><b style="font-size:36px;color:#efd08b;">2887.4</b><br>Historical public submission rating · checked 21 September 2026</p>
</div>

A compact release of a previously submitted agent, with an offline build, a complete match demo, and diagnostics you can reuse. **Run all cells to create `submission.tar.gz`.** No GPU, API key, or private dataset is needed.

| Included | What you get |
|:--|:--|
| **Play** | A complete agent that produces farming and market actions |
| **Inspect** | Cash trajectories, action counts, and two seat-swapped demonstration games |
| **Submit** | A verified archive, SHA-256 checksums, and download links |
| **Experiment** | Editable seeds and a simple opponent you can replace |

The **2887.4** figure belongs to original submission **56258004**, submitted **15 September 2026**, as returned by Kaggle's authenticated submissions API on **21 September 2026**. It is a historical rating, not a promised score for a new submission or a local cash result. The compact release is a transformed version; its packaging checks are described below.

## 01 / Start here

1. Choose **Copy & Edit**, then **Run All**.
2. Read the completed match diagnostics and download **submission.tar.gz** from the output files.
3. On the [Kaggriculture competition page](https://www.kaggle.com/competitions/kaggriculture), submit that archive after accepting the competition rules.

The build uses Python's standard library. The match lab uses `kaggle-environments==1.32.7`, pandas and matplotlib. If Kaggle's preinstalled engine differs, the setup cell downloads the pinned official package; keep notebook Internet enabled for that step. Set `RUN_MATCH_LAB=False` for an offline archive-only build. The agent itself runs without Internet, and the notebook never submits to the competition automatically.

[code cell 2: 9 lines]
```
from pathlib import Path
import base64, hashlib, io, json, tarfile, zlib
from IPython.display import HTML, FileLink, display

ROOT = Path('/kaggle/working') if Path('/kaggle/working').exists() else Path.cwd()
RELEASE_DIR = ROOT / 'fieldcraft_release'
RELEASE_DIR.mkdir(exist_ok=True)
SEEDS = [2026]   # Each seed is played from both seats; increase for your own checks.
RUN_MATCH_LAB = True
```

## 02 / Build the agent

The distribution below contains minified Python source with shortened local names, compressed for a compact notebook. It is **obfuscation, not encryption**: runnable public code is recoverable. The payload has been checked before packing; it contains the agent and public route data, with research comments removed. Its only agent dependencies are the bundled route module and Python's `math` module.

The visible harness checks decoded-source hashes and builds the archive. The large payload cell can stay collapsed while you work through the match lab.

[code cell 4: 4 lines]
```
PAYLOADS = {'main.py': 'c-qx{S$7&a7vQt~E1ZXKs4~J0#Bma^e5R@>_RWB|a5#0ajU76+aRbisW%A$WE|N-BkfmqNJWThAsghJ$ukNm^$h(%Apx17P!6>SRgHfa1_z(^<yOB4QnTOf*HoBc%uUDAxL1z53M!ORAz2WF=5MtVu%sf9#Z)Q+z`VA8<WoG^~U(crx_;vwxOjqk@wVplW`?<{g^D=!}&(~D=OlH1J*Rv%)k7VY0zFdFA=b_AeoIl;q@Oc0&EEj*zZq~C~d_R?$VKImnpYWv*T^gKqgL*XV_ePk~lbO}@GZ*d3Of?KE_}GDtET*@d-p1;evsJWSs9v|Qq#8WFH&w@AT&7F|8t(LZqk1EZhV@<_)9NzQ2*M~BgkHxa)@0_+{;(=DH;c!|`C5%2g#7t(wZ`WPbY;5yJma?jzg({85A***1urm94|-mGocyb(?R9B9p3FQho@SKw9>z9*noVgM-{C;-@#(G1TzP|TG#vGKt&U`7R4Cxn8=1NAM!d|2GE*6F$6wQ8KCR=`EXqv3@!^AK##VqLQ(mOJ%y6my%FN5t!{X)>d<Uz0yM!tbV7|dp{IkS?eYHxgJ}#ay_lwM|7hj&>=`&2eH|T_eVbt*ktq|AoMP@o-yVr%sHIIDAE4kt~uiNN&ZFpbGOt&`})#33USfJh+JwC$#!y#6*keSe<rzcp`#q!f^iLE~(n0}r;trtri!h_7zy}>zu@=0bs&7W|o{+5|<^VtI~#hivTmzi3xH^k}u2s1Hzx&<(WmwT8eSQ`BL4)@aqJj|dwqk(tfhl9Ztyx&rp0KdI~ta=#YjKcN{Yc+V7;#3E%Gfae?w)#lG0{iQt*TaFr#_BZMEqH=WRd3Lep5xw_-^{RUu$OL@3*2R}lcrDeN7{iyp056&S2+u?dxLo3bNcR-7X2G-LfB4$HyF@Pf{k=HT|Q!wE;aKRHUzxDP6Du`PhlU8dL3`ngJ;-5YLmm>0R%CGr-rqw5Z3BkB{c<`WEi$_U{yI<zRY%`P*$f8D|moCaZwLF>_mXu<LMR~^JNzR9^eije+tV8aCNs_JnlWtm&?U6LcradKRz#(>%EcJ4|mm&hcc>&s4t?nh-M;s5z)1XE=6=DqQ<UT^ROZ@k5jLy5Pq<W+vlw;&~G8H9*$&j7Z)M|ECi3V#j1_La3rJ9dW*U}EG47rE~2ac0PqC9RJ^Mr2|MI|<`fPOMd9e3i)n9l+R-~vcweNnLOv=KRC@6+FN*J=ELL{W=vI0cI;U_Xibsd8>J;o#7_wIsfSll8W49dwl6kiaJ0Cj;KT&uIU@4FC^wRMzhms#hokrI@0wRCC%d5+kMpOe<{F#bW!gk|49MAv}%uUmM-87c$_M)0MsD#~U09z9$I>a;_MIr%fj1$y1avb@S-AeJje2;&jNw3mwbVK>J@QxC?p*IL|=BxBt1Dqx^_tWL=4DibB>~1f*h2+JP<Cb=J=68Efi}fB9EG=j2m*vwQw1lbVQ}b=fld22j{G_Z(dwcU0)e!l60
```

[code cell 5: 31 lines]
```
header = '# Fieldcraft R1 | Apache-2.0 | See NOTICE.txt and LICENSE.txt.\n# Adapted distribution: local-name minification and compressed Python source.\n'
for name, encoded in PAYLOADS.items():
    decoded = zlib.decompress(base64.b85decode(encoded))
    assert hashlib.sha256(decoded).hexdigest() == RELEASE['compact_source_sha256'][name]
    compile(decoded, name, 'exec')
    source = header + 'import base64 as _b85, zlib as _zl\nexec(_zl.decompress(_b85.b85decode(' + repr(encoded) + ')), globals())\ndel _b85, _zl\n'
    destination = RELEASE_DIR / name
    destination.write_text(source, encoding='utf-8', newline='\n')
    assert hashlib.sha256(destination.read_bytes()).hexdigest() == RELEASE['distribution_sha256'][name]

(RELEASE_DIR / 'NOTICE.txt').write_text(NOTICE, encoding='utf-8', newline='\n')
(RELEASE_DIR / 'LICENSE.txt').write_text(LICENSE, encoding='utf-8', newline='\n')
archive = ROOT / 'submission.tar.gz'
# Fixed timestamps and ownership make the output reproducible.
import gzip
with archive.open('wb') as raw:
    with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w') as bundle:
            for name in ['main.py', 'mirror_plan.py', 'LICENSE.txt', 'NOTICE.txt']:
                data = (RELEASE_DIR / name).read_bytes()
                info = tarfile.TarInfo(name)
                info.size = len(data); info.mtime = 0; info.mode = 0o644
                bundle.addfile(info, io.BytesIO(data
```

## 03 / What to watch during a match

The agent combines a recorded production plan with adjustments based on visible farm and town state. Farming operations and market orders are coordinated so that harvested goods can reach storage and be sold. Route selection and economic decisions can change as shops become visible.

Three practical questions make a replay useful:

| Question | Diagnostic | Why it helps |
|:--|:--|:--|
| When does the farm turn activity into cash? | Cash trajectory | Separates spending periods from revenue periods |
| Where do the workers spend their actions? | Action mix | Highlights movement, harvesting, and idle time |
| Does a result depend on player position? | Both seats | Exposes seat dependence before a larger evaluation |

Cash curves show the balance, **not profit per crop**. An emitted `SELL` is a request; its quantity is not proof of a fill. Action counts therefore describe decisions, not completed transactions.

[code cell 7: 43 lines]
```
import contextlib, importlib.metadata, os, subprocess, sys, time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter

try:
    engine_version = importlib.metadata.version('kaggle-environments')
except importlib.metadata.PackageNotFoundError:
    engine_version = None
if RUN_MATCH_LAB and engine_version != RELEASE['engine_version']:
    print('Installing the pinned official Kaggle engine (Internet required for this step).')
    install = subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', '--no-deps',
                              '--disable-pip-version-check', 'kaggle-environments==1.32.7'],
                              capture_output=True, text=True)
    if install.returncode:
        raise RuntimeError('Engine setup failed. Enable Internet and rerun. ' + install.stderr[-1200:])
    importlib.invalidate_caches()
    engine_version = importlib.metadata.version('kaggle-environments')
LAB_READY = RUN_MATCH_LAB and engine_version == RELEASE['engine_version']
print('Installed engine:', engine_version)
if LAB_READY:
    engine_file = importlib.metadata.distribution('kaggle-environments').locate_file(
        'kaggle_environments/envs/kaggriculture/kaggriculture.py')
    assert hashlib.sha256(Path(engine_file).read_bytes()).hexdigest() == RELEASE['engine_sha256'], 'Engine source differs from the verified release.'
    # Optional games registered by the package can print native-library warnings.
    # Silence that im
```

### A small, transparent demonstration

The opponent below passes every turn. It is deliberately simple: these matches verify that the agent runs and make the plots easy to read. **They do not estimate leaderboard strength.** Replace it with a legal reactive baseline and use many fresh seeds for a competitive benchmark. Independent module state is essential when loading two different agents that share module names.

[code cell 9: 33 lines]
```
def passive_opponent(observation, configuration):
    return {'farmer': ['PASS'], 'hands': [], 'market': []}

games, summaries, traces, action_counts = [], [], [], Counter()
if LAB_READY:
    for seed in SEEDS:
        for seat in (0, 1):
            sys.modules.pop('mirror_plan', None)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                env = make('kaggriculture', configuration={'seed': int(seed), 'episodeSteps': 720}, debug=True)
                players = [passive_opponent, passive_opponent]
                players[seat] = str(RELEASE_DIR/'main.py')
                started = time.perf_counter()
                env.run(players)
            statuses = [s.status for s in env.state]
            assert statuses == ['DONE', 'DONE'], statuses
            final_farms = env.state[0].observation['farms']
            summaries.append({'seed': seed, 'seat': seat, 'agent_cash': final_farms[seat]['money'],
                              'opponent_cash': final_farms[1-seat]['money'], 'status': 'DONE',
                              'seconds': round(time.perf_counter()-started, 2)})
            for index, state in enumerate(env.steps):
                farms = state[0].observation.get('farms')
                if farms:
                    traces.append({'seed':seed, 'seat':seat, 'step':index,
                                   'agent_cash':farms[seat]['money'], 'opponent_cash':farms[1-seat]['money']})
                action = 
```

[code cell 10: 22 lines]
```
if LAB_READY:
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':11, 'axes.spines.top':False,
                         'axes.spines.right':False, 'axes.titleweight':'bold'})
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), gridspec_kw={'width_ratios':[1.4,1]})
    fig.patch.set_facecolor('#f7f8f2')
    trace = pd.DataFrame(traces)
    for (seed, seat), frame in trace.groupby(['seed','seat']):
        axes[0].plot(frame.step/24, frame.agent_cash/1000, label=f'Agent · seat {seat} · seed {seed}',
                     color=['#246b58','#c59132'][seat], linewidth=2.3)
    axes[0].axhline(summaries[0]['opponent_cash']/1000, color='#909b95', linestyle='--', label='Passive opponent')
    axes[0].set(title='Activity becomes cash', xlabel='Day', ylabel='Cash ($ thousands)')
    axes[0].legend(frameon=False, fontsize=8)
    common=action_counts.most_common(7)[::-1]
    axes[1].barh([x[0] for x in common], [x[1] for x in common], color='#246b58', height=.62)
    axes[1].set(title='Where worker actions go', xlabel='Emitted unit actions · both seats')
    for ax in axes:
        ax.set_facecolor('#f7f8f2'); ax.grid(axis='x', alpha=.14); ax.set_axisbelow(True)
    fig.suptitle('FIELDCRAFT / MATCH LAB', x=.06, ha='left', color='#173f35', fontsize=16, weight='bold')
    fig.text(.06,.005,'Demonstration against a passive opponent. These results are not leaderboard ratings.',color='#66766e',fontsize=9)
    fig.tight_layout(rect=[0,.04,1,.94])
    fig.savefig(ROOT/'match_lab.
```

## 04 / Read the score honestly

| Evidence | Result | Interpretation |
|:--|:--|:--|
| Original Kaggle submission **56258004** | **2887.4** | Historical public rating, verified 21 September 2026 |
| Local packaging verification | See release checks below | Checks transformation and loading, not strength |
| Notebook match lab | Generated by this run | Functional demonstration against a passive opponent |

The original agent's rating can be checked by its owner with `kaggle competitions submissions -c kaggriculture -v`. [Kaggle's leaderboard](https://www.kaggle.com/competitions/kaggriculture/leaderboard) shows current team standings; it is not an archive of every historical submission score. A fresh submission starts its own match history, and the opposition changes over time.

The release manifest connects the score record to the original archive and records the compact source and distributed-file hashes. It is a provenance record, not an independent public attestation by Kaggle.

### Release checks

The minified agent matched the original agent on **2,876 actions across four complete games** (two seeds, both seats). All games completed, and a separate game passed through Kaggle's file-path loader. Tests used the pinned 1.32.7 engine. This is finite behavioral equivalence evidence, not proof over all possible states.

The audited source contains no credential, network, or file-access code. The publication bundle is built from an explicit file allowlist; private experiment logs, local paths, and private notebook or dataset references are excluded.

## 05 / Take the next useful step

For an experiment that teaches you something, replace the passive opponent with a reactive agent, run both seats over fresh seeds, and report wins, ties, and median cash margin separately. Change one mechanism at a time and keep a held-out set of seeds untouched.

If you find a reproducible failure, share the engine version, seed, player seat, and the first unexpected action. Those details make feedback actionable.

### Credits and license

This is an adapted release. Public route lineage includes **Ahmed Berat Ozer's V43** and **yhay81's shop-router series**. Retained upstream credits include thomastschinkel, destbreso, aurax7, tetsutani, prvsiyan, Dmitrii Gluzdov, and Rayk Kretzschmar. hakdevelopment contributed the release's control and market integration and this notebook. Public recorded play supplied the base route. Full notices and Apache-2.0 terms are included in the archive.

- [yhay81 · shop-router-0909](https://www.kaggle.com/code/yhay81/shop-router-0909)
- [yhay81 · shop-router-0911-simple](https://www.kaggle.com/code/yhay81/shop-router-0911-simple)
- [Ahmed Berat Ozer](https://www.kaggle.com/ahmedberatozer)
- [Kaggle Environments](https://github.com/Kaggle/kaggle-environments)
- [Competition rules](https://www.kaggle.com/competitions/kaggriculture/rules)

[code cell 14: 6 lines]
```
display(HTML('<div style="background:#102c28;color:#f7f8f2;padding:22px 26px;border-radius:12px;"><b style="font-size:22px;color:#efd08b;">Ready to run your own match.</b><p>Download the agent archive and keep the manifest with your results.</p></div>'))
display(FileLink('submission.tar.gz'))
display(FileLink('release_manifest.json'))
if LAB_READY:
    display(FileLink('demo_results.csv'))
    display(FileLink('match_lab.png'))
```