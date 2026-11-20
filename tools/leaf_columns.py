"""Column segmentation by ink gaps, for 将棋精妙 下巻 leaves.

Usage: python tools/leaf_columns.py <pid> <rid> <outprefix> [--native PATH]

Writes <outprefix>_S1.jpg .. _S4.jpg (one column each, 900px wide) plus a
contact sheet <outprefix>_sheet.jpg. S1 = rightmost printed column.
"""
import argparse
import io
import sys
import urllib.request

import numpy as np
from PIL import Image, ImageDraw

UA = {"User-Agent": "edo-tsume-repro/1.0"}
CW = 900


def load(pid, rid, native=None):
    if native:
        return Image.open(native).convert("L")
    url = "https://dl.ndl.go.jp/api/iiif/%s/%s/full/full/0/default.jpg" % (pid, rid)
    req = urllib.request.Request(url, headers=UA)
    return Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=300).read())).convert("L")


def segment(im):
    a = np.array(im)
    ink = a < 110
    prof = ink.sum(axis=0) / float(im.height)
    on = (prof > 0.02) & (prof < 0.45)
    # text band = longest run
    best = (0, 0)
    start = last = None
    for x, v in enumerate(on):
        if v:
            if start is None:
                start = x
            last = x
        elif start is not None and x - last > 25:
            if last - start > best[1] - best[0]:
                best = (start, last)
            start = None
    if start is not None and last is not None and last - start > best[1] - best[0]:
        best = (start, last)
    x0, x1 = best
    # fixed 4-way split inside the detected text band (the columns touch, so
    # gap/peak detection is unreliable on these scans; see docs/procedures.md)
    w = (x1 - x0) // 4
    bounds = [x0 + w * k for k in range(5)]
    rows = ink.sum(axis=1)
    idx = np.where(rows >= rows.max() * 0.04)[0]
    y0, y1 = int(idx[0]), int(idx[-1])
    return [(bounds[i], bounds[i + 1]) for i in range(4)], (y0, y1)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Column segmentation by ink gaps, for one leaf.")
    ap.add_argument("pid")
    ap.add_argument("rid")
    ap.add_argument("prefix")
    ap.add_argument("--native", default=None)
    args = ap.parse_args(argv)
    pid, rid, prefix, native = args.pid, args.rid, args.prefix, args.native
    im = load(pid, rid, native)
    blocks, (y0, y1) = segment(im)
    ordered = list(reversed(blocks))  # S1 = rightmost
    thumbs = []
    for i, (bx0, bx1) in enumerate(ordered, 1):
        crop = im.crop((bx0, y0, bx1, y1))
        crop = crop.resize((CW, int(crop.height * CW / float(crop.width))), Image.LANCZOS)
        p = "%s_S%d.jpg" % (prefix, i)
        crop.save(p, quality=92)
        thumbs.append(crop)
        print(p, crop.size, "x", bx0, bx1)
    th = max(t.height for t in thumbs)
    sheet = Image.new("L", (4 * (CW // 2 + 8), th // 2 + 24), 255)
    d = ImageDraw.Draw(sheet)
    for i, t in enumerate(thumbs, 1):
        d.text(((i - 1) * (CW // 2 + 8) + 3, 4), "S%d" % i, fill=0)
        sheet.paste(t.resize((CW // 2, t.height // 2), Image.LANCZOS),
                    ((i - 1) * (CW // 2 + 8) + 4, 20))
    sheet.save("%s_sheet.jpg" % prefix, quality=90)
    print("%s_sheet.jpg" % prefix, sheet.size)


if __name__ == "__main__":
    main()
