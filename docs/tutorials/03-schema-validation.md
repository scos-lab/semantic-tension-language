# Tutorial 3: Schema Validation

Learn how to validate STL documents against domain-specific schemas.

**What you'll learn:**
- Load `.stl.schema` files with `load_schema()`
- Validate documents with `validate_against_schema()`
- Understand schema syntax: namespaces, anchor patterns, modifier constraints
- Use the 6 built-in domain schemas
- Create your own schemas

**Prerequisites:** [Tutorial 2: Building](02-building.md)

---

## Step 1: Load a Schema

Schemas are `.stl.schema` files that define constraints for a specific domain:

```python
from stl_parser import load_schema

schema = load_schema("docs/schemas/causal.stl.schema")

print(f"Schema: {schema.name} v{schema.version}")
print(f"Namespace: {schema.namespace}")
```

## Step 2: Validate a Document

```python
from stl_parser import parse, load_schema, validate_against_schema

schema = load_schema("docs/schemas/causal.stl.schema")

result = parse('[Rain] -> [Flooding] ::mod(rule="causal", confidence=0.85, strength=0.8)')

validation = validate_against_schema(result, schema)

if validation.is_valid:
    print("Document passes schema validation")
else:
    for err in validation.errors:
        print(f"  Error: {err}")
```

## Step 3: Understand Validation Errors

When a document violates schema constraints, you get specific error messages:

```python
from stl_parser import parse, load_schema, validate_against_schema

# Medical schema requires prefixed anchors (Symptom_, Drug_, etc.)
schema = load_schema("docs/schemas/medical.stl.schema")

# This uses unprefixed anchors — will fail
result = parse('[Aspirin] -> [PainRelief] ::mod(rule="causal", confidence=0.85, strength=0.7)')

validation = validate_against_schema(result, schema)
print(f"Valid: {validation.is_valid}")  # False
for err in validation.errors:
    print(f"  {err}")
```

## Step 4: Schema Syntax

A `.stl.schema` file defines four constraint sections:

```
schema SchemaName v1.0 {

    namespace "Domain"           # Optional: expected anchor namespace

    anchor source {
        pattern: /regex/         # Regex pattern for source anchor names
    }

    anchor target {
        pattern: /regex/         # Regex pattern for target anchor names
    }

    modifier {
        required: [field1, field2]   # Fields that must be present
        optional: [field3, field4]   # Additional allowed fields

        field1: float(min, max)      # Float range constraint
        field2: enum("a", "b", "c")  # Enum constraint
        field3: string               # Any string value
    }

    constraints {
        min_statements: 1            # Minimum statements in document
        max_statements: 500          # Maximum statements in document
    }
}
```

## Step 5: The 6 Built-In Schemas

| Schema | File | Key Constraints |
|--------|------|----------------|
| **TCM** | `tcm.stl.schema` | Unicode anchors, `domain` required, confidence 0.5-1.0 |
| **Scientific** | `scientific.stl.schema` | `source` required, confidence 0.3-1.0 |
| **Causal** | `causal.stl.schema` | `strength` required, rule must be "causal" |
| **Historical** | `historical.stl.schema` | `time` + `source` required, multi-script support |
| **Medical** | `medical.stl.schema` | Prefixed anchors (Symptom_, Drug_, Condition_, ...) |
| **Legal** | `legal.stl.schema` | Prefixed anchors (Law_, Regulation_, Precedent_, ...) |

### Example: Using the Scientific Schema

```python
from stl_parser import parse, load_schema, validate_against_schema

schema = load_schema("docs/schemas/scientific.stl.schema")

# Valid: has required source field
result = parse("""
[Smoking] -> [Lung_Cancer] ::mod(
  rule="empirical",
  confidence=0.92,
  source="doi:10.1234/study"
)
""")
validation = validate_against_schema(result, schema)
print(f"Valid: {validation.is_valid}")  # True
```

### Example: Using the Legal Schema

```python
schema = load_schema("docs/schemas/legal.stl.schema")

result = parse("""
[Law_GDPR_Article5] -> [Regulation_DataMinimization] ::mod(
  rule="definitional",
  confidence=0.95,
  source="legal_code://GDPR/Article5"
)
""")
validation = validate_against_schema(result, schema)
print(f"Valid: {validation.is_valid}")  # True
```

## Step 6: Create a Custom Schema

Start from the template:

```
# docs/schemas/_template.stl.schema
schema YourDomainName v1.0 {

    namespace "YourNamespace"

    anchor source {
        pattern: /[A-Za-z0-9_]+/
    }

    anchor target {
        pattern: /[A-Za-z0-9_]+/
    }

    modifier {
        required: [confidence, rule]
        optional: [source, author, time]

        confidence: float(0.0, 1.0)
        rule: enum("causal", "logical", "empirical", "definitional")
    }

    constraints {
        min_statements: 1
        max_statements: 1000
    }
}
```

### Example: Education Domain Schema

```
schema EducationKnowledge v1.0 {

    namespace "Edu"

    anchor source {
        pattern: /(Course|Topic|Concept|Skill|Student|Assessment)_[A-Za-z0-9_]+/
    }

    anchor target {
        pattern: /(Course|Topic|Concept|Skill|Student|Assessment|Outcome|Prerequisite)_[A-Za-z0-9_]+/
    }

    modifier {
        required: [confidence, rule]
        optional: [source, domain, difficulty, time]

        confidence: float(0.5, 1.0)
        rule: enum("definitional", "causal", "empirical")
    }

    constraints {
        min_statements: 1
        max_statements: 2000
    }
}
```

## Step 7: Schema Validation via CLI

```bash
stl schema-validate knowledge_base.stl --schema docs/schemas/scientific.stl.schema
```

## Step 8: Combine with LLM Pipeline

Use schemas with the LLM validation pipeline for end-to-end checking:

```python
from stl_parser import validate_llm_output, load_schema

schema = load_schema("docs/schemas/causal.stl.schema")
result = validate_llm_output(
    "Rain => Flooding mod(rule=causal, confidence=0.85, strength=0.8)",
    schema=schema
)
print(f"Valid: {result.is_valid}")
print(f"Repairs: {len(result.repairs)}")
```

---

## Complete Example

```python
from stl_parser import stl, stl_doc, load_schema, validate_against_schema

# Build a medical knowledge document
doc = stl_doc(
    stl("[Symptom_Headache]", "[Condition_Migraine]")
        .mod(rule="empirical", confidence=0.75, strength=0.6,
             source="doi:10.1234/neuro"),

    stl("[Drug_Sumatriptan]", "[Effect_PainRelief]")
        .mod(rule="causal", confidence=0.88, strength=0.80,
             source="doi:10.1234/pharma", domain="neurology"),
)

# Validate against medical schema
schema = load_schema("docs/schemas/medical.stl.schema")
validation = validate_against_schema(doc, schema)

if validation.is_valid:
    print(f"All {len(doc.statements)} statements pass medical schema")
else:
    print(f"Validation failed with {len(validation.errors)} errors:")
    for err in validation.errors:
        print(f"  {err}")
```

---

**Next:** [Tutorial 4: LLM Pipeline](04-llm-pipeline.md)
