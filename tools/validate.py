#!/usr/bin/env python3
"""validate.py — Open Tsume record validator (Python stdlib only, MIT).

Checks, per problem JSON:
  1. record fields (mirrors schema/problem.schema.json)
  2. SFEN parse + piece inventory (40-piece set, gote king count)
  3. initial-position rules (gote not in check, no nifu, no dead pieces)
  4. solution: alternating sides, sente moves all check, each USI move
     legal (incl. drops and promotion flags), gote replies resolve check
  5. final position is mate (gote in check, zero legal replies incl.
     interpositions from the box)
  6. provenance fields present (archive identifier or URL)

Usage:
    python3 tools/validate.py collections/edo/zukou/problems/001.json [...]
    python3 tools/validate.py collections/edo/zukou/problems/*.json
Exit code 0 when no errors (warnings allowed); 1 otherwise.
"""
import glob
import json
import re
import sys

STD = {"P": 18, "L": 4, "N": 4, "S": 4, "G": 4, "B": 2, "R": 2, "K": 2}
PROMOTABLE = {"P", "L", "N", "S", "B", "R"}
SFEN_ORDER = ["R", "B", "G", "S", "N", "L", "P"]
USI_MOVE_RE = re.compile(r"^(([1-9][a-i]){2}\+?|[RBGSNLP]\*[1-9][a-i])$")


def opp(c):
    return "w" if c == "b" else "b"


def in_zone(color, rank):
    return rank <= 3 if color == "b" else rank >= 7


def last_ranks(color, kind):
    """Ranks where a piece could never move again (unpromoted)."""
    if color == "b":
        if kind in ("P", "L"):
            return {1}
        if kind == "N":
            return {1, 2}
    else:
        if kind in ("P", "L"):
            return {9}
        if kind == "N":
            return {8, 9}
    return set()


class Board:
    def __init__(self):
        self.sq = {}          # (file,rank) -> [color, kind, promoted]
        self.hand = {"b": {}, "w": {}}
        self.side = "b"

    def clone(self):
        n = Board()
        n.sq = {k: list(v) for k, v in self.sq.items()}
        n.hand = {c: dict(h) for c, h in self.hand.items()}
        n.side = self.side
        return n


def parse_sfen(sfen):
    errors = []
    parts = sfen.split(" ")
    if len(parts) != 4:
        return None, [f"SFEN must have 4 fields: {sfen!r}"]
    bpart, side, hpart, ply = parts
    if side not in ("b", "w"):
        errors.append(f"bad side to move: {side!r}")
    ranks = bpart.split("/")
    if len(ranks) != 9:
        errors.append(f"board part must have 9 ranks: {bpart!r}")
        return None, errors
    bd = Board()
    bd.side = side
    for ri, seg in enumerate(ranks):
        rank = ri + 1
        f = 9
        i = 0
        prom = False
        while i < len(seg):
            c = seg[i]
            if c == "+":
                prom = True
                i += 1
                continue
            if c.isdigit():
                f -= int(c)
                i += 1
                continue
            if c.upper() not in STD:
                errors.append(f"bad piece letter {c!r} in rank {rank}")
                i += 1
                prom = False
                continue
            if f < 1:
                errors.append(f"rank {rank} overflows 9 files")
                break
            color = "b" if c.isupper() else "w"
            bd.sq[(f, rank)] = [color, c.upper(), prom]
            f -= 1
            prom = False
            i += 1
        if f != 0:
            errors.append(f"rank {rank} has {9 - f} squares, want 9")
    if hpart != "-":
        ms = re.findall(r"(\d*)([RBGSNLPrbgsnlp])", hpart)
        joined = "".join(m[0] + m[1] for m in ms)
        if joined != hpart:
            errors.append(f"bad hand part: {hpart!r}")
        for num, ch in ms:
            color = "b" if ch.isupper() else "w"
            bd.hand[color][ch.upper()] = bd.hand[color].get(ch.upper(), 0) + (
                int(num) if num else 1)
    if not ply.isdigit():
        errors.append(f"bad ply: {ply!r}")
    return bd, errors


