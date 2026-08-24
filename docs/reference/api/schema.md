# API: schema

Domain-specific schema validation for STL documents.

**Module:** `stl_parser.schema`
**Import:** `from stl_parser import load_schema, validate_against_schema, STLSchema, load_profile, validate_against_profiles`

> Requires `stl-parser >= 1.11.0` for `require {}` cross-statement rules and the
> `resolvers=` hook; `>= 1.10.0` for `edge {}` rules, profiles, and fail-closed
> schema parsing (unknown blocks/keys raise `E602` instead of being skipped).

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

**Raises:** `STLSchemaError` (`E600`–`E603`). Since 1.10.0 schema parsing is
**fail-closed**: unknown top-level blocks, anchor keys, constraint keys, and
modifier field types raise `E602` instead of being silently skipped. A missing
schema file path raises `E400` instead of being parsed as schema text.

**Schema validation error codes** (emitted by the validators below):

| Code | Meaning |
|------|---------|
| `E603` | Range / enum / pattern violation |
| `E604` | Field type mismatch |
| `E605` | Document statement count out of bounds |
| `E606` | Anchor namespace / pattern violation |
| `E607` | Missing required field |
| `E608` | `max_chain_length` exceeded |
| `E609` | Cycle present with `allow_cycles: false` |
| `E610` | Profile routing failure (statement matches no registered profile) |
| `E611` | Statement matches no declared `edge {}` rule |
| `E612` | Unsatisfied cross-statement `require {}` rule |

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
    resolvers: Optional[Dict[str, Callable[[str], bool]]] = None,
) -> SchemaValidationResult
```

Validate a `ParseResult` against schema constraints.

**Checks:**
- Anchor namespace and pattern requirements
- Required modifier fields
- Field type, range, and enum constraints
- Document-level constraints (min/max statements); `max_chain_length` (`E608`) and `allow_cycles: false` (`E609`) are enforced
- Typed edge rules, when the schema declares `edge {}` blocks (`E611`)
- Cross-statement `require {}` rules (`E612`) — see `resolvers` below

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `parse_result` | `ParseResult` | Document to validate |
| `schema` | `STLSchema` | Schema to validate against |
| `resolvers` | `Dict[str, Callable[[str], bool]]` | Named identity resolvers for `require {}` rules that declare a `resolver:`. The identity registry stays external to the engine (orchestrator-agnostic). A requirement whose resolver is not supplied **fails closed** with `E612`. |

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

## load_profile() / validate_against_profiles()

```python
load_profile(source: str) -> Dict[str, STLSchema]

validate_against_profiles(
    parse_result: ParseResult,
    profiles: Dict[str, STLSchema],
    resolvers: Optional[Dict[str, Callable[[str], bool]]] = None,
) -> SchemaValidationResult
```

Multi-schema validation for documents that mix namespaces (e.g. agent
coordination traffic + review traffic in one document).

- `load_profile(path)` loads a `.stl.profile` manifest into a
  `{namespace: STLSchema}` map. Missing files and missing or duplicate
  namespaces are errors.
- `validate_against_profiles` routes each statement to a schema by source
  namespace (or unique anchor-prefix match), validates cross-namespace targets
  against every registered profile, applies per-profile `min/max_statements`
  to the routed subset, and applies the strictest composite graph constraints
  (cycles rejected if any profile forbids them; smallest `max_chain_length`
  wins). `edge {}` and `require {}` rules apply per routed profile.

See `docs/schemas/agent.stl.profile` for a manifest example, and
[`docs/schemas/agent-comms.md`](../../schemas/agent-comms.md) for the design
notes behind the agent-communication profiles.

---

## STLSchema

```python
class STLSchema(BaseModel):
    name: str
    version: str = "1.0"
    namespace: Optional[str] = None
    source_anchor: SchemaAnchorConstraint
    target_anchor: SchemaAnchorConstraint
    modifier: SchemaModifierConstraint
    constraints: SchemaConstraints
    edge_rules: List[SchemaEdgeRule] = []      # from edge {} blocks (1.10.0)
    requirements: List[RequirementRule] = []   # from require {} blocks (1.11.0)
```

`SchemaEdgeRule` carries `source_types` / `relations` / `target_types`.
`RequirementRule` carries `trigger_action` / `binding_action` /
`binding_outcome` / `independent` / `resolver` — a statement whose `action`
equals `trigger_action` is valid only if the document also contains a
satisfying binding statement.

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
