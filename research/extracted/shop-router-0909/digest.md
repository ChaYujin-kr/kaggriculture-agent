# Shop Router 0909 Python

1. At step 144, choose a plan using the first two revealed shops.
2. Insert DIG when weeds block planting or construction, delaying only that worker's remaining actions for the current day.
3. Bring eligible sales forward one turn and liquidate on the final turn. All routes share the ending from step 648.

The complete runtime code is shown below. Data files are stored separately from the implementation.

Sale timing is based on [aurax7 Reactive Router](https://www.kaggle.com/code/aurax7/kaggriculture-reactive-router). Shop-pair routing and same-day worker queues were added in this research.

[code cell 1: %%writefile main.py, 233 lines]

## Load the data

Restore the submission data, including the 13 complete, 719-turn plans.

[code cell 3: 9 lines]
```
import base64
import gzip
import json
from pathlib import Path

data_payload = 'H4sIAAAAAAAC/+y9W48cW5Kd+VeIfiYGzIjMJDlvvIROEcVzkkiSCtR0CweNGQ3mArUASW/C/Pfh6aruYmZ4ZLq52bdsbQ9/UbVYUZ5+sW3bttm6/M9/+Of//X/83//1X/77//L//Pf/+i//8L+++Id//Kd/efHiX/+fFy/+51//48WLf/qH//Of/9t/+c//7Z9+/OIf/+0f//jnL+++fv2nf/i3f/lPL//+P/i//vlf/o///q+///lf/8s//7f/9z//j0eX+en//OM377//5fcv93cfv3/49k//8PLhf3f80+Hd43+92v/9//efXp697NfD58+V10vd5r+/sb/+H//fy7kv/Le7+29/qn7j3a/mZtZV//Tp/vD3J1/NT/94We9++/Tru9NP8OHu+OjfdtlLfv3T4fDliYsuDsyvd9+fD8yzd/zl04c/f/8y/QJmPfLDRPTkTx8tobLfznyGqTf00yINv/iJP/vvn3nh1wg9df+Lf//90+ePv/+4kW/fH606ybv+W0Zb+K7P37x3sH9+9+Egj/VZu1/ynuWv/Xj4+m3mTz+8gwP84b2MlzYC7/JMun6UOZ9/x0/uwl8Ph48nf+LXw+e734g9+Ewu8fiMP1bfb9/OvQvVFaa/+aMMrvrmVxXf/DSpZXf/gtc8PyqO774d7onfPk4E1ZnyP/zrV174iiNPEnmZ87OfpL4yWiYPd87o5wrsKsqEGLmvydpn5M0uVarY5rj8jT1MTKPtZY8e/uTRh0u0kTuIlvfxTzfZ1CtZjQ8fM/iZHjWP2Ax7Wu3VfOhgxeH08TKplNkc8zkz9ZklOXPvmTO1eyOTSec+w6UkWGgf1CbYk2cY5+vNmZNuGdbzoJH6dtJk2nwmKZ+2pBYNlPGgvvWW25q+Uj61nX5nybdzzW2RV+ea28IDgUvLbamvYfUu299P5qc++IZoqhPBrlicnXoQE95pxE31udPVl+QlvCd/kc990slvfOjU/CzwICct8M5nvvv8+fDh2+//4XD/7dPnT/9bov8SeKyn/qoJDC6H9Vz8gNMzzPBl6ur1Sdz0z/dz9rBVh50uaSIf3iXSfmR4k8JyZY5VIaQ+hcspSCTYGhB8h9hyMTjfzq/Ml6B4a3s++gAXvdpcehn1rBl56i2QVGeL9cRX4IT6sDjYoit/WFtNR2xxKT94bad6ve+4YmINXdb1pOOtn167B20fevvQ24ceakKmnGX99G/XAimFZEvQT81gceWUmp0Y0J75iiM1aOnnisHNdQwIUzjr6f8I+GQsycPvf0H4jqtKdBmCykWkOYpfjEdQT0Y6qb8HyUg54MolxJNj6QXS6y4vIw0EhzEIJ3y9JQXRoICa/4b+9O7+P45LaVVlu8B+OQIs3TEJTgXiOpk0PRk2RL7Xs2W0YLaLKAWfw6bNb492
```

## Build the submission

Package the verified files.

[code cell 5: 19 lines]
```
import hashlib
import io
import json
import tarfile

expected_hashes = {'main.py': 'd6d74997dc5b483db63d8e39cafa1afeec0f366824e75107e109123f111e866b', 'actions.json': '17d503f2fd20d59f9c0f14024d1e74a8add8bb9b5561d4d908b45deecb5495ef', 'LICENSE.txt': 'cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30'}
archive_data = io.BytesIO()
with tarfile.open(fileobj=archive_data, mode="w") as archive:
    for name, expected in expected_hashes.items():
        data = Path(name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected, name
        member = tarfile.TarInfo(name)
        member.size, member.mode, member.mtime = len(data), 0o644, 0
        archive.addfile(member, io.BytesIO(data))
submission = gzip.compress(archive_data.getvalue(), mtime=0)
Path("submission.tar.gz").write_bytes(submission)
manifest = {"members": expected_hashes, "archive_sha256": hashlib.sha256(submission).hexdigest()}
Path("submission-manifest.json").write_text(json.dumps(manifest, indent=2))
print("submission.tar.gz:", len(submission), "bytes")
```