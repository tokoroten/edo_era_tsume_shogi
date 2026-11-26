#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-measure a draft against the printed board using the frame stored in it.

    python tools/remeasure_board.py gyokuzu 8
    python tools/remeasure_board.py --all
    python tools/remeasure_board.py --all --write   # docs/frame-audit.md
    python tools/remeasure_board.py --all --check

Drafts that have been read from a measured frame carry it in
`source.frame` ({pid, rid, corners, mirror}).  Keeping the frame with the
record means the measurement can be repeated later without re-deriving the
four corners from the notes.
"""
import argparse
import glob
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import board_cell_ink as b  # noqa: E402

BASES = {
    "seimyo": os.path.join("edo", "seimyo"),
    "kanju": os.path.join("meiji", "kanju"),
    "gyokuzu": os.path.join("edo", "gyokuzu"),
    "meijin": os.path.join("taisho", "meijin"),
    "shiroto": os.path.join("taisho", "shiroto"),
}
DOC = os.path.join(ROOT, "docs", "frame-audit.md")


def measure(rec):
    frame = rec.get("source", {}).get("frame")
    if not frame:
        return None
    xs = frame["corners"][0::2]
    ys = frame["corners"][1::2]
    pad = 0.04
    region = "pct:%.2f,%.2f,%.2f,%.2f" % (
        min(xs) - pad, min(ys) - pad,
        max(xs) - min(xs) + 2 * pad, max(ys) - min(ys) + 2 * pad)
    img = b.fetch(frame["pid"], frame["rid"], region, 2000)
    sq = b.warp(img, region, b.parse_corners(",".join(str(v) for v in frame["corners"])),
                side=1800)
    cells = b.ink_matrix(sq)
    grid = b.sfen_grid(rec["sfen"])
    if frame.get("mirror"):
        grid = b.mirror_grid(grid)
    return b.agreement(cells, grid)


def all_rows():
    rows = []
    for base in sorted(BASES):
        for p in sorted(glob.glob(os.path.join(ROOT, "collections", BASES[base],
                                               "drafts", "*.json"))):
            rec = json.load(io.open(p, encoding="utf-8"))
            got = measure(rec)
            if got:
                rows.append((base, rec["number"], got[0], got[1]))
    return rows


def build_doc(rows):
    lines = [
        u"# 保存した枠の再測定（自動生成）",
        u"",
        u"`source.frame` に保存した四隅で、draft の盤面と印字の占有を比べた結果。",
        u"`--mirror` は玉図のように画像左＝f1の本で列を反転して比べる指定。",
        u"81/81 は「その枠で draft の配置が印字と完全に一致」を意味する。",
        u"",
        u"`python tools/remeasure_board.py --all --write` で作り直す。",
        u"",
        u"| 書 | 題 | 一致 |",
        u"|---|---|---|",
    ]
    for base, n, ok, t in rows:
        lines.append(u"| %s | %d | %d/%d |" % (base, n, ok, t))
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("collection", nargs="?", choices=sorted(BASES))
    ap.add_argument("number", nargs="?", type=int)
    ap.add_argument("--all", action="store_true", help="every draft that has a frame")
    ap.add_argument("--write", action="store_true", help="write docs/frame-audit.md")
    ap.add_argument("--check", action="store_true", help="check docs/frame-audit.md")
    args = ap.parse_args(argv)
    if args.write or args.check:
        rows = all_rows()
        text = build_doc(rows)
        if args.write:
            io.open(DOC, "w", encoding="utf-8", newline="\n").write(text)
            print("wrote docs/frame-audit.md", len(rows))
            return 0
        old = io.open(DOC, encoding="utf-8").read() if os.path.exists(DOC) else ""
        if old != text:
            print("docs/frame-audit.md out of sync")
            return 1
        print("docs/frame-audit.md in sync")
        return 0
    if args.all:
        for base, n, ok, t in all_rows():
            print("%-8s %3d  %d/%d" % (base, n, ok, t))
        return 0
    if not args.collection or args.number is None:
        ap.print_help()
        return 2
    base = BASES[args.collection]
    p = os.path.join(ROOT, "collections", base, "drafts", "%03d.json" % args.number)
    rec = json.load(io.open(p, encoding="utf-8"))
    got = measure(rec)
    if not got:
        print("no frame stored for %s %d" % (args.collection, args.number))
        return 1
    print("%s %d  %d/%d" % (args.collection, args.number, got[0], got[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
