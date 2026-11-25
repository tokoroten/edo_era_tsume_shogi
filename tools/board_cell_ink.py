#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Measure the ink fraction of every board cell after warping the frame square.

    python tools/board_cell_ink.py <pid> <rid> "pct:x,y,w,h" \
        "ulx,uly,urx,ury,lrx,lry,llx,lly" [--draft seimyo:75] [--out sq.png]

Why this exists
---------------
Reading a cell by eye from a wide crop is how two misreads happened: the cell
was off by one file and the "blank" square was really paper beside the glyph.
Measuring the ink inside each cell instead gives numbers that do not depend on
where the reader thinks the cell is:

  * empty cells sit at 0.00-0.05,
  * a tokin (と) prints at about 0.12-0.22,
  * a promoted great piece (馬, 龍) at 0.30 and above.

So the tool answers two questions at once: does the *occupancy* match the draft,
and is an unknown glyph light (と) or heavy (馬/龍 class).

Ink is measured against the cell's own median, which keeps the reading stable
across faded and dark pages but means a cell more than half covered in ink
reads as zero.  Printed pieces sit well below that (0.13-0.49 measured), so the
cap has not bitten; it is stated here because it is the one way this tool can
lie.

The frame is warped with a bilinear QUAD transform, which is enough for the
slight trapezoid of a woodblock page.  Give the four corners in page percent,
clockwise from the upper left, and the transform maps them to a square.  If the
draft is supplied the printed grid is labelled with the draft's pieces, which
makes a one-file error obvious at a glance.
"""
import argparse
import io
import sys
import urllib.request

import numpy as np
from PIL import Image

UA = {"User-Agent": "edo-tsume-repro/1.0"}
SIDE = 1800
MARGIN = 40


def fetch(pid, rid, region, width):
    url = "https://dl.ndl.go.jp/api/iiif/%s/%s/%s/%d,/0/default.jpg" % (
        pid, rid, region, width)
    req = urllib.request.Request(url, headers=UA)
    return Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=300).read())).convert("L")


def sfen_grid(sfen):
    """Return a 9x9 list of piece strings from an SFEN position field."""
    rows = sfen.split()[0].split("/")
    if len(rows) != 9:
        raise ValueError("SFEN must have nine ranks")
    out = []
    for row in rows:
        line, i = [], 0
        while i < len(row):
            ch = row[i]
            if ch.isdigit():
                line += [""] * int(ch)
                i += 1
            elif ch == "+":
                line.append("+" + row[i + 1])
                i += 2
            else:
                line.append(ch)
                i += 1
        if len(line) != 9:
            raise ValueError("rank %r does not have nine files" % row)
        out.append(line)
    return out


def ink_matrix(img, side=SIDE, margin=MARGIN, dx=0.0, dy=0.0, scale=1.0):
    """Ink fraction per cell; dx/dy shift the grid and scale stretches it.

    A cell whose window would fall outside the square is marked -1.0 (not
    judged) rather than wrapped round to the other edge.  `scale` expands the
    grid about the centre, which is what a corners estimate taken slightly
    outside the printed rule needs (贯珠 and some 精妙 pages).
    """
    a = np.asarray(img).astype(np.float32)
    cells = np.zeros((9, 9))
    step = side / 9.0
    cell = step * scale
    ox = (side - 9.0 * cell) / 2.0 + dx * step
    oy = (side - 9.0 * cell) / 2.0 + dy * step
    for r in range(9):
        for c in range(9):
            y0 = int(r * cell + oy) + margin
            y1 = int((r + 1) * cell + oy) - margin
            x0 = int(c * cell + ox) + margin
            x1 = int((c + 1) * cell + ox) - margin
            if y0 < 0 or x0 < 0 or y1 > side or x1 > side or y1 <= y0 or x1 <= x0:
                cells[r, c] = -1.0
                continue
            sub = a[y0:y1, x0:x1]
            thr = np.percentile(sub, 50) - 30
            cells[r, c] = float((sub < thr).mean())
    return cells


def agreement(cells, grid):
    """Count cells whose inked/blank state matches the draft's occupied/empty.

    This is one-sided evidence, as everywhere in this project: a high score
    supports the draft's *placement*, a low one proves nothing (a warped or
    faded page scores low with the correct board).
    """
    ok = total = 0
    for r in range(9):
        for c in range(9):
            if cells[r, c] < 0:
                continue
            total += 1
            if (cells[r, c] >= 0.10) == bool(grid[r][c]):
                ok += 1
    return ok, total


def warp(img, region, corners, side=SIDE):
    x0p, y0p, rw, rh = [float(v) for v in region.replace("pct:", "").split(",")]
    W, H = img.size
    px = lambda p: (p - x0p) / rw * (W - 1)
    py = lambda p: (p - y0p) / rh * (H - 1)
    (ulx, uly), (urx, ury), (lrx, lry), (llx, lly) = corners
    data = (px(ulx), py(uly), px(llx), py(lly),
            px(lrx), py(lry), px(urx), py(ury))
    return img.transform((side, side), Image.QUAD, data=data, resample=Image.BICUBIC)


def mirror_grid(grid):
    """File-reverse a 9x9 piece grid.

    gyokuzu numbers its files from the left, so its drafts line up with the
    printed board only after reversing the columns (see docs/ink-evidence.md).
    """
    return [list(reversed(row)) for row in grid]


def parse_corners(text):
    nums = [float(v) for v in text.replace(" ", ",").split(",") if v.strip()]
    if len(nums) != 8:
        raise argparse.ArgumentTypeError("need 8 numbers: ulx,uly,urx,ury,lrx,lry,llx,lly")
    return [(nums[i], nums[i + 1]) for i in range(0, 8, 2)]


def load_draft(spec):
    import json
    import os
    coll, num = spec.split(":")
    base = {
        "seimyo": ("edo", "seimyo"),
        "kanju": ("meiji", "kanju"),
        "zukou": ("edo", "zukou"),
        "musou": ("edo", "musou"),
        "gyokuzu": ("edo", "gyokuzu"),
        "kinza": ("edo", "kinza"),
        "meijin": ("taisho", "meijin"),
        "shiroto": ("taisho", "shiroto"),
    }[coll]
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(root, "collections", base[0], base[1], "drafts", "%03d.json" % int(num))
    rec = json.load(io.open(p, encoding="utf-8"))
    return rec["sfen"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pid")
    ap.add_argument("rid")
    ap.add_argument("region", help="fetch region, e.g. pct:47,30,36,50")
    ap.add_argument("corners", type=parse_corners,
                    help="frame corners in page percent: ulx,uly,urx,ury,lrx,lry,llx,lly")
    ap.add_argument("--draft", help="collection:number, e.g. seimyo:75")
    ap.add_argument("--out", help="save the warped square here")
    ap.add_argument("--width", type=int, default=2000, help="IIIF fetch width (default 2000)")
    ap.add_argument("--shift", metavar="DX,DY",
                    help="apply a sampling shift in cell fractions, e.g. 0,0.2")
    ap.add_argument("--scale", type=float, default=1.0,
                    help="stretch the sampling grid about the centre (default 1.0)")
    ap.add_argument("--search", action="store_true",
                    help="with --draft: try shifts of +-0.4 cell and report the best agreement")
    ap.add_argument("--mirror", action="store_true",
                    help="with --draft: the book numbers files from the left "
                         "(gyokuzu), so compare against the file-reversed draft")
    args = ap.parse_args(argv)

    img = fetch(args.pid, args.rid, args.region, args.width)
    sq = warp(img, args.region, args.corners)
    if args.out:
        sq.save(args.out)
    dx, dy = 0.0, 0.0
    if args.shift:
        dx, dy = [float(v) for v in args.shift.split(",")]
    cells = ink_matrix(sq, dx=dx, dy=dy, scale=args.scale)

    grid = sfen_grid(load_draft(args.draft)) if args.draft else [[""] * 9 for _ in range(9)]
    if args.mirror:
        grid = mirror_grid(grid)
    print("      " + " ".join("f%d    " % (c + 1 if args.mirror else 9 - c) for c in range(9)))
    for r in range(9):
        row = []
        for c in range(9):
            piece = grid[r][c] or "."
            row.append("%s%.2f" % (piece.ljust(3), cells[r, c]))
        print("r%d " % (r + 1) + " ".join(row))

    filled = [(r + 1, 9 - c, cells[r, c]) for r in range(9) for c in range(9) if cells[r, c] >= 0.10]
    print("cells with ink >= 0.10: %d" % len(filled))

    if args.draft:
        ok, total = agreement(cells, grid)
        print("agreement with the draft: %d/%d" % (ok, total))
        if args.search:
            def score(o, t):
                return (o / float(t)) if t >= 60 else 0.0

            best = None
            for sc in (0.96, 1.0, 1.04):
                for i in (-2, 0, 2):
                    for j in (-2, 0, 2):
                        m = ink_matrix(sq, dx=i / 10.0, dy=j / 10.0, scale=sc)
                        o, t = agreement(m, grid)
                        cand = (score(o, t), i / 10.0, j / 10.0, sc, o, t)
                        if best is None or cand[0] > best[0]:
                            best = cand
            # refine the shift at the chosen scale
            for i in range(-4, 5):
                for j in range(-4, 5):
                    m = ink_matrix(sq, dx=i / 10.0, dy=j / 10.0, scale=best[3])
                    o, t = agreement(m, grid)
                    if score(o, t) > best[0]:
                        best = (score(o, t), i / 10.0, j / 10.0, best[3], o, t)
            print("best dx=%.1f dy=%.1f scale=%.2f -> %d/%d (%.0f%%)"
                  % (best[1], best[2], best[3], best[4], best[5], 100 * best[0]))
            if best[4] < best[5] - 5:
                print("WARNING: even the best grid disagrees on %d cells; "
                      "the grid is not trustworthy for this page" % (best[5] - best[4]))
        elif ok < total - 5:
            print("WARNING: the grid may be off; try --search")
    return 0


if __name__ == "__main__":
    sys.exit(main())
