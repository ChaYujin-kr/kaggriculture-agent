"""Original 16x16 pixel-art tiles for replay GIFs (drawn for this repo; no third-party art).

tile_image(tile, x, y, size) returns an RGB image of one farm tile; person_image(is_farmer, size) an RGBA
figure to paste on top. Objects get an automatic dark outline so they read at small sizes.
"""
import random

from PIL import Image

PAL = {
    "d": (138, 90, 54), "D": (107, 66, 40), "l": (168, 116, 74),           # tilled soil
    "g": (111, 174, 75), "G": (79, 138, 54), "h": (143, 204, 94),           # grass
    "f": (47, 74, 44), "F": (34, 54, 31), "k": (62, 94, 56),                 # forest (locked)
    "y": (232, 192, 80), "Y": (201, 154, 46), "w": (245, 221, 136),         # wheat
    "o": (238, 138, 42), "O": (197, 100, 20),                                # carrot
    "v": (92, 173, 60), "V": (61, 130, 40),                                  # leaves
    "r": (216, 64, 58), "R": (168, 42, 38), "p": (240, 122, 106),           # tomato
    "m": (124, 194, 87), "M": (79, 143, 54), "n": (58, 110, 40),            # melon
    "s": (232, 74, 106), "S": (180, 44, 74), "c": (247, 226, 122),          # strawberry
    "e": (86, 100, 46), "E": (60, 71, 32),                                   # weed
    "b": (156, 106, 60), "B": (110, 69, 36), "q": (184, 69, 58), "Q": (138, 47, 40),  # wood, roof
    "W": (244, 241, 230), "a": (189, 184, 168), "K": (42, 38, 34), "P": (242, 167, 167),
    "j": (240, 154, 42), "x": (216, 51, 42), "u": (236, 228, 204), "z": (216, 69, 58),
    "H": (217, 178, 90), "t": (241, 201, 160), "i": (58, 100, 184), "I": (107, 143, 214),
    "#": (43, 32, 25), "T": (217, 184, 106),
}
OUTLINE = (43, 32, 25, 255)

SPROUT = [
    "................", "................", "................", "................",
    "................", "................", "......v..v......", ".....vvv.vv.....",
    "......vvvv......", ".......VV.......", ".......VV.......", "................",
    "................", "................", "................", "................"]
WHEAT = [
    "................", "...w...w....w...", "..wyw.wyw..wyw..", "..yYy.yYy..yYy..",
    "..yYy.yYy..yYy..", "...Y..yYy...Y...", "...Y...Y....Y...", "...v...Y....v...",
    "..vv...v...vv...", "...v..vv....v...", "...V...v....V...", "...V...V....V...",
    "................", "................", "................", "................"]
CARROT = [
    "................", "...v.v.....v.v..", "..vVvVv...vVvVv.", "...vVv.....vVv..",
    "....V.......V...", "...oOo.....oOo..", "...oOo.....oOo..", "....o.......o...",
    "................", "......v.v.......", ".....vVvVv......", "......vVv.......",
    ".......V........", "......oOo.......", "......oOo.......", ".......o........"]
TOMATO = [
    ".......b........", "......vbv.......", ".....vvbvv......", "....rp.b.v......",
    "....rR.bvrp.....", ".....v.b.rR.....", "....vvvbvv......", "...rp..b..v.....",
    "...rR.vbv.rp....", "....v..b..rR....", "...vvv.b.vvv....", ".......b........",
    ".......B........", "................", "................", "................"]
MELON = [
    "................", "................", "...v.......v....", "..vVv.....vVv...",
    "...V...V...V....", "....VVVmmmm.....", "....mmnmmnmm....", "...mmnmmnmmnm...",
    "...mnmmnmmnmm...", "...mmnmmnmmnm...", "....mnmmnmmn....", ".....MMMMMM.....",
    "................", "................", "................", "................"]
STRAWBERRY = [
    "................", "....v.v..v.v....", "...vVvVvvVvVv...", "....vVv..vVv....",
    ".....V....V.....", "....sSs..sSs....", "...scsS..sScs...", "...sSsS..sSsS...",
    "....sS....sS....", ".....S.....S....", "......v.v.......", ".....vVvVv......",
    "......sSs.......", ".....scsSs......", "......sS........", "................"]
