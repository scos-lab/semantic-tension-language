# API: parser

Core parsing functions for STL text and files.

**Module:** `stl_parser.parser`
**Import:** `from stl_parser import parse, parse_file`

---

## parse()

```python
parse(text: str) -> ParseResult
```

Parse STL text into structured format. Handles multi-line statements, comments, and mixed content.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | `str` | STL text to parse |

**Returns:** `ParseResult` — contains `statements`, `errors`, `warnings`, `is_valid`

**Example:**

```python
from stl_parser import parse

result = parse('[A] -> [B] ::mod(confidence=0.95, rule="causal")')
print(result.is_valid)                    # True
print(result.statements[0].source.name)   # "A"
```

---

## parse_file()

```python
parse_file(
    file_path: str,
    mode: str = "auto",
    auto_extract: bool = True
) -> ParseResult
```

Parse an STL file with automatic content extraction from mixed-content files.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_path` | `str` | — | Path to STL file |
| `mode` | `str` | `"auto"` | Extraction mode: `"auto"`, `"fenced"`, `"heuristic"`, `"strict"` |
| `auto_extract` | `bool` | `True` | Enable/disable automatic STL extraction |

**Extraction Modes:**

| Mode | Behavior |
|------|----------|
| `"auto"` | Try fenced blocks first, fall back to heuristic |
| `"fenced"` | Only extract from `` ```stl `` code fences |
| `"heuristic"` | Pattern matching to identify STL lines |
| `"strict"` | Treat entire file as pure STL |

**Returns:** `ParseResult`

**Errors:** Raises `STLFileError` (E400-E404) for file I/O issues.

**Example:**

```python
from stl_parser import parse_file

result = parse_file("knowledge_base.stl")
result = parse_file("notes.md", mode="fenced")
```
