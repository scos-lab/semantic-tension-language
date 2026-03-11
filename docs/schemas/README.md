# STL Schema Ecosystem

> **Version**: 1.0
> **Status**: Active
> **Last Updated**: 2026-02-13

## Overview

STL schemas (`.stl.schema`) define domain-specific constraints for STL documents.
A schema specifies which anchor patterns, modifier fields, value ranges, and
document structures are valid for a particular domain.

Schemas are **protocol-level documents** — they constrain how knowledge is
structured within a domain, not the knowledge itself.

## Directory Structure

```
docs/schemas/
├── README.md                          # This file
├── _template.stl.schema               # Blank template for new domains
├── tcm.stl.schema                     # Traditional Chinese Medicine
├── scientific.stl.schema              # Scientific research & claims
├── causal.stl.schema                  # Causal inference & analysis
├── historical.stl.schema              # Historical knowledge & events
├── medical.stl.schema                 # Medical/clinical domain
└── legal.stl.schema                   # Legal reasoning & regulation
```

## Quick Start

### Loading a Schema

```python
from stl_parser import load_schema, validate_against_schema, parse

# Load from file
schema = load_schema("docs/schemas/tcm.stl.schema")

# Validate a document
doc = parse("[TCM:湿邪] -> [TCM:苦味药] ::mod(confidence=0.85, rule=\"causal\", domain=\"TCM\")")
result = validate_against_schema(doc, schema)

if result.is_valid:
    print("Document conforms to TCM schema")
else:
    for err in result.errors:
        print(f"  {err.code}: {err.message}")
```

### Creating a New Domain Schema

1. Copy `_template.stl.schema`
2. Fill in domain-specific constraints
3. Test with representative STL documents
4. Add to this README index

## Schema Index

| Schema | Domain | Required Fields | Anchor Pattern | Version |
|--------|--------|-----------------|----------------|---------|
| `tcm` | Traditional Chinese Medicine | confidence, rule, domain | Unicode + Latin | 1.0 |
| `scientific` | Scientific research | confidence, rule, source | Latin + underscore | 1.0 |
| `causal` | Causal inference | confidence, rule, strength | Latin + underscore | 1.0 |
| `historical` | Historical knowledge | confidence, time, source | Latin + Unicode | 1.0 |
| `medical` | Medical/clinical | confidence, rule, source, domain | Prefixed (Symptom_, Drug_, etc.) | 1.0 |
| `legal` | Legal reasoning | confidence, rule, source | Prefixed (Law_, Regulation_, etc.) | 1.0 |

## Schema Syntax Reference

```
schema <Name> <Version> {

    # Top-level namespace (metadata, not enforced)
    namespace "<default_namespace>"

    # Anchor constraints
    anchor source {
        namespace: required("<ns>")    # or: optional
        pattern: /regex/               # Anchor name must fullmatch
    }
    anchor target {
        namespace: optional
        pattern: /regex/
    }

    # Modifier constraints
    modifier {
        required: [field1, field2]      # Must be present
        optional: [field3, field4]      # Documented, not enforced

        field1: float(min, max)         # Numeric range
        field2: enum("a", "b", "c")    # Allowed values
        field3: string                  # String type
        field4: datetime                # ISO 8601
        field5: boolean                 # true/false
        field6: integer(min, max)       # Integer range
    }

    # Document-level constraints
    constraints {
        min_statements: 1
        max_statements: 1000
        max_chain_length: 5            # Parsed, not yet enforced
        allow_cycles: false            # Parsed, not yet enforced
    }
}
```

## Naming Conventions

- **Schema file**: `<domain>.stl.schema` (lowercase, no spaces)
- **Schema name**: PascalCase (e.g., `TraditionalChineseMedicine`)
- **Anchor patterns**: Domain prefix + underscore + name (e.g., `Symptom_Fever`)
- **Enum values**: lowercase (e.g., `"causal"`, `"empirical"`)
- **Namespace values**: Short uppercase or PascalCase (e.g., `"TCM"`, `"Med"`)

## Versioning

- Schema versions follow `major.minor` (e.g., `v1.0`, `v1.1`, `v2.0`)
- Breaking changes (removing required fields, narrowing ranges) require major bump
- Additive changes (new optional fields, wider ranges) use minor bump
