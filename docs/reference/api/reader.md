# API: reader

Streaming input for STL files.

**Module:** `stl_parser.reader`
**Import:** `from stl_parser import stream_parse, STLReader, ReaderStats`

---

## stream_parse()

```python
stream_parse(
    source: Union[str, Path, TextIO, Iterable[str]],
    *,
    where: Optional[Dict[str, Any]] = None,
    on_error: Literal["skip", "raise"] = "skip"
) -> Generator[Statement, None, None]
```

Memory-efficient generator that yields statements one at a time.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | `str`, `Path`, `TextIO`, `Iterable[str]` | — | File path, file handle, StringIO, or line iterable |
| `where` | `dict` | `None` | Filter conditions (same operators as `find()`) |
| `on_error` | `str` | `"skip"` | `"skip"` silently skips bad lines; `"raise"` raises immediately |

**Yields:** `Statement` objects.

**Raises:** `STLReaderError` (E960-E962)

**Example:**

```python
for stmt in stream_parse("data.stl", where={"confidence__gte": 0.8}):
    print(stmt)
```

---

## STLReader

Context manager with statistics and tail mode.

```python
STLReader(
    source: Union[str, Path, TextIO],
    *,
    where: Optional[Dict[str, Any]] = None,
    on_error: Literal["skip", "raise"] = "skip",
    tail: bool = False,
    tail_interval: float = 0.5
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | `str`, `Path`, `TextIO` | — | File path or file handle |
| `where` | `dict` | `None` | Filter conditions |
| `on_error` | `str` | `"skip"` | Error handling mode |
| `tail` | `bool` | `False` | Enable tail mode (like `tail -f`) |
| `tail_interval` | `float` | `0.5` | Poll interval in seconds for tail mode |

**Methods:**

| Method | Return Type | Description |
|--------|------------|-------------|
| `__iter__()` | `Generator[Statement]` | Iterate over statements |
| `read_all()` | `ParseResult` | Consume generator into a `ParseResult` |
| `close()` | `None` | Close file handles |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `stats` | `ReaderStats` | Read-only statistics snapshot |

**Example:**

```python
with STLReader("events.stl", where={"rule": "causal"}) as reader:
    for stmt in reader:
        print(stmt)
    print(reader.stats)
```

---

## ReaderStats

```python
class ReaderStats(BaseModel):
    lines_processed: int = 0
    statements_yielded: int = 0
    errors_skipped: int = 0
    comments_seen: int = 0
    blank_lines: int = 0
```
