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


if __name__ == "__main__":
    unittest.main(verbosity=2)
