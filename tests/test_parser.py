"""Tests for logscope_core.parser."""

import os
import sys
import unittest
from datetime import timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logscope_core.parser import LogParser, parse_timestamp

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


class TestParseTimestamp(unittest.TestCase):
    def test_z_suffix(self):
        dt = parse_timestamp("2026-10-01T08:00:00Z")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.tzinfo, timezone.utc)
        self.assertEqual(dt.hour, 8)

    def test_offset_suffix(self):
        dt = parse_timestamp("2026-10-01T08:00:00+00:00")
        self.assertIsNotNone(dt)

    def test_naive_timestamp_assumed_utc(self):
        dt = parse_timestamp("2026-10-01T08:00:00")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.tzinfo, timezone.utc)

    def test_invalid_timestamp_returns_none(self):
        self.assertIsNone(parse_timestamp("not-a-timestamp"))


class TestLogParser(unittest.TestCase):
    def test_parses_valid_line(self):
        parser = LogParser(os.path.join(FIXTURES, "mixed_with_malformed.log"))
        lines = list(parser.stream())
        self.assertTrue(any(l.level == "INFO" and "Application started" in l.message for l in lines))

    def test_malformed_lines_are_counted_and_skipped(self):
        parser = LogParser(os.path.join(FIXTURES, "mixed_with_malformed.log"))
        lines = list(parser.stream())
        # 2 lines don't match the log pattern + 1 has an uparseable calendar date;
        # blank line is skipped silently (not malformed)
        self.assertEqual(parser.malformed_count, 3)
        self.assertEqual(len(lines), 6)

    def test_level_is_uppercased(self):
        parser = LogParser(os.path.join(FIXTURES, "mixed_with_malformed.log"))
        for parsed in parser.stream():
            self.assertEqual(parsed.level, parsed.level.upper())

    def test_blank_lines_do_not_count_as_malformed(self):
        parser = LogParser(os.path.join(FIXTURES, "mixed_with_malformed.log"))
        list(parser.stream())
        # malformed_count already asserted == 3 above (blank line excluded)
        self.assertEqual(parser.malformed_count, 3)

    def test_missing_file_exits_with_code_1(self):
        parser = LogParser(os.path.join(FIXTURES, "does_not_exist.log"))
        with self.assertRaises(SystemExit) as ctx:
            list(parser.stream())
        self.assertEqual(ctx.exception.code, 1)

    def test_stream_is_a_generator_not_a_list(self):
        import inspect

        parser = LogParser(os.path.join(FIXTURES, "mixed_with_malformed.log"))
        self.assertTrue(inspect.isgenerator(parser.stream()))


if __name__ == "__main__":
    unittest.main()
