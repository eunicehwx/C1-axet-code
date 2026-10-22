# logscope — Implementation Plan

Status: DRAFT — for review before any code is written.

## Phase 1: Project Skeleton
- `logscope/` package: `parser.py`, `commands/summary.py`, `commands/timeline.py`, `commands/grep.py`, `formatter.py`, `cli.py` (argparse entry point), `__main__.py`.
- Define the log line contract (ISO-8601 timestamp, level token, message) and the `ParsedLine` / `ParseError` data shapes shared by all commands.

## Phase 2: Streaming Parser (`parser.py`)
- Regex-based line parser: `(timestamp) (LEVEL) (message)`.
- Generator function `stream(path)` that opens the file and `yield`s one parsed record at a time — never reads the whole file into a list.
- On regex mismatch: increment `malformed_count`, skip the line, continue (never raise).
- Normalize timestamps to timezone-aware UTC `datetime` once per line (reused by all three commands).

## Phase 3: `summary` command
- Single pass over the stream: `Counter` for levels, `Counter` for error messages (first 100 chars), track running `first_ts`/`last_ts` without storing every timestamp.
- Emit: total lines, malformed count, level counts, first/last timestamp, top-5 errors.

## Phase 4: `timeline` command
- Parse `--bucket` (`<int>[m|h|d]`) into seconds; reject invalid formats with exit code 1.
- For each ERROR line: bucket key = `floor(epoch / bucket_secs) * bucket_secs`; accumulate counts in a `defaultdict(int)` keyed by bucket start (sorted at the end, not buffered as raw lines).
- Render as text bar chart (`█` repeated proportional to count) in the Markdown path; raw counts in JSON.

## Phase 5: `grep` command
- Parse `--since` accepting both `"YYYY-MM-DD HH:MM"` and ISO-8601/`Z` forms; exit 1 with a helpful message on bad format.
- Stream, apply `--level` and `--since` filters inline (no buffering beyond the result set).
- Cap stored results (e.g. 10k lines) with a `truncated` flag; always report `matched_count` (true count) separately from lines actually kept.

## Phase 6: Output layer (`formatter.py`)
- `--format json` (default): single `json.dumps` of a structured result dict (command, file, stats, data, malformed_lines).
- `--format md`: render tables/sections/bar-chart via templated Markdown; if `--output <file>` given, write the file and print only a confirmation to stdout/stderr.
- Auto-select `md` when `--output` is passed without explicit `--format`.

## Phase 7: CLI wiring (`cli.py`)
- `argparse` subcommands: `summary`, `timeline`, `grep`, each with its own flags plus shared `--format`/`--output`.
- Centralized error handling: file-not-found, bad `--bucket`, bad `--since` → print to stderr, `sys.exit(1)`; normal completion → `sys.exit(0)`.

## Phase 8: Test Suite
- Fixtures: small mixed-level log, log with interspersed malformed lines, large synthetic log (~100MB generated on the fly, not committed) to verify constant memory/streaming behavior.
- Unit tests per command (counts, top-5 ordering, bucket math, filter combinations, truncation flag).
- Format tests: JSON schema shape, Markdown contains expected sections/tables, `--output` writes file and auto-switches format.
- Edge cases: empty file, all-malformed file, no ERROR lines (timeline/summary), `--since` beyond last timestamp (empty grep result).

## Phase 9: Performance Validation
- Run `summary`/`timeline`/`grep` against a 100MB generated log; assert peak memory stays roughly constant (e.g. via `tracemalloc` or `/usr/bin/time -v`) and wall-clock stays reasonable.

## Phase 10: Docs
- README with install/usage examples (mirrors SPEC.md commands) and sample output for each format.

## Open Questions
- Exact timestamp formats accepted by `--since` (ISO 8601 vs. space-separated, timezone handling).
- Exact bucket-size units supported by `--bucket` beyond `15m`.
- Report file naming/path convention when `--format md` is used without an explicit output path.
