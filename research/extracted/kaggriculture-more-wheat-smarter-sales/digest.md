# Kaggriculture: More Wheat, Smarter Sales

A farming agent built on an order-book market policy and the Metav4 production controller. It coordinates crops, animal care, deliveries and the order in which goods reach the market.

The added rule preserves fertilizer when a wheat or carrot crop already has sufficient coverage, or when another application would not increase its planned harvest. Sequential worker actions are simulated before deciding; uncertain reactive-worker plans keep their fertilizer. Saved inputs remain available for later crops.


## Run and local evaluation

Run all cells to create `submission.tar.gz` and replay a complete game against the source policy. The engine and agent bytes are pinned. Code is collapsed by default.

On September 22, 2026, the added rule won 9 of 10 exploratory games against its source policy. An untouched confirmation used five new worlds and both seats: 9 wins, 1 loss and 0 ties against that source, with a mean final-money margin of +266.2. Matched source-versus-candidate checks also used two frozen responding controls. All 55 confirmation games completed normally. The opponents share ancestry and the sample is small; these local results do not establish broad leaderboard strength. The replay below is one reproducible illustration from that confirmation.

Retaining fertilizer can increase storage pressure: one confirmation world lost an extra carrot to shed overflow, reducing the relative margin by up to 43 coins.


## Credits

