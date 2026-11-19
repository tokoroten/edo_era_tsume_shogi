#!/usr/bin/env python3
"""run_tests.py — unittest suite for Open Tsume (stdlib only, MIT).

- Every problem JSON under collections/ passes tools/validate.py.
- Spot checks: zukou-002 solution length/parity and known final move.
- Schema file is valid JSON and every record carries required top keys.
"""
import glob
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import validate  # noqa: E402


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def all_problems():
    return sorted(glob.glob(
        os.path.join(ROOT, "collections", "*", "*", "problems", "*.json")))


def all_collections():
    return sorted(glob.glob(
        os.path.join(ROOT, "collections", "*", "*", "collection.json")))


class TestDataset(unittest.TestCase):
    def test_problems_exist(self):
        self.assertTrue(all_problems(), "no problem files found")

    def test_all_records_validate(self):
        bad = []
        for p in all_problems():
            errors, _ = validate.validate_file(p)
            if errors:
                bad.append((p, errors))
        self.assertEqual(bad, [], f"validation failures: {bad}")

    def test_schema_file_valid(self):
        sp = os.path.join(ROOT, "schema", "problem.schema.json")
        schema = load_json(sp)
        self.assertEqual(schema["type"], "object")
        self.assertIn("sfen", schema["properties"])

    def test_zukou002_spotcheck(self):
        p = os.path.join(ROOT, "collections", "edo", "zukou",
                         "problems", "002.json")
        rec = load_json(p)
        self.assertEqual(rec["id"], "zukou-002")
        self.assertEqual(rec["solution_moves"], 21)
        self.assertEqual(len(rec["solution_usi"]), 21)
        self.assertTrue(rec["sfen"].split(" ")[1] == "b")
        self.assertTrue(rec["verification"]["needs_manual_review"])

    def test_collection_consistency(self):
        for cpath in glob.glob(os.path.join(
                ROOT, "collections", "*", "*", "collection.json")):
            cid = load_json(cpath)["collection_id"]
            nums = sorted(load_json(p)["number"]
                          for p in all_problems()
                          if f"/{cid}/problems/" in p.replace(os.sep, "/"))
            self.assertEqual(sorted(load_json(cpath)["problems_transcribed"]),
                             nums, f"collection {cid} mismatch")

    def test_collection_schema_valid(self):
        cpaths = all_collections()
        self.assertTrue(cpaths, "no collection.json files found")
        schema = load_json(
            os.path.join(ROOT, "schema", "collection.schema.json"))
        self.assertEqual(schema["type"], "object")
        self.assertIn("collection_id", schema["required"])
        self.assertIn("digital", schema["properties"]["source"]["properties"])
        bad = []
        for cpath in cpaths:
            rec = load_json(cpath)
            for key in schema["required"]:
                if key not in rec:
                    bad.append((cpath, f"missing field: {key}"))
            if not isinstance(rec.get("source", {}).get("digital"), dict):
                bad.append((cpath, "source.digital must be an object"))
            errors, _ = validate.validate_collection(rec)
            if errors:
                bad.append((cpath, errors))
            ferrs, _ = validate.validate_file(cpath)
            if ferrs:
                bad.append((cpath + " via validate_file", ferrs))
        self.assertEqual(bad, [], f"collection schema failures: {bad}")

    def test_intended_solution_fields(self):
        schema = load_json(
            os.path.join(ROOT, "schema", "problem.schema.json"))
        for key in ("intended_solution_usi", "intended_solution_moves",
                    "intended_solution_source"):
            self.assertIn(key, schema["properties"],
                          f"schema missing {key}")
        self.assertIn("intended_solution_verified",
                      schema["properties"]["status"]["properties"],
                      "schema status missing intended_solution_verified")
        bad = []
        for p in all_problems():
            rec = load_json(p)
            iusi = rec.get("intended_solution_usi", None)
            imoves = rec.get("intended_solution_moves", None)
            isrc = rec.get("intended_solution_source", None)
            if iusi is None and imoves is None and isrc is None:
                flag = rec.get("status", {}).get(
                    "intended_solution_verified", False)
                if flag is not False:
                    bad.append((p, "untranscribed but flag is not false"))
                continue
            if iusi is not None:
                if not isinstance(iusi, list) or not iusi:
                    bad.append((p, "intended_solution_usi not non-empty"))
                    continue
                for m in iusi:
                    if not validate.USI_MOVE_RE.match(m):
                        bad.append((p, f"bad intended USI: {m!r}"))
                if imoves is not None and imoves != len(iusi):
                    bad.append((p, "intended_solution_moves != "
                                   "len(intended_solution_usi)"))
                bd, serrs = validate.parse_sfen(rec["sfen"])
                if serrs or bd is None:
                    bad.append((p, f"SFEN unusable for replay: {serrs}"))
                    continue
                pos = bd.clone()
                for i, m in enumerate(iusi):
                    e = validate.apply_usi(pos, m)
                    if e:
                        bad.append(
                            (p, f"intended move {i + 1} ({m}) illegal: {e}"))
                        break
            if isrc is not None and not isinstance(isrc, str):
                bad.append((p, "intended_solution_source not str/null"))
        self.assertEqual(bad, [], f"intended solution failures: {bad}")


def make_draft_record(**over):
    rec = {
        "id": "gyokuzu-001",
        "collection_id": "gyokuzu",
        "number": 1,
        "author": "桑原君仲",
        "published_year": 1836,
        "period": "Edo",
        "sfen": "?8/9/9/9/9/4k4/9/9/9 b - 1",
        "solution_usi": [],
        "solution_moves": 0,
        "status": {
            "position_verified": False,
            "solution_verified": False,
            "unique_solution_verified": False,
        },
        "verification": {
            "method": "draft transcription in progress",
            "tool": "tools/validate.py --draft",
            "checked_date": None,
            "transcribed_by": None,
            "transcribed_from": None,
            "transcribed_date": None,
            "reference_urls": [],
            "needs_manual_review": True,
        },
        "source": {
            "title": "将棋玉図・将棋玉図詰手",
            "repository": "国立国会図書館",
            "identifier": "NDLBibID:000000493916 / 請求記号:209-462",
            "page": None,
            "url": "https://ndlsearch.ndl.go.jp/books/R100000002-I000000493916",
            "edition": None,
        },
        "rights": {
            "original_work": "Public Domain",
            "dataset_record": "CC0-1.0",
        },
        "notes": ["draft staging fixture (temporary data only)"],
    }
    rec.update(over)
    return rec