# ---- move generation -------------------------------------------------

def steps_for(color, kind, prom):
    f = -1 if color == "b" else 1  # forward in ranks
    if kind == "K":
        return [(-1, -1), (0, -1), (1, -1), (-1, 0),
                (1, 0), (-1, 1), (0, 1), (1, 1)], []
    if kind == "G" or prom and kind in ("P", "L", "N", "S"):
        return [(-1, f), (0, f), (1, f), (-1, 0), (1, 0), (0, -f)], []
    if kind == "S":
        d = [(-1, f), (0, f), (1, f), (-1, -f), (1, -f)]
        return (d, []) if not prom else (d, [])
    if kind == "N":
        return [(-1, 2 * f), (1, 2 * f)], []
    if kind == "P":
        return [(0, f)], []
    if kind == "L":
        return [], [(0, f)]
    if kind == "B":
        d = [(-1, -1), (1, -1), (-1, 1), (1, 1)]
        return ([(-1, 0), (1, 0), (0, -1), (0, 1)] if prom else []), d
    if kind == "R":
        o = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        return ([(-1, -1), (1, -1), (-1, 1), (1, 1)] if prom else []), o
    raise ValueError(kind)


def pseudo_targets(bd, frm):
    """All pseudo-legal destinations for the piece on frm (ignores checks)."""
    color, kind, prom = bd.sq[frm]
    f0, r0 = frm
    out = []
    steps, slides = steps_for(color, kind, prom)
    for dx, dy in steps:
        t = (f0 + dx, r0 + dy)
        if 1 <= t[0] <= 9 and 1 <= t[1] <= 9:
            occ = bd.sq.get(t)
            if occ is None or occ[0] != color:
                out.append(t)
    for dx, dy in slides:
        t = (f0 + dx, r0 + dy)
        while 1 <= t[0] <= 9 and 1 <= t[1] <= 9:
            occ = bd.sq.get(t)
            if occ is None:
                out.append(t)
            else:
                if occ[0] != color:
                    out.append(t)
                break
            t = (t[0] + dx, t[1] + dy)
    return out


def find_king(bd, color):
    for sq, p in bd.sq.items():
        if p[0] == color and p[1] == "K":
            return sq
    return None


def is_attacked(bd, sq, by):
    for frm, p in bd.sq.items():
        if p[0] != by:
            continue
        if sq in pseudo_targets(bd, frm):
            return True
    return False


def parse_usi(s):
    if not USI_MOVE_RE.match(s):
        return None, f"bad USI syntax: {s!r}"
    if "*" in s:
        kind = s[0]
        t = (int(s[2]), ord(s[3]) - ord("a") + 1)
        return ("drop", kind, t), None
    f1 = (int(s[0]), ord(s[1]) - ord("a") + 1)
    t = (int(s[2]), ord(s[3]) - ord("a") + 1)
    return ("move", f1, t, s.endswith("+")), None


def file_pawn_count(bd, color, f):
    return sum(1 for (ff, _), p in bd.sq.items()
               if ff == f and p[0] == color and p[1] == "P" and not p[2])


