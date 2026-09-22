#!/usr/bin/env python3
"""build_drafts_page.py — generate the decipher-recruitment page for drafts.

Reads collections/edo/*/drafts/*.json (+ collection.json + the solver
trials report) and writes:
  web/drafts.html
  web/collections/gyokuzu_drafts.json
  web/collections/kinza_drafts.json

Drafts are staging (never promoted). This page shows the CURRENT
transcription state per draft: diagram with ? squares, ? count, NDL
links, gap notes and solver-candidate badges, inviting human collation.
It never claims a verified solution.

Usage:
    python3 tools/build_drafts_page.py
"""
import glob
import html
import json
import os
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REPO = "tokoroten/edo_era_tsume_shogi"
ISSUE_LABEL = "decipher"


def issue_url(d, col_title):
    """Prefilled GitHub-issue URL carrying a machine-parsable report form.

    Format version OT-DECIPHER-REPORT v1 (see docs/decipher-issues.md).
    Humans fill the blank fences by eye-reading NDL scans; agents later
    ingest open issues with that marker and transcribe into drafts/.
    """
    title = f"【解読報告】{d['id']}（{col_title} 第{d['number']}番）"
    body = f"""<!-- OT-DECIPHER-REPORT v1 | id:{d['id']} -->
<!-- このIssueは https://tokoroten.github.io/edo_era_tsume_shogi/drafts.html#{d['id']} から生成されました -->
<!-- 記入はNDL一次資料スキャンの直接読取のみ。推測は「推測」と明記すること -->

## 対象
- id: {d['id']}
- 現SFEN: `{d['sfen']}`
- 出典頁: {d['page']}
- 読取源(現状): {d['transcribed_from']}
- NDL: {d['url']} / {d['digital']}

## 盤面読み（目視結果をSFENで記入。不明升は ? のまま残すこと）
```sfen
<d['sfen'] と異なる場合のみ、読み取ったSFEN全文をここに貼る>
```

## 手順読み（USI配列または日本語棋譜。列番号付きが望ましい）
```usi
<例: 7g7f / S*3g …。不明手は ???? と書く>
```

## 読取源（必須: NDL PID / RID / 列範囲・丁）
- <例: NDL PID:861197 R0000010右 / NDL PID:861198 R0000003>

## 備考（印影・くずし・推測箇所の明示）
-
"""
    q = urllib.parse.urlencode(
        {"title": title, "body": body, "labels": ISSUE_LABEL})
    return f"https://github.com/{REPO}/issues/new?{q}"

JP = {"P": "歩", "L": "香", "N": "桂", "S": "銀", "G": "金",
      "B": "角", "R": "飛", "K": "玉"}
JPP = {"P": "と", "L": "杏", "N": "圭", "S": "全", "B": "馬", "R": "龍"}


def parse_board(sfen):
    """Parse board part of SFEN, keeping '?' as None-unknown."""
    bpart = sfen.split(" ")[0]
    rows = []
    for seg in bpart.split("/"):
        row = []
        prom = False
        for c in seg:
            if c == "+":
                prom = True
                continue
            if c.isdigit():
                row.extend([("empty", None, False)] * int(c))
                continue
            if c == "?":
                row.append(("unknown", None, False))
                prom = False
                continue
            color = "b" if c.isupper() else "w"
            row.append(("piece", color + c.upper(), prom))
            prom = False
        while len(row) < 9:
            row.append(("empty", None, False))
        rows.append(row[:9])
    return rows


def board_html(sfen):
    rows = parse_board(sfen)
    L = ['<table class="board" aria-label="現転記盤面（？は未読升）">']
    for r in rows:
        L.append("<tr>")
        for kind, code, prom in r:
            if kind == "empty":
                L.append('<td class="empty">・</td>')
            elif kind == "unknown":
                L.append('<td class="unk">？</td>')
            else:
                color, k = code[0], code[1]
                name = JPP[k] if prom and k in JPP else JP.get(k, k)
                cls = "b" if color == "b" else "w"
                pro = " prom" if prom else ""
                L.append(f'<td><span class="{cls}{pro}">{name}</span></td>')
        L.append("</tr>")
    L.append("</table>")
    return "".join(L)


def load_trials():
    p = os.path.join(ROOT, "docs", "solver-trials-2026-09-22.json")
    if not os.path.exists(p):
        return {}
    doc = json.load(open(p, encoding="utf-8"))
    return {r["id"]: r for r in doc.get("results", [])}


