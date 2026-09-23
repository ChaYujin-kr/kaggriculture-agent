# Kaggriculture V56 — Smarter Seeds and Fertilizer

This revised V56 keeps the previously validated late seed budget and adds one independently tested fertilizer rule. The earlier seed budget stops purchasing wheat/carrot seeds that exceed all remaining planting opportunities. The new layer avoids spending another fertilizer on a wheat/carrot crop when existing coverage already lasts three days, or when the native scheduled harvest is predicted to be unchanged without it. Sequential worker actions are accounted for; unconfirmed reactive-worker plans retain their fertilizer. Crop production inputs remain available to the rest of the policy.

This is one additional mechanism, not three separate upgrades. Reusing stored fertilizer at purchase time and broadening sequential carrot substitutions were also tested, but failed or did not activate and were excluded. Newly published Fieldcraft was evaluated as an independent opponent; its source was not transplanted.

The source was frozen before confirmation. Tests use the unmodified official engine, reacting opponents, both seats and exact source hashes. Baseline below means the previous seed-budget V56, not V55. These are local results, not a guaranteed live rating.

| Panel | Previous V56 W/L/T | Revised V56 W/L/T | Previous winrate | Revised winrate | Point gain | Mean margin gain |
|---|---:|---:|---:|---:|---:|---:|
| Pilot: 4 worlds | 16/4/12 | 28/4/0 | 0.5000 | 0.8750 | +0.1875 | $+201.00 |
| Confirmation: 8 new worlds | 30/12/22 | 44/12/8 | 0.4688 | 0.6875 | +0.1094 | $+100.25 |
| Final: 4 more worlds, 6 rivals | 35/5/8 | 40/4/4 | 0.7292 | 0.8333 | +0.0625 | $+97.52 |

A paired physical diagnostic kept wheat/carrot harvest quantities unchanged and produced two extra strawberries after retained fertilizer became available to later work. This is a diagnostic of one world, not an assertion that every action or crop total is unchanged. Competitive results include reacting market prices: some improvement comes from reducing the rival's revenue, and not every own-cash result improves. Related opponent lineages and both seats are correlated; research uncertainty is grouped by whole world seeds.

The agent is standard-library-only. Original Apache-2.0 notices are retained, including Thomas Tschinkel, Yusuke Hayashi, destbreso, aurax7, Tetsutani, prvsiyan, Dmitrii Gluzdov and Seyit Kaan Gunes. Ahmed Berat Ozer's additions are the remaining-planting seed budget and harvest-aware fertilizer cap, with integration and independent evaluation.

Run the three code cells on CPU. No dataset attachment, Internet, GPU or training is required. The notebook writes `submission_competitive_v56.tar.gz` in `/kaggle/working`; it does not submit or publish anything.

Source SHA256: `a1ad0fd1d174477ee2cbdd561a812bcb7029647ce34599e79d6b79e9057eff6c`. Isolated normal-GC maximum callback: 28.832 ms on the tested Windows host.


[code cell 1: 5 lines]
```
from pathlib import Path
OUTPUT_ROOT = Path('/kaggle/working') if Path('/kaggle/working').exists() else Path.cwd()
WORKDIR = OUTPUT_ROOT / 'v56_agent'
WORKDIR.mkdir(parents=True, exist_ok=True)
print('Agent directory:', WORKDIR)

```

