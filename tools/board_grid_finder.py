#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find a board's ten rules in a page image and print the grid corners.

    python tools/board_grid_finder.py page.png x0 y0 x1 y1

Why this exists
---------------
`board_cell_ink.py` needs the four corners of the printed grid, and taking them
by eye is the slowest and most error-prone step of a board read: the outer frame
often sits a whole cell outside the grid (see 精妙 87 and the 大正 volumes), so a
corner taken on the frame shifts every cell by one.

This tool looks for the rules themselves.  It collects thin dark runs along many
scan lines on each axis, keeps the strong peaks, and then fits an arithmetic
progression of ten lines to those peaks.  Because the fit is a progression, a
frame line one cell outside the grid simply fails to join it, which is exactly
the behaviour a human reader wants.

Output: the ten positions per axis in page pixels, the step, and the four corners
as page percent (upper left, upper right, lower right, lower left) ready to paste
into `board_cell_ink.py`.
"""
import sys

import numpy as np
from PIL import Image

MIN_RUN, MAX_RUN = 1, 4
PEAK_FRACTION = 0.10
PEAK_MIN_DIST = 6
TOL = 0.22            # of one step; how far a peak may sit from the ideal line


def _runs(mask):
    out, start = [], None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        elif not v and start is not None:
            out.append((start, i - 1))
            start = None
    if start is not None:
        out.append((start, len(mask) - 1))
    return [r for r in out if MIN_RUN <= r[1] - r[0] + 1 <= MAX_RUN]


def _centres(img, axis, box, step=2, thr=150):
    dark = img < thr
    x0, y0, x1, y1 = box
    pts = []
    if axis == "h":
        for x in range(x0, x1, step):
            for a, b in _runs(dark[y0:y1, x]):
                pts.append(y0 + 0.5 * (a + b))
    else:
        for y in range(y0, y1, step):
            for a, b in _runs(dark[y, x0:x1]):
                pts.append(x0 + 0.5 * (a + b))
    return pts


def _peaks(pts, lo, hi):
    if not pts:
        return []
    hist = np.zeros(hi - lo + 2)
    for p in pts:
        i = int(round(p - lo))
        if 0 <= i < len(hist):
            hist[i] += 1
    smooth = np.convolve(hist, [0.25, 0.5, 0.25], mode="same")
    thr = max(2.0, PEAK_FRACTION * smooth.max())
    out = []
    for i in range(1, len(smooth) - 1):
        if smooth[i] >= thr and smooth[i] >= smooth[i - 1] and smooth[i] >= smooth[i + 1]:
            pos = lo + i - 1
            if out and pos - out[-1] < PEAK_MIN_DIST:
                if smooth[i] > smooth[i - 1]:
                    out[-1] = pos
            else:
                out.append(pos)
    return out


def _candidates(peaks, step_min=8.0, step_max=120.0, fixed_step=None):
    """All (score, start, step, hits, error) fits of ten evenly spaced lines."""
    if len(peaks) < 4:
        return []
    cands = set()
    if fixed_step is not None:
        cands.add(round(fixed_step, 2))
    else:
        for i in range(len(peaks)):
            for j in range(i + 1, len(peaks)):
                d = peaks[j] - peaks[i]
                for k in range(1, 10):
                    s = d / float(k)
                    if step_min <= s <= step_max:
                        cands.add(round(s, 2))
    out = []
    for s in sorted(cands):
        for p in peaks:
            err, hit = 0.0, 0
            for t in range(10):
                want = p + t * s
                near = min(peaks, key=lambda q: abs(q - want))
                d = abs(near - want)
                if d <= s * TOL:
                    hit += 1
                    err += d / s
                else:
                    err += 1.0
            out.append((hit - 0.5 * err, p, s, hit, err))
    out.sort(key=lambda z: -z[0])
    return out


def _fit(peaks, step_min=8.0, step_max=120.0, fixed_step=None):
    """Best arithmetic progression of ten lines through `peaks`.

    When two fits tie, prefer the one that does not start on the box's outermost
    line: that line is usually the outer frame, which often sits a whole cell
    outside the grid (see 精妙 87 and the 大正 volumes).
    """
    cands = _candidates(peaks, step_min, step_max, fixed_step)
    if not cands:
        return None
    top = cands[0]
    if len(cands) > 1 and cands[1][0] > top[0] - 0.3:
        lo, hi = min(peaks), max(peaks)
        for c in cands[:6]:
            if c[1] > lo + 1e-6 and c[1] + 9 * c[2] < hi - 1e-6:
                top = c
                break
    cands.remove(top)
    cands.insert(0, top)
    score, p, s, hit, err = cands[0]
    return {"start": p, "step": s, "hits": hit, "error": err, "score": score,
            "positions": [p + t * s for t in range(10)],
            "alternatives": [(c[1], c[2], c[3]) for c in cands[1:4]]}


def find(path, box):
    """Fit both axes; a board is square, so the weaker axis is refit to the other's step."""
    img = np.asarray(Image.open(path).convert("L")).astype(np.int16)
    x0, y0, x1, y1 = box
    hp = _peaks(_centres(img, "h", box), y0, y1)
    vp = _peaks(_centres(img, "v", box), x0, x1)
    hs, vs = _fit(hp), _fit(vp)
    if hs and vs and abs(hs["step"] - vs["step"]) > 0.03 * vs["step"]:
        # refit the axis with the weaker score at the other's step
        if hs["score"] <= vs["score"]:
            alt = _fit(hp, fixed_step=vs["step"])
            if alt and alt["score"] > hs["score"]:
                hs = alt
        else:
            alt = _fit(vp, fixed_step=hs["step"])
            if alt and alt["score"] > vs["score"]:
                vs = alt
    return hs, vs, img.shape


def corners_pct(path, hs, vs):
    W, H = Image.open(path).size
    if not hs or not vs:
        return None
    ul = (vs["positions"][0], hs["positions"][0])
    ur = (vs["positions"][-1], hs["positions"][0])
    lr = (vs["positions"][-1], hs["positions"][-1])
    ll = (vs["positions"][0], hs["positions"][-1])
    return [(100.0 * x / W, 100.0 * y / H) for x, y in (ul, ur, lr, ll)]


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "-h" in argv or "--help" in argv or len(argv) != 5:
        print(__doc__)
        return 0 if ("-h" in argv or "--help" in argv) else 2
    path = argv[0]
    box = tuple(int(float(v)) for v in argv[1:5])
    hs, vs, shape = find(path, box)
    for name, f in (("h", hs), ("v", vs)):
        if f:
            print("%s: start %.1f step %.2f hits %d error %.2f" %
                  (name, f["start"], f["step"], f["hits"], f["error"]))
            print("   " + " ".join("%.0f" % p for p in f["positions"]))
            for alt in f.get("alternatives", []):
                print("   alt: start %.0f step %.2f hits %d" % alt)
        else:
            print("%s: no fit" % name)
    cs = corners_pct(path, hs, vs)
    if cs:
        print("corners pct: " + ",".join("%.1f,%.1f" % c for c in cs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
