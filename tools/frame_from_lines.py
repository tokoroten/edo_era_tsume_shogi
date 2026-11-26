#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find a board's frame from the printed grid lines.

    python tools/frame_from_lines.py gyokuzu 45
    python tools/frame_from_lines.py gyokuzu 45 --write

The scan's rules are darker than the paper, so summing dark pixels down each
column and across each row gives peaks.  The board's *border* lines are the
thickest peaks: choosing the thickest pair whose distance fits one board
(about 34-37 percent of the page wide, 37-43 percent tall) is far more
reliable than guessing a frame from piece occupancy, which mixes "wrong
frame" with "misread piece".

Rows are measured through a central window because many of these pages are
hand-drawn and their horizontal lines drift; a full-width sum blurs them.

The tool only proposes a frame and prints how well the draft's placement
agrees with it.  `--write` stores the frame in the draft (source.frame) but
never changes the position.
"""
import argparse
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import board_cell_ink as b  # noqa: E402
import numpy as np  # noqa: E402

BASES = {
    "seimyo": os.path.join("edo", "seimyo"),
    "kanju": os.path.join("meiji", "kanju"),
    "gyokuzu": os.path.join("edo", "gyokuzu"),
    "meijin": os.path.join("taisho", "meijin"),
    "shiroto": os.path.join("taisho", "shiroto"),
}
PAGE_WIDTH = 2400


def peak_widths(values, threshold):
    """Return (centre, width) for each run above threshold."""
    idx = [i for i, v in enumerate(values) if v > threshold]
    out = []
    cur = []
    for i in idx:
        if cur and i - cur[-1] <= 2:
            cur.append(i)
        else:
            if cur:
                out.append((sum(cur) / float(len(cur)), len(cur)))
            cur = [i]
    if cur:
        out.append((sum(cur) / float(len(cur)), len(cur)))
    return out


def best_pair(peaks, lo, hi, target):
    """Pick the thickest pair whose span lies in [lo, hi]."""
    best = None
    for i in range(len(peaks)):
        for j in range(i + 1, len(peaks)):
            a, wa = peaks[i]
            c, wc = peaks[j]
            span = c - a
            if lo <= span <= hi:
                score = min(wa, wc) * 10.0 - abs(span - target)
                if best is None or score > best[0]:
                    best = (score, a, c, wa, wc)
    return best


def page_half(rec):
    page = rec.get("source", {}).get("page") or ""
    m = re.search(r"R\d{7}\s*([左右])", page)
    if m:
        return (10.0, 52.0) if m.group(1) == u"左" else (46.0, 88.0)
    return (46.0, 88.0) if u"右" in page else (10.0, 52.0)


def detect(pid, rid, xa, xb, ya=32.0, yb=78.0):
    img = b.fetch(pid, rid, "pct:0,0,100,100", PAGE_WIDTH)
    a = np.asarray(img).astype(np.float32)
    H, W = a.shape
    dark = a < 160

    x0, x1 = int(xa / 100.0 * W), int(xb / 100.0 * W)
    y0, y1 = int(ya / 100.0 * H), int(yb / 100.0 * H)
    sub = dark[y0:y1, x0:x1]
    cols = sub.sum(axis=0) / float(sub.shape[0])

    # columns: whole band; rows: central window (hand-drawn lines drift)
    xw0 = x0 + int(0.28 * (x1 - x0))
    xw1 = x0 + int(0.68 * (x1 - x0))
    rows = dark[y0:y1, xw0:xw1].sum(axis=1) / float(xw1 - xw0)

    cpeaks = [((x0 + c) / float(W) * 100.0, w) for c, w in peak_widths(cols, 0.28)]
    rpeaks = [((y0 + c) / float(H) * 100.0, w) for c, w in peak_widths(rows, 0.40)]

    cp = best_pair(cpeaks, 33.0, 38.0, 35.0)
    rp = best_pair(rpeaks, 37.0, 43.0, 40.0)
    if not cp or not rp:
        return None
    return {"left": cp[1], "right": cp[2], "top": rp[1], "bottom": rp[2]}


def measure(rec, corners):
    frame = rec["source"]["frame"]
    region = "pct:0,0,100,100"
    img = b.fetch(frame["pid"], frame["rid"], region, 1600)
    sq = b.warp(img, region, [tuple(corners[0:2]), tuple(corners[2:4]),
                              tuple(corners[4:6]), tuple(corners[6:8])], side=1800)
    cells = b.ink_matrix(sq)
    grid = b.sfen_grid(rec["sfen"])
    if frame.get("mirror"):
        grid = b.mirror_grid(grid)
    return b.agreement(cells, grid)


def load(spec, number):
    base = BASES[spec]
    p = os.path.join(ROOT, "collections", base, "drafts", "%03d.json" % number)
    return p, json.load(io.open(p, encoding="utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("collection", choices=sorted(BASES))
    ap.add_argument("number", type=int)
    ap.add_argument("--write", action="store_true",
                    help="store the detected frame in source.frame")
    args = ap.parse_args(argv)

    p, rec = load(args.collection, args.number)
    frame = rec.get("source", {}).get("frame") or {}
    pid = frame.get("pid") or rec.get("source", {}).get("pid") or "861197"
    rid = frame.get("rid")
    if not rid:
        m = re.search(r"R\d{7}", rec.get("source", {}).get("page") or "")
        if not m:
            print("no page id on this draft")
            return 1
        rid = m.group(0)
    xa, xb = page_half(rec)
    d = detect(pid, rid, xa, xb)
    if not d:
        print("no board border found")
        return 1
    corners = [d["left"], d["top"], d["right"], d["top"],
               d["right"], d["bottom"], d["left"], d["bottom"]]
    rec.setdefault("source", {})["frame"] = {
        "pid": pid, "rid": rid, "corners": [round(v, 2) for v in corners],
        "mirror": bool(frame.get("mirror")) or args.collection == "gyokuzu",
        "note": "board border measured from the printed rules"}
    ok, total = measure(rec, corners)
    print("%s %d  %.2f,%.2f - %.2f,%.2f  %d/%d" % (
        args.collection, args.number, d["left"], d["top"], d["right"],
        d["bottom"], ok, total))
    if args.write:
        io.open(p, "w", encoding="utf-8", newline="\n").write(
            json.dumps(rec, ensure_ascii=False, indent=2) + "\n")
        print("wrote frame to", os.path.relpath(p, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
