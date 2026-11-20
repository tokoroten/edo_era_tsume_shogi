#!/usr/bin/env python3
"""Render a leaf with detected columns numbered, as a proof sheet.

Usage:
    python tools/column_sheet.py <pid> <rid> [--width 1400] [--out FILE]

Uses the same density rule as tools/find_columns.py, draws a vertical line at
each column start/end with its index and percent range, so a reader can say
"column 7" instead of estimating percentages from a grid. Saves a JPEG and
prints the column table.
"""
import argparse
import io
import os
import sys
import urllib.request

import numpy as np
from PIL import Image, ImageDraw

UA = {"User-Agent": "edo-tsume-repro/1.0"}


def fetch(pid, rid, timeout=300):
    url = "https://dl.ndl.go.jp/api/iiif/%s/%s/full/full/0/default.jpg" % (
        pid, rid)
    req = urllib.request.Request(url, headers=UA)
    data = urllib.request.urlopen(req, timeout=timeout).read()
    return Image.open(io.BytesIO(data)).convert("RGB")


def columns(im, y0=10.0, y1=90.0, min_gap=6):
    w, h = im.size
    top, bot = int(h * y0 / 100.0), int(h * y1 / 100.0)
    a = np.array(im.convert("L").crop((0, top, w, bot)))
    ink = a < 110
    prof = ink.sum(axis=0) / float(max(1, a.shape[0]))
    on = (prof > 0.03) & (prof < 0.60)
    runs = []
    start = None
    last = None
    for x, v in enumerate(on):
        if v:
            if start is None:
                start = x
            last = x
        elif start is not None and x - last > min_gap:
            runs.append((start, last))
            start = None
    if start is not None:
        runs.append((start, last))
    return [r for r in runs if r[1] - r[0] > 30]


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Render a leaf with detected columns numbered, as a proof sheet.")
    ap.add_argument("pid")
    ap.add_argument("rid")
    ap.add_argument("--width", type=int, default=1400)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    pid, rid, width, out = args.pid, args.rid, args.width, args.out
    im = fetch(pid, rid)
    w, h = im.size
    cols = columns(im)
    im = im.resize((width, int(h * width / float(w))), Image.LANCZOS)
    w2, h2 = im.size
    d = ImageDraw.Draw(im)
    print("columns:", len(cols))
    for i, (a, b) in enumerate(cols, 1):
        xa = int(a * w2 / float(w))
        xb = int(b * w2 / float(w))
        d.line([(xa, 0), (xa, h2)], fill=(255, 0, 0), width=2)
        d.line([(xb, 0), (xb, h2)], fill=(255, 0, 0), width=2)
        d.text((xa + 3, 4), "c%d" % i, fill=(255, 0, 0))
        print("  c%-2d %5.1f-%5.1f%%" % (i, 100.0 * a / w, 100.0 * b / w))
    if out is None:
        out = os.path.join(os.environ.get("TEMP", "."),
                           "%s_%s_sheet.jpg" % (pid, rid))
    im.save(out, quality=88)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
