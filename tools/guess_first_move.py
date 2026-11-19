#!/usr/bin/env python3
"""List (piece, destination) candidates that check the gote king in a draft.

The 詰手 prints a two-character destination above the piece name. Reading those
small glyphs is error-prone (二/三 and 段/筋 order are easy to confuse), so this
tool inverts the check: for each piece type it prints every square from which
that piece would attack the gote king on the current draft board. A reading is
credible when its destination appears in this list.

Usage:
    python tools/guess_first_move.py kanju 14
    python tools/guess_first_move.py seimyo 35 [--all]
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RANKS = "abcdefghi"
KANJI_RANKS = "零一二三四五六七八九"

BASES = {
    "kanju": ("collections", "meiji", "kanju", "drafts"),
    "seimyo": ("collections", "edo", "seimyo", "drafts"),
}

PIECES = ["P", "L", "N", "S", "G", "B", "R", "K"]


def load(cid, number):
    path = os.path.join(ROOT, *BASES[cid], "%03d.json" % number)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def checks_from(bd, ksq, file, rank, code, promoted=False):
    """True iff the piece placed on (file, rank) itself attacks ksq.

    Uses pseudo_targets so blockers matter (unlike is_attacked, which also
    returns True when some *other* sente piece already attacks the king).
    """
    probe = bd.clone()
    probe.sq.pop(ksq, None)
    probe.sq[(file, rank)] = ["b", code, promoted]
    return ksq in validate.pseudo_targets(probe, (file, rank))


def candidates(bd, ksq):
    out = {}
    for code in PIECES:
        squares = []
        for f in range(1, 10):
            for r in range(1, 10):
                if (f, r) == ksq:
                    continue
                if checks_from(bd, ksq, f, r, code):
                    squares.append((f, r))
        if squares:
            out[code] = squares
    return out


def fmt(sq):
    f, r = sq
    return "%d%s" % (f, RANKS[r - 1])


def probe_pair(bd, ksq, pair, piece, promote):
    """Report both readings of a printed 2-digit pair and whether each checks."""
    kanji = "零一二三四五六七八九"
    if len(pair) != 2 or any(ch not in kanji for ch in pair):
        print("pair must be two digits from 一二三四五六七八九")
        return 2
    if piece not in PIECES:
        print("piece must be one of %s" % " ".join(PIECES))
        return 2
    a = kanji.index(pair[0])
    b = kanji.index(pair[1])
    for label, rank, file in (("段\u2192筋", a, b), ("筋\u2192段", b, a)):
        ok = checks_from(bd, ksq, file, rank, piece, bool(promote))
        print("%s: %s = %d%s %s%s" % (
            label, piece, file, RANKS[rank - 1],
            "王手" if ok else "王手にならない",
            "\uff08\u6210\uff09" if promote else ""))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cid", choices=sorted(BASES))
    ap.add_argument("number", type=int)
    ap.add_argument("--all", action="store_true",
                    help="also print promoted pieces")
    ap.add_argument("--pair", help="printed 2-digit pair, e.g. 八四")
    ap.add_argument("--piece", help="piece code for --pair (P L N S G B R K)")
    ap.add_argument("--promote", action="store_true",
                    help="treat the --pair move as promoting")
    args = ap.parse_args(argv)

    rec = load(args.cid, args.number)
    sfen = rec["sfen"]
    bd, errs = validate.parse_sfen(sfen.replace("?", "1"))
    if bd is None:
        print("invalid sfen: %s" % errs)
        return 2
    ksq = validate.find_king(bd, "w")
    if ksq is None:
        print("no gote king in draft")
        return 2

    print("%s 第%d番 後手玉: %s (?=%d)"
          % (args.cid, args.number, fmt(ksq), sfen.count("?")))
    print("持駒: %s" % sfen.split(" ")[2])
    print("")
    if args.pair:
        return probe_pair(bd, ksq, args.pair, args.piece, args.promote)
    cand = candidates(bd, ksq)
    promo = {"P": "+P", "L": "+L", "N": "+N", "S": "+S", "B": "+B", "R": "+R"}
    for code in PIECES:
        if code not in cand:
            continue
        print("%-2s: %s" % (code, " ".join(fmt(s) for s in cand[code])))
        if args.all and code in promo:
            sq_list = []
            for f in range(1, 10):
                for r in range(1, 10):
                    if (f, r) == ksq:
                        continue
                    if checks_from(bd, ksq, f, r, code, True):
                        sq_list.append((f, r))
            if sq_list:
                print("%-2s: %s" % (promo[code],
                                   " ".join(fmt(s) for s in sq_list)))
    if not cand:
        print("(どの駒も王手にならない: 玉位置か盤面を再確認)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
