"""Streaming log parser.

Parses log lines of the form:

    2026-10-01T08:00:00Z INFO Application started

without ever loading the whole file into memory, and never raises on
malformed input -- malformed lines are counted and skipped.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional


LOG_PATTERN = re.compile(
    r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)"
    r"\s+(\S+)"  # level token
    r"\s+(.*)"  # message (rest of line)
)


@dataclass(frozen=True)
class ParsedLine:
    """A single successfully-parsed log line."""

    raw_timestamp: str
    level: str
    message: str
    timestamp: datetime

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.raw_timestamp} {self.level} {self.message}"


def parse_timestamp(raw: str) -> Optional[datetime]:
    """Parse an ISO-8601 timestamp (with optional Z/offset) into an aware
    UTC datetime. Returns None if it cannot be parsed."""
    try:
        normalized = raw.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


class LogParser:
    """Streaming, memory-bounded log file parser.

    Usage:
        parser = LogParser(path)
        for parsed in parser.stream():
            ...
        parser.malformed_count  # lines skipped because they didn't match
    """

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.malformed_count = 0

    def parse_line(self, line: str) -> Optional[ParsedLine]:
        """Parse a single raw line. Returns None (and bumps the malformed
        counter) if the line is blank or does not match the expected
        format, or if its timestamp cannot be parsed."""
        line = line.rstrip("\r\n")
        if not line.strip():
            return None

        match = LOG_PATTERN.match(line)
        if not match:
            self.malformed_count += 1
            return None

        raw_timestamp, level, message = match.groups()
        timestamp = parse_timestamp(raw_timestamp)
        if timestamp is None:
            self.malformed_count += 1
            return None

        return ParsedLine(
            raw_timestamp=raw_timestamp,
            level=level.upper(),
            message=message,
            timestamp=timestamp,
        )

    def stream(self) -> Iterator[ParsedLine]:
        """Stream parsed lines from the file one at a time.

        On I/O errors (missing file, permission, etc.) prints a message to
        stderr and exits the process with status 1, matching the tool-wide
        error-handling convention.
        """
        try:
            with open(self.filepath, "r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    parsed = self.parse_line(line)
                    if parsed is not None:
                        yield parsed
        except FileNotFoundError:
            print(f"Error: File not found: {self.filepath}", file=sys.stderr)
            sys.exit(1)
        except OSError as exc:
            print(f"Error reading file: {exc}", file=sys.stderr)
            sys.exit(1)
