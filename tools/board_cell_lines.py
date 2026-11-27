#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""board_cell_lines.py — crop cells from a printed board by its measured rules.

Some pages are warped (page curvature, rectangular cells), so one global warp
cannot align all 81 cells.  When the ten vertical and ten horizontal rules have
been measured in page percent, each cell is the quadrilateral between two
adjacent rules; cropping that rectangle directly keeps every cell aligned.

The mapping defaults to ``row i = rank, column j = file``; use --transpose or
--flip-x/--flip-y for diagrams printed in other orientations.

Usage:
    python tools/board_cell_lines.py PID RID \
        "14.16,16.40,...,34.27" "46.56,...,85.13" "4,6;3,8;1,9" --out cells.png

Each rule list must hold ten page-percent positions.
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import board_cell_ink as b  # noqa: E402

KANJI = "一二三四五六七八九"


def _font(size):
    """Largest readable face available; the default bitmap font is far too
    small to label 160px tiles, which made earlier sheets easy to misread.
    A CJK face is required because the labels carry 漢数字."""
    for path in (r"C:\Windows\Fonts\msyh.ttc",
                 r"C:\Windows\Fonts\meiryo.ttc",
                 r"C:\Windows\Fonts\msgothic.ttc",
                 r"C:\Windows\Fonts\arialbd.ttf",
                 "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                pass
    return ImageFont.load_default()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("pid")
    ap.add_argument("rid")
    ap.add_argument("xs", help="ten vertical rules, page percent, left to right")
    ap.add_argument("ys", help="ten horizontal rules, page percent, top to bottom")
    ap.add_argument("cells", help="rank,file pairs separated by ';'")
    ap.add_argument("--out", default="cells.png")
    ap.add_argument("--width", type=int, default=3000)
    ap.add_argument("--pad", type=float, default=0.06,
                    help="fraction of a cell kept as margin")
    ap.add_argument("--shift", type=float, default=0.0,
                    help="move the crop window up by this fraction of a cell "
                         "(some figures print the glyph near the top rule)")
    ap.add_argument("--transpose", action="store_true")
    ap.add_argument("--flip-x", action="store_true")
    ap.add_argument("--flip-y", action="store_true")
    ap.add_argument("--sheet", action="store_true",
                    help="draw all 81 cells as a labelled 9x9 sheet")
    ap.add_argument("--tile", type=int, default=130, help="sheet tile height")
    args = ap.parse_args(argv)

    xs = [float(v) for v in args.xs.split(",")]
    ys = [float(v) for v in args.ys.split(",")]
    if len(xs) != 10 or len(ys) != 10:
        raise SystemExit("need ten rules in each list")
    want = []
    for part in args.cells.split(";"):
        rk, fl = part.split(",")
        want.append((int(rk), int(fl)))

    img = b.fetch(args.pid, args.rid, "pct:0,0,100,100", args.width).convert("L")
    W, H = img.size

    def cell_rect(rk, fl):
        i, j = rk - 1, fl - 1
        if args.transpose:
            i, j = j, i
        if args.flip_y:
            i = 8 - i
        if args.flip_x:
            j = 8 - j
        x0, x1 = xs[j], xs[j + 1]
        y0, y1 = ys[i], ys[i + 1]
        dy = (y1 - y0) * args.shift
        y0, y1 = y0 - dy, y1 - dy
        padx = (x1 - x0) * args.pad
        pady = (y1 - y0) * args.pad
        return (W * (x0 - padx) / 100.0, H * (y0 - pady) / 100.0,
                W * (x1 + padx) / 100.0, H * (y1 + pady) / 100.0)

    if args.sheet:
        t = args.tile
        ch = max(18, t // 5)
        f = _font(max(12, int(ch * 0.8)))
        sheet = Image.new("L", (9 * t + 20, 9 * (t + ch) + 20), 255)
        d = ImageDraw.Draw(sheet)
        for rk in range(1, 10):
            for fl in range(1, 10):
                box = cell_rect(rk, fl)
                im = img.crop(tuple(int(v) for v in box))
                im = im.resize((t - 2, t - 2), Image.LANCZOS)
                px, py = 10 + (fl - 1) * t, 10 + (rk - 1) * (t + ch)
                sheet.paste(im, (px, py))
                # the caption is the 筋段 this tile really is, so a mis-read
                # of the grid cannot be blamed on counting tiles by eye
                d.text((px + 2, py + t - 1), "%d%s" % (fl, KANJI[rk - 1]),
                       fill=0, font=f)
        sheet.save(args.out)
        print("wrote sheet", args.out, "caption = file + rank")
        return 0

    tiles = []
    for rk, fl in want:
        box = cell_rect(rk, fl)
        im = img.crop(tuple(int(v) for v in box))
        scale = 380.0 / im.height
        im = im.resize((max(1, int(im.width * scale)), 380), Image.LANCZOS)
        tiles.append(("r%d f%d" % (rk, fl), im))

    width = sum(max(t.width, 60) + 12 for _, t in tiles) + 12
    sheet = Image.new("L", (width, 460), 255)
    d = ImageDraw.Draw(sheet)
    f = _font(26)
    x = 8
    for label, tile in tiles:
        sheet.paste(tile, (x, 46))
        d.text((x, 8), label, fill=0, font=f)
        x += max(tile.width, 60) + 12
    sheet.save(args.out)
    print("wrote", args.out, [t[0] for t in tiles])
    return 0


if __name__ == "__main__":
    sys.exit(main())
