# 40/40 Early Floor | 39/46 Top-10 | v48 Fast Routes

**v47's live artifact produced no meaningful play: all 11 recorded
games ended at exactly 3,000, and its action stream contained no
non-PASS action. v48 fixes the execution path and then returns to
the idea that made v43 climb: a stable public backbone with only a
few empirically justified continuations.**

| Frozen-action panel | **v48** | Mean margin | Worst margin |
|---|---:|---:|---:|
| previous first 20 opponents, both seats | **40/40** | +18,708 | **+64** |
| current Top-10 holdout, both seats | **39/46** | +5,991 | -26,535 |
| current Top-30 holdout, both seats | **97/140** | +2,197 | -42,048 |
| v43 public-era 58 opponents, both seats | **103/116** | +13,182 | -25,480 |

These are reproducible local replays against frozen public action
streams—not Public-LB claims. The title reports two explicitly
named panels, not an unseen ladder score.

    v43/v44-compatible floor
      + first-shop fast-route continuations
      + one narrow BAKERY capital recovery
      + one child controller call per turn
      = v48 Fast-Climber Sparse Route Hybrid

## 1. The immediate failure was execution, not a bad matchup

Every one of v47's first 11 ladder games returned the starting
capital of 3,000. Its submitted action stream was PASS-only for all
719 turns. Therefore 0/11 cannot be interpreted as eleven strategic
losses.

The risky implementation pattern was evaluating four complete
stateful child policies before the decision point on every turn.
One irrelevant child exception—or hosted timing pressure—could
collapse the whole comprehension into the outer PASS fallback.

v48 makes the invariant structural: **exactly one selected child is
called per turn**. Build smoke records 719 policy calls and 719
child calls in each seat, and clean-import tests require a non-PASS
first action. The fallback remains only as a last crash guard.

## 2. Learn from fast climbs, but do not paste one tape globally

I froze the current Top-30 and audited each submission
chronologically. Crop Dusta, junseok lee, taiseiu, and Kaileh57 all
opened **20/20**. For route selection, each team was split by time:
earlier public episodes formed the route pool, while the newest two
episodes per team stayed in holdout.

The best single current route managed only
**29/46** on the untouched
Top-10 panel. The v44 floor managed
**35/46**. The sparse hybrid reaches
**39/46**. This is the key result: the
gain comes from preserving options and selecting compatible
continuations—not declaring the newest route universally optimal.

Two train-only public trajectories supplied the new branches:

