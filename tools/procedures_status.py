#!/usr/bin/env python3
"""Summarise the 詰手 transcription status (procedures/*.json).

Prints one line per file: collection, leaf, covered problems, ply counts per
column, whether the transcription is verified, and how many moves are in
`verified_prefix`.
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    files = sorted(glob.glob(os.path.join(
        ROOT, "collections", "*", "*", "procedures", "*.json")))
    if not files:
        print("no procedure files")
        return 0
    for p in files:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        cols = {}
        for m in d.get("moves", []):
            cols[m["col"]] = cols.get(m["col"], 0) + 1
        tr = d.get("transcription", {})
        vp = tr.get("verified_prefix") or {}
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        print("%s | %s %s | covers=%s | plies=%s | verified=%s | prefix=%d"
              % (rel, d.get("collection_id"), d.get("leaf"),
                 d.get("covers_problems"),
                 ",".join("%s:%d" % (k, v) for k, v in sorted(cols.items())),
                 tr.get("verified"), len(vp.get("moves") or [])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
