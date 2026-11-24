#!/usr/bin/env python3
"""Render a board sheet from its *measured* rule positions.

    python tools/board_lines_sheet.py <pid> <rid> "pct:x,y,w,h" <width> \
        "<10 x positions>" "<10 y positions>" <out.png>

The peak-series fit assumes evenly spaced rules and can lock onto a text column;
the four-corner warp assumes a clean quad.  Woodblock pages are neither: the cell
width often grows toward the binding.  This tool takes the ten vertical and ten
horizontal rule positions as measured (e.g. from `peak` output) and cuts the 81
cells between them, so no regularity is assumed at all.

Both line lists are page percent, ascending, 10 values each.
"""
import argparse
import io
import sys
import urllib.request

from PIL import Image, ImageDraw

UA = {"User-Agent": "edo-tsume-repro/1.0"}


def fetch(pid, rid, region, width):
    url = "https://dl.ndl.go.jp/api/iiif/%s/%s/%s/%d,/0/default.jpg" % (
        pid, rid, region, width)
    data = urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=300).read()
    return Image.open(io.BytesIO(data)).convert("L")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pid")
    ap.add_argument("rid")
    ap.add_argument("region")
    ap.add_argument("width", type=int)
    ap.add_argument("xlines")
    ap.add_argument("ylines")
    ap.add_argument("out")
    ap.add_argument("--cell", type=int, default=150)
    args = ap.parse_args(argv)

    xs = [float(v) for v in args.xlines.replace(",", " ").split()]
    ys = [float(v) for v in args.ylines.replace(",", " ").split()]
    if len(xs) != 10 or len(ys) != 10:
        raise SystemExit("need 10 x and 10 y positions")
    im = fetch(args.pid, args.rid, args.region, args.width)
    x0p, y0p, rw, rh = [float(v) for v in args.region.replace("pct:", "").split(",")]
    W, H = im.size
    px = lambda p: (p - x0p) / rw * (W - 1)
    py = lambda p: (p - y0p) / rh * (H - 1)

    cell, pad, rul = args.cell, 4, 26
    side = rul + 9 * (cell + pad) + pad
    sheet = Image.new("L", (side, side), 255)
    d = ImageDraw.Draw(sheet)
    for r in range(9):
        for c in range(9):
            box = (int(px(xs[c])), int(py(ys[r])),
                   int(px(xs[c + 1])), int(py(ys[r + 1])))
            ox = rul + pad + c * (cell + pad)
            oy = rul + pad + r * (cell + pad)
            sheet.paste(im.crop(box).resize((cell, cell)), (ox, oy))
            d.rectangle([ox, oy, ox + cell, oy + cell], outline=128)
    for c in range(9):
        d.text((rul + pad + c * (cell + pad) + cell // 2 - 3, 8),
               str(9 - c), fill=0)
    for r in range(9):
        d.text((8, rul + pad + r * (cell + pad) + cell // 2 - 3),
               str(r + 1), fill=0)
    sheet.save(args.out)
    print(args.out, sheet.size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
