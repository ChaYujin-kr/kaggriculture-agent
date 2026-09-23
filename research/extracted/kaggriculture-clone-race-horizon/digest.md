[code cell 0: 5 lines]
```
from pathlib import Path
OUTPUT_ROOT = Path('/kaggle/working') if Path('/kaggle/working').exists() else Path.cwd()
WORKDIR = OUTPUT_ROOT 
WORKDIR.mkdir(parents=True, exist_ok=True)
print('Agent directory:', WORKDIR)

```

[code cell 1: 109 lines]
```
import base64, hashlib, zlib
EXPECTED_MAIN_SHA256 = '0070f9e125902d690995acbbb0df1e3f46185a560771c0843d074f315345c778'
SOURCE_BLOB = ''.join((
    'c-q{(=X&Bw(<u7iS0RkeOE4aCFkpkpHaXjK1`tSqKuA~;+4$N|2StL%>s{Y>p1sekFd(|CtE;OkcgsxFC4rRa@%Dje`GW+#k!X$*!RNq#L}JMD9PK36q(BpMQkc;aA<!Z%tVoIBIby;K%ntlL68Jgca}yGOWhQ(fLRt!(cuzDYGywpNX+dqdCPhM|S$ZhZ6al_3NJgM3r%00$LD3Q|%o&amC1yxSv?z%H962T#PLv1<00ZOfXb$2=i2PC*(uCFPA=bRWQsNyE@DXEjPK!2z<S2rr$rUXUOHQC!Fh2@_;ui}r9ZnMA$PgYtYRqsX3;IEP7Cg%gxA#PXWr>Br@B$(5ONrseci<~eEr)Q@cMvB@5}3gfeMN(TDUF;%o|6Es5D+<>kpS|TfP`CMlF`&X=vv^1U_7nCoTr!(Geq<RbMUx40jDeM^tkVdvVxs%I6!_p288uWj>iHsT(W@PG$Aerb4C<lqgD8q_kma}2Vg!#%Nr)F2{7V>c6#nzcLc`+`U27nXqI2why}Y85j9p}f+e@K0I6O}B-51+qRSonLRj?+j}}~%=mp^pd+yZL^|^>&kWT>Ggxh1gBa-E2EuXG|4~bf>+(5L-rE4ij!^HwH8Xy*l*A{#s_!0QXh{T9tX*j`jr{Z)6y#yoja1Fr%(i|chW<`<ySkfHe0>B^($VbFrOKd0PHst;#PWXirE*~ubdb-_Ck(n=8T2BevDGkwpfgmvih%yuy@}4O15+<z#S%h3l{2b5#EF!yw{S(^SJOJdukAQ856Na17?469v9bj!y8UO<FfL)dXxe49@{+7h0L~;ydsD-c+nJvj70;RxM0>cnlcDbYY72rn|WdKNE@EV8_bs-g=z$<z>tCiOc)&<SY4@OQ*=Ai8}4YoZ|-qFGxQKuIYJs*I58b%xlLDZF9I;V#dfTlQqAcg|J=wY_%@dCgFkcVCa@>4WgOim)eCKxfo9J2`nar;=prGX$TGDCVi?&n|N|GuPdU;UDpIb2&7%!C}%4=PRWbn}N$)NMh7vG_SN6cN=J4hS&;jT_M@vRsIgK$CL-c1Uv~Al8Uy&lAZLQi<gIDUp(ZGGkhNkXMzU$gLAHvMBKam;^Cik^&VuUQuE(*@}>b2rTfx2f!P{B@MR)MJ^!KB_3b|7HiE&6DZk?!Vxg@lErLre?%U*AS9wFA(0Cj69+98fQohnl(}FFEgsJA6<7F};>U#Y-(foW!Vg3p^aXuFdI?F0B-m*{08@9`42M80@bWw%(Ats%D^3%Dxq#3DB-F-?T;53Pu0bHMbVf6jg`GTeuyx5x(+k}xdPG~%(4D%Z;NQRg!Ke}i%v0a@XaRu=Q9`2kh2#K7Y{6hI-#6VRlC*gE^=rLe-;-#ldt
```

[code cell 2: 18 lines]
```
import ast, gzip, hashlib, io, tarfile
source_bytes = MAIN.read_bytes()
assert hashlib.sha256(source_bytes).hexdigest() == EXPECTED_MAIN_SHA256
assert [n.name for n in ast.parse(source_bytes).body if isinstance(n, ast.FunctionDef)][-1] == 'e410_agent'
ARCHIVE = OUTPUT_ROOT / 'submission.tar.gz'
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

```