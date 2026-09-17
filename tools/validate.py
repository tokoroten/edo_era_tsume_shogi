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

Also checks, per collection JSON (mirrors schema/collection.schema.json):
  - required top-level keys present
  - source.digital is an object (plain-string form rejected)

Usage:
    python3 tools/validate.py collections/edo/zukou/problems/001.json [...]
    python3 tools/validate.py collections/edo/zukou/problems/*.json
    python3 tools/validate.py collections/*/*/collection.json

    Draft (staging) mode — incomplete records under drafts/ only:
    python3 tools/validate.py --draft [collections/edo/<id>/drafts/*.json]
    (no paths = auto-discover collections/*/*/drafts/*.json)
    Relaxed: sfen may contain '?' (untranscribed squares),
    solution_usi may be [] with solution_moves 0 (unsolved).
    Remaining gaps are printed as `gap:` lines. Exit code 0 when
    no errors (gaps/warnings allowed); 1 otherwise.
    Strict (default) mode never accepts drafts/ files and is unchanged.
Exit code 0 when no errors (warnings allowed); 1 otherwise.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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

    Returns (all_futile, details). Alone it never flips
    solution_verified; combined with exhaustive_mate_in_1 (all_mate)
    it constitutes promotion-grade evidence (see validate_record).
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


def exhaustive_mate_in_1(pos):
    """For each gote reply, test whether sente has any mating reply
    (mate-in-1, typically an immediate recapture / 取り返し詰み).

    Returns (all_mate, details). This is the promotion-grade check:
    combined with futile_analysis (all_futile), an all_mate result
    constitutes mechanical evidence that the final position is
    exhaustively mated within one recapture, and may support
    status.solution_verified=true.
    """
    details = []
    all_mate = True
    for u in gen_replies(pos):
        t = pos.clone()
        if apply_usi(t, u) is not None:
            continue
        t.side = "b"
        mate_move = None
        for s in gen_replies(t):
            u2 = t.clone()
            if apply_usi(u2, s) is None and is_mate(u2):
                mate_move = s
                break
        if mate_move is None:
            all_mate = False
            details.append(f"{u}: no mate-in-1")
        else:
            details.append(f"{u}: mate-in-1 with {mate_move}")
    return all_mate, details


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
                    all_mate, mate_details = exhaustive_mate_in_1(pos)
                    verified = bool(rec["status"].get("solution_verified"))
                    if all_futile and all_mate and replies:
                        # Promotion-grade evidence: every gote reply is a
                        # futile interposition AND allows an immediate
                        # sente mate-in-1 (recapture / 取り返し詰み),
                        # confirmed exhaustively via gen_replies.
                        if verified:
                            pass
                        else:
                            warn("exhaustive mate-in-1 proven for all "
                                 f"{len(replies)} gote replies "
                                 "(futile_analysis all_futile + gen_replies "
                                 "mate-in-1 confirmed, e.g. "
                                 f"{mate_details[:5]}); "
                                 "status.solution_verified is false (update "
                                 "the flag if this is intended)")
                    else:
                        for d in details:
                            warn(f"reply: {d}")
                        if all_futile and replies:
                            warn("all gote replies look like futile "
                                 "interpositions (mudaai): immediate recapture "
                                 "mates. Needs solver confirmation; "
                                 "solution_verified must stay false in v1.")
                        if verified:
                            err(f"not mate: gote has {len(replies)} replies, "
                                f"e.g. {replies[:5]}")
                        else:
                            warn(f"final mate unproven ({len(replies)} gote "
                                 "replies); solution_verified=false recorded")
    # intended solution (historical line; solver canonical stays in
    # solution_usi above and is unchanged). Only legality + count.
    _validate_intended_solution(rec, bd, err, warn)
    return errors, warnings


def _validate_intended_solution(rec, bd, err, warn):
    """Validate historical intended-solution fields when present.

    - intended_solution_usi: null/absent = not yet transcribed (skip).
      When present: must be a non-empty list of USI strings and each
      move must be legally playable from the initial SFEN in order.
      Continuous-check / final-mate are NOT required here because old
      records may contain an incorrect line.
    - intended_solution_moves: null/absent = unknown (skip). When both
      usi and moves are present, they must agree.
    - intended_solution_source: null/absent or string.
    - status.intended_solution_verified: absent = unverified (false);
      when present must be bool.
    """
    iusi = rec.get("intended_solution_usi", None)
    imoves = rec.get("intended_solution_moves", None)
    isrc = rec.get("intended_solution_source", None)

    st = rec.get("status", {})
    if "intended_solution_verified" in st and \
            not isinstance(st["intended_solution_verified"], bool):
        err("status.intended_solution_verified must be a boolean")

    if isrc is not None and not isinstance(isrc, str):
        err("intended_solution_source must be a string or null")

    if iusi is None:
        if imoves is not None:
            err("intended_solution_moves present without "
                "intended_solution_usi")
        if st.get("intended_solution_verified") is True:
            err("status.intended_solution_verified is true without "
                "intended_solution_usi")
        return

    if not isinstance(iusi, list) or not iusi:
        err("intended_solution_usi must be a non-empty list or null")
        return
    for m in iusi:
        if not isinstance(m, str) or not USI_MOVE_RE.match(m):
            err(f"bad USI syntax in intended_solution: {m!r}")

    if imoves is None:
        warn("intended_solution_usi present without "
             "intended_solution_moves")
    else:
        if not isinstance(imoves, int) or isinstance(imoves, bool) or \
                imoves < 1:
            err("intended_solution_moves must be an integer >= 1 or null")
        elif imoves != len(iusi):
            err("intended_solution_moves != len(intended_solution_usi)")

    if bd is None:
        return
    pos = bd.clone()
    for i, m in enumerate(iusi):
        if not isinstance(m, str) or not USI_MOVE_RE.match(m):
            break
        e = apply_usi(pos, m)
        if e:
            err(f"intended move {i + 1} ({m}): illegal: {e}")
            break


# ---- draft (staging) validation -----------------------------------------

DRAFT_REQUIRED = ("id", "collection_id", "number", "author", "published_year",
                  "period", "sfen", "solution_usi", "solution_moves",
                  "status", "verification", "source", "rights")


def is_draft_path(path):
    """True when path points under a drafts/ staging directory."""
    return "/drafts/" in path.replace("\\", "/")


def validate_draft_record(rec):
    """Relaxed validator for staging records (drafts/ only).

    Relaxed vs strict (validate_record):
      - sfen may contain '?' (untranscribed squares).
      - solution_usi may be [] with solution_moves 0 (unsolved).
    Returns (errors, warnings, gaps):
      - errors: must be fixed (bad id, broken SFEN structure, bad USI
        syntax, provenance/rights failures, ...).
      - warnings: same meaning as strict (e.g. needs_manual_review).
      - gaps: explicit list of unfinished items ('?' count, empty
        solution, skipped board/solution-walk checks).
    A complete draft (no '?' and non-empty solution) is delegated to
    validate_record so promotion to problems/ is a pure move.
    Schema files (problem.schema.json) are unchanged; drafts are
    intentionally schema-invalid until '?'/empty-solution are resolved.
    """
    errors, warnings, gaps = [], [], []

    def err(m):
        errors.append(m)

    def warn(m):
        warnings.append(m)

    def gap(m):
        gaps.append(m)

    if not isinstance(rec, dict):
        return ["draft record must be an object"], warnings, gaps
    for f in DRAFT_REQUIRED:
        if f not in rec:
            err(f"missing field: {f}")
    if errors:
        return errors, warnings, gaps

    sfen = rec.get("sfen")
    usi = rec.get("solution_usi")
    has_q = isinstance(sfen, str) and "?" in sfen
    empty_sol = isinstance(usi, list) and len(usi) == 0

    if not has_q and not empty_sol:
        # Complete: strict equivalence, no gaps.
        serrs, swarns = validate_record(rec)
        return serrs, swarns, []

    # ---- header checks (relaxed) ----
    if not re.match(r"^[a-z]+-[0-9]{3}$", str(rec.get("id", ""))):
        err(f"bad id: {rec.get('id')}")
    try:
        want = f"{rec['collection_id']}-{rec['number']:03d}"
        if rec["id"] != want:
            err("id/collection_id/number inconsistent")
    except Exception:
        err("id/collection_id/number inconsistent")
    st = rec.get("status", {})
    if not isinstance(st, dict):
        err("status must be an object")
    else:
        for k in ("position_verified", "solution_verified",
                  "unique_solution_verified"):
            if k not in st:
                err(f"status.{k} missing")
    rights = rec.get("rights", {})
    if not isinstance(rights, dict):
        err("rights must be an object")
    else:
        if rights.get("original_work") != "Public Domain":
            err("rights.original_work must be 'Public Domain'")
        if rights.get("dataset_record") != "CC0-1.0":
            err("rights.dataset_record must be 'CC0-1.0'")
    src = rec.get("source", {})
    if not isinstance(src, dict):
        err("source must be an object")
    elif not src.get("identifier") and not src.get("url"):
        err("provenance: source needs identifier or url")
    ver = rec.get("verification", {})
    if isinstance(ver, dict) and ver.get("needs_manual_review"):
        warn("needs_manual_review: not yet collated against original scans")

    # ---- sfen (relaxed) ----
    bd = None
    if not isinstance(sfen, str) or not sfen:
        err("sfen must be a non-empty string")
    else:
        if has_q:
            gap(f"sfen has {sfen.count('?')} '?' "
                f"(untranscribed squares)")
        sanitized = sfen.replace("?", "1")
        parsed, serrs = parse_sfen(sanitized)
        for e in serrs:
            err("SFEN: " + e)
        if parsed is not None and parsed.side != "b":
            err("SFEN side to move must be b (attacker first)")
        if has_q:
            gap("board-dependent checks skipped "
                "(sfen incomplete: ? remains)")
            bd = None
        else:
            bd = parsed

    # ---- solution_usi (relaxed) ----
    moves = rec.get("solution_moves")
    if not isinstance(usi, list):
        err("solution_usi must be a list (empty allowed in draft)")
    elif len(usi) == 0:
        gap("solution_usi empty (unsolved)")
        if moves != 0:
            err("solution_moves must be 0 when solution_usi "
                "is empty (draft)")
        gap("solution walk skipped (solution empty)")
    else:
        if moves != len(usi):
            err("solution_moves != len(solution_usi)")
        for m in usi:
            if not isinstance(m, str) or not USI_MOVE_RE.match(m):
                err(f"bad USI syntax in solution: {m!r}")
        if has_q:
            gap("solution walk skipped (sfen incomplete: ? remains)")
        # NOTE: parity (odd length) and legality/mate walk are strict-only;
        # partial draft lines may be even-length prefixes, so they are
        # reported as gaps here and enforced on promotion via
        # validate_record.

    # ---- intended solution: syntax/count only while board incomplete ----
    _validate_intended_solution(rec, bd, err, warn)
    return errors, warnings, gaps


def validate_draft_file(path):
    """Load + draft-validate one file. Returns (errors, warnings, gaps)."""
    try:
        with open(path, encoding="utf-8") as f:
            rec = json.load(f)
    except Exception as e:
        return [f"cannot load JSON: {e}"], [], []
    norm = path.replace("\\", "/")
    if norm.endswith("collection.json"):
        return ["draft mode targets problem drafts only, "
                "not collection.json"], [], []
    if not is_draft_path(path):
        return ["not under drafts/ (--draft only targets drafts/)"], [], []
    if isinstance(rec, dict) and "collection_id" in rec and "id" not in rec:
        return ["draft mode targets problem drafts only, "
                "not collection records"], [], []
    return validate_draft_record(rec)


# ---- collection validation ----------------------------------------------

COLLECTION_REQUIRED = (
    "collection_id", "title", "author", "published_year", "period",
    "problem_count", "problems_transcribed", "source", "rights",
)
COLLECTION_ID_RE = re.compile(r"^[a-z]+$")


def validate_collection(rec):
    """Simplified collection check (stdlib only, no jsonschema).

    Mirrors schema/collection.schema.json: required top-level keys and
    source.digital must be an object (regression guard against the old
    plain-string form).
    """
    errors, warnings = [], []

    if not isinstance(rec, dict):
        return ["collection record must be an object"], warnings
    for f in COLLECTION_REQUIRED:
        if f not in rec:
            errors.append(f"missing field: {f}")
    if errors:
        return errors, warnings
    if not isinstance(rec["collection_id"], str) or \
            not COLLECTION_ID_RE.match(rec["collection_id"]):
        errors.append(f"bad collection_id: {rec['collection_id']!r}")
    if rec["period"] != "Edo":
        errors.append(f"period must be 'Edo': {rec['period']!r}")
    if not isinstance(rec["published_year"], int):
        errors.append("published_year must be an integer")
    if not isinstance(rec["problem_count"], int) or rec["problem_count"] < 1:
        errors.append("problem_count must be an integer >= 1")
    pts = rec["problems_transcribed"]
    if not isinstance(pts, list):
        errors.append("problems_transcribed must be a list")
    elif len(pts) == 0:
        warnings.append("problems_transcribed is empty "
                        "(scaffold: transcription not yet started)")
    else:
        if any(not isinstance(n, int) or n < 1 for n in pts):
            errors.append("problems_transcribed items must be integers >= 1")
        if len(set(pts)) != len(pts):
            errors.append("problems_transcribed must have unique items")
    rights = rec["rights"]
    if not isinstance(rights, dict):
        errors.append("rights must be an object")
    else:
        if rights.get("original_work") != "Public Domain":
            errors.append("rights.original_work must be 'Public Domain'")
        if rights.get("dataset_record") != "CC0-1.0":
            errors.append("rights.dataset_record must be 'CC0-1.0'")
    src = rec["source"]
    if not isinstance(src, dict):
        errors.append("source must be an object")
    else:
        for f in ("title", "repository", "digital"):
            if f not in src:
                errors.append(f"source.{f} missing")
        if "digital" in src and not isinstance(src["digital"], dict):
            errors.append("source.digital must be an object "
                          "(plain-string form rejected)")
    return errors, warnings


def validate_file(path, draft=False):
    """Validate one file.

    Strict (draft=False, default): unchanged; drafts/ files are rejected
    with an explicit error so production data and draft staging never mix.
    Returns (errors, warnings).
    Draft (draft=True): only files under drafts/ are accepted; relaxed
    checks apply. Returns (errors, warnings, gaps).
    """
    if draft:
        return validate_draft_file(path)
    if is_draft_path(path):
        return [f"draft file requires --draft: {path}"], []
    try:
        with open(path, encoding="utf-8") as f:
            rec = json.load(f)
    except Exception as e:
        return [f"cannot load JSON: {e}"], []
    is_collection_path = path.replace("\\", "/").endswith("collection.json")
    is_collection_body = (isinstance(rec, dict)
                          and "collection_id" in rec and "id" not in rec)
    if is_collection_path or is_collection_body:
        return validate_collection(rec)
    return validate_record(rec)


def expand_paths(paths):
    files = []
    for p in paths:
        files.extend(glob.glob(p) if any(c in p for c in "*?[") else [p])
    return sorted(files)


def main(paths, draft=False):
    if draft:
        if not paths:
            paths = [os.path.join(ROOT, "collections", "*", "*",
                                  "drafts", "*.json")]
        files = expand_paths(paths)
        if not files:
            print("no draft files found")
            return 0
        failed = 0
        for path in files:
            errors, warnings, gaps = validate_file(path, draft=True)
            tag = "OK " if not errors else "FAIL"
            print(f"[{tag}] {path}")
            for g in gaps:
                print(f"    gap: {g}")
            for w in warnings:
                print(f"    warn: {w}")
            for e in errors:
                print(f"    ERROR: {e}")
            if errors:
                failed += 1
        print(f"{len(files) - failed}/{len(files)} drafts passed "
              f"(gaps allowed)")
        return 1 if failed else 0
    if not paths:
        print("usage: validate.py <problem.json> [...] "
              "or: validate.py --draft [drafts/*.json]", file=sys.stderr)
        return 2
    files = expand_paths(paths)
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
    _args = sys.argv[1:]
    _draft = "--draft" in _args
    _paths = [a for a in _args if a != "--draft"]
    sys.exit(main(_paths, draft=_draft))
