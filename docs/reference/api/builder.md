# API: builder

Programmatic STL statement construction.

**Module:** `stl_parser.builder`
**Import:** `from stl_parser import stl, stl_doc, StatementBuilder`

---

## stl()

```python
stl(source: str, target: str) -> StatementBuilder
```

Create a builder for a single statement.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `source` | `str` | Source anchor: `"[A]"`, `"A"`, `"[Ns:A]"`, or `"Ns:A"` |
| `target` | `str` | Target anchor (same formats) |

**Returns:** `StatementBuilder` for fluent chaining.

**Example:**

```python
from stl_parser import stl
stmt = stl("[Rain]", "[Flooding]").mod(rule="causal", confidence=0.85).build()
```

---

## stl_doc()

```python
stl_doc(*builders: Union[StatementBuilder, Statement]) -> ParseResult
```

Build multiple statements into a `ParseResult`.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `*builders` | `StatementBuilder` or `Statement` | Variadic builders or pre-built statements |

**Returns:** `ParseResult` containing all built statements.

**Example:**

```python
from stl_parser import stl, stl_doc
doc = stl_doc(
    stl("[A]", "[B]").mod(confidence=0.9),
    stl("[C]", "[D]").mod(rule="causal"),
)
```

---

## StatementBuilder

### .mod()

```python
StatementBuilder.mod(**kwargs: Any) -> StatementBuilder
```

Add modifier key-value pairs. Later calls override earlier values for the same key. Returns `self` for chaining.

### .no_validate()

```python
StatementBuilder.no_validate() -> StatementBuilder
```

Disable post-build semantic validation. Pydantic field constraints (type, range) still apply. Returns `self`.

### .build()

```python
StatementBuilder.build() -> Statement
```

Build the `Statement` from accumulated state. Separates standard vs custom modifier fields.

**Raises:** `STLBuilderError` (E500-E502) on validation failure.

**Example:**

```python
stmt = (
    stl("[Drug_X]", "[Effect_Y]")
    .mod(rule="causal", confidence=0.85, dosage="500mg")
    .build()
)
# dosage is stored in stmt.modifiers.custom["dosage"]
```
