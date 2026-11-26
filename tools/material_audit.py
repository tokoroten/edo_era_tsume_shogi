#!/usr/bin/env python3
"""material_audit.py — flag positions that use more pieces than exist.

A shogi set is finite: 18 pawns, 4 lances, 4 knights, 4 silvers, 4 golds,
2 bishops, 2 rooks, 2 kings.  Both players plus both hands draw from that one
set, and promoted pieces still count as their base type.  A transcribed
position that exceeds a limit is necessarily wrong, no matter how many models
agreed on the glyphs.

Usage:
    python tools/material_audit.py                 # every collection with drafts
    python tools/material_audit.py seimyo
    python tools/material_audit.py --md
    python tools/material_audit.py --write         # docs/material-audit.md
    python tools/material_audit.py --check

The audit covers every collection, not only the two that are transcribed in
full: the other collections were never run through it, and a complete-looking
board can still hold two pawns of one side on a file.
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
# Boards whose *print* carries more of a kind than one set holds.  The tsume
# collections give the defender extra material, and gyokuzu prints five golds on
# several boards (five glyphs, all with the two inner strokes of 金 - see
# docs/open-issues.json gyokuzu-014-material and -037-material).  These are not
# transcription errors, and the boards must not be bent to satisfy the cap.
PRINTED_EXCESS = {("gyokuzu", 14), ("gyokuzu", 37), ("gyokuzu", 96), ("gyokuzu", 99), ("gyokuzu", 100)}
def collection_dirs():
    """collection_id -> drafts directory, for every collection that has drafts."""
    out = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "collections", "*", "*", "drafts"))):
        if glob.glob(os.path.join(path, "*.json")):
            out[os.path.basename(os.path.dirname(path))] = path
    return out


BASES = collection_dirs()


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
    for path in sorted(glob.glob(os.path.join(BASES[cid], "*.json"))):
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


def violation_squares(sfen):
    """[(reason, squares)] - the squares a re-reader must look at.

    One entry per rule broken, with the exact squares involved, so a violation
    turns into a short list of cells instead of a whole board.
    """
    bd, errs = validate.parse_sfen(sfen.replace("?", "1"))
    if errs or bd is None:
        return None
    out = []
    per = {}
    for (f, r), (side, kind, prom) in bd.sq.items():
        if kind == "P" and not prom:
            per.setdefault((side, f), []).append((f, r))
    for (side, f), sqs in sorted(per.items()):
        if len(sqs) > 1:
            out.append((u"二歩 %d筋 %s" % (f, u"先手" if side == "b" else u"後手"),
                        sorted(sqs)))
    for f, r, piece in dead_pieces(sfen) or []:
        out.append((u"死に駒 %s" % piece, [(f, r)]))
    for kind in sorted(excess(sfen) or {}):
        sqs = sorted((f, r) for (f, r), (_s, k, _p) in bd.sq.items() if k == kind)
        out.append((u"総数超過 %s（盤上%d枚）" % (kind, len(sqs)), sqs))
    return out


def build_squares():
    """Markdown for docs/violation-squares.md."""
    lines = [
        u"# 規則違反の升（自動生成）",
        u"",
        u"`docs/material-audit.md` の違反を、**読み直すべき升**まで落とした一覧。",
        u"二歩は同じ筋の歩を全部、死に駒はその升、総数超過はその種類の駒を全部挙げる。",
        u"この升のどれかが誤っているので、原寸で字を見れば違反は解ける。",
        u"",
        u"`python tools/material_audit.py --squares --write` で作り直す。",
        u"",
    ]
    for cid in sorted(BASES):
        rows = []
        for path in sorted(glob.glob(os.path.join(BASES[cid], "*.json"))):
            rec = json.load(open(path, encoding="utf-8"))
            bad = violation_squares(rec["sfen"])
            if bad:
                rows.append((rec.get("number"), rec["sfen"].count("?"), bad))
        if not rows:
            continue
        lines.append(u"## %s" % cid)
        lines.append(u"")
        lines.append(u"| 題 | `?` | 見る升 |")
        lines.append(u"|---|---|---|")
        for n, q, bad in rows:
            parts = []
            for reason, sqs in bad:
                text = u"・".join(u"%d%d" % (f, r) for f, r in sqs) or u"—"
                parts.append(u"%s: %s" % (reason, text))
            lines.append(u"| %d | %d | %s |" % (n, q, u"<br>".join(parts)))
        lines.append(u"")
    return "\n".join(lines) + "\n"


def build_material():
    """Markdown for docs/material-audit.md (every collection)."""
    lines = [
        u"# 駒の規則に反している draft（自動生成）",
        u"",
        u"駒一式は 歩18・香4・桂4・銀4・金4・角2・飛2・玉2。成駒は元の種類で数える。",
        u"この上限を超える盤面と、同じ側の不成の歩が同じ筋に2枚ある盤面（二歩）、",
        u"動けない位置に残った歩・香・桂（死に駒）は、**印刷をどう読んでも成立しない**ので、",
        u"転記の誤りである。修正は原寸の読みにしか戻せないが、ここに挙がった題は",
        u"「完成」と数えてはいけない。**（印字）** を付けた題は、監査ではなく**印字そのもの**が",
        u"上限を超えている（詰将棋は玉方に余分な駒を与えることがあり、玉図は金5枚・銀5枚の図を",
        u"複数刷っている。docs/open-issues.json の gyokuzu-014-material / -037-material /",
        u"-096-material / -099-material / -100-material）。",
        u"盤面は曲げない。",
        u"",
        u"`python tools/material_audit.py --write` で作り直す。",
        u"",
        u"| 書 | 題 | `?` | 内容 |",
        u"|---|---|---|---|",
    ]
    kinds = {"P": u"歩", "L": u"香", "N": u"桂", "S": u"銀", "G": u"金",
             "B": u"角", "R": u"飛", "K": u"玉"}
    for cid in sorted(BASES):
        for n, q, bad in audit(cid):
            if isinstance(bad, str):
                lines.append(u"| %s | %d | %d | %s |" % (cid, n, q, bad))
                continue
            parts = []
            ex = bad.get("excess")
            if ex:
                mark = u"（印字）" if (cid, n) in PRINTED_EXCESS else u""
                parts.append(u"総数超過 " + u"・".join(
                    u"%s%d枚" % (kinds.get(k, k), v) for k, v in sorted(ex.items())) + mark)
            ni = bad.get("nifu")
            if ni:
                parts.append(u"二歩 " + u"・".join(
                    u"%d筋%s" % (f, u"先手" if s == "b" else u"後手") for f, s, _n in ni))
            de = bad.get("dead")
            if de:
                parts.append(u"死に駒 " + u"・".join(
                    u"%d%d" % (f, r) for f, r, _p in de))
            lines.append(u"| %s | %d | %d | %s |" % (cid, n, q, u"／".join(parts)))
    return "\n".join(lines) + "\n"


PER_SIDE_DOC = os.path.join(ROOT, "docs", "per-side-audit.md")
MATERIAL_DOC = os.path.join(ROOT, "docs", "material-audit.md")
SQUARES_DOC = os.path.join(ROOT, "docs", "violation-squares.md")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("collection", nargs="?", default="all",
                    choices=["all"] + sorted(BASES))
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--per-side", action="store_true",
                    help="report sides holding more pieces than one player owns")
    ap.add_argument("--squares", action="store_true",
                    help="list the squares to re-read for each violation")
    ap.add_argument("--write", action="store_true",
                    help="write the audit markdown (docs/material-audit.md, or "
                         "docs/per-side-audit.md with --per-side, or "
                         "docs/violation-squares.md with --squares)")
    ap.add_argument("--check", action="store_true",
                    help="check the audit markdown is in sync")
    args = ap.parse_args(argv)
    if args.write or args.check:
        if args.squares:
            doc, text = SQUARES_DOC, build_squares()
        elif args.per_side:
            doc, text = PER_SIDE_DOC, build_per_side()
        else:
            doc, text = MATERIAL_DOC, build_material()
        if args.write:
            io.open(doc, "w", encoding="utf-8", newline="\n").write(text)
            print("wrote", os.path.relpath(doc, ROOT))
            return 0
        old = io.open(doc, encoding="utf-8").read() if os.path.exists(doc) else ""
        if old != text:
            print(os.path.relpath(doc, ROOT), "out of sync")
            return 1
        print(os.path.relpath(doc, ROOT), "in sync")
        return 0
    if args.per_side:
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