def main():
    trials = load_trials()
    collections = {}
    for cpath in sorted(glob.glob(os.path.join(
            ROOT, "collections", "*", "*", "collection.json"))):
        col = json.load(open(cpath, encoding="utf-8"))
        collections[col["collection_id"]] = col
    groups = {}
    for dpath in sorted(glob.glob(os.path.join(
            ROOT, "collections", "*", "*", "drafts", "*.json"))):
        rec = json.load(open(dpath, encoding="utf-8"))
        cid = rec["collection_id"]
        sfen = rec.get("sfen", "")
        try:
            hand = sfen.split(" ")[2]
        except IndexError:
            hand = ""
        gap = ""
        for n in rec.get("notes", []):
            if n.startswith("gap:"):
                gap = n if len(n) <= 400 else n[:400] + "…"
                break
        ver = rec.get("verification", {})
        src = rec.get("source", {})
        col = collections.get(cid, {})
        dig = col.get("source", {}).get("digital", {})
        t = trials.get(rec["id"])
        if t:
            v = t["verdict"]
            badge = {"MATE_3_CROSS_CONFIRMED": "solver候補: 3手詰（2エンジン一致・要照合）",
                     "MATE_1_CROSS_CONFIRMED_SUSPECT_POSITION": "solver候補: 1手詰（2エンジン一致・図面要再読）",
                     "REFUTED_WITHIN_7": "solver: 7手以内詰まず（要再読）",
                     "MATE_1_UNDER_VALIDATOR_BOX_UNKNOWN_UNDER_STRICT_BOX":
                     "solver候補: 駒箱次第（要照合）"}.get(v, v)
        else:
            badge = "未試行（?残のため対象外）" if "?" in sfen else "未試行"
        cand_rel = f"candidates/{rec['id']}-candidate.kif"
        has_cand = os.path.exists(os.path.join(ROOT, "web", cand_rel))
        groups.setdefault(cid, []).append({
            "id": rec["id"], "number": rec.get("number"),
            "candidate_kif": cand_rel if has_cand else "",
            "issue_url": issue_url(
                {"id": rec["id"], "number": rec.get("number"),
                 "sfen": sfen, "page": src.get("page", ""),
                 "url": src.get("url", ""),
                 "digital": dig.get("internet_public", ""),
                 "transcribed_from": ver.get("transcribed_from", "")},
                col.get("title", cid)),
            "sfen": sfen, "q": sfen.count("?"), "hand": hand,
            "page": src.get("page", ""),
            "url": src.get("url", ""),
            "digital": dig.get("internet_public", ""),
            "transcribed_from": ver.get("transcribed_from", ""),
            "intended_source": rec.get("intended_solution_source", ""),
            "gap": gap,
            "solver": badge,
            "solver_detail": (t or {}).get("handling", ""),
        })
    outdir = os.path.join(ROOT, "web", "collections")
    os.makedirs(outdir, exist_ok=True)
    for cid, items in groups.items():
        items.sort(key=lambda d: (d["q"], d["number"]))
        with open(os.path.join(outdir, f"{cid}_drafts.json"),
                  "w", encoding="utf-8", newline="\n") as f:
            json.dump({"collection_id": cid,
                       "title": collections.get(cid, {}).get("title", cid),
                       "drafts": items}, f, ensure_ascii=False, indent=2)
            f.write("\n")
    cards = []
    for cid in sorted(groups):
        col = collections.get(cid, {})
        cards.append(
            f'<h2 id="{html.escape(cid)}">{html.escape(col.get("title", cid))}'
            f"（解読募集中・draft {len(groups[cid])}件）</h2>"
            f'<p class="meta">NDL書誌: {html.escape(col.get("source", {}).get("identifier", ""))} ／ '
            f'<a href="{html.escape(col.get("source", {}).get("url", "#"))}">国立国会図書館サーチ（書誌）</a>'
            + (f' ／ <a href="{html.escape(col.get("source", {}).get("digital", {}).get("internet_public", "#"))}">'
               "デジタルコレクション（書誌ID検索）</a>" if col.get("source", {}).get("digital", {}).get("internet_public") else "")
            + "</p>")
        for d in groups[cid]:
            ndl_links = []
            if d["url"]:
                ndl_links.append(f'<a href="{html.escape(d["url"])}">NDL書誌</a>')
            if d["digital"]:
                ndl_links.append(f'<a href="{html.escape(d["digital"])}">NDLデジタル（書誌ID検索）</a>')
            cards.append(
                f'<div class="card" id="{html.escape(d["id"])}" data-cid="{html.escape(cid)}" data-q="{d["q"]}">'
                f'<h3>{html.escape(d["id"])}（第{d["number"]}番） '
                f'<span class="badge">？残 {d["q"]}</span> '
                f'<span class="badge">{html.escape(d["solver"])}</span></h3>'
                f"{board_html(d['sfen'])}"
                f'<p class="meta mono">SFEN: {html.escape(d["sfen"])}</p>'
                f'<p class="meta">持駒: {html.escape(d["hand"] or "—")}</p>'
                f'<p class="meta">出典頁: {html.escape(d["page"] or "—")}</p>'
                f'<p class="meta">読取源: {html.escape(d["transcribed_from"] or "—")}</p>'
                f'<p class="meta">手順翻刻: {html.escape(d["intended_source"] or "—")}</p>'
                + (f'<p class="meta">残件: {html.escape(d["gap"])}</p>' if d["gap"] else "")
                + (f'<p class="meta">solver: {html.escape(d["solver_detail"])}</p>' if d["solver_detail"] else "")
                + (f'<p class="meta">リンク: {" ／ ".join(ndl_links)}</p>' if ndl_links else "")
                + (f'<p class="meta"><a href="{html.escape(d["candidate_kif"])}">'
                    "solver候補棋譜（KIF・未検証・参考）をダウンロード</a></p>"
                    if d.get("candidate_kif") else "")
                + (f'<p class="meta"><a href="{html.escape(issue_url(d, col.get("title", cid)))}">'
                    "GitHub Issueで解読結果を報告する（文言入りフォームを開く）</a></p>")
                + "</div>")
    page = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>解読募集中の図面 | Open Tsume</title>