def write_temp_draft(tmpdir, rec, name="001.json"):
    ddir = os.path.join(tmpdir, "drafts")
    os.makedirs(ddir, exist_ok=True)
    path = os.path.join(ddir, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    return path


class TestDraft(unittest.TestCase):
    def test_draft_allows_question_and_empty_solution(self):
        rec = make_draft_record()
        errors, warnings, gaps = validate.validate_draft_record(rec)
        self.assertEqual(errors, [])
        self.assertTrue(any("'?' " in g or "'?'" in g for g in gaps),
                        f"expected sfen gap, got: {gaps}")
        self.assertTrue(any("solution_usi empty" in g for g in gaps),
                        f"expected solution gap, got: {gaps}")

    def test_draft_file_roundtrip_temp(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_temp_draft(tmp, make_draft_record())
            errors, warnings, gaps = validate.validate_file(
                path, draft=True)
            self.assertEqual(errors, [])
            self.assertTrue(gaps)
            # strict mode must refuse drafts/ files explicitly
            serrs, _ = validate.validate_file(path)
            self.assertTrue(serrs)
            self.assertTrue(any("--draft" in e for e in serrs))

    def test_strict_still_rejects_question_and_empty(self):
        rec = make_draft_record()
        errors, _ = validate.validate_record(rec)
        self.assertTrue(errors, "strict must reject '?' sfen/empty solution")

    def test_draft_rejects_bad_id(self):
        rec = make_draft_record(id="BAD-ID")
        errors, _, _ = validate.validate_draft_record(rec)
        self.assertTrue(errors)
        self.assertTrue(any("bad id" in e for e in errors))

    def test_draft_rejects_non_draft_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            ppath = os.path.join(tmp, "problems", "001.json")
            os.makedirs(os.path.dirname(ppath), exist_ok=True)
            with open(ppath, "w", encoding="utf-8") as f:
                json.dump(make_draft_record(), f)
            errors, _, _ = validate.validate_file(ppath, draft=True)
            self.assertTrue(errors)
            self.assertTrue(any("drafts/" in e for e in errors))

    def test_draft_complete_delegates_to_strict(self):
        src = os.path.join(ROOT, "collections", "edo", "zukou",
                           "problems", "002.json")
        rec = load_json(src)
        with tempfile.TemporaryDirectory() as tmp:
            path = write_temp_draft(tmp, rec, name="002.json")
            d_errors, _, d_gaps = validate.validate_file(
                path, draft=True)
            s_errors, _ = validate.validate_record(rec)
            self.assertEqual(d_errors, s_errors)
            if not s_errors:
                self.assertEqual(d_gaps, [])

    def test_draft_flags_illegal_position(self):
        rec = make_draft_record(
            sfen="1B1S2R2/3PgLP+P1/8P/2Pk+PP3/1S4+Pg1/1P1L1S2N/5N3/8L/9 b B2GS 1")
        errors, _, gaps = validate.validate_draft_record(rec)
        self.assertEqual(errors, [])
        self.assertTrue(any("illegal position" in g for g in gaps),
                        f"expected illegal-position gap, got: {gaps}")
        ok = make_draft_record(
            sfen="4k4/9/9/9/9/9/9/9/9 b RBGSN 1")
        _, _, gaps2 = validate.validate_draft_record(ok)
        self.assertFalse(any("illegal position" in g for g in gaps2),
                         f"unexpected illegal-position gap: {gaps2}")

    def test_draft_empty_glob_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc = validate.main(
                [os.path.join(tmp, "drafts", "*.json")], draft=True)
            self.assertEqual(rc, 0)

    def test_no_drafts_in_strict_suite(self):
        probs = all_problems()
        self.assertTrue(probs)
        leaked = [p for p in probs
                  if "/drafts/" in p.replace(os.sep, "/")]
        self.assertEqual(leaked, [])
        # build_web source glob must also exclude drafts/
        import build_web  # noqa: E402
        web_src = sorted(glob.glob(os.path.join(
            ROOT, "collections", "*", "*", "problems", "*.json")))
        leaked_web = [p for p in web_src
                      if "/drafts/" in p.replace(os.sep, "/")]
        self.assertEqual(leaked_web, [])


def make_procedure_record(n_plies=3, **over):
    moves = []
    for i in range(1, n_plies + 1):
        moves.append({
            "col": "S1", "n": i,
            "piece": "R" if i % 2 else "K",
            "dest": "same" if i > 1 else "89",
            "marker": "-",
        })
    rec = {
        "collection_id": "seimyo",
        "pid": "861217",
        "leaf": "R0000002",
        "covers_problems": [1],
        "transcription": {"method": "test", "verified": True},
        "moves": moves,
    }
    rec.update(over)
    return rec


class TestProcedure(unittest.TestCase):
    def test_odd_plies_ok(self):
        errors, warnings, gaps = validate.validate_procedure_record(
            make_procedure_record(3))
        self.assertEqual(errors, [])
        self.assertFalse(any("even" in g for g in gaps), gaps)

    def test_even_plies_reported(self):
        _, _, gaps = validate.validate_procedure_record(
            make_procedure_record(4))
        self.assertTrue(any("even" in g for g in gaps), gaps)

    def test_first_move_cannot_be_same(self):
        rec = make_procedure_record(3)
        rec["moves"][0]["dest"] = "same"
        errors, _, _ = validate.validate_procedure_record(rec)
        self.assertTrue(any("cannot be 'same'" in e for e in errors), errors)

    def test_bad_marker_and_piece(self):
        rec = make_procedure_record(3)
        rec["moves"][0]["marker"] = "x"
        rec["moves"][1]["piece"] = "W"
        errors, _, _ = validate.validate_procedure_record(rec)
        self.assertTrue(any("bad marker" in e for e in errors), errors)
        self.assertTrue(any("bad piece" in e for e in errors), errors)

    def test_move_numbers_must_be_sequential(self):
        rec = make_procedure_record(3)
        rec["moves"][2]["n"] = 5
        errors, _, _ = validate.validate_procedure_record(rec)
        self.assertTrue(any("must run 1..N" in e for e in errors), errors)

    def test_draft_flags_piece_budget(self):
        rec = make_draft_record(
            sfen="4k4/9/9/9/GGGGG4/9/9/9/9 b - 1")
        errors, _, gaps = validate.validate_draft_record(rec)
        self.assertEqual(errors, [])
        self.assertTrue(any("piece budget" in g for g in gaps), gaps)

    def test_draft_flags_dead_piece(self):
        rec = make_draft_record(
            sfen="P3k4/9/9/9/9/9/9/9/9 b - 1")
        errors, _, gaps = validate.validate_draft_record(rec)
        self.assertEqual(errors, [])
        self.assertTrue(any("dead piece" in g for g in gaps), gaps)

    def test_draft_flags_nifu(self):
        rec = make_draft_record(
            sfen="4k4/9/9/9/P8/P8/9/9/9 b - 1")
        errors, _, gaps = validate.validate_draft_record(rec)
        self.assertEqual(errors, [])
        self.assertTrue(any("nifu" in g for g in gaps), gaps)
        ok = make_draft_record(
            sfen="4k4/9/9/9/P8/1P7/9/9/9 b - 1")
        _, _, gaps2 = validate.validate_draft_record(ok)
        self.assertFalse(any("nifu" in g for g in gaps2), gaps2)

    def test_last_move_king_flagged(self):
        rec = make_procedure_record(3)
        rec["moves"][-1]["piece"] = "K"
        _, _, gaps = validate.validate_procedure_record(rec)
        self.assertTrue(any("king move" in g for g in gaps), gaps)

    def test_unverified_is_warning(self):
        rec = make_procedure_record(3)
        rec["transcription"]["verified"] = False
        errors, warnings, _ = validate.validate_procedure_record(rec)
        self.assertEqual(errors, [])
        self.assertTrue(any("verified" in w for w in warnings), warnings)

    def test_repo_procedures_pass(self):
        rc = validate.main([], procedures=True)
        self.assertEqual(rc, 0)


class TestIiifCrop(unittest.TestCase):
    def test_build_url(self):
        import iiif_crop
        url = iiif_crop.build_url("861217", "R0000002",
                                  "pct:40.8,16,4.8,66", 900)
        self.assertEqual(
            url,
            "https://dl.ndl.go.jp/api/iiif/861217/R0000002/"
            "pct:40.8,16,4.8,66/900,/0/default.jpg")

    def test_build_url_full(self):
        import iiif_crop
        self.assertTrue(iiif_crop.build_url("861192", "R0000021",
                                            "full", 1600).endswith(
            "/R0000021/full/1600,/0/default.jpg"))


class TestSeimyoLedger(unittest.TestCase):
    def test_ledger_qcounts_match_drafts(self):
        import re
        doc = os.path.join(ROOT, "docs", "seimyo-transcription.md")
        with open(doc, encoding="utf-8") as f:
            text = f.read()
        start = text.index("## 台帳")
        end = text.index("## ", start + 5)
        rows = [l for l in text[start:end].splitlines()
                if re.match(r"^\| \S+番 \|", l)]
        self.assertEqual(len(rows), 100, "ledger should have 100 rows")
        bad = []
        for i, row in enumerate(rows, 1):
            cells = [c.strip() for c in row.strip("|").split("|")]
            try:
                want = int(cells[3])
            except (IndexError, ValueError):
                bad.append((i, "unparsable ? cell"))
                continue
            p = os.path.join(ROOT, "collections", "edo", "seimyo",
                             "drafts", "%03d.json" % i)
            with open(p, encoding="utf-8") as f:
                rec = json.load(f)
            got = rec["sfen"].count("?")
            if got != want:
                bad.append((i, "%d != %d" % (want, got)))
        self.assertEqual(bad, [], "ledger ? counts out of sync: %s" % bad[:5])


class TestSeimyoHandLedger(unittest.TestCase):
    KANJI = {"歩": "P", "香": "L", "桂": "N", "銀": "S",
             "金": "G", "角": "B", "飛": "R", "玉": "K"}
    DIGITS = {"一": 1, "二": 2, "三": 3, "四": 4,
              "五": 5, "六": 6, "七": 7, "八": 8,
              "九": 9, "十": 10}

    def parse(self, text):
        t = text.split("＋")[0].replace("枚", "")
        out = []
        for ch in t:
            if ch in self.KANJI:
                out.append(self.KANJI[ch])
            elif ch.isdigit():
                if not out:
                    return None
                out.extend([out[-1]] * (int(ch) - 1))
            elif ch in self.DIGITS:
                if not out:
                    return None
                out.extend([out[-1]] * (self.DIGITS[ch] - 1))
            else:
                return None
        return sorted(out)

    def test_ledger_hands_are_subset_of_drafts(self):
        import re
        doc = os.path.join(ROOT, "docs", "seimyo-transcription.md")
        with open(doc, encoding="utf-8") as f:
            text = f.read()
        start = text.index("## 台帳")
        end = text.index("## ", start + 5)
        rows = [l for l in text[start:end].splitlines()
                if re.match(r"^\| \S+番 \|", l)]
        self.assertEqual(len(rows), 100)
        bad = []
        for i, row in enumerate(rows, 1):
            cells = [c.strip() for c in row.strip("|").split("|")]
            want = cells[2]
            if want in ("—", "-", "なし", "記載なし"):
                continue
            parsed = self.parse(want)
            if parsed is None:
                bad.append((i, "unparsable", want))
                continue
            path = os.path.join(ROOT, "collections", "edo", "seimyo",
                                "drafts", "%03d.json" % i)
            with open(path, encoding="utf-8") as f:
                hand = json.load(f)["sfen"].split(" ")[2]
            got = []
            n = 0
            for ch in hand:
                if ch.isdigit():
                    n = n * 10 + int(ch)
                    continue
                got.extend([ch] * max(n, 1))
                n = 0
            missing = [x for x in parsed if parsed.count(x) > got.count(x)]
            if missing:
                bad.append((i, want, hand))
        self.assertEqual(bad, [], "ledger hand missing in sfen: %s" % bad[:5])


class TestSeimyoFirstMoves(unittest.TestCase):
    def test_first_moves_check_the_king(self):
        path = os.path.join(ROOT, "docs", "seimyo-first-moves.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertTrue(data["moves"])
        bad = []
        for m in data["moves"]:
            draft = os.path.join(ROOT, "collections", "edo", "seimyo",
                                 "drafts", "%03d.json" % m["number"])
            with open(draft, encoding="utf-8") as f:
                rec = json.load(f)
            bd, errs = validate.parse_sfen(rec["sfen"].replace("?", "1"))
            if bd is None:
                bad.append((m["number"], "sfen: %s" % errs))
                continue
            ksq = validate.find_king(bd, "w")
            if ksq is None:
                bad.append((m["number"], "no gote king"))
                continue
            bd2 = bd.clone()
            bd2.sq.pop(ksq, None)
            bd2.sq[(m["file"], m["rank"])] = [
                "b", m["piece"], bool(m.get("promoted"))]
            if ksq not in validate.pseudo_targets(
                    bd2, (m["file"], m["rank"])):
                bad.append((m["number"], "move does not check"))
        self.assertEqual(bad, [], "seimyo first-move checks failed: %s" % bad[:5])


class TestWebPages(unittest.TestCase):
    def test_procedures_page_cards(self):
        import re
        s = open(os.path.join(ROOT, "web", "procedures.html"),
                 encoding="utf-8").read()
        cards = re.findall(
            r'<div class="card" id="([^"]+)">(.*?)</div>', s, re.S)
        self.assertEqual(len(cards), 42,
                         "procedures page should have 42 cards")
        self.assertEqual(len({c for c, _ in cards}), 42,
                         "duplicate card ids")
        for cid, body in cards:
            self.assertIn("<img", body, cid)
            self.assertIn("worksheets/", body, cid)
            self.assertIn("issues/new", body, cid)

    def test_drafts_page_cards(self):
        import re
        s = open(os.path.join(ROOT, "web", "drafts.html"),
                 encoding="utf-8").read()
        ids = re.findall(r'<div class="card" id="([^"]+)"', s)
        self.assertEqual(len(ids), 304)
        self.assertEqual(len(set(ids)), 304, "duplicate draft card ids")
        self.assertEqual(s.count("issues/new"), 304)


class TestKanjuLedger(unittest.TestCase):
    def test_ledger_qcounts_match_drafts(self):
        import re
        doc = os.path.join(ROOT, "docs", "kanju-transcription.md")
        with open(doc, encoding="utf-8") as f:
            text = f.read()
        start = text.index("## 4. 既読台帳")
        end = text.index("## 5. ")
        rows = [l for l in text[start:end].splitlines()
                if re.match(r"^\| \S+ \|", l)]
        rows = [r for r in rows
                if r.strip("|").split("|")[0].strip() != "番"]
        self.assertEqual(len(rows), 50, "kanju ledger should have 50 rows")
        bad = []
        for i, row in enumerate(rows, 1):
            cells = [c.strip() for c in row.strip("|").split("|")]
            try:
                want = int(cells[3])
            except (IndexError, ValueError):
                bad.append((i, "unparsable ? cell"))
                continue
            path = os.path.join(ROOT, "collections", "meiji", "kanju",
                                "drafts", "%03d.json" % i)
            with open(path, encoding="utf-8") as f:
                rec = json.load(f)
            got = rec["sfen"].count("?")
            if got != want:
                bad.append((i, "%d != %d" % (want, got)))
        self.assertEqual(bad, [],
                         "kanju ledger ? counts out of sync: %s" % bad[:5])


class TestKanjuHandLedger(unittest.TestCase):
    """Ledger 持駒 and source.page must quote the same printed hand."""

    KANJI = {"歩": "P", "香": "L", "桂": "N", "銀": "S",
             "金": "G", "角": "B", "飛": "R", "玉": "K"}
    DIGITS = {"二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
              "七": 7, "八": 8, "九": 9, "十": 10}

    def normalize(self, text):
        t = text.replace("枚", "").replace("「", "").replace("」", "")
        out = []
        for ch in t:
            if ch in self.KANJI:
                out.append(self.KANJI[ch])
            elif ch.isdigit():
                if not out:
                    return None
                out.extend([out[-1]] * (int(ch) - 1))
            elif ch in self.DIGITS:
                if not out:
                    return None
                out.extend([out[-1]] * (self.DIGITS[ch] - 1))
            else:
                return None
        return sorted(out)

    def test_ledger_hands_match_printed_source(self):
        import re
        doc = os.path.join(ROOT, "docs", "kanju-transcription.md")
        with open(doc, encoding="utf-8") as f:
            text = f.read()
        start = text.index("## 4. 既読台帳")
        end = text.index("## 5. ", start)
        rows = [l for l in text[start:end].splitlines()
                if re.match(r"^\| \S+ \|", l)]
        rows = [r for r in rows
                if r.strip("|").split("|")[0].strip() != "番"]
        self.assertEqual(len(rows), 50)
        bad = []
        for i, row in enumerate(rows, 1):
            cells = [c.strip() for c in row.strip("|").split("|")]
            ledger = cells[2]
            path = os.path.join(ROOT, "collections", "meiji", "kanju",
                                "drafts", "%03d.json" % i)
            with open(path, encoding="utf-8") as f:
                page = json.load(f)["source"].get("page") or ""
            j = page.find("持駒")
            seg = None
            if j >= 0:
                seg = page[j + 2:].split(")")[0].strip().strip("「」")
                seg = seg.replace("相当", "").strip()
            if seg is not None:
                seg = seg.strip()
            none_marked = ("持駒記載なし" in page) or (seg in ("なし", ""))
            want = None if none_marked else self.normalize(seg or "")
            if ledger in ("記載なし", "なし"):
                if want:
                    bad.append((i, ledger, seg))
                continue
            got = self.normalize(ledger)
            if got is None or got != want:
                bad.append((i, ledger, seg))
        self.assertEqual(bad, [], "ledger vs printed hand: %s" % bad[:5])
class TestFirstMoveStatus(unittest.TestCase):
    def rows(self, text, heading, stop):
        a = text.index(heading)
        b = text.index(stop, a)
        rows = [l for l in text[a:b].splitlines()
                if l.startswith("| ") and not l.startswith("| 番 ")]
        return [r for r in rows if not r.startswith("|---")]

    def test_king_columns_match_drafts(self):
        doc = os.path.join(ROOT, "docs", "first-move-status.md")
        with open(doc, encoding="utf-8") as f:
            text = f.read()
        specs = [
            ("## 将棋貫珠 詰手", "## 将棋精妙", "kanju", 50),
            ("## 将棋精妙 下巻", "## 集計", "seimyo", None),
        ]
        bad = []
        for heading, stop, cid, count in specs:
            rows = self.rows(text, heading, stop)
            if count is not None:
                self.assertEqual(len(rows), count)
            base = (("collections", "meiji", "kanju", "drafts")
                    if cid == "kanju"
                    else ("collections", "edo", "seimyo", "drafts"))
            for row in rows:
                cells = [c.strip() for c in row.strip("|").split("|")]
                try:
                    n = int(cells[0])
                    cell = cells[1]
                    file_part = int(cell[0])
                    rank_part = "abcdefghi".index(cell[1]) + 1
                except (ValueError, IndexError):
                    bad.append((cid, row[:20], "unparsable"))
                    continue
                path = os.path.join(ROOT, *base, "%03d.json" % n)
                with open(path, encoding="utf-8") as f:
                    rec = json.load(f)
                bd, _ = validate.parse_sfen(rec["sfen"].replace("?", "1"))
                ksq = validate.find_king(bd, "w")
                if ksq != (file_part, rank_part):
                    bad.append((cid, n, cell, ksq))
                if "?=" in cells[3]:
                    q = int(cells[3].split("?=")[1].rstrip("）").strip())
                    if q != rec["sfen"].count("?"):
                        bad.append((cid, n, "q", q,
                                    rec["sfen"].count("?")))
        self.assertEqual(bad, [], "status doc drift: %s" % bad[:5])

    def test_totals_match_json(self):
        doc = os.path.join(ROOT, "docs", "first-move-status.md")
        with open(doc, encoding="utf-8") as f:
            text = f.read()

        def load(name):
            path = os.path.join(ROOT, "docs", name)
            with open(path, encoding="utf-8") as f:
                return json.load(f)

        kanju = len(load("kanju-first-moves.json")["moves"])
        seimyo = len(load("seimyo-first-moves.json")["moves"])
        readings = len(load("kanju-procedure-readings.json")["readings"])
        self.assertIn("検証済み %d/50" % kanju, text)
        self.assertIn("検証済み %d/100" % seimyo, text)
        self.assertIn("貫珠 %d題" % readings, text)


class TestKanjuColumnHeads(unittest.TestCase):
    KANJI = "零一二三四五六七八九"

    def test_heads_are_consistent(self):
        path = os.path.join(ROOT, "docs", "kanju-column-heads.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        fpath = os.path.join(ROOT, "docs", "kanju-first-moves.json")
        with open(fpath, encoding="utf-8") as f:
            firsts = json.load(f)["moves"]
        by_number = dict((m["number"], {"moves": [m]}) for m in firsts)
        rpath = os.path.join(ROOT, "docs", "kanju-procedure-readings.json")
        with open(rpath, encoding="utf-8") as f:
            for r in json.load(f)["readings"]:
                by_number.setdefault(r["number"], r)
        bad = []
        for h in data["heads"]:
            if h.get("kind") == "cartouche" or "raw" not in h:
                continue
            if "dest" not in h:
                continue

            raw = h["raw"]
            a, b = raw[0], raw[1]
            if a not in self.KANJI or b not in self.KANJI:
                bad.append((h["leaf"], raw, "digits"))
                continue
            ai = self.KANJI.index(a)
            bi = self.KANJI.index(b)
            if h.get("order") == "file-rank":
                want = "%d%s" % (ai, self.KANJI[bi])
            else:
                want = "%d%s" % (bi, self.KANJI[ai])
            if want != h["dest"]:
                bad.append((h["leaf"], raw, h["dest"], want))
            n = h.get("problem")
            if h.get("verified") and n is not None:
                r = by_number.get(n)
                if r is None:
                    bad.append((h["leaf"], raw, "no reading"))
                elif r["moves"][0]["raw"] != raw:
                    bad.append((h["leaf"], raw,
                                "reading raw %s" % r["moves"][0]["raw"]))
        self.assertEqual(bad, [], "column heads inconsistent: %s" % bad[:5])


class TestFirstMoveTargets(unittest.TestCase):
    def test_doc_matches_generator(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import list_first_move_targets as g

        path = os.path.join(ROOT, "docs", "first-move-targets.md")
        with open(path, encoding="utf-8") as f:
            doc = f.read()
        self.assertEqual(doc, g.build(25),
                         "regenerate with tools/list_first_move_targets.py "
                         "--out docs/first-move-targets.md")


class TestCandidatesReport(unittest.TestCase):
    def test_docs_match_generator(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import candidates_report as g

        for cid, name in (("kanju", "first-move-candidates-kanju.md"),
                          ("seimyo", "first-move-candidates.md")):
            path = os.path.join(ROOT, "docs", name)
            with open(path, encoding="utf-8") as f:
                doc = f.read()
            self.assertEqual(
                doc, g.render(cid),
                "regenerate with tools/candidates_report.py "
                "--collection %s --out docs/%s" % (cid, name))

    def test_claimed_heads_are_annotated(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import candidates_report as g

        hits = [h for _, _, _, hs in g.build("kanju") for h in hs]
        self.assertTrue(hits)
        self.assertTrue(any(h["used_by"] for h in hits))


class TestDocsCounts(unittest.TestCase):
    def test_procedures_section_41_counts(self):
        with open(os.path.join(ROOT, "docs", "kanju-first-moves.json"),
                  encoding="utf-8") as f:
            kanju = len(json.load(f)["moves"])
        with open(os.path.join(ROOT, "docs", "kanju-procedure-readings.json"),
                  encoding="utf-8") as f:
            readings = len(json.load(f)["readings"])
        with open(os.path.join(ROOT, "docs", "seimyo-first-moves.json"),
                  encoding="utf-8") as f:
            seimyo = len(json.load(f)["moves"])
        with open(os.path.join(ROOT, "docs", "procedures.md"),
                  encoding="utf-8") as f:
            text = f.read()
        self.assertIn("貫珠 **%d題**" % readings, text)
        self.assertIn("精妙 **%d/100**" % seimyo, text)


    def test_checks_from_ignores_other_attackers(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import guess_first_move as g

        # 玉 1二 is already attacked by the 飛 on 1九 (illegal draft).
        bd, errs = validate.parse_sfen("9/8k/9/9/9/9/9/9/8R w - 1")
        self.assertEqual(errs, [])
        ksq = validate.find_king(bd, "w")
        self.assertEqual(ksq, (1, 2))
        self.assertTrue(validate.is_attacked(bd, ksq, "b"))
        self.assertFalse(g.checks_from(bd, ksq, 5, 5, "P"))
        self.assertTrue(g.checks_from(bd, ksq, 1, 3, "P"))

class TestSeimyoColumnHeads(unittest.TestCase):
    KANJI = "\u96f6\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d"

    def test_heads_are_consistent(self):
        path = os.path.join(ROOT, "docs", "seimyo-column-heads.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        rpath = os.path.join(ROOT, "docs", "seimyo-first-moves.json")
        with open(rpath, encoding="utf-8") as f:
            moves = {m["number"]: m for m in json.load(f)["moves"]}
        bad = []
        for h in data["heads"]:
            if h.get("kind") == "cartouche" or "raw" not in h:
                continue
            if "dest" not in h:
                continue
            raw = h["raw"]
            a, b = raw[0], raw[1]
            if a not in self.KANJI or b not in self.KANJI:
                bad.append((h["leaf"], raw, "digits"))
                continue
            ai = self.KANJI.index(a)
            bi = self.KANJI.index(b)
            if h.get("order") == "file-rank":
                want = "%d%s" % (ai, self.KANJI[bi])
            else:
                want = "%d%s" % (bi, self.KANJI[ai])
            if want != h["dest"]:
                bad.append((h["leaf"], raw, h["dest"], want))
            n = h.get("problem")
            if h.get("verified") and n is not None:
                m = moves.get(n)
                if m is None:
                    bad.append((h["leaf"], raw, "no first-move"))
                elif m["raw"] != raw:
                    bad.append((h["leaf"], raw, "first-move %s" % m["raw"]))
        self.assertEqual(bad, [], "seimyo heads inconsistent: %s" % bad[:5])



class TestFirstMoveBoardQ(unittest.TestCase):
    def test_board_q_matches_draft(self):
        bad = []
        for cid, base in (("kanju", ("collections", "meiji", "kanju",
                                    "drafts")),
                          ("seimyo", ("collections", "edo", "seimyo",
                                      "drafts"))):
            path = os.path.join(ROOT, "docs", "%s-first-moves.json" % cid)
            with open(path, encoding="utf-8") as f:
                moves = json.load(f)["moves"]
            for m in moves:
                dpath = os.path.join(ROOT, *base, "%03d.json" % m["number"])
                with open(dpath, encoding="utf-8") as f:
                    sfen = json.load(f)["sfen"]
                q = sfen.count("?")
                if q != m.get("board_q"):
                    bad.append((cid, m["number"], m.get("board_q"), q))
                want = ("board-good" if q <= 12
                        else "board-partial" if q <= 19 else "board-sparse")
                if m.get("confidence") != want:
                    bad.append((cid, m["number"], m.get("confidence"), want))
        self.assertEqual(bad, [], "board_q out of date: %s" % bad[:5])



class TestHeadAssignment(unittest.TestCase):
    def test_no_problem_assigned_twice(self):
        for cid in ("kanju", "seimyo"):
            with open(os.path.join(ROOT, "docs",
                                   "%s-column-heads.json" % cid),
                      encoding="utf-8") as f:
                heads = json.load(f)["heads"]
            seen = {}
            bad = []
            for h in heads:
                n = h.get("problem")
                if not h.get("verified") or n is None:
                    continue
                if n in seen:
                    bad.append((cid, n, seen[n], h["x_pct"]))
                seen[n] = h["x_pct"]
            self.assertEqual(bad, [],
                             "problem assigned to two heads: %s" % bad[:5])

    def test_assigned_problem_is_verified_and_unique_position(self):
        for cid in ("kanju", "seimyo"):
            with open(os.path.join(ROOT, "docs",
                                   "%s-column-heads.json" % cid),
                      encoding="utf-8") as f:
                heads = json.load(f)["heads"]
            with open(os.path.join(ROOT, "docs",
                                   "%s-first-moves.json" % cid),
                      encoding="utf-8") as f:
                done = {m["number"] for m in json.load(f)["moves"]}
            rpath = os.path.join(ROOT, "docs",
                                 "%s-procedure-readings.json" % cid)
            if os.path.exists(rpath):
                with open(rpath, encoding="utf-8") as f:
                    done |= {r["number"] for r in json.load(f)["readings"]}
            unverified = [(h["leaf"], h["x_pct"], h.get("raw"),
                           h["problem"]) for h in heads
                          if h.get("problem") is not None
                          and h["problem"] not in done]
            self.assertEqual(unverified, [],
                             "%s heads assigned to unverified problems: %s"
                             % (cid, unverified[:5]))
            seen = set()
            dup = []
            for h in heads:
                key = (h["leaf"], h["page"], h["x_pct"])
                if key in seen:
                    dup.append(key)
                seen.add(key)
            self.assertEqual(dup, [], "%s duplicate head positions: %s"
                             % (cid, dup[:5]))



class TestImageRefs(unittest.TestCase):
    def test_every_source_rid_has_image(self):
        import re
        bad = []
        for path in glob.glob(os.path.join(ROOT, "collections", "*", "*",
                                           "drafts", "*.json")):
            with open(path, encoding="utf-8") as f:
                page = json.load(f).get("source", {}).get("page") or ""
            for pid, rid in re.findall(r"PID:(\d{6})\s*(R\d{7})", page):
                img = os.path.join(ROOT, "web", "images",
                                   "%s_%s.jpg" % (pid, rid))
                if not os.path.exists(img):
                    bad.append((os.path.basename(path), pid, rid))
        self.assertEqual(bad, [], "source images missing: %s" % bad[:5])



class TestDraftProvenance(unittest.TestCase):
    def test_drafts_carry_policy_note(self):
        marker = "NDL\u753b\u50cf\u76f4\u63a5\u8aad\u53d6\u306e\u307f\u3092\u6839\u62e0\u3068\u3059\u308bdraft"
        bad = []
        paths = glob.glob(os.path.join(ROOT, "collections", "*", "*",
                                       "drafts", "*.json"))
        self.assertGreater(len(paths), 300)
        for path in paths:
            with open(path, encoding="utf-8") as f:
                notes = json.load(f).get("notes") or []
            if not notes or marker not in notes[0]:
                bad.append(os.path.basename(path))
        self.assertEqual(bad, [], "drafts without policy note: %s" % bad[:5])



    def test_all_drafts_flagged_for_review(self):
        bad = []
        for path in glob.glob(os.path.join(ROOT, "collections", "*", "*",
                                           "drafts", "*.json")):
            with open(path, encoding="utf-8") as f:
                if json.load(f).get("needs_manual_review") is not True:
                    bad.append(os.path.basename(path))
        self.assertEqual(bad, [], "drafts not flagged: %s" % bad[:5])

    def test_summary_q_totals_match(self):
        import re
        with open(os.path.join(ROOT, "docs", "progress.md"),
                  encoding="utf-8") as f:
            text = f.read()
        rows = {}
        for l in text.splitlines():
            if "staging drafts" not in l or not l.startswith("| "):
                continue
            cells = [c.strip() for c in l.strip("|").split("|")]
            m = re.match(r"([a-z]+)", cells[0])
            if not m:
                continue
            try:
                rows[m.group(1)] = int(cells[3].split("(")[0].replace(",", ""))
            except (IndexError, ValueError):
                pass
        bad = []
        for cid, want in rows.items():
            total = 0
            for path in glob.glob(os.path.join(ROOT, "collections", "*", cid,
                                               "drafts", "*.json")):
                with open(path, encoding="utf-8") as f:
                    total += json.load(f)["sfen"].count("?")
            if total != want:
                bad.append((cid, want, total))
        self.assertEqual(bad, [], "summary ? totals out of sync: %s" % bad)

    def test_readme_counts_match_json(self):
        import re
        with open(os.path.join(ROOT, "docs", "seimyo-first-moves.json"),
                  encoding="utf-8") as f:
            seimyo = len(json.load(f)["moves"])
        with open(os.path.join(ROOT, "docs", "kanju-first-moves.json"),
                  encoding="utf-8") as f:
            kanju = len(json.load(f)["moves"])
        with open(os.path.join(ROOT, "docs",
                               "kanju-procedure-readings.json"),
                  encoding="utf-8") as f:
            readings = len(json.load(f)["readings"])
        with open(os.path.join(ROOT, "README.ja.md"),
                  encoding="utf-8") as f:
            ja = f.read()
        with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
            en = f.read()
        self.assertIn("**%d\u984c** \u3092\u539f\u5178\u5207\u51fa" % seimyo, ja)
        self.assertIn("**%d\u984c**\uff08%d\u984c\u306f\u76e4\u9762\u691c\u8a3c"
                      % (kanju + readings, kanju), ja)
        self.assertIn("**%d of 100**" % seimyo, en)
        self.assertIn("**%d problems** (%d board-checked"
                      % (kanju + readings, kanju), en)

class TestWebRefs(unittest.TestCase):
    def test_local_links_resolve(self):
        import re
        bad = []
        for page in ("web/index.html", "web/drafts.html", "web/procedures.html"):
            path = os.path.join(ROOT, page)
            with open(path, encoding="utf-8") as f:
                text = f.read()
            base = os.path.dirname(path)
            for m in re.finditer(r'(?:href|src)="([^"#?]+)"', text):
                url = m.group(1)
                if url.startswith(("http://", "https://", "mailto:",
                                   "data:")) or "${" in url:
                    continue
                if url.startswith("/"):
                    continue
                target = os.path.normpath(os.path.join(base, url))
                if not os.path.exists(target):
                    bad.append((page, url))
        self.assertEqual(bad, [], "missing local links: %s" % bad[:5])


class TestToolsCompile(unittest.TestCase):
    def test_tools_compile(self):
        import glob
        import py_compile
        bad = []
        for path in sorted(glob.glob(os.path.join(ROOT, "tools", "*.py"))):
            try:
                py_compile.compile(path, doraise=True)
            except py_compile.PyCompileError as exc:
                bad.append((os.path.basename(path), str(exc)))
        self.assertEqual(bad, [], "tools with syntax errors: %s" % bad[:3])


class TestCollectionCounts(unittest.TestCase):
    def test_counts_match_problem_count(self):
        import glob
        for col in sorted(glob.glob(os.path.join(
                ROOT, "collections", "*", "*", "collection.json"))):
            with open(col, encoding="utf-8") as f:
                rec = json.load(f)
            base = os.path.dirname(col)
            n = 0
            for sub in ("drafts", "problems"):
                d = os.path.join(base, sub)
                if os.path.isdir(d):
                    n += len(glob.glob(os.path.join(d, "*.json")))
            self.assertEqual(
                n, rec.get("problem_count"),
                "%s: %d files vs problem_count %s"
                % (col, n, rec.get("problem_count")))


class TestKanjuFirstMoves(unittest.TestCase):
    def test_first_moves_check_the_king(self):
        path = os.path.join(ROOT, "docs", "kanju-first-moves.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertTrue(data["moves"])
        bad = []
        for m in data["moves"]:
            draft = os.path.join(ROOT, "collections", "meiji", "kanju",
                                 "drafts", "%03d.json" % m["number"])
            with open(draft, encoding="utf-8") as f:
                rec = json.load(f)
            bd, errs = validate.parse_sfen(rec["sfen"].replace("?", "1"))
            if bd is None:
                bad.append((m["number"], "sfen: %s" % errs))
                continue
            ksq = validate.find_king(bd, "w")
            if ksq is None:
                bad.append((m["number"], "no gote king"))
                continue
            bd2 = bd.clone()
            bd2.sq.pop(ksq, None)
            bd2.sq[(m["file"], m["rank"])] = [
                "b", m["piece"], bool(m.get("promoted"))]
            if ksq not in validate.pseudo_targets(
                    bd2, (m["file"], m["rank"])):
                bad.append((m["number"], "move does not check"))
        self.assertEqual(bad, [], "first-move checks failed: %s" % bad[:5])


class TestKanjuProcedureReadings(unittest.TestCase):
    def test_readings_are_notation_consistent(self):
        path = os.path.join(ROOT, "docs", "kanju-procedure-readings.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertTrue(data["readings"])
        kanji = "零一二三四五六七八九"
        bad = []
        for r in data["readings"]:
            draft = os.path.join(ROOT, "collections", "meiji", "kanju",
                                 "drafts", "%03d.json" % r["number"])
            with open(draft, encoding="utf-8") as f:
                rec = json.load(f)
            bd, errs = validate.parse_sfen(rec["sfen"].replace("?", "1"))
            if bd is None:
                bad.append((r["number"], "sfen: %s" % errs))
                continue
            ksq = validate.find_king(bd, "w")
            for i, m in enumerate(r["moves"]):
                want = "sente" if i % 2 == 0 else "gote"
                if m["side"] != want:
                    bad.append((r["number"], i, "side order"))
                rank, file = m["dest"]["rank"], m["dest"]["file"]
                if not (1 <= rank <= 9 and 1 <= file <= 9):
                    bad.append((r["number"], i, "dest range"))
                if m["raw"].startswith("同"):
                    if m["dest"] != r["moves"][i - 1]["dest"]:
                        bad.append((r["number"], i, "同 dest mismatch"))
                elif not m["raw"].startswith(
                        (kanji[file] + kanji[rank])
                        if m.get("order") == "file-rank"
                        else (kanji[rank] + kanji[file])):
                    bad.append((r["number"], i, "raw/dest mismatch"))
                if m.get("attacks_gote_king"):
                    if ksq is None:
                        bad.append((r["number"], i, "no gote king"))
                        continue
                    probe = bd.clone()
                    probe.sq.pop(ksq, None)
                    probe.sq[(file, rank)] = ["b", m["piece"],
                                               bool(m.get("promoted"))]
                    if ksq not in validate.pseudo_targets(
                            probe, (file, rank)):
                        bad.append((r["number"], i, "claimed check fails"))
                if m["side"] == "gote" and m["piece"] == "K":
                    if ksq is None:
                        bad.append((r["number"], i, "no gote king"))
                        continue
                    bd.sq.pop(ksq, None)
                    bd.sq[(file, rank)] = ["w", "K", False]
                    ksq = (file, rank)
                elif m["side"] == "sente":
                    bd.sq.pop((file, rank), None)
                    bd.sq[(file, rank)] = ["b", m["piece"], False]
        self.assertEqual(bad, [], "procedure readings failed: %s" % bad[:5])


class TestGuessFirstMove(unittest.TestCase):
    def test_candidates_match_known_readings(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import guess_first_move as g

        bd, _ = validate.parse_sfen(
            g.load("kanju", 13)["sfen"].replace("?", "1"))
        cand = g.candidates(bd, validate.find_king(bd, "w"))
        self.assertIn((8, 1), cand["S"], "kanju 13: 8一 must check with 銀")

        bd, _ = validate.parse_sfen(
            g.load("kanju", 14)["sfen"].replace("?", "1"))
        cand = g.candidates(bd, validate.find_king(bd, "w"))
        self.assertEqual(cand.get("N"), [(2, 3)],
                         "kanju 14: only 2三 桂 checks")

    def test_probe_pair_resolves_order(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import guess_first_move as g
        import io as _io
        import contextlib

        bd, _ = validate.parse_sfen(
            g.load("kanju", 18)["sfen"].replace("?", "1"))
        ksq = validate.find_king(bd, "w")
        buf = _io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = g.probe_pair(bd, ksq, "三一", "S", True)
        out = buf.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("1c 王手にならない", out)
        self.assertIn("3a 王手", out)



if __name__ == "__main__":
    unittest.main(verbosity=2)
