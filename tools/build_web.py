#!/usr/bin/env python3
"""build_web.py — generate GitHub Pages data (KIF/JSON/viewer index) from records.

All derived artifacts (Japanese notation, KIF text) are generated from the
canonical USI/SFEN in collections/, never hand-edited.

Usage:
    python3 tools/build_web.py            # regenerate web/problems/*, web/index.json
    python3 tools/build_web.py --check    # CI: fail if generated files differ
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import validate  # noqa: E402

ZEN = "０１２３４５６７８９"
KAN = "〇一二三四五六七八九"
JP_NAME = {"P": "歩", "L": "香", "N": "桂", "S": "銀", "G": "金",
           "B": "角", "R": "飛", "K": "玉"}
JP_PROM = {"P": "と", "L": "杏", "N": "圭", "S": "全", "B": "馬", "R": "龍"}


def jp_sq(f, r):
    return f"{ZEN[f]}{KAN[r]}"


def render_moves(sfen, usi_list):
    """Replay USI -> Japanese move strings (with 同/打/成/不成/from)."""
    bd, errs = validate.parse_sfen(sfen)
    assert not errs, errs
    bd = bd.clone()
    out = []
    prev_dest = None
    for i, m in enumerate(usi_list):
        side = "▲" if i % 2 == 0 else "△"
        par, err = validate.parse_usi(m)
        assert not err, err
        if par[0] == "drop":
            _, kind, t = par
            s = f"{side}{jp_sq(*t)}{JP_NAME[kind]}打"
            bd.sq[t] = [bd.side, kind, False]
            bd.hand[bd.side][kind] -= 1
        else:
            _, frm, t, prom = par
            color, kind, already = bd.sq[frm]
            if prom:
                name, suffix = JP_NAME[kind], "成"
            elif already:
                name, suffix = JP_PROM[kind], ""
            elif (kind in validate.PROMOTABLE and
                    (validate.in_zone(color, frm[1]) or
                     validate.in_zone(color, t[1]))):
                name, suffix = JP_NAME[kind], "不成"
            else:
                name, suffix = JP_NAME[kind], ""
            dest = "同　" if t == prev_dest else jp_sq(*t)
            s = f"{side}{dest}{name}({frm[0]}{frm[1]}){suffix}"
            occ = bd.sq.get(t)
            if occ is not None:
                bd.hand[color][occ[1]] = bd.hand[color].get(occ[1], 0) + 1
            del bd.sq[frm]
            bd.sq[t] = [color, kind, already or prom]
        bd.side = validate.opp(bd.side)
        out.append(s)
        prev_dest = t
    return out


def board_ascii(bd):
    rows = ["  ９ ８ ７ ６ ５ ４ ３ ２ １",
            "+---------------------------+"]
    for r in range(1, 10):
        cells = []
        for f in range(9, 0, -1):
            p = bd.sq.get((f, r))
            if p is None:
                cells.append("・")
                continue
            color, kind, prom = p
            ch = JP_PROM[kind] if prom else JP_NAME[kind]
            cells.append(("v" if color == "w" else " ") + ch)
        rows.append("|" + "".join(f"{c:>3}" for c in cells) + "|")
    rows.append("+---------------------------+")
    return "\n".join(rows)


def hand_str(hand):
    parts = []
    for k in ["R", "B", "G", "S", "N", "L", "P"]:
        n = hand.get(k, 0)
        if n:
            parts.append(f"{JP_NAME[k]}{n if n > 1 else ''}")
    return "　".join(parts) if parts else "なし"


def render_kif(rec, moves_jp):
    bd, _ = validate.parse_sfen(rec["sfen"])
    L = []
    L.append(f"# Open Tsume record {rec['id']} (CC0-1.0)")
    L.append(f"# 原典: {rec['source']['title']}（{rec['source']['repository']}）")
    L.append("手合割：詰将棋")
    L.append("先手：攻方")
    L.append("後手：玉方")
    L.append("手数----指手---------消費時間--")
    L.append(board_ascii(bd))
    L.append(f"先手の持駒：{hand_str(bd.hand['b'])}")
    L.append(f"後手の持駒：{hand_str(bd.hand['w'])}")
    for i, s in enumerate(moves_jp, 1):
        L.append(f"{i:>4} {s}")
    L.append(f"まで{len(moves_jp)}手で詰み")
    return "\n".join(L) + "\n"


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page_title}</title>
<style>
  body {{ font-family: sans-serif; max-width: 960px; margin: 1em auto; padding: 0 1em; }}
  table.board {{ border-collapse: collapse; margin: 1em 0; }}
  table.board td {{ width: 46px; height: 50px; border: 1px solid #333; text-align: center;
                   font-size: 22px; background: #f8e9c0; position: relative; padding: 2px; }}
  table.board td.last {{ background: #ffe08a; }}
  /* Piece pentagon styles adapted from tokoroten/tsume board.css */
  .piece {{ display: block; width: 100%; height: 100%; overflow: visible;
           filter: drop-shadow(0 1.5px 1px rgb(69 43 15 / 30%)); }}
  .piece--defender {{ transform: rotate(180deg); }}
  .piece__body {{ fill: #f6e3bd; stroke: #5a3a1a; stroke-width: 2.4; stroke-linejoin: round; }}
  .piece--defender .piece__body {{ fill: #efd9ac; }}
  .piece__highlight {{ fill: none; stroke: rgb(255 247 221 / 55%); stroke-width: 2;
                      stroke-linecap: round; pointer-events: none; }}
  .piece__kanji {{ font-weight: 700; fill: #1a1a1a; text-anchor: middle; }}
  .piece__kanji--promoted {{ fill: #a00; }}
  .piece__latin {{ font-weight: 700; fill: #1a1a1a; text-anchor: middle; }}
  .piece__promoted-bar {{ fill: #a00; }}
  .w {{ color: #a00; }}
  .b {{ color: #111; }}
  .prom {{ text-decoration: underline; }}
  #moves {{ max-height: 300px; overflow-y: auto; border: 1px solid #ccc; padding: .5em; }}
  #moves div.cur {{ background: #fff3b0; }}
  .badge {{ display:inline-block; border:1px solid #888; border-radius:4px; padding:0 .4em;
           font-size:.85em; margin-right:.3em; }}
  .warn {{ background:#fff0f0; border:1px solid #c00; padding:.5em; margin:.5em 0; }}
  .meta {{ font-size:.9em; color:#333; }}
  button {{ margin:.2em; }}
</style>
</head>
<body>
<p><a href="index.html">← 作品集一覧へ</a></p>
<h1>{heading}</h1>
<p class="meta">原作品 Public Domain ／ 本データ CC0-1.0 ／
  <a href="https://github.com/tokoroten/edo_era_tsume_shogi">GitHub: tokoroten/edo_era_tsume_shogi</a></p>

<label>問題:
<select id="plist"></select></label>
<span id="badges"></span>
<div id="review" class="warn" style="display:none"></div>

<h2 id="title"></h2>
<table class="board" id="board"></table>
<p class="meta" id="hands"></p>
<p>
  <button id="prev">◀ 前</button>
  <button id="next">次 ▶</button>
  <button id="start">⏮ 初期局面</button>
  <button id="end">⏭ 最終局面</button>
  <button id="copySfen">SFENをコピー</button>
  <a id="dlKif" href="#">KIFをダウンロード</a> /
  <a id="dlJson" href="#">JSONをダウンロード</a>
</p>

<h3>手順（日本語表記はUSIから自動生成）</h3>
<details>
<summary>解答手順を表示（ネタバレ注意）</summary>
<div id="moves"></div>
</details>

<h3>出典・検証情報</h3>
<div class="meta" id="prov"></div>

<script>window.OT_CONFIG = {{index: "collections/{cid}.json", dir: "problems/"}};</script>
<script src="pieces-port.js"></script>
<script src="viewer.js"></script>
</body>
</html>
"""


