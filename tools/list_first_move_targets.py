#!/usr/bin/env python3
"""List unverified first-move targets, easiest first (fewest `?` on the board).

A draft with few `?` gives a trustworthy check: if no column head checks the
gote king on such a board, the reading or the column attribution is wrong.
Those problems are the best place to start.

Usage:
    python tools/list_first_move_targets.py --limit 20
    python tools/list_first_move_targets.py --limit 25 --out docs/first-move-targets.md
"""

import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RANKS = "abcdefghi"

COLLECTIONS = [
    ("kanju", ("collections", "meiji", "kanju", "drafts")),
    ("seimyo", ("collections", "edo", "seimyo", "drafts")),
]

HEADER = [
    "| ? | collection | 番 | 後手玉 | 盤面RID | 原典記述 |",
    "|---:|---|---:|---|---|---|",
]


def done_numbers(cid):
    done = set()
    for name, key in (("%s-first-moves.json", "moves"),
                      ("%s-procedure-readings.json", "readings")):
        path = os.path.join(ROOT, "docs", name % cid)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        done.update(r["number"] for r in data.get(key, []))
    return done


def leaf_of(page):
    m = re.search(r"R\d{7}", page or "")
    return m.group(0) if m else "?"


def build(limit):
    rows = []
    for cid, base in COLLECTIONS:
        done = done_numbers(cid)
        for path in glob.glob(os.path.join(ROOT, *base, "*.json")):
            with open(path, encoding="utf-8") as f:
                rec = json.load(f)
            n = rec["number"]
            if n in done:
                continue
            bd, _ = validate.parse_sfen(rec["sfen"].replace("?", "1"))
            ksq = validate.find_king(bd, "w")
            king = "%d%s" % (ksq[0], RANKS[ksq[1] - 1]) if ksq else "?"
            rows.append((rec["sfen"].count("?"), cid, n, king,
                         leaf_of(rec["source"].get("page")),
                         rec["source"].get("page") or ""))
    rows.sort()
    lines = list(HEADER)
    for q, cid, n, king, rid, page in rows[:limit]:
        note = page.split("(", 1)[1].rstrip(")") if "(" in page else page
        lines.append("| %d | %s | %d | %s | %s | %s |"
                     % (q, cid, n, king, rid, note.replace("|", "/")[:70]))
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--out", help="write the table to this file")
    args = ap.parse_args(argv)
    table = build(args.limit)
    if args.out:
        path = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(table)
        print("wrote %s" % args.out)
    else:
        sys.stdout.write(table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
