#!/usr/bin/env python3
"""Render a board as a 9x9 sheet from its four corners (projective-ish).

    python tools/board_quad_sheet.py <pid> <rid> "pct:x,y,w,h" <width> \
        "<UL: x,y LL: x,y LR: x,y UR: x,y>" <out.png>

The peak-series fit spreads nine cells over ten detected lines when a text
column sits just left of the board, so ``dx`` comes out 9/8 too large and every
cell drifts.  When that happens (精妙 48, 65, 18) the only reliable way in is to
name the board's four frame corners and warp the quad to a square.  PIL's QUAD
transform is bilinear, which is exact enough for the slight trapezoid of a
woodblock page.

Prints nothing but writes the sheet; cells are labelled with file (9..1) and
rank (1..9) exactly as ``tools/board_sheet.py`` does.
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


def parse_corners(text):
    nums = [float(v) for v in text.replace(":", ",").replace(" ", ",").split(",")
            if v.strip()]
    if len(nums) != 8:
        raise argparse.ArgumentTypeError("need 8 numbers (UL LL LR UR)")
    return [(nums[i], nums[i + 1]) for i in range(0, 8, 2)]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pid")
    ap.add_argument("rid")
    ap.add_argument("region")
    ap.add_argument("width", type=int)
    ap.add_argument("corners")
    ap.add_argument("out")
    ap.add_argument("--cell", type=int, default=150)
    args = ap.parse_args(argv)

    im = fetch(args.pid, args.rid, args.region, args.width)
    x0p, y0p, rw, rh = [float(v) for v in args.region.replace("pct:", "").split(",")]
    W, H = im.size
    px = lambda p: (p - x0p) / rw * (W - 1)
    py = lambda p: (p - y0p) / rh * (H - 1)
    ul, ll, lr, ur = parse_corners(args.corners)
    data = (px(ul[0]), py(ul[1]), px(ll[0]), py(ll[1]),
            px(lr[0]), py(lr[1]), px(ur[0]), py(ur[1]))
    sq = im.transform((900, 900), Image.QUAD, data=data,
                      resample=Image.BILINEAR)

    cell, pad, rul = args.cell, 4, 26
    side = rul + 9 * (cell + pad) + pad
    sheet = Image.new("L", (side, side), 255)
    d = ImageDraw.Draw(sheet)
    for rank in range(9):
        for col in range(9):
            ox = rul + pad + col * (cell + pad)
            oy = rul + pad + rank * (cell + pad)
            sheet.paste(sq.crop((col * 100, rank * 100,
                                 (col + 1) * 100, (rank + 1) * 100))
                        .resize((cell, cell)), (ox, oy))
            d.rectangle([ox, oy, ox + cell, oy + cell], outline=128)
    for col in range(9):
        d.text((rul + pad + col * (cell + pad) + cell // 2 - 3, 8),
               str(9 - col), fill=0)
    for rank in range(9):
        d.text((8, rul + pad + rank * (cell + pad) + cell // 2 - 3),
               str(rank + 1), fill=0)
    sheet.save(args.out)
    print(args.out, sheet.size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
