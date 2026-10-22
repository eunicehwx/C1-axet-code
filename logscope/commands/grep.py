"""grep command: filter log lines by level and/or a --since timestamp."""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Any, Dict, Optional

from logscope_core.parser import LogParser, parse_timestamp

DEFAULT_LINE_LIMIT = 10_000


def parse_since(value: str) -> datetime:
    """Parse a --since value, accepting both space-separated
    ('2026-10-01 09:00') and ISO-8601 ('2026-10-01T09:00:00Z') forms.

    Raises ValueError on an unparseable value.
    """
    normalized = value.strip()
    if "T" not in normalized:
        normalized = normalized.replace(" ", "T", 1)
    dt = parse_timestamp(normalized)
    if dt is None:
        raise ValueError(
            f"Invalid timestamp: {value!r}. Use e.g. '2026-10-01 09:00' or "
            "'2026-10-01T09:00:00Z'"
        )
    return dt


def run_grep(
    logfile: str,
    level: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = DEFAULT_LINE_LIMIT,
) -> Dict[str, Any]:
    """Stream `logfile`, filtering by level and/or since-timestamp.

    Results are capped at `limit` lines to bound memory; `matched_lines`
    always reports the true match count and `truncated` flags whether the
    returned lines were capped.
    """
    since_dt = None
    if since:
        try:
            since_dt = parse_since(since)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    level_filter = level.upper() if level else None

    parser = LogParser(logfile)
    filtered_lines = []
    matched_count = 0

    for parsed in parser.stream():
        if level_filter and parsed.level != level_filter:
            continue
        if since_dt and parsed.timestamp < since_dt:
            continue

        matched_count += 1
        if len(filtered_lines) < limit:
            filtered_lines.append(str(parsed))

    return {
        "command": "grep",
        "file": logfile,
        "filters": {"level": level, "since": since},
        "malformed_lines": parser.malformed_count,
        "matched_lines": matched_count,
        "filtered_lines": filtered_lines,
        "truncated": matched_count > limit,
    }
