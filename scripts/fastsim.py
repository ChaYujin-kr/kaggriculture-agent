"""Fast headless match runner: drives the official kaggriculture interpreter directly,
skipping kaggle-environments' per-step deepcopy/structify (≈5x faster).

Agents receive the live observation objects, so they must not mutate them (ours don't).
"""
import importlib.util
import json
import os

from kaggle_environments.envs.kaggriculture import kaggriculture as K


class O(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__


_SPEC = json.load(open(os.path.join(os.path.dirname(K.__file__), "kaggriculture.json"), encoding="utf-8"))
DEFAULT_CFG = {k: v.get("default") if isinstance(v, dict) else v for k, v in _SPEC["configuration"].items()}


def load_agent(path, tag, params=None, flags=None):
    """Load an agent file as an isolated module (own globals).

    params: overrides for a PARAMS dict (our own agents).
    flags:  overrides for module-level globals of any agent; a "cfg.<key>" name instead patches
            the public chassis settings (_IMPL.chassis.cfg), which are copied at import time.
    """
    if not str(path).endswith(".py"):
        return K.agents[path]
    spec = importlib.util.spec_from_file_location(f"agent_{tag}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if params:
        for k, v in params.items():
            if isinstance(v, dict) and isinstance(mod.PARAMS.get(k), dict):
                mod.PARAMS[k] = {**mod.PARAMS[k], **v}
            else:
                mod.PARAMS[k] = v
    for k, v in (flags or {}).items():
        if k.startswith("cfg."):
            mod._IMPL.chassis.cfg[k[4:]] = v
        else:
            setattr(mod, k, v)
    return mod.agent


def play(agent_a, agent_b, seed):
    cfg = O(DEFAULT_CFG)
    cfg["seed"] = seed
    env = O(configuration=cfg, info={}, done=False)
    state = [O(observation=O(step=0), action=None, reward=0, status="ACTIVE") for _ in range(2)]
    K.interpreter(state, env)
    agents = [agent_a, agent_b]
    for step in range(cfg["episodeSteps"]):
        for s in state:
            s.observation["step"] = step
        for i, s in enumerate(state):
            o = s.observation
            obs0 = state[0].observation
            view = O(player=i, step=step, day=obs0.day, hour=obs0.hour, farms=obs0.farms,
                     market=obs0.market, town=obs0.town, private=o.private)
            try:
                s.action = agents[i](view)
            except Exception:
                s.action = {"farmer": ["PASS"], "hands": [], "market": []}
        K.interpreter(state, env)
        if all(s.status == "DONE" for s in state):
            break
    return [float(s.reward or 0.0) for s in state]


if __name__ == "__main__":
    import sys
    import time
    a = sys.argv[1] if len(sys.argv) > 1 else "agents/main.py"
    b = sys.argv[2] if len(sys.argv) > 2 else "agents/archive/v1.py"
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 7
    t = time.time()
    print(play(load_agent(a, "a"), load_agent(b, "b"), seed), f"{time.time() - t:.1f}s")