[code cell 2: 206 lines]
```
import base64, hashlib, zlib
EXPECTED_MAIN_SHA256 = 'a1ad0fd1d174477ee2cbdd561a812bcb7029647ce34599e79d6b79e9057eff6c'
SOURCE_BLOB = ''.join((
    'c-q{(XM5txvM~DHzd{(BL-Y_07_h-)o1E>r0|+EQAS5h_Z2a4A2StL%Yp;Fo^S*cX>@^^|tE;Q4D|gFG)FpwG=<)V}Xo@r;O=yDQ#05Q+Xo{#X3)<zmCvw|?z)<A{%`x1V81kGX@GMIUcSMaQMUfeE1VgbjvF3#tEr<lQ6ktOLY{Uqn1U?BgO;F@kBqW|#up}ori8UBkAV`iPCZw>UK{K8M7|`<tFOb5PSWjqDB8CFLa6(WVA%Hf#fRThSIDq1U6s0A22EkA?%d7xM_&e%+M^r!`8UV+AmIIa<5=B}fSAJq4@YHfBF+7Jl&q;v0WSCrI!iWU;OG=W!43>~00=*PzC+fgRA|Zmd+!zcggBJOvFr>j_hGhwkrYVttC_$)z5OWfac1NTbksJVW@eBB!WC@yEF#yn<<|G$I12R+K6G3kPec;b5Ge87kd6I&36?rrrQW#DkaDbsmvm+Noon!z}?yk&4fgggN3vxIk$FR?wr<f5lL>P!p!t3_lyWC-y*L_En1qL($t(AE~k_fa0>y;dj1!lNp5v9fDV9tO=2aQ(YU%m%r?k!)KuqMEW6WZmyb2|x+mzW_f5(Ap$*EX<XOA+C{3KJ~31$+WP*AmHer9+GXD>%^?!irZ6Axew{eh#QfF9=WA>m(+;!0f<dznl047Yv|Hc)T_zkt{cB`E(6@NYrZO23nt7x|RYXkPAdl3d|0T4!#il2z&%&8!;>mCz$S3T%Mp0P?Bc>CSYMOr^`Gc(jQBj8{(b82msb#OKd0PHstvwPWXjO-~n?8fSw+YOJwE?u(mo%*iLDP2D}dvLx3nlfg$gR5-(xWN|4XUrNl#a0gK3PVgH1-HV*)K@S`Y+VEwrn%{padoL~ot(f|;U2Q0c2$W0LJ99j~W63H=60A(SpL}p83j!%KH1co89>~cr(t2;tN82}O(yar-KT}Xu|@QR+!YUT5QbwP6rfRPiEIcWP#1NlOfceLOn>huC^?*Z5^VZ?zDM4e`_u$j}t2|!bvKcGF|!)(>#1q$xP61@iG*EWZKN5LH+fHi_k13^|~hV*(p&%eNb{Yl+s|0OYVxV9{q2|1=8RGK(-^M_E>Z9#*v_&GBa@wVrHv=q>|5sf0t1rP-^IR{{eG$#ULjern2OC)bdC6fQAL`nk6jA`*fUR5YbU67HXJOq;<#!FJ5BF8IAEGAnKvJhYbVUFekcw@Mv;kKa21*AF<$15*btTiJ|h<iU+c-)o&G7QKwX1-)G8{8d{2QCPS#iv9rXiOZmSO6;86$_FPz!q9OoZl<%@G-@Y2^DZ+I{Cv7L>=@6eL}jGbP^&7b{b2QlvA7G5Qqg{o+kuaTXJB<fe4;JO$A7(jTyPTk<?v-Kme2>%fK1R!c
```

[code cell 3: 19 lines]
```
import ast, gzip, hashlib, io, tarfile
source_bytes = MAIN.read_bytes()
assert hashlib.sha256(source_bytes).hexdigest() == EXPECTED_MAIN_SHA256
assert [n.name for n in ast.parse(source_bytes).body if isinstance(n, ast.FunctionDef)][-1] == 'e410_agent'
ARCHIVE = OUTPUT_ROOT / 'submission_competitive_v56.tar.gz'
buffer = io.BytesIO()
with tarfile.open(fileobj=buffer, mode='w') as tar:
    info = tarfile.TarInfo('main.py')
    info.size = len(source_bytes); info.mtime = 0; info.mode = 0o644
    tar.addfile(info, io.BytesIO(source_bytes))
with ARCHIVE.open('wb') as stream:
    with gzip.GzipFile(fileobj=stream, mode='wb', mtime=0, filename='') as zipper:
        zipper.write(buffer.getvalue())
with tarfile.open(ARCHIVE) as tar:
    assert tar.getnames() == ['main.py']
    assert tar.extractfile('main.py').read() == source_bytes
print('Ready:', ARCHIVE)
print('main.py SHA256:', EXPECTED_MAIN_SHA256)
print('No competition submission was made.')

```