"""Tests for logscope_core.commands.grep."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logscope_core.commands.grep import parse_since, run_grep

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
TIMELINE_LOG = os.path.join(FIXTURES, "timeline_sample.log")
MIXED_LOG = os.path.join(FIXTURES, "mixed_with_malformed.log")


class TestParseSince(unittest.TestCase):
    def test_space_separated(self):
        dt = parse_since("2026-10-01 09:00:00")
        self.assertEqual(dt.hour, 9)

    def test_iso_with_z(self):
        dt = parse_since("2026-10-01T09:00:00Z")
        self.assertEqual(dt.hour, 9)

    def test_space_separated_no_seconds(self):
        dt = parse_since("2026-10-01 09:00")
        self.assertEqual(dt.minute, 0)

    def test_invalid_raises(self):
        with self.assertRaises(ValueError):
            parse_since("not-a-date")


class TestRunGrep(unittest.TestCase):
    def test_filter_by_level_only(self):
        result = run_grep(TIMELINE_LOG, level="ERROR")
        self.assertEqual(result["matched_lines"], 6)
        self.assertEqual(len(result["filtered_lines"]), 6)
        self.assertFalse(result["truncated"])

    def test_filter_by_level_case_insensitive(self):
        result = run_grep(TIMELINE_LOG, level="error")
        self.assertEqual(result["matched_lines"], 6)

    def test_filter_by_since_only(self):
        result = run_grep(TIMELINE_LOG, since="2026-10-01 09:15:00")
        # errors/info/warn at or after 09:15:00: 09:15 ERROR, 09:20 WARN,
        # 09:29:59 ERROR, 10:00 ERROR, 10:05 INFO = 5 lines
        self.assertEqual(result["matched_lines"], 5)

    def test_filter_by_level_and_since(self):
        result = run_grep(TIMELINE_LOG, level="ERROR", since="2026-10-01 09:15:00")
        self.assertEqual(result["matched_lines"], 3)  # 09:15, 09:29:59, 10:00

    def test_malformed_lines_reported(self):
        result = run_grep(TIMELINE_LOG)
        self.assertEqual(result["malformed_lines"], 1)

    def test_no_filters_returns_all_valid_lines(self):
        result = run_grep(MIXED_LOG)
        self.assertEqual(result["matched_lines"], 6)

    def test_truncation_flag_and_cap(self):
        result = run_grep(TIMELINE_LOG, level="ERROR", limit=2)
        self.assertEqual(result["matched_lines"], 6)
        self.assertEqual(len(result["filtered_lines"]), 2)
        self.assertTrue(result["truncated"])

    def test_invalid_since_exits_1(self):
        with self.assertRaises(SystemExit) as ctx:
            run_grep(TIMELINE_LOG, since="not-a-timestamp")
        self.assertEqual(ctx.exception.code, 1)

    def test_empty_result_when_no_match(self):
        result = run_grep(TIMELINE_LOG, level="FATAL")
        self.assertEqual(result["matched_lines"], 0)
        self.assertEqual(result["filtered_lines"], [])
        self.assertFalse(result["truncated"])

    def test_missing_file_exits_1(self):
        with self.assertRaises(SystemExit) as ctx:
            run_grep(os.path.join(FIXTURES, "does_not_exist.log"))
        self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
