# Kaggriculture: 7-Turn Rescue | Historical LB 2800+

The title records the earlier agent’s historical leaderboard result. Version 2 refreshes the full-game controller after the original lost all 16 local games against four September 22 controls.

The final seven turns still use a short simulation to recover harvests and deliver goods before liquidation. The planner evaluates up to 128 simulations with eight proposals per actor and abandons an unsafe shadow plan. Earlier turns now use an order-book market controller with updated crop and livestock routes. Harvest-aware fertilizer checks preserve unnecessary inputs, while a late seed budget limits purchases to remaining planned planting demand. This is a full controller refresh, not an isolated endgame patch.


## Reproducible local evaluation — September 22, 2026

| Responding opponent | Wins | Losses | Ties | Mean money margin |
|---|---:|---:|---:|---:|
| Order Book v2 | 10 | 0 | 0 | +143.6 |
| V56 | 10 | 0 | 0 | +1016.6 |
| V47 | 10 | 0 | 0 | +3615.0 |
| More Wheat v7 | 10 | 0 | 0 | +127.8 |
| Original Rescue v1 | 10 | 0 | 0 | +11392.3 |

Five previously unused worlds, both seats, and frozen executable opponents were used for each row. The complete confirmation comprised 145 games including matched original and modern-controller controls. Selection used outcomes and relative final money; financing, execution ledgers and runtime were checked separately. The seed-budget variant was chosen on separate development worlds.

Order Book and V56 were updated within the preceding 48 hours; V47 is an older strong control. These policies share ancestry, and five worlds give limited coverage. Local wins do not establish a new leaderboard rating.

Run all cells to build `submission.tar.gz` and reproduce one complete confirmation game against More Wheat v7. Engine and agent bytes are pinned; code is collapsed by default.


## Credits

