#!/usr/bin/env python3
"""Render a board as a 9x9 contact sheet with file/rank rulers.

    python tools/board_sheet.py <pid> <rid> "pct:x,y,w,h" <width> \
        "<x0,dx,y0,dy>" <out.png>

The peak-series fit in ``board_fit`` sometimes locks onto a page's text
column and reports a first line one cell away from the board's real frame.
A wrong origin is hard to see in a single-cell crop, but obvious in this
sheet: if the printed lines do not coincide with the drawn borders, or a
glyph straddles two cells, the calibration is off.

Reading the sheet (not a fitted list of numbers) is what settled 精妙 66.
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


def pct_map(region, size):
    x0, y0, w, h = [float(v) for v in region.replace("pct:", "").split(",")]
    return (lambda p: (p - x0) / w * (size[0] - 1),
            lambda p: (p - y0) / h * (size[1] - 1))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pid")
    ap.add_argument("rid")
    ap.add_argument("region")
    ap.add_argument("width", type=int)
    ap.add_argument("grid", help="x0,dx,y0,dy in page percent")
    ap.add_argument("out")
    ap.add_argument("--cell", type=int, default=150)
    args = ap.parse_args(argv)

    im = fetch(args.pid, args.rid, args.region, args.width)
    px, py = pct_map(args.region, im.size)
    x0, dx, y0, dy = [float(v) for v in args.grid.split(",")]
    cell, pad, rul = args.cell, 4, 26
    side = rul + 9 * (cell + pad) + pad
    sheet = Image.new("L", (side, side), 255)
    d = ImageDraw.Draw(sheet)
    for rank in range(9):
        for col in range(9):
            box = (int(px(x0 + col * dx)), int(py(y0 + rank * dy)),
                   int(px(x0 + (col + 1) * dx)), int(py(y0 + (rank + 1) * dy)))
            ox = rul + pad + col * (cell + pad)
            oy = rul + pad + rank * (cell + pad)
            sheet.paste(im.crop(box).resize((cell, cell)), (ox, oy))
            d.rectangle([ox, oy, ox + cell, oy + cell], outline=128)
    for col in range(9):
        d.text((rul + pad + col * (cell + pad) + cell // 2 - 3, 8),
               str(9 - col), fill=0)
    for rank in range(9):
        d.text((8, rul + pad + rank * (cell + pad) + cell // 2 - 3),
               str(rank + 1), fill=0)
    sheet.save(args.out)
    print(args.out, sheet.size)


if __name__ == "__main__":
    sys.exit(main())
