"""Daily meta refresh: pull the newest public agents, test them against our champion, and submit
a better one (with our tuned knobs applied) if it clearly wins.

Head to head against the champion is only the first filter. The best challenger, with our knobs
applied, is submitted only if it passes the lineage-weighted gauntlet (scripts/gauntlet.py,
research/gauntlet.json): it has to hold the wall lineages and outscore the champion.

The public meta in this competition turns over daily, so the champion file must keep up.

usage: python scripts/daily_refresh.py [--dry-run] [--seeds 3] [--workers 2] [--max-new 6]
Log: research/daily_log.txt   Champion pointer: tuning/champion.json
"""
import argparse
import ast
import datetime as dt
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV = os.path.join(ROOT, ".venv", "Scripts")
KAGGLE = os.path.join(VENV, "kaggle.exe")
POOL = os.path.join(ROOT, "research", "pool")
OUTPUTS = os.path.join(ROOT, "research", "outputs")
LOG = os.path.join(ROOT, "research", "daily_log.txt")
CHAMPION = os.path.join(ROOT, "tuning", "champion.json")
SEEN = os.path.join(ROOT, "research", "kernel_runs_seen.json")  # kernel ref -> lastRunTime fetched
FLAGS = os.path.join(ROOT, "tuning", "best_flags_v1.json")


def log(msg):
    line = f"{dt.datetime.now():%Y-%m-%d %H:%M}  {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def env():
    e = dict(os.environ)
    for ln in open(os.path.join(ROOT, ".env"), encoding="utf-8-sig"):
        m = re.match(r"^(KAGGLE_\w+)=(.+)$", ln.strip())
        if m and m.group(2).strip():
            e[m.group(1)] = m.group(2).strip()
    e["KAGGLE_COMPETITION"] = "kaggriculture"
    return e


def run(args, **kw):
    # kernel titles contain emoji; the console codepage (cp949 here) cannot decode them
    return subprocess.run(args, capture_output=True, text=True, env=env(),
                          encoding="utf-8", errors="replace", **kw)


def newest_kernel_runs(limit=25):
    """[(ref, lastRunTime)], newest run first. Titles can hold quoted commas, so parse as CSV."""
    import csv
    out = run([KAGGLE, "kernels", "list", "--competition", "kaggriculture",
               "--sort-by", "dateRun", "--page-size", str(limit), "-v"]).stdout
    return [(r["ref"].strip(), r.get("lastRunTime", "").strip())
            for r in csv.DictReader(ln for ln in out.splitlines() if ln.strip())
            if "/" in (r.get("ref") or "")]


def newest_kernels(limit=25):
    return [ref for ref, _ in newest_kernel_runs(limit)]


def md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def fetch_agent(ref, dest=None):
    """Download a kernel's output and return the path of a usable single-file agent, or None."""
    name = ref.split("/")[1]
    dest = dest or os.path.join(OUTPUTS, name)
    if not os.path.exists(dest):
        r = run([KAGGLE, "kernels", "output", ref, "-p", dest])
        if r.returncode != 0:
            return None
    for tgz in glob.glob(os.path.join(dest, "*.tar.gz")):
        x = os.path.join(dest, "x")
        if not os.path.exists(x):
            try:
                with tarfile.open(tgz) as t:
                    t.extractall(x)
            except Exception:
                pass
    cands = [p for p in glob.glob(os.path.join(dest, "**", "*.py"), recursive=True)
             if os.path.getsize(p) > 100_000]
    for p in sorted(cands, key=os.path.getsize, reverse=True):
        try:
            src = open(p, encoding="utf-8", errors="replace").read()
            ast.parse(src)
            if "def agent(" in src:
                return p
        except Exception:
            continue
    return None


def champion_path():
    if os.path.exists(CHAMPION):
        p = json.load(open(CHAMPION, encoding="utf-8-sig")).get("path")
        if p and os.path.exists(p):
            return p
    return os.path.join(ROOT, "submissions", "hybrid2965_tuned.py")


def apply_flags(src_path, out_path):
    """Append our tuned knob values, but only those the file actually defines."""
    src = open(src_path, encoding="utf-8").read()
    flags = json.load(open(FLAGS, encoding="utf-8-sig")) if os.path.exists(FLAGS) else {}
    used = {k: v for k, v in flags.items()
            if re.search(rf"^{re.escape(k)}\s*=", src, re.M)}
    block = ["", "", "# " + "-" * 92,
             "# MODIFIED by Yujin Cha: knob values found by a search over this agent's own exposed",
             "# settings (scripts/tune_flags.py), scored by win count against a pool of public agents.",
             "# Logic unchanged; upstream Apache-2.0 notices above are retained.",
             "# " + "-" * 92]
    block += [f"{k} = {v!r}" for k, v in used.items()]
    open(out_path, "w", encoding="utf-8").write(src + "\n".join(block) + "\n")
    return used


def duel(a_path, b_path, seeds, workers):
    import league
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=workers) as ex:
        out = league.evaluate(a_path, [b_path], seeds, pool=ex)
    rs = [r for v in out.values() for r in v]
    w = sum(1 for r in rs if r[0] > r[1]) + 0.5 * sum(1 for r in rs if r[0] == r[1])
    return w, len(rs)


