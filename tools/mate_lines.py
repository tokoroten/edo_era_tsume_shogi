#!/usr/bin/env python3
"""mate_lines.py — enumerate mating lines and the moves they all share.

A transcribed procedure only needs the scan where the lines *differ*.  Given a
board (and optionally a verified prefix), this lists every mating line up to a
ply bound and reports the common prefix: those moves are forced by the board.

    python tools/mate_lines.py kanju 44
    python tools/mate_lines.py kanju 44 --prefix "三三飛打 同香" --max-ply 13
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import check_moves as cm  # noqa: E402
import replay_line as rl  # noqa: E402
import validate  # noqa: E402


def legal(bd, side, checks_only):
    out = []
    for usi, note in rl.legal_moves(bd, side):
        if checks_only:
            b2 = bd.clone()
            validate.apply_usi(b2, usi)
            king = validate.find_king(b2, "w")
            if not (king and validate.is_attacked(b2, king, "b")):
                continue
        out.append((usi, note))
    return out


def search(bd, max_ply, limit, node_budget=200000):
    """Return (lines, nodes, aborted).  Aborts when the node budget is spent."""
    lines = []
    state = {"nodes": 0, "aborted": False}

    def dfs(node, path):
        if len(lines) >= limit:
            return
        state["nodes"] += 1
        if state["nodes"] > node_budget:
            state["aborted"] = True
            return
        side = node.side
        if side == "w":
            if rl.strict_mate(node):
                lines.append(list(path))
                return
            if not validate.is_attacked(node, validate.find_king(node, "w"), "b"):
                return
        if len(path) >= max_ply:
            return
        for usi, note in legal(node, side, checks_only=(side == "b")):
            nxt = node.clone()
            validate.apply_usi(nxt, usi)
            nxt.side = "w" if side == "b" else "b"
            path.append((usi, note))
            dfs(nxt, path)
            path.pop()

    dfs(bd, [])
    return lines, state["nodes"], state["aborted"]


def common_prefix(lines):
    if not lines:
        return []
    out = []
    for i in range(min(len(x) for x in lines)):
        if len({x[i][1] for x in lines}) == 1:
            out.append(lines[0][i])
        else:
            break
    return out


def apply_prefix(bd, tokens):
    side, prev = "b", None
    for tok in tokens:
        digits, kind, marker = rl.parse_token(tok)
        K = rl.KANJI
        cands = [prev] if digits == "同" else [
            (K.index(digits[1]), K.index(digits[0])),
            (K.index(digits[0]), K.index(digits[1]))]
        done = False
        for sq in cands:
            b2 = rl.apply_move(bd, side, kind, marker, sq)
            if b2 is None:
                continue
            king = validate.find_king(b2, "w" if side == "b" else "b")
            if side == "b" and not (king and validate.is_attacked(b2, king, side)):
                continue
            bd, prev, done = b2, sq, True
            break
        if not done:
            raise ValueError("prefix move not playable: %s" % tok)
        bd.side = "w" if side == "b" else "b"
        side = bd.side
    return bd


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("collection", choices=["seimyo", "kanju"])
    ap.add_argument("number", type=int)
    ap.add_argument("--prefix", default="")
    ap.add_argument("--max-ply", type=int, default=11)
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--node-budget", type=int, default=200000)
    args = ap.parse_args(argv)

    bd, errs = validate.parse_sfen(cm.load_sfen(args.collection, args.number, False))
    if errs:
        print("bad sfen", errs)
        return 1
    tokens = args.prefix.split()
    if tokens:
        bd = apply_prefix(bd, tokens)
    lines, nodes, aborted = search(bd, args.max_ply, args.limit, args.node_budget)
    print("mating lines:", len(lines), "nodes:", nodes,
          "aborted:" if aborted else "")
    for line in lines:
        print("  ", " ".join(n for _, n in line))
    pref = common_prefix(lines)
    total = len(tokens) + len(pref)
    print("common prefix: %d plies%s" % (total, "" if not tokens else
                                         " (%d after the given prefix)" % len(pref)))
    print("  ", " ".join(tokens + [n for _, n in pref]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
