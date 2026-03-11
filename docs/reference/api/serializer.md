# API: serializer

Serialization and deserialization for STL documents.

**Module:** `stl_parser.serializer`
**Import:** `from stl_parser import to_json, to_dict, from_json, from_dict, to_stl`
**RDF Import:** `from stl_parser.serializer import to_rdf`

---

## to_json()

```python
to_json(parse_result: ParseResult, indent: Optional[int] = 2) -> str
```

Serialize a `ParseResult` to a JSON string.

**Example:**

```python
from stl_parser import parse, to_json
result = parse('[A] -> [B] ::mod(confidence=0.9)')
print(to_json(result, indent=2))
```

---

## to_dict()

```python
to_dict(parse_result: ParseResult) -> Dict[str, Any]
```

Serialize a `ParseResult` to a Python dictionary.

---

## from_json()

```python
from_json(json_string: str) -> ParseResult
```

Deserialize a JSON string back into a `ParseResult`.

**Raises:** `STLSerializationError` (E200-E207) on invalid JSON or validation failure.

---

## from_dict()

```python
from_dict(data: Dict[str, Any]) -> ParseResult
```

Deserialize a dictionary back into a `ParseResult`.

**Raises:** `STLSerializationError` (E200-E207) on validation failure.

---

## to_stl()

```python
to_stl(parse_result: ParseResult) -> str
```

Convert a `ParseResult` back to STL text format. Each statement becomes one line.

**Example:**

```python
from stl_parser import parse, to_stl
result = parse('[A] -> [B] ::mod(confidence=0.9)')
print(to_stl(result))
# [A] -> [B] ::mod(confidence=0.9)
```

---

## to_rdf()

```python
to_rdf(parse_result: ParseResult, format: str = "turtle") -> str
```

Serialize to RDF using standard reification.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `parse_result` | `ParseResult` | — | Document to serialize |
| `format` | `str` | `"turtle"` | RDF format: `"turtle"`, `"xml"`, `"nt"`, `"json-ld"` |

**Returns:** RDF string in the requested format.

**Raises:** `STLSerializationError` (E200-E207)

**Note:** `to_rdf` must be imported from `stl_parser.serializer` directly, not from the top-level package.