def build():
    problems = sorted(glob.glob(os.path.join(
        ROOT, "collections", "*", "*", "problems", "*.json")))
    outdir = os.path.join(ROOT, "web", "problems")
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(os.path.join(ROOT, "web", "collections"), exist_ok=True)
    index = []
    collections = {}
    col_meta = {}
    outputs = {}
    for p in problems:
        rec = json.load(open(p, encoding="utf-8"))
        moves_jp = render_moves(rec["sfen"], rec["solution_usi"])
        kif = render_kif(rec, moves_jp)
        stem = os.path.splitext(os.path.basename(p))[0]
        cid = rec["collection_id"]
        cpath = os.path.join(ROOT, "collections", "*", cid, "collection.json")
        cfiles = glob.glob(cpath)
        ctitle = rec["source"]["title"]
        if cfiles and cid not in col_meta:
            col = json.load(open(cfiles[0], encoding="utf-8"))
            ctitle = col.get("title", ctitle)
            col_meta[cid] = col
        collections[cid] = ctitle
        outputs[f"web/problems/{cid}-{stem}.kif"] = kif
        src = dict(rec["source"])
        if "digital" not in src:
            col_src = col_meta.get(cid, {}).get("source", {})
            if "digital" in col_src:
                src["digital"] = col_src["digital"]
        status = dict(rec["status"])
        if "intended_solution_verified" not in status:
            status["intended_solution_verified"] = False
        data = {
            "id": rec["id"], "collection_id": cid, "number": rec["number"],
            "collection_title": collections[cid],
            "author": rec["author"], "published_year": rec["published_year"],
            "sfen": rec["sfen"], "solution_usi": rec["solution_usi"],
            "solution_moves": rec["solution_moves"],
            "intended_solution_usi": rec.get("intended_solution_usi"),
            "intended_solution_moves": rec.get("intended_solution_moves"),
            "intended_solution_source": rec.get("intended_solution_source"),
            "moves_jp": moves_jp,
            "status": status, "verification": rec["verification"],
            "source": src, "rights": rec["rights"],
            "notes": rec.get("notes", []),
            "kif": f"problems/{cid}-{stem}.kif",
            "json": f"problems/{cid}-{stem}.json",
        }
        outputs[f"web/problems/{cid}-{stem}.json"] = json.dumps(
            data, ensure_ascii=False, indent=2) + "\n"
        index.append({"id": rec["id"], "number": rec["number"],
                      "collection_id": cid,
                      "collection_title": collections[cid],
                      "solution_moves": rec["solution_moves"],
                      "needs_manual_review": rec["verification"]["needs_manual_review"],
                      "solution_verified": rec["status"]["solution_verified"],
                      "data": f"problems/{cid}-{stem}.json"})
    by_col = {}
    for e in index:
        by_col.setdefault(e["collection_id"], []).append(e)
    col_list = []
    for cid in sorted(collections):
        col = col_meta.get(cid, {})
        probs = sorted(by_col.get(cid, []), key=lambda d: d["number"])
        verified = sum(1 for e in probs if e["solution_verified"])
        review = sum(1 for e in probs if e["needs_manual_review"])
        col_list.append({
            "id": cid,
            "title": collections[cid],
            "author": col.get("author"),
            "published_year": col.get("published_year"),
            "published_year_note": col.get("published_year_note"),
            "problem_count": col.get("problem_count"),
            "transcribed": len(probs),
            "solution_verified": verified,
            "needs_manual_review": review,
            "page": f"{cid}.html",
        })
        outputs[f"web/collections/{cid}.json"] = json.dumps(
            {"collection_id": cid, "title": collections[cid],
             "problems": probs}, ensure_ascii=False, indent=2) + "\n"
        heading = (f"{collections[cid]} — {col.get('author', '')}"
                   f"（推定出版年: {col.get('published_year', '—')}年）"
                   if col else collections[cid])
        outputs[f"web/{cid}.html"] = PAGE_TEMPLATE.format(
            page_title=f"{collections[cid]} | Open Tsume",
            heading=heading, cid=cid)
    outputs["web/index.json"] = json.dumps(
        {"collections": col_list,
         "problems": sorted(index,
                            key=lambda d: (d["collection_id"], d["number"]))},
        ensure_ascii=False, indent=2) + "\n"
    return outputs


def main():
    check = "--check" in sys.argv
    outputs = build()
    dirty = []
    for rel, content in outputs.items():
        path = os.path.join(ROOT, rel)
        if check:
            if (not os.path.exists(path) or
                    open(path, encoding="utf-8", newline="").read() != content):
                dirty.append(rel)
        else:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            print("wrote", rel)
    if check:
        if dirty:
            print("out of sync:", *dirty, file=sys.stderr)
            return 1
        print("web data in sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())
