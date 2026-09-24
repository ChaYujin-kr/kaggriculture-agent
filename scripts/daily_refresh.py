"""Daily meta refresh: pull the newest public agents, test them against our champion, and submit
a better one (with our tuned knobs applied) if it clearly wins.

The public meta in this competition turns over daily, so the champion file must keep up.

usage: python scripts/daily_refresh.py [--dry-run] [--seeds 3] [--workers 2] [--max-new 6]
Log: research/daily_log.txt   Champion pointer: tuning/champion.json
"""
import argparse
import ast
import datetime as dt
import glob
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


def newest_kernels(limit=25):
    out = run([KAGGLE, "kernels", "list", "--competition", "kaggriculture",
               "--sort-by", "dateRun", "--page-size", str(limit), "-v"]).stdout
    refs = []
    for line in out.splitlines()[1:]:
        parts = line.split(",")
        if len(parts) >= 4 and "/" in parts[0]:
            refs.append(parts[0].strip())
    return refs


def fetch_agent(ref):
    """Download a kernel's output and return the path of a usable single-file agent, or None."""
    name = ref.split("/")[1]
    dest = os.path.join(OUTPUTS, name)
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--max-new", type=int, default=6)
    ap.add_argument("--win-threshold", type=float, default=0.60)
    a = ap.parse_args()
    os.makedirs(POOL, exist_ok=True)
    champ = champion_path()
    log(f"=== daily refresh; champion = {os.path.basename(champ)}")

    known = {os.path.basename(p)[:-3] for p in glob.glob(os.path.join(POOL, "*.py"))}
    new = []
    for ref in newest_kernels():
        name = ref.split("/")[1]
        if name[:40] in known or any(k.startswith(name[:25]) for k in known):
            continue
        p = fetch_agent(ref)
        if not p:
            continue
        dst = os.path.join(POOL, name[:40] + ".py")
        shutil.copy(p, dst)
        new.append(dst)
        log(f"new candidate: {ref} -> {os.path.basename(dst)} ({os.path.getsize(dst) // 1024} KB)")
        if len(new) >= a.max_new:
            break
    if not new:
        log("no new public agents today")
        return

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
    best = challengers[0][1]
    tuned = os.path.join(ROOT, "submissions", f"auto_{dt.date.today():%m%d}_{os.path.basename(best)}")
    used = apply_flags(best, tuned)
    log(f"applying flags {used} to {os.path.basename(best)}")
    seeds2 = list(range(21000, 21000 + a.seeds + 2))
    w, n = duel(tuned, champ, seeds2, a.workers)
    log(f"validation on fresh seeds: {w}/{n}")
    if w / n < a.win_threshold:
        log("did not hold up on fresh seeds; champion keeps its place")
        return
    if a.dry_run:
        log(f"DRY RUN: would submit {os.path.basename(tuned)}")
        return
    msg = f"auto: {os.path.basename(best)[:-3]} (public, Apache-2.0) + our knob search; {w}/{n} vs previous champion"
    r = run([KAGGLE, "competitions", "submit", "kaggriculture", "-f", tuned, "-m", msg])
    out = (r.stdout or "").strip()
    log(f"submit: {out.splitlines()[-1] if out else (r.stderr or '')[:200]}")
    if "Successfully submitted" in out:
        json.dump({"path": tuned, "date": str(dt.date.today())}, open(CHAMPION, "w"), indent=1)
        log(f"new champion: {os.path.basename(tuned)}")


if __name__ == "__main__":
    main()
