#!/usr/bin/env python3
"""List the recorded column-head candidates for every unverified problem.

For each problem without a confirmed first move, print the heads whose
destination would check its gote king, with the leaf and x range so a reader
can go straight to the right place. Problems with no candidate mean the head
for that problem is not recorded yet.

A head that is already the confirmed first move of another problem is marked
`（N番で使用済み）`: one column head can only belong to one problem, so such a
candidate is not available. `★` marks a problem with exactly one unclaimed
candidate, i.e. the next problems that can be settled without reading further.

Usage:
    python tools/candidates_report.py [--collection seimyo] [--out FILE]
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KANJI = "零一二三四五六七八九"
BASES = {
    "kanju": ("collections", "meiji", "kanju", "drafts"),
    "seimyo": ("collections", "edo", "seimyo", "drafts"),
}
COUNTS = {"kanju": 50, "seimyo": 100}
TITLES = {"kanju": "kanju", "seimyo": "seimyo"}


def dest_of(h):
    if "dest" in h:
        return int(h["dest"][0]), KANJI.index(h["dest"][1])
    a, b = KANJI.index(h["raw"][0]), KANJI.index(h["raw"][1])
    return (a, b) if h.get("order") == "file-rank" else (b, a)


def verified_first_moves(cid):
    """Map (piece, promoted, file, rank, raw) to the sorted problem numbers."""
    out = {}

    def add(key, number):
        out.setdefault(key, set()).add(number)

    with open(os.path.join(ROOT, "docs", "%s-first-moves.json" % cid),
              encoding="utf-8") as f:
        for m in json.load(f)["moves"]:
            if m.get("head_unassigned"):
                continue
            add((m["piece"], bool(m.get("promoted")), m["file"], m["rank"],
                 m.get("raw")), m["number"])
    rpath = os.path.join(ROOT, "docs", "%s-procedure-readings.json" % cid)
    if os.path.exists(rpath):
        with open(rpath, encoding="utf-8") as f:
            for r in json.load(f)["readings"]:
                first = next((m for m in r["moves"]
                              if m["side"] == "sente"), None)
                if not first or "dest" not in first:
                    continue
                add((first["piece"], bool(first.get("promoted")),
                     first["dest"]["file"], first["dest"]["rank"],
                     first.get("raw")), r["number"])
    return out


def build(cid):
    with open(os.path.join(ROOT, "docs", "%s-column-heads.json" % cid),
              encoding="utf-8") as f:
        heads = [h for h in json.load(f)["heads"] if h.get("raw")]
    with open(os.path.join(ROOT, "docs", "%s-first-moves.json" % cid),
              encoding="utf-8") as f:
        done = {m["number"] for m in json.load(f)["moves"]}
    rpath = os.path.join(ROOT, "docs", "%s-procedure-readings.json" % cid)
    if os.path.exists(rpath):
        with open(rpath, encoding="utf-8") as f:
            done |= {r["number"] for r in json.load(f)["readings"]}
    claimed = verified_first_moves(cid)

    rows = []
    for n in range(1, COUNTS[cid] + 1):
        if n in done:
            continue
        path = os.path.join(ROOT, *BASES[cid], "%03d.json" % n)
        with open(path, encoding="utf-8") as f:
            sfen = json.load(f)["sfen"]
        bd, _ = validate.parse_sfen(sfen.replace("?", "1"))
        ksq = validate.find_king(bd, "w")
        if not ksq:
            continue
        hits = []
        for h in heads:
            try:
                file, rank = dest_of(h)
            except (ValueError, IndexError):
                continue
            probe = bd.clone()
            probe.sq.pop(ksq, None)
            probe.sq[(file, rank)] = ["b", h["piece"],
                                      bool(h.get("promoted"))]
            if ksq in validate.pseudo_targets(probe, (file, rank)):
                key = (h["piece"], bool(h.get("promoted")), file, rank,
                       h.get("raw"))
                hits.append({
                    "label": "%s %s %s" % (h["raw"], h["leaf"], h["x_pct"]),
                    "head": (h["raw"], h["leaf"], h["x_pct"]),
                    "used_by": sorted(claimed.get(key, ())),
                })
        rows.append((n, "Q=%d" % sfen.count("?"), ksq, hits))
    return rows


def render(cid):
    rows = build(cid)
    lines = ["# 未検証の初手候補（%s）" % TITLES[cid], "",
             "各題の玉に王手になる記録済み列頭。`（確定済み: N番）` は同じ手が",
             "既に確定題の初手になっている列頭。1つの列頭は1題のものなので、",
             "その列頭が未検証題の初手かは確定題との取り合いになる（複数番は",
             "同じ手の題が複数あり、列頭の帰属が一意でないことを示す）。",
             "候補が1つでも、その列頭が他の未検証題の候補にもなっていれば未決。",
             "0なら列頭が未記録。",
             ""]
    if not rows:
        lines.append("未検証の題はありません（全題の初手が確定済み）。")
    shared = {}
    for n, _, _, hits in rows:
        for h in hits:
            shared.setdefault(h["head"], []).append(n)
    for n, q, ksq, hits in rows:
        parts = []
        for h in hits:
            if h["used_by"]:
                parts.append("%s（確定済み: %s番）" % (
                    h["label"], ",".join(map(str, h["used_by"]))))
            else:
                parts.append(h["label"])
        where = "%d%s" % (ksq[0], "abcdefghi"[ksq[1] - 1])
        lines.append("- **%d**（%s, 玉%s）: %s" % (
            n, q, where, " / ".join(parts) if parts else "候補なし"))
    multi = [(k, v) for k, v in shared.items() if len(v) > 1]
    if multi:
        lines += ["", "## 未検証題どうしで共有している候補", "",
                  "同じ列頭が複数の未検証題で王手になる（帰属は未決）。", ""]
        for (raw, leaf, x), nums in sorted(multi,
                                          key=lambda kv: kv[1][0]):
            lines.append("- %s %s %s: %s" % (
                raw, leaf, x, ", ".join(map(str, nums))))
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--collection", default="seimyo", choices=sorted(BASES))
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    text = render(args.collection)
    if args.out:
        path = args.out if os.path.isabs(args.out) else os.path.join(
            ROOT, args.out)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("wrote %s" % args.out)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