<style>
  body {{ font-family: sans-serif; max-width: 960px; margin: 1em auto; padding: 0 1em; line-height: 1.7; }}
  table.board {{ border-collapse: collapse; margin: .5em 0; }}
  table.board td {{ width: 40px; height: 44px; border: 1px solid #333; text-align: center; font-size: 20px; background: #f8e9c0; }}
  table.board td.empty {{ color: #999; }} table.board td.unk {{ background: #ffe08a; font-weight: 700; }}
  .w {{ color: #a00; display: inline-block; transform: rotate(180deg); }} .b {{ color: #111; }} .prom {{ text-decoration: underline; }}
  .card {{ border: 1px solid #999; border-radius: 8px; padding: 1em; margin: 1em 0; background: #fffdf5; }}
  .badge {{ display: inline-block; border: 1px solid #888; border-radius: 4px; padding: 0 .4em; font-size: .85em; margin-right: .3em; }}
  .meta {{ font-size: .9em; color: #333; }} .mono {{ word-break: break-all; }}
  .warn {{ background: #fff0f0; border: 1px solid #c00; padding: .5em; margin: .5em 0; }}
  .filter {{ display: flex; gap: .5em; flex-wrap: wrap; align-items: center; border: 1px solid #ccc; border-radius: 8px; padding: .8em; background: #fff; }}
  .filter button {{ min-height: 44px; font-size: 1em; padding: .4em 1em; }}
</style>
</head>
<body>
<p><a href="index.html">← トップへ</a></p>
<h1>解読募集中の図面（draft・未確定）</h1>
<div class="warn">⚠ このページの盤面は転記途中の <strong>draft</strong> です。「？」は未読升を示し、詰み・手順の主張はしません。
原典（国立国会図書館スキャン）との照合にご協力ください。各図面の
「GitHub Issueで解読結果を報告する」リンクから、記入欄入りの報告フォームを開けます。
報告Issueはエージェントが回収しdraftへ反映します（運用手順は
<a href="https://github.com/tokoroten/edo_era_tsume_shogi/blob/main/docs/decipher-issues.md">docs/decipher-issues.md</a>）。
参加方法は <a href="https://github.com/tokoroten/edo_era_tsume_shogi/blob/main/CONTRIBUTING.md">CONTRIBUTING.md</a> 参照。
solver候補の表示は未検証の参考情報であり、原典照合を代替しません。</div>
<div class="filter">
  <button data-f="all">すべて</button>
  <button data-f="gyokuzu">玉図のみ</button>
  <button data-f="kinza">絹篩のみ</button>
  <button data-f="solved-candidate">solver候補あり</button>
</div>
{"".join(cards)}
<script>
document.querySelectorAll(".filter button").forEach((b)=>{{
  b.addEventListener("click", ()=>{{
    const f = b.dataset.f;
    document.querySelectorAll(".card").forEach((c)=>{{
      const show = f === "all" || c.dataset.cid === f ||
        (f === "solved-candidate" && /solver候補/.test(c.textContent));
      c.style.display = show ? "" : "none";
    }});
  }});
}});
if (location.hash) {{
  const el = document.querySelector(location.hash);
  if (el) el.scrollIntoView();
}}
</script>
</body>
</html>
"""
    with open(os.path.join(ROOT, "web", "drafts.html"),
              "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print(f"wrote web/drafts.html + {len(groups)} drafts JSON files")


if __name__ == "__main__":
    main()
