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
import material_audit  # noqa: E402
import head_check  # noqa: E402

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
    over = material_audit.excess(sfen)
    if over:
        raise ValueError("SFEN exceeds the material set: %s" % over)
    dead = material_audit.dead_pieces(sfen)
    if dead:
        raise ValueError("SFEN has a dead piece: %s" % dead)
    twin = material_audit.nifu(sfen)
    if twin:
        raise ValueError("SFEN has nifu: %s" % twin)
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


def totals():
    """(seimyo q, seimyo zero, seimyo verified, kanju ...) for both collections."""
    out = {}
    for cid in ("seimyo", "kanju"):
        paths = glob.glob(os.path.join(ROOT, "collections", "*", cid, "drafts", "*.json"))
        qs = [json.load(open(p, encoding="utf-8"))["sfen"].count("?") for p in paths]
        mv = json.load(open(os.path.join(ROOT, "docs", "%s-first-moves.json" % cid),
                            encoding="utf-8"))["moves"]
        out[cid] = (sum(qs), sum(1 for x in qs if x == 0),
                    sum(1 for m in mv
                        if head_check.check(cid, m["number"], m)[0] in ("OK", "OK(drop)")))
    return out


# Each pattern is anchored on a marker that exists in exactly one collection's
# sentence, so the two README paragraphs cannot be confused with each other.
TOTAL_PATTERNS = {
    ("README.md", "seimyo"): (r"\d+ `\?` squares remain \(\d+ of 100 boards have no `\?`\)",
                              "%d `?` squares remain (%d of %d boards have no `?`)"),
    ("README.md", "kanju"): (r"\d+ `\?` squares remain \(\d+ of 50 boards have no `\?`\)",
                             "%d `?` squares remain (%d of %d boards have no `?`)"),
    ("README.ja.md", "seimyo"):
        (r"`\?` 残は合計\d+升（\d+題中\d+題は `\?` なし）、原典翻刻",
         "`?` 残は合計%d升（%d題中%d題は `?` なし）、原典翻刻"),
    ("README.ja.md", "kanju"):
        (r"`\?` 残は合計\d+升（\d+題中\d+題は `\?` なし）、USI化率",
         "`?` 残は合計%d升（%d題中%d題は `?` なし）、USI化率"),
    ("docs/progress.md", "seimyo"):
        (r"\| seimyo（将棋精妙 上巻） \| staging drafts \| 100 \| \d+ \| \d+/100",
         "| seimyo（将棋精妙 上巻） | staging drafts | 100 | %d | %d/100"),
    ("docs/progress.md", "kanju"):
        (r"\| kanju（将棋貫珠 本編） \| staging drafts \| 50 \| \d+ \| \d+/50",
         "| kanju（将棋貫珠 本編） | staging drafts | 50 | %d | %d/50"),
    ("docs/progress.md", "summary"):
        (r"精妙 \*\*\d+\*\*（\d+題は `\?` なし）・貫珠 \*\*\d+\*\*（\d+題は `\?` なし）",
         "精妙 **%d**（%d題は `?` なし）・貫珠 **%d**（%d題は `?` なし）"),
    ("README.md", "seimyo-moves"): (r"The first move is confirmed for \*\*\d+ of 100\*\* problems",
                                    "The first move is confirmed for **%d of 100** problems"),
    ("README.md", "kanju-moves"): (r"The first move is confirmed for \*\*\d+ of 50\*\* problems",
                                   "The first move is confirmed for **%d of 50** problems"),
    ("README.ja.md", "seimyo-moves"): (r"詰手の初手は \*\*\d+題\*\* を原典切出",
                                       "詰手の初手は **%d題** を原典切出"),
    ("README.ja.md", "kanju-moves"): (r"詰手の初手は \*\*\d+題\*\*（\d+題は盤面検証",
                                      "詰手の初手は **%d題**（%d題は盤面検証"),
}


def sync_status_totals(dry_run=False):
    """Regenerate the two summary lines of docs/first-move-status.md."""
    lines = {}
    for cid, label, tail in (("kanju", "貫珠詰手", "（列頭の帰属を原本で確認）"),
                             ("seimyo", "精妙下巻", "")):
        mv = json.load(open(os.path.join(ROOT, "docs", "%s-first-moves.json" % cid),
                            encoding="utf-8"))["moves"]
        n = len(mv)
        v = sum(1 for m in mv
                if head_check.check(cid, m["number"], m)[0] in ("OK", "OK(drop)"))
        g = sum(1 for m in mv if m.get("confidence") == "board-good")
        p = sum(1 for m in mv if m.get("confidence") == "board-partial")
        s = sum(1 for m in mv if m.get("confidence") == "board-sparse")
        lines[label] = ("- %s: 検証済み %d/%d（good %d / partial %d / sparse %d）。"
                        "残り%d題は盤面のみ採用し**初手は未決**%s"
                        % (label, v, n, g, p, s, n - v, tail))
    path = os.path.join(ROOT, "docs", "first-move-status.md")
    text = io.open(path, encoding="utf-8").read()
    for label, line in lines.items():
        text, k = re.subn(r"^- %s: .*$" % label, line.replace("\\", r"\\"), text,
                          count=1, flags=re.M)
        if k != 1:
            raise ValueError("status total line missing: %s" % label)
    if not dry_run:
        io.open(path, "w", encoding="utf-8", newline="\n").write(text)
    return lines


