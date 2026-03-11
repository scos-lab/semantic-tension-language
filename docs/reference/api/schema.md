# API: schema

Domain-specific schema validation for STL documents.

**Module:** `stl_parser.schema`
**Import:** `from stl_parser import load_schema, validate_against_schema, STLSchema`

---

## load_schema()

```python
load_schema(path: str) -> STLSchema
```

Parse a `.stl.schema` file into an `STLSchema` object.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str` | Path to `.stl.schema` file |

**Returns:** `STLSchema`

**Raises:** `STLSchemaError` (E600-E603)

**Example:**

```python
from stl_parser import load_schema
schema = load_schema("docs/schemas/causal.stl.schema")
print(f"{schema.name} v{schema.version}")
```

---

## validate_against_schema()

```python
validate_against_schema(
    parse_result: ParseResult,
    schema: STLSchema,
) -> SchemaValidationResult
```

Validate a `ParseResult` against schema constraints.

**Checks:**
- Anchor namespace and pattern requirements
- Required modifier fields
- Field type, range, and enum constraints
- Document-level constraints (min/max statements)

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `parse_result` | `ParseResult` | Document to validate |
| `schema` | `STLSchema` | Schema to validate against |

**Returns:** `SchemaValidationResult` with `is_valid`, `errors`, `warnings`

**Example:**

```python
from stl_parser import parse, load_schema, validate_against_schema

schema = load_schema("docs/schemas/medical.stl.schema")
result = parse('[Symptom_Fever] -> [Condition_Infection] ::mod(rule="causal", confidence=0.8, strength=0.7)')
validation = validate_against_schema(result, schema)
print(validation.is_valid)
```

---

## STLSchema

```python
class STLSchema(BaseModel):
    name: str
    version: str
    namespace: Optional[str] = None
    source_anchor: Optional[AnchorConstraint] = None
    target_anchor: Optional[AnchorConstraint] = None
    modifier: Optional[ModifierConstraint] = None
    constraints: Optional[DocumentConstraint] = None
```

---

## SchemaValidationResult

```python
class SchemaValidationResult(BaseModel):
    is_valid: bool = True
    errors: List[SchemaError] = []
    warnings: List[SchemaWarning] = []
    schema_name: str = ""
    schema_version: str = ""
```

---

## to_pydantic() / from_pydantic()

```python
to_pydantic(schema: STLSchema) -> type
from_pydantic(model_class: type) -> STLSchema
```

Convert between `STLSchema` and dynamically generated Pydantic model classes. Advanced use case for runtime validation.
