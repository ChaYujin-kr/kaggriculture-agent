"""Download every replay of our recent submissions, summarise each to one JSON line, delete the replay.

Episode lists come from research/ladder/eps_<submission id>.csv; output is research/ladder/summaries.jsonl.
usage: python scripts/ladder_harvest.py [threads]
"""
import csv, json, os, re, subprocess, sys, hashlib
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, "research", "ladder")
RP = os.path.join(S, "rp")
KAGGLE = os.path.join(ROOT, ".venv", "Scripts", "kaggle.exe")
OUT = os.path.join(S, "summaries.jsonl")
SUBS = {"56482583": "v7_endgame", "56481388": "v7_base", "56473646": "hybrid_tuned",
        "56541496": "shepherd_0925", "56549345": "hybrid_resub",
        "56612456": "shepherd_p6", "56612448": "hybrid_cxd_p8",
        "56633420": "ttv1_flags"}
ME = "Yujin Cha"


def env():
    e = dict(os.environ)
    for ln in open(os.path.join(ROOT, ".env"), encoding="utf-8-sig"):
        m = re.match(r"^(KAGGLE_\w+)=(.+)$", ln.strip())
        if m and m.group(2).strip():
            e[m.group(1)] = m.group(2).strip()
    e["PYTHONIOENCODING"] = "utf-8"
    return e


def mix(tiles):
    c = Counter()
    for row in tiles:
        for t in row:
            if t is None or t == "LOCKED":
                continue
            if t.get("kind") == "PLANT":
                c["p:" + t["crop"]] += 1
            elif t.get("animal"):
                c["a:" + t["animal"]] += 1
            else:
                c["k:" + t["kind"]] += 1
    return dict(c)


def summarise(path, ep, sub, ctime):
    r = json.load(open(path, encoding="utf-8"))
    teams = r["info"]["TeamNames"]
    steps = r["steps"]
    me = 0 if teams[0] == ME else 1
    op = 1 - me
    rew = r.get("rewards") or [steps[-1][p].get("reward") for p in (0, 1)]
    money = {0: [], 1: []}
    mixes = {}
    for t in range(0, len(steps), 24):
        farms = steps[t][0]["observation"]["farms"]
        for p in (0, 1):
            money[p].append(farms[p]["money"])
    for d in (5, 10, 15, 20, 25, 29):
        t = min(len(steps) - 1, d * 24 + 12)
        farms = steps[t][0]["observation"]["farms"]
        mixes[d] = {p: mix(farms[p]["tiles"]) for p in (0, 1)}
    # action stats per seat (action at step t is in steps[t][p]["action"])
    acts = {0: Counter(), 1: Counter()}
    mkt = {0: Counter(), 1: Counter()}
    hands = {0: [], 1: []}
    quads = {0: [], 1: []}
    open_seq = {0: [], 1: []}
    for t in range(1, len(steps)):
        for p in (0, 1):
            a = steps[t][p].get("action") or {}
            f = a.get("farmer") or []
            if f:
                acts[p][f[0]] += 1
            for h in a.get("hands") or []:
                if h:
                    acts[p]["hand:" + str(h[0])] += 1
            for m in a.get("market") or []:
                if m:
                    key = " ".join(str(x) for x in m[:2])
                    mkt[p][key] += 1
            if t <= 48:
                open_seq[p].append(json.dumps(a, sort_keys=True))
    for t in range(0, len(steps), 24):
        farms = steps[t][0]["observation"]["farms"]
        for p in (0, 1):
            hands[p].append(len(farms[p].get("hands") or []))
            quads[p].append(len(farms[p].get("unlocked_quadrants") or []))
    spend0 = {p: 3000.0 - steps[1][0]["observation"]["farms"][p]["money"] for p in (0, 1)}
    return dict(
        ep=ep, sub=SUBS[sub], sub_id=sub, ctime=ctime, seed=r["info"].get("seed"),
        me_seat=me, opp=teams[op], rew_me=rew[me], rew_op=rew[op],
        status=[steps[-1][p].get("status") for p in (0, 1)],
        money_me=money[me], money_op=money[op],
        mix_me={d: v[me] for d, v in mixes.items()}, mix_op={d: v[op] for d, v in mixes.items()},
        acts_me=dict(acts[me]), acts_op=dict(acts[op]), mkt_me=dict(mkt[me]), mkt_op=dict(mkt[op]),
        hands_me=hands[me], hands_op=hands[op], quads_me=quads[me], quads_op=quads[op],
        spend0_me=spend0[me], spend0_op=spend0[op],
        openhash_op=hashlib.md5("|".join(open_seq[op]).encode()).hexdigest()[:10],
        openhash_me=hashlib.md5("|".join(open_seq[me]).encode()).hexdigest()[:10],
    )


def job(args):
    ep, sub, ctime = args
    local = os.path.join(ROOT, "replays", f"episode-{ep}-replay.json")
    path = local if os.path.exists(local) else os.path.join(RP, f"episode-{ep}-replay.json")
    try:
        if not os.path.exists(path):
            subprocess.run([KAGGLE, "competitions", "replay", ep, "-p", RP], capture_output=True,
                           env=env(), timeout=600)
        if not os.path.exists(path):
            return {"ep": ep, "sub": SUBS[sub], "error": "download failed"}
        s = summarise(path, ep, sub, ctime)
        if path.startswith(RP):
            os.remove(path)
        return s
    except Exception as e:
        return {"ep": ep, "sub": SUBS[sub], "error": repr(e)}


def main():
    done = set()
    if os.path.exists(OUT):
        for ln in open(OUT, encoding="utf-8"):
            d = json.loads(ln)
            if "error" not in d:
                done.add(d["ep"])
    todo = []
    for sub in SUBS:
        eps = os.path.join(S, f"eps_{sub}.csv")
        if not os.path.exists(eps):   # written by ladder_track.py once the submission is active
            continue
        for row in csv.DictReader(open(eps, encoding="utf-8")):
            if row["id"] and row["id"].isdigit() and "COMPLETED" in (row["state"] or "") and row["id"] not in done:
                todo.append((row["id"], sub, row["createTime"]))
    print(len(todo), "to do", flush=True)
    with ThreadPoolExecutor(int(sys.argv[1]) if len(sys.argv) > 1 else 6) as ex, open(OUT, "a", encoding="utf-8") as f:
        for i, s in enumerate(ex.map(job, todo)):
            f.write(json.dumps(s) + "\n")
            f.flush()
            if i % 10 == 0:
                print(i, s.get("ep"), s.get("sub"), s.get("opp"), s.get("error"), flush=True)


if __name__ == "__main__":
    main()
