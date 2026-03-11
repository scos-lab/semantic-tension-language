# STLC Specification: CLI Query Command
# Version: 1.0.0
# Module: stl_parser.cli (extension)
# Depends: stl_parser.query, stl_parser.cli
# Status: Draft

---

## 0. Overview

Adds a `stl query` subcommand to the existing CLI, exposing the query module
(find_all, filter_statements, select, stl_pointer) to shell users, CI/CD
pipelines, and scripting workflows.

**Design Principles:**
- Thin CLI layer — all logic delegates to `query.py`
- Consistent with existing CLI conventions (Typer + Rich, `handle_error()`)
- Machine-friendly output modes (JSON, CSV) alongside human-friendly (table, STL)
- Unix-philosophy: composable with pipes and shell scripts

---

## 1. Command Signature

```
stl query <FILE> [OPTIONS]
```

### 1.1 Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `FILE`   | Path | Yes      | Path to STL file to query (must exist, readable) |

### 1.2 Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--where` | `-w` | str | None | Filter conditions (comma-separated `field=value` or `field__op=value`) |
| `--select` | `-s` | str | None | Comma-separated field names to project (e.g. `source,target,confidence`) |
| `--pointer` | `-p` | str | None | STL pointer path (e.g. `/0/source/name`). Mutually exclusive with --where/--select |
| `--format` | `-f` | str | `"table"` | Output format: `table`, `json`, `stl`, `csv` |
| `--count` | `-c` | bool | False | Only print the count of matching statements |
| `--limit` | `-l` | int | None | Maximum number of results to return |

### 1.3 Mutual Exclusivity

- `--pointer` is standalone: when used, `--where`, `--select`, `--count`, and `--limit` are ignored.
- `--count` suppresses normal output; only prints the integer count.
- `--select` and `--format table` work together (columns = selected fields).
- `--select` and `--format json` returns list of dicts with selected keys.
- `--select` and `--format csv` returns CSV with header row.

---

## 2. Where-Clause Parsing

The `--where` value is a comma-separated list of conditions.

### 2.1 Syntax

```
field=value             → equality (eq)
field__op=value         → operator lookup (gt, gte, lt, lte, ne, contains, startswith, in)
```

### 2.2 Value Typing

Reuse existing `_parse_mod_string()` logic for auto-typing:
- Quoted strings: `rule="causal"` → `"causal"`
- Floats: `confidence=0.8` → `0.8`
- Integers: `line=42` → `42`
- Booleans: `flag=true` → `True`
- Unquoted strings: `rule=causal` → `"causal"`

### 2.3 Special: `__in` Operator

For `--where "rule__in=causal|logical"`, split on `|` to produce a list:
`["causal", "logical"]`.

### 2.4 Examples

```bash
# Find statements where source is "Theory_X"
stl query data.stl --where "source=Theory_X"

# Confidence > 0.8 AND rule is "causal"
stl query data.stl -w "confidence__gt=0.8,rule=causal"

# Rule is either causal or logical
stl query data.stl -w "rule__in=causal|logical"
```

---

## 3. Select Projection

`--select` takes a comma-separated list of field names.

### 3.1 Supported Fields

All fields supported by `query.select()`:
- Special: `source`, `target`, `source_namespace`, `target_namespace`, `arrow`
- Standard modifier: `confidence`, `rule`, `time`, `domain`, etc.
- Custom modifier: any key stored in `Modifier.custom`

### 3.2 Examples

```bash
# Extract source names and confidence
stl query data.stl --select "source,confidence"

# Combined with filter
stl query data.stl -w "confidence__gte=0.8" -s "source,target,confidence"
```

---

## 4. Pointer Mode

`--pointer` provides direct scalar access via `stl_pointer()`.

### 4.1 Behaviour

- Calls `stl_pointer(result, path)` directly.
- Prints the value to stdout (one line, no Rich formatting).
- For complex objects (Statement, Anchor, Modifier), print the STL string representation.
- Exit code 0 on success, 1 on error (invalid path, out-of-range index).

### 4.2 Examples

```bash
# Get source name of first statement
stl query data.stl --pointer "/0/source/name"
# Output: Theory_X

# Get confidence of second statement
stl query data.stl -p "/1/modifiers/confidence"
# Output: 0.95
```

---

## 5. Output Formats

### 5.1 Table (default)

Rich table with columns. Without `--select`, columns are:
`#`, `Source`, `Target`, `Confidence`, `Rule`.

With `--select "source,confidence"`, columns are: `Source`, `Confidence`.

### 5.2 JSON

Without `--select`: array of statement dicts (same as `to_dict()` per statement).
With `--select`: array of `{field: value}` dicts.

Output is valid JSON, suitable for piping to `jq`.

### 5.3 STL

Calls `to_stl()` on the filtered ParseResult.
Output is valid STL text, suitable for piping to `stl validate`.

### 5.4 CSV

Without `--select`: columns are `source,target,confidence,rule`.
With `--select`: columns match the selected fields.

First row is header. Values are unquoted unless they contain commas.

### 5.5 Count Mode

`--count` prints a single integer to stdout (no table, no formatting).

---

## 6. Implementation Plan