Based on [shiiin9's Your Market List Is an Order Book](https://www.kaggle.com/code/shiiin9/your-market-list-is-an-order-book),
which extends Ahmed Berat Özer's V55 and [Thomas Tschinkel's Metav4 controller](https://www.kaggle.com/code/thomastschinkel/the-metav4-farm-submission-v13).
The harvest-aware fertilizer rule is adapted from [Ahmed Berat Özer's V56](https://www.kaggle.com/code/ahmedberatozer/kaggriculture-v56-smarter-seeds-and-fertilizer).  Original author notices and Apache-2.0 license information are preserved in the archive.


[code cell 3: 5 lines]
```
EVALUATION_MANIFEST = {'candidate_source_sha256': '3ad1863592a8f199cea93aabccce57e61814d280638e29ad72860ec26e3bce5f', 'opponent_source_sha256': 'a16e0e9b40c489972630a0b9d04f30e9c1cab03159fa78676db74277d84d82ab', 'engine_distribution': '1.32.7', 'demo_seed': 29462300, 'demo_candidate_seat': 0, 'demo_rewards': [141946.0, 141472.0], 'demo_action_hash_sequence_sha256': ['42836ec8d2c4acaa1ac76d182be2614c8f429cc0f76c08e5eb28a7a7c86097e5', '6c2565edf4d26dba8b176814a8059669407c12a89e78a32de3c545b008368335']}
LOCAL_EVALUATION = {'date': '2026-09-22', 'development_worlds': [29462200, 29462201, 29462202, 29462203, 29462204], 'confirmation_worlds': [29462300, 29462301, 29462302, 29462303, 29462304], 'cohorts': {'Previous': {'games': 10, 'wins': 10, 'losses': 0, 'ties': 0, 'mean_margin': 767.8, 'worst_margin': 338.0, 'point_delta': 0.0, 'margin_delta': 257.2, 'worst_margin_delta': -37.0, 'own_cash_delta': 153.6}, 'V56': {'games': 10, 'wins': 10, 'losses': 0, 'ties': 0, 'mean_margin': 368.6, 'worst_margin': 168.0, 'point_delta': 0.2, 'margin_delta': 271.4, 'worst_margin_delta': -38.0, 'own_cash_delta': 185.0}, 'OrderBook': {'games': 10, 'wins': 9, 'losses': 1, 'ties': 0, 'mean_margin': 266.2, 'worst_margin': -123.0, 'point_delta': 0.4, 'margin_delta': 266.2, 'worst_margin_delta': -43.0, 'own_cash_delta': 144.2}}, 'source_versions': [{'ref': 'shiiin9/your-market-list-is-an-order-book', 'notebook_sha256': 'bcd3503d92b1685b8bbf0ea04f4430334693cde716aaf151b92b1d6dc1f3a468', 'version': 2}, {'re
```

[code cell 4: 38 lines]
```
from pathlib import Path
import ast, base64, gzip, hashlib, io, tarfile, tempfile

WORK = Path.cwd()
ARCHIVE = WORK / "submission.tar.gz"
ARCHIVE_BYTES = base64.b64decode('H4sIAAAAAAACCuy9+V/iTpcwOj/7VwRRhtVmXwQUZFcEZBG0bwsBAoQlwSTs4t9+a8lSYVG79ZnPe+87zneehlB1qurUqbOfSj6XSBUqqQtpKf3Xf+rPCf78Xi/6F/zt/Ov2uzx+5Zn8POAH/1DO//of+JuJEi2AIf/r/86/E+qzv/iU7gwYKs92GE5kPmr/yAgiy3OU+8Jpp25pbkYLK8rtdHqPdhpI0vTy16/FYnFBo2EueKH/a4yHEn+dwI7VVPm+QsULSSpRLCRz1VyxUKHSxTJVq6TsVDlVKheTtQR8bEetkrlKtZy7qcEnCIDrgkoyPZZjJTA58eJEns2pvKJTShzQ4zE1YWiOksBKJUaYiBTNdakOz3VxL6rHC9RMZOyUwEwFvjvrwMd2GRRs22VFSWDbM/icokWqC4dkulR7RVWYDgbiAvAFftYfUCGK74EvLGjHd2YThpN258ULexPr8NOVwPYHEsUvOEagwJRAR1ZaUfRMGvACu0bjyXAO9ZAGtESBQfsCDTpyfdRIxgMxAaZPj6kUAr03iRkHF4hmz1B0B0FRZgHQANrKYHjQQJ4gy4h4aIBQSeDHdooWGOXLGE3aDlcDn864LujW4ScTnpMhyQ2pBSsNMBw84AWV5gU0j+lMmPKAYjSsqhuu7NGpDOUULUWkzKwFd+UXjGAH2yeAXYKTYDn82U5JPNWhwabDdjIU/BPCgEBNaI7uM3Dz4LjirDOQJ2anFgMGLR/sPhqXRrBJzCxYSE0AipkFM0HbIw7YKYTUY3sAm1NG6EDQZp/z3IKG4wF6MOIVQDMJcC8wX7AHYJsERlQgApBthgNI6LBgK3XQiXlqW/7Ez04pM+gLPwmnFnLXwX8QJ3O2O4OwBIqkDxkAswSzZUU4ETDvCSuKiOARneFDgLZlj9QqYLQOOILgeE12KW0qMD1GEEB39GsPYXwEh5jwXRYsjUanStlgluuMZwgV4BBSHC9RY3bCwtHBPop8T1pA8hLRgGBTugD7ytlDgGQwuIFdOf89tj8T0O9gW8YMwT6K7SEghf2p09wKPwPbMRuj89ET+An4sTOgOTBr5YAAquBE2JJWCAo9GctfexRNYfQgcHb9AmUYO8sEx2bKwgPFo8nJy+wDSgBrAI91Cya5F1jpHHNvEcLBZ3fCdFmaklZTctl1XhjtMYUFeIhmjPgQpDTtCLCcsgz1AGDUycua0F3ASOY0O6bbY+X8E3zJDrkpJMAOLZMSrfIFhbsBNIDGKnvDmAKNWYRWWpKgbEEYUmYrgzCDBTBLejIFI4OOgLUDMscdYcv4dMqAkZfgMI35hUXDQpIR
```

[code cell 5: 77 lines]
```
import base64, contextlib, hashlib, importlib.metadata, importlib.util, io, json, os, sys
from pathlib import Path

ENGINE_SOURCE = base64.b64decode("aW1wb3J0IGpzb24KaW1wb3J0IG1hdGgKaW1wb3J0IHJhbmRvbQpmcm9tIG9zIGltcG9ydCBwYXRoCgpmcm9tIGthZ2dsZV9lbnZpcm9ubWVudHMudXRpbHMgaW1wb3J0IHJlc29sdmVfZXBpc29kZV9zZWVkCgpkaXJwYXRoID0gcGF0aC5kaXJuYW1lKF9fZmlsZV9fKQoKCkNST1BTID0gewogICAgIldIRUFUIjogICAgICB7InNlZWQiOiAxMCwgImZpcnN0X3lpZWxkX2RheSI6IDIsICJtYXhfeWllbGRfZGF5IjogNCwgImludGVydmFsIjogMCwgIm1heF95aWVsZCI6IDYsICJvbmdvaW5nIjogRmFsc2V9LAogICAgIkNBUlJPVCI6ICAgICB7InNlZWQiOiAyMCwgImZpcnN0X3lpZWxkX2RheSI6IDIsICJtYXhfeWllbGRfZGF5IjogMywgImludGVydmFsIjogMCwgIm1heF95aWVsZCI6IDQsICJvbmdvaW5nIjogRmFsc2V9LAogICAgIlRPTUFUTyI6ICAgICB7InNlZWQiOiA1MCwgImZpcnN0X3lpZWxkX2RheSI6IDgsICJtYXhfeWllbGRfZGF5IjogOCwgImludGVydmFsIjogMSwgIm1heF95aWVsZCI6IDQsICJvbmdvaW5nIjogVHJ1ZX0sCiAgICAiU1RSQVdCRVJSWSI6IHsic2VlZCI6IDEwMCwgImZpcnN0X3lpZWxkX2RheSI6IDEwLCAibWF4X3lpZWxkX2RheSI6IDEwLCAiaW50ZXJ2YWwiOiAyLCAibWF4X3lpZWxkIjogNCwgIm9uZ29pbmciOiBUcnVlfSwKICAgICJNRUxPTiI6ICAgICAgeyJzZWVkIjogODAsICJmaXJzdF95aWVsZF9kYXkiOiAxMCwgIm1heF95aWVsZF9kYXkiOiAxMiwgImludGVydmFsIjogMCwgIm1heF95aWVsZCI6IDYsICJvbmdvaW5nIjogRmFsc2V9LAp9CgpBTklNQUxTID0gewogICAgIkdPT1NFIjogeyJjb3N0IjogMzAwLCAic3RydWN0dXJlIjogIkNPT1AiLCAgICAiZmlyc3RfeWllbGRfZGF5IjogNCwgImludGVydmFsIjogMSwgIm1heF9oZWxkIjogNCwgInByb2R1Y3QiOiAiRUdHIn0sCiAgICAiQ09XIjogICB7ImNvc3QiOiA0MDAsICJzdHJ1Y3R1cmUiOiAiUEFTVFVSRSIsICJmaXJzdF95aWVsZF9kYXkiOiA4LCAiaW50ZXJ2YWwiOiAyLCAibWF4X2
```

[code cell 6: 43 lines]
```
import contextlib, hashlib, io, json, os, sys
from contextlib import contextmanager

@contextmanager
def silence_native_output():
    sys.stdout.flush()
    sys.stderr.flush()
    saved_out, saved_err = os.dup(1), os.dup(2)
    sink = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(sink, 1)
        os.dup2(sink, 2)
        yield
    finally:
        os.dup2(saved_out, 1)
        os.dup2(saved_err, 2)
        os.close(saved_out)
        os.close(saved_err)
        os.close(sink)

with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()), silence_native_output():
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 29462300})
    steps = env.run([str(MAIN), str(CONTROL)])
assert len(steps) == 720
final = steps[-1]
statuses = [agent["status"] for agent in final]
rewards = [agent["reward"] for agent in final]
callbacks_per_agent = [sum(state[i].get("action") is not None for state in steps[1:]) for i in range(2)]
actions = [[row[i].get("action") for row in steps[1:]] for i in range(2)]
def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
actions_sha256 = [digest([digest(action) for action in seat]) for seat in actions]
assert statuses == ["DONE", "DONE"]
assert callbacks_per_agent == [719, 719]
assert all(isinstance(value, (int, float)) for value in rewards)
assert actions_sha256 == EXPECTED_ACTIONS_SHA256, "Pinned full-game action stream mismatch
```