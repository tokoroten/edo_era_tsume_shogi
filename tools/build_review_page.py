#!/usr/bin/env python3
"""build_review_page.py — human-comparison guide for never-proven problems.

Problems the solver could not prove may carry transcription errors.
This page lists them in tiers (S: demoted+corroborated, A: short but
unprovable at huge budgets, B: other unproven) with diagrams, solver
status, NDL links and prefilled GitHub-issue links so humans can compare
the record against the archive scan and report back.

Usage: python3 tools/build_review_page.py
Policy: docs/image-policy.md (no scan images for zukou/musou: no public
digital exists; link to NDL search instead), docs/decipher-issues.md.
"""
import glob
import html
import json
import os
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_web  # noqa: E402

REPO = "tokoroten/edo_era_tsume_shogi"


def issue_url(pid, title, moves, tier, why, cid, curl, cident):
    t = f"【比較報告】{pid}（{title}・{tier}）"
    body = f"""<!-- OT-COMPARE-REPORT v1 | id:{pid} -->
<!-- このIssueは https://tokoroten.github.io/edo_era_tsume_shogi/review.html#{pid} から生成されました -->
<!-- 記録図面とNDL一次資料スキャンを見比べて、誤読の疑い・正しい読みを報告してください -->

## 対象
- id: {pid}（記録手順 {moves}手・solver未証明 `{tier}`）
- 疑いの理由: {why}
- NDL: {curl} / {cident}

## 比較結果（該当する方に記入）
- [ ] 記録図面どおり（誤読なし）。対照源（PID/RID/丁）:
- [ ] 誤読あり。下のSFEN案に正しい読みを記入:
```sfen
<正しいと思うSFEN全文。不明升は ? のまま>
```

## 対照源（必須: NDL PID/RID・丁・所蔵記号）
-

## 備考（印影・くずし・版の異同など）
-
"""
    q = urllib.parse.urlencode(
        {"title": t, "body": body, "labels": "compare"})
    return f"https://github.com/{REPO}/issues/new?{q}"


