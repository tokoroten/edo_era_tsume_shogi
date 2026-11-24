#!/usr/bin/env python3
"""Scan single-square repairs for the unassigned position heads.

Usage:
    python tools/head_repair_scan.py            # add-piece and kind-change
    python tools/head_repair_scan.py --shift    # whole-board +-1 file

A head is "unassigned" when the printed first move cannot be played on the
recorded board.  Three repairs are tried, each requiring that the head become
a legal, checking first move AND that the board still passes the material
audit (no nifu, no excess, no dead piece):

  add    put the moving piece (correctly promoted or not) on one empty square
  kind   change the kind of one occupied square, keeping its side
  shift  move every piece one file left or right, dropping what falls off

MOVER STATE.  The dataset's `promoted` flag records the ARRIVAL state, so a
head printed ...角成 has promoted=True while the piece that moved is a plain
bishop.  Before 2026-11-25 these scans looked for a promoted mover on such
heads, which is impossible; that inflated the add-piece count from 15 to 24.
`mover_prom()` now derives the mover state from the printed head.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import material_audit as ma
import validate

BASES = {"kanju": ("collections", "meiji", "kanju", "drafts"),
         "seimyo": ("collections", "edo", "seimyo", "drafts")}
CODES = ["P", "L", "N", "S", "G", "B", "R", "+P", "+L", "+N", "+S", "+B", "+R"]


def mover_prom(raw):
    """Promotion state of the piece that MOVES, from the printed head."""
    r = raw.replace("打", "")
    if r.endswith("成"):
        return False
    if "馬" in r or "龍" in r or "竜" in r:
        return True
    return False


def grid(sfen):
    out = []
    for row in sfen.split(" ")[0].split("/"):
        cells, i = [], 0
        while i < len(row):
            if row[i].isdigit():
                cells.extend([""] * int(row[i]))
                i += 1
            elif row[i] == "+":
                cells.append(row[i:i + 2])
                i += 2
            else:
                cells.append(row[i])
                i += 1
        out.append(cells)
    return out


def rebuild(g, rest):
    rows = []
    for cells in g:
        s, run = "", 0
        for x in cells:
            if x == "":
                run += 1
                continue
            if run:
                s += str(run)
                run = 0
            s += x
        if run:
            s += str(run)
        rows.append(s)
    return "/".join(rows) + " " + rest


def can_play(sfen, kind, prom, dest):
    bd, errs = validate.parse_sfen(sfen.replace("?", "1"))
    if errs:
        return False
    king = validate.find_king(bd, "w")
    if not king or validate.is_attacked(bd, king, "b"):
        return False
    src = None
    for sq, (side, kk, pp) in bd.sq.items():
        if side == "b" and kk == kind and pp == prom and dest in validate.pseudo_targets(bd, sq):
            src = sq
            break
    if src is None:
        return False
    probe = bd.clone()
    probe.sq.pop(src)
    probe.sq[dest] = ["b", kind, prom]
    return validate.is_attacked(probe, king, "b")


def clean(sfen):
    s = sfen.replace("?", "1")
    return not ma.nifu(s) and not ma.excess(s) and not ma.dead_pieces(s)


def code_of(cell):
    if not cell:
        return None, None
    if cell.startswith("+"):
        body = cell[1]
        return ("b" if body.isupper() else "w"), "+" + body.upper()
    return ("b" if cell[0].isupper() else "w"), cell[0].upper()


def encode(side, code):
    if code.startswith("+"):
        body = code[1]
        return "+" + (body if side == "b" else body.lower())
    return code if side == "b" else code.lower()


def shift(g, k):
    out = []
    for cells in g:
        row = [""] * 9
        for i, x in enumerate(cells):
            if x and 0 <= i + k < 9:
                row[i + k] = x
        out.append(row)
    return out


def heads():
    for cid, base in BASES.items():
        path = os.path.join(ROOT, "docs", "%s-first-moves.json" % cid)
        data = json.load(open(path, encoding="utf-8"))
        for m in data["moves"]:
            if not m.get("head_unassigned"):
                continue
            draft = os.path.join(ROOT, *(base + ("%03d.json" % m["number"],)))
            sfen = json.load(open(draft, encoding="utf-8"))["sfen"]
            yield cid, m, sfen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shift", action="store_true", help="test whole-board one-file shifts")
    args = ap.parse_args()

    if args.shift:
        tally = {"-1": 0, "+1": 0, "both": 0, "none": 0}
        for cid, m, sfen in heads():
            g = grid(sfen)
            rest = " ".join(sfen.split(" ")[1:])
            dest = (m["file"], m["rank"])
            mp = mover_prom(m["raw"])
            ok = [k for k in (-1, 1)
                  if can_play(rebuild(shift(g, k), rest), m["piece"], mp, dest)]
            key = "both" if len(ok) == 2 else ("%+d" % ok[0] if ok else "none")
            tally[key] += 1
        print(tally)
        return

    rows = []
    for cid, m, sfen in heads():
        g = grid(sfen)
        rest = " ".join(sfen.split(" ")[1:])
        dest = (m["file"], m["rank"])
        mp = mover_prom(m["raw"])
        add, kind = [], []
        for r in range(9):
            for c in range(9):
                if g[r][c] != "":
                    continue
                g2 = [row[:] for row in g]
                g2[r][c] = encode("b", ("+" if mp else "") + m["piece"])
                s2 = rebuild(g2, rest)
                if can_play(s2, m["piece"], mp, dest) and clean(s2):
                    add.append((9 - c, r + 1))
        for r in range(9):
            for c in range(9):
                side, old = code_of(g[r][c])
                if side is None:
                    continue
                for new in CODES:
                    if new == old:
                        continue
                    g2 = [row[:] for row in g]
                    g2[r][c] = encode(side, new)
                    s2 = rebuild(g2, rest)
                    if can_play(s2, m["piece"], mp, dest) and clean(s2):
                        kind.append(((9 - c, r + 1), old, new))
        rows.append((cid, m["number"], m["raw"], mp, add, kind))

    print("%-8s %-4s %-9s %-6s %-24s %s"
          % ("book", "no", "head", "mover", "add-piece", "kind-change"))
    for cid, n, raw, mp, add, kind in rows:
        print("%-8s %3d %-9s %-6s %-24s %s"
              % (cid, n, raw, "prom" if mp else "plain",
                 (str(add[:2]) + ("..." if len(add) > 2 else "")) if add else "-",
                 (str(kind[:2]) + ("..." if len(kind) > 2 else "")) if kind else "-"))
    print()
    print("heads:", len(rows),
          " add-piece repairs:", sum(1 for x in rows if x[4]),
          " unique:", sum(1 for x in rows if len(x[4]) == 1))
    print("kind-change repairs:", sum(1 for x in rows if x[5]),
          " unique:", sum(1 for x in rows if len(x[5]) == 1))
    print("neither:", sum(1 for x in rows if not x[4] and not x[5]))


if __name__ == "__main__":
    main()
