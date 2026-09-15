#!/usr/bin/env python3
"""kif2open.py — KIF (Kifu-for-JS style, Shift_JIS) -> Open Tsume problem JSON.

This is *tooling* (MIT). It transcribes board + main-line moves (facts) from
a KIF file into the canonical Open Tsume record. Commentary lines (`*`) and
variations are ignored. Every output record keeps `needs_manual_review: true`
until a human collates it against the primary-source archive scans.

Usage:
    python3 tools/kif2open.py <in.kif> --id zukou-001 --collection zukou \\
        --number 1 --out collections/edo/zukou/problems/001.json
"""
import argparse
import json
import re
import sys

ZEN_DIGITS = {c: i for i, c in enumerate("０１２３４５６７８９")}
KANJI_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
             "六": 6, "七": 7, "八": 8, "九": 9}
KANJI_RANK = KANJI_NUM
PIECE_JP = {"歩": "P", "香": "L", "桂": "N", "銀": "S", "金": "G",
            "角": "B", "飛": "R", "玉": "K", "王": "K",
            "と": "+P", "杏": "+L", "圭": "+N", "全": "+S",
            "成香": "+L", "成桂": "+N", "成銀": "+S",
            "馬": "+B", "龍": "+R", "竜": "+R"}
SFEN_ORDER = ["R", "B", "G", "S", "N", "L", "P"]


def zen_int(s):
    out = ""
    for c in s:
        if c in ZEN_DIGITS:
            out += str(ZEN_DIGITS[c])
        elif c.isascii() and c.isdigit():
            out += c
        else:
            raise ValueError(f"bad digit: {c!r}")
    return int(out)


def kanji_count(s):
    """Parse 短い漢数字 (e.g. 二, 十一, 十三, 十六, 二十)."""
    if not s:
        return 1
    total = 0
    tmp = 0
    for c in s:
        if c == "十":
            tmp = 10 if tmp == 0 else tmp * 10
        elif c in KANJI_NUM:
            tmp += KANJI_NUM[c]
        else:
            raise ValueError(f"bad kanji numeral: {s!r}")
    return tmp if tmp else total


def parse_hand(line):
    """'後手の持駒：金二　桂　香二　歩十一' -> {'G':2,'N':1,'L':2,'P':11}."""
    m = re.search(r"[：:](.*)$", line)
    body = m.group(1).strip() if m else ""
    if not body or "なし" in body:
        return {}
    hand = {}
    for tok in re.split(r"[\s　]+", body):
        if not tok:
            continue
        mm = re.match(r"^(歩|香|桂|銀|金|角|飛)(.*)$", tok)
        if not mm:
            raise ValueError(f"bad hand token: {tok!r}")
        jp, cnt = mm.group(1), mm.group(2)
        hand[PIECE_JP[jp]] = kanji_count(cnt)
    return hand


def parse_board(rows):
    """9 diagram rows -> dict {(file,rank): (color, kind, promoted)}."""
    board = {}
    for line in rows:
        m = re.search(r"\|(.*)\|\s*([一二三四五六七八九])", line)
        if not m:
            continue
        cells = re.findall(r"v?[・歩香桂銀金角飛玉王と馬龍杏圭全竜]",
                           m.group(1).replace(" ", "").replace("　", ""))
        rank = KANJI_RANK[m.group(2)]
        if len(cells) != 9:
            raise ValueError(f"board row has {len(cells)} cells: {line!r}")
        for i, cell in enumerate(cells):
            f = 9 - i
            if cell in ("・", "·", ".", ""):
                continue
            color = "w" if cell.startswith("v") else "b"
            jp = cell[1:] if color == "w" else cell
            if jp not in PIECE_JP:
                raise ValueError(f"unknown piece {cell!r}")
            code = PIECE_JP[jp]
            promoted = code.startswith("+")
            board[(f, rank)] = (color, code.lstrip("+"), promoted)
    return board


MOVE_RE = re.compile(
    r"^\s*(\d+)\s+(同|[０-９0-9][一二三四五六七八九])"
    r"(成銀|成桂|成香|王|玉|飛|龍|竜|角|馬|金|銀|全|桂|圭|香|杏|歩|と)"
    r"(成|不成)?(\((\d+)\)|打)\s*(\+)?\s*$"
)


def board_to_sfen(board, sente_hand, gote_hand):
    parts = []
    for rank in range(1, 10):
        empty = 0
        seg = ""
        for f in range(9, 0, -1):
            p = board.get((f, rank))
            if p is None:
                empty += 1
                continue
            if empty:
                seg += str(empty)
                empty = 0
            color, kind, prom = p
            ch = kind if color == "b" else kind.lower()
            seg += ("+" if prom else "") + ch
        if empty:
            seg += str(empty)
        parts.append(seg)
    hand = ""
    for color, h in (("b", sente_hand), ("w", gote_hand)):
        for k in SFEN_ORDER:
            c = h.get(k, 0)
            if c:
                ch = k if color == "b" else k.lower()
                hand += (str(c) if c > 1 else "") + ch
    return f"{'/'.join(parts)} b {hand or '-'} 1"


def to_usi_sq(f, rank):
    return f"{f}{chr(ord('a') + rank - 1)}"


