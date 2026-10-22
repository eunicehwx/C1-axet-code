"""Tests for logscope_core.formatter."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logscope_core.formatter import format_json, format_markdown, format_output

SUMMARY_DATA = {
    "command": "summary",
    "file": "app.log",
    "total_lines": 10,
    "malformed_lines": 1,
    "levels": {"ERROR": 2, "INFO": 7, "WARN": 1},
    "first_timestamp": "2026-10-01T08:00:00Z",
    "last_timestamp": "2026-10-01T09:00:00Z",
    "top_errors": [("Database timeout", 2)],
}

TIMELINE_DATA = {
    "command": "timeline",
    "file": "app.log",
    "bucket": "15m",
    "malformed_lines": 0,
    "timeline": [("2026-10-01T09:00:00+00:00", 3), ("2026-10-01T09:15:00+00:00", 1)],
    "total_errors": 4,
}

GREP_DATA = {
    "command": "grep",
    "file": "app.log",
    "filters": {"level": "ERROR", "since": None},
    "malformed_lines": 0,
    "matched_lines": 2,
    "filtered_lines": ["2026-10-01T08:00:00Z ERROR a", "2026-10-01T08:05:00Z ERROR b"],
    "truncated": False,
}


class TestFormatJson(unittest.TestCase):
    def test_round_trips(self):
        rendered = format_json(SUMMARY_DATA)
        parsed = json.loads(rendered)
        self.assertEqual(parsed["command"], "summary")
        self.assertEqual(parsed["total_lines"], 10)


class TestFormatMarkdown(unittest.TestCase):
    def test_summary_markdown_has_expected_sections(self):
        md = format_markdown(SUMMARY_DATA)
        self.assertIn("# logscope Report", md)
        self.assertIn("## Summary", md)
        self.assertIn("| ERROR | 2 |", md)
        self.assertIn("Database timeout", md)

    def test_timeline_markdown_has_bar_chart(self):
        md = format_markdown(TIMELINE_DATA)
        self.assertIn("## Timeline", md)
        self.assertIn("█", md)
        self.assertIn("2026-10-01T09:00:00+00:00", md)

    def test_grep_markdown_lists_filtered_lines(self):
        md = format_markdown(GREP_DATA)
        self.assertIn("## Grep Results", md)
        self.assertIn("2026-10-01T08:00:00Z ERROR a", md)

    def test_empty_timeline_shows_no_errors_message(self):
        data = dict(TIMELINE_DATA, timeline=[], total_errors=0)
        md = format_markdown(data)
        self.assertIn("No errors found", md)

    def test_unknown_command_falls_back_to_json_block(self):
        md = format_markdown({"command": "unknown", "x": 1})
        self.assertIn("```json", md)


class TestFormatOutput(unittest.TestCase):
    def test_json_default(self):
        rendered = format_output(SUMMARY_DATA)
        json.loads(rendered)  # must be valid JSON

    def test_md_format(self):
        rendered = format_output(SUMMARY_DATA, format_type="md")
        self.assertIn("## Summary", rendered)

    def test_writes_output_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "report.md")
            format_output(SUMMARY_DATA, format_type="md", output_file=out_path)
            with open(out_path, encoding="utf-8") as fh:
                content = fh.read()
            self.assertIn("## Summary", content)


if __name__ == "__main__":
    unittest.main()
