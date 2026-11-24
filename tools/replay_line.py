#!/usr/bin/env python3
"""replay_line.py — verify a transcribed 詰手 line against the problem's board.

    python tools/replay_line.py seimyo 67 "三五金 同玉 三六金打"
    python tools/replay_line.py kanju 6 "一六銀 六三王 二六角成 四五王 六五香打"

Each token is `<digits><piece>[打|成]`, or `同<piece>`.  The digits are tried in
both orders (rank-file and file-rank) because the book varies.  A sente move
must give check; a gote move must be legal; the last move must mate.

Exit status 0 means the whole line replayed and ended in mate.
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import check_moves as cm  # noqa: E402
import validate  # noqa: E402

KANJI = "零一二三四五六七八九"
KIND = {"金": "G", "銀": "S", "桂": "N", "香": "L", "歩": "P", "角": "B",
        "飛": "R", "王": "K", "玉": "K", "と": "P", "馬": "B", "龍": "R",
        "全": "S", "杏": "L", "圭": "N"}


def parse_token(tok):
    """('三五','金','-') / ('同','玉','-') / ('三六','金','d')."""
    marker = "-"
    if tok.endswith("打"):
        marker, tok = "d", tok[:-1]
    elif tok.endswith("成"):
        marker, tok = "+", tok[:-1]
    if tok.startswith("同"):
        digits, piece = "同", tok[1:]
    else:
        if len(tok) < 3 or tok[0] not in KANJI or tok[1] not in KANJI:
            raise ValueError("bad token %r" % tok)
        digits, piece = tok[:2], tok[2:]
    if piece not in KIND:
        raise ValueError("unknown piece in %r" % tok)
    return digits, KIND[piece], marker


def apply_move(bd, side, kind, marker, sq):
    b2 = bd.clone()
    captured = b2.sq.get(sq)
    if captured and captured[0] == side:
        return None
    if captured and captured[1] == "K":
        return None
    if marker == "d":
        if b2.hand[side].get(kind, 0) <= 0:
            return None
        b2.hand[side][kind] -= 1
        b2.sq[sq] = [side, kind, False]
        return b2
    src = None
    for s, (sd, kk, prom) in b2.sq.items():
        if sd == side and kk == kind and sq in validate.pseudo_targets(b2, s):
            src = s
            break
    if src is None:
        return None
    moved = b2.sq.pop(src)
    b2.sq[sq] = [side, moved[1], moved[2] or (marker == "+")]
    if captured:
        b2.hand[side][captured[1]] = b2.hand[side].get(captured[1], 0) + 1
    return b2


def strict_mate(bd):
    """Mate under the book rule: the defender may drop only from its own hand.

    validate.is_mate() also gives the defender the whole unused piece box,
    which is a different convention (see validate.box_for).
    """
    me = bd.side
    king = validate.find_king(bd, me)
    if king is None or not validate.is_attacked(bd, king, opp_side(me)):
        return False
    for frm, (color, kind, prom) in list(bd.sq.items()):
        if color != me:
            continue
        for t in validate.pseudo_targets(bd, frm):
            b2 = bd.clone()
            moved = b2.sq.pop(frm)
            if b2.sq.get(t) and b2.sq[t][1] == "K":
                continue
            b2.sq[t] = [me, moved[1], moved[2]]
            if not validate.is_attacked(b2, validate.find_king(b2, me), opp_side(me)):
                return False
    for kind, n in bd.hand[me].items():
        if n <= 0:
            continue
        for f in range(1, 10):
            for r in range(1, 10):
                if bd.sq.get((f, r)):
                    continue
                b2 = bd.clone()
                b2.sq[(f, r)] = [me, kind, False]
                if not validate.is_attacked(b2, validate.find_king(b2, me), opp_side(me)):
                    return False
    return True


def opp_side(side):
    return "w" if side == "b" else "b"


def replay(sfen, tokens):
    """Return (ok, rows) where rows are (n, token, square, mate_after)."""
    bd, errs = validate.parse_sfen(sfen.replace("?", "1"))
    if errs:
        return False, [("sfen", errs)]
    side, prev, rows = "b", None, []
    for i, tok in enumerate(tokens, 1):
        digits, kind, marker = parse_token(tok)
        cands = [prev] if digits == "同" else [
            (KANJI.index(digits[1]), KANJI.index(digits[0])),
            (KANJI.index(digits[0]), KANJI.index(digits[1]))]
        chosen = None
        for sq in cands:
            if not sq or not (1 <= sq[0] <= 9 and 1 <= sq[1] <= 9):
                continue
            b2 = apply_move(bd, side, kind, marker, sq)
            if b2 is None:
                continue
            king = validate.find_king(b2, "w" if side == "b" else "b")
            if side == "b" and not (king and validate.is_attacked(b2, king, side)):
                continue
            chosen = (sq, b2)
            break
        if not chosen:
            rows.append((i, tok, None, False))
            return False, rows
        sq, bd = chosen
        bd.side = "w" if side == "b" else "b"
        mate = strict_mate(bd) if bd.side == "w" else False
        rows.append((i, tok, sq, mate))
        prev, side = sq, bd.side
    # a tsume must end on the attacker's move, in mate
    ok = len(tokens) % 2 == 1 and rows and rows[-1][3]
    return ok, rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("collection", choices=["seimyo", "kanju"])
    ap.add_argument("number", type=int)
    ap.add_argument("line")
    ap.add_argument("--sfen", help="override the draft board")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    sfen = args.sfen or cm.load_sfen(args.collection, args.number, False)
    tokens = args.line.split()
    ok, rows = replay(sfen, tokens)
    if args.json:
        print("OK" if ok else "FAIL")
    for i, tok, sq, mate in rows:
        print("%2d %-6s %-10s %s" % (i, tok, sq, "MATE" if mate else ""))
    print("RESULT:", "verified mate line" if ok else "does not end in mate")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