The production and order-book controller builds on [shiiin9’s Order Book](https://www.kaggle.com/code/shiiin9/your-market-list-is-an-order-book), Ahmed Berat Özer’s V55 and [V56 input rules](https://www.kaggle.com/code/ahmedberatozer/kaggriculture-v56-smarter-seeds-and-fertilizer), and [Thomas Tschinkel’s Metav4](https://www.kaggle.com/code/thomastschinkel/the-metav4-farm-submission-v13). The seven-turn rescue originates with Dmitrii Gluzdov’s earlier implementation; upstream ShopRouter work is credited to Hayashi. Original notices and Apache-2.0 licensing are retained in the distributed source and archive.


[code cell 3: 4 lines]
```
EVALUATION_MANIFEST = {'candidate_source_sha256': '0565e742904024379315cfc4d3228616a214c7939d0c7804f494bc4e3d4700c7', 'opponent_source_sha256': '3ad1863592a8f199cea93aabccce57e61814d280638e29ad72860ec26e3bce5f', 'engine_distribution': '1.32.7', 'demo_seed': 29463300, 'demo_candidate_seat': 0, 'demo_rewards': [64921.0, 64761.0], 'demo_action_hash_sequence_sha256': ['5e1a855dd10d0d75c5b5e1edb800ea62556f125826677a172b5578a8f9324359', '6cf56ed08813a4b22fecd11d4bae01367eb9a6f8282afd3b79eab7bc1b648e40']}
LOCAL_EVALUATION = {'date': '2026-09-22', 'development_worlds': [29463200, 29463201, 29463202, 29463203, 29463204], 'confirmation_worlds': [29463300, 29463301, 29463302, 29463303, 29463304], 'cohorts': {'Order Book v2': {'games': 10, 'wins': 10, 'losses': 0, 'ties': 0, 'mean_margin': 143.6, 'worst_margin': 2.0, 'paired_margin_delta': 126.6, 'paired_point_delta': 0.1, 'versus_original_margin_delta': 11411.9}, 'V56': {'games': 10, 'wins': 10, 'losses': 0, 'ties': 0, 'mean_margin': 1016.6, 'worst_margin': 69.0, 'paired_margin_delta': 128.0, 'paired_point_delta': 0.0, 'versus_original_margin_delta': 11842.1}, 'V47': {'games': 10, 'wins': 10, 'losses': 0, 'ties': 0, 'mean_margin': 3615.0, 'worst_margin': 2086.0, 'paired_margin_delta': 128.0, 'paired_point_delta': 0.0, 'versus_original_margin_delta': 13151.9}, 'More Wheat v7': {'games': 10, 'wins': 10, 'losses': 0, 'ties': 0, 'mean_margin': 127.8, 'worst_margin': 2.0, 'paired_margin_delta': 126.6, 'paired_point_delta': 0.3, 'versus_origi
```

[code cell 4: 38 lines]
```
from pathlib import Path
import ast, base64, gzip, hashlib, io, tarfile, tempfile

WORK = Path.cwd()
ARCHIVE = WORK / "submission.tar.gz"
ARCHIVE_BYTES = base64.b64decode('H4sIAAAAAAACCuy9eUPqTpMwOn/7KaKoAwLKJouAgiyKIiCguNwjBAgQWYJJ2ET97Leru5N0WNRz9Jk7997XeeZ3FDrV3dW1V3Ulm0mkcqXUvjpV/+s/9eNCP36fD/+Lfhb+9fjdXr/2Gf084Ef/cK7/+h/4GSkqL6Mp/+v/nz8b3Fc/8SHf6AhcVmwIA0X4bPytICuiNOA8+y4Hd8EPRrw84zwul2/tQx1VHR4dHEwmk30eT7Mvye2DHplKOdiAB8up4lWJi+eSXCKfS2bKmXyuxKXzRe6mlHJwxVShmE/eJOBjBx6VzJTKxczpDXyCAbj3uaTQEgeiihan7G/Q1WzRHW1xSofv9bi+wA84Fe1UFeS+wvGDJteQBk3yFNeSZG6kCA5OFoay1Bw14GMHBQVjm6KiymJ9BJ9zvMI1YUqhydVnXEloECBuBF+WRu0OF+KkFvpDROOkxqgvDNTFdUny0sIa0nAmi+2OykmTgSBzaEnoQVGdcfxI7Uiy+Irno3BWPaF2eJVDk7ZlHj04aONBFA/MAoQ23+NSGPTSIkYD2CBevcDxDQxFWwVCAxpLwUhoAF2gKChkaoRQVZZ6Do6XBe2PHl60A3YDn44GTfRYQ+r3pQGFRAdyE1HtEDhkwn0uLcl4HcORPJQQxRhY1Q9cO6MtCmULb0XhrKKNPCpNBNmBjk9GpwSLEAfkdwenSlyDR4cO4ygU8hXGgMz1+QHfFuDwYF5l1OjQhTm4SUfA20enj+flMWwWMxMRqAlBsYpoJfh4lI44BEgtsYWwORTkBoC2Hrp2bHg6CaGHIF4DNFKR9ELrRWeAjkkWFA0iAlkXBggJDREdpQk6s07jyO+l0RZnRc/Cb/KWjT119D/AyVhsjgCWzLH0QQEIU7RaUYGFoHX3RUXBBI/pjDABPpYlUiuh2RqIBRF79RcpbSgLLUGW0eP42xbGeBem6EtNEW2Nx1ylHbA4aPRGGBWICbmBpHI9sS/C7OgcFamlToC8FDwhOpQmwr7GexgQBUMGODT+b4ntkYy/R8fSExjxka8/I1JYXjo/mJHP0HGMepg/WrLUR182OvwArVpjEEQVAwVG8hpB4U969M8Wx3MEPRicw7xBCmNhm4hthiIwlIQXR7fZRpSA9oA+Nm2YlV5op2MivRWAQ3i3LzRFnlNnQ3bbFUnuLgmFCfoQrxjLIaA0gwXEgbYNnQEI6ui2+nwTCZIxL/b4ek/jf0YuOUCaAgE2eEpKvC4XNOmG0IAG6+KNYAoNFjFaeVUF3YIxpK2WgrCiDQhTvj9EM6MHkWhHZE4ehJHx4VBAM08RM/Wkic3AQlKQ
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
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 29463300})
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