WEED = [
    "................", "................", "...e.....e..e...", "..eEe..e.Ee.e...",
    "...E..eEe.E.E...", "..e.E..E..EeE...", ".eEeE.eEe..E..e.", "..EE...E..eEe.E.",
    "...E..eEe..E.eE.", "..eEe..E..eEeE..", "...E...E...E.E..", "................",
    "................", "................", "................", "................"]
COW = [
    "................", "................", "................", "............a.a.",
    "..WWKKWWWWW.WWWW", ".WWKKKWWKKWWKWWK", ".WWWKWWWKKWWWWPP", ".WWWWWWWWWWWWWPK",
    ".WWKKWWWWWWWWW..", "..WKKWWWKWWWW...", "..W.W....W.W....", "..K.K....K.K....",
    "................", "................", "................", "................"]
SHEEP = [
    "................", "................", "................", "....uuuuuuu.....",
    "...uuuuuuuuuu...", "..uuuuuuuuuuuKK.", "..uuuuuuuuuuKKKK", "..uuuuuuuuuuKWKK",
    "..uuuuuuuuuuuKK.", "...uuuuuuuuuu...", "....K.K...K.K...", "....K.K...K.K...",
    "................", "................", "................", "................"]
GOOSE = [
    "................", "................", "..........WW....", ".........WWKW...",
    ".........WWWjj..", ".........WW.....", "........WW......", "...WWWWWWW......",
    "..WWWaWWWW......", "..WWWaaWWW......", "...WWWWWW.......", "....j...j.......",
    "...jj..jj.......", "................", "................", "................"]
CHICKEN = [
    "................", "................", "................", "..........xx....",
    ".........WWWx...", ".........WKWjj..", ".........WWW....", "...WW...WWW.....",
    "..WWWWWWWWW.....", "..WWaaWWWWW.....", "...WWaWWWW......", "....WWWWW.......",
    ".....j..j.......", "....jj.jj.......", "................", "................"]
COOP = [
    "................", "......QQQQ......", ".....QqqqqQ.....", "....QqqqqqqQ....",
    "...QqqqqqqqqQ...", "..QQQQQQQQQQQQ..", "...bbbbbbbbbb...", "...bBbbBBbbBb...",
    "...bbbbKKbbbb...", "...bBbbKKbbBb...", "...bbbbKKbbbb...", "...BBBBBBBBBB...",
    "................", "................", "................", "................"]
PERSON = [
    "................", "......HHHH......", ".....HHHHHH.....", "....HHHHHHHH....",
    "......tttt......", "......tKtK......", "......tttt......", ".....zziizz.....",
    "....tziiiizt....", "......iiii......", "......iiii......", "......i..i......",
    "......B..B......", "................", "................", "................"]

READY = {"WHEAT": WHEAT, "CARROT": CARROT, "TOMATO": TOMATO, "MELON": MELON, "STRAWBERRY": STRAWBERRY}
ANIMALS = {"COW": COW, "SHEEP": SHEEP, "GOOSE": GOOSE, "CHICKEN": CHICKEN}
_cache = {}