def sync_totals(dry_run=False):
    """Rewrite the public totals from the data.  Returns the values used."""
    t = totals()
    subs = {
        ("README.md", "seimyo"): (t["seimyo"][0], t["seimyo"][1], 100),
        ("README.md", "kanju"): (t["kanju"][0], t["kanju"][1], 50),
        ("README.ja.md", "seimyo"): (t["seimyo"][0], 100, t["seimyo"][1]),
        ("README.ja.md", "kanju"): (t["kanju"][0], 50, t["kanju"][1]),
        ("docs/progress.md", "seimyo"): (t["seimyo"][0], t["seimyo"][2]),
        ("docs/progress.md", "kanju"): (t["kanju"][0], t["kanju"][2]),
        ("docs/progress.md", "summary"): (t["seimyo"][0], t["seimyo"][1],
                                          t["kanju"][0], t["kanju"][1]),
        ("README.md", "seimyo-moves"): (t["seimyo"][2],),
        ("README.md", "kanju-moves"): (t["kanju"][2],),
        ("README.ja.md", "seimyo-moves"): (t["seimyo"][2],),
        ("README.ja.md", "kanju-moves"): (t["kanju"][2], t["kanju"][2]),
    }
    cache = {}
    for (path, key), vals in subs.items():
        full = os.path.join(ROOT, *path.split("/"))
        text = cache.get(full) or io.open(full, encoding="utf-8").read()
        pattern, template = TOTAL_PATTERNS[(path, key)]
        new, n = re.subn(pattern, template % vals, text, count=1)
        if n != 1:
            raise ValueError("totals pattern did not match: %s / %s" % (path, key))
        cache[full] = new
    if not dry_run:
        for full, text in cache.items():
            io.open(full, "w", encoding="utf-8", newline="\n").write(text)
    return t


def _grid(sfen):
    """9x9 board cells as a flat list of (cell string)."""
    out = []
    for row in sfen.split(" ")[0].split("/"):
        i = 0
        while i < len(row):
            if row[i].isdigit():
                out.extend([""] * int(row[i]))
                i += 1
            elif row[i] == "+":
                out.append(row[i:i + 2])
                i += 2
            else:
                out.append(row[i])
                i += 1
    return out


def apply(cid, number, sfen, why, dry_run=False, keep_head=False):
    bd, q = check_sfen(sfen)
    conf = confidence(q)
    base = os.path.join(*BASES[cid])

    draft_path = os.path.join(ROOT, base, "%03d.json" % number)
    rec = json.load(open(draft_path, encoding="utf-8"))
    old_q = rec["sfen"].count("?")
    # a board edit may only touch squares that were unknown
    old_cells, new_cells = _grid(rec["sfen"]), _grid(sfen)
    if len(old_cells) != 81 or len(new_cells) != 81:
        raise ValueError("board does not expand to 81 cells")
    changed = [i for i in range(81) if old_cells[i] != new_cells[i]]
    bad = [i for i in changed if old_cells[i] != "?"]
    if bad:
        raise ValueError("edit changes known squares: %s"
                         % [(9 - i % 9, i // 9 + 1) for i in bad[:5]])
    rec["sfen"] = sfen
    rec["verification"]["needs_manual_review"] = True

    fm_path = os.path.join(ROOT, "docs", "%s-first-moves.json" % cid)
    data = json.load(open(fm_path, encoding="utf-8"))
    entry = [m for m in data["moves"] if m["number"] == number][0]
    print("%s %d: q %d -> %d, head %s -> %s" % (
        cid, number, old_q, q, entry["raw"], "kept" if keep_head else "unassigned"))
    if dry_run:
        return {"old_q": old_q, "q": q, "head": entry["raw"]}

    rec["notes"].append("2026-11-25 盤面のみ採用 (? %d→%d): %s" % (old_q, q, why))
    json.dump(rec, open(draft_path, "w", encoding="utf-8", newline=""),
              ensure_ascii=False, indent=2)

    entry["board_q"] = q
    entry["confidence"] = conf
    if keep_head:
        # --keep-head must be *checked*: it used to write "verified" blindly.
        probe = {k: v for k, v in entry.items() if k != "head_unassigned"}
        st = head_check.check(cid, number, probe)[0]
        if st in ("OK", "OK(drop)"):
            entry.pop("head_unassigned", None)
            entry["note"] = ("2026-11-25 盤面は複数モデル一致で採用 (?=%d)。"
                             "列頭 %s は新しい盤面でも王手になることを機械確認。" % (q, entry["raw"]))
        else:
            entry["head_unassigned"] = True
            entry["note"] = ("2026-11-25 盤面は複数モデル一致で採用 (?=%d)。"
                             "--keep-head 指定だが現盤面では %s のため初手は未決。" % (q, st))
    else:
        entry["head_unassigned"] = True
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
    first = entry["raw"] if keep_head else "未決（列頭 %s）" % entry["raw"]
    row = "| %d | %s | %s | %s（?=%d） |" % (number, king_cell(bd), first, conf, q)
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
        if not keep_head and "初手は未決" not in line:
            line = line.rstrip().rstrip("|").rstrip() + "／初手は未決（盤面のみ採用） |"
        lines[i] = line
        break
    io.open(lp, "w", encoding="utf-8", newline="\n").write("\n".join(lines))

    sync_status_totals()
    t = sync_totals()
    print("totals:", t)
    return {"old_q": old_q, "q": q, "head": entry["raw"], "totals": t}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("collection", choices=sorted(BASES))
    ap.add_argument("number", type=int)
    ap.add_argument("sfen")
    ap.add_argument("--why", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--keep-head", action="store_true",
                    help="the recorded head still checks on the new board")
    args = ap.parse_args(argv)
    apply(args.collection, args.number, args.sfen, args.why, args.dry_run,
          args.keep_head)
    return 0


if __name__ == "__main__":
    sys.exit(main())
