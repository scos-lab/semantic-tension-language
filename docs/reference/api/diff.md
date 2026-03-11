# API: diff

Semantic diff and patch for STL documents.

**Module:** `stl_parser.diff`
**Import:** `from stl_parser import stl_diff, stl_patch, diff_to_text, diff_to_dict, STLDiff`

---

## stl_diff()

```python
stl_diff(
    a: ParseResult,
    b: ParseResult,
    *,
    ignore_order: bool = True
) -> STLDiff
```

Compute semantic diff between two documents.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `a` | `ParseResult` | — | Source document (before) |
| `b` | `ParseResult` | — | Target document (after) |
| `ignore_order` | `bool` | `True` | If True, reordering doesn't generate diffs |

**Returns:** `STLDiff`

---

## stl_patch()

```python
stl_patch(doc: ParseResult, diff: STLDiff) -> ParseResult
```

Apply a diff to produce a new document.

**Raises:** `STLDiffError` (E950-E953) if patch cannot be applied.

---

## diff_to_text()

```python
diff_to_text(diff: STLDiff) -> str
```

Render diff as human-readable text with `+`/`-`/`~` markers.

---

## diff_to_dict()

```python
diff_to_dict(diff: STLDiff) -> dict
```

Serialize diff as a JSON-compatible dict with `"entries"` and `"summary"` keys.

---

## STLDiff

```python
class STLDiff(BaseModel):
    entries: List[DiffEntry] = []
    summary: DiffSummary

    @property
    def is_empty(self) -> bool        # True if documents identical
    @property
    def added(self) -> List[DiffEntry]
    @property
    def removed(self) -> List[DiffEntry]
    @property
    def modified(self) -> List[DiffEntry]
```

## DiffSummary

```python
class DiffSummary(BaseModel):
    added: int = 0
    removed: int = 0
    modified: int = 0
    unchanged: int = 0
    total_a: int = 0
    total_b: int = 0
```

## DiffEntry

```python
class DiffEntry(BaseModel):
    op: DiffOp                                  # ADD, REMOVE, or MODIFY
    key: str                                    # Human-readable key: "[A] -> [B]"
    statement_a: Optional[Statement] = None     # From doc A
    statement_b: Optional[Statement] = None     # From doc B
    index_a: Optional[int] = None
    index_b: Optional[int] = None
    modifier_changes: List[ModifierChange] = []
```

## DiffOp

```python
class DiffOp(str, Enum):
    ADD = "add"
    REMOVE = "remove"
    MODIFY = "modify"
```
