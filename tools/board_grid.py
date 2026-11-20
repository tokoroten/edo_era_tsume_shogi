#!/usr/bin/env python3
"""Measure a printed shogi board grid and print a 9x9 ink map.

Usage:
    python tools/board_grid.py <pid> <rid> --region pct:X,Y,W,H

    [--width 1200] [--out FILE] [--threshold 0.5]

Detects the ten vertical and ten horizontal grid lines inside the region by
ink projection, snaps them to the nine ranks/files (falling back to even
spacing when a line is missed), prints the boundaries as image percentages
and the mean ink of every cell (r1 at top, f9 at right for a right page).
Saves an annotated JPEG when --out is given, so the grid can be checked by
eye before a cell is transcribed.
"""
import argparse
import io
import os
import urllib.request

import numpy as np
from PIL import Image, ImageDraw

UA = {"User-Agent": "edo-tsume-repro/1.0"}


def fetch(pid, rid, region, width):
    url = "https://dl.ndl.go.jp/api/iiif/%s/%s/%s/%d,/0/default.jpg" % (
        pid, rid, region, width)
    req = urllib.request.Request(url, headers=UA)
    data = urllib.request.urlopen(req, timeout=300).read()
    return Image.open(io.BytesIO(data)).convert("RGB")


def peaks(fractions, cutoff):
    found = [x for x in range(1, len(fractions) - 1)
             if fractions[x] > cutoff
             and fractions[x] >= fractions[x - 1]
             and fractions[x] >= fractions[x + 1]]
    groups = []
    for x in found:
        if groups and x - groups[-1][-1] <= 5:
            groups[-1].append(x)
        else:
            groups.append([x])
    return [sum(g) / float(len(g)) for g in groups]


def fit_lines(centres, size, count=10):
    """Build a uniform grid anchored on the outermost detected frame lines.

    Print skew makes every interior line an estimate: the matrix is meant to
    locate pieces to within a cell, and the annotated image is the check.
    """
    centres = sorted(c for c in centres if 4 <= c < size - 4)
    if len(centres) < 2:
        return [float(size - 1) * i / (count - 1) for i in range(count)]
    first, last = centres[0], centres[-1]
    if last - first < 0.5 * (size - 1):
        # frame partly outside the region: keep even spacing from one edge
        step = (size - 1) * 1.0 / (count - 1)
        if first < size / 2.0:
            last = first + step * (count - 1)
        else:
            first = last - step * (count - 1)
    return [first + (last - first) * i / float(count - 1)
            for i in range(count)]


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Measure a printed board grid and print a 9x9 ink map.")
    ap.add_argument("pid")
    ap.add_argument("rid")
    ap.add_argument("--region", required=True,
                    help="IIIF pct region, e.g. pct:47,28,45,56")
    ap.add_argument("--width", type=int, default=1200)
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    x0, y0, rw, rh = [float(v) for v in
                      args.region.replace("pct:", "").split(",")]
    im = fetch(args.pid, args.rid, args.region, args.width)
    w, h = im.size
    dark = np.array(im.convert("L")) < 120
    cols = fit_lines(peaks(dark.sum(axis=0) / float(h), args.threshold), w)
    rows = fit_lines(peaks(dark.sum(axis=1) / float(w), args.threshold), h)

    def pct_x(px):
        return x0 + rw * px / float(w - 1)

    def pct_y(px):
        return y0 + rh * px / float(h - 1)

    print("cols:", " ".join("%.2f" % pct_x(c) for c in cols))
    print("rows:", " ".join("%.2f" % pct_y(r) for r in rows))
    print("      " + " ".join("%4s" % ("f%d" % (9 - i)) for i in range(9)))
    for r in range(9):
        cells = []
        for i in range(9):
            x_lo, x_hi = cols[8 - i], cols[9 - i]
            y_lo, y_hi = rows[r], rows[r + 1]
            pad_x = max(2, int((x_hi - x_lo) * 0.12))
            pad_y = max(2, int((y_hi - y_lo) * 0.12))
            cell = dark[int(y_lo) + pad_y:int(y_hi) - pad_y,
                        int(x_lo) + pad_x:int(x_hi) - pad_x]
            cells.append("%4.2f" % (cell.mean() if cell.size else 0.0))
        print("r%d    " % (r + 1) + " ".join(cells))

    if args.out:
        sheet = im.copy()
        draw = ImageDraw.Draw(sheet)
        for c in cols:
            draw.line([(c, 0), (c, h)], fill=(255, 0, 0), width=2)
        for r in rows:
            draw.line([(0, r), (w, r)], fill=(255, 0, 0), width=2)
        sheet.save(args.out, quality=88)
        print("wrote", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
