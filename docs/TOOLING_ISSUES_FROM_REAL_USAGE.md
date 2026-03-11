# STL Tooling Issues — Real-World Usage Report

> **Reporter:** Syn-claude
> **Context:** Building `project_scanner.py` — a project metadata scanner that outputs STL as interchange format between Python programs and LLMs
> **Date:** 2026-02-11
> **stl_parser version:** 1.1.0 (installed from source)
> **Severity scale:** P0 (blocking) / P1 (workaround needed) / P2 (inconvenience)

---

## Root Cause Analysis

The core issue is a **confusion between validation layer and transport layer**.

STL's `::mod(key=value, ...)` is a key-value data container, functionally equivalent to JSON's `{"key": value, ...}`. A JSON serializer never drops fields just because they aren't in a predefined schema — it faithfully reads, stores, and writes all key-value pairs. STL should behave the same way.

The current implementation correctly uses 30 hardcoded standard fields as a **validation schema** (e.g., `confidence` must be `float` in `[0.0, 1.0]`). This is analogous to JSON Schema — useful for type checking, but should not affect data transport.

**The bug:** `Statement.__str__()` (`models.py:248`) applies `exclude={"custom"}`, treating the validation schema as a transport filter. Fields that aren't in the 30 standard names get stored into `Modifier.custom` dict during build, then silently dropped during serialization. This breaks the fundamental contract that STL is a lossless data interchange format.

**The fix principle:** Validation and transport are separate concerns. Validate known fields strictly, but serialize ALL fields faithfully.

---

## Background

In implementing the `/index` skill, I needed a Python program to scan project directories and output structured metadata as STL statements. The natural approach was to use stl_parser's Builder + Emitter API chain:

```python
from stl_parser import stl, STLEmitter

with STLEmitter(log_path="scan.stl") as emitter:
    emitter.emit("[Mod:builder]", "[Cls:StatementBuilder]",
                 type="class", line=86, signature="build() -> Statement",
                 source_file="builder.py", category="source")
```

All five issues below were encountered during this development. Each has a workaround, but the workarounds collectively forced me to abandon the high-level API entirely in favor of writing raw STL text.

---

## Issue 1: `Statement.__str__()` drops all custom modifier fields

**Severity:** P0 (blocking — the primary use case fails silently)

**Location:** `stl_parser/models.py:248`

```python
def __str__(self) -> str:
    if self.modifiers:
        mod_dict = self.modifiers.model_dump(exclude_none=True, exclude={"custom"})  # ← HERE
```

**Problem:** `exclude={"custom"}` explicitly removes the entire `custom` dict from serialization. Any modifier key that isn't one of the 30 standard fields (confidence, rule, source, etc.) gets stored in `Modifier.custom` by the Builder, then silently dropped when the Statement is converted to string.

**Reproduction:**

```python
from stl_parser import stl

stmt = stl("[Mod:builder]", "[Cls:Foo]").mod(
    type="class",          # custom field
    line=86,               # custom field
    signature="build()",   # custom field
    confidence=0.95,       # standard field
).build()

print(str(stmt))
# Actual:   [Mod:builder] -> [Cls:Foo] ::mod(confidence=0.95)
# Expected: [Mod:builder] -> [Cls:Foo] ::mod(confidence=0.95, line=86, signature="build()", type="class")
```

Three fields silently vanish. No error, no warning.

**Impact chain:**
- `Statement.__str__()` drops custom → `ParseResult.to_stl()` drops custom (calls `str()`) → `STLEmitter._write()` drops custom (calls `str()`) → **the entire Builder→Emitter pipeline is lossy for any non-standard modifier**

**Suggested fix:** Include custom fields in serialization:

```python
def __str__(self) -> str:
    if self.modifiers:
        mod_dict = self.modifiers.model_dump(exclude_none=True, exclude={"custom"})
        # Also include custom fields
        if self.modifiers.custom:
            mod_dict.update(self.modifiers.custom)
        if mod_dict:
            # ... rest of serialization
```

---

## Issue 2: `STLEmitter.emit()` parameter name collides with `Modifier.source`

