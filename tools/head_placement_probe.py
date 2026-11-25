#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Probe whether an unassigned head can be played at all.

    python tools/head_placement_probe.py

For each head marked `head_unassigned`, the tool places that head's piece (sente,
same promotion state) on every unknown square in turn and asks whether the
recorded move from there is legal and gives check, with the rest of the position
legal (material caps, no nifu, no dead piece, gote king not already in check).

If no square works, the head cannot be played in *any* completion of the board
where one unknown square holds that piece - so either the column attribution or
the printed head is wrong.  That is stronger than `head_check`'s MOVER?, which
only says the mover may be hiding on an unknown square.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import board_cell_ink as b  # noqa: E402
import material_audit as mat  # noqa: E402
import validate  # noqa: E402


def _sfen_with(sfen, f, r, piece):
    grid = b.sfen_grid(sfen)
    grid[r - 1][9 - f] = piece
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


def _legal(sfen):
    if mat.excess(sfen) or mat.nifu(sfen) or mat.dead_pieces(sfen):
        return False
    bd, errs = validate.parse_sfen(sfen.replace("?", "1"))
    if errs:
        return False
    k = validate.find_king(bd, "w")
    return not (k and validate.is_attacked(bd, k, "b"))


def _plays(sfen, m, f, r):
    piece = m["piece"]
    code = piece if piece.isupper() else piece.upper()
    if m.get("promoted"):
        code = "+" + code
    placed = _sfen_with(sfen, f, r, code)
    if not _legal(placed):
        return False
    bd, errs = validate.parse_sfen(placed.replace("?", "1"))
    if errs:
        return False
    dest = (m["file"], m["rank"])
    if dest not in validate.pseudo_targets(bd, (f, r)):
        return False
    occ = bd.sq.get(dest)
    if occ and occ[0] == "b":
        return False
    moved = bd.clone()
    moved.sq.pop((f, r), None)
    moved.sq[dest] = ["b", piece.upper(), bool(m.get("promoted")) or (occ[2] if occ else False)]
    k = validate.find_king(moved, "w")
    return bool(k and validate.is_attacked(moved, k, "b"))


def probe():
    out = []
    for cid, base in (("seimyo", "edo"), ("kanju", "meiji")):
        data = json.load(open(os.path.join(ROOT, "docs", "%s-first-moves.json" % cid),
                              encoding="utf-8"))
        for m in data["moves"]:
            if not m.get("head_unassigned") or not m.get("raw"):
                continue
            num = m["number"]
            rec = json.load(open(os.path.join(ROOT, "collections", base, cid, "drafts",
                                              "%03d.json" % num), encoding="utf-8"))
            sfen = rec["sfen"]
            grid = b.sfen_grid(sfen)
            qs = [(9 - c, r + 1) for r in range(9) for c in range(9) if grid[r][c] == "?"]
            if not qs:
                continue
            good = [(f, r) for (f, r) in qs if _plays(sfen, m, f, r)]
            out.append({"collection": cid, "number": num, "head": m["raw"],
                        "unknowns": len(qs), "viable": [list(g) for g in good]})
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0
    rows = probe()
    for r in rows:
        print("%s %d %s unknowns=%d viable=%d %s" % (
            r["collection"], r["number"], r["head"], r["unknowns"], len(r["viable"]),
            " ".join("%d%d" % tuple(v) for v in r["viable"])))
    dead = [r for r in rows if not r["viable"]]
    print("cannot be played even with one unknown square filled: %d of %d" % (len(dead), len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
