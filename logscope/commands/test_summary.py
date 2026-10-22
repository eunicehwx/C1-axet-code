"""Tests for logscope_core.commands.summary."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logscope_core.commands.summary import run_summary

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


class TestRunSummary(unittest.TestCase):
    def setUp(self):
        self.result = run_summary(os.path.join(FIXTURES, "mixed_with_malformed.log"))

    def test_total_and_malformed_counts(self):
        self.assertEqual(self.result["total_lines"], 6)
        self.assertEqual(self.result["malformed_lines"], 3)

    def test_level_counts(self):
        self.assertEqual(self.result["levels"], {"ERROR": 3, "INFO": 2, "WARN": 1})

    def test_first_and_last_timestamp(self):
        self.assertEqual(self.result["first_timestamp"], "2026-10-01T08:00:00Z")
        self.assertEqual(self.result["last_timestamp"], "2026-10-01T08:05:00Z")

    def test_top_errors(self):
        top_errors = dict(self.result["top_errors"])
        self.assertEqual(top_errors["Failed to connect to cache server"], 2)
        self.assertEqual(top_errors["Database timeout"], 1)
        self.assertLessEqual(len(self.result["top_errors"]), 5)

    def test_command_and_file_metadata(self):
        self.assertEqual(self.result["command"], "summary")
        self.assertTrue(self.result["file"].endswith("mixed_with_malformed.log"))

    def test_empty_file(self):
        empty_path = os.path.join(FIXTURES, "empty.log")
        with open(empty_path, "w", encoding="utf-8"):
            pass
        try:
            result = run_summary(empty_path)
            self.assertEqual(result["total_lines"], 0)
            self.assertEqual(result["malformed_lines"], 0)
            self.assertEqual(result["levels"], {})
            self.assertIsNone(result["first_timestamp"])
            self.assertIsNone(result["last_timestamp"])
            self.assertEqual(result["top_errors"], [])
        finally:
            os.remove(empty_path)

    def test_missing_file_exits_1(self):
        with self.assertRaises(SystemExit) as ctx:
            run_summary(os.path.join(FIXTURES, "does_not_exist.log"))
        self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
