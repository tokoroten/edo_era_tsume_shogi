"""Emit per-leaf column crops for transcription.

Usage: python tools/leaf_crops.py <pid> <rid> <outprefix>

Writes <outprefix>_S12.jpg (columns 1-2 = right page) and <outprefix>_S34.jpg
(columns 3-4 = left page), each column upscaled to 800px wide.
S1 = rightmost printed column of the leaf.
"""
import argparse
import io
import sys
import urllib.request

import numpy as np
from PIL import Image, ImageDraw

UA = {"User-Agent": "edo-tsume-repro/1.0"}
COL_W = 800
TALL = 2600


def fetch(pid, rid, w=2600):
    url = "https://dl.ndl.go.jp/api/iiif/%s/%s/full/%d,/0/default.jpg" % (pid, rid, w)
    req = urllib.request.Request(url, headers=UA)
    return Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=180).read())).convert("L")


def text_block(cols, height, lo=0.02, hi=0.45, gap=20):
    frac = cols / float(height)
    on = (frac > lo) & (frac < hi)
    best = (0, 0)
    start = last = None
    for x, v in enumerate(on):
        if v:
            if start is None:
                start = x
            last = x
        elif start is not None and x - last > gap:
            if last - start > best[1] - best[0]:
                best = (start, last)
            start = None
    if start is not None and last is not None and last - start > best[1] - best[0]:
        best = (start, last)
    return best


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Emit per-leaf column crops for transcription.")
    ap.add_argument("pid")
    ap.add_argument("rid")
    ap.add_argument("prefix")
    args = ap.parse_args(argv)
    pid, rid, prefix = args.pid, args.rid, args.prefix
    im = fetch(pid, rid)
    a = np.array(im)
    ink = a < 110
    cols = ink.sum(axis=0)
    rows = ink.sum(axis=1)
    x0, x1 = text_block(cols, im.height)
    ry = np.where(rows >= rows.max() * 0.05)[0]
    y0, y1 = int(ry[0]), int(ry[-1])
    w = (x1 - x0) // 4
    blocks = [(x0 + i * w, x0 + (i + 1) * w) for i in range(4)]
    blocks[3] = (blocks[3][0], x1)
    # S1..S4 are right-to-left
    ordered = list(reversed(blocks))
    for part, idxs in (("S12", (0, 1)), ("S34", (2, 3))):
        crops = []
        for i in idxs:
            bx0, bx1 = ordered[i]
            crop = im.crop((bx0, y0, bx1, y1))
            scale = TALL / float(crop.height)
            crop = crop.resize((max(1, int(crop.width * scale)), TALL), Image.LANCZOS)
            crops.append(crop)
        cw = max(c.width for c in crops)
        canvas = Image.new("L", (len(idxs) * (cw + 12), TALL + 24), 255)
        d = ImageDraw.Draw(canvas)
        for k, (i, crop) in enumerate(zip(idxs, crops)):
            d.text((k * (cw + 12) + 4, 4), "S%d" % (i + 1), fill=0)
            canvas.paste(crop, (k * (cw + 12) + 6, 22))
        out = "%s_%s.jpg" % (prefix, part)
        canvas.save(out, quality=90)
        print(out, canvas.size)


if __name__ == "__main__":
    main()
