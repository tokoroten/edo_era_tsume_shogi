#!/usr/bin/env python3
"""List recorded column heads that check only one of two neighbouring problems.

A column belongs to exactly one problem, and every sente move in a 詰手 is a
check, so a head that checks problem N but not N-1/N+1 is a strong candidate
for N's first move even when N's 題簽 position is uncertain.

Usage:
    python tools/first_move_gaps.py [--collection seimyo] [--near 1] [--near-leaf 1]

--near excludes heads that also check the neighbouring problems; --near-leaf
keeps only heads from leaves within N of the problem's own leaf.

Heads without a recorded dest are printed with both digit orders (段→筋 and
筋→段) because the order differs per problem; the one that checks is shown
as ``raw→dest``.
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
COUNTS = {"kanju": 50, "seimyo": 100}
# Leaf ranges from docs/procedures.md 1.1 (seimyo) and kanju-transcription 5.
SEIMYO_LEAVES = [
    (2, 2), (3, 6), (4, 10), (5, 14), (6, 19), (7, 23), (8, 28),
    (9, 32), (10, 37), (11, 41), (12, 44), (13, 49), (14, 54),
    (15, 59), (16, 62), (17, 66), (18, 70), (19, 73), (20, 78),
    (21, 82), (22, 85), (23, 89), (24, 93), (25, 96), (26, 100),
]


def dest_of(h):
    """Every plausible destination for a column head.

    Heads assigned to a problem carry the verified ``dest``. Unassigned
    heads only have the printed two digits, and the digit order is
    段→筋 for some problems and 筋→段 for others, so both readings are
    returned and the caller keeps the one that checks the king.
    """
    if "dest" in h:
        return [(int(h["dest"][0]), KANJI.index(h["dest"][1]))]
    try:
        a, b = KANJI.index(h["raw"][0]), KANJI.index(h["raw"][1])
    except (ValueError, IndexError):
        return []
    order = h.get("order")
    if order == "file-rank":
        return [(a, b)]
    if order == "rank-file":
        return [(b, a)]
    return [(b, a), (a, b)]


def board(cid, n):
    path = os.path.join(ROOT, *BASES[cid], "%03d.json" % n)
    with open(path, encoding="utf-8") as f:
        rec = json.load(f)
    return validate.parse_sfen(rec["sfen"].replace("?", "1"))[0]


def checks(bd, file, rank, piece, promoted):
    ksq = validate.find_king(bd, "w")
    if not ksq:
        return False
    probe = bd.clone()
    probe.sq.pop(ksq, None)
    probe.sq[(file, rank)] = ["b", piece, promoted]
    return ksq in validate.pseudo_targets(probe, (file, rank))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--collection", default="seimyo", choices=sorted(BASES))
    ap.add_argument("--near", type=int, default=1,
                    help="how many neighbours on each side to exclude")
    ap.add_argument("--near-leaf", type=int, default=1,
                    help="keep only heads within N leaves of the problem's leaf")
    args = ap.parse_args(argv)
    cid = args.collection
    with open(os.path.join(ROOT, "docs", "%s-column-heads.json" % cid),
              encoding="utf-8") as f:
        heads = [h for h in json.load(f)["heads"] if h.get("raw")]
    with open(os.path.join(ROOT, "docs", "%s-first-moves.json" % cid),
              encoding="utf-8") as f:
        done = {m["number"] for m in json.load(f)["moves"]}
    rpath = os.path.join(ROOT, "docs", "%s-procedure-readings.json" % cid)
    if os.path.exists(rpath):
        with open(rpath, encoding="utf-8") as f:
            done |= {r["number"] for r in json.load(f)["readings"]}
    boards = {}
    for n in range(1, COUNTS[cid] + 1):
        try:
            boards[n] = board(cid, n)
        except IOError:
            pass
    def leaf_of(n):
        if cid == "seimyo":
            for i, (lo, hi) in enumerate(SEIMYO_LEAVES):
                if lo <= n <= hi:
                    return 2 + i
        return None

    for n in range(1, COUNTS[cid] + 1):
        if n in done or n not in boards:
            continue
        home = leaf_of(n)
        others = [m for m in range(n - args.near, n + args.near + 1)
                  if m != n and m in boards]
        hits = []
        for h in heads:
            prom = bool(h.get("promoted"))
            if home is not None and args.near_leaf:
                try:
                    leaf = int(h["leaf"].lstrip("R"))
                except (KeyError, ValueError):
                    continue
                if abs(leaf - home) > args.near_leaf:
                    continue
            for file, rank in dest_of(h):
                if not checks(boards[n], file, rank, h["piece"], prom):
                    continue
                if any(checks(boards[m], file, rank, h["piece"], prom)
                       for m in others):
                    continue
                hits.append("%s→%d%s %s %s" % (
                    h["raw"], file, KANJI[rank], h["leaf"], h["x_pct"]))
                break
        if hits:
            print("%3d: %s" % (n, " / ".join(hits)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
