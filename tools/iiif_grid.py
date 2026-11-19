#!/usr/bin/env python3
"""Render an NDL leaf with a labelled percent grid (for picking crop regions).

Usage:
  python tools/iiif_grid.py 861216 R0000028 --width 1400 --out C:/tmp/g.jpg

Draws light lines every 5% and heavier lines every 10% with percent labels,
so a crop region can be read off the image directly and passed to
tools/iiif_crop.py (pct:x,y,w,h).
"""
import argparse
import io
import sys
import urllib.request

from PIL import Image, ImageDraw

UA = {"User-Agent": "edo-tsume-repro/1.0"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pid")
    ap.add_argument("rid")
    ap.add_argument("--width", type=int, default=1400)
    ap.add_argument("--step", type=int, default=5)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    url = "https://dl.ndl.go.jp/api/iiif/%s/%s/full/%d,/0/default.jpg" % (
        args.pid, args.rid, args.width)
    data = urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=300).read()
    im = Image.open(io.BytesIO(data)).convert("RGB")
    d = ImageDraw.Draw(im)
    w, h = im.size

    for p in range(0, 101, args.step):
        x = int(w * p / 100.0)
        y = int(h * p / 100.0)
        col = (255, 80, 80) if p % 10 == 0 else (120, 200, 255)
        d.line([(x, 0), (x, h)], fill=col, width=1)
        d.line([(0, y), (w, y)], fill=col, width=1)
        if p % 10 == 0:
            d.text((x + 2, 2), str(p), fill=(255, 0, 0))
            d.text((2, y + 2), str(p), fill=(255, 0, 0))
    im.save(args.out, quality=90)
    print("%s  %dx%d" % (args.out, w, h))
    return 0


if __name__ == "__main__":
    sys.exit(main())
