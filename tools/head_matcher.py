#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""head_matcher.py — match printed column heads to the moves they could be.

The solution pages are hard to attribute (cartouche positions, leaves and
x_pct in the ledger are not always reliable), so this tool ignores the page and
asks a different question: given the current board of every unassigned problem,
which problems could the head legally check?

A head matches a problem when its digits, read as (rank, file) or (file, rank),
and its piece (with 成/と/龍/馬 promoted) put the giver in check.  A head that
matches exactly one problem is a strong candidate for that problem's first
move; a head that matches several is only a lead.  Candidates marked with a
trailing '~' need the mover to promote although the head prints no 成; treat
them as weak (the print usually shows 成 or the promoted name).

Usage:
    python tools/head_matcher.py            # both collections
    python tools/head_matcher.py seimyo
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import head_check  # noqa: E402
import validate  # noqa: E402

DIGIT = {u"一": 1, u"二": 2, u"三": 3, u"四": 4, u"五": 5,
         u"六": 6, u"七": 7, u"八": 8, u"九": 9}
KIND = {u"歩": "P", u"香": "L", u"桂": "N", u"銀": "S", u"金": "G",
        u"角": "B", u"飛": "R", u"と": "P", u"杏": "L", u"圭": "N",
        u"全": "S", u"馬": "B", u"龍": "R", u"竜": "R"}
PROMOTED = {u"と", u"杏", u"圭", u"全", u"馬", u"龍", u"竜"}

BASES = {
    "seimyo": ("docs/seimyo-first-moves.json", "docs/seimyo-column-heads.json"),
    "kanju": ("docs/kanju-first-moves.json", "docs/kanju-column-heads.json"),
}


def legal_checks(cid, n):
    rec = head_check.load(cid, n)
    bd, _ = validate.parse_sfen(rec["sfen"].replace("?", "1"))
    kinds = set()
    for sq, (side, kk, pp) in bd.sq.items():
        if side == "b":
            kinds.add((kk, pp))
    hand = bd.hand["b"]
    hits = set()
    for f in range(1, 10):
        for r in range(1, 10):
            for kind, prom in kinds:
                m = {"number": n, "piece": kind, "promoted": prom,
                     "file": f, "rank": r}
                if head_check.check(cid, n, m)[0] == "OK":
                    hits.add((kind, bool(prom), f, r))
            for kind, cnt in hand.items():
                if not cnt:
                    continue
                m = {"number": n, "piece": kind, "promoted": False,
                     "file": f, "rank": r}
                if head_check.check(cid, n, m)[0] == "OK(drop)":
                    hits.add((kind, False, f, r))
    return hits


def parse_head(raw):
    if len(raw) < 3 or raw[0] not in DIGIT or raw[1] not in DIGIT:
        return None
    body = raw[2:]
    kind = None
    for ch in body:
        if ch in KIND:
            kind = KIND[ch]
            break
    if kind is None:
        return None
    promoted = any(ch in PROMOTED for ch in body) or (u"成" in body)
    return DIGIT[raw[0]], DIGIT[raw[1]], kind, promoted


def run(cid):
    moves_path, heads_path = BASES[cid]
    moves = json.load(open(os.path.join(ROOT, moves_path), encoding="utf-8"))["moves"]
    verified = set()
    pending = []
    for m in moves:
        if head_check.check(cid, m["number"], m)[0] in ("OK", "OK(drop)"):
            verified.add(m["number"])
        else:
            pending.append(m["number"])
    # verified problems are included so a head that belongs to one of them is
    # not reported as a unique match for an unassigned problem
    legal = {n: legal_checks(cid, n) for n in (pending + sorted(verified))}
    heads = json.load(open(os.path.join(ROOT, heads_path),
                           encoding="utf-8"))["heads"]
    rows = []
    for h in heads:
        if h.get("problem") in verified:
            continue
        parsed = parse_head(h.get("raw") or "")
        if not parsed:
            continue
        a, b_, kind, promoted = parsed
        cands = []
        for rk, fl in ((a, b_), (b_, a)):
            for n in legal:
                for (kk, pp, ff, rr) in legal[n]:
                    if kk == kind and ff == fl and rr == rk and (pp or not promoted):
                        implied = pp and not promoted
                        cands.append((n, kind, fl, rk, pp, n in verified, implied))
        cands = sorted(set(cands))
        if cands:
            rows.append((h.get("leaf"), h.get("x_pct"), h.get("raw"), cands))
    for leaf, x, raw, cands in rows:
        open_problems = {c[0] for c in cands if not c[5]}
        has_verified = any(c[5] for c in cands)
        cands = [c[:5] + ("~" if c[6] else "",) for c in cands]
        mark = "*" if (len(open_problems) == 1 and not has_verified) else " "
        print("%s %s x=%-12s %-8s %s" % (mark, leaf, x, raw,
                                         [c for c in cands]))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cid", nargs="?", choices=sorted(BASES))
    args = ap.parse_args(argv)
    for cid in ([args.cid] if args.cid else sorted(BASES)):
        print("==", cid)
        run(cid)
    return 0


if __name__ == "__main__":
    sys.exit(main())
