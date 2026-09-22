#!/usr/bin/env python3
"""write_candidate_kif.py — render UNVERIFIED solver-candidate KIFs for web.

Candidates come from docs/solver-trials-2026-09-22.json (verdict MATE_*).
Output: web/candidates/<id>-candidate.kif (reference only, never a record).
Headers state 未検証・要原典照合 explicitly; records are untouched.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_web  # noqa: E402

CANDIDATES = {
    "gyokuzu-008": ["S*3g", "2h1g", "2f1f"],
    "gyokuzu-043": ["9f9h"],
    "gyokuzu-076": ["S*7f"],
}


def main():
    trials = {r["id"]: r for r in json.load(
        open(os.path.join(ROOT, "docs", "solver-trials-2026-09-22.json"),
             encoding="utf-8"))["results"]}
    outdir = os.path.join(ROOT, "web", "candidates")
    os.makedirs(outdir, exist_ok=True)
    for gid, pv in CANDIDATES.items():
        num = gid.split("-")[1]
        rec = json.load(open(os.path.join(
            ROOT, "collections", "edo", "gyokuzu", "drafts", f"{num}.json"),
            encoding="utf-8"))
        t = trials[gid]
        moves_jp = build_web.render_moves(rec["sfen"], pv)
        lines = [
            f"# Open Tsume SOLVER CANDIDATE {gid} (UNVERIFIED, CC0-1.0)",
            "# 注意: 未検証の参考手順。原典照合前の暫定SFENに対するsolver候補であり、",
            "# 検証解・正解を主張しない。扱いは docs/solver-trials-2026-09-22.json 参照。",
            f"# solver: python tools/mate_search.py -> {','.join(pv)}; "
            f"rust tsume-solver -> {t['verdict']}",
            f"# 原典: {rec['source']['title']}（{rec['source']['repository']}）",
            f"# 出典頁: {rec['source'].get('page', '')}",
            "手合割：詰将棋（候補）",
            "先手：攻方",
            "後手：玉方",
            "手数----指手---------消費時間--",
            build_web.board_ascii(build_web.validate.parse_sfen(rec["sfen"])[0]),
            f"先手の持駒：{build_web.hand_str(build_web.validate.parse_sfen(rec['sfen'])[0].hand['b'])}",
            f"後手の持駒：{build_web.hand_str(build_web.validate.parse_sfen(rec['sfen'])[0].hand['w'])}",
        ]
        for i, s in enumerate(moves_jp, 1):
            lines.append(f"{i:>4} {s}")
        lines.append(f"まで{len(moves_jp)}手で詰み（候補・未検証）")
        with open(os.path.join(outdir, f"{gid}-candidate.kif"),
                  "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
        print("wrote", f"web/candidates/{gid}-candidate.kif")


if __name__ == "__main__":
    main()
