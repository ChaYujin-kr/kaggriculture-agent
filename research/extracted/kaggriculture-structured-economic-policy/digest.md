# Kaggriculture research candidate B

B keeps the same complete V36 parent program and no-op-slot adapter as A. An additional admission model can decline the initial day-12 six-sheep capital project under explicit feed-cost and competing-supply stress scenarios. The parent continues to govern its already-started feeding, care, harvesting and delivery.

Both alternatives use the same cached information cutoff, **2026-09-12T09:00:00Z**. A is not claimed to be today's strongest policy. B is an unverified hypothesis about adoption of a public sheep strategy, not an established improvement. The existing fixed0 policy remains a required reference for a later benchmark.

The notebook builds exact submission bytes and makes one action call on a saved initial observation. It runs **zero games**. This establishes a small execution check; it does not establish project-branch coverage, counterfactual reachability, score, future advantage, or release eligibility. A paired current-population, response-scenario and genuinely later-generation comparison remains pending.

Market no-ops preserve the original interleaved order positions. The narrowly scoped slot profile accepts only exact `['SELL', 'WHEAT', 0]` placeholders; every other order and all field commands use the repository's canonical strict validator. The receipt reports canonical strict and scoped-profile results separately. A future benchmark must explicitly declare this profile.


## Source and assumptions

Upstream: **Ahmed Berat Özer**, [Kaggriculture V36 Guarded Four Turn Sales](https://www.kaggle.com/code/ahmedberatozer/kaggriculture-v36-guarded-four-turn-sales), observed public notebook version 1, acquired 2026-09-12. The packaged unmodified `upstream.py` SHA-256 is `7eb5ab6c48581c82906ab6fa6b2cc5c9607513249ef59b2c45fcd6176e8653dd`. The archive preserves the source license and attribution notices. Inherited replay-level route lineage is incomplete; this notebook does not claim to have reconstructed every original route author or seam.

B's gate uses observable herd, inventory, shop and parent-program information. Its forward prices and competing-adoption cases are stress assumptions, not observed future weights or guaranteed profit bounds. Future shops, hidden storage, realised execution and opportunity costs remain uncertain. Consult the packaged configuration and module for the exact model. The notebook's initial observation does not exercise B's day-12 gate.

The engine, schema and official Python loader are pinned to Kaggle Environments 1.32.7 and checked by content hash. Both notebook directories are alternatives for the same configured public destination; creating them does not push either version or submit to the competition.


[code cell 2: 8 lines]
```
import importlib.metadata, subprocess, sys
try:
    installed = importlib.metadata.version("kaggle-environments")
except importlib.metadata.PackageNotFoundError:
    installed = None
if installed != "1.32.7":
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "kaggle-environments==1.32.7"],
                   check=True, capture_output=True, text=True)

```

[code cell 3: 45 lines]
```
import base64, hashlib, io, json, tarfile, tempfile
from pathlib import Path, PurePosixPath
def verify_archive(payload: bytes, expected_archive_hash: str, expected_files: dict[str, str]) -> dict[str, bytes]:
    """Validate the complete member set and bytes before extracting anything."""
    if hashlib.sha256(payload).hexdigest() != expected_archive_hash:
        raise ValueError("archive SHA-256 mismatch")
    files = {}
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
        for member in archive.getmembers():
            parts = PurePosixPath(member.name)
            if (not member.isfile() or parts.is_absolute() or ".." in parts.parts
                    or str(parts) != member.name or "\\" in member.name or member.name in files):
                raise ValueError("unsafe or duplicate archive member")
            if member.name not in expected_files:
                raise ValueError("unexpected archive member")
            handle = archive.extractfile(member)
            if handle is None:
                raise ValueError("unreadable archive member")
            data = handle.read()
            if hashlib.sha256(data).hexdigest() != expected_files[member.name]:
                raise ValueError("archive member SHA-256 mismatch")
            files[member.name] = data
    if set(files) != set(expected_files):
        raise ValueError("missing archive member")
    return files


ARM = 'B'
EXPECTED_FILES = {'NOTICE.txt': 'bdf3ce2bb14da2c07cba307966b9
```

[code cell 4: 28 lines]
```
smoke_path = work / "smoke_receipt.json"
completed = subprocess.run(
    [sys.executable, "-I", str(work / "_candidate_smoke.py"), str(runtime),
     str(work / "smoke_fixture.json"), str(smoke_path)],
    cwd=runtime, capture_output=True, text=True, timeout=60,
)
if completed.returncode:
    raise RuntimeError("Isolated initial-observation smoke failed: " + completed.stderr[-4000:])
smoke = json.loads(smoke_path.read_text())
if smoke["observation_calls"] != 1 or smoke["full_games"] != 0:
    raise RuntimeError("unexpected smoke execution scope")
if smoke["entrypoint_sha256"] != EXPECTED_FILES["main.py"]:
    raise RuntimeError("executed entrypoint differs from prepared source")
actual_files = {path.relative_to(runtime).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in runtime.rglob("*") if path.is_file()
                and "__pycache__" not in path.parts and path.suffix != ".pyc"}
if actual_files != EXPECTED_FILES:
    raise RuntimeError("runtime tree changed during the smoke call")
if hashlib.sha256((work / "submission.tar.gz").read_bytes()).hexdigest() != EXPECTED_ARCHIVE_SHA256:
    raise RuntimeError("output archive differs from prepared bytes")
receipt = {"artifact_type": "candidate_notebook_execution_receipt", "arm": ARM,
           "archive_sha256": EXPECTED_ARCHIVE_SHA256, "runtime_files": actual_files,
           "smoke": smoke, "status": "PASS_INITIAL_OBSERVATION_ONLY", "full_games": 0,
           "promotion_status": "UNVERIFIED
```