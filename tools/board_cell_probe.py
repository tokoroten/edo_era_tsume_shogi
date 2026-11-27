#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""board_cell_probe.py — fit one printed board and crop named cells.

Some collections print the board with rectangular cells, and the orientation of
the diagram (which side is at the top) differs from figure to figure.  This
tool fits the 9x9 grid by trying the eight symmetries plus a small scale/shift
search, scores the fit against a draft's SFEN, and saves a contact sheet of the
requested cells.

The score is one-sided evidence only: a high score supports the draft's
placement, a low one proves nothing (see docs/ink-evidence.md).

Usage:
    python tools/board_cell_probe.py PID RID "x0,y0,x1,y1" DRAFT.json \
        "rank,file;rank,file;..." [--out sheet.png] [--width 3000]
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import board_cell_ink as b  # noqa: E402

SYMMETRIES = {
    "id": lambda m: m,
    "r90": lambda m: np.rot90(m, 3),
    "r180": lambda m: np.rot90(m, 2),
    "r270": lambda m: np.rot90(m, 1),
    "fh": lambda m: m[:, ::-1],
    "fv": lambda m: m[::-1, :],
    "tr": lambda m: m.T,
    "atr": lambda m: np.rot90(m, 2).T,
}


def score(cells, grid):
    ok = total = 0
    for r in range(9):
        for c in range(9):
            if cells[r, c] < 0:
                continue
            total += 1
            if (cells[r, c] >= 0.10) == bool(grid[r][c]):
                ok += 1
    return ok, total


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("pid")
    ap.add_argument("rid")
    ap.add_argument("frame", help="x0,y0,x1,y1 in page percent")
    ap.add_argument("draft")
    ap.add_argument("cells", help="rank,file pairs separated by ';'")
    ap.add_argument("--out", default="cells.png")
    ap.add_argument("--width", type=int, default=3000)
    ap.add_argument("--side", type=int, default=2000)
    args = ap.parse_args(argv)

    rec = json.load(open(args.draft, encoding="utf-8"))
    grid = b.sfen_grid(rec["sfen"])
    x0, y0, x1, y1 = [float(v) for v in args.frame.split(",")]
    want = []
    for part in args.cells.split(";"):
        rk, fl = part.split(",")
        want.append((int(rk), int(fl)))

    img = b.fetch(args.pid, args.rid, "pct:0,0,100,100", args.width)
    sq = b.warp(img, "pct:0,0,100,100",
                [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], side=args.side)

    base = b.ink_matrix(sq, side=args.side, margin=22)
    best = None
    for name, fn in SYMMETRIES.items():
        ok, total = score(fn(base), grid)
        if best is None or ok > best[0]:
            best = (ok, total, name)
    name = best[2]
    fn = SYMMETRIES[name]

    fine = None
    for sc in [0.90 + 0.02 * i for i in range(7)]:
        for dx in [v / 10.0 for v in range(-3, 4)]:
            for dy in [v / 10.0 for v in range(-3, 4)]:
                ok, total = score(
                    fn(b.ink_matrix(sq, side=args.side, margin=22,
                                    dx=dx, dy=dy, scale=sc)), grid)
                if fine is None or ok > fine[0]:
                    fine = (ok, total, sc, dx, dy)
    ok, total, sc, dx, dy = fine
    print("fit %s %d/%d scale %.2f dx %.1f dy %.1f" %
          (name, ok, total, sc, dx, dy))

    labels = np.array([[(i, j) for j in range(9)] for i in range(9)],
                      dtype=object)
    moved = fn(labels)
    pos = {}
    for rk, fl in want:
        for r in range(9):
            for c in range(9):
                if tuple(moved[r][c]) == (rk - 1, 9 - fl):
                    pos[(rk, fl)] = (r, c)

    step = args.side / 9.0
    cell = step * sc
    ox = (args.side - 9 * cell) / 2.0 + dx * step
    oy = (args.side - 9 * cell) / 2.0 + dy * step
    sheet = Image.new("L", (max(1, len(pos)) * 500 + 20, 550), 255)
    draw = ImageDraw.Draw(sheet)
    for i, ((rk, fl), (r, c)) in enumerate(pos.items()):
        cx = ox + (c + 0.5) * cell
        cy = oy + (r + 0.5) * cell
        h = 0.95 * cell
        im = sq.crop((int(cx - h), int(cy - h), int(cx + h), int(cy + h)))
        sheet.paste(im.resize((490, 490), Image.LANCZOS), (i * 500 + 5, 45))
        draw.text((i * 500 + 5, 10), "r%d f%d" % (rk, fl), fill=0)
    sheet.save(args.out)
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
