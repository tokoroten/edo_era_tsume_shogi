#!/usr/bin/env python3
"""Fit a board grid from the SFEN's known pieces (anchor fit).

    python tools/board_anchor_fit.py <pid> <rid> "pct:x,y,w,h" <width> "<sfen>"

The series fit in board_fit.py fails on pages where the binding rules
out-number the board lines.  This tool instead matches the *known* pieces of
the draft to ink blobs: it searches the column origin/spacing that puts the
greatest number of known files on a blob, and likewise for ranks.  Print the
result and feed it to tools/cellsheet.py (x0 dx y0 dy).
"""
import argparse
import io
import sys
import urllib.request

import numpy as np
from PIL import Image
from scipy import ndimage

UA = {"User-Agent": "edo-tsume-repro/1.0"}


def fetch(pid, rid, region, width):
    url = "https://dl.ndl.go.jp/api/iiif/%s/%s/%s/%d,/0/default.jpg" % (
        pid, rid, region, width)
    data = urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=300).read()
    return Image.open(io.BytesIO(data)).convert("L")


def known_cells(sfen):
    """(file, rank) of every non-'?' piece."""
    out = []
    for r, row in enumerate(sfen.split(" ")[0].split("/"), 1):
        c, i = [], 0
        while i < len(row):
            if row[i].isdigit():
                c.extend([""] * int(row[i]))
                i += 1
            elif row[i] == "+":
                c.append(row[i:i + 2])
                i += 2
            else:
                c.append(row[i])
                i += 1
        for ci, x in enumerate(c, 1):
            if x:
                out.append((10 - ci, r))
    return out


def blobs(a):
    lab, n = ndimage.label(a)
    if n == 0:
        return []
    objs = ndimage.find_objects(lab)
    sizes = ndimage.sum(a, lab, range(1, n + 1))
    h, w = a.shape
    out = []
    for k, sl in enumerate(objs):
        if sizes[k] < 150:
            continue
        ys, xs = sl
        hh, ww = ys.stop - ys.start, xs.stop - xs.start
        if hh < 12 or ww < 8 or hh > 0.8 * h or ww > 0.8 * w:
            continue
        out.append(((ys.start + ys.stop) / 2.0, (xs.start + xs.stop) / 2.0))
    return out


def fit_axis(known_coords, blob_centres, size, lo_frac, hi_frac, dmin, dmax, step=1):
    """Best (origin, spacing in px) putting the known coordinates on blobs."""
    best = None
    lo = lo_frac * size
    span = hi_frac * size - lo
    d = dmin
    while d <= dmax:
        for origin_i in range(0, 80, step):
            origin = lo + span * origin_i / 80.0
        for origin_i in range(0, 60, step):
            origin = lo + span * origin_i / 60.0
            hits = 0
            for c in known_coords:
                x = origin + c * d
                if x < 0 or x > size:
                    continue
                if any(abs(x - b) < 0.30 * d for b in blob_centres):
                    hits += 1
            if best is None or hits > best[0]:
                best = (hits, origin, d)
        d += 0.5
    return best


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pid")
    ap.add_argument("rid")
    ap.add_argument("region")
    ap.add_argument("width", type=int)
    ap.add_argument("sfen")
    ap.add_argument("--dx-range", default="1.5,4.5",
                    help="plausible cell width in page percent")
    ap.add_argument("--dy-range", default="3.4,6.5",
                    help="plausible cell height in page percent")
    args = ap.parse_args(argv)

    im = fetch(args.pid, args.rid, args.region, args.width)
    a = np.array(im) < 120
    h, w = a.shape
    x0p, y0p, rw, rh = [float(v) for v in args.region.replace("pct:", "").split(",")]
    bs = blobs(a)
    print("blobs:", len(bs))
    known = known_cells(args.sfen)
    files = sorted(set(9 - f for f, _ in known))          # 0 = file 9
    ranks = sorted(set(r - 1 for _, r in known))
    dminx, dmaxx = [float(v) for v in args.dx_range.split(",")]
    dminy, dmaxy = [float(v) for v in args.dy_range.split(",")]
    col = fit_axis(files, [b[1] for b in bs], w, 0.0, 1.0,
                   dminx / rw * w, dmaxx / rw * w)
    row = fit_axis(ranks, [b[0] for b in bs], h, 0.0, 1.0,
                   dminy / rh * h, dmaxy / rh * h)
    if not col or not row:
        print("no fit")
        return 1
    print("cells matched: cols %d/%d rows %d/%d"
          % (col[0], len(files), row[0], len(ranks)))
    # x0/dx are page percentages: origin so that cell i spans [x0+i*dx, ...]
    dxp, dyp = rw * col[2] / (w - 1), rh * row[2] / (h - 1)
    print("x0=%.2f dx=%.2f y0=%.2f dy=%.2f"
          % (x0p + rw * col[1] / (w - 1) - dxp / 2.0, dxp,
             y0p + rh * row[1] / (h - 1) - dyp / 2.0, dyp))
    return 0


if __name__ == "__main__":
    sys.exit(main())
