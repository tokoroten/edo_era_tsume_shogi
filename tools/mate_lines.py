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


class BudgetExceeded(Exception):
    pass


class Budget(object):
    def __init__(self, limit):
        self.limit = limit
        self.calls = 0

    def tick(self):
        self.calls += 1
        if self.calls > self.limit:
            raise BudgetExceeded()


def sig(bd):
    return (bd.side,
            tuple(sorted((sq, tuple(v)) for sq, v in bd.sq.items())),
            tuple(sorted((s, k, n) for s, h in bd.hand.items() for k, n in h.items() if n)))


def apply(bd, usi, side):
    b2 = bd.clone()
    validate.apply_usi(b2, usi)
    b2.side = "w" if side == "b" else "b"
    return b2


def sente_wins(bd, n, memo, budget=None):
    if n <= 0:
        return False
    key = (sig(bd), n)
    if key in memo:
        return memo[key]
    if budget:
        budget.tick()
    for usi, _note in rl.legal_moves(bd, "b"):
        if gote_loses(apply(bd, usi, "b"), n - 1, memo, budget):
            memo[key] = True
            return True
    memo[key] = False
    return False


def gote_loses(bd, n, memo, budget=None):
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
    if budget:
        budget.tick()
    for usi, _note in replies:
        if not sente_wins(apply(bd, usi, "w"), n - 1, memo, budget):
            memo[key] = False
            return False
    memo[key] = True
    return True


def pv(bd, n, memo, out, budget=None):
    """Follow one proven winning line."""
    if bd.side == "b":
        for usi, note in rl.legal_moves(bd, "b"):
            b2 = apply(bd, usi, "b")
            if gote_loses(b2, n - 1, memo, budget):
                out.append((usi, note))
                pv(b2, n - 1, memo, out, budget)
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


def first_moves(bd, max_ply, node_budget=None):
    """All sente first moves that force mate within max_ply.

    Returns (good, memo, aborted).  `aborted` is True when the node budget ran
    out before the search finished, in which case `good` is incomplete.
    """
    memo, good = {}, []
    budget = Budget(node_budget) if node_budget else None
    try:
        for usi, note in rl.legal_moves(bd, "b"):
            if gote_loses(apply(bd, usi, "b"), max_ply - 1, memo, budget):
                good.append((usi, note))
    except BudgetExceeded:
        return good, memo, True
    return good, memo, False


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("collection", choices=["seimyo", "kanju"])
    ap.add_argument("number", type=int)
    ap.add_argument("--prefix", default="")
    ap.add_argument("--max-ply", type=int, default=9)
    ap.add_argument("--node-budget", type=int, default=300000)
    args = ap.parse_args(argv)

    bd, errs = validate.parse_sfen(cm.load_sfen(args.collection, args.number, False)
                                   .replace("?", "1"))
    if errs:
        print("bad sfen", errs)
        return 1
    tokens = args.prefix.split()
    if tokens:
        bd = rl.apply_tokens(bd, tokens) if hasattr(rl, "apply_tokens") else bd

    good, memo, aborted = first_moves(bd, args.max_ply, args.node_budget)
    print("forcing first moves within %d plies: %d%s"
          % (args.max_ply, len(good), " (BUDGET EXCEEDED, incomplete)" if aborted else ""))
    for usi, note in good:
        line = [(usi, note)]
        pv(apply(bd, usi, "b"), args.max_ply - 1, memo, line)
        print("  ", " ".join(n for _, n in line))
    return 0


if __name__ == "__main__":
    sys.exit(main())
