import sys, time, json, pickle, collections
sys.path.insert(0, r"C:/Users/chauj/Desktop/kagriculture/scripts")
import fastsim
from concurrent.futures import ProcessPoolExecutor
CH = r"C:/Users/chauj/Desktop/kagriculture/submissions/v7_endgame.py"
POOL = r"C:/Users/chauj/Desktop/kagriculture/research/pool/"

def feat(o):
    me = o.farms[o.player]
    # compact scalar summary as a proxy of featurization cost
    tiles = me["tiles"]; n=0
    for row in tiles:
        for t in row:
            if isinstance(t, dict): n+=1
    return (o.step, me["money"], n, len(me["hands"]), tuple(sorted(o.market["prices"].items())), len(o.town["unlocked_shops"]))

def run(job):
    opp, seed, swap = job
    teacher = fastsim.load_agent(CH, "t")
    o = fastsim.load_agent(POOL + opp, "o")
    log = []
    def wrap(obs):
        a = teacher(obs)
        log.append((feat(obs), json.dumps(a, sort_keys=True)))
        return a
    t = time.time()
    r = fastsim.play(o, wrap, seed) if swap else fastsim.play(wrap, o, seed)
    dt = time.time() - t
    me = r[1] if swap else r[0]; op = r[0] if swap else r[1]
    return opp, seed, swap, dt, me, op, [l[1] for l in log], len(pickle.dumps(log))

if __name__ == "__main__":
    jobs = [(opp, s, sw) for opp in ["v56.py", "aurax7_v7.py", "farm2945.py"] for s in (101, 202) for sw in (0, 1)]
    t0 = time.time()
    with ProcessPoolExecutor(8) as ex:
        res = list(ex.map(run, jobs))
    wall = time.time() - t0
    print(f"{len(jobs)} games wall {wall:.1f}s -> {len(jobs)/wall:.2f} games/s on 8 workers")
    for opp, s, sw, dt, me, op, acts, sz in res:
        print(opp, s, sw, f"{dt:.1f}s", me, op, "win" if me > op else "loss", "logbytes", sz)
    # tape-ness: compare action strings of first job vs others, excluding market
    def unit(a): d = json.loads(a); return json.dumps([d.get("farmer"), d.get("hands")])
    def mk(a): d = json.loads(a); return json.dumps(d.get("market"))
    base = res[0][6]
    for r_ in res[1:]:
        acts = r_[6]; L = min(len(base), len(acts))
        u = sum(unit(base[i]) == unit(acts[i]) for i in range(L)) / L
        m = sum(mk(base[i]) == mk(acts[i]) for i in range(L)) / L
        first_div = next((i for i in range(L) if unit(base[i]) != unit(acts[i])), L)
        print("vs", r_[0], r_[1], r_[2], f"unit-identical {u:.3f} market-identical {m:.3f} first unit divergence step {first_div}")
    # action vocabulary stats
    cnt = collections.Counter(); nh = []
    for a in base:
        d = json.loads(a); cnt[d["farmer"][0]] += 1; nh.append(len(d.get("hands", [])))
        for h in d.get("hands", []): cnt["h:" + h[0]] += 1
        for mo in d.get("market", []): cnt["m:" + mo[0]] += 1
    print(cnt.most_common(40)); print("max hands", max(nh), "mean", sum(nh)/len(nh))
