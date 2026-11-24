#!/usr/bin/env python3
"""build_procedures_page.py — publish the 詰手 (procedure) leaves for collation.

Reads:
  collections/edo/seimyo/procedures/*.json   (leaf transcriptions, may be unverified)
  web/images/<PID>_<RID>.jpg                 (published NDL canvases)
and writes web/procedures.html: one card per leaf with the scan, the
problem numbers it covers, any recorded moves, and a prefilled GitHub issue
link (OT-PROCEDURE-REPORT v1) so humans can transcribe/verify.

The page never claims a verified solution.
"""
import glob
import html
import json
import os
import re
import sys
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "tokoroten/edo_era_tsume_shogi"
LABEL = "decipher"
CHECK = False
DIFFS = []

COLLECTIONS = {
    "seimyo": {
        "pid": "861217",
        "title": "将棋精妙 下巻（詰手）",
        "leaves": [
            ("R0000002", (1, 2)), ("R0000003", (3, 6)), ("R0000004", (7, 10)),
            ("R0000005", (11, 14)), ("R0000006", (15, 19)), ("R0000007", (20, 23)),
            ("R0000008", (24, 28)), ("R0000009", (29, 32)), ("R0000010", (33, 37)),
            ("R0000011", (38, 41)), ("R0000012", (42, 44)), ("R0000013", (45, 49)),
            ("R0000014", (50, 54)), ("R0000015", (55, 59)), ("R0000016", (60, 62)),
            ("R0000017", (63, 66)), ("R0000018", (67, 70)), ("R0000019", (71, 73)),
            ("R0000020", (74, 78)), ("R0000021", (79, 82)), ("R0000022", (83, 85)),
            ("R0000023", (86, 89)), ("R0000024", (90, 93)), ("R0000025", (94, 96)),
            ("R0000026", (97, 100)), ("R0000027", (100, 100)),
        ],
        "note": "全25コマの題簽を原寸で確認済み。1コマ2〜5題で一定しない（docs/procedures.md §1.1）。R27 は左頁が刊記で、右頁に百番の続き1列がある。",
    },
    "kanju": {
        "pid": "861192",
        "title": "将棋貫珠 詰手",
        "leaves": [
            ("R0000003", (1, 1)), ("R0000004", (2, 5)), ("R0000005", (6, 9)),
            ("R0000006", (10, 12)), ("R0000007", (13, 16)), ("R0000008", (17, 19)),
            ("R0000009", (20, 22)), ("R0000010", (23, 24)), ("R0000011", (25, 27)),
            ("R0000012", (28, 31)), ("R0000013", (32, 36)), ("R0000014", (37, 41)),
            ("R0000015", (42, 44)), ("R0000016", (45, 47)), ("R0000017", (48, 50)),
            ("R0000018", (50, 50)),
        ],
        "note": "各題の冒頭列に「N番」題簽。1題が複数列に及ぶことがあり、列数から題数を逆算しない。全15コマ（R3〜R17）の題簽を実見済み。五十番は R18 右側に続く。R18左〜R20は草書の散文、R21は刊記・跋。",
    },
}

PIECES = {"K": "玉", "R": "飛", "B": "角", "G": "金", "S": "銀", "N": "桂",
          "L": "香", "P": "歩", "Q": "と", "X": "杏", "Y": "圭", "Z": "全",
          "M": "馬", "H": "龍", "?": "？"}
MARK = {"+": "成", "=": "不成", "d": "打", "-": ""}


def range_label(lo, hi):
    if not lo:
        return "図番未確定"
    if lo == hi:
        return "第%d番" % lo
    return "第%d〜%d番" % (lo, hi)


