#!/usr/bin/env python3
"""head_check.py — verify recorded first moves against draft boards.

For each collection/problem with a first-move record:
  * king present, position not already in check
  * the recorded destination is reachable by a legal mover
      - a sente piece of that kind can legally move there (path included, via
        validate.pseudo_targets from the source square), or
      - the piece is in hand (drop)
  * placing the piece on the destination checks the gote king

'?' squares are treated as empty (so a False check is conclusive, a True one
is not).

Usage:
    python tools/head_check.py                 # both collections
    python tools/head_check.py kanju
    python tools/head_check.py --md            # markdown table
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import validate  # noqa: E402

BASES = {
    "kanju": ("collections", "meiji", "kanju", "drafts"),
    "seimyo": ("collections", "edo", "seimyo", "drafts"),
}


def load(cid, n):
    p = os.path.join(ROOT, *BASES[cid], "%03d.json" % n)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def check(cid, n, m):
    rec = load(cid, n)
    sfen = rec["sfen"]
    bd, errs = validate.parse_sfen(sfen.replace("?", "1"))
    if errs:
        return "BAD SFEN", errs[0]
    k = validate.find_king(bd, "w")
    if not k:
        return "NO KING", ""
    if validate.is_attacked(bd, k, "b"):
        if sfen.count("?"):
            return "PRE-CHECK?", ""
        return "PRE-CHECK", ""
    dest = (m["file"], m["rank"])
    kind, prom = m["piece"], bool(m.get("promoted"))
    src = None
    for sq, (side, kk, pp) in bd.sq.items():
        if side != "b" or kk != kind:
            continue
        # a promoting move ("成") starts from the unpromoted piece as well
        if pp and not prom:
            continue
        if not pp and not prom:
            pass
        if dest in validate.pseudo_targets(bd, sq):
            src = sq
            break
    drop = src is None and bd.hand["b"].get(kind, 0) > 0
    probe = bd.clone()
    occ = probe.sq.get(dest)
    if occ and occ[0] == "b":
        return "OWN PIECE", str(dest)
    probe.sq.pop(dest, None)
    probe.sq[dest] = ["b", kind, prom]
    hit = k in validate.pseudo_targets(probe, dest)
    if not hit:
        return "NO CHECK", str(dest)
    if src:
        return "OK", "move %s->%s" % (src, dest)
    if drop:
        return "OK(drop)", ""
    if sfen.count("?"):
        # the mover may sit on an untranscribed square
        return "MOVER?", str(dest)
    return "NO MOVER", str(dest)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("collection", nargs="?", default="all",
                    choices=["all"] + sorted(BASES))
    ap.add_argument("--md", action="store_true")
    args = ap.parse_args(argv)
    cids = sorted(BASES) if args.collection == "all" else [args.collection]
    if args.md:
        print("| collection | # | head | status | detail |")
        print("|---|---|---|---|---|")
    for cid in cids:
        with open(os.path.join(ROOT, "docs", "%s-first-moves.json" % cid),
                  encoding="utf-8") as f:
            moves = json.load(f)["moves"]
        counts = {}
        for m in moves:
            status, detail = check(cid, m["number"], m)
            counts[status] = counts.get(status, 0) + 1
            if args.md:
                if status not in ("OK", "OK(drop)"):
                    print("| %s | %d | %s | %s | %s |"
                          % (cid, m["number"], m.get("raw", ""), status, detail))
        if not args.md:
            print(cid, json.dumps(counts, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
