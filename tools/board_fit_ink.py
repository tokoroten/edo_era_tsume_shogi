#!/usr/bin/env python3
"""Fit a board grid by maximising ink inside the known pieces' cell centres.

    python tools/board_fit_ink.py <pid> <rid> "pct:x,y,w,h" <width> "<sfen>" \
        "<x0,dx,y0,dy>"

Unlike ``board_fit`` (which counts lines) and ``board_anchor_fit`` (which
matches blobs), this scores a candidate grid by how much ink falls in the
**central half** of every cell that the draft says holds a piece.  A glyph
straddling two cells scores low; only a grid that centres every known piece
scores high.  No centroid is computed, so neighbouring strokes and the rules
themselves cannot drag the fit away.

The starting grid is usually ``board_fit``'s output; the search moves it by a
few percent, so it also recovers a fit that is one cell off (try both).
Prints x0 dx y0 dy in page percent for tools/board_sheet.py.
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


def known_cells(sfen):
    """(col0, row0) for every piece the draft knows; col0 0 is the left edge."""
    out = []
    for r, row in enumerate(sfen.split(" ")[0].split("/")):
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
        for ci, x in enumerate(c):
            if x and x != "?":
                out.append((ci, r))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pid")
    ap.add_argument("rid")
    ap.add_argument("region")
    ap.add_argument("width", type=int)
    ap.add_argument("sfen")
    ap.add_argument("grid", help="starting x0,dx,y0,dy in page percent")
    args = ap.parse_args(argv)

    im = fetch(args.pid, args.rid, args.region, args.width)
    a = np.asarray(im) < 140
    h, w = a.shape
    x0p, y0p, rw, rh = [float(v) for v in args.region.replace("pct:", "").split(",")]
    cells = known_cells(args.sfen)
    x0, dx, y0, dy = [float(v) for v in args.grid.split(",")]
    X0 = (x0 - x0p) / rw * (w - 1)
    DX = dx / rw * (w - 1)
    Y0 = (y0 - y0p) / rh * (h - 1)
    DY = dy / rh * (h - 1)

    def score(X0, DX, Y0, DY):
        s = 0.0
        for c, r in cells:
            xl = X0 + (c + 0.25) * DX
            xr = X0 + (c + 0.75) * DX
            yt = Y0 + (r + 0.25) * DY
            yb = Y0 + (r + 0.75) * DY
            if xl < 0 or yt < 0 or xr >= w or yb >= h:
                continue
            s += a[int(yt):int(yb), int(xl):int(xr)].sum()
        return s

    def sweep(X0, DX, Y0, DY, rx, rd, steps):
        best = (score(X0, DX, Y0, DY), X0, DX, Y0, DY)
        for k in range(1, steps + 1):
            f = rx * k / steps
            for sx in (1.0 - f, 1.0, 1.0 + f):
                for sd in (1.0 - rd * k / steps, 1.0, 1.0 + rd * k / steps):
                    s = score(X0 * sx, DX * sd, Y0, DY)
                    if s > best[0]:
                        best = (s, X0 * sx, DX * sd, Y0, DY)
            for sy in (1.0 - f, 1.0, 1.0 + f):
                for sd in (1.0 - rd * k / steps, 1.0, 1.0 + rd * k / steps):
                    s = score(best[1], best[2], Y0 * sy, DY * sd)
                    if s > best[0]:
                        best = (s, best[1], best[2], Y0 * sy, DY * sd)
            X0, DX, Y0, DY = best[1:]
        return best

    best = (score(X0, DX, Y0, DY), X0, DX, Y0, DY)
    for _ in range(3):
        best = sweep(best[1], best[2], best[3], best[4], 0.04, 0.06, 8)
    _, X0, DX, Y0, DY = best
    to_pct = lambda v, off, span, size: off + span * v / (size - 1)
    print("cells %d score %.0f  x0=%.2f dx=%.3f y0=%.2f dy=%.3f"
          % (len(cells), best[0], to_pct(X0, x0p, rw, w), rw * DX / (w - 1),
             to_pct(Y0, y0p, rh, h), rh * DY / (h - 1)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
