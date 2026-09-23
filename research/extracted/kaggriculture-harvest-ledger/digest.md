# V59 — Harvest Ledger — Protected Order Book

Keep V57 farming, seed caps and fertilizer guards. Port shiiin9's within-turn order-book evaluator but keep all purchase, hire and deliberate empty slots fixed. Search only permutations of existing cash-sale slots, excluding products bought in the same list. The rival is approximated as a mirror, not observed private inventory; predicted gains are not guaranteed actual gains. Also adopt the four published market settings (prediction interval 2, reservation horizon 44, slot margin 8 and carrot margin -15), without replacing V57 tomato expansion qualification.

This is a credited public-strategy refresh. V59 restricts within-turn sale reordering; V60 also ports the public investment gate and market settings. Neither adds the V58 sale-advance layer. Both share public ancestors. Local match results cannot predict Kaggle ratings.

Direct source: https://www.kaggle.com/code/shiiin9/your-market-list-is-an-order-book. Full author notices are retained in main.py and NOTICE.txt, with Apache-2.0 licensing. Public version numbering differs from this workspace.

Run both cells to create `submission.tar.gz` containing `main.py`, `LICENSE.txt` and `NOTICE.txt` at archive root. Standard-library CPU only; no network or GPU is required. No tests, replay data, credentials or automatic submission are included.


[code cell 1: 12 lines]
```
# Strategy: Keep V57 farming, seed caps and fertilizer guards. Port shiiin9's within-turn order-book evaluator but keep all purchase, hire and deliberate empty slots fixed. Search only permutations of existing cash-sale slots, excluding products bought in the same list. The rival is approximated as a mirror, not observed private inventory; predicted gains are not guaranteed actual gains. Also adopt the four published market settings (prediction interval 2, reservation horizon 44, slot margin 8 and carrot margin -15), without replacing V57 tomato expansion qualification.
from pathlib import Path
import base64
import zlib
import hashlib

FILES = {'LICENSE.txt': 'c-q}sTa(+i6@K@xKsD3p?hGwEY0@^%lj2=BY8~y)YF#&z$pb`!5^9oQ0CKhJukX3wMoGJNr*HLm5=$Zu4$kE}-#Oq5@wq>XUY0v0-s@6zPQ7^M$$u#8wCTjx^Vfy=o9squ58~_BufKV6(QX*}H?Lmp_xrh|ZRW;qUp2gyd-Vbr-e2GSv=)oim3Vuzx?0{ZZ&qvZ?&eN>SYH?7?)vub=IX;+{JNm0u9oZjyX6lb@Ea2F)m&VuT6cN?<=p&**JkEVG!t$on?|%sc4B~&4$8Jp$gUEl=_+0&YGcLdR3WVDt*OQmzb?Eee74eVuzEA%_d+^R;g+frn}b-Zl7)N)@~s)SJMo<`HGI(UoGHgvb;Ge<#-1ovn*Lz*b~gyK@01mw5-iliLCA5~8LR(I`*}I%Rt!5i2-tLMB`oZ=^pLkhrhwYYMqHEV6D7tD4@lZ8Axn}Hv;Z@}vtEpW2fTt>Io=u!I#|;bLRu9*G^BKar@?Q>u7YKyX<O5IN&Z2x*TatG@P>2o&REi;A8l_SVv<#(!-J1zUdoJ);>3l%<fUe>Yys}G;3ZT-cl_@{3`Ud^oQ}_VDf|;zz=~FOa;wmJxUU<_omZ?7`<<fWgZF7)NwRax>@`LcNV(9U3AxAZbdQp1U4u1yWlI!&@$Kv1U($94%)^Ecg2urOV0H8XxXCIPB!b9|>c9x423Jm`XL=@=|7^yYxPZ0zFFU);y$*lTCJ(wAQI-{Xe0Txs5wz6~6#>0l?HmO>#Th37x#c9(*05U%DG2G+9!FYlRjsUr<@9S!7XO4>w5HN<G)Y+%9IU&t8OaoogrYNpXmqP_ckrV#^{~hAa<m~hr2^}R+
```

[code cell 2: 18 lines]
```
# Strategy: package exactly the frozen agent and its licenses; no testing or submission calls.
from pathlib import Path
import gzip
import io
import tarfile

with Path('submission.tar.gz').open('wb') as raw:
    with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode='w') as archive:
            for filename in FILES:
                content = Path(filename).read_bytes()
                assert hashlib.sha256(content).hexdigest() == EXPECTED[filename]
                member = tarfile.TarInfo(filename)
                member.size = len(content)
                member.mode = 0o644
                member.mtime = 0
                archive.addfile(member, io.BytesIO(content))
print('Created submission.tar.gz')

```