def apply_usi(bd, usi):
    """Apply one USI move for bd.side. Returns error string or None."""
    par, err = parse_usi(usi)
    if err:
        return err
    me = bd.side
    if par[0] == "drop":
        _, kind, t = par
        if kind == "K":
            return "cannot drop a king"
        if bd.hand[me].get(kind, 0) <= 0:
            return f"{me} has no {kind} in hand"
        if t in bd.sq:
            return f"drop target {t} occupied"
        tf, tr = t
        if kind == "P" and file_pawn_count(bd, me, tf):
            return "nifu (two pawns on file)"
        if tr in last_ranks(me, kind):
            return f"dead-square drop {kind} on rank {tr}"
        bd.sq[t] = [me, kind, False]
        bd.hand[me][kind] -= 1
    else:
        _, frm, t, prom = par
        if frm not in bd.sq:
            return f"no piece at {frm}"
        color, kind, already = bd.sq[frm]
        if color != me:
            return f"piece at {frm} belongs to {color}"
        if t not in pseudo_targets(bd, frm):
            return f"pseudo-illegal {usi} for {kind} at {frm}"
        if prom:
            if already:
                return "promote flag on already-promoted piece"
            if kind not in PROMOTABLE:
                return f"{kind} cannot promote"
            ff, fr = frm
            tf, tr = t
            if not (in_zone(me, fr) or in_zone(me, tr)):
                return "promotion outside promotion zone"
        else:
            if kind in ("P", "L", "N") and not already:
                tf, tr = t
                must = ((kind == "P" and tr in last_ranks(me, "P")) or
                        (kind == "L" and tr in last_ranks(me, "L")) or
                        (kind == "N" and tr in last_ranks(me, "N")))
                # NOTE: knight reaching last two ranks may still move
                # (rank 2 for sente); only fully-dead squares force promotion.
                if must:
                    return f"{kind} must promote moving to rank {tr}"
        occ = bd.sq.get(t)
        if occ is not None:
            if occ[0] == me:
                return "cannot capture own piece"
            if occ[1] == "K":
                return "king capture (mate must stop before this)"
            bd.hand[me][occ[1]] = bd.hand[me].get(occ[1], 0) + 1
        del bd.sq[frm]
        bd.sq[t] = [me, kind, already or prom]
    # own king safety
    ksq = find_king(bd, me)
    if ksq is not None and is_attacked(bd, ksq, opp(me)):
        return f"{me} king left in check"
    bd.side = opp(me)
    return None


def is_mate(pos):
    """True when pos.side is checkmated (in check, zero legal replies)."""
    me = pos.side
    ksq = find_king(pos, me)
    if ksq is None or not is_attacked(pos, ksq, opp(me)):
        return False
    return not gen_replies(pos)


def futile_analysis(pos):
    """For each gote reply, test whether an immediate sente recapture on
    the reply square mates (classical futile interposition / 無駄合い).

    Returns (all_futile, details). Informative only: v1 cannot prove
    longer futile sequences, so this never flips solution_verified.
    """
    details = []
    all_futile = True
    for u in gen_replies(pos):
        t = pos.clone()
        if apply_usi(t, u) is not None:
            continue
        # square the reply touched: drop target or move destination
        par, _ = parse_usi(u)
        sq = par[2] if par[0] == "drop" else par[2]
        t.side = "b"
        futile = False
        for s in gen_replies(t):
            spar, _ = parse_usi(s)
            starget = spar[2] if spar[0] == "drop" else spar[2]
            if spar[0] != "drop" and starget == sq:
                u2 = t.clone()
                if apply_usi(u2, s) is None and is_mate(u2):
                    futile = True
                    break
        details.append(f"{u}: {'futile' if futile else 'escapes'}")
        if not futile:
            all_futile = False
    return all_futile, details


def box_for(bd, color):
    """Remaining pieces available to `color` for drops (the box)."""
    rem = {}
    on_board = {}
    for p in bd.sq.values():
        on_board[p[1]] = on_board.get(p[1], 0) + 1
    hand = bd.hand[color]
    for k, total in STD.items():
        if k == "K":
            continue
        left = total - on_board.get(k, 0) - bd.hand[opp(color)].get(k, 0)
        have = hand.get(k, 0)
        # In tsume SFEN the defender hand should equal the remainder.
        rem[k] = max(have, left) if color == "w" else have
    return rem


