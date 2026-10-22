"""logscope command-line interface: argument parsing and dispatch."""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from logscope_core.commands.grep import run_grep
from logscope_core.commands.summary import run_summary
from logscope_core.commands.timeline import run_timeline
from logscope_core.formatter import format_output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logscope",
        description="logscope: fast log analysis for incidents, no dashboard required",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    summary = subparsers.add_parser("summary", help="Counts by level, top errors, first/last timestamp")
    summary.add_argument("logfile", help="Path to log file")
    summary.add_argument("--format", choices=["json", "md"], default=None, help="Output format (default: json, or md if --output is set)")
    summary.add_argument("--output", type=str, default=None, help="Write output to file (implies --format md if not specified)")

    timeline = subparsers.add_parser("timeline", help="Error count per time bucket, as a text bar chart")
    timeline.add_argument("logfile", help="Path to log file")
    timeline.add_argument("--bucket", default="15m", help="Bucket size: 15m, 1h, 1d, etc. (default: 15m)")
    timeline.add_argument("--format", choices=["json", "md"], default=None, help="Output format (default: json, or md if --output is set)")
    timeline.add_argument("--output", type=str, default=None, help="Write output to file (implies --format md if not specified)")

    grep = subparsers.add_parser("grep", help="Filter log lines by level and/or timestamp")
    grep.add_argument("logfile", help="Path to log file")
    grep.add_argument("--level", type=str, default=None, help="Filter by log level (INFO, WARN, ERROR, ...)")
    grep.add_argument("--since", type=str, default=None, help='Filter lines at/after timestamp, e.g. "2026-10-01 09:00"')
    grep.add_argument("--format", choices=["json", "md"], default=None, help="Output format (default: json, or md if --output is set)")
    grep.add_argument("--output", type=str, default=None, help="Write output to file (implies --format md if not specified)")

    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Default to json, unless writing a report file (then default to md).
    if args.format is None:
        args.format = "md" if args.output else "json"

    if args.command == "summary":
        result = run_summary(args.logfile)
    elif args.command == "timeline":
        result = run_timeline(args.logfile, bucket=args.bucket)
    elif args.command == "grep":
        result = run_grep(args.logfile, level=args.level, since=args.since)
    else:  # pragma: no cover - argparse restricts choices already
        parser.print_help()
        sys.exit(1)

    output = format_output(result, args.format, args.output)
    print(output)
    sys.exit(0)


if __name__ == "__main__":
    main()
