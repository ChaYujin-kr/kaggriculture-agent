"""Digest Kaggle's official daily top-episode dataset into one small CSV row per seat.

The raw daily dump (kaggle/kaggriculture-episodes-YYYY-MM-DD) unzips to ~20 GB of 30 MB replays.
Only the lineage-relevant bits are kept: team, seed, bank, and the action-stream hashes that
scripts/ladder_fingerprint.py and the community dataset use (sha256 over canonical JSON per action,
NUL between turns, 16 hex, turns counted from step 1).

usage: python scripts/official_eps_digest.py data/official_eps/2026-09-24 research/ladder/official_2026-09-24.csv
"""
import csv
import glob
import hashlib
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

CUTS = (24, 48, 100)


def digest(path):
    d = json.load(open(path, encoding="utf-8"))
    teams = eval(d["info"]["TeamNames"]) if isinstance(d["info"]["TeamNames"], str) else d["info"]["TeamNames"]
    steps, rows = d["steps"], []
    for seat in (0, 1):
        h, row = hashlib.sha256(), {"episode_id": d["info"]["EpisodeId"], "seat": seat, "team": teams[seat],
                                   "opp_team": teams[1 - seat], "seed": d["info"].get("seed"),
                                   "bank": d["rewards"][seat], "opp_bank": d["rewards"][1 - seat]}
        for t in range(1, len(steps)):
            h.update(json.dumps(steps[t][seat].get("action") or {}, sort_keys=True, separators=(",", ":")).encode())
            h.update(b"\0")
            if t in CUTS:
                row[f"h{t}"] = h.hexdigest()[:16]
        row["spend0"] = 3000.0 - steps[1][0]["observation"]["farms"][seat]["money"]
        rows.append(row)
    return rows


if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    files = sorted(glob.glob(os.path.join(src, "*.json")))
    with ProcessPoolExecutor(3) as ex, open(out, "w", newline="", encoding="utf-8") as f:
        w = None
        for i, rows in enumerate(ex.map(digest, files, chunksize=4)):
            if w is None:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                w.writeheader()
            w.writerows(rows)
            if i % 100 == 0:
                print(i, "/", len(files), flush=True)
    print("wrote", out)
