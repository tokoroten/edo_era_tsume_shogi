#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate the tables in docs/unassigned-heads.md from the head records.

    python tools/build_unassigned_heads.py [--check]

`docs/unassigned-heads.md` lists every head with `head_unassigned: true` and the
reason it cannot be played on its board.  The reasons come from `head_check.check`,
so the tables can be rebuilt exactly; the prose after `## 理由の意味` is hand-written
and is left untouched.

With `--check` the tool only reports whether the file is in sync.
"""
import glob
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import head_check  # noqa: E402

DOC = os.path.join(ROOT, "docs", "unassigned-heads.md")
START = "## seimyo"
END = "## 理由の意味"

NOTE = {
    "MOVER?": u"移動元が `?` に隠れている可能性",
    "NO MOVER": u"移動元が盤上にも持駒にも無い",
    "OWN PIECE": u"着地点が自分の駒",
    "NO CHECK": u"王手にならない",
}


def rows(cid):
    path = os.path.join(ROOT, "docs", "%s-first-moves.json" % cid)
    data = json.load(open(path, encoding="utf-8"))
    out = []
    for m in data["moves"]:
        if not m.get("head_unassigned"):
            continue
        probe = dict(m)
        probe["head_unassigned"] = False
        status, detail = head_check.check(cid, m["number"], probe)
        out.append((m["number"], m.get("board_q", 0), m.get("raw", ""),
                    "%s（%s）" % (status, NOTE.get(status, detail))))
    return sorted(out)


def tables():
    parts = []
    for cid, label in (("seimyo", "seimyo"), ("kanju", "kanju")):
        rs = rows(cid)
        parts.append("## %s（%d題）\n" % (label, len(rs)))
        parts.append("| 題 | 盤面`?` | 印字 | 未決の理由 |")
        parts.append("|---|---|---|---|")
        for num, q, raw, why in rs:
            parts.append("| %d | %d | %s | %s |" % (num, q, raw, why))
        parts.append("")
    return "\n".join(parts)


def build(old):
    i = old.index(START)
    j = old.index(END)
    return old[:i] + tables() + "\n" + old[j:]


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0
    old = io.open(DOC, encoding="utf-8").read()
    new = build(old)
    if "--check" in argv:
        if new != old:
            print("unassigned-heads.md out of sync")
            return 1
        print("unassigned-heads.md in sync")
        return 0
    io.open(DOC, "w", encoding="utf-8", newline="\n").write(new)
    print("wrote docs/unassigned-heads.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
