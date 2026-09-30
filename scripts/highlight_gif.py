"""Render one ladder replay as an animated GIF: both farms side by side, the bank lead, and its history.

Our seat is always drawn on the left. Frames run every 12 steps until day 26, then every 2 steps so the
last three days play slowly, and the final frame holds.
usage: python scripts/highlight_gif.py REPLAY.json OUT.gif [--me "Yujin Cha"]
"""
import argparse
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_sprites import person_image, tile_image  # noqa: E402

FONT = "C:/Windows/Fonts/malgun.ttf"
FONT_B = "C:/Windows/Fonts/malgunbd.ttf"
T = 32                      # tile size in px (16x16 pixel art at 2x)
GRID = 10 * T
PAD = 16
W = PAD * 3 + GRID * 2
H = 44 + 22 + GRID + 110

BG = (246, 247, 242)
INK = (27, 34, 28)
MUTED = (88, 100, 90)
RULE = (211, 217, 205)
US = (46, 106, 59)
THEM = (154, 102, 20)


def draw_farm(im, farm, x0, y0):
    for y, row in enumerate(farm["tiles"]):
        for x, t in enumerate(row):
            im.paste(tile_image(t, x, y, T), (x0 + x * T, y0 + y * T))
    people = [farm["farmer"]] + list(farm.get("hands") or [])
    for i, (hx, hy) in reversed(list(enumerate(people))):
        sp = person_image(i == 0, T)
        im.paste(sp, (x0 + hx * T, y0 + hy * T - 4), sp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("replay")
    ap.add_argument("out")
    ap.add_argument("--me", default="Yujin Cha")
    a = ap.parse_args()
    r = json.load(open(a.replay, encoding="utf-8"))
    steps = r["steps"]
    names = r["info"]["TeamNames"]
    me = names.index(a.me)
    op = 1 - me
    final = [steps[-1][p].get("reward") for p in (0, 1)]
    f_big = ImageFont.truetype(FONT_B, 17)
    f = ImageFont.truetype(FONT, 13)
    f_small = ImageFont.truetype(FONT, 11)

    lead_all = []
    for t in range(len(steps)):
        fm = steps[t][0]["observation"]["farms"]
        lead_all.append(fm[me]["money"] - fm[op]["money"])
    lead_all[-1] = final[me] - final[op]
    scale = max(800.0, max(abs(v) for v in lead_all))
    idx = list(range(0, 26 * 24, 12)) + list(range(26 * 24, len(steps), 2))
    if idx[-1] != len(steps) - 1:
        idx.append(len(steps) - 1)
    leads = []
    frames, durations = [], []
    for k, t in enumerate(idx):
        obs = steps[t][0]["observation"]
        farms = obs["farms"]
        last = t == len(steps) - 1
        money = [final[p] if last else farms[p]["money"] for p in (0, 1)]
        lead = money[me] - money[op]
        leads.append((t, lead))

        im = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(im)
        day, hour = t // 24, t % 24
        d.text((PAD, 12), "FINAL" if last else f"Day {day + 1}  ·  {hour:02d}:00", font=f_big, fill=INK)
        tag = f"step {t}/719"
        d.text((W - PAD - d.textlength(tag, font=f_small), 17), tag, font=f_small, fill=MUTED)
        for col, (p, colr) in enumerate(((me, US), (op, THEM))):
            x0 = PAD + col * (GRID + PAD)
            nm = names[p] if len(names[p]) <= 22 else names[p][:21] + "…"
            d.text((x0, 44), nm, font=f, fill=colr)
            m = f"${money[p]:,.0f}"
            d.text((x0 + GRID - d.textlength(m, font=f), 44), m, font=f, fill=INK)
            draw_farm(im, farms[p], x0, 66)

        # lead bar: centre line, our lead grows right in green, theirs left in brown
        y = 66 + GRID + 14
        cx, half = W // 2, W // 2 - PAD
        d.line([PAD, y + 7, W - PAD, y + 7], fill=RULE, width=1)
        w = int(half * min(1.0, abs(lead) / scale))
        if lead >= 0:
            d.rectangle([cx, y, cx + w, y + 14], fill=US)
        else:
            d.rectangle([cx - w, y, cx, y + 14], fill=THEM)
        d.line([cx, y - 3, cx, y + 17], fill=INK, width=1)
        txt = ("Lead " if lead >= 0 else "Behind ") + f"${abs(lead):,.0f}"
        d.text((cx + 6 if lead < 0 else cx - 6 - d.textlength(txt, font=f), y + 18), txt, font=f,
               fill=US if lead >= 0 else THEM)

        # lead history over the whole game so far
        gy, gh = y + 40, 34
        d.line([PAD, gy + gh // 2, W - PAD, gy + gh // 2], fill=RULE, width=1)
        pts = [(PAD + (W - 2 * PAD) * tt / 719, gy + gh // 2 - (gh // 2) * max(-1, min(1, v / scale)))
               for tt, v in leads]
        for (p0, (_, v0)), (p1, (_, v1)) in zip(zip(pts, leads), zip(pts[1:], leads[1:])):
            d.line([p0, p1], fill=US if v1 >= 0 else THEM, width=2)
        d.text((PAD, gy + gh + 1), "day 1", font=f_small, fill=MUTED)
        d.text((W - PAD - d.textlength("day 30", font=f_small), gy + gh + 1), "day 30", font=f_small, fill=MUTED)

        frames.append(im)
        durations.append(3500 if last else (70 if t < 26 * 24 else 110))
    probe = Image.new("RGB", (W, H * 3))
    for i, fr in enumerate((frames[0], frames[len(frames) // 2], frames[-1])):
        probe.paste(fr, (0, H * i))
    pal = probe.quantize(colors=160, method=Image.Quantize.MEDIANCUT)
    frames = [fr.quantize(palette=pal, dither=Image.Dither.NONE) for fr in frames]
    frames[0].save(a.out, save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True)
    print(f"{a.out}: {len(frames)} frames, final {final[me]:.0f} vs {final[op]:.0f}")


if __name__ == "__main__":
    main()
