#!/usr/bin/env python3
"""check_moves.py — enumerate the legal checking moves on each draft board.

A tsume-shogi problem must start with a check, so the set of legal checking
moves is an independent constraint on both the board transcription and the
recorded first move (the "head" column of the solution volume).

For every problem this tool reports

  * q            the number of '?' squares in the board SFEN
  * checks       the number of legal checking moves (moves and drops), with
                 '?' squares treated as empty
  * head         whether the recorded first move is one of them
  * detail       the checking moves, so a human can compare with the source

Because '?' squares are treated as empty the count is an upper bound on the
moves that avoid them, but a check whose origin, path and destination avoid
every '?' square is legal in *any* completion of the board.

Usage:
    python tools/check_moves.py                  # both collections, q<=6
    python tools/check_moves.py seimyo --max-q 9
    python tools/check_moves.py --md --only-fail
    python tools/check_moves.py --candidates     # use banked 採用候補SFEN
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import validate  # noqa: E402

BASES = {
    "kanju": ("collections", "meiji", "kanju", "drafts"),
    "seimyo": ("collections", "edo", "seimyo", "drafts"),
}
KANJI = "零一二三四五六七八九"


def unknowns(body):
    """Squares that are '?' in the board part of an SFEN."""
    out = set()
    for row, rank in enumerate(body.split("/"), 1):
        f = 9
        for ch in rank:
            if ch.isdigit():
                f -= int(ch)
            else:
                if ch == "?":
                    out.add((f, row))
                f -= 1
    return out


def drop_ok(bd, kind, sq):
    """Drop legality for sente: empty square, not dead, no nifu."""
    f, r = sq
    if bd.sq.get(sq):
        return False
    if kind in ("P", "L") and r == 1:
        return False          # could never move again
    if kind == "N" and r <= 2:
        return False
    if kind == "P" and validate.file_pawn_count(bd, "b", f) > 0:
        return False          # nifu
    return True


def load_sfen(cid, n, use_candidates):
    p = os.path.join(ROOT, *BASES[cid], "%03d.json" % n)
    rec = json.load(open(p, encoding="utf-8"))
    sfen = rec["sfen"]
    if use_candidates and sfen.count("?") > 0:
        cand = [m.group(1) for m in
                (re.search(r"採用候補SFEN[:：]?\s*(\S+)", x) for x in rec.get("notes", []))
                if m]
        for c in reversed(cand):
            if c.count("/") == 8:
                return c if c.count(" b ") or c.count(" w ") else c + " b - 1"
    return sfen


def checks(bd):
    """All legal checking moves.

    Each entry is (kind, src, dest, promotes_now, src_promoted).  The last
    field distinguishes a tokin/knight/horse/dragon that is already promoted
    (promotes_now is False, but the piece on the destination is promoted)
    from a genuinely unpromoted piece that moved without promoting.
    """
    out = []
    k = validate.find_king(bd, "w")
    if not k:
        return out
    for (f, r), (side, kind, prom) in list(bd.sq.items()):
        if side != "b":
            continue
        for dest in validate.pseudo_targets(bd, (f, r)):
            # promotion choices: keep, or promote an unpromoted promotable piece
            opts = [False]
            if not prom and kind in validate.PROMOTABLE:
                opts.append(True)
            for p2 in opts:
                if p2 and (dest[1] > 3 and r > 3):
                    continue  # must promote: only when leaving the zone
                if not p2:
                    # a pawn/lance may not stay unpromoted on the last rank,
                    # nor a knight on the last two
                    if kind in ("P", "L") and dest[1] == 1:
                        continue
                    if kind == "N" and dest[1] <= 2:
                        continue
                b2 = bd.clone()
                b2.sq.pop((f, r))
                b2.sq[dest] = ["b", kind, prom or p2]
                if validate.is_attacked(b2, k, "b"):
                    out.append((kind, (f, r), dest, p2, prom))
    for kind in sorted(bd.hand["b"]):
        for f in range(1, 10):
            for r in range(1, 10):
                sq = (f, r)
                if not drop_ok(bd, kind, sq):
                    continue
                b2 = bd.clone()
                b2.sq[sq] = ["b", kind, False]
                if not validate.is_attacked(b2, validate.find_king(b2, "w"), "b"):
                    continue
                # 打ち歩詰め: a pawn drop that mates immediately is illegal
                if kind == "P":
                    b3 = b2.clone()
                    b3.side = "w"
                    if validate.is_mate(b3):
                        continue
                out.append((kind + "*", None, sq, False, False))
    return out


def lands_promoted(c):
    """Is the piece on the destination a promoted one after the move?"""
    return bool(c[3] or c[4])


def avoids(c, qs):
    """True when the move touches no '?' square at all."""
    kind, src, dest = c[0], c[1], c[2]
    if dest in qs:
        return False
    return not (src and src in qs)


def fmt(c):
    kind, src, dest, p2, sp = c
    if src is None:
        return "%s*%d%d" % (kind.rstrip("*"), dest[0], dest[1])
    mover = ("+" if sp else "") + kind
    return "%s%d%d%s<-%d%d" % (mover, dest[0], dest[1], "+" if p2 else "", src[0], src[1])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("collection", nargs="?", default="all",
                    choices=["all"] + sorted(BASES))
    ap.add_argument("--max-q", type=int, default=6,
                    help="skip boards with more '?' than this (default 6)")
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--only-fail", action="store_true",
                    help="only problems whose recorded head is not a checking move")
    ap.add_argument("--candidates", action="store_true",
                    help="prefer the banked 採用候補SFEN when it is complete")
    ap.add_argument("--moves", action="store_true", help="print every checking move")
    args = ap.parse_args(argv)

    cids = sorted(BASES) if args.collection == "all" else [args.collection]
    if args.md:
        print("| collection | # | q | checks | head | detail |")
        print("|---|---|---|---|---|---|")
    for cid in cids:
        mfile = os.path.join(ROOT, "docs", "%s-first-moves.json" % cid)
        moves = {m["number"]: m for m in json.load(open(mfile, encoding="utf-8"))["moves"]}
        for n in sorted(moves):
            m = moves[n]
            sfen = load_sfen(cid, n, args.candidates)
            q = sfen.count("?")
            if q > args.max_q:
                continue
            bd, errs = validate.parse_sfen(sfen.replace("?", "1"))
            if errs or not bd:
                print("%s %d BAD SFEN %s" % (cid, n, errs))
                continue
            if not validate.find_king(bd, "w"):
                print("%s %d NO KING" % (cid, n))
                continue
            ch = checks(bd)
            qs = unknowns(sfen.split(" ")[0])
            dest = (m["file"], m["rank"])
            kind = m["piece"]
            want_prom = bool(m.get("promoted"))
            head_ok = any(c[0].rstrip("*") == kind and c[2] == dest
                          and lands_promoted(c) == want_prom
                          for c in ch)
            if args.only_fail and head_ok:
                continue
            solid = [c for c in ch if avoids(c, qs)]
            detail = ", ".join(fmt(c) for c in (ch if args.moves else solid[:6]))
            if args.md:
                print("| %s | %d | %d | %d | %s | %s |"
                      % (cid, n, q, len(ch), "ok" if head_ok else "**FAIL**", detail))
            else:
                print("%-7s %3d q=%d checks=%-2d solid=%-2d head=%-4s %s"
                      % (cid, n, q, len(ch), len(solid), "ok" if head_ok else "FAIL", detail))
    return 0


if __name__ == "__main__":
    sys.exit(main())
