# -*- coding: utf-8 -*-
"""List the rule-clean candidates for specific cells.

    python cell_candidates.py <cid> <n> <file> <rank> [<file> <rank> ...]
"""
import argparse
import json
import sys

ROOT = r"E:\GitHub\edo_era_tsume_shogi"
sys.path.insert(0, ROOT + r"\tools")
import material_audit as ma
import validate

BASES = {"kanju": ("collections", "meiji", "kanju", "drafts"),
         "seimyo": ("collections", "edo", "seimyo", "drafts")}
CODES = []
for c in "PLNSGBR":
    CODES += [c.lower(), c, "+" + c.lower(), "+" + c]
CODES += ["k", "K"]


def cells(sfen):
    out = []
    for row in sfen.split(" ")[0].split("/"):
        c, i = [], 0
        while i < len(row):
            if row[i].isdigit():
                c.extend([""] * int(row[i]))
                i += 1
            elif row[i] == "+":
                c.append(row[i:i + 2])
                i += 2
            else:
                c.append(row[i])
                i += 1
        out.append(c)
    return out


def rebuild(grid, rest):
    rows = []
    for c in grid:
        s, run = "", 0
        for x in c:
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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('cid', choices=('seimyo', 'kanju'))
    ap.add_argument('n', type=int)
    ap.add_argument('cells', nargs='+', metavar='file rank',
                    help='one or more pairs of file rank')
    args = ap.parse_args(argv)
    cid, n = args.cid, args.n
    vals = [int(v) for v in args.cells]
    coords = list(zip(vals[0::2], vals[1::2]))
    rec = json.load(open("%s/%s/%03d.json" % (ROOT, "/".join(BASES[cid]), n),
                        encoding="utf-8"))
    sfen = rec["sfen"]
    g = cells(sfen)
    for file_, rank in coords:
        i = 9 - file_
        if g[rank - 1][i] != "?":
            print(cid, n, file_, rank, "not ?:", g[rank - 1][i])
            continue
        clean = []
        for code in [""] + CODES:
            g2 = [row[:] for row in g]
            g2[rank - 1][i] = code
            new = rebuild(g2, " ".join(sfen.split(" ")[1:]))
            bd, e = validate.parse_sfen(new.replace("?", "1"))
            if e:
                continue
            k = validate.find_king(bd, "w")
            if ma.nifu(new) or ma.dead_pieces(new) or ma.excess(new):
                continue
            if k and validate.is_attacked(bd, k, "b"):
                continue
            clean.append(code or "empty")
        print(cid, n, "f%d r%d" % (file_, rank),
              "clean:", " ".join(clean))


if __name__ == "__main__":
    main()
