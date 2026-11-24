#!/usr/bin/env python3
"""Make a labelled contact sheet of a board's '?' cells.

    python tools/cellsheet.py <pid> <rid> "pct:x,y,w,h" <width> \
        <x0> <dx> <y0> <dy> <sfen> <out.png>

x0/dx/y0/dy are the fitted grid (page percentages, from tools/board_fit.py).
The board is fetched once, the '?' cells are cut locally and assembled into
one image, so several cells can be read in a single look.
"""
import argparse
import io
import sys
import urllib.request

import numpy as np
from PIL import Image, ImageDraw

UA = {"User-Agent": "edo-tsume-repro/1.0"}


def cells_of(sfen):
    out = []
    for r, row in enumerate(sfen.split(" ")[0].split("/"), 1):
        cells, i = [], 0
        while i < len(row):
            ch = row[i]
            if ch.isdigit():
                cells.extend([""] * int(ch))
                i += 1
            elif ch == "+":
                cells.append(row[i:i + 2])
                i += 2
            else:
                cells.append(ch)
                i += 1
        out.append(cells)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pid")
    ap.add_argument("rid")
    ap.add_argument("region")
    ap.add_argument("width", type=int)
    ap.add_argument("x0", type=float)
    ap.add_argument("dx", type=float)
    ap.add_argument("y0", type=float)
    ap.add_argument("dy", type=float)
    ap.add_argument("sfen")
    ap.add_argument("out")
    ap.add_argument("--rotate", type=int, default=0)
    args = ap.parse_args(argv)

    url = "https://dl.ndl.go.jp/api/iiif/%s/%s/%s/%d,/0/default.jpg" % (
        args.pid, args.rid, args.region, args.width)
    im = Image.open(io.BytesIO(urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=300).read())).convert("RGB")
    w, h = im.size
    rx, ry, rw, rh = [float(v) for v in args.region.replace("pct:", "").split(",")]

    def px(pct, span, size, off):
        return int(size * (pct - off) / span)

    grid = cells_of(args.sfen)
    quads = []
    for r in range(9):
        for i in range(9):
            if grid[r][i] != "?":
                continue
            file_ = 9 - i
            x_a = args.x0 + i * args.dx
            y_a = args.y0 + r * args.dy
            # keep a margin, but never reach past the board frame: at the
            # outer files the neighbouring page (or the gutter) would be
            # cropped in, which made those cells unreadable.
            m_lo = 0.0 if i == 0 else 0.10
            m_hi = 0.0 if i == 8 else 0.10
            my_lo = 0.0 if r == 0 else 0.10
            my_hi = 0.0 if r == 8 else 0.10
            # compensate by widening on the inner side
            x_lo = px(x_a - m_lo * args.dx - (0.10 if i == 8 else 0.0) * args.dx,
                      rw, w, rx)
            x_hi = px(x_a + (1 + m_hi + (0.10 if i == 0 else 0.0)) * args.dx,
                      rw, w, rx)
            y_lo = px(y_a - my_lo * args.dy - (0.10 if r == 8 else 0.0) * args.dy,
                      rh, h, ry)
            y_hi = px(y_a + (1 + my_hi + (0.10 if r == 0 else 0.0)) * args.dy,
                      rh, h, ry)
            cell = im.crop((max(0, x_lo), max(0, y_lo), min(w, x_hi), min(h, y_hi)))
            if args.rotate:
                cell = cell.rotate(args.rotate, expand=True)
            quads.append(("%d%s" % (file_, "一二三四五六七八九"[r]), cell))
    if not quads:
        print("no '?' cells")
        return 1

    H = 420
    tiles = [(lab, c.resize((int(c.width * H / c.height), H), Image.LANCZOS))
             for lab, c in quads]
    pad, per_row = 8, 4
    rows = (len(tiles) + per_row - 1) // per_row
    wid = max(sum(t.width for _, t in tiles[r * per_row:(r + 1) * per_row])
              + pad * (min(per_row, len(tiles) - r * per_row) + 1) for r in range(rows))
    canvas = Image.new("RGB", (wid, rows * (H + 30) + pad), (255, 255, 255))
    d = ImageDraw.Draw(canvas)
    x = y = pad
    for k, (lab, t) in enumerate(tiles):
        if k and k % per_row == 0:
            x, y = pad, y + H + 30
        canvas.paste(t, (x, y + 24))
        d.text((x + 3, y + 5), lab, fill=(200, 0, 0))
        x += t.width + pad
    canvas.save(args.out)
    print("wrote", args.out, canvas.size, "cells", len(tiles))
    return 0


if __name__ == "__main__":
    sys.exit(main())
