#!/usr/bin/env python3
"""Fit a 9x9 shogi board grid from ink-projection peaks.

    python tools/board_fit.py 861216 R0000041 "pct:51,28,35,55" 1400

Prints the ten column and ten row lines (page percentages) of the arithmetic
series that best matches the detected ink peaks.  Use the result as the frame:
file f is column index 9-f (leftmost = file 9), rank r is row r, and a cell is
  x in [cols[9-f], cols[10-f]], y in [rows[r-1], rows[r]].

Unlike peak picking alone this survives a missing line, and unlike blob
centroids it is not disturbed by glyphs touching the grid.
"""
import argparse
import io
import sys
import urllib.request

import numpy as np
from PIL import Image

UA = {"User-Agent": "edo-tsume-repro/1.0"}


def fetch(pid, rid, region, width):
    url = "https://dl.ndl.go.jp/api/iiif/%s/%s/%s/%d,/0/default.jpg" % (
        pid, rid, region, width)
    data = urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=300).read()
    return Image.open(io.BytesIO(data)).convert("L")


def peaks_of(frac, rel=0.35):
    idx = np.where(frac > rel * frac.max())[0]
    groups = []
    for i in idx:
        if groups and i - groups[-1][-1] <= 6:
            groups[-1].append(i)
        else:
            groups.append([i])
    return [sum(g) / float(len(g)) for g in groups if len(g)]


def series(pk, size):
    """Best arithmetic series of ten lines through the peaks."""
    best = None
    for i in range(len(pk)):
        for j in range(i + 1, len(pk)):
            for k in range(1, 10):
                dx = (pk[j] - pk[i]) / float(k)
                if not (0.055 * size < dx < 0.15 * size):
                    continue
                for m in range(10):
                    p0 = pk[i] - m * dx
                    if p0 < -2 or p0 + 9 * dx > size + 2:
                        continue
                    lines = [p0 + t * dx for t in range(10)]
                    n = sum(1 for q in pk
                            if min(abs(q - L) for L in lines) < 0.22 * dx)
                    score = (n, dx)
                    if best is None or score > best[0]:
                        best = (score, lines)
    return best[1], best[0][0]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pid")
    ap.add_argument("rid")
    ap.add_argument("region", help="IIIF pct region, e.g. pct:51,28,35,55")
    ap.add_argument("width", type=int, nargs="?", default=1400)
    args = ap.parse_args(argv)

    im = fetch(args.pid, args.rid, args.region, args.width)
    a = np.array(im) < 120
    h, w = a.shape
    x0, y0, rw, rh = [float(v) for v in args.region.replace("pct:", "").split(",")]
    cols, cn = series(peaks_of(a.sum(axis=0) / float(h)), w)
    rows, rn = series(peaks_of(a.sum(axis=1) / float(w)), h)
    print("cols pct:", " ".join("%.2f" % (x0 + rw * c / (w - 1)) for c in cols),
          "matched", cn)
    print("rows pct:", " ".join("%.2f" % (y0 + rh * r / (h - 1)) for r in rows),
          "matched", rn)
    return 0


if __name__ == "__main__":
    sys.exit(main())