def issue_url(cid, rid, lo, hi):
    rng = range_label(lo, hi)
    title = "【手順報告】%s %s（%s）" % (cid, rid, rng)
    body = """<!-- OT-PROCEDURE-REPORT v1 | collection:%s | leaf:%s -->
<!-- 記入はNDL一次資料スキャンの直接読取のみ。推測は「推測」と明記すること -->

## 対象
- collection: %s
- leaf: NDL PID:%s %s
- 図番: %s

## 手順（駒・行き先・成/不成/打。1手1行）
```text
<例: 1 ▲角 98 / 2 △王 同 / 3 ▲桂打 …。不明は ? と書く>
```

## 読取源（必須: NDL PID / RID / 頁・列）
- NDL PID:%s %s

## 備考（くずし・印影・既存転記への指摘）
- 
""" % (cid, rid, cid, COLLECTIONS[cid]["pid"], rid, rng,
       COLLECTIONS[cid]["pid"], rid)
    q = urllib.parse.urlencode({"title": title, "body": body, "labels": LABEL})
    return "https://github.com/%s/issues/new?%s" % (REPO, q)


def load_transcriptions(cid):
    out = {}
    for p in sorted(glob.glob(os.path.join(ROOT, "collections", "*", cid,
                                           "procedures", "*.json"))):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        out[d.get("leaf")] = d
    return out


def moves_html(d):
    if not d:
        return ""
    by_col = {}
    for m in d.get("moves", []):
        by_col.setdefault(m["col"], []).append(m)
    parts = []
    for col in sorted(by_col):
        seq = sorted(by_col[col], key=lambda m: m["n"])
        txt = " ".join("%s%s%s" % (PIECES.get(m["piece"], m["piece"]),
                                   m["dest"], MARK.get(m["marker"], m["marker"]))
                       for m in seq)
        parts.append('<p class="meta mono">%s: %s</p>' % (html.escape(col), html.escape(txt)))
    tr = d.get("transcription", {})
    vp = tr.get("verified_prefix") or {}
    if vp.get("moves"):
        vtxt = " ".join("%s%s%s" % (PIECES.get(m.get("piece"), m.get("piece")),
                                    m.get("dest"), MARK.get(m.get("marker"), m.get("marker")))
                        for m in sorted(vp["moves"], key=lambda m: m.get("n", 0)))
        parts.append('<p class="meta mono">%s 検証済み（原寸再読・筋段順）: %s</p>'
                     % (html.escape(vp.get("col", "")), html.escape(vtxt)))
    state = "照合済" if tr.get("verified") else "未検証"
    parts.append('<p class="meta">翻刻状態: %s（%s）</p>'
                 % (state, html.escape(tr.get("method", "")[:120])))
    return "".join(parts)


def ndl_url(pid, rid, size="full"):
    return "https://dl.ndl.go.jp/api/iiif/%s/%s/%s/0/default.jpg" % (
        pid, rid, size)


def page_urls(pid, rid):
    """Left/right page crops at 1600px (IIIF pct regions, no hosting)."""
    return (ndl_url(pid, rid, "pct:0,0,50,100/1600,"),
            ndl_url(pid, rid, "pct:50,0,50,100/1600,"))


def load_column_map(cid="kanju"):
    """Parse docs/columns-<cid>.md into {RID: "x1-x2 / x3-x4 / ..."}."""
    path = os.path.join(ROOT, "docs", "columns-%s.md" % cid)
    out = {}
    if not os.path.exists(path):
        return out
    cur = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^## (R\d{7})", line)
            if m:
                cur = m.group(1)
                continue
            m = re.match(r"^- x範囲: (.+)$", line.strip())
            if m and cur:
                out[cur] = m.group(1)
    return out


def verified_first_moves_text(cid, lo, hi):
    path = os.path.join(ROOT, "docs", "%s-first-moves.json" % cid)
    if not lo or not os.path.exists(path):
        return ""
    data = json.load(open(path, encoding="utf-8"))
    rows = [m for m in data.get("moves", [])
            if lo <= m["number"] <= hi and not m.get("head_unassigned")]
    text = ""
    if rows:
        text = ("# 初手（検証済み）: "
                + " ／ ".join("第%d番 %s" % (m["number"], m["raw"])
                              for m in sorted(rows,
                                              key=lambda x: x["number"])))
    done = {m["number"] for m in rows}
    missing = [n for n in range(lo, hi + 1) if n not in done]
    if missing:
        text = (text + "\n" if text else "") + "# 初手（未検証）: " + " ／ ".join(
            "第%d番" % n for n in missing)
    return text