def playoff(paths, n_seeds, workers):
    """Round-robin the challengers tied against the champion; sorting by path would pick by name."""
    seeds = list(range(20500, 20500 + n_seeds))
    wins = {p: 0.0 for p in paths}
    for i, p in enumerate(paths):
        for q in paths[i + 1:]:
            w, n = duel(p, q, seeds, workers)
            wins[p] += w
            wins[q] += n - w
            log(f"  playoff: {os.path.basename(p)} vs {os.path.basename(q)}: {w}/{n}")
    return max(paths, key=lambda p: wins[p])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--max-new", type=int, default=6)
    ap.add_argument("--win-threshold", type=float, default=0.60)
    ap.add_argument("--gauntlet-seeds", type=int, default=6)
    ap.add_argument("--wall-min", type=float, default=0.5)
    ap.add_argument("--gauntlet-margin", type=float, default=0.0)
    a = ap.parse_args()
    os.makedirs(POOL, exist_ok=True)
    champ = champion_path()
    log(f"=== daily refresh; champion = {os.path.basename(champ)}")

    # A known kernel name is not a known agent: authors re-run the same notebook with new code.
    # So refetch any kernel whose last run changed since we saw it, and call it new by content hash.
    # Candidates stay staged in the download folder until evaluate() finishes; only then do they
    # join the pool and the kernel runs count as seen, so a run killed midway re-tests them.
    known = {md5(p) for p in glob.glob(os.path.join(POOL, "*.py"))}
    seen = json.load(open(SEEN, encoding="utf-8")) if os.path.exists(SEEN) else {}
    stamp = dt.datetime.now().strftime("%m%d_%H%M%S")
    new = []
    for ref, ran in newest_kernel_runs():
        if seen.get(ref) == ran:
            continue
        name = ref.split("/")[1]
        dest = os.path.join(OUTPUTS, "_runs", name, stamp)  # apart from fetch_agent's default folders
        p = fetch_agent(ref, dest)
        if not os.path.isdir(dest):
            continue  # download failed: leave it unseen so the next run retries
        if p and md5(p) not in known:
            pool_name = name[:40] + ".py"
            if os.path.exists(os.path.join(POOL, pool_name)):
                pool_name = f"{name[:30]}_{stamp[:4]}_{md5(p)[:6]}.py"
            # outside dest, or a refetch into dest would find this copy; the name also names auto_ files
            staged = os.path.join(OUTPUTS, "_runs", "_staged", stamp, pool_name)
            os.makedirs(os.path.dirname(staged), exist_ok=True)
            shutil.copy(p, staged)
            known.add(md5(p))
            new.append(staged)
            log(f"new candidate: {ref} (run {ran}) -> {pool_name} ({os.path.getsize(staged) // 1024} KB)")
        seen[ref] = ran
        if len(new) >= a.max_new:
            break
    if new:
        evaluate(a, champ, new)
    else:
        log("no new public agents today")
    for p in new:
        shutil.copy(p, os.path.join(POOL, os.path.basename(p)))
    json.dump(seen, open(SEEN, "w", encoding="utf-8"), indent=1)


def evaluate(a, champ, new):
    """Duel the new agents against the champion, gauntlet the best, and submit it if it passes."""
    seeds = list(range(20000, 20000 + a.seeds))
    challengers = []
    for p in new:
        try:
            w, n = duel(p, champ, seeds, a.workers)
        except Exception as e:
            log(f"  {os.path.basename(p)}: ERROR {e}")
            continue
        log(f"  {os.path.basename(p)} vs champion: {w}/{n}")
        if w / n >= a.win_threshold:
            challengers.append((w / n, p))
    if not challengers:
        log("champion holds")
        return

    challengers.sort(reverse=True)
    top = [p for r, p in challengers if r == challengers[0][0]]
    best = top[0] if len(top) == 1 else playoff(top, a.seeds, a.workers)
    tuned = os.path.join(ROOT, "submissions", f"auto_{dt.date.today():%m%d}_{os.path.basename(best)}")
    used = apply_flags(best, tuned)
    log(f"applying flags {used} to {os.path.basename(best)}")

    # Beating the champion head to head is only a cheap filter: on 09-25 it promoted an agent that
    # loses to hybrid and V53, the ladder's biggest lineages. Submission needs the weighted gauntlet.
    import gauntlet
    cfg = json.load(open(gauntlet.CONFIG, encoding="utf-8"))
    gseeds = list(range(gauntlet.SEED0, gauntlet.SEED0 + a.gauntlet_seeds))
    base = gauntlet.score(champ, gseeds, a.workers, cfg)
    res = gauntlet.score(tuned, gseeds, a.workers, cfg)
    lines = ", ".join(f"{k} {v:.0%}" for k, v in res["lineages"].items())
    log(f"gauntlet: {res['score']:.1%} vs champion {base['score']:.1%} ({lines})")
    ok, why = gauntlet.verdict(res, cfg, a.wall_min, base, a.gauntlet_margin)
    if not ok:
        log("gauntlet rejects: " + "; ".join(why) + "; champion keeps its place")
        return
    if a.dry_run:
        log(f"DRY RUN: would submit {os.path.basename(tuned)}")
        return
    msg = (f"auto: {os.path.basename(best)[:-3]} (public, Apache-2.0) + our knob search; "
           f"gauntlet {res['score']:.0%} vs previous champion {base['score']:.0%}")
    r = run([KAGGLE, "competitions", "submit", "kaggriculture", "-f", tuned, "-m", msg])
    out = (r.stdout or "").strip()
    log(f"submit: {out.splitlines()[-1] if out else (r.stderr or '')[:200]}")
    if "Successfully submitted" in out:
        json.dump({"path": tuned, "date": str(dt.date.today())}, open(CHAMPION, "w"), indent=1)
        log(f"new champion: {os.path.basename(tuned)}")


if __name__ == "__main__":
    main()
