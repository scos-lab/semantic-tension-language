# How-To: Create Custom Schemas

Define domain-specific validation rules for STL documents using `.stl.schema` files. Schemas enforce required fields, value ranges, naming patterns, and structural constraints.

**Prerequisites:** Familiarity with [STL syntax](../reference/stl-syntax.md) and [modifiers](../reference/modifiers.md).

---

## Schema File Syntax

A schema file uses `.stl.schema` extension and follows this structure:

```
schema MedicalTrial v1.0 {
    namespace "Medicine"

    anchor source {
        pattern: /[A-Za-z0-9_]+/
    }

    anchor target {
        pattern: /[A-Za-z0-9_]+/
    }

    modifier {
        required: [confidence, rule, source]
        optional: [strength, author, timestamp, domain]

        confidence: float(0.5, 1.0)
        strength: float(0.0, 1.0)
        rule: enum("causal", "empirical")
    }

    constraints {
        min_statements: 1
        max_statements: 500
        max_chain_length: 3
        allow_cycles: false
    }
}
```

---

## Step 1: Define Anchor Constraints

Anchor constraints restrict source and target naming:

```
anchor source {
    namespace: required("Medicine")    # Must use this namespace
    pattern: /[A-Z][A-Za-z0-9_]+/     # Must start with uppercase
}

anchor target {
    namespace: optional                # Namespace is allowed but not required
    pattern: /[A-Za-z0-9_]+/
}
```

**Options:**
- `namespace: required("Name")` — Anchor must have this exact namespace
- `namespace: optional` — Namespace is allowed but not enforced
- `pattern: /regex/` — Anchor name must match the regex

---

## Step 2: Define Modifier Constraints

The `modifier` block specifies which fields are required, which are optional, and what values they accept:

```
modifier {
    required: [confidence, rule, source]
    optional: [certainty, strength, author, timestamp]

    confidence: float(0.3, 1.0)
    certainty: float(0.0, 1.0)
    strength: float(0.0, 1.0)
    rule: enum("causal", "empirical", "logical", "definitional")
    source: string
    author: string
    timestamp: datetime
}
```

**Field type constraints:**

| Type | Syntax | Example |
|------|--------|---------|
| Float range | `float(min, max)` | `confidence: float(0.0, 1.0)` |
| Integer range | `integer(min, max)` | `priority: integer(1, 10)` |
| Enum values | `enum("a", "b", "c")` | `rule: enum("causal", "empirical")` |
| String | `string` | `author: string` |
| String pattern | `string(/regex/)` | `identifier: string(/[A-Z]+-[0-9]+/)` |
| DateTime | `datetime` | `timestamp: datetime` |
| Boolean | `boolean` | `verified: boolean` |

**Strictness (since 1.10.0):** schema parsing is fail-closed — unknown blocks,
keys, and field types raise `E602` rather than being silently ignored. Typed
values are strict: `integer` rejects bools and floats, `boolean` requires a
real bool, `datetime` requires an ISO 8601 string, and `string(/…/)` patterns
match with `re.fullmatch`.

---

## Step 3: Define Document Constraints

The `constraints` block sets structural limits:

```
constraints {
    min_statements: 1          # At least 1 statement required
    max_statements: 1000       # No more than 1000 statements
    max_chain_length: 5        # Chained paths limited to 5 nodes
    allow_cycles: false        # No cyclic references allowed
}
```

All constraint fields are optional. Omit any you don't need.
`max_chain_length` (`E608`) and `allow_cycles: false` (`E609`) are enforced
since 1.10.0.

---

## Step 3b: Typed Edge Rules (`edge {}` blocks, 1.10.0+)

Repeatable `edge {}` blocks restrict which source-type / relation / target-type
combinations are legal. When a schema declares any edge rules, every statement
must match at least one triple (`E611`); schemas without edge blocks behave
exactly as before.

```
edge {
    source: [Gate, Check]
    relation: [gate, check]
    target: [Branch, WorkItem]
}

edge {
    source: [Verifier]
    relation: [verify]
    target: [Artifact, Revision]
}
```

---

## Step 3c: Cross-Statement Requirements (`require {}` blocks, 1.11.0+)

A `require {}` block makes one kind of statement conditional on the presence of
another — across the whole document. A statement whose `action` equals the
trigger is valid only if the document also contains a satisfying binding
statement; otherwise validation fails with `E612`, naming exactly what is
missing.

```
require {
    action: "merge"          # trigger: statements with action="merge"
    binding: "verify"        # require a statement with action="verify"
    outcome: "pass"          # …whose outcome is "pass"
    independent: true        # …with verifier != claimant on the binding
    resolver: "identity"     # …whose verifier resolves via this named resolver
}
```

The identity registry stays **external to the engine**: supply resolvers at
validation time —

```python
validation = validate_against_schema(result, schema,
                                     resolvers={"identity": my_registry.knows})
```

If a required resolver is not supplied, the gate **fails closed** (`E612`).
This is the structural fix for silent approval deadlocks — a gate required
from a role bound to nobody becomes a validation error instead of a stall.
See [`docs/schemas/software-review.stl.schema`](../schemas/software-review.stl.schema)
for a real deployment and [`docs/schemas/agent-comms.md`](../schemas/agent-comms.md)
for the field report that motivated it.

