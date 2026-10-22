"""Output formatting: render command result dicts as JSON or Markdown,
and optionally write the result to a report file.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

MAX_BAR_WIDTH = 50
MAX_MARKDOWN_GREP_LINES = 100


def format_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, indent=2, default=str)


def _render_summary_md(data: Dict[str, Any]) -> str:
    lines = ["## Summary", ""]
    lines.append(f"**File:** `{data['file']}`")
    lines.append(f"**Total lines:** {data['total_lines']}")
    lines.append(f"**Malformed lines:** {data['malformed_lines']}")
    lines.append(f"**First timestamp:** {data['first_timestamp']}")
    lines.append(f"**Last timestamp:** {data['last_timestamp']}")
    lines.append("")

    lines.append("### Counts by Level")
    lines.append("")
    lines.append("| Level | Count |")
    lines.append("|-------|-------|")
    for level, count in data["levels"].items():
        lines.append(f"| {level} | {count} |")
    lines.append("")

    lines.append("### Top 5 Error Messages")
    lines.append("")
    if data["top_errors"]:
        for i, (message, count) in enumerate(data["top_errors"], 1):
            lines.append(f"{i}. `{message}` ({count} occurrences)")
    else:
        lines.append("_No errors found._")
    lines.append("")
    return "\n".join(lines)


def _render_timeline_md(data: Dict[str, Any]) -> str:
    lines = ["## Timeline", ""]
    lines.append(f"**File:** `{data['file']}`")
    lines.append(f"**Bucket size:** {data['bucket']}")
    lines.append(f"**Total errors:** {data['total_errors']}")
    lines.append(f"**Malformed lines:** {data['malformed_lines']}")
    lines.append("")

    lines.append("### Error Count by Time Bucket")
    lines.append("")
    if data["timeline"]:
        lines.append("```")
        max_count = max(count for _, count in data["timeline"]) or 1
        for bucket_label, count in data["timeline"]:
            bar_len = max(1, min(MAX_BAR_WIDTH, round(count / max_count * MAX_BAR_WIDTH)))
            bar = "█" * bar_len
            lines.append(f"{bucket_label}  {bar} {count}")
        lines.append("```")
    else:
        lines.append("_No errors found._")
    lines.append("")
    return "\n".join(lines)


def _render_grep_md(data: Dict[str, Any]) -> str:
    lines = ["## Grep Results", ""]
    lines.append(f"**File:** `{data['file']}`")
    level = data["filters"].get("level") or "(any)"
    since = data["filters"].get("since") or "(none)"
    lines.append(f"**Level filter:** {level}")
    lines.append(f"**Since filter:** {since}")
    lines.append(f"**Matched lines:** {data['matched_lines']}")
    lines.append(f"**Malformed lines:** {data['malformed_lines']}")
    if data["truncated"]:
        lines.append(
            f"**Note:** results truncated; showing first "
            f"{len(data['filtered_lines'])} of {data['matched_lines']} matches."
        )
    lines.append("")

    lines.append("### Filtered Lines")
    lines.append("")
    shown = data["filtered_lines"][:MAX_MARKDOWN_GREP_LINES]
    if shown:
        lines.append("```")
        lines.extend(shown)
        if len(data["filtered_lines"]) > MAX_MARKDOWN_GREP_LINES:
            lines.append(
                f"... and {len(data['filtered_lines']) - MAX_MARKDOWN_GREP_LINES} more lines"
            )
        lines.append("```")
    else:
        lines.append("_No matching lines._")
    lines.append("")
    return "\n".join(lines)


_MD_RENDERERS = {
    "summary": _render_summary_md,
    "timeline": _render_timeline_md,
    "grep": _render_grep_md,
}


def format_markdown(data: Dict[str, Any], title: str = "logscope Report") -> str:
    generated_at = datetime.now(timezone.utc).isoformat()
    header = f"# {title}\n\n**Generated:** {generated_at}\n\n"

    command = data.get("command")
    renderer = _MD_RENDERERS.get(command)
    if renderer is None:
        # Unknown command shape: fall back to a raw JSON code block so
        # nothing is silently lost.
        body = "```json\n" + format_json(data) + "\n```\n"
    else:
        body = renderer(data)

    return header + body


def format_output(
    data: Dict[str, Any],
    format_type: str = "json",
    output_file: Optional[str] = None,
) -> str:
    """Render `data` as JSON or Markdown and optionally write it to a file.

    Returns the rendered string (also written to `output_file` if given).
    """
    if format_type == "md":
        rendered = format_markdown(data)
    else:
        rendered = format_json(data)

    if output_file:
        Path(output_file).write_text(rendered, encoding="utf-8")
        print(f"Report written to: {output_file}", file=sys.stderr)

    return rendered
