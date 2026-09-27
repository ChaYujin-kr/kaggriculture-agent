"""Re-download public agents at their latest version and keep the ones that are new or changed.

ladder_fetch_pool.py never re-downloads a kernel it already has, so research/ladder_pool/ holds the
version current on the day of the first fetch. On 2026-09-27 the a-wonderful-life / cha22 lineage
(same 48-turn opening as our local copies) beat the Shepherd's Ledger in 72% of 93 ladder games while
our local copies of it lost almost every game: the ladder runs newer versions. This script collects
kernel refs (keyword search, most recently run first, plus refs already known), downloads each
kernel's current output into research/outputs_fresh/, and copies the agent to
research/ladder_pool_fresh/ when it is new or its content differs from research/ladder_pool/.

usage: python scripts/refresh_public_agents.py [--pages 6]
"""
import argparse
import hashlib
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import daily_refresh as dr  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL = os.path.join(ROOT, "research", "ladder_pool")
FRESH = os.path.join(ROOT, "research", "ladder_pool_fresh")
OUTPUTS = os.path.join(ROOT, "research", "outputs_fresh")
KNOWN = os.path.join(ROOT, "research", "ladder", "public_kernels.txt")
TOPICAL = re.compile(r"kaggricult|farm|harvest|wheat|sheep|shepherd|herd|ledger|crop|agri|metav|hybrid|"
                     r"orchard|barn|pasture|yarn|order-book|v5\d|k0013|wonderful|cha22|autonomous", re.I)
QUERIES = ("kaggriculture", "wonderful life", "cha22", "herd-safe", "shepherd", "farm agent", "autonomous farming")


def sha(path):
    return hashlib.sha1(open(path, "rb").read()).hexdigest()


def search(q, pages):
    refs = []
    for page in range(1, pages + 1):
        out = dr.run([dr.KAGGLE, "kernels", "list", "--search", q, "--sort-by", "dateRun",
                      "--page-size", "20", "--page", str(page), "-v"]).stdout
        got = [l.split(",")[0].strip() for l in out.splitlines()[1:] if "/" in l.split(",")[0]]
        if not got:
            break
        refs += got
    return refs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=6)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    os.makedirs(FRESH, exist_ok=True)
    os.makedirs(OUTPUTS, exist_ok=True)

    refs = set(open(KNOWN).read().split()) if os.path.exists(KNOWN) else set()
    for q in QUERIES:
        refs |= set(search(q, a.pages))
    refs = sorted(r for r in refs if TOPICAL.search(r))
    print(len(refs), "topical kernel refs")

    dr.OUTPUTS = OUTPUTS          # fetch_agent downloads here; the folder starts empty, so every kernel is fetched fresh
    stats = {"new": 0, "changed": 0, "same": 0, "none": 0}
    for ref in refs:
        name = ref.split("/")[1][:40]
        try:
            p = dr.fetch_agent(ref)
        except Exception as e:
            print("ERR ", ref, repr(e)[:80])
            continue
        if not p:
            stats["none"] += 1
            continue
        old = os.path.join(POOL, name + ".py")
        kind = "new" if not os.path.exists(old) else ("same" if sha(old) == sha(p) else "changed")
        stats[kind] += 1
        if kind != "same":
            shutil.copy(p, os.path.join(FRESH, name + ".py"))
            print(f"{kind:8s}{ref} ({os.path.getsize(p) // 1024} KB)")
    print(stats)


if __name__ == "__main__":
    main()