---

## Step 3d: Multi-Schema Profiles (`.stl.profile`, 1.10.0+)

When one document mixes namespaces (e.g. agent coordination + review traffic),
a profile manifest routes each statement to its schema:

```python
from stl_parser import load_profile, validate_against_profiles

profiles = load_profile("docs/schemas/agent.stl.profile")   # {namespace: STLSchema}
validation = validate_against_profiles(result, profiles,
                                       resolvers={"identity": my_registry.knows})
```

Statements route by source namespace (or unique anchor-prefix match);
cross-namespace targets are validated against every registered profile; the
strictest composite graph constraints win (any profile forbidding cycles
forbids them; smallest `max_chain_length` applies).

---

## Step 4: Load and Validate

```python
from stl_parser import parse
from stl_parser.schema import load_schema, validate_against_schema

# Load schema from file
schema = load_schema("medical.stl.schema")

# Parse an STL document
result = parse("""
[Drug_Aspirin] -> [Effect_PainRelief] ::mod(
  confidence=0.92,
  rule="causal",
  source="doi:10.1234/aspirin-study",
  strength=0.85
)
""")

# Validate
validation = validate_against_schema(result, schema)

if validation.is_valid:
    print("Document conforms to schema")
else:
    for error in validation.errors:
        print(f"{error.code}: {error.message}")
        if error.statement_index is not None:
            print(f"  Statement #{error.statement_index}")
        if error.field:
            print(f"  Field: {error.field}")
```

---

## Step 5: Load Schema from Inline Text

You can also load a schema from a string:

```python
schema_text = """
schema QuickTest v1.0 {
    modifier {
        required: [confidence]
        confidence: float(0.0, 1.0)
    }
}
"""

schema = load_schema(schema_text)
validation = validate_against_schema(result, schema)
```

---

## Example: Scientific Research Schema

```
schema ScientificResearch v1.0 {
    namespace "Science"

    anchor source {
        pattern: /[A-Za-z0-9_]+/
    }

    anchor target {
        pattern: /[A-Za-z0-9_]+/
    }

    modifier {
        required: [confidence, rule, source]
        optional: [certainty, strength, author, timestamp, domain, location]

        confidence: float(0.3, 1.0)
        certainty: float(0.0, 1.0)
        strength: float(0.0, 1.0)
        rule: enum("causal", "empirical", "logical", "definitional")
    }

    constraints {
        min_statements: 1
        max_statements: 1000
    }
}
```

---

## Example: Causal Inference Schema

```
schema CausalInference v1.0 {
    namespace "Causal"

    anchor source { pattern: /[A-Za-z0-9_]+/ }
    anchor target { pattern: /[A-Za-z0-9_]+/ }

    modifier {
        required: [confidence, rule, strength]
        optional: [conditionality, cause, effect, source, time, location]

        confidence: float(0.3, 1.0)
        strength: float(0.0, 1.0)
        rule: enum("causal")
        conditionality: enum("Sufficient", "Necessary", "Both")
    }

    constraints {
        min_statements: 1
        max_statements: 500
        allow_cycles: false
    }
}
```

---

## Generate Pydantic Models from Schemas

Convert a schema to a dynamic Pydantic model for programmatic validation:

```python
from stl_parser.schema import load_schema, to_pydantic

schema = load_schema("scientific.stl.schema")
ModifierModel = to_pydantic(schema)

# Use the generated model
try:
    mod = ModifierModel(confidence=0.85, rule="causal", source="doi:10.1234")
    print(mod.model_dump())
except Exception as e:
    print(f"Validation failed: {e}")
```

---

## CLI Usage

Validate a document against a schema from the command line:

```bash
stl schema-validate knowledge.stl --schema medical.stl.schema
```

Exit code 0 = valid, 1 = errors found.

---

## Built-in Schemas

STL ships with domain schemas in `docs/schemas/`:

| Schema | Domain | Required Fields |
|--------|--------|-----------------|
| `scientific.stl.schema` | Scientific research | confidence, rule, source |
| `causal.stl.schema` | Causal inference | confidence, rule, strength |
| `medical.stl.schema` | Medical/clinical | confidence, rule, source, domain |
| `historical.stl.schema` | Historical knowledge | confidence, time, source |
| `legal.stl.schema` | Legal reasoning | confidence, rule, source |
| `tcm.stl.schema` | Traditional Chinese Medicine | confidence, domain (Unicode anchors) |
| `software-agentcoord.stl.schema` | Multi-agent coordination (DRAFT) | action, outcome, provenance, … |
| `software-review.stl.schema` | Agent code review + merge gates (DRAFT) | action, outcome, provenance, … |
| `_template.stl.schema` | Starting template | confidence |

Use the template as a starting point for your own schemas. The two `software-*`
profiles are community-contributed drafts grounded in a field report of live
multi-agent STL traffic — design notes in
[`docs/schemas/agent-comms.md`](../schemas/agent-comms.md); `software-review`
uses `edge {}` + `require {}` end to end.

---

## See Also

- [Tutorial: Schema Validation](../tutorials/03-schema-validation.md) — Step-by-step tutorial
- [API: schema](../reference/api/schema.md) — Full API reference
- [Modifier Reference](../reference/modifiers.md) — All modifier fields
