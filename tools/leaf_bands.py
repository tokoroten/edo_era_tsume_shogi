#!/usr/bin/env python3
"""Split one NDL leaf region into readable horizontal bands.

Fetches the full-resolution canvas once, crops an optional horizontal range
(percent of the whole canvas), then cuts N horizontal bands and upscales each
to a fixed width. Useful because the raw scan is only ~1847 px per page, so
whole-page crops are unreadable; narrow column crops upscaled are readable.

Usage:
  python tools/leaf_bands.py 861217 R0000004 --page R --x0 70 --x1 78 \
      --bands 3 --width 900 --out C:/tmp/r4c

x0/x1 are percentages of the full canvas width (0-100). If omitted, the
whole selected page is used.
"""
import argparse
import io
import os
import sys
import urllib.request

from PIL import Image

UA = {"User-Agent": "edo-tsume-repro/1.0"}


def fetch_full(pid, rid, timeout=300):
    url = "https://dl.ndl.go.jp/api/iiif/%s/%s/full/full/0/default.jpg" % (
        pid, rid)
    req = urllib.request.Request(url, headers=UA)
    data = urllib.request.urlopen(req, timeout=timeout).read()
    return Image.open(io.BytesIO(data)).convert("L")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pid")
    ap.add_argument("rid")
    ap.add_argument("--page", choices=["L", "R", "B"], default="B")
    ap.add_argument("--x0", type=float, default=None,
                    help="left edge in percent of canvas width")
    ap.add_argument("--x1", type=float, default=None,
                    help="right edge in percent of canvas width")
    ap.add_argument("--y0", type=float, default=0.0)
    ap.add_argument("--y1", type=float, default=100.0)
    ap.add_argument("--bands", type=int, default=3)
    ap.add_argument("--width", type=int, default=900)
    ap.add_argument("--out", required=True, help="output prefix")
    args = ap.parse_args(argv)

    im = fetch_full(args.pid, args.rid)
    w, h = im.size

    if args.x0 is None or args.x1 is None:
        if args.page == "L":
            bx0, bx1 = 0, w // 2
        elif args.page == "R":
            bx0, bx1 = w // 2, w
        else:
            bx0, bx1 = 0, w
    else:
        bx0 = int(w * args.x0 / 100.0)
        bx1 = int(w * args.x1 / 100.0)

    by0 = int(h * args.y0 / 100.0)
    by1 = int(h * args.y1 / 100.0)
    cw = bx1 - bx0
    ch = by1 - by0

    d = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(d, exist_ok=True)
    n = args.bands
    for i in range(n):
        y0 = by0 + ch * i // n
        y1 = by0 + ch * (i + 1) // n
        band = im.crop((bx0, y0, bx1, y1))
        scale = args.width / float(cw)
        band = band.resize(
            (args.width, max(1, int((y1 - y0) * scale))), Image.LANCZOS)
        p = "%s_%d.jpg" % (args.out, i + 1)
        band.save(p, quality=92)
        print("%s  %dx%d" % (p, band.width, band.height))
    return 0


if __name__ == "__main__":
    sys.exit(main())