### 6.1 Function: `_parse_where_string()`

```python
def _parse_where_string(where: str) -> dict:
    """Parse --where string into kwargs for query functions.

    Input:  "confidence__gt=0.8,rule=causal"
    Output: {"confidence__gt": 0.8, "rule": "causal"}

    Special: __in operator splits value on '|'.
    """
```

Delegates value typing to `_parse_mod_string()` internally, but preserves
the `__op` suffix in the key (unlike `_parse_mod_string` which strips it).

### 6.2 Function: `query()` (Typer command)

```python
@app.command()
def query(
    file_path: Annotated[Path, typer.Argument(...)],
    where: Annotated[Optional[str], typer.Option("--where", "-w", ...)] = None,
    select_fields: Annotated[Optional[str], typer.Option("--select", "-s", ...)] = None,
    pointer: Annotated[Optional[str], typer.Option("--pointer", "-p", ...)] = None,
    format: Annotated[str, typer.Option("--format", "-f", ...)] = "table",
    count: Annotated[bool, typer.Option("--count", "-c", ...)] = False,
    limit: Annotated[Optional[int], typer.Option("--limit", "-l", ...)] = None,
):
```

### 6.3 Flow

```
1. parse_file(file_path) → ParseResult
2. If --pointer: stl_pointer(result, pointer) → print → exit
3. Parse --where → kwargs dict
4. filter_statements(result, **kwargs) → filtered ParseResult
5. Apply --limit (slice filtered.statements)
6. If --count: print len → exit
7. If --select: select() for each field → render
8. Else: render full statements
9. Render using chosen --format
```

### 6.4 Rendering Helpers

```python
def _render_table(statements, fields, console):
    """Render a Rich table."""

def _render_json(statements, fields):
    """Render JSON array to stdout."""

def _render_csv(statements, fields):
    """Render CSV with header to stdout."""

def _render_stl(filtered_result):
    """Render STL text to stdout."""
```

---

## 7. Error Handling

| Condition | Error Code | Behaviour |
|-----------|------------|-----------|
| File parse error | (parse errors) | Print errors, exit 1 |
| Invalid --where syntax | E450 | `handle_error()`, exit 1 |
| Invalid --pointer path | E451 | `handle_error()`, exit 1 |
| Pointer index out of range | E452 | `handle_error()`, exit 1 |
| Invalid --format value | (CLI) | Typer shows usage help, exit 2 |
| No statements match | (none) | Exit 0, empty table / `[]` / `0` |

---

## 8. Test Specification

### 8.1 Unit Tests for `_parse_where_string()`

| ID | Input | Expected Output |
|----|-------|-----------------|
| T01 | `"source=Theory_X"` | `{"source": "Theory_X"}` |
| T02 | `"confidence__gt=0.8"` | `{"confidence__gt": 0.8}` |
| T03 | `"confidence__gt=0.8,rule=causal"` | `{"confidence__gt": 0.8, "rule": "causal"}` |
| T04 | `"rule__in=causal\|logical"` | `{"rule__in": ["causal", "logical"]}` |
| T05 | `""` (empty) | `{}` |
| T06 | `"confidence=0.95,source=A"` | `{"confidence": 0.95, "source": "A"}` |

### 8.2 CLI Integration Tests (via `typer.testing.CliRunner`)

| ID | Command | Assertion |
|----|---------|-----------|
| T10 | `query data.stl` | Exit 0, table with all statements |
| T11 | `query data.stl -w "source=Theory_X"` | Exit 0, only Theory_X rows |
| T12 | `query data.stl -w "confidence__gt=0.8"` | Exit 0, filtered rows |
| T13 | `query data.stl -s "source,confidence"` | Exit 0, only 2 columns |
| T14 | `query data.stl -w "source=Theory_X" -c` | Exit 0, stdout contains "2" |
| T15 | `query data.stl -p "/0/source/name"` | Exit 0, stdout contains "Theory_X" |
| T16 | `query data.stl -p "/99/source/name"` | Exit 1, error message |
| T17 | `query data.stl -f json` | Exit 0, valid JSON array |
| T18 | `query data.stl -f stl` | Exit 0, valid STL text |
| T19 | `query data.stl -f csv` | Exit 0, CSV with header |
| T20 | `query data.stl -w "source=Nonexistent"` | Exit 0, empty result |
| T21 | `query data.stl -w "confidence__gte=0.8" -l 1` | Exit 0, exactly 1 result |
| T22 | `query data.stl -w "confidence__gte=0.8" -f json -s "source"` | Exit 0, JSON with only source field |
| T23 | `query invalid.stl` | Exit 1, parse errors shown |

---

## 9. Acceptance Criteria

1. `stl query` appears in `stl --help` output.
2. All 6 options work independently and in combination.
3. `--pointer` mode returns exact scalar values.
4. `--format json` output is valid JSON parseable by `json.loads()`.
5. `--format csv` output is valid CSV with header row.
6. `--count` returns integer only (no Rich markup).
7. Exit code 0 for success (including empty results), 1 for errors.
8. No new dependencies (uses existing Typer, Rich, json, csv stdlib).
9. All 23+ tests pass.
10. Existing CLI tests remain green.
