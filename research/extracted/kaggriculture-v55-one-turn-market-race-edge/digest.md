# Kaggriculture V55 — One-Turn Market Race Edge

V55 keeps V54's production, purchases, route tables, field actions, and visible wheat-price guard intact. It changes one market parameter: a planned premium-product sale may be reserved 41 turns ahead instead of 40. That extra turn matters when close Frontier-family agents compete for the same demand, while leaving most worlds unchanged.

The candidate was frozen before two independent confirmations. Every game below used the unmodified official engine, both seats, 719 callbacks, terminal `DONE`, exact action replay on the checked fixtures, and no telemetry errors.

| Panel | V54 W/L/T | V55 W/L/T | V54 points | V55 points | Paired margin gain |
|---|---:|---:|---:|---:|---:|
| Five-lineage selection, 3 worlds | 21/5/4 | 25/5/0 | 0.7667 | 0.8333 | $+64.93 |
| Six-lineage confirmation, 4 new worlds | 38/2/8 | 42/4/2 | 0.8750 | 0.8958 | $+63.88 |
| Frontier/Auto stress, 8 new worlds | 16/2/14 | 24/6/2 | 0.7188 | 0.7812 | $+56.00 |

Across the three panels, V54 scored 75/9/26 and V55 scored 91/15/4 over 110 games per arm. Match points rose from 0.8000 to 0.8455 and paired mean margin rose by about $61.9. The final untouched stress panel improved points by +0.0625, margin by $+56.00, and own cash by $+19.81. Its worst paired change was $-14 and its best was $+385.

The broader search rejected more aggressive 42/43-turn horizons because each regressed in 10 paired games despite larger mean-dollar gains. It also rejected opening, post-consumption sale, animal service, crop salvage, final courier, and apparent no-op patches. V55 contains none of those layers.

The public lineage credits and Apache-2.0 notices for Tetsutani, haideptry, Dmitrii Gluzdov, prvsiyan, and upstream contributors remain inside `main.py`. Ahmed Berat Ozer performed the current-meta audit, sequential-engine correction, official-engine selection, independent confirmations, packaging, and validation for V55.

Run the three code cells on Kaggle CPU. The last cell writes `submission_competitive_v55.tar.gz` to `/kaggle/working`; it does not submit or publish anything. No input dataset, internet, GPU, training, or non-standard package is required. Local evidence supports a stronger attempt than V54, but a ladder rating cannot be guaranteed because the live opponent mix and rating path vary.

Agent SHA256: `f09034624844da494669c4ab0e0d9a797da1a19db95eb138b875d309bd1aa01b`. Isolated normal-GC maximum callback on the tested Windows host: 45.350 ms.


[code cell 1: 5 lines]
```
from pathlib import Path
OUTPUT_ROOT = Path('/kaggle/working') if Path('/kaggle/working').exists() else Path.cwd()
WORKDIR = OUTPUT_ROOT / 'v55_agent'
WORKDIR.mkdir(parents=True, exist_ok=True)
print('Agent directory:', WORKDIR)

```

[code cell 2: 207 lines]
```
import base64, hashlib, zlib
EXPECTED_MAIN_SHA256 = 'f09034624844da494669c4ab0e0d9a797da1a19db95eb138b875d309bd1aa01b'
SOURCE_BLOB = ''.join((
    'c-q{(XM5txvM~DHzd{(BL-Y_07_h-)o1E>r0|+EQAS5h_Z2a4A2StL%Yp;Fo^S*cX>@^^|tE;Q4D|gFG)FpwG=<)V}Xo@r;O=yDQ#05Q+Xo{#X3)<zmCvw|?z)<A{%`x1V81kGX@GMIUcSMaQMUfeE1VgbjvF3#tEr<lQ6ktOLY{Uqn1U?BgO;F@kBqW|#up}ori8UBkAV`iPCZw>UK{K8M7|`<tFOb5PSWjqDB8CFLa6(WVA%Hf#fRThSIDq1U6s0A22EkA?%d7xM_&e%+M^r!`8UV+AmIIa<5=B}fSAJq4@YHfBF+7Jl&q;v0WSCrI!iWU;OG=W!43>~00=*PzC+fgRA|Zmd+!zcggBJOvFr>j_hGhwkrYVttC_$)z5OWfac1NTbksJVW@eBB!WC@yEF#yn<<|G$I12R+K6G3kPec;b5Ge87kd6I&36?rrrQW#DkaDbsmvm+Noon!z}?yk&4fgggN3vxIk$FR?wr<f5lL>P!p!t3_lyWC-y*L_En1qL($t(AE~k_fa0>y;dj1!lNp5v9fDV9tO=2aQ(YU%m%r?k!)KuqMEW6WZmyb2|x+mzW_f5(Ap$*EX<XOA+C{3KJ~31$+WP*AmHer9+GXD>%^?!irZ6Axew{eh#QfF9=WA>m(+;!0f<dznl047Yv|Hc)T_zkt{cB`E(6@NYrZO23nt7x|RYXkPAdl3d|0T4!#il2z&%&8!;>mCz$S3T%Mp0P?Bc>CSYMOr^`Gc(jQBj8{(b82msb#OKd0PHstvwPWXjO-~n?8fSw+YOJwE?u(mo%*iLDP2D}dvLx3nlfg$gR5-(xWN|4XUrNl#a0gK3PVgH1-HV*)K@S`Y+VEwrn%{padoL~ot(f|;U2Q0c2$W0LJ99j~W63H=60A(SpL}p83j!%KH1co89>~cr(t2;tN82}O(yar-KT}Xu|@QR+!YUT5QbwP6rfRPiEIcWP#1NlOfceLOn>huC^?*Z5^VZ?zDM4e`_u$j}t2|!bvKcGF|!)(>#1q$xP61@iG*EWZKN5LH+fHi_k13^|~hV*(p&%eNb{Yl+s|0OYVxV9{q2|1=8RGK(-^M_E>Z9#*v_&GBa@wVrHv=q>|5sf0t1rP-^IR{{eG$#ULjern2OC)bdC6fQAL`nk6jA`*fUR5YbU67HXJOq;<#!FJ5BF8IAEGAnKvJhYbVUFekcw@Mv;kKa21*AF<$15*btTiJ|h<iU+c-)o&G7QKwX1-)G8{8d{2QCPS#iv9rXiOZmSO6;86$_FPz!q9OoZl<%@G-@Y2^DZ+I{Cv7L>=@6eL}jGbP^&7b{b2QlvA7G5Qqg{o+kuaTXJB<fe4;JO$A7(jTyPTk<?v-Kme2>%fK1R!c
```

[code cell 3: 19 lines]
```
import ast, gzip, hashlib, io, tarfile
source_bytes = MAIN.read_bytes()
assert hashlib.sha256(source_bytes).hexdigest() == EXPECTED_MAIN_SHA256
assert [n.name for n in ast.parse(source_bytes).body if isinstance(n, ast.FunctionDef)][-1] == 'final_price_guard'
ARCHIVE = OUTPUT_ROOT / 'submission_competitive_v55.tar.gz'
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
print('No Kaggle competition submission was made.')

```