def write_worksheet(cid, rid, lo, hi):
    """Plain-text worksheet: one numbered line per move, blanks for a human."""
    d = os.path.join(ROOT, "web", "worksheets")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "%s-%s.txt" % (cid, rid))
    pid = COLLECTIONS[cid]["pid"]
    rng = range_label(lo, hi)
    lines = [
        "# %s %s  %s" % (COLLECTIONS[cid]["title"], rid, rng),
        "# 原典: NDL PID:%s %s（web/images/%s_%s.jpg）"
        % (pid, rid, pid, rid),
        "# 原寸: %s" % ndl_url(pid, rid),
        "# 画像左頁(1600px): %s" % page_urls(pid, rid)[0],
        "# 画像右頁(1600px): %s" % page_urls(pid, rid)[1],
        "# 記入はNDL一次資料スキャンの直接読取のみ。推測は「推測」と明記。不明は ?。",
        "# 形式: <手数> <手番> <駒> <行き先2桁|同> <成/不成/打|->",
        "# 行が足りない場合は追記してよい（1題ごとに '# 第N番' の見出しを入れる）。",
        "# 列の x範囲（%% of canvas・右から左へ）: %s"
        % (load_column_map(cid).get(rid, "未生成（tools/find_columns.py で生成）")),
    ]
    first = verified_first_moves_text(cid, lo, hi)
    if first:
        lines.append(first)
    rpath = os.path.join(ROOT, "docs", "%s-procedure-readings.json" % cid)
    if lo and os.path.exists(rpath):
        rdata = json.load(open(rpath, encoding="utf-8"))
        rrows = [r for r in rdata.get("readings", []) if lo <= r["number"] <= hi]
        if rrows:
            lines.append("# 詰手の読み（機械検証前）: " + " ／ ".join(
                "第%d番 %s" % (r["number"],
                                " → ".join(m["raw"] for m in r["moves"])
                                + ("（以降保留）" if r.get("unresolved") else ""))
                for r in sorted(rrows, key=lambda x: x["number"])))
    lines.append("")
    for i in range(1, 61):
        lines.append("%2d %s ____ ____ ____" % (i, "▲" if i % 2 else "△"))
    text = "\n".join(lines) + "\n"
    if CHECK:
        try:
            with open(path, encoding="utf-8") as f:
                if f.read() != text:
                    DIFFS.append(os.path.relpath(path, ROOT))
        except IOError:
            DIFFS.append(os.path.relpath(path, ROOT))
    else:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    return "worksheets/%s-%s.txt" % (cid, rid)


def verified_first_moves(cid, lo, hi):
    """Render verified first moves for the problems covered by this leaf."""
    path = os.path.join(ROOT, "docs", "%s-first-moves.json" % cid)
    if not lo or not os.path.exists(path):
        return ""
    data = json.load(open(path, encoding="utf-8"))
    rows = [m for m in data.get("moves", []) if lo <= m["number"] <= hi]
    if not rows:
        return ""
    items = []
    for m in sorted(rows, key=lambda x: x["number"]):
        items.append("第%d番 %s（%s）"
                     % (m["number"], m["raw"],
                        "成" if m.get("promoted") else "不成"))
    return ('<p class="meta">初手（検証済み）: ' + " ／ ".join(items)
            + "</p>")


def procedure_readings(cid, lo, hi):
    """Readings of 詰手 column heads that cannot be machine-checked."""
    path = os.path.join(ROOT, "docs", "%s-procedure-readings.json" % cid)
    if not lo or not os.path.exists(path):
        return ""
    data = json.load(open(path, encoding="utf-8"))
    rows = [r for r in data.get("readings", []) if lo <= r["number"] <= hi]
    if not rows:
        return ""
    items = []
    for r in sorted(rows, key=lambda x: x["number"]):
        seq = " → ".join(m["raw"] for m in r["moves"])
        if r.get("unresolved"):
            seq += "（以降保留）"
        items.append("第%d番 %s" % (r["number"], seq))
    return ('<p class="meta">詰手の読み（機械検証前）: ' + " ／ ".join(items)
            + "</p>")


