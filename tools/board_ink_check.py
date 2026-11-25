#!/usr/bin/env python3
"""One-sided occupancy check: does the printed ink agree with the draft board?

    python tools/board_ink_check.py head-ok 10
    python tools/board_ink_check.py head-bad 60

For each board the ten rules are fitted with ``board_fit``, the ink is sampled
inside the 49 interior cells (files 2-8, ranks 2-8), and occupied/empty is
compared with the draft.

Reading the result:

  * **high agreement** (47-49 of 49) means the draft's piece *placement*
    matches the page.  It says nothing about kind or side - a pawn read as a
    gold occupies the same square - so the head can still fail.
  * **low agreement** is inconclusive: the fitted grid may simply be off.
    A wrong origin shows as mismatches lining up in one file or one rank, and
    as a file with ink in every rank.
  * maps that fail those two guards are printed as rejected and must not be
    used as evidence in either direction.

The outer ring is excluded because the board's frame line sits inside it and
adds ink to every edge cell regardless of what the cell holds.
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASES = {"kanju": ("collections", "meiji", "kanju", "drafts"),
         "seimyo": ("collections", "edo", "seimyo", "drafts")}
THRESH = 0.07
INSET = 0.22


def grid(sfen):
    out = []
    for row in sfen.split(" ")[0].split("/"):
        cells, i = [], 0
        while i < len(row):
            if row[i].isdigit():
                cells.extend([""] * int(row[i]))
                i += 1
            elif row[i] == "+":
                cells.append(row[i:i + 2])
                i += 2
            else:
                cells.append(row[i])
                i += 1
        out.append(cells)
    return out


def fit(pid, rid, side):
    window = "pct:50,26,42,56" if side == "右" else "pct:9,26,42,56"
    cmd = [sys.executable, os.path.join(ROOT, "tools", "board_fit.py"),
           pid, rid, window, "1600"]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                         errors="replace")
    cols = rows = None
    for ln in res.stdout.splitlines():
        if ln.startswith("cols pct:"):
            cols = [float(x) for x in ln.split(":", 1)[1].split("matched")[0].split()]
        elif ln.startswith("rows pct:"):
            rows = [float(x) for x in ln.split(":", 1)[1].split("matched")[0].split()]
    if not cols or not rows or len(cols) != 10 or len(rows) != 10:
        return None, None
    return cols, rows


def fetch(pid, rid, region, width):
    import tempfile
    import urllib.request
    url = "https://dl.ndl.go.jp/api/iiif/%s/%s/%s/%d,/0/default.jpg" % (
        pid, rid, region, width)
    req = urllib.request.Request(url, headers={"User-Agent": "edo-tsume-repro/1.0"})
    data = urllib.request.urlopen(req, timeout=300).read()
    p = os.path.join(tempfile.gettempdir(), "ink_check.jpg")
    open(p, "wb").write(data)
    return Image.open(p).convert("L")


def sample(img, cols, rows, left, top, span_x, span_y):
    a = np.asarray(img, dtype=np.float32)
    h, w = a.shape
    dark = a < 128
    out = {}
    for i in range(9):
        for j in range(9):
            x0 = (cols[i] - left) / span_x * w
            x1 = (cols[i + 1] - left) / span_x * w
            y0 = (rows[j] - top) / span_y * h
            y1 = (rows[j + 1] - top) / span_y * h
            xa, xb = int(x0 + INSET * (x1 - x0)), int(x1 - INSET * (x1 - x0))
            ya, yb = int(y0 + INSET * (y1 - y0)), int(y1 - INSET * (y1 - y0))
            if xa < 0 or ya < 0 or xb > w or yb > h or xb <= xa or yb <= ya:
                return None
            out[(9 - i, j + 1)] = float(dark[ya:yb, xa:xb].mean())
    return out


def rule_line(ink):
    """True when a file has ink in every rank - a rule sampled as a cell."""
    for f in range(1, 10):
        if sum(ink[(f, r)] for r in range(1, 10)) / 9.0 > 0.18:
            return True
    return False


def compare(g, ink):
    tp = fp = fn = tn = 0
    bad = []
    unknown = []
    for r in range(9):
        for c in range(9):
            f = 9 - c
            if f in (1, 9) or r + 1 in (1, 9):
                continue
            if g[r][c] == "?":
                # an unknown square cannot be scored, but its ink is evidence
                # that *something* is printed there.
                if ink[(f, r + 1)] >= THRESH:
                    unknown.append((f, r + 1, round(ink[(f, r + 1)], 2)))
                continue
            occ = bool(g[r][c])
            inked = ink[(f, r + 1)] >= THRESH
            if occ and inked:
                tp += 1
            elif occ:
                fn += 1
                bad.append((f, r + 1, "piece/no-ink"))
            elif inked:
                fp += 1
                bad.append((f, r + 1, "ink/no-piece"))
            else:
                tn += 1
    return tp + tn, fp + fn, tp + fp + fn + tn, bad, unknown


def one_line(bad):
    if len(bad) < 6:
        return False
    files, ranks = {}, {}
    for f, r, _ in bad:
        files[f] = files.get(f, 0) + 1
        ranks[r] = ranks.get(r, 0) + 1
    return max(files.values()) * 2 >= len(bad) or max(ranks.values()) * 2 >= len(bad)


def main():
    group = sys.argv[1] if len(sys.argv) > 1 else "head-ok"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    shown = 0
    for cid, base in BASES.items():
        path = os.path.join(ROOT, "docs", "%s-first-moves.json" % cid)
        flags = {m["number"]: bool(m.get("head_unassigned"))
                 for m in json.load(open(path, encoding="utf-8"))["moves"]}
        for n in range(1, 101 if cid == "seimyo" else 51):
            if shown >= limit:
                return
            if flags.get(n) != (group == "head-bad"):
                continue
            rec = json.load(open(os.path.join(ROOT, *(base + ("%03d.json" % n,))),
                                 encoding="utf-8"))
            m = re.search(r"PID:(\d+)\s+(R\d+)([左右])",
                          rec.get("source", {}).get("page", ""))
            if not m:
                continue
            pid, rid, side = m.groups()
            cols, rows = fit(pid, rid, side)
            if not cols:
                print("%s %3d  fit rejected" % (cid, n))
                continue
            cw = float(np.median(np.diff(cols)))
            ch = float(np.median(np.diff(rows)))
            left, top = cols[0] - 2 * cw, rows[0] - 2 * ch
            right, bottom = cols[-1] + 2 * cw, rows[-1] + 2 * ch
            region = "pct:%.2f,%.2f,%.2f,%.2f" % (
                left, top, right - left, bottom - top)
            try:
                img = fetch(pid, rid, region, 1200)
            except Exception as exc:  # noqa: BLE001
                print("%s %3d  fetch failed %s" % (cid, n, exc))
                continue
            ink = sample(img, cols, rows, left, top, right - left, bottom - top)
            if ink is None:
                print("%s %3d  image too small" % (cid, n))
                continue
            if rule_line(ink):
                print("%s %3d  rejected: a file has ink in every rank" % (cid, n))
                continue
            score, miss, total, bad, unknown = compare(grid(rec["sfen"]), ink)
            if one_line(bad):
                print("%s %3d  rejected: mismatches line up in one file/rank" % (cid, n))
                continue
            lack = [b for b in bad if b[2] == "ink/no-piece"]
            extra = [b for b in bad if b[2] == "piece/no-ink"]
            print("%s %3d  interior %2d/%d  mismatch %d  missing %s  extra %s%s"
                  % (cid, n, score, total, miss,
                     ["%d%s" % (f, "一二三四五六七八九"[r - 1]) for f, r, _ in lack],
                     ["%d%s" % (f, "一二三四五六七八九"[r - 1]) for f, r, _ in extra],
                     "" if not unknown else "  unknown-with-ink %s" % unknown))
            shown += 1


if __name__ == "__main__":
    main()
