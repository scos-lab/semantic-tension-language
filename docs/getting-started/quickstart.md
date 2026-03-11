# Quickstart

This guide walks you through the core STL operations in 5 minutes. By the end, you'll be able to parse, build, validate, query, and use the CLI.

## 1. Parse STL Text

```python
from stl_parser import parse

result = parse("""
[Einstein] -> [Theory_Relativity] ::mod(
  rule="empirical",
  confidence=0.98,
  source="doi:10.1002/andp.19053221004"
)
[Theory_Relativity] -> [Prediction_TimeDilation] ::mod(
  rule="logical",
  confidence=0.99
)
""")

print(f"Valid: {result.is_valid}")           # True
print(f"Statements: {len(result.statements)}")  # 2

# Inspect the first statement
stmt = result.statements[0]
print(f"Source: {stmt.source.name}")          # "Einstein"
print(f"Target: {stmt.target.name}")          # "Theory_Relativity"
print(f"Confidence: {stmt.modifiers.confidence}")  # 0.98
print(f"Rule: {stmt.modifiers.rule}")         # "empirical"
```

## 2. Build Statements Programmatically

Instead of writing STL text by hand, use the builder API:

```python
from stl_parser import stl

# Build a single statement
stmt = (
    stl("[Rain]", "[Flooding]")
    .mod(rule="causal", confidence=0.85, strength=0.8)
    .build()
)
print(str(stmt))
# [Rain] -> [Flooding] ::mod(confidence=0.85, rule="causal", strength=0.8)
```

Build multi-statement documents with `stl_doc()`:

```python
from stl_parser import stl, stl_doc

doc = stl_doc(
    stl("[Rain]", "[Flooding]").mod(rule="causal", confidence=0.85),
    stl("[Flooding]", "[Evacuation]").mod(rule="causal", confidence=0.90),
    stl("[Evacuation]", "[Safety]").mod(rule="causal", confidence=0.95),
)

print(f"Statements: {len(doc.statements)}")  # 3
for s in doc.statements:
    print(f"  {s}")
```

## 3. Serialize to JSON and RDF

```python
from stl_parser import parse, to_json, to_stl
from stl_parser.serializer import to_rdf

result = parse('[Water] -> [H2O] ::mod(rule="definitional", confidence=0.99)')

# To JSON
print(to_json(result, indent=2))

# Back to STL text
print(to_stl(result))

# To RDF/Turtle
print(to_rdf(result, format="turtle"))
```

## 4. Validate Against a Schema

Domain schemas enforce constraints on your STL documents:

```python
from stl_parser import parse, load_schema, validate_against_schema

# Load a domain schema
schema = load_schema("docs/schemas/causal.stl.schema")

# Parse a document
result = parse('[Rain] -> [Flooding] ::mod(rule="causal", confidence=0.85, strength=0.8)')

# Validate — returns SchemaValidationResult
validation = validate_against_schema(result, schema)
if validation.is_valid:
    print("Document is valid against causal schema")
else:
    for err in validation.errors:
        print(f"  {err}")
```

## 5. Clean LLM Output

LLMs often produce malformed STL. The repair pipeline fixes common issues automatically:

```python
from stl_parser import validate_llm_output

# Messy LLM output with multiple issues
raw = "Einstein => Relativity mod(confience=1.5)"

result = validate_llm_output(raw)
print(f"Valid: {result.is_valid}")
print(f"Repairs applied: {len(result.repairs)}")
for r in result.repairs:
    print(f"  - {r}")
```

## 6. Query Statements

Filter and project fields from parsed documents:

```python
from stl_parser import parse, find, find_all, filter_statements, select

result = parse("""
[Rain] -> [Flooding] ::mod(rule="causal", confidence=0.85)
[Sun] -> [Evaporation] ::mod(rule="causal", confidence=0.90)
[Wind] -> [Erosion] ::mod(rule="empirical", confidence=0.70)
""")

# Find first match (special field "source" resolves to source.name)
stmt = find(result, source="Rain")
print(f"Found: {stmt}")

# Find all matching statements
causal = find_all(result, rule="causal")
print(f"Causal statements: {len(causal)}")  # 2

# Filter returns a new ParseResult
high_conf = filter_statements(result, confidence__gte=0.85)
print(f"High confidence: {len(high_conf.statements)} statements")

# Extract a single field from all statements
names = select(result, field="source")
print(names)  # ["Rain", "Sun", "Wind"]

confs = select(result, field="confidence")
print(confs)  # [0.85, 0.9, 0.7]
```

## 7. Use the CLI

Create a file `example.stl`:

```stl
[Einstein] -> [Theory_Relativity] ::mod(rule="empirical", confidence=0.98)
[Theory_Relativity] -> [Prediction_TimeDilation] ::mod(rule="logical", confidence=0.99)
```

Then run:

```bash
# Validate
stl validate example.stl

# Convert to JSON
stl convert example.stl --to json

# Graph analysis
stl analyze example.stl

# Query
stl query example.stl --where "confidence__gte=0.99"
```

---

## What's Next?

- **[Key Concepts](key-concepts.md)** — Understand the STL data model in depth (anchors, paths, modifiers)
- **[Tutorials](../tutorials/)** — Step-by-step guides for each capability
- **[API Reference](../reference/)** — Complete function documentation