def board_links(cid, lo, hi):
    """Links to the matching board drafts (drafts.html has per-problem ids)."""
    if not lo:
        return ""
    links = []
    for n in range(lo, hi + 1):
        links.append('<a href="drafts.html#%s-%03d">第%d番</a>'
                     % (cid, n, n))
    return ('<p class="meta">対応盤面（drafts.html）: '
            + " ／ ".join(links) + "</p>")


def main():
    cards = []
    for cid, spec in COLLECTIONS.items():
        tr = load_transcriptions(cid)
        cards.append('<h2 id="%s">%s</h2>' % (html.escape(cid), html.escape(spec["title"])))
        cards.append('<p class="meta">%s ／ PID:%s ／ %s</p>'
                     % (html.escape(spec["note"]), spec["pid"], ""))
        for rid, rng in spec["leaves"]:
            lo, hi = rng if rng else (None, None)
            img = "images/%s_%s.jpg" % (spec["pid"], rid)
            has_img = os.path.exists(os.path.join(ROOT, "web", img))
            d = tr.get(rid)
            cards.append(
                '<div class="card" id="%s-%s">' % (html.escape(cid), rid)
                + '<h3>%s %s（%s）</h3>' % (
                    html.escape(cid), rid,
                    range_label(lo, hi))
                + (('<figure><img loading="lazy" src="%s" alt="%s %s"></figure>'
                    % (html.escape(img), spec["pid"], rid)) if has_img else "")
                + moves_html(d)
                + verified_first_moves(cid, lo, hi)
                + procedure_readings(cid, lo, hi)
                + board_links(cid, lo, hi)
                + '<p class="meta"><a href="%s">原寸</a> ／ '
                % html.escape(ndl_url(spec["pid"], rid))
                + '<a href="%s">画像左頁 1600px</a> ／ '
                % html.escape(page_urls(spec["pid"], rid)[0])
                + '<a href="%s">画像右頁 1600px</a> ／ '
                % html.escape(page_urls(spec["pid"], rid)[1])
                + '<a href="%s">ワークシート（記入用テキスト）</a> ／ '
                % html.escape(write_worksheet(cid, rid, lo, hi))
                + '<a href="%s">GitHub Issueで手順を報告する（文言入りフォーム）</a></p>'
                % html.escape(issue_url(cid, rid, lo, hi))
                + "</div>")

    page = """<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>詰手（手順）翻刻の募集 | Open Tsume</title>
<style>
 body { font-family: sans-serif; max-width: 1000px; margin: 1em auto; padding: 0 1em; line-height: 1.7; }
 .card { border: 1px solid #999; border-radius: 8px; padding: 1em; margin: 1em 0; background: #fffdf5; }
 .meta { font-size: .9em; color: #333; } .mono { word-break: break-all; }
 img { max-width: 100%; border: 1px solid #ccc; }
 .warn { background: #fff0f0; border: 1px solid #c00; padding: .5em; margin: .5em 0; }
</style></head><body>
<p><a href="index.html">← トップへ</a> ／ <a href="drafts.html">盤面の解読募集</a></p>
<h1>詰手（手順）翻刻の募集</h1>
<div class="warn">このページは下巻・詰手の<strong>手順文</strong>を原典スキャンとともに公開し、
翻刻・照合を募るものです。盤面の詰み・手順の正しさを主張するものではありません。
記入はNDL一次資料スキャンの直接読取のみとし、推測は「推測」と明記してください。</div>
""" + "".join(cards) + """
</body></html>
"""
    out = os.path.join(ROOT, "web", "procedures.html")
    if CHECK:
        try:
            with open(out, encoding="utf-8", newline="") as f:
                if f.read() != page:
                    DIFFS.append(os.path.relpath(out, ROOT))
        except IOError:
            DIFFS.append(os.path.relpath(out, ROOT))
    else:
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(page)
        print("wrote web/procedures.html (%d bytes)" % len(page))
    if CHECK:
        if DIFFS:
            print("out of sync: %s" % ", ".join(DIFFS))
            return 1
        print("procedures page and worksheets in sync")
    return 0


if __name__ == "__main__":
    CHECK = "--check" in sys.argv[1:]
    sys.exit(main())
