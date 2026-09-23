"""Download top-episode replays from a daily dataset and tabulate who played, who won, and each
side's opening spend (bank at step 1 tells us which lineage they belong to).

usage: python scripts/scan_episodes.py --date 2026-09-22 --count 16 [--team DSM]
"""
import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KAGGLE = os.path.join(ROOT, ".venv", "Scripts", "kaggle.exe")
DEST = os.path.join(ROOT, "research", "episodes", "scan")


def env():
    e = dict(os.environ)
    for ln in open(os.path.join(ROOT, ".env"), encoding="utf-8-sig"):
        m = re.match(r"^(KAGGLE_\w+)=(.+)$", ln.strip())
        if m and m.group(2).strip():
            e[m.group(1)] = m.group(2).strip()
    return e


def run(args):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env())


def list_files(slug, want):
    names, token = [], None
    while len(names) < want:
        cmd = [KAGGLE, "datasets", "files", slug, "--page-size", "50", "-v"]
        if token:
            cmd += ["--page-token", token]
        out = run(cmd).stdout
        page = [ln.split(",")[0] for ln in out.splitlines() if re.match(r"^\d+\.json", ln)]
        if not page:
            break
        names += page
        m = re.search(r"Next Page Token = (\S+)", out)
        token = m.group(1) if m else None
        if not token:
            break
    return names[:want]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="2026-09-22")
    ap.add_argument("--count", type=int, default=16)
    ap.add_argument("--team")
    a = ap.parse_args()
    slug = f"kaggle/kaggriculture-episodes-{a.date}"
    os.makedirs(DEST, exist_ok=True)
    names = list_files(slug, a.count)
    print(f"{len(names)} files listed from {slug}", flush=True)
    rows = []
    for n in names:
        path = os.path.join(DEST, n)
        if not os.path.exists(path):
            r = run([KAGGLE, "datasets", "download", "-d", slug, "-f", n, "-p", DEST, "--force"])
            if not os.path.exists(path):
                print(f"  {n}: download failed {r.stderr.strip()[:80]}", flush=True)
                continue
        try:
            rep = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            print(f"  {n}: unreadable ({e})", flush=True)
            continue
        teams = rep["info"]["TeamNames"]
        steps = rep["steps"]
        final = [steps[-1][p].get("reward") or 0 for p in (0, 1)]
        spend = [3000.0 - steps[1][0]["observation"]["farms"][p]["money"] for p in (0, 1)]
        rows.append((n[:-5], teams, final, spend))
        os.remove(path)  # 33 MB each; keep the table, not the file
    print(f"\n{'episode':<10} {'winner':<26} {'spend':>6}  {'loser':<26} {'spend':>6}  margin")
    for ep, teams, final, spend in rows:
        w = 0 if final[0] >= final[1] else 1
        print(f"{ep:<10} {teams[w][:26]:<26} {spend[w]:6.0f}  {teams[1-w][:26]:<26} {spend[1-w]:6.0f}"
              f"  {abs(final[0] - final[1]):>8.0f}")
    if a.team:
        hits = [r for r in rows if any(a.team.lower() in t.lower() for t in r[1])]
        losses = [r for r in hits if (r[1][0].lower().find(a.team.lower()) >= 0) != (r[2][0] >= r[2][1])]
        print(f"\n{a.team}: {len(hits)} games, {len(losses)} losses")
        for ep, teams, final, spend in losses:
            w = 0 if final[0] >= final[1] else 1
            print(f"  lost to {teams[w]} (opening spend {spend[w]:.0f}) by {abs(final[0]-final[1]):.0f}")


if __name__ == "__main__":
    main()