**Severity:** P1 (workaround: rename caller's modifier key)

**Location:** `stl_parser/emitter.py:78`

```python
def emit(self, source: str, target: str, **modifiers: Any) -> Statement:
```

**Problem:** The method's first positional parameter is named `source`. But `source` is also a standard STL provenance modifier key (defined in `Modifier.source`, models.py:171). Passing both causes a `TypeError`.

**Reproduction:**

```python
emitter.emit("[Study_X]", "[Finding_Y]",
             source="doi:10.1234/study",    # provenance modifier
             confidence=0.82)
# TypeError: emit() got multiple values for argument 'source'
```

This is especially problematic because `source` is a **REQUIRED** modifier for verifiable knowledge per the STL Operational Protocol (Section 5.3).

**Suggested fix:** Rename positional parameters to avoid collision:

```python
def emit(self, source_anchor: str, target_anchor: str, **modifiers: Any) -> Statement:
```

Or use a dedicated parameter:

```python
def emit(self, src: str, tgt: str, **modifiers: Any) -> Statement:
```

---

## Issue 3: STLEmitter has no API for writing comments

**Severity:** P2 (inconvenience — must bypass Emitter)

**Location:** `stl_parser/emitter.py` (missing feature)

**Problem:** STL files commonly use `#` comments for section headers and human context:

```stl
# Module Details
[Mod:builder] -> [Cls:StatementBuilder] ::mod(type="class", line=86)

# Internal Dependencies
[Mod:builder] -> [Mod:models] ::mod(type="imports")
```

The Emitter provides no way to write comments. Its `_stream` attribute is private, and the only public methods are `emit()` and `emit_statement()` — both only write statements.

**Workaround used:** Bypass the Emitter entirely:

```python
output_stream.write("# Module Details\n")
```

**Suggested fix:** Add a `comment()` method:

```python
def comment(self, text: str) -> None:
    """Write a comment line to configured outputs."""
    self._write_raw(f"# {text}\n")

def section(self, name: str) -> None:
    """Write a section separator comment."""
    self._write_raw(f"\n# {name}\n")
```

---

## Issue 4: Anchor name validation rejects common identifiers

**Severity:** P2 (inconvenience — requires sanitization layer)

**Location:** `stl_parser/models.py:92`

```python
if not re.match(r"^[\w\u4e00-\u9fff\u0600-\u06ff]+$", v, re.UNICODE):
    raise ValueError(...)
```

**Problem:** Many real-world identifiers contain hyphens, dots, or slashes that are invalid in STL anchors:

- Package names: `stl-parser`, `my-project`, `@scope/package`
- File paths: `src/core.py`, `tests/test_parser.py`
- Version strings: `1.0.0`, `v2.3.1`

The validation correctly enforces the STL spec, but provides no built-in sanitization helper.

**Workaround used:** Wrote a custom `_safe_anchor()` function:

```python
def _safe_anchor(name: str) -> str:
    s = re.sub(r'[-./\\@#$%^&*()+=\[\]{}<>|~`!?,;:\'"]+', '_', name)
    s = re.sub(r'[^\w]', '_', s)
    s = re.sub(r'_+', '_', s)
    return s.strip('_') or "Unknown"
```

**Suggestion:** Add a `sanitize_anchor_name()` utility to `_utils.py`:

```python
from stl_parser._utils import sanitize_anchor_name
name = sanitize_anchor_name("stl-parser")  # → "stl_parser"
```

Or provide it as an option in the Builder:

```python
stl("[stl-parser]", "[Metadata]", auto_sanitize=True)  # auto-converts hyphens
```

---

## Issue 5: Round-trip lossy — `parse()` → `to_stl()` drops custom fields

**Severity:** P1 (data loss in round-trip)

**Location:** `stl_parser/models.py:364-370`

```python
def to_stl(self) -> str:
    return "\n".join(str(stmt) for stmt in self.statements)
```

**Problem:** Since `to_stl()` calls `str(stmt)` which drops custom fields (Issue 1), any STL document with non-standard modifiers loses data through a parse→serialize round-trip.

**Reproduction:**

```stl
# Input STL
[Mod:builder] -> [Cls:Foo] ::mod(type="class", line=86, confidence=0.95)
```

```python
from stl_parser import parse
result = parse(input_stl)
output = result.to_stl()
# Output: [Mod:builder] -> [Cls:Foo] ::mod(confidence=0.95)
# Lost: type="class", line=86
```

**Note:** This depends on whether the parser puts non-standard keys into `Modifier.custom` or drops them entirely. If the parser preserves them in `custom`, then Issue 1's fix would also fix this. If the parser drops them during parsing, that's a separate issue.

---

## Summary

| # | Issue | Severity | Root Cause | Fix Complexity | Status |
|---|-------|----------|------------|----------------|--------|
| 1 | `str(Statement)` drops custom fields | P0 | `exclude={"custom"}` in `__str__` | Low (add custom dict to output) | **FIXED v1.3.0** |
| 2 | `emit()` source name collision | P1 | Parameter name matches modifier key | Low (rename parameter) | **FIXED v1.3.0** |
| 3 | No comment API in Emitter | P2 | Missing feature | Low (add method) | **FIXED v1.3.0** |
| 4 | No anchor name sanitization utility | P2 | Missing utility | Low (add function) | **FIXED v1.3.0** |
| 5 | Round-trip loses custom fields | P1 | Consequence of Issue 1 | Fixed by Issue 1 | **FIXED v1.3.0** |

**All issues resolved in v1.3.0 (2026-02-12).** The Builder→Emitter pipeline now faithfully serializes all modifier fields.

---

## Workaround Used

Due to Issues 1-3 combined, the `project_scanner.py` bypassed the entire Builder/Emitter API and writes STL text directly:

```python
def _emit(out, source: str, target: str, **mods) -> None:
    """Write STL text directly, preserving ALL fields."""
    parts = []
    for k, v in mods.items():
        if isinstance(v, str):
            parts.append(f'{k}="{v}"')
        elif isinstance(v, (int, float)):
            parts.append(f"{k}={v}")
        elif isinstance(v, bool):
            parts.append(f"{k}={str(v).lower()}")
    mod_str = ", ".join(parts)
    out.write(f"{source} -> {target} ::mod({mod_str})\n")
```

This works but loses: validation, thread-safety, auto-timestamp injection, namespace prefixing — all features the Emitter was designed to provide.

---

**End of Report**
