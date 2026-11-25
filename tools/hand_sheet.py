#!/usr/bin/env python3
"""Compose the printed hand lines (盤下持駒) of several boards into one image.

    python tools/hand_sheet.py seimyo:6 seimyo:15 kanju:13 --out hands.png

For each board the ten fitted rules give the board's bottom edge; the hand line
is printed just below it, in large type that survives the scan's ~170 px per
square.  Label each strip with the recorded hand (from the SFEN's hand field)
so one look compares the print with the record.

Why one image: six boards per image keeps the reading cheap, and the hand line
needs no magnification beyond what the scan holds (`docs/image-policy.md`).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASES = {"kanju": ("collections", "meiji", "kanju", "drafts"),
         "seimyo": ("collections", "edo", "seimyo", "drafts")}
UA = {"User-Agent": "edo-tsume-repro/1.0"}


def fetch(pid, rid, region, width, out):
    url = "https://dl.ndl.go.jp/api/iiif/%s/%s/%s/%d,/0/default.jpg" % (
        pid, rid, region, width)
    data = urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                  timeout=120).read()
    open(out, "wb").write(data)


def fit(pid, rid, side):
    window = "pct:50,26,42,56" if side == "右" else "pct:9,26,42,56"
    res = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "board_fit.py"),
                          pid, rid, window, "1400"],
                         capture_output=True, text=True, encoding="utf-8",
                         errors="replace")
    cols = rows = None
    for ln in res.stdout.splitlines():
        if ln.startswith("cols pct:"):
            cols = [float(x) for x in ln.split(":", 1)[1].split("matched")[0].split()]
        elif ln.startswith("rows pct:"):
            rows = [float(x) for x in ln.split(":", 1)[1].split("matched")[0].split()]
    return cols, rows


def hand_of(sfen):
    parts = sfen.split(" ")
    if len(parts) < 3 or parts[2] == "-":
        return "-"
    return parts[2]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("boards", nargs="+", help="cid:number, e.g. seimyo:6")
    ap.add_argument("--out", default=None)
    ap.add_argument("--width", type=int, default=1000)
    ap.add_argument("--yoff", type=float, default=0.5,
                    help="percent below the fitted bottom rule to start the strip")
    ap.add_argument("--yheight", type=float, default=4.8,
                    help="strip height in percent")
    args = ap.parse_args(argv)
    tiles = []
    for spec in args.boards:
        cid, num = spec.split(":")
        n = int(num)
        rec = json.load(open(os.path.join(ROOT, *(BASES[cid] + ("%03d.json" % n,))),
                            encoding="utf-8"))
        m = re.search(r"PID:(\d+)\s+(R\d+)([\u5de6\u53f3])?", rec["source"]["page"])
        if not m:
            print(spec, "no page")
            continue
        pid, rid, side = m.groups()
        side = side or "\u53f3"
        cols, rows = fit(pid, rid, side)
        if not cols:
            print(spec, "no grid")
            continue
        region = "pct:%.2f,%.2f,%.2f,%.1f" % (cols[0], rows[-1] + args.yoff,
                                               cols[-1] - cols[0], args.yheight)
        out = os.path.join(os.environ.get("TEMP", "."), "hand_%s_%03d.png" % (cid, n))
        fetch(pid, rid, region, args.width, out)
        tiles.append(("%s %d printed? record=%s" % (cid, n, hand_of(rec["sfen"])), out))
    if not tiles:
        return 1
    imgs = [(label, Image.open(p).convert("L")) for label, p in tiles]
    W = max(im.width for _, im in imgs)
    H = sum(im.height for _, im in imgs) + 22 * len(imgs)
    sheet = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(sheet)
    y = 0
    for label, im in imgs:
        d.text((4, y + 4), label, fill=0)
        sheet.paste(im, (0, y + 20))
        y += im.height + 22
    p = args.out or os.path.join(ROOT, "hands-sheet.png")
    sheet.save(p)
    print(p, sheet.size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
