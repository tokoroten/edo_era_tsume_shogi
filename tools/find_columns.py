#!/usr/bin/env python3
"""Detect vertical text columns in an NDL leaf and print their x ranges.

Usage:
  python tools/find_columns.py 861192 R0000014 --y0 18 --y1 48

Prints one line per column: index, x range in percent of the canvas width,
and the column centre. Useful before cropping a single column with
tools/iiif_crop.py or tools/leaf_bands.py.

Detection: vertical ink projection over the given y band; a column is a run
of columns with ink density between 3% and 60% separated by gaps of at least
6 px (native). Rows are not analysed, so multi-column table lines may merge.
"""
import argparse
import io
import sys
import urllib.request

import numpy as np
from PIL import Image

UA = {"User-Agent": "edo-tsume-repro/1.0"}


def fetch(pid, rid, timeout=300):
    url = "https://dl.ndl.go.jp/api/iiif/%s/%s/full/full/0/default.jpg" % (
        pid, rid)
    req = urllib.request.Request(url, headers=UA)
    data = urllib.request.urlopen(req, timeout=timeout).read()
    return Image.open(io.BytesIO(data)).convert("L")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pid")
    ap.add_argument("rid")
    ap.add_argument("--y0", type=float, default=10.0)
    ap.add_argument("--y1", type=float, default=90.0)
    ap.add_argument("--min-gap", type=int, default=6)
    args = ap.parse_args(argv)

    im = fetch(args.pid, args.rid)
    w, h = im.size
    top = int(h * args.y0 / 100.0)
    bot = int(h * args.y1 / 100.0)
    a = np.array(im.crop((0, top, w, bot)))
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
        elif start is not None and x - last > args.min_gap:
            runs.append((start, last))
            start = None
    if start is not None:
        runs.append((start, last))

    print("%s %s  y %.1f-%.1f%%  width %d" % (args.pid, args.rid,
                                              args.y0, args.y1, w))
    for i, (x0, x1) in enumerate(runs, 1):
        print("  col %2d  %5.1f%% - %5.1f%%  centre %5.1f%%  (%d px)"
              % (i, x0 * 100.0 / w, (x1 + 1) * 100.0 / w,
                 (x0 + x1 + 1) * 50.0 / w, x1 - x0 + 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
