# API: query

Search, filter, and extract data from STL documents.

**Module:** `stl_parser.query`
**Import:** `from stl_parser import find, find_all, filter_statements, select, stl_pointer`

---

## find()

```python
find(result: ParseResult, **kwargs: Any) -> Optional[Statement]
```

Find the first statement matching **all** conditions (AND logic).

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `result` | `ParseResult` | Document to search |
| `**kwargs` | `Any` | Field conditions with optional operator suffixes |

**Returns:** First matching `Statement`, or `None`.

**Example:**

```python
stmt = find(result, source="Rain", confidence__gte=0.8)
```

---

## find_all()

```python
find_all(result: ParseResult, **kwargs: Any) -> List[Statement]
```

Find all statements matching all conditions.

**Returns:** List of matching `Statement` objects (empty if none).

**Example:**

```python
causal = find_all(result, rule="causal")
```

---

## filter_statements()

```python
filter_statements(result: ParseResult, **kwargs: Any) -> ParseResult
```

Filter a `ParseResult` to only matching statements. Returns a **new** `ParseResult`; the original is unmodified.

**Example:**

```python
filtered = filter_statements(result, confidence__gte=0.8)
print(len(filtered.statements))
```

---

## select()

```python
select(result: ParseResult, field: str) -> List[Any]
```

Extract a single field value from every statement.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `result` | `ParseResult` | Document to extract from |
| `field` | `str` | Field name (see resolution below) |

**Returns:** List of values (includes `None` for absent fields).

**Field Resolution Order:**
1. Special fields: `source`, `target`, `source_namespace`, `target_namespace`, `arrow`
2. Standard modifier fields: `confidence`, `rule`, `strength`, etc.
3. Custom modifier fields

**Example:**

```python
names = select(result, field="source")       # ["Rain", "Wind", ...]
confs = select(result, field="confidence")   # [0.85, 0.7, None, ...]
```

---

## stl_pointer()

```python
stl_pointer(result: ParseResult, path: str) -> Any
```

Access a nested value by slash-delimited path (inspired by JSON Pointer RFC 6901).

**Path format:** `/<statement_index>/<attribute>[/<sub_attribute>...]`

**Examples:**

| Path | Resolves To |
|------|------------|
| `/0/source/name` | First statement's source name |
| `/1/modifiers/confidence` | Second statement's confidence |
| `/2/arrow` | Third statement's arrow |

**Raises:** `STLQueryError` (E450-E453) if path is invalid or index out of range.

---

## Operators

Use double-underscore suffixes on field names:

| Operator | Suffix | Example |
|----------|--------|---------|
| Equals | (none) or `__eq` | `confidence=0.9` |
| Greater than | `__gt` | `confidence__gt=0.8` |
| Greater or equal | `__gte` | `confidence__gte=0.8` |
| Less than | `__lt` | `confidence__lt=0.5` |
| Less or equal | `__lte` | `confidence__lte=0.7` |
| Not equal | `__ne` | `rule__ne="logical"` |
| Contains | `__contains` | `source__contains="Theory"` |
| Starts with | `__startswith` | `target__startswith="Effect"` |
| In list | `__in` | `rule__in=["causal", "logical"]` |

All conditions are combined with AND logic.