def convert_moves(board, sente_hand, move_lines):
    """KIF main-line moves -> USI list. Applies moves to resolve 同."""
    b = dict(board)
    usi_moves = []
    prev_dest = None
    for lineno, text in move_lines:
        m = MOVE_RE.match(text)
        if not m:
            raise ValueError(f"line {lineno}: unparsable move: {text!r}")
        n, dest_s, jp, naru, from_s, from_xy, _plus = m.groups()
        n = int(n)
        if dest_s == "同":
            if prev_dest is None:
                raise ValueError(f"line {lineno}: 同 with no previous move")
            dest = prev_dest
        else:
            dest = (zen_int(dest_s[0]), KANJI_NUM[dest_s[1]])
        code = PIECE_JP[jp]
        disp_prom = code.startswith("+")
        kind = code.lstrip("+")
        if from_s == "打":
            frm = None
        else:
            frm = (int(from_xy[0]), int(from_xy[1]))
        side = "b" if n % 2 == 1 else "w"
        if frm is None:
            usi = f"{kind}*{to_usi_sq(*dest)}"
            b[dest] = (side, kind, False)
        else:
            if frm not in b:
                raise ValueError(f"line {lineno}: no piece at {frm}: {text!r}")
            color, bk, bprom = b[frm]
            if color != side:
                raise ValueError(f"line {lineno}: wrong side at {frm}: {text!r}")
            promote = False
            if naru == "成":
                promote = True
            elif disp_prom and not bprom:
                promote = True
            usi = f"{to_usi_sq(*frm)}{to_usi_sq(*dest)}{'+' if promote else ''}"
            del b[frm]
            b[dest] = (side, bk, bprom or promote)
        usi_moves.append(usi)
        prev_dest = dest
    return usi_moves


def parse_kif(path):
    raw = open(path, "rb").read()
    text = raw.decode("cp932")
    lines = text.splitlines()
    meta = {}
    board_rows = []
    sente_hand, gote_hand = {}, {}
    in_board = False
    moves = []
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith("変化"):
            break
        if s.startswith("後手の持駒"):
            gote_hand = parse_hand(s)
            continue
        if s.startswith("先手の持駒"):
            sente_hand = parse_hand(s)
            continue
        if s.startswith("+----------------"):
            in_board = not in_board
            continue
        if in_board:
            board_rows.append(line)
            continue
        for key, pat in (("source_title", r"^出典[：:](.*)"),
                         ("num", r"^作品番号[：:](.*)"),
                         ("author", r"^作者[：:](.*)"),
                         ("year", r"^発表年月[：:](.*)"),
                         ("moves_declared", r"^手数[：:](.*)")):
            mm = re.match(pat, s)
            if mm:
                meta[key] = mm.group(1).strip()
        if not s or s.startswith("*"):
            continue
        if re.match(r"^\s*\d+\s+", line) and re.search(
                r"[王玉飛龍竜角馬金銀全桂圭香杏歩と]", line):
            if MOVE_RE.match(line):
                moves.append((i, line.rstrip()))
            else:
                raise ValueError(f"line {i}: looks like a move but unparsable: {line!r}")
    board = parse_board(board_rows)
    return meta, board, sente_hand, gote_hand, moves


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kif")
    ap.add_argument("--id", required=True)
    ap.add_argument("--collection", required=True)
    ap.add_argument("--number", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ref-url", default="")
    ap.add_argument("--transcriber", default="edo_era_tsume_shogi maintainers")
    ap.add_argument("--author", default="伊藤看寿")
    ap.add_argument("--year", type=int, default=1755)
    ap.add_argument("--source-title", default="将棋図巧")
    ap.add_argument("--src-identifier",
                    default="NDLBibID:000000493927 / 請求記号:209-461")
    ap.add_argument("--src-url",
                    default="https://ndlsearch.ndl.go.jp/books/R100000002-I000000493927")
    ap.add_argument("--src-edition", default=None)
    ap.add_argument("--transcribed-from", default=None)
    args = ap.parse_args()

    meta, board, sh, gh, moves = parse_kif(args.kif)
    declared = zen_int(re.sub(r"[^\d０-９]", "", meta.get("moves_declared", "")) or "0")
    if declared and declared != len(moves):
        print(f"warning: declared {declared} moves but parsed {len(moves)}",
              file=sys.stderr)
    usi = convert_moves(board, sh, moves)
    sfen = board_to_sfen(board, sh, gh)

    rec = {
        "id": args.id,
        "collection_id": args.collection,
        "number": args.number,
        "title": None,
        "author": args.author,
        "published_year": args.year,
        "period": "Edo",
        "sfen": sfen,
        "corrected_sfen": None,
        "correction_note": None,
        "solution_usi": usi,
        "solution_moves": len(usi),
        "status": {
            "position_verified": False,
            "solution_verified": False,
            "unique_solution_verified": False,
        },
        "verification": {
            "method": "transcription from reference KIF collation + engine check (tools/validate.py)",
            "tool": "tools/kif2open.py + tools/validate.py",
            "checked_date": None,
            "transcribed_by": args.transcriber,
            "transcribed_from": args.transcribed_from or (
                "mechanical transcription of board facts and main-line moves "
                f"from collation-reference KIF ({args.ref_url or 'URL not recorded'}); "
                "original archive scans NOT yet collated"),
            "transcribed_date": "2026-09-15",
            "reference_urls": [args.ref_url] if args.ref_url else [],
            "needs_manual_review": True,
        },
        "source": {
            "title": args.source_title,
            "repository": "国立国会図書館",
            "identifier": args.src_identifier,
            "page": None,
            "url": args.src_url,
            "edition": args.src_edition,
        },
        "rights": {
            "original_work": "Public Domain",
            "dataset_record": "CC0-1.0",
        },
        "features": {},
        "notes": [
            f"参考KIFの申告手数: {declared}手" if declared else "参考KIFの申告手数: 不明",
        ],
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"wrote {args.out}: sfen={sfen} moves={len(usi)}")


if __name__ == "__main__":
    main()
