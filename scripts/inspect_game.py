"""Play one game and print a per-day trace of both players (money, land, tile mix, hands, shed, prices).

usage: python scripts/inspect_game.py [agentA] [agentB] [--seed N]
"""
import argparse
import importlib.util
import os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path_or_name, tag):
    if not path_or_name.endswith(".py"):
        return path_or_name
    spec = importlib.util.spec_from_file_location(f"agent_{tag}", path_or_name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent


def tile_mix(tiles):
    c = Counter()
    for row in tiles:
        for t in row:
            if t is None:
                c["."] += 1
            elif t == "LOCKED":
                continue
            elif t.get("kind") == "PLANT":
                c[t["crop"][:3]] += 1
            elif t.get("animal"):
                c[t["animal"][:3]] += 1
            else:
                c[t.get("kind")[:4]] += 1
    return " ".join(f"{k}:{v}" for k, v in sorted(c.items()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a", nargs="?", default=os.path.join(ROOT, "agents", "main.py"))
    ap.add_argument("b", nargs="?", default=os.path.join(ROOT, "agents", "archive", "v1.py"))
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"seed": args.seed}, debug=True)
    env.run([load(args.a, "a"), load(args.b, "b")])
    for s in range(0, len(env.steps), 24):
        obs = env.steps[s][0].observation
        print(f"day {s // 24:2d} shops={len(obs.town['unlocked_shops'])} prices="
              + " ".join(f"{k[:3]}{v}" for k, v in obs.market["prices"].items()))
        for p in range(2):
            st = env.steps[s][p]
            f = obs.farms[p]
            shed = {k: v for k, v in st.observation.private["shed"].items() if v}
            print(f"   P{p} ${f['money']:8.0f} q={len(f['unlocked_quadrants'])} hands={len(f['hands'])} "
                  f"| {tile_mix(f['tiles'])} | shed {shed}")
    print("final", [s.reward for s in env.steps[-1]], [s.status for s in env.steps[-1]])


if __name__ == "__main__":
    main()
