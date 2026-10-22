"""End-to-end tests for logscope_core.cli."""

import json
import os
import sys
import tempfile
import unittest
from io import StringIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logscope_core.cli import main

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
MIXED_LOG = os.path.join(FIXTURES, "mixed_with_malformed.log")
TIMELINE_LOG = os.path.join(FIXTURES, "timeline_sample.log")


def run_cli(argv):
    """Run main() with argv, capturing stdout, and return (stdout, exit_code)."""
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        try:
            main(argv)
        except SystemExit as exc:
            code = exc.code if exc.code is not None else 0
        else:
            code = 0
        return sys.stdout.getvalue(), code
    finally:
        sys.stdout = old_stdout


class TestCliSummary(unittest.TestCase):
    def test_summary_json_default(self):
        out, code = run_cli(["summary", MIXED_LOG])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["command"], "summary")
        self.assertEqual(data["total_lines"], 6)

    def test_summary_md_format(self):
        out, code = run_cli(["summary", MIXED_LOG, "--format", "md"])
        self.assertEqual(code, 0)
        self.assertIn("## Summary", out)


class TestCliTimeline(unittest.TestCase):
    def test_timeline_default_bucket(self):
        out, code = run_cli(["timeline", TIMELINE_LOG])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["bucket"], "15m")

    def test_timeline_invalid_bucket_exits_1(self):
        out, code = run_cli(["timeline", TIMELINE_LOG, "--bucket", "bogus"])
        self.assertEqual(code, 1)


class TestCliGrep(unittest.TestCase):
    def test_grep_level_filter(self):
        out, code = run_cli(["grep", TIMELINE_LOG, "--level", "ERROR", "--format", "json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["matched_lines"], 6)

    def test_grep_since_filter(self):
        out, code = run_cli(["grep", TIMELINE_LOG, "--since", "2026-10-01 09:15:00"])
        data = json.loads(out)
        self.assertEqual(data["matched_lines"], 5)


class TestCliOutputFile(unittest.TestCase):
    def test_output_without_format_auto_selects_md(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "report.md")
            run_cli(["summary", MIXED_LOG, "--output", out_path])
            with open(out_path, encoding="utf-8") as fh:
                content = fh.read()
            self.assertIn("## Summary", content)

    def test_missing_logfile_exits_1(self):
        out, code = run_cli(["summary", os.path.join(FIXTURES, "nope.log")])
        self.assertEqual(code, 1)

    def test_no_command_exits_1(self):
        out, code = run_cli([])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
