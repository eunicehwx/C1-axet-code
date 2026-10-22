"""Tests for logscope_core.commands.timeline."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logscope_core.commands.timeline import parse_bucket_size, run_timeline

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
TIMELINE_LOG = os.path.join(FIXTURES, "timeline_sample.log")


class TestParseBucketSize(unittest.TestCase):
    def test_minutes(self):
        self.assertEqual(parse_bucket_size("15m"), 15 * 60)

    def test_hours(self):
        self.assertEqual(parse_bucket_size("1h"), 3600)

    def test_days(self):
        self.assertEqual(parse_bucket_size("1d"), 86400)

    def test_invalid_format_raises(self):
        with self.assertRaises(ValueError):
            parse_bucket_size("bogus")

    def test_zero_value_raises(self):
        with self.assertRaises(ValueError):
            parse_bucket_size("0m")


class TestRunTimeline(unittest.TestCase):
    def test_buckets_errors_only_by_15m(self):
        result = run_timeline(TIMELINE_LOG, bucket="15m")
        counts = dict(result["timeline"])
        self.assertEqual(counts["2026-10-01T09:00:00+00:00"], 3)  # 09:01, 09:05, 09:14:59
        self.assertEqual(counts["2026-10-01T09:15:00+00:00"], 2)  # 09:15:00, 09:29:59
        self.assertEqual(counts["2026-10-01T10:00:00+00:00"], 1)  # 10:00:00

    def test_total_errors_matches_sum(self):
        result = run_timeline(TIMELINE_LOG, bucket="15m")
        total = sum(c for _, c in result["timeline"])
        self.assertEqual(total, result["total_errors"])
        self.assertEqual(result["total_errors"], 6)

    def test_malformed_lines_counted(self):
        result = run_timeline(TIMELINE_LOG, bucket="15m")
        self.assertEqual(result["malformed_lines"], 1)

    def test_non_error_levels_excluded(self):
        result = run_timeline(TIMELINE_LOG, bucket="1h")
        total = sum(c for _, c in result["timeline"])
        self.assertEqual(total, 6)  # INFO/WARN lines never counted

    def test_invalid_bucket_exits_1(self):
        with self.assertRaises(SystemExit) as ctx:
            run_timeline(TIMELINE_LOG, bucket="not-a-bucket")
        self.assertEqual(ctx.exception.code, 1)

    def test_no_errors_returns_empty_timeline(self):
        no_error_log = os.path.join(FIXTURES, "no_errors.log")
        with open(no_error_log, "w", encoding="utf-8") as fh:
            fh.write("2026-10-01T09:00:00Z INFO all good\n")
        try:
            result = run_timeline(no_error_log, bucket="15m")
            self.assertEqual(result["timeline"], [])
            self.assertEqual(result["total_errors"], 0)
        finally:
            os.remove(no_error_log)


if __name__ == "__main__":
    unittest.main()