def gen_replies(bd):
    """All legal moves for bd.side. Returns list of USI strings."""
    me = bd.side
    out = []
    for frm, (color, kind, prom) in list(bd.sq.items()):
        if color != me:
            continue
        for t in pseudo_targets(bd, frm):
            cands = [False]
            if (not prom and kind in PROMOTABLE and
                    (in_zone(me, frm[1]) or in_zone(me, t[1]))):
                cands.append(True)
            for pr in cands:
                if not pr and kind in ("P", "L", "N") and not prom:
                    if t[1] in last_ranks(me, kind):
                        continue
                trial = bd.clone()
                usi = (f"{frm[0]}{chr(ord('a') + frm[1] - 1)}"
                       f"{t[0]}{chr(ord('a') + t[1] - 1)}"
                       f"{'+' if pr else ''}")
                if apply_usi(trial, usi) is None:
                    out.append(usi)
    box = box_for(bd, me)
    empties = [(f, r) for f in range(1, 10) for r in range(1, 10)
               if (f, r) not in bd.sq]
    for kind, n in box.items():
        if n <= 0:
            continue
        for t in empties:
            if t[1] in last_ranks(me, kind):
                continue
            if kind == "P" and file_pawn_count(bd, me, t[0]):
                continue
            trial = bd.clone()
            trial.hand[me][kind] = trial.hand[me].get(kind, 0) + 1 \
                if trial.hand[me].get(kind, 0) < n else n
            usi = f"{kind}*{t[0]}{chr(ord('a') + t[1] - 1)}"
            if apply_usi(trial, usi) is None:
                out.append(usi)
    return out


# ---- record validation ------------------------------------------------

