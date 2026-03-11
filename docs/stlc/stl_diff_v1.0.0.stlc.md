# STLC Specification: STL Diff / Patch Module
# Version: 1.0.0
# Module: stl_parser.diff
# Depends: stl_parser.models, stl_parser.errors
# Status: Draft

---

## 0. Overview

Computes semantic differences between two STL documents and applies patches to
transform one document into another. Analogous to JSON Patch (RFC 6902) and
JSON Merge Patch (RFC 7396) for the STL ecosystem.

**Design Principles:**
- **Semantic, not textual** — compares meaning (anchors + modifiers), not raw text
- **Modifier-granular** — for modified statements, reports exactly which fields changed
- **Read-only diffing** — `stl_diff()` never mutates its inputs
- **Deterministic** — same inputs always produce the same diff
- **Roundtrip** — `stl_patch(a, stl_diff(a, b))` produces a document equivalent to `b`

---

## 1. Matching Strategy

### 1.1 Statement Identity Key

Two statements are considered "the same statement" (for diff purposes) if they
share the same **identity key**:

```
key = (source.namespace, source.name, target.namespace, target.name, arrow)
```

This means:
- Same anchors, different modifiers → **MODIFY** (not remove+add)
- Same anchors, different path_type → **MODIFY**
- Different anchors → **ADD** / **REMOVE**

### 1.2 Duplicate Key Handling

STL allows multiple statements with the same source→target pair. When both
documents contain N statements with the same key:

1. Sort statements within each key group by their string representation
2. Match positionally within the sorted group
3. Extras in B → ADD; extras in A → REMOVE

### 1.3 Modifier Comparison

For MODIFY operations, compare modifiers at field granularity:

- Standard fields: compare each of the 30+ Modifier fields
- Custom fields: compare `custom` dict entries
- Report each changed field as a `ModifierChange(field, old_value, new_value)`
- Fields present in A but absent in B → `ModifierChange(field, old_value, None)`
- Fields absent in A but present in B → `ModifierChange(field, None, new_value)`

---

## 2. Data Models

### 2.1 DiffOp

```python
class DiffOp(str, Enum):
    ADD = "add"         # Statement exists in B but not A
    REMOVE = "remove"   # Statement exists in A but not B
    MODIFY = "modify"   # Same key, different content
```

### 2.2 ModifierChange

```python
class ModifierChange(BaseModel):
    field: str                # e.g. "confidence", "rule", "custom_field"
    old_value: Optional[Any]  # None if field was added
    new_value: Optional[Any]  # None if field was removed
```

### 2.3 DiffEntry

```python
class DiffEntry(BaseModel):
    op: DiffOp
    key: str                              # Human-readable key, e.g. "[A] -> [B]"
    statement_a: Optional[Statement]      # From doc A (None for ADD)
    statement_b: Optional[Statement]      # From doc B (None for REMOVE)
    index_a: Optional[int]                # Position in A (None for ADD)
    index_b: Optional[int]                # Position in B (None for REMOVE)
    modifier_changes: List[ModifierChange]  # Only populated for MODIFY
```

### 2.4 STLDiff

```python
class STLDiff(BaseModel):
    entries: List[DiffEntry]               # All changes
    summary: DiffSummary                   # Aggregate stats

class DiffSummary(BaseModel):
    added: int
    removed: int
    modified: int
    unchanged: int
    total_a: int      # len(doc_a.statements)
    total_b: int      # len(doc_b.statements)
```

### 2.5 PatchOp

```python
class PatchAction(str, Enum):
    ADD = "add"
    REMOVE = "remove"
    REPLACE = "replace"

class PatchOp(BaseModel):
    action: PatchAction
    statement: Optional[Statement]          # Full statement for ADD
    key: Optional[str]                      # Identity key for REMOVE/REPLACE
    index: Optional[int]                    # Target position (for ADD)
    modifier_updates: Optional[Dict[str, Any]]  # For REPLACE: new modifier values
    modifier_removals: Optional[List[str]]  # For REPLACE: fields to remove
```

---

## 3. Public API

### 3.1 `stl_diff(a, b) -> STLDiff`

