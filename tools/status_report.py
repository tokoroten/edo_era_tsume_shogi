#!/usr/bin/env python3
"""status_report.py — one table with the dataset's current state.

Every headline number in the docs should be reproducible from this command:

    python tools/status_report.py
    python tools/status_report.py --md
"""
import argparse
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import head_check  # noqa: E402
import material_audit  # noqa: E402

BASES = {"kanju": ("collections", "meiji", "kanju", "drafts"),
         "seimyo": ("collections", "edo", "seimyo", "drafts")}


def collection(cid):
    paths = sorted(glob.glob(os.path.join(ROOT, *BASES[cid], "*.json")))
    qs = []
    for p in paths:
        rec = json.load(open(p, encoding="utf-8"))
        qs.append(rec["sfen"].count("?"))
    moves = json.load(open(os.path.join(ROOT, "docs", "%s-first-moves.json" % cid),
                           encoding="utf-8"))["moves"]
    verified = sum(1 for m in moves
                   if head_check.check(cid, m["number"], m)[0] in ("OK", "OK(drop)"))
    return {
        "drafts": len(paths),
        "unknown": sum(qs),
        "complete": sum(1 for q in qs if q == 0),
        "moves": len(moves),
        "verified": verified,
        "unassigned": len(moves) - verified,
        "violations": len(material_audit.audit(cid)),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", action="store_true")
    args = ap.parse_args(argv)
    rows = [(cid, collection(cid)) for cid in ("seimyo", "kanju")]
    procs = glob.glob(os.path.join(ROOT, "collections", "*", "*", "procedures", "*.json"))
    states = {}
    for p in procs:
        rec = json.load(open(p, encoding="utf-8"))
        st = (rec.get("completeness") or {}).get("state", "unmarked")
        states[st] = states.get(st, 0) + 1
    proc_line = "procedures: %d (complete %d)" % (len(procs), states.get("complete", 0))
    if args.md:
        print("| collection | drafts | `?` | complete | first moves | verified | unassigned | rule violations |")
        print("|---|---|---|---|---|---|---|---|")
        for cid, s in rows:
            print("| %s | %d | %d | %d | %d | %d | %d | %d |"
                  % (cid, s["drafts"], s["unknown"], s["complete"], s["moves"],
                     s["verified"], s["unassigned"], s["violations"]))
        print()
        print(proc_line)
    else:
        for cid, s in rows:
            print("%-7s drafts=%-3d ?=%-3d complete=%-2d moves=%-3d verified=%-3d "
                  "unassigned=%-2d violations=%d"
                  % (cid, s["drafts"], s["unknown"], s["complete"], s["moves"],
                     s["verified"], s["unassigned"], s["violations"]))
        print(proc_line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
