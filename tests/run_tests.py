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


if __name__ == "__main__":
    unittest.main(verbosity=2)
