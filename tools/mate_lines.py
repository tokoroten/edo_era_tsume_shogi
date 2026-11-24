#!/usr/bin/env python3
"""mate_lines.py — prove mates and list their principal variations.

This is an AND/OR search, not a line sampler:

* at a sente node, ONE checking move must survive **every** gote reply;
* at a gote node, **all** legal replies must lose.

    python tools/mate_lines.py kanju 44 --max-ply 9
    python tools/mate_lines.py kanju 44 --prefix "三三飛打 同香" --max-ply 13

`replay_line.py` verifies a single line; this tool proves that the attack
works against all defences and reports how many first moves do.
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import check_moves as cm  # noqa: E402
import replay_line as rl  # noqa: E402
import validate  # noqa: E402


def sig(bd):
    return (bd.side,
            tuple(sorted((sq, tuple(v)) for sq, v in bd.sq.items())),
            tuple(sorted((s, k, n) for s, h in bd.hand.items() for k, n in h.items() if n)))


def apply(bd, usi, side):
    b2 = bd.clone()
    validate.apply_usi(b2, usi)
    b2.side = "w" if side == "b" else "b"
    return b2


def sente_wins(bd, n, memo):
    if n <= 0:
        return False
    key = (sig(bd), n)
    if key in memo:
        return memo[key]
    for usi, _note in rl.legal_moves(bd, "b"):
        if gote_loses(apply(bd, usi, "b"), n - 1, memo):
            memo[key] = True
            return True
    memo[key] = False
    return False


def gote_loses(bd, n, memo):
    king = validate.find_king(bd, "w")
    if king is None or not validate.is_attacked(bd, king, "b"):
        return False          # the attacker stopped checking
    replies = rl.defender_moves(bd)
    if not replies:
        return True           # mate
    if n <= 0:
        return False
    key = (sig(bd), n)
    if key in memo:
        return memo[key]
    for usi, _note in replies:
        if not sente_wins(apply(bd, usi, "w"), n - 1, memo):
            memo[key] = False
            return False
    memo[key] = True
    return True


def pv(bd, n, memo, out):
    """Follow one proven winning line."""
    if bd.side == "b":
        for usi, note in rl.legal_moves(bd, "b"):
            b2 = apply(bd, usi, "b")
            if gote_loses(b2, n - 1, memo):
                out.append((usi, note))
                pv(b2, n - 1, memo, out)
                return
        return
    king = validate.find_king(bd, "w")
    if king is None or not validate.is_attacked(bd, king, "b"):
        return
    replies = rl.defender_moves(bd)
    if not replies:
        return
    usi, note = replies[0]
    b2 = apply(bd, usi, "w")
    out.append((usi, note))
    pv(b2, n - 1, memo, out)


def first_moves(bd, max_ply):
    """All sente first moves that force mate within max_ply."""
    memo = {}
    good = []
    for usi, note in rl.legal_moves(bd, "b"):
        if gote_loses(apply(bd, usi, "b"), max_ply - 1, memo):
            good.append((usi, note))
    return good, memo


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("collection", choices=["seimyo", "kanju"])
    ap.add_argument("number", type=int)
    ap.add_argument("--prefix", default="")
    ap.add_argument("--max-ply", type=int, default=9)
    args = ap.parse_args(argv)

    bd, errs = validate.parse_sfen(cm.load_sfen(args.collection, args.number, False)
                                   .replace("?", "1"))
    if errs:
        print("bad sfen", errs)
        return 1
    tokens = args.prefix.split()
    if tokens:
        bd = rl.apply_tokens(bd, tokens) if hasattr(rl, "apply_tokens") else bd

    good, memo = first_moves(bd, args.max_ply)
    print("forcing first moves within %d plies: %d" % (args.max_ply, len(good)))
    for usi, note in good:
        line = [(usi, note)]
        pv(apply(bd, usi, "b"), args.max_ply - 1, memo, line)
        print("  ", " ".join(n for _, n in line))
    return 0


if __name__ == "__main__":
    sys.exit(main())
