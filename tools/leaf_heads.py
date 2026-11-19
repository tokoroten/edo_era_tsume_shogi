#!/usr/bin/env python3
"""Show which problems each recorded column head would check.

The 詰手 leaves and the board numbers drift (a problem's first column can sit
on a different leaf than its 題簽), so the reliable test is: place the piece on
the head's destination and ask whether it checks a problem's gote king.

Usage:
    python tools/leaf_heads.py R0000015
    python tools/leaf_heads.py R0000015 --range 50 59
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KANJI = "零一二三四五六七八九"
BASES = {
    "kanju": ("collections", "meiji", "kanju", "drafts"),
    "seimyo": ("collections", "edo", "seimyo", "drafts"),
}


def load_heads(cid, leaf):
    path = os.path.join(ROOT, "docs", "%s-column-heads.json" % cid)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [h for h in data["heads"] if h["leaf"] == leaf and h.get("raw")]


def dest_of(h):
    if "dest" in h:
        return int(h["dest"][0]), KANJI.index(h["dest"][1])
    raw = h["raw"]
    a, b = KANJI.index(raw[0]), KANJI.index(raw[1])
    if h.get("order") == "file-rank":
        return a, b
    return b, a


def load_board(cid, n):
    path = os.path.join(ROOT, *BASES[cid], "%03d.json" % n)
    with open(path, encoding="utf-8") as f:
        rec = json.load(f)
    return validate.parse_sfen(rec["sfen"].replace("?", "1"))[0]


def checks(bd, ksq, file, rank, piece, promoted):
    probe = bd.clone()
    probe.sq.pop(ksq, None)
    probe.sq[(file, rank)] = ["b", piece, promoted]
    return ksq in validate.pseudo_targets(probe, (file, rank))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("leaf")
    ap.add_argument("--collection", default="seimyo", choices=sorted(BASES))
    ap.add_argument("--range", nargs=2, type=int, metavar=("LO", "HI"))
    args = ap.parse_args(argv)

    heads = load_heads(args.collection, args.leaf)
    if not heads:
        print("no heads recorded for %s" % args.leaf)
        return 1
    lo, hi = args.range if args.range else (1, 100)
    boards = {}
    for n in range(lo, hi + 1):
        try:
            bd = load_board(args.collection, n)
        except IOError:
            continue
        ksq = validate.find_king(bd, "w")
        if ksq:
            boards[n] = (bd, ksq)

    print("%s: %d heads, %d boards (%d-%d)"
          % (args.leaf, len(heads), len(boards), lo, hi))
    for h in sorted(heads, key=lambda x: x["x_pct"], reverse=True):
        file, rank = dest_of(h)
        hits = [n for n, (bd, ksq) in sorted(boards.items())
                if checks(bd, ksq, file, rank, h["piece"],
                          bool(h.get("promoted")))]
        star = "*" if h.get("problem") in hits else " "
        where = "checks " + ",".join(map(str, hits)) if hits else "-"
        print("%s %-9s %-9s -> %d%s  %s"
              % (star, h["x_pct"], h["raw"], file,
                 "abcdefghi"[rank - 1], where))

    print("")
    print("-- per problem --")
    for n, (bd, ksq) in sorted(boards.items()):
        matches = []
        for h in sorted(heads, key=lambda x: x["x_pct"], reverse=True):
            file, rank = dest_of(h)
            if checks(bd, ksq, file, rank, h["piece"],
                      bool(h.get("promoted"))):
                matches.append(h["raw"])
        if len(matches) == 1:
            print("%3d  UNIQUE  %s" % (n, matches[0]))
        elif matches:
            print("%3d  %d heads: %s" % (n, len(matches), ", ".join(matches)))
        else:
            print("%3d  none" % n)

    singles = {}
    for n, (bd, ksq) in sorted(boards.items()):
        matches = []
        for h in heads:
            file, rank = dest_of(h)
            if checks(bd, ksq, file, rank, h["piece"],
                      bool(h.get("promoted"))):
                matches.append(h["raw"])
        if len(matches) == 1:
            singles.setdefault(matches[0], []).append(n)
    conflicts = dict((k, v) for k, v in singles.items() if len(v) > 1)
    if conflicts:
        print("")
        print("-- conflicts (one candidate for several problems) --")
        for raw in sorted(conflicts):
            print("%s: %s" % (raw, ", ".join(map(str, conflicts[raw]))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
