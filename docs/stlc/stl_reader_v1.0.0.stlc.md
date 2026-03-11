# STLC Specification: STL Reader (Streaming)

> **Module:** `stl_parser.reader`
> **Version:** 1.0.0
> **Priority:** P2-b (complement to Emitter)
> **Depends on:** `parser.parse`, `query._resolve_field`, `query._match_value`, `_utils.merge_multiline_statements`, `errors`
> **STLC Compiler Target:** Python 3.9+

---

## 1. Purpose

Provide a **streaming, memory-efficient** reader for STL files and streams. This is the read-side complement to `STLEmitter` (write-side), completing the streaming I/O loop.

### Design Principles

- **Generator-based**: Yield `Statement` objects one at a time — never materialize full list in memory
- **Emitter-compatible**: Seamlessly reads files produced by `STLEmitter`
- **Query-integrated**: Built-in `where` filtering reuses the Query module's field resolution and matching
- **Graceful degradation**: Unparseable lines are skipped by default (matching Emitter's append-only philosophy)
- **Minimal surface**: Two public entry points (`stream_parse` function + `STLReader` class)

---

## 2. Data Models

### 2.1 ReaderStats

```
class ReaderStats(BaseModel):
    lines_processed: int = 0
    statements_yielded: int = 0
    errors_skipped: int = 0
    comments_seen: int = 0
    blank_lines: int = 0
```

Read-only running statistics. Updated as the generator advances.

---

## 3. Public API

### 3.1 `stream_parse(source, *, where, on_error) -> Generator[Statement]`

**Signature:**
```python
def stream_parse(
    source: Union[str, Path, TextIO, Iterable[str]],
    *,
    where: Optional[Dict[str, Any]] = None,
    on_error: Literal["skip", "raise"] = "skip",
) -> Generator[Statement, None, None]:
```

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | `str \| Path \| TextIO \| Iterable[str]` | required | File path, open file handle, StringIO, or iterable of line strings |
| `where` | `Dict[str, Any] \| None` | `None` | Django-style filter criteria (reuses Query module matching) |
| `on_error` | `"skip" \| "raise"` | `"skip"` | Error handling: skip bad lines or raise STLReaderError |

**Source resolution:**
1. If `str` or `Path` and points to existing file → open and read line-by-line
2. If `TextIO` (has `.readline`) → read line-by-line from stream
3. If `Iterable[str]` → iterate directly

**Yields:** `Statement` objects, one per successfully parsed STL statement.

**Behavior:**
- Reads lines one at a time (never `f.read()` or `f.readlines()`)
- Merges multi-line statements (tracks parenthesis depth for unclosed `::mod(`)
- Skips comment lines (`# ...`) and blank lines
- If `where` is provided, only yields statements matching the criteria
- If `on_error="skip"`, silently skips unparseable lines
- If `on_error="raise"`, raises `STLReaderError` on first unparseable line

### 3.2 `STLReader` class

**Signature:**
```python
class STLReader:
    def __init__(
        self,
        source: Union[str, Path, TextIO],
        *,
        where: Optional[Dict[str, Any]] = None,
        on_error: Literal["skip", "raise"] = "skip",
        tail: bool = False,
        tail_interval: float = 0.5,
    ) -> None: ...

    def __enter__(self) -> "STLReader": ...
    def __exit__(self, *exc) -> None: ...
    def __iter__(self) -> Generator[Statement, None, None]: ...

    @property
    def stats(self) -> ReaderStats: ...

    def close(self) -> None: ...
    def read_all(self) -> ParseResult: ...
```

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | `str \| Path \| TextIO` | required | File path or open stream |
| `where` | `Dict[str, Any] \| None` | `None` | Filter criteria |
| `on_error` | `"skip" \| "raise"` | `"skip"` | Error handling mode |
| `tail` | `bool` | `False` | If True, watch file for new content (like `tail -f`) |
| `tail_interval` | `float` | `0.5` | Seconds between file polls in tail mode |

**Tail mode behavior:**
- Only available for file paths (not streams)
- After reaching EOF, sleeps for `tail_interval` seconds then checks for new content
- Yields new statements as they appear (e.g., from a concurrent STLEmitter)
- Exits when: context manager exits, `close()` called, or `KeyboardInterrupt`
- Uses file position tracking (`f.tell()` / `f.seek()`) — no re-reading

**`read_all()` method:**
- Convenience: consumes entire generator and returns a `ParseResult`
- For when you want streaming filtering but final batch result
- Sets `ParseResult.is_valid = True` (errors were already handled by on_error policy)

**`stats` property:**
- Returns current `ReaderStats` snapshot
- Updates as iteration progresses

---

## 4. Internal Helpers

### 4.1 `_line_iter(source) -> Generator[Tuple[int, str]]`

Resolves source type and yields `(line_number, line_text)` pairs.

- `str`/`Path` → `open(path, "r", encoding="utf-8")`, yield lines with `enumerate(f, 1)`
- `TextIO` → `enumerate(source, 1)`
- `Iterable[str]` → `enumerate(source, 1)`

### 4.2 `_merge_continuation(line_iter) -> Generator[Tuple[int, str]]`

Buffers multi-line statements. Logic:
- Track parenthesis depth: increment on `(`, decrement on `)`
- If depth > 0 at end of line, buffer and continue to next line
- When depth returns to 0, yield merged line with start line number
- Max continuation: 20 lines (safety limit → raise error if exceeded)

### 4.3 `_parse_single_line(line, line_number) -> Statement`

Parse one complete STL line into a Statement:
1. Call `parse(line)` (existing parser)
2. If result has exactly 1 statement → return it
3. If result has errors or 0 statements → raise `STLReaderError`

### 4.4 `_matches_where(stmt, where) -> bool`

Reuse query module internals:
- Import `_resolve_field` and `_match_value` from `query.py`
- For each key in `where`, resolve the field on the statement, then match

---

## 5. Error Handling

### 5.1 Error Codes

| Code | Name | When |
|------|------|------|
| E960 | `E960_READER_SOURCE_ERROR` | Cannot open/read source (file not found, permission denied) |
| E961 | `E961_READER_PARSE_ERROR` | Line cannot be parsed as valid STL (when on_error="raise") |
| E962 | `E962_READER_CONTINUATION_OVERFLOW` | Multi-line statement exceeds 20-line continuation limit |

### 5.2 Exception Class

```python
class STLReaderError(STLError):
    """Raised by reader module on unrecoverable errors."""
    def __init__(self, *, code: ErrorCode, message: str, line_number: Optional[int] = None):
        super().__init__(code=code, message=message)
        self.line_number = line_number
```

---

## 6. CLI Extension

### 6.1 `stl stream` command

**Not included in v1.0.0.** The reader is designed as a library API. CLI streaming (e.g., `stl stream --tail agent.stl --where "confidence__gt=0.8"`) can be added later if needed.

---

## 7. Integration Points

### 7.1 Emitter → Reader loop

```python
# Writer (one process/thread)
with STLEmitter(log_path="events.stl", namespace="Agent") as emitter:
    emitter.emit("[Observe]", "[Act]", confidence=0.9)
    emitter.emit("[Act]", "[Result]", confidence=0.85)

# Reader (same or different process)
with STLReader("events.stl") as reader:
    for stmt in reader:
        print(f"{stmt.source.name} → {stmt.target.name}: {stmt.modifiers.confidence}")
```

### 7.2 Tail mode (real-time monitoring)

```python
# Reader watches file as Emitter appends
with STLReader("events.stl", tail=True) as reader:
    for stmt in reader:  # Blocks waiting for new content
        if stmt.modifiers and stmt.modifiers.confidence and stmt.modifiers.confidence < 0.5:
            alert(f"Low confidence: {stmt}")
```

### 7.3 Filtered streaming into ParseResult

```python
# Stream-filter a large file, then use batch APIs on the result
with STLReader("huge_kb.stl", where={"rule": "causal", "confidence__gt": 0.7}) as reader:
    result = reader.read_all()  # Only matching statements materialized

graph = STLGraph(result)  # Analyze filtered subset
```

---

## 8. Test Specifications

### 8.1 stream_parse — Core Functionality

| # | Test Name | Input | Expected |
|---|-----------|-------|----------|
| T01 | `test_stream_parse_file` | File with 3 statements | Generator yields 3 Statement objects |
| T02 | `test_stream_parse_stringio` | StringIO with 2 statements | Yields 2 Statement objects |
| T03 | `test_stream_parse_iterable` | List of line strings | Yields correct statements |
| T04 | `test_stream_parse_filepath_string` | String path | Opens file, yields statements |
| T05 | `test_stream_parse_path_object` | `Path` object | Opens file, yields statements |
| T06 | `test_stream_parse_empty_file` | Empty file | Yields nothing, no error |
| T07 | `test_stream_parse_comments_skipped` | File with `# comment` lines | Comments not yielded |
| T08 | `test_stream_parse_blank_lines_skipped` | File with blank/whitespace lines | Blanks not yielded |
| T09 | `test_stream_parse_mixed_content` | Statements + comments + blanks | Only statements yielded |

### 8.2 stream_parse — Multi-line Merging

| # | Test Name | Input | Expected |
|---|-----------|-------|----------|
| T10 | `test_multiline_modifier` | Statement split across 2 lines (`::mod(\n  confidence=0.9)`) | Merged and parsed as single statement |
| T11 | `test_multiline_deep_nesting` | Statement split across 3+ lines | Merged correctly |
| T12 | `test_multiline_overflow` | 25-line continuation | Raises E962 (on_error="raise") or skips (on_error="skip") |

### 8.3 stream_parse — Where Filtering

| # | Test Name | Input | Expected |
|---|-----------|-------|----------|
| T13 | `test_where_exact_match` | `where={"source": "Theory_X"}` | Only matching statements |
| T14 | `test_where_gt_operator` | `where={"confidence__gt": 0.8}` | Only high-confidence |
| T15 | `test_where_multiple_conditions` | `where={"rule": "causal", "confidence__gte": 0.5}` | AND logic |
| T16 | `test_where_no_matches` | `where={"source": "Nonexistent"}` | Yields nothing |

### 8.4 stream_parse — Error Handling

| # | Test Name | Input | Expected |
|---|-----------|-------|----------|
| T17 | `test_on_error_skip` | File with 1 valid + 1 invalid line | Yields 1 statement, no exception |
| T18 | `test_on_error_raise` | File with invalid line, `on_error="raise"` | Raises STLReaderError with E961 |
| T19 | `test_source_not_found` | Non-existent file path | Raises STLReaderError with E960 |

### 8.5 STLReader — Context Manager

| # | Test Name | Input | Expected |
|---|-----------|-------|----------|
| T20 | `test_reader_context_manager` | `with STLReader(path) as r:` | File opened and closed properly |
| T21 | `test_reader_iter` | `for stmt in reader:` | Yields statements |
| T22 | `test_reader_stats` | File with 5 stmts, 2 comments, 1 error | `stats` reflects all counts |
| T23 | `test_reader_read_all` | 3 statements | Returns ParseResult with 3 statements |
| T24 | `test_reader_read_all_with_where` | 5 stmts, `where={"rule": "causal"}` | ParseResult with only causal statements |
| T25 | `test_reader_close_explicit` | Call `reader.close()` | File handle released |

### 8.6 STLReader — Tail Mode

| # | Test Name | Input | Expected |
|---|-----------|-------|----------|
| T26 | `test_tail_reads_new_content` | Write 2 lines, start tail reader, write 2 more | Reader yields all 4 |
| T27 | `test_tail_only_for_files` | `STLReader(StringIO(), tail=True)` | Raises ValueError |
| T28 | `test_tail_interval_custom` | `tail_interval=0.1` | Polls at specified interval |

### 8.7 Emitter → Reader Integration

| # | Test Name | Input | Expected |
|---|-----------|-------|----------|
| T29 | `test_emitter_reader_roundtrip` | Emit 5 statements, read back | All 5 recovered with correct data |
| T30 | `test_emitter_reader_with_namespace` | Emit with `namespace="Agent"` | Reader yields namespaced anchors |
| T31 | `test_emitter_reader_with_comments` | Emit with `comment()` and `section()` | Reader skips comments, yields statements |
| T32 | `test_emitter_reader_with_timestamp` | Emit with `auto_timestamp=True` | Reader yields statements with timestamp field |

### 8.8 Memory Efficiency

| # | Test Name | Input | Expected |
|---|-----------|-------|----------|
| T33 | `test_large_file_constant_memory` | Generate 1000-statement file, stream-parse | Only 1 Statement in memory at a time (verified by not collecting into list) |

### 8.9 Edge Cases

| # | Test Name | Input | Expected |
|---|-----------|-------|----------|
| T34 | `test_unicode_statements` | Chinese/Arabic anchor names | Parsed correctly |
| T35 | `test_namespaced_anchors` | `[NS:Name]` format | Parsed correctly |

---

## 9. File Layout

```
parser/stl_parser/reader.py      # New module (~150 lines)
parser/tests/test_reader.py      # New test file (~35 tests)
```

---

## 10. Export Changes

### `__init__.py`

```python
# Streaming I/O
from .reader import stream_parse, STLReader, ReaderStats
```

Add to `__all__`:
```python
"stream_parse",
"STLReader",
"ReaderStats",
```

### Version bump

```python
__version__ = "1.7.0"
```

---

## 11. Design Decisions

### Why generator, not async?

The codebase has zero async patterns. Adding `asyncio` would be a paradigm shift for one module. Generators cover the primary use case (memory-efficient iteration) without forcing async on consumers.

### Why reuse `parse()` internally?

Each line is parsed by calling `parse(line)` which goes through the full Lark grammar. This is intentional:
- Maintains single source of truth for parsing logic
- Handles all edge cases (Unicode, namespaces, modifier parsing)
- Performance is acceptable: Lark parsing of single lines is fast (~0.1ms per statement)

### Why not extend `parse_file()`?

`parse_file()` has extraction logic (fenced blocks, Markdown) that doesn't apply to pure STL streams. A separate module keeps responsibilities clean. Users who need extraction + streaming can pre-process with `auto_extract_stl()` then pipe to `stream_parse()`.

### Tail mode scope

Tail mode is intentionally simple (polling-based). File system watchers (`inotify`, `FSEvents`) would add platform-specific dependencies. Polling with configurable interval is portable and sufficient for the primary use case (monitoring Emitter output).

---

**End of STLC Specification**

**Spec ID:** `stl_reader_v1.0.0`
**Author:** Syn-claude
**Date:** 2026-02-13