def validate_record(rec):
    errors, warnings = [], []

    def err(m):
        errors.append(m)

    def warn(m):
        warnings.append(m)

    for f in ("id", "collection_id", "number", "author", "published_year",
              "period", "sfen", "solution_usi", "solution_moves",
              "status", "verification", "source", "rights"):
        if f not in rec:
            err(f"missing field: {f}")
    if errors:
        return errors, warnings
    if not re.match(r"^[a-z]+-[0-9]{3}$", rec["id"]):
        err(f"bad id: {rec['id']}")
    if rec["id"] != f"{rec['collection_id']}-{rec['number']:03d}":
        err("id/collection_id/number inconsistent")
    usi = rec["solution_usi"]
    if not isinstance(usi, list) or not usi:
        err("solution_usi must be a non-empty list")
        return errors, warnings
    if rec["solution_moves"] != len(usi):
        err("solution_moves != len(solution_usi)")
    if len(usi) % 2 == 0:
        err("solution length must be odd (sente mates)")
    for m in usi:
        if not USI_MOVE_RE.match(m):
            err(f"bad USI syntax in solution: {m!r}")
    st = rec["status"]
    for k in ("position_verified", "solution_verified",
              "unique_solution_verified"):
        if k not in st:
            err(f"status.{k} missing")
    if rec["rights"].get("original_work") != "Public Domain":
        err("rights.original_work must be 'Public Domain'")
    if rec["rights"].get("dataset_record") != "CC0-1.0":
        err("rights.dataset_record must be 'CC0-1.0'")
    src = rec["source"]
    if not src.get("identifier") and not src.get("url"):
        err("provenance: source needs identifier or url")
    if rec["verification"].get("needs_manual_review"):
        warn("needs_manual_review: not yet collated against original scans")

    bd, serrs = parse_sfen(rec["sfen"])
    errors.extend("SFEN: " + e for e in serrs)
    if bd is None:
        return errors, warnings
    if bd.side != "b":
        err("SFEN side to move must be b (attacker first)")

    # inventory
    counts = {}
    for p in bd.sq.values():
        counts[p[1]] = counts.get(p[1], 0) + 1
    for c in ("b", "w"):
        for k, n in bd.hand[c].items():
            counts[k] = counts.get(k, 0) + n
    for k, n in counts.items():
        if n > STD.get(k, 0):
            err(f"inventory overflow: {k} x{n} > {STD.get(k, 0)}")
    kings_w = sum(1 for p in bd.sq.values() if p == ["w", "K", False])
    kings_b = sum(1 for p in bd.sq.values() if p[0] == "b" and p[1] == "K")
    if kings_w != 1:
        err(f"gote king count = {kings_w}, want 1")
    if kings_b > 1:
        err("more than one sente king")
    # box cross-check for the defender
    if kings_w == 1:
        on_board = {}
        for p in bd.sq.values():
            on_board[p[1]] = on_board.get(p[1], 0) + 1
        for k in SFEN_ORDER:
            expect = STD[k] - on_board.get(k, 0) - bd.hand["b"].get(k, 0)
            got = bd.hand["w"].get(k, 0)
            if got != expect:
                warn(f"gote hand {k}: SFEN has {got}, box recompute says "
                     f"{expect} (transcription of defender box differs)")
    # initial rules
    if kings_w == 1:
        ksq = find_king(bd, "w")
        if is_attacked(bd, ksq, "b"):
            err("initial position: gote king already in check")
    for color in ("b", "w"):
        for f in range(1, 10):
            if file_pawn_count(bd, color, f) > 1:
                err(f"initial nifu: {color} pawns x2 on file {f}")
    for sq, (color, kind, prom) in bd.sq.items():
        if not prom and sq[1] in last_ranks(color, kind):
            err(f"dead piece {kind} at {sq}")
    if errors:
        return errors, warnings

    # solution walk
    pos = bd.clone()
    for i, m in enumerate(usi):
        mover = pos.side
        expect = "b" if i % 2 == 0 else "w"
        if mover != expect:
            err(f"move {i + 1}: side {mover} to move, want {expect}")
            break
        e = apply_usi(pos, m)
        if e:
            err(f"move {i + 1} ({m}): illegal: {e}")
            break
        ksq = find_king(pos, "w")
        if ksq is None:
            err(f"move {i + 1}: gote king vanished")
            break
        if mover == "b":
            if not is_attacked(pos, ksq, "b"):
                err(f"move {i + 1} ({m}): sente move gives no check")
                break
        else:
            if is_attacked(pos, ksq, "b"):
                err(f"move {i + 1} ({m}): gote still in check")
                break
    else:
        # completed without break: mate test
        if pos.side != "w":
            err("final side to move is not gote")
        else:
            ksq = find_king(pos, "w")
            if not is_attacked(pos, ksq, "b"):
                err("final position: gote king not in check")
            else:
                replies = gen_replies(pos)
                if not replies:
                    if not rec["status"].get("solution_verified"):
                        warn("engine proves mate; status.solution_verified "
                             "is false (update the flag if this is intended)")
                else:
                    all_futile, details = futile_analysis(pos)
                    for d in details:
                        warn(f"reply: {d}")
                    if all_futile and replies:
                        warn("all gote replies look like futile "
                             "interpositions (mudaai): immediate recapture "
                             "mates. Needs solver confirmation; "
                             "solution_verified must stay false in v1.")
                    if rec["status"].get("solution_verified"):
                        err(f"not mate: gote has {len(replies)} replies, "
                            f"e.g. {replies[:5]}")
                    else:
                        warn(f"final mate unproven ({len(replies)} gote "
                             f"replies); solution_verified=false recorded")
    return errors, warnings


def validate_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            rec = json.load(f)
    except Exception as e:
        return [f"cannot load JSON: {e}"], []
    return validate_record(rec)


def main(paths):
    if not paths:
        print("usage: validate.py <problem.json> [...]", file=sys.stderr)
        return 2
    files = []
    for p in paths:
        files.extend(glob.glob(p) if any(c in p for c in "*?[") else [p])
    failed = 0
    for path in sorted(files):
        errors, warnings = validate_file(path)
        tag = "OK " if not errors else "FAIL"
        print(f"[{tag}] {path}")
        for w in warnings:
            print(f"    warn: {w}")
        for e in errors:
            print(f"    ERROR: {e}")
        if errors:
            failed += 1
    print(f"{len(files) - failed}/{len(files)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
