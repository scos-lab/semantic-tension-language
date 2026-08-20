# API: schema

Domain-specific schema validation for STL documents.

**Module:** `stl_parser.schema`
**Import:** `from stl_parser import load_schema, load_profile, validate_against_schema, validate_against_profiles, STLSchema`

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

**Raises:** `STLSchemaError` for schema parsing and loading failures

Parsing is fail-closed: unknown declarations, constraints, and field types are errors.

## load_profile()

`load_profile(path: str) -> Dict[str, STLSchema]` loads a `.stl.profile` manifest, resolves includes relative to it, and keys schemas by unique namespace.

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
- Document-level constraints (statement count, maximum chain length, cycles)

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

## validate_against_profiles()

```python
validate_against_profiles(
    parse_result: ParseResult,
    profiles: Dict[str, STLSchema],
) -> SchemaValidationResult
```

Validate a mixed-domain document. Each statement is validated by the schema selected from its source namespace, or by one unique source-pattern match when the namespace is absent. Targets may match any registered profile.

Unknown and ambiguous source routing returns `E610`. Routed statement counts apply per profile; cycle policy and the strictest chain limit apply globally. The result uses `schema_name="CompositeProfiles"` and includes each profile version in `schema_version`.

```python
from stl_parser import parse_file, load_schema, validate_against_profiles

document = parse_file("docs/schemas/examples/small-software-project.stl")
profiles = {
    "Software": load_schema("docs/schemas/software-core.stl.schema"),
    "Delivery": load_schema("docs/schemas/software-delivery.stl.schema"),
}
validation = validate_against_profiles(document, profiles)
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

Convert between `STLSchema` and dynamic Pydantic models. Enum fields use `Literal`, datetime fields use `datetime`, integers are strict, and string patterns are preserved.
