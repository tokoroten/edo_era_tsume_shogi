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
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import validate  # noqa: E402

MAX = {"P": 18, "L": 4, "N": 4, "S": 4, "G": 4, "B": 2, "R": 2, "K": 2}
# One player owns at most nine pawns, four of each minor, two great pieces, one king.
# These are separate from MAX: a position can be under the combined limit and still
# give one side more pieces than it has (see docs/per-side-audit.md).
SIDE_MAX = {"P": 9, "L": 4, "N": 4, "S": 4, "G": 4, "B": 2, "R": 2, "K": 1}
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


def side_counts(sfen):
    """Per-side piece totals for a draft SFEN, counting each side's own hand."""
    bd, errs = validate.parse_sfen(sfen.replace("?", "1"))
    if errs or bd is None:
        return None
    out = {"b": {}, "w": {}}
    for _sq, (side, kind, _prom) in bd.sq.items():
        out[side][kind] = out[side].get(kind, 0) + 1
    for side in ("b", "w"):
        for kind, n in bd.hand[side].items():
            out[side][kind] = out[side].get(kind, 0) + n
    return out


def side_excess(sfen):
    """[(side, kind, count)] for each side holding more of a kind than it owns.

    A side owns nine pawns and one king, so ten sente pawns is impossible
    however the totals add up.  This catches drafts that pass `excess` because
    one side was given another side's pieces.
    """
    c = side_counts(sfen)
    if c is None:
        return None
    out = []
    for side in ("b", "w"):
        for kind, n in sorted(c[side].items()):
            if n > SIDE_MAX.get(kind, 0):
                out.append((side, kind, n))
    return out


def dead_pieces(sfen):
    """Squares holding a base pawn/lance/knight that could never move again."""
    bd, errs = validate.parse_sfen(sfen.replace("?", "1"))
    if errs or bd is None:
        return None
    out = []
    for (f, r), (side, kind, prom) in bd.sq.items():
        if prom:
            continue
        if kind in ("P", "L") and ((side == "b" and r == 1) or (side == "w" and r == 9)):
            out.append((f, r, side + kind))
        if kind == "N" and ((side == "b" and r <= 2) or (side == "w" and r >= 8)):
            out.append((f, r, side + kind))
    return out


def nifu(sfen):
    """Two unpromoted pawns of one side on the same file (illegal)."""
    bd, errs = validate.parse_sfen(sfen.replace("?", "1"))
    if errs or bd is None:
        return None
    per = {}
    for (f, _r), (side, kind, prom) in bd.sq.items():
        if kind == "P" and not prom:
            per[(side, f)] = per.get((side, f), 0) + 1
    return [(f, side, n) for (side, f), n in sorted(per.items()) if n > 1]


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
        dead = dead_pieces(rec["sfen"])
        twin = nifu(rec["sfen"])
        if bad is None:
            rows.append((int(os.path.basename(path)[:3]), rec["sfen"].count("?"), "BAD SFEN"))
            continue
        if bad or dead or twin:
            rows.append((int(os.path.basename(path)[:3]), rec["sfen"].count("?"),
                         {"excess": bad, "dead": dead, "nifu": twin}))
    return rows


def side_audit(pattern=None):
    """Every draft whose transcription gives one side more of a kind than it owns."""
    pat = pattern or os.path.join(ROOT, "collections", "*", "*", "drafts", "*.json")
    rows = []
    for path in sorted(glob.glob(pat)):
        rec = json.load(open(path, encoding="utf-8"))
        bad = side_excess(rec["sfen"])
        if bad is None:
            rows.append((rec.get("collection_id"), rec.get("number"), rec["sfen"].count("?"), "BAD SFEN"))
        elif bad:
            rows.append((rec.get("collection_id"), rec.get("number"), rec["sfen"].count("?"), bad))
    return rows


def build_per_side():
    """Markdown for docs/per-side-audit.md."""
    rows = side_audit()
    lines = [
        u"# 一人分の駒数を超えている draft（自動生成）",
        u"",
        u"駒は一人につき 歩9・香4・桂4・銀4・金4・角2・飛2・玉1 まで。合計（歩18 など）が",
        u"足りていても、片方に寄りすぎた盤面は**その側の駒を他から借りている**ので、必ず",
        u"読み違いがある。ここに挙がった draft は、材数だけでは気づけない誤りを含む。",
        u"",
        u"`python tools/material_audit.py --per-side --write` で作り直す。",
        u"",
        u"| 書 | 題 | `?` | 超過 |",
        u"|---|---|---|---|",
    ]
    names = {"b": u"先手", "w": u"後手"}
    kinds = {"P": u"歩", "L": u"香", "N": u"桂", "S": u"銀", "G": u"金",
             "B": u"角", "R": u"飛", "K": u"玉"}
    for cid, n, q, bad in rows:
        if isinstance(bad, str):
            lines.append(u"| %s | %s | %d | %s |" % (cid, n, q, bad))
            continue
        text = u"・".join(u"%s%s %d枚" % (names[s], kinds.get(k, k), c) for s, k, c in bad)
        lines.append(u"| %s | %s | %d | %s |" % (cid, n, q, text))
    return "\n".join(lines) + "\n"


DOC = os.path.join(ROOT, "docs", "per-side-audit.md")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("collection", nargs="?", default="all",
                    choices=["all"] + sorted(BASES))
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--per-side", action="store_true",
                    help="report sides holding more pieces than one player owns")
    ap.add_argument("--write", action="store_true",
                    help="write docs/per-side-audit.md (with --per-side)")
    ap.add_argument("--check", action="store_true",
                    help="check docs/per-side-audit.md is in sync (with --per-side)")
    args = ap.parse_args(argv)
    if args.per_side:
        if args.write:
            io.open(DOC, "w", encoding="utf-8", newline="\n").write(build_per_side())
            print("wrote docs/per-side-audit.md")
            return 0
        if args.check:
            old = io.open(DOC, encoding="utf-8").read() if os.path.exists(DOC) else ""
            if old != build_per_side():
                print("docs/per-side-audit.md out of sync")
                return 1
            print("docs/per-side-audit.md in sync")
            return 0
        rows = side_audit()
        if args.md:
            print("| collection | # | q | over one side's set |")
            print("|---|---|---|---|")
            for cid, n, q, bad in rows:
                print("| %s | %s | %d | %s |" % (cid, n, q, bad))
        else:
            print("drafts that give one side more pieces than it owns:", len(rows))
            for cid, n, q, bad in rows:
                print("   %-8s %3s q=%-2d %s" % (cid, n, q, bad))
        return 0
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
            print(cid, "positions that break the piece rules:", len(rows))
            for n, q, bad in rows:
                print("   %3d q=%-2d %s" % (n, q, bad))
    return 0 if total else 0


if __name__ == "__main__":
    sys.exit(main())
