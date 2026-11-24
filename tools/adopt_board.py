# -*- coding: utf-8 -*-
"""adopt_board.py — adopt a board read while keeping every document in sync.

    python tools/adopt_board.py seimyo 30 <sfen> --why "..."

Sets the draft SFEN, marks the first move as *head unassigned* (the printed
column is kept for traceability), updates the column-head record, the status
table, the transcription ledger and the public totals.

Two failure modes this tool exists to prevent:

* a candidate SFEN that does not parse (stored candidates can be corrupt),
* a status-row regex hitting the other collection's table, because both
  tables start with ``| 1 |`` … ``| 50 |``.
"""
import argparse
import glob
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import validate  # noqa: E402

BASES = {
    "kanju": ("collections", "meiji", "kanju", "drafts"),
    "seimyo": ("collections", "edo", "seimyo", "drafts"),
}
STATUS_SECTIONS = {
    "kanju": ("## 将棋貫珠 詰手", "## 将棋精妙"),
    "seimyo": ("## 将棋精妙 下巻", "## 集計"),
}
LEDGER_SECTIONS = {
    "kanju": ("## 4. 既読台帳", "## 5. "),
    "seimyo": ("## 台帳", "## "),
}


def confidence(q):
    return "board-good" if q <= 12 else ("board-partial" if q <= 19 else "board-sparse")


def check_sfen(sfen):
    """Parse and sanity-check a candidate board.  Returns (board, q)."""
    if sfen.count("/") != 8:
        raise ValueError("SFEN needs 9 ranks, got %d" % (sfen.count("/") + 1))
    bd, errs = validate.parse_sfen(sfen.replace("?", "1"))
    if errs or bd is None:
        raise ValueError("SFEN does not parse: %s" % errs)
    if not validate.find_king(bd, "w"):
        raise ValueError("SFEN has no gote king")
    return bd, sfen.count("?")


def king_cell(bd):
    f, r = validate.find_king(bd, "w")
    return "%d%s" % (f, "abcdefghi"[r - 1])


def replace_in_section(text, heading, stop, pattern, replacement):
    """Regex-replace inside one table of a document.

    Both first-move tables share the row numbers 1..50, so an unscoped
    ``^\\| 30 \\|`` edit silently rewrites the wrong collection.
    """
    a = text.index(heading)
    b = text.index(stop, a)
    body, n = re.subn(pattern, replacement, text[a:b], count=1, flags=re.M)
    if n != 1:
        raise ValueError("row not found in section %r" % heading)
    return text[:a] + body + text[b:], n


def apply(cid, number, sfen, why, dry_run=False):
    bd, q = check_sfen(sfen)
    conf = confidence(q)
    base = os.path.join(*BASES[cid])

    draft_path = os.path.join(ROOT, base, "%03d.json" % number)
    rec = json.load(open(draft_path, encoding="utf-8"))
    old_q = rec["sfen"].count("?")
    rec["sfen"] = sfen
    rec["verification"]["needs_manual_review"] = True

    fm_path = os.path.join(ROOT, "docs", "%s-first-moves.json" % cid)
    data = json.load(open(fm_path, encoding="utf-8"))
    entry = [m for m in data["moves"] if m["number"] == number][0]
    print("%s %d: q %d -> %d, head %s -> unassigned" % (cid, number, old_q, q, entry["raw"]))
    if dry_run:
        return {"old_q": old_q, "q": q, "head": entry["raw"]}

    rec["notes"].append("2026-11-25 盤面のみ採用 (? %d→%d): %s" % (old_q, q, why))
    json.dump(rec, open(draft_path, "w", encoding="utf-8", newline=""),
              ensure_ascii=False, indent=2)

    entry["head_unassigned"] = True
    entry["board_q"] = q
    entry["confidence"] = conf
    entry["note"] = ("2026-11-25 盤面は複数モデル一致で採用 (?=%d)。"
                     "列頭 %s は王手にならず初手は未決。" % (q, entry["raw"]))
    with open(fm_path, "w", encoding="utf-8", newline="") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    hp = os.path.join(ROOT, "docs", "%s-column-heads.json" % cid)
    heads = json.load(open(hp, encoding="utf-8"))
    for h in heads["heads"]:
        if h.get("problem") == number and h.get("verified"):
            h["verified"] = False
            h["note"] = "2026-11-25 盤面を q=%d に更新したところ王手にならなかった。初手は未決。" % q
    json.dump(heads, open(hp, "w", encoding="utf-8", newline=""),
              ensure_ascii=False, indent=2)

    sp = os.path.join(ROOT, "docs", "first-move-status.md")
    text = io.open(sp, encoding="utf-8").read()
    row = "| %d | %s | 未決（列頭 %s） | %s（?=%d） |" % (
        number, king_cell(bd), entry["raw"], conf, q)
    text, _ = replace_in_section(text, *STATUS_SECTIONS[cid],
                                 pattern=r"^\| %d \| .*\|$" % number, replacement=row)
    io.open(sp, "w", encoding="utf-8", newline="\n").write(text)

    lp = os.path.join(ROOT, "docs", "%s-transcription.md" % cid)
    lines = io.open(lp, encoding="utf-8").read().split("\n")
    start, stop = LEDGER_SECTIONS[cid]
    a = next(i for i, l in enumerate(lines) if l.startswith(start))
    b = next(i for i in range(a + 5, len(lines)) if lines[i].startswith(stop))
    idx = 0
    row_re = r"^\| \S+番 \|" if cid == "seimyo" else r"^\| \S+ \|"
    for i in range(a, b):
        if not re.match(row_re, lines[i]):
            continue
        cells = lines[i].strip().strip("|").split("|")
        if len(cells) < 4 or cells[0].strip() == "番":
            continue
        idx += 1
        if idx != number:
            continue
        cells[3] = " %d " % q
        line = "|" + "|".join(cells).rstrip()
        if not line.endswith("|"):
            line += " |"
        if "初手は未決" not in line:
            line = line.rstrip().rstrip("|").rstrip() + "／初手は未決（盤面のみ採用） |"
        lines[i] = line
        break
    io.open(lp, "w", encoding="utf-8", newline="\n").write("\n".join(lines))

    totals = {}
    for other in ("seimyo", "kanju"):
        paths = glob.glob(os.path.join(ROOT, "collections", "*", other, "drafts", "*.json"))
        qs = [json.load(open(p, encoding="utf-8"))["sfen"].count("?") for p in paths]
        mv = json.load(open(os.path.join(ROOT, "docs", "%s-first-moves.json" % other),
                            encoding="utf-8"))["moves"]
        totals[other] = (sum(qs), sum(1 for x in qs if x == 0),
                         sum(1 for m in mv if not m.get("head_unassigned")))
    print("totals:", totals)
    return {"old_q": old_q, "q": q, "head": entry["raw"], "totals": totals}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("collection", choices=sorted(BASES))
    ap.add_argument("number", type=int)
    ap.add_argument("sfen")
    ap.add_argument("--why", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    apply(args.collection, args.number, args.sfen, args.why, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
