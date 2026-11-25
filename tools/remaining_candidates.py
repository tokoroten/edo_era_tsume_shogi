#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""List, for every unknown square, the pieces that could legally stand there.

    python tools/remaining_candidates.py [--check]

For each `?` square the tool substitutes every piece (both sides, promoted and
not) and keeps those that leave the position legal:

  * the 40-piece caps hold (material_audit.excess),
  * no two pawns of one side on a file (nifu),
  * no dead piece,
  * the kings that were on the board are still there,
  * the gote king is not in check (a tsume may not open with check).

An empty square is always a candidate in the list's sense (the print may show
nothing), and is reported first.  The output is `docs/remaining-candidates.md`.
"""
import glob
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import board_cell_ink as b  # noqa: E402
import material_audit as m  # noqa: E402
import validate  # noqa: E402

DOC = os.path.join(ROOT, "docs", "remaining-candidates.md")
KINDS = [("P", u"歩"), ("L", u"香"), ("N", u"桂"), ("S", u"銀"), ("G", u"金"),
         ("B", u"角"), ("R", u"飛")]
PROMOTED = [("+P", u"成歩"), ("+L", u"成香"), ("+N", u"成桂"), ("+S", u"成銀"),
            ("+B", u"成角"), ("+R", u"成飛")]


def set_cell(sfen, file, rank, piece):
    rows = sfen.split()[0].split("/")
    grid = b.sfen_grid(sfen)
    grid[rank - 1][9 - file] = piece
    rows = []
    for row in grid:
        out, run = "", 0
        for cell in row:
            if cell == "":
                run += 1
            else:
                if run:
                    out += str(run)
                    run = 0
                out += cell
        if run:
            out += str(run)
        rows.append(out)
    return "/".join(rows) + " " + " ".join(sfen.split()[1:])


def _kings(sfen):
    bd, errs = validate.parse_sfen(sfen.replace("?", "1"))
    if errs:
        return None
    return tuple(len([1 for _s, (c, k, _p) in bd.sq.items() if k == "K" and c == side])
                 for side in ("b", "w"))


def legal(sfen, base):
    """True when `sfen` keeps every rule and the kings the base position has."""
    if m.excess(sfen) or m.nifu(sfen) or m.dead_pieces(sfen):
        return False
    if _kings(sfen) != _kings(base):
        return False
    bd, errs = validate.parse_sfen(sfen.replace("?", "1"))
    if errs:
        return False
    k = validate.find_king(bd, "w")
    if k and validate.is_attacked(bd, k, "b"):
        return False
    return True


def rows():
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, "collections", "*", "*", "drafts", "*.json"))):
        rec = json.load(open(path, encoding="utf-8"))
        cid = rec.get("collection_id")
        if cid not in ("seimyo", "kanju"):
            continue
        sfen = rec["sfen"]
        if "?" not in sfen:
            continue
        grid = b.sfen_grid(sfen)
        for r in range(9):
            for c in range(9):
                if grid[r][c] != "?":
                    continue
                file, rank = 9 - c, r + 1
                cands = [u"空"]
                for code, label in KINDS + PROMOTED:
                    for side in ("b", "w"):
                        pc = code if side == "b" else code.lower()
                        if legal(set_cell(sfen, file, rank, pc), sfen):
                            cands.append(label + (u"(先)" if side == "b" else u"(後)"))
                out.append((cid, rec["number"], file, rank, cands))
    return out


def build():
    rs = rows()
    lines = [u"# 残った `?` と、規則上ありうる駒（自動生成）", u"",
             u"各升について「置いても材数・二歩・死に駒・玉1枚・初手未王手を破らない駒」を列挙した。",
             u"字形はこの中から選べばよい（空も候補）。%d題・%d升。" % (len(set((r[0], r[1]) for r in rs)), len(rs)),
             u"", u"| 題 | 升 | 候補数 | 候補 |", u"|---|---|---|---|"]
    for cid, num, f, r, cands in rs:
        lines.append("| %s %d | %d%s | %d | %s |" % (
            cid, num, f, u"一二三四五六七八九"[r - 1], len(cands), u"・".join(cands)))
    return "\n".join(lines) + "\n"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0
    new = build()
    if "--check" in argv:
        old = io.open(DOC, encoding="utf-8").read() if os.path.exists(DOC) else ""
        if new != old:
            print("remaining-candidates.md out of sync")
            return 1
        print("remaining-candidates.md in sync")
        return 0
    io.open(DOC, "w", encoding="utf-8", newline="\n").write(new)
    print("wrote docs/remaining-candidates.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