- first YARN_STORE: [Kaileh57, episode 98720726](https://www.kaggle.com/competitions/kaggriculture/episodes/98720726), switching after the shared step-87 prefix;
- first FARMERS_MARKET: [taiseiu, episode 98706979](https://www.kaggle.com/competitions/kaggriculture/episodes/98706979), switching after the shared step-119 prefix.

Public replay provenance is behavioral citation; it does not imply
ownership of another participant's source code.

## 3. Sparse closed loop: six routes, four observable events

The default remains the v43/v44-compatible route. Runtime never
reads identity, rating, episode ID, Notebook origin, submission ID,
or future actions. It observes only legal public game state.

```text
default
  first shop YARN_STORE at step 88
    -> Kaileh57 fast YARN continuation
  first shop FARMERS_MARKET at step 120
    -> taiseiu fast FARMERS continuation
  second YARN_STORE at step 153
    -> retained v43 YARN continuation
  validated third-YARN state at step 216
    -> retained v44 YARN continuation
  BAKERY then PIZZA + visible 3C/2S/melon capital state at step 160
    -> Cary Jin capital continuation
```

The BAKERY branch is deliberately narrow. Before it, the old
first-20 panel was 39/40; after it, 40/40 with a worst margin of
+64. Broad BAKERY routing was not admitted.

A clone-aware market expert still adjusts SELL priority, but a
public-state veto disables it in the BAKERY sheep/crop state where
preemption previously created two regressions. This keeps the
market layer subordinate to route legality and capital formation.

## 4. Evaluation matrix and the promotion rule

| Panel | Games | Wins | Win value | Worst-seat | Failures |
|---|---:|---:|---:|---:|---:|
| old first-20 × both seats | 40 | **40** | 1.000 | 1.000 | 0 |
| current Top-10 holdout | 46 | **39** | 0.848 | 0.826 | 0 |
| current Top-30 holdout | 140 | **97** | 0.721 | 0.700 | 0 |
| v43 public-era 58 × both seats | 116 | **103** | 0.888 | 0.862 | 0 |
| v47's 11 live opponents × both seats | 22 | **22** | 1.000 | 1.000 | 0 |

Promotion required all of the following: repair the 40-game early
floor, preserve 39/46 on the untouched Top-10 holdout, remain above
70% win value across the Top-30 panel, make no runtime error, and
improve on both seats. v48 passes those gates.

Limitations remain material: replay opponents cannot react to the
counterfactual agent; repeated lineages reduce effective sample
size; local and hosted engines may differ; and the next live games
are the only true walk-forward test.

## 5. Lineage-safe evaluation, runtime-blind deployment

Team- and seed-grouped folds leak when many teams share one action
lineage. Route extraction and holdout were therefore chronological
within team, and continuation conclusions were checked across both
seats and multiple public generations. The broader correction—use
action-stream lineage only to construct evaluation folds—follows
[Georgy Mamarin's Kaggriculture Episodes dataset](https://www.kaggle.com/datasets/georgymamarin/kaggriculture-episodes).

Lineage is **evaluation metadata only**. Deployment conditions on
shops, public farms, prices, inventories, money, step, and internal
controller memory. That distinction keeps the agent legal and
tests the behavior it can actually reproduce at runtime.

## 6. Prior work and public provenance

- stable backbone and previous public result: [v43 Sparse Shop Hybrid](https://www.kaggle.com/code/kaitofukami/103-128-fresh-public-v43-sparse-shop-hybrid)
- default route provenance: [ActiveMusyoku, episode 96815867](https://www.kaggle.com/competitions/kaggriculture/episodes/96815867)
- BAKERY capital continuation: [Cary Jin, episode 98316955](https://www.kaggle.com/competitions/kaggriculture/episodes/98316955)
- public meta analyses: [Rayk Kretzschmar](https://www.kaggle.com/code/raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta), [beicicc](https://www.kaggle.com/code/beicicc/kaggriculture-c20-exact-replication-control), and [prvsiyan](https://www.kaggle.com/code/prvsiyan/kaggriculture-frontier-the-moon-counts-melons)

The purpose of publishing is not to freeze one route as the answer.
It is to make the failure modes, provenance, and falsification tests
explicit enough that the community can build the next idea rather
than reproduce an unexplained artifact.

## 7. Exact artifact integrity

- `main.py`: **107,008 bytes**
- SHA-256: `dadee25a9840313218384208c53b2c4752f82c3209cc654632e0b96c65e2664a`
- deterministic `submission.tar.gz`: `f2973a7c7636e1f95cea74c8c2cb7bbfec20f4082a9da079aeb8ba74fbe8b4fe`
- focused controller tests: **16 passed**
- build smoke: both seats `DONE`, first action non-PASS
- controller invariant: **719 policy calls = 719 child calls**
- external runtime packages: none
- identity/lineage/future-action runtime fields: none

The next cell reconstructs the exact submitted bytes and archive.

[code cell 8: 1287 lines]
```
from pathlib import Path
import base64
import gzip
import hashlib
import io
import json
import tarfile
import zlib

payload = (
'c-'
'pLdTi2?{mgRf?iZm5U^q2!gP)kL?8+cbh#2y856BPjkxd`fSZ}a5#tJB@pJ$j7p{ql)K#0*v})|zugxc~U$kEqu8_ur#h?f1jQ^Z'
'ehhmoWJK9(%w0rh57Ppa%DfemOas>Hn^K?)~J3>iy)o!JmKp@yBn!ot&%Z-+$NCz{G3ct8?JF-_OA#_<p=UuIA50dO2yo{q~z-'
'9)4FoGf=LoZmX7AbXCWM{{6S#KmQ!h2ruUEoxjHT^Y4q`Ps_aj-'
'R7T7PKR%+Q}FxTbIred{tvzX3H#^lpO^gS^S^Ze&vt(*%Heb|73I_6kG2-'
'N#>F%$zb5tXfBatl{jXl1KYtK^{I6Yqwfkr9zuNs*E$+vE-'
'u`d@@pJQE9_zpT)$2b#xBtHWXA|GNhrav$=3h*8@l@lV5Al!R126RTuf49SZ@Tw?{I2}tcl~&}7{4a-'
'r~kQeKmE06#XtW1<HvA+H~&wA{SV9V_f6=x|65D`AFTLaS?|BJ+~1hL{a={IOiaC~d(QO(R{Yxr|M;J$@Q>gB_^a6;(7)U<PWoL@'
'{<jtg%)5HO`^A4n|GUk9{4(ixEa<;nA!YNi;B3(srUULX;lEykKmS^+p!k=!|7n<iP1!etp!oOu@~76o{`%4|i@z2BIpV+R760-'
'^QI`wtmvbEh<Mkwj5oEZTcjIiWq#}UtFk)de<7;{!``)&R7-'
';@DaSTwK;Wx5Z`M19ZDstPRI|^GZ1Xz;|=D3=!ZWMc0=xkhTOqjC}1LCt&GLA<dn-%IecWqIP^?lB)-|H$pKAP}_;l6`~J7(ix-a'
'I3U>8fz9_p*H~WH*b8F&^ROVy6h^2XbsWFnHeit?RDYAu_NgF||oI&fA51y-q?E733f7%(+js#x-@mWBYs_+AhwK+GcIg-'
'B00`*(Kx7^m0ZXgZhN%-bPkdt+vTay0(WG{+t_A9-kF~z9sIl?lh-H-'
'kCFnnF62)8b8@v?HUQN)ST+`Wf8i*7v>kroBB?H>`0rGo^*P;@lsaW4E8fgVJ9PgZft<<j<<yQWnX*N6fZBjC-'
'NwfQ)_t};P0#nw5>o)tApHPd!G9JgZ4;z!0N&3h5BI^nAO&%>ivRB#{<G0-yOY@cv(=PZ)EYLRo-~TxP50+*cO*%(>DY(5DUF-_E'
'4e=LE>1dpNQMaAHdTFYvQV!n4qouDsb)5t8t@!Uz4#)4R*`RU^ip$qjo<>*dW+?_`b{M(Ui)!HeU!i)SC|*W`Xl<Te5+k*Sn9X7r'
'a-VQ2n&;Pb=5@rdd2#9S)-'
'IQzZ8i@X8g4qQH4Yl_Xz(%+^fms?mkoqlF*Oy4BVz6RCU5Y#5&SVPKYEYGM?;UXLQ(#E77GxL=u4VzVj>
```

[code cell 9: 2 lines]
```
# Full public source: exactly the bytes written above.
print(agent_bytes.decode("utf-8"))
```

[code cell 10: 72 lines]
```
import hashlib
import importlib.metadata
import importlib.util
import sys
import traceback
from pathlib import Path
from kaggle_environments import make
import kaggle_environments.envs.kaggriculture.kaggriculture as kaggriculture_module

def load_module(name):
    spec = importlib.util.spec_from_file_location(name, "main.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def pass_agent(obs, configuration=None):
    seat = int(obs.get("player", 0))
    hands = (obs.get("farms", [{}, {}])[seat].get("hands", []) or [])
    return {"farmer": ["PASS"], "hands": [["PASS"] for _ in hands], "market": []}

engine_path = Path(kaggriculture_module.__file__)
print({
    "kaggle_environments": importlib.metadata.version("kaggle-environments"),
    "engine_sha256": hashlib.sha256(engine_path.read_bytes()).hexdigest(),
})
summaries = []
for seat in (0, 1):
    module = load_module(f"v48_smoke_{{seat}}")
    failures = []

    def candidate(obs, configuration=None):
        try:
            return module._V48_POLICY(obs, configuration)
        except Exception as exc:
            if len(failures) < 5:
                failures.append({
                    "step": int(obs.get("step", -1)),
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "traceback": traceback.format_exc(limit=4),
                })
            return pass_agent(obs, configurati
```

## 8. What would falsify v48?

Reject the design if the first live block again contains a 3,000
execution trace, if YARN/FARMERS branches lose outside their source
family, or if the BAKERY gate fires without a positive capital
delta. A failure should trigger a new chronological holdout and a
smaller causal correction—not another unconditional route layer.