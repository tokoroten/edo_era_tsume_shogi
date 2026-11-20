"""Split one NDL leaf into four column strips for transcription.

Usage: python tools/fetch_leaf.py <pid> <rid> <out.jpg>

Fetches the leaf from NDL IIIF, finds three low-ink seams and writes a
contact sheet S1..S4 (S1 = rightmost printed column). Used to read the
seimyo solution volume column by column.
"""

import argparse
import io
import sys
import urllib.request

import numpy as np
from PIL import Image, ImageDraw

UA = {"User-Agent": "edo-tsume-repro/1.0"}
TARGET_W = 560
TARGET_H = 1800


def fetch(pid, rid, w=2400):
    url = "https://dl.ndl.go.jp/api/iiif/%s/%s/full/%d,/0/default.jpg" % (pid, rid, w)
    req = urllib.request.Request(url, headers=UA)
    return Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=180).read())).convert("L")


def column_profile(im):
    a = np.array(im)
    ink = (a < 110)
    return ink.sum(axis=0), ink.sum(axis=1)


def text_rows(rows, frac=0.08):
    thr = rows.max() * frac
    idx = np.where(rows >= thr)[0]
    return (int(idx[0]), int(idx[-1])) if len(idx) else (0, len(rows) - 1)


def four_columns(cols, rows_hint):
    """Split the ink profile into 4 column blocks by 3 lowest-density seams."""
    thr = cols.max() * 0.12
    xs = np.where(cols >= thr)[0]
    if len(xs) < 40:
        return None
    lo, hi = int(xs[0]), int(xs[-1])
    span = hi - lo
    seams = []
    for k in (1, 2, 3):
        centre = lo + span * k // 4
        win = max(6, span // 40)
        a, b = max(lo + 5, centre - win), min(hi - 5, centre + win)
        if b <= a:
            continue
        seams.append(a + int(np.argmin(cols[a:b])))
    if len(seams) != 3:
        return None
    bounds = [lo] + seams + [hi]
    return [(bounds[i], bounds[i + 1]) for i in range(4)]


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Split one NDL leaf into four column strips.")
    ap.add_argument("pid")
    ap.add_argument("rid")
    ap.add_argument("out")
    args = ap.parse_args(argv)
    pid, rid, out = args.pid, args.rid, args.out
    im = fetch(pid, rid)
    cols, rows = column_profile(im)
    blocks = four_columns(cols, rows)
    if blocks is None:
        raise SystemExit("could not split into 4 columns")
    y0, y1 = text_rows(rows)
    strips = []
    for i in range(4):
        x0, x1 = blocks[3 - i]  # S1 = rightmost printed column
        crop = im.crop((x0, y0, x1, y1))
        crop = crop.resize((TARGET_W, TARGET_H), Image.LANCZOS)
        strips.append(crop)
    canvas = Image.new("L", (4 * (TARGET_W + 10), TARGET_H + 24), 255)
    d = ImageDraw.Draw(canvas)
    for i, s in enumerate(strips):
        d.text((i * (TARGET_W + 10) + 4, 5), "S%d" % (i + 1), fill=0)
        canvas.paste(s, (i * (TARGET_W + 10) + 5, 22))
    canvas.save(out, quality=90)
    print(out, canvas.size, "blocks", blocks, "rows", y0, y1)


if __name__ == "__main__":
    main()