def _sprite(rows, swap=None):
    """16x16 RGBA from a char map, with a 1px dark outline around opaque pixels."""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = im.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                ch = (swap or {}).get(ch, ch)
                px[x, y] = PAL[ch] + (255,)
    out = im.copy()
    po = out.load()
    for y in range(16):
        for x in range(16):
            if px[x, y][3] == 0 and any(0 <= x + dx < 16 and 0 <= y + dy < 16 and px[x + dx, y + dy][3]
                                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                po[x, y] = OUTLINE
    return out


def _base(kind, x, y, wet=False):
    """Textured 16x16 ground, seeded by tile position so it does not flicker between frames."""
    rnd = random.Random(x * 31 + y * 17 + len(kind) * 101)
    im = Image.new("RGB", (16, 16))
    px = im.load()
    if kind == "soil":
        a, b, c = (PAL["D"], PAL["d"], PAL["l"]) if not wet else ((84, 52, 32), (104, 66, 42), (122, 82, 54))
        for yy in range(16):
            for xx in range(16):
                px[xx, yy] = a if yy % 4 == 3 else (c if rnd.random() < .08 else b)
    elif kind in ("grass", "pasture"):
        for yy in range(16):
            for xx in range(16):
                r = rnd.random()
                px[xx, yy] = PAL["h"] if r < .07 else (PAL["G"] if r < .2 else PAL["g"])
        if kind == "pasture":
            for xx in range(16):
                px[xx, 1] = PAL["b"]
            for xx in (1, 8, 15):
                for yy in range(0, 4):
                    px[xx, yy] = PAL["B"]
    elif kind == "forest":
        for yy in range(16):
            for xx in range(16):
                px[xx, yy] = PAL["F"] if rnd.random() < .5 else PAL["f"]
        for _ in range(3):
            cx, cy = rnd.randrange(2, 14), rnd.randrange(2, 14)
            for yy in range(16):
                for xx in range(16):
                    if (xx - cx) ** 2 + (yy - cy) ** 2 <= 9:
                        px[xx, yy] = PAL["k"] if (xx - cx) + (yy - cy) < 0 else PAL["f"]
    elif kind == "straw":
        for yy in range(16):
            for xx in range(16):
                px[xx, yy] = PAL["T"] if rnd.random() > .15 else PAL["Y"]
        for i in range(16):
            px[i, 0] = px[i, 15] = px[0, i] = px[15, i] = PAL["B"]
    return im


def tile_image(t, x, y, size=32):
    if t == "LOCKED":
        key, base, obj = ("L", x, y), ("forest", False), None
    elif not isinstance(t, dict):
        key, base, obj = ("G", x, y), ("grass", False), None
    else:
        kind = t.get("kind")
        if kind == "PLANT":
            ready = (t.get("yield_units") or 0) > 0
            wet = bool(t.get("watered_today"))
            crop = t.get("crop")
            key = ("P", crop, ready, wet, x, y)
            base, obj = ("soil", wet), (READY.get(crop, SPROUT) if ready else SPROUT)
        elif kind == "WEED":
            key, base, obj = ("W", x, y), ("grass", False), WEED
        elif kind == "PASTURE":
            key = ("A", t.get("animal"), x, y)
            base, obj = ("pasture", False), ANIMALS.get(t.get("animal"))
        elif kind == "COOP":
            key = ("C", t.get("animal"), x, y)
            base, obj = ("straw", False), ANIMALS.get(t.get("animal")) or COOP
        else:
            key, base, obj = ("G", x, y), ("grass", False), None
    key = key + (size,)
    if key not in _cache:
        im = _base(base[0], x, y, base[1]).convert("RGBA")
        if obj:
            im.alpha_composite(_sprite(obj))
        _cache[key] = im.convert("RGB").resize((size, size), Image.NEAREST)
    return _cache[key]


def person_image(is_farmer, size=32):
    key = ("person", is_farmer, size)
    if key not in _cache:
        swap = None if is_farmer else {"H": "Y", "i": "I", "z": "v"}
        _cache[key] = _sprite(PERSON, swap).resize((size, size), Image.NEAREST)
    return _cache[key]


def sheet(path, size=48):
    """Contact sheet of every tile type, for checking the art."""
    demo = ["LOCKED", None,
            {"kind": "PLANT", "crop": "WHEAT", "yield_units": 0}, {"kind": "PLANT", "crop": "WHEAT", "yield_units": 0, "watered_today": True}]
    demo += [{"kind": "PLANT", "crop": c, "yield_units": 1} for c in READY]
    demo += [{"kind": "WEED"}] + [{"kind": "PASTURE", "animal": a} for a in ("COW", "SHEEP")]
    demo += [{"kind": "COOP"}] + [{"kind": "COOP", "animal": a} for a in ("GOOSE", "CHICKEN")]
    im = Image.new("RGB", (size * 8, size * 2 + size), (246, 247, 242))
    for i, t in enumerate(demo):
        im.paste(tile_image(t, i, 0, size), ((i % 8) * size, (i // 8) * size))
    im.paste(person_image(True, size), (0, size * 2), person_image(True, size))
    im.paste(person_image(False, size), (size, size * 2), person_image(False, size))
    im.save(path)


if __name__ == "__main__":
    import sys
    sheet(sys.argv[1] if len(sys.argv) > 1 else "sprites.png")
