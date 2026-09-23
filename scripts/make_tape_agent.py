"""Turn one seat of a downloaded replay into a standalone sparring agent that replays its actions.

The tape is open-loop: it repeats what that team did, which is exactly how the public "tape" agents
work, so it is a realistic stand-in for that ladder opponent (it cannot react to us, so treat wins
against it as an upper bound).

usage: python scripts/make_tape_agent.py research/episodes/top/111414734.json --seat 1 --out research/pool/tape_dsm.py
"""
import argparse
import base64
import json
import os
import zlib

TEMPLATE = '''"""Sparring agent: open-loop replay of {team} (seat {seat}) from Kaggle episode {episode}.
Final bank in that episode: ${bank:.0f}. Built by scripts/make_tape_agent.py for local evaluation only.
"""
import base64 as _b64
import json as _json
import zlib as _zlib

_TAPE = _json.loads(_zlib.decompress(_b64.b64decode("{blob}")).decode("utf-8"))
_PASS = {{"farmer": ["PASS"], "hands": [], "market": []}}


def agent(obs, config=None):
    step = obs.get("step", 0) if hasattr(obs, "get") else obs["step"]
    act = _TAPE[step] if 0 <= step < len(_TAPE) else None
    if not isinstance(act, dict):
        return dict(_PASS)
    hands = obs["farms"][obs["player"]].get("hands") or []
    out = {{"farmer": act.get("farmer") or ["PASS"],
           "hands": (act.get("hands") or [])[:len(hands)],
           "market": act.get("market") or []}}
    while len(out["hands"]) < len(hands):
        out["hands"].append(["PASS"])
    return out
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("replay")
    ap.add_argument("--seat", type=int, default=None, help="default: the winning seat")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    r = json.load(open(a.replay, encoding="utf-8"))
    steps = r["steps"]
    rewards = [steps[-1][p].get("reward") or 0 for p in (0, 1)]
    seat = a.seat if a.seat is not None else (0 if rewards[0] >= rewards[1] else 1)
    team = (r.get("info", {}).get("TeamNames") or ["?", "?"])[seat]
    tape = [(steps[i][seat].get("action") if i < len(steps) else None) for i in range(1, len(steps))]
    blob = base64.b64encode(zlib.compress(json.dumps(tape).encode("utf-8"), 9)).decode("ascii")
    src = TEMPLATE.format(team=team, seat=seat, episode=os.path.basename(a.replay).split(".")[0],
                          bank=rewards[seat], blob=blob)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(src)
    print(f"wrote {a.out}: {team} seat {seat}, bank ${rewards[seat]:.0f}, {len(tape)} steps, {len(src) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
