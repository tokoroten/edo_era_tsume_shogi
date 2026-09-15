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


def build():
    problems = sorted(glob.glob(os.path.join(
        ROOT, "collections", "*", "*", "problems", "*.json")))
    outdir = os.path.join(ROOT, "web", "problems")
    os.makedirs(outdir, exist_ok=True)
    index = []
    collections = {}
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
        if cfiles:
            ctitle = json.load(open(cfiles[0], encoding="utf-8")).get(
                "title", ctitle)
        collections[cid] = ctitle
        outputs[f"web/problems/{cid}-{stem}.kif"] = kif
        data = {
            "id": rec["id"], "collection_id": cid, "number": rec["number"],
            "collection_title": collections[cid],
            "author": rec["author"], "published_year": rec["published_year"],
            "sfen": rec["sfen"], "solution_usi": rec["solution_usi"],
            "solution_moves": rec["solution_moves"],
            "moves_jp": moves_jp,
            "status": rec["status"], "verification": rec["verification"],
            "source": rec["source"], "rights": rec["rights"],
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
    outputs["web/index.json"] = json.dumps(
        {"collections": [{"id": cid, "title": t}
                         for cid, t in sorted(collections.items())],
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
                    open(path, encoding="utf-8").read() != content):
                dirty.append(rel)
        else:
            with open(path, "w", encoding="utf-8") as f:
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
