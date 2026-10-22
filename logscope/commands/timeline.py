"""timeline command: error count per time bucket, as data for a text bar chart."""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict

from logscope_core.parser import LogParser

BUCKET_PATTERN = re.compile(r"^(\d+)([mhd])$")
UNIT_SECONDS = {"m": 60, "h": 3600, "d": 86400}


def parse_bucket_size(bucket: str) -> int:
    """Parse a bucket spec like '15m', '1h', '1d' into a number of seconds.

    Raises ValueError on an invalid format (caller decides how to report it).
    """
    match = BUCKET_PATTERN.match(bucket.strip())
    if not match:
        raise ValueError(f"Invalid bucket format: {bucket!r}. Use e.g. 15m, 1h, 1d")
    value, unit = int(match.group(1)), match.group(2)
    if value <= 0:
        raise ValueError(f"Invalid bucket format: {bucket!r}. Value must be positive")
    return value * UNIT_SECONDS[unit]


def run_timeline(logfile: str, bucket: str = "15m") -> Dict[str, Any]:
    """Run the timeline analysis: error count per time bucket.

    Only ERROR-level lines are bucketed. Buckets are keyed by their start
    time (floor-aligned to bucket_secs), rendered as ISO-8601 UTC strings.
    """
    try:
        bucket_secs = parse_bucket_size(bucket)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    parser = LogParser(logfile)
    buckets: Dict[int, int] = defaultdict(int)

    for parsed in parser.stream():
        if parsed.level != "ERROR":
            continue
        epoch = parsed.timestamp.timestamp()
        bucket_key = int(epoch // bucket_secs) * bucket_secs
        buckets[bucket_key] += 1

    timeline = [
        (datetime.fromtimestamp(key, tz=timezone.utc).isoformat(), count)
        for key, count in sorted(buckets.items())
    ]

    return {
        "command": "timeline",
        "file": logfile,
        "bucket": bucket,
        "malformed_lines": parser.malformed_count,
        "timeline": timeline,
        "total_errors": sum(buckets.values()),
    }
