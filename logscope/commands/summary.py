"""summary command: counts by level, top 5 error messages, first/last timestamp."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict

from logscope_core.parser import LogParser

ERROR_MESSAGE_TRUNCATE_LEN = 100
TOP_ERRORS_LIMIT = 5


def run_summary(logfile: str) -> Dict[str, Any]:
    """Run the summary analysis over `logfile` and return a result dict.

    Single pass over the stream: counts by level, top 5 error messages,
    first/last timestamp. Does not buffer the whole file in memory.
    """
    parser = LogParser(logfile)

    levels: Counter = Counter()
    error_messages: Counter = Counter()
    total_lines = 0
    first_timestamp = None
    last_timestamp = None

    for parsed in parser.stream():
        total_lines += 1
        levels[parsed.level] += 1

        if first_timestamp is None:
            first_timestamp = parsed.raw_timestamp
        last_timestamp = parsed.raw_timestamp

        if parsed.level == "ERROR":
            error_key = parsed.message[:ERROR_MESSAGE_TRUNCATE_LEN]
            error_messages[error_key] += 1

    return {
        "command": "summary",
        "file": logfile,
        "total_lines": total_lines,
        "malformed_lines": parser.malformed_count,
        "levels": dict(sorted(levels.items())),
        "first_timestamp": first_timestamp,
        "last_timestamp": last_timestamp,
        "top_errors": error_messages.most_common(TOP_ERRORS_LIMIT),
    }
