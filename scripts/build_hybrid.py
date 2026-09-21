"""Build a single-file hybrid submission: the public "2945 Farm" agent (Apache-2.0) drives the game until
SWITCH_STEP, then our market-aware planner (agents/main.py + tuned PARAMS) takes over.

usage: python scripts/build_hybrid.py --switch 432 --out submissions/hybrid_432.py
The base agent's license header is copied verbatim to the top of the output; both sources are embedded
compressed and executed in separate namespaces so their module-level state never collides.
"""
import argparse
import base64
import json
import os
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "research", "extracted", "the-2945-farm-96-vs-the-top-10-public-bots", "main.py")
PLANNER = os.path.join(ROOT, "agents", "main.py")
PARAMS = os.path.join(ROOT, "tuning", "best_params.json")

TEMPLATE = '''{header}
#
# ---------------------------------------------------------------------------------------------
# MODIFIED by Yujin Cha (2026-09): hybrid wrapper. The unmodified base agent above ("2945 Farm",
# thomastschinkel, Kaggle notebook "the-2945-farm-96-vs-the-top-10-public-bots", Apache-2.0) plays
# steps < SWITCH_STEP; afterwards our own market-aware planner (original work) takes over.
# ---------------------------------------------------------------------------------------------
import base64 as _hb_b64
import zlib as _hb_zlib

SWITCH_STEP = {switch}
_HB_PLANNER_PARAMS = {params}


def _hb_load(blob, name):
    ns = {{"__name__": name, "__builtins__": __builtins__}}
    src = _hb_zlib.decompress(_hb_b64.b64decode(blob)).decode("utf-8")
    exec(compile(src, name, "exec"), ns)
    return ns


_HB_BASE = _hb_load("{base_blob}", "hb_base")
_HB_PLAN = _hb_load("{plan_blob}", "hb_planner")
for _k, _v in _HB_PLANNER_PARAMS.items():
    if isinstance(_v, dict) and isinstance(_HB_PLAN["PARAMS"].get(_k), dict):
        _HB_PLAN["PARAMS"][_k].update(_v)
    else:
        _HB_PLAN["PARAMS"][_k] = _v


def agent(obs, config=None):
    step = obs.get("step", 0) if hasattr(obs, "get") else obs["step"]
    if step < SWITCH_STEP:
        return _HB_BASE["agent"](obs, config)
    return _HB_PLAN["agent"](obs, config)
'''


def blob(path):
    return base64.b64encode(zlib.compress(open(path, "rb").read(), 9)).decode("ascii")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--switch", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--params", default=PARAMS)
    ap.add_argument("--planner", default=PLANNER)
    a = ap.parse_args()
    header = []
    for line in open(BASE, encoding="utf-8"):
        if line.strip() and not line.lstrip().startswith("#"):
            break
        header.append(line.rstrip("\n"))
    params = json.load(open(a.params)) if a.params and os.path.exists(a.params) else {}
    src = TEMPLATE.format(header="\n".join(header), switch=a.switch, params=repr(params),
                          base_blob=blob(BASE), plan_blob=blob(a.planner))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(src)
    print(f"wrote {a.out} ({len(src) / 1024:.0f} KB), switch at step {a.switch}")


if __name__ == "__main__":
    main()
