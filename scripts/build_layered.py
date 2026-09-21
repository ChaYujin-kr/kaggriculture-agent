"""Build a single-file submission: public "2945 Farm" base agent (Apache-2.0, embedded unmodified)
plus our layer (agents/layer_fert.py, inlined as readable source).

usage: python scripts/build_layered.py --out submissions/layer_a.py [--set extra_hands=2 stationary=False]
"""
import argparse
import ast
import base64
import os
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "research", "extracted", "the-2945-farm-96-vs-the-top-10-public-bots", "main.py")
LAYER = os.path.join(ROOT, "agents", "layer_fert.py")

WRAPPER = '''
# ---------------------------------------------------------------------------------------------
# MODIFIED by Yujin Cha (2026-09): the unmodified base agent above ("2945 Farm", thomastschinkel,
# Kaggle notebook "the-2945-farm-96-vs-the-top-10-public-bots", Apache-2.0) is embedded below and
# wrapped by an original gap-filling layer. Layer settings: {overrides}
# ---------------------------------------------------------------------------------------------
import base64 as _hb_b64
import zlib as _hb_zlib


def _hb_load(blob, name):
    ns = {{"__name__": name, "__builtins__": __builtins__}}
    exec(compile(_hb_zlib.decompress(_hb_b64.b64decode(blob)).decode("utf-8"), name, "exec"), ns)
    return ns


_HB_BASE = _hb_load("{base_blob}", "hb_base")

{layer_src}

LAYER.update({overrides})


def agent(obs, config=None):
    base = _HB_BASE["agent"](obs, config)
    try:
        return layer(obs, base)
    except Exception:
        return base
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--set", nargs="*", default=[], help="LAYER overrides key=value (python literal)")
    a = ap.parse_args()
    overrides = {}
    for kv in a.set:
        k, v = kv.split("=", 1)
        overrides[k] = ast.literal_eval(v)
    header = []
    for line in open(BASE, encoding="utf-8"):
        if line.strip() and not line.lstrip().startswith("#"):
            break
        header.append(line.rstrip("\n"))
    blob = base64.b64encode(zlib.compress(open(BASE, "rb").read(), 9)).decode("ascii")
    src = "\n".join(header) + "\n" + WRAPPER.format(
        overrides=repr(overrides), base_blob=blob, layer_src=open(LAYER, encoding="utf-8").read())
    compile(src, a.out, "exec")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(src)
    print(f"wrote {a.out} ({len(src) / 1024:.0f} KB) overrides={overrides}")


if __name__ == "__main__":
    main()