```python
def stl_diff(
    a: ParseResult,
    b: ParseResult,
    *,
    ignore_order: bool = True,
) -> STLDiff:
    """Compute semantic diff between two STL documents.

    Args:
        a: Source document (before).
        b: Target document (after).
        ignore_order: If True (default), statement order does not generate
            diff entries. If False, reordered statements produce MODIFY entries.

    Returns:
        STLDiff with all changes needed to transform A into B.
    """
```

### 3.2 `stl_patch(doc, diff) -> ParseResult`

```python
def stl_patch(
    doc: ParseResult,
    diff: STLDiff,
) -> ParseResult:
    """Apply a diff to produce a new document.

    Args:
        doc: Original document (should match diff's source).
        diff: Diff to apply.

    Returns:
        New ParseResult equivalent to the diff's target.

    Raises:
        STLDiffError: If patch cannot be applied (e.g. statement to remove
            not found).
    """
```

### 3.3 `diff_to_text(diff) -> str`

```python
def diff_to_text(diff: STLDiff) -> str:
    """Render diff as human-readable text.

    Format:
        + [A] -> [B] ::mod(confidence=0.95)          # added
        - [C] -> [D] ::mod(rule="causal")             # removed
        ~ [E] -> [F]                                   # modified
            confidence: 0.8 -> 0.95
            rule: (none) -> "causal"

    Returns:
        Multi-line string with diff markers (+, -, ~).
    """
```

### 3.4 `diff_to_dict(diff) -> dict`

```python
def diff_to_dict(diff: STLDiff) -> dict:
    """Serialize diff as a JSON-compatible dict.

    Returns:
        Dict with keys: "entries", "summary".
    """
```

---

## 4. Algorithm

### 4.1 Diff Algorithm

```
1. Build key → [Statement] mapping for both A and B
   key = (src.ns, src.name, tgt.ns, tgt.name, arrow)

2. Collect all unique keys from both mappings

3. For each key:
   a. If key in A only → REMOVE entries for all A statements with this key
   b. If key in B only → ADD entries for all B statements with this key
   c. If key in both:
      - Sort A group and B group by str(stmt) for deterministic matching
      - Zip matched pairs:
        - If pair is identical (Statement.__eq__) → unchanged
        - If pair differs → MODIFY, compute modifier_changes
      - Leftover A statements → REMOVE
      - Leftover B statements → ADD

4. Build DiffSummary from counts

5. Return STLDiff(entries, summary)
```

### 4.2 Modifier Change Detection

```
1. Get modifier dicts for both statements:
   dict_a = stmt_a.modifiers.model_dump(exclude_none=True, exclude={"custom"})
   dict_a.update(stmt_a.modifiers.custom)
   (same for dict_b)

2. If stmt has no modifiers: treat as empty dict

3. All keys = union(dict_a.keys(), dict_b.keys())

4. For each key:
   - In A only → ModifierChange(key, old=value_a, new=None)
   - In B only → ModifierChange(key, old=None, new=value_b)
   - In both, values differ → ModifierChange(key, old=value_a, new=value_b)
   - In both, values equal → skip

5. Also compare path_type:
   - If path_type differs → ModifierChange("path_type", old, new)
```

### 4.3 Patch Algorithm

```
1. Start with a copy of doc.statements

2. Process REMOVE entries (reverse index order to avoid shifting):
   - Find matching statement in doc by key + content
   - Remove it

3. Process MODIFY entries:
   - Find matching statement in doc by key
   - Apply modifier_updates (set new values)
   - Apply modifier_removals (clear fields)

4. Process ADD entries:
   - Insert statement_b at index_b (or append if beyond end)

5. Return new ParseResult(statements=result, is_valid=doc.is_valid)
```

---

## 5. Error Handling

Error codes: E950–E959 (Diff/Patch range, sharing E900–E999 with Decay)

| Code | Name | Condition |
|------|------|-----------|
| E950 | DIFF_TYPE_ERROR | Input is not a ParseResult |
| E951 | PATCH_STATEMENT_NOT_FOUND | Statement to remove/modify not found in target doc |
| E952 | PATCH_CONFLICT | Patch conflicts with current document state |
| E953 | PATCH_INVALID_OP | Invalid patch operation |

---

## 6. CLI Extension

### 6.1 `stl diff`

```
stl diff <FILE_A> <FILE_B> [OPTIONS]

Options:
  --format, -f   Output format: text (default), json
  --summary, -s  Only print summary (counts)
  --quiet, -q    Exit code only: 0 = identical, 1 = different
```

