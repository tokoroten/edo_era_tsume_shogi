#!/usr/bin/env python3
"""material_audit.py — flag positions that use more pieces than exist.

A shogi set is finite: 18 pawns, 4 lances, 4 knights, 4 silvers, 4 golds,
2 bishops, 2 rooks, 2 kings.  Both players plus both hands draw from that one
set, and promoted pieces still count as their base type.  A transcribed
position that exceeds a limit is necessarily wrong, no matter how many models
agreed on the glyphs.

Usage:
    python tools/material_audit.py                 # both collections
    python tools/material_audit.py seimyo
    python tools/material_audit.py --md
"""
import argparse
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import validate  # noqa: E402

MAX = {"P": 18, "L": 4, "N": 4, "S": 4, "G": 4, "B": 2, "R": 2, "K": 2}
BASES = {
    "kanju": os.path.join("collections", "meiji", "kanju", "drafts"),
    "seimyo": os.path.join("collections", "edo", "seimyo", "drafts"),
}


def counts(sfen):
    """Piece-type totals for a draft SFEN, counting board and both hands."""
    bd, errs = validate.parse_sfen(sfen.replace("?", "1"))
    if errs or bd is None:
        return None
    out = {}
    for _sq, (_side, kind, _prom) in bd.sq.items():
        out[kind] = out.get(kind, 0) + 1
    for side in ("b", "w"):
        for kind, n in bd.hand[side].items():
            out[kind] = out.get(kind, 0) + n
    return out


def excess(sfen):
    """{piece type: count} for types that exceed the material limit."""
    c = counts(sfen)
    if c is None:
        return None
    return {k: v for k, v in c.items() if v > MAX.get(k, 0)}


def audit(cid):
    rows = []
    for path in sorted(glob.glob(os.path.join(ROOT, BASES[cid], "*.json"))):
        rec = json.load(open(path, encoding="utf-8"))
        bad = excess(rec["sfen"])
        if bad is None:
            rows.append((int(os.path.basename(path)[:3]), rec["sfen"].count("?"), "BAD SFEN"))
        elif bad:
            rows.append((int(os.path.basename(path)[:3]), rec["sfen"].count("?"), bad))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("collection", nargs="?", default="all",
                    choices=["all"] + sorted(BASES))
    ap.add_argument("--md", action="store_true")
    args = ap.parse_args(argv)
    cids = sorted(BASES) if args.collection == "all" else [args.collection]
    total = 0
    if args.md:
        print("| collection | # | q | excess |")
        print("|---|---|---|---|")
    for cid in cids:
        rows = audit(cid)
        total += len(rows)
        if args.md:
            for n, q, bad in rows:
                print("| %s | %d | %d | %s |" % (cid, n, q, bad))
        else:
            print(cid, "exceeding material limits:", len(rows))
            for n, q, bad in rows:
                print("   %3d q=%-2d %s" % (n, q, bad))
    return 0 if total else 0


if __name__ == "__main__":
    sys.exit(main())
