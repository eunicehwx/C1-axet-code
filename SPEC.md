# logscope — Specification

## 1. Scenario

The operations team wants a quick tool to summarise application logs after an
incident, without opening a dashboard.

## 2. Purpose

`logscope` is a command-line tool that parses application log files and
produces incident-ready summaries, timelines, and filtered views, in either
machine-readable (JSON) or human-readable (Markdown) form.

## 3. Commands

### 3.1 `logscope summary app.log`

Summarises the log file:
- Counts of lines by level (INFO / WARN / ERROR, etc.)
- Top 5 most frequent error messages
- First and last timestamp seen in the file

### 3.2 `logscope timeline app.log --bucket 15m`

Buckets errors over time and renders them as a text bar chart:
- `--bucket` sets the bucket size (e.g. `15m`, `1h`, `1d`)
- Output: error count per time bucket, shown as a text bar chart

### 3.3 `logscope grep app.log --level ERROR --since "2026-10-01 09:00"`

Returns filtered log lines:
- `--level` filters by log level (INFO / WARN / ERROR / etc.)
- `--since` filters lines at or after the given timestamp

## 4. Output Formats

Every command supports:

```
--format json|md
```

- `json` (default): structured output for scripting/automation.
- `md`: human-readable Markdown; when used with an output path, writes a
  report file instead of printing to stdout.

## 5. Non-Functional Requirements

### Memory / Performance
- Must handle a 100 MB log file without loading it fully into memory
  (stream / process line-by-line).

### Robustness
- Malformed lines are counted, not fatal: the tool skips them and continues
  processing.
- Malformed line count is included in command output.
- The tool never crashes due to malformed input.

## 6. Open Items

- Exact timestamp formats accepted by `--since` (ISO 8601 vs. space-separated,
  timezone handling).
- Exact bucket-size units supported by `--bucket` beyond `15m`.
- Report file naming/path convention when `--format md` is used without an
  explicit output path.