### 6.2 `stl patch`

```
stl patch <FILE> <DIFF_JSON> [OPTIONS]

Options:
  --output, -o   Write result to file (default: stdout)
```

---

## 7. Test Specification

### 7.1 Unit Tests: `stl_diff()`

| ID | Scenario | Expected |
|----|----------|----------|
| T01 | Identical documents | entries=[], summary.unchanged=N |
| T02 | Statement added in B | 1 ADD entry with correct statement_b |
| T03 | Statement removed from A | 1 REMOVE entry with correct statement_a |
| T04 | Modifier changed (confidence 0.8→0.95) | 1 MODIFY entry, 1 ModifierChange |
| T05 | Multiple modifier changes | 1 MODIFY entry, N ModifierChanges |
| T06 | Modifier added (A has none, B has confidence) | MODIFY, ModifierChange(old=None) |
| T07 | Modifier removed (A has rule, B doesn't) | MODIFY, ModifierChange(new=None) |
| T08 | Reordered statements (ignore_order=True) | entries=[], all unchanged |
| T09 | Reordered statements (ignore_order=False) | TBD based on implementation |
| T10 | Multiple statements same key, different modifiers | Correct matching within group |
| T11 | Empty doc A, non-empty B | All ADD entries |
| T12 | Non-empty A, empty B | All REMOVE entries |
| T13 | Both empty | entries=[], unchanged=0 |
| T14 | Namespace differences | Treated as different keys |
| T15 | Custom modifier field change | ModifierChange for custom field |
| T16 | path_type change | ModifierChange for path_type |
| T17 | Large documents (100 statements) | Performance: completes in <1s |
| T18 | DiffSummary counts correct | added+removed+modified+unchanged = max(total_a, total_b) or correct |

### 7.2 Unit Tests: `stl_patch()`

| ID | Scenario | Expected |
|----|----------|----------|
| T20 | Apply empty diff | Result equals original |
| T21 | Apply ADD patch | Result has new statement |
| T22 | Apply REMOVE patch | Result missing removed statement |
| T23 | Apply MODIFY patch | Result has updated modifiers |
| T24 | Roundtrip: patch(a, diff(a,b)) == b | Statements match |
| T25 | Remove nonexistent statement | Raises E951 |
| T26 | Apply diff with mixed ops | All 3 op types work together |

### 7.3 Unit Tests: Output Formats

| ID | Scenario | Expected |
|----|----------|----------|
| T30 | diff_to_text with ADD | Line starts with "+" |
| T31 | diff_to_text with REMOVE | Line starts with "-" |
| T32 | diff_to_text with MODIFY | Line starts with "~", indented field changes |
| T33 | diff_to_dict structure | Has "entries" and "summary" keys |
| T34 | diff_to_dict roundtrip | JSON serializable |

### 7.4 CLI Integration Tests

| ID | Command | Expected |
|----|---------|----------|
| T40 | `stl diff a.stl b.stl` | Exit 0, text diff output |
| T41 | `stl diff a.stl a.stl` | Exit 0, "No differences" |
| T42 | `stl diff a.stl b.stl -f json` | Exit 0, valid JSON |
| T43 | `stl diff a.stl b.stl -s` | Exit 0, summary only |
| T44 | `stl diff a.stl b.stl -q` | Exit 1 (different) |
| T45 | `stl diff a.stl a.stl -q` | Exit 0 (identical) |
| T46 | `stl patch a.stl diff.json` | Exit 0, patched STL output |
| T47 | `stl patch a.stl diff.json -o out.stl` | Exit 0, file written |

---

## 8. Acceptance Criteria

1. `stl_diff(a, b)` correctly identifies all ADD, REMOVE, MODIFY operations
2. `stl_patch(a, stl_diff(a, b))` produces a document semantically equivalent to `b`
3. Modifier changes are tracked at field granularity (not whole-modifier replacement)
4. Custom modifier fields are handled correctly
5. Deterministic output (same inputs → same diff)
6. `diff_to_text()` produces human-readable output with +/-/~ markers
7. `diff_to_dict()` produces JSON-serializable output
8. CLI `stl diff` and `stl patch` commands work
9. No new dependencies
10. All 40+ tests pass
11. Existing tests remain green