def main():
    recs = {}
    for p in sorted(glob.glob(os.path.join(
            ROOT, "collections", "*", "*", "problems", "*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        recs[d["id"]] = d
    prov = set()
    for line in open(os.path.join(ROOT, "docs", "solver-coverage.md"),
                      encoding="utf-8"):
        if line.startswith("| ") and "PROVEN(" in line:
            prov.add(line.split("|")[1].strip())
    cols = {}
    for cpath in sorted(glob.glob(os.path.join(
            ROOT, "collections", "*", "*", "collection.json"))):
        c = json.load(open(cpath, encoding="utf-8"))
        cols[c["collection_id"]] = c
    tiers = []
    for pid in sorted(recs):
        d = recs[pid]
        if pid in prov:
            continue
        mv = d["solution_moves"]
        if not d["status"]["solution_verified"]:
            tiers.append((pid, "S",
                          "solution_verified=false（格下げ済み）＋solverのbound内否認と整合。不完全作または誤読の疑い"))
        elif mv <= 25:
            tiers.append((pid, "A",
                          f"記録{mv}手の短手数ながら3億ノード級でも未証明。序盤分岐の高密度または図面誤読の疑い"))
        else:
            tiers.append((pid, "B",
                          f"記録{mv}手・solver未証明（予算切れ）。長詰のため証明が高額"))
    cards = []
    data = []
    for pid, tier, why in tiers:
        d = recs[pid]
        cid = d["collection_id"]
        col = cols.get(cid, {})
        csrc = col.get("source", {})
        curl = csrc.get("url", d["source"].get("url", ""))
        cident = csrc.get("identifier", d["source"].get("identifier", ""))
        dig = csrc.get("digital", {}).get("internet_public", "")
        bd, _ = build_web.validate.parse_sfen(d["sfen"])
        asc = build_web.board_ascii(bd)
        hand_b = build_web.hand_str(bd.hand["b"])
        hand_w = build_web.hand_str(bd.hand["w"])
        page = {"musou": "musou.html", "zukou": "zukou.html"}.get(cid, cid + ".html")
        iurl = issue_url(pid, col.get("title", cid), d["solution_moves"],
                         tier, why, cid, curl, cident)
        data.append({"id": pid, "tier": tier, "why": why,
                     "sfen": d["sfen"], "solution_moves": d["solution_moves"],
                     "source_page": d["source"].get("page", ""),
                     "ndl_search": curl, "ndl_identifier": cident,
                     "issue_url": iurl})
        ndl = []
        if curl:
            ndl.append(f'<a href="{html.escape(curl)}">NDL書誌</a>')
        if dig:
            ndl.append(f'<a href="{html.escape(dig)}">NDLデジタル（書誌ID検索）</a>')
        cards.append(
            f'<div class="card" id="{html.escape(pid)}">'
            f"<h3>{html.escape(pid)} "
            f'<span class="badge">要人手比較 ({html.escape(tier)})</span>'
            f'<span class="badge">{d["solution_moves"]}手</span></h3>'
            f"<p>{html.escape(why)}</p>"
            f"<pre>{html.escape(asc)}\n先手の持駒：{html.escape(hand_b)}\n"
            f"後手の持駒：{html.escape(hand_w)}</pre>"
            f'<p class="meta mono">SFEN: {html.escape(d["sfen"])}</p>'
            f'<p class="meta">出典頁: {html.escape(d["source"].get("page", "—") or "—")}'
            f" ／ NDL資料ID: {html.escape(cident or '—')}</p>"
            + (f'<p class="meta">リンク: {" ／ ".join(ndl)}</p>' if ndl else "")
            + f'<p><a href="{html.escape(page)}?id={html.escape(pid)}">'
            f"棋譜ビューアで開く →</a></p>"
            + f'<p><a href="{html.escape(iurl)}">'
            f"GitHub Issueで比較結果・誤り指摘を報告する</a></p>"
            + "</div>")
    counts = {t: sum(1 for _, x, _ in tiers if x == t) for t in "SAB"}
    page = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>要人手比較の問題 | Open Tsume</title>
<style>
  body {{ font-family: sans-serif; max-width: 960px; margin: 1em auto; padding: 0 1em; line-height: 1.7; }}
  .card {{ border: 1px solid #999; border-radius: 8px; padding: 1em; margin: 1em 0; background: #fffdf5; }}
  .badge {{ display: inline-block; border: 1px solid #888; border-radius: 4px; padding: 0 .4em; font-size: .85em; margin-right: .3em; }}
  .meta {{ font-size: .9em; color: #333; }} .mono {{ word-break: break-all; }}
  pre {{ background: #f4f4f4; padding: .5em; overflow-x: auto; }}
  .warn {{ background: #fff0f0; border: 1px solid #c00; padding: .5em; margin: .5em 0; }}
  .filter button {{ min-height: 44px; font-size: 1em; padding: .4em 1em; margin: .2em; }}
</style>
</head>
<body>
<p><a href="index.html">← トップへ</a></p>
<h1>要人手比較の問題（solver未完走＝誤読の可能性）</h1>
<div class="warn">⚠ solverで証明できない問題は、<strong>図面の読み取りに誤りがある可能性</strong>があります。
記録図面と国立国会図書館の一次資料スキャンを見比べてください。
無双・図巧にインターネット公開画像はありません（館内利用・遠隔複写等で対照）。
報告は各カードのIssueリンクから（定型フォーム）。エージェントが回収します
（<a href="https://github.com/tokoroten/edo_era_tsume_shogi/blob/main/docs/decipher-issues.md">運用手順</a>）。
件数: S {counts.get("S", 0)} / A {counts.get("A", 0)} / B {counts.get("B", 0)}。
S=格下げ済み＋solver傍証あり、A=短手数なのに未証明、 B=その他未証明。</div>
<div class="filter">
  <button data-f="all">すべて</button>
  <button data-f="S">Sのみ</button>
  <button data-f="A">Aのみ</button>
  <button data-f="B">Bのみ</button>
</div>
{"".join(cards)}
<script>
document.querySelectorAll(".filter button").forEach((b)=>{{
  b.addEventListener("click", ()=>{{
    const f = b.dataset.f;
    document.querySelectorAll(".card").forEach((c)=>{{
      c.style.display = (f === "all" || c.textContent.includes("(" + f + ")")) ? "" : "none";
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
    with open(os.path.join(ROOT, "web", "review.html"),
              "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    with open(os.path.join(ROOT, "web", "collections", "review.json"),
              "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"wrote web/review.html ({len(cards)} cards)")


if __name__ == "__main__":
    main()
