# Tutorial 2: Building STL Programmatically

Learn how to construct STL statements in code using the builder API, without writing raw text.

**What you'll learn:**
- Build single statements with `stl()`
- Set modifiers with `.mod()`
- Build multi-statement documents with `stl_doc()`
- Use namespaces and custom modifiers
- Convert built statements to text and JSON

**Prerequisites:** [Tutorial 1: Parsing](01-parsing.md)

---

## Step 1: Build a Simple Statement

```python
from stl_parser import stl

stmt = stl("[Rain]", "[Flooding]").build()
print(str(stmt))
# [Rain] -> [Flooding]
```

The `stl()` function takes source and target anchor strings, returning a `StatementBuilder`. Call `.build()` to produce the final `Statement` object.

## Step 2: Add Modifiers

Chain `.mod()` to add modifier key-value pairs:

```python
stmt = (
    stl("[Rain]", "[Flooding]")
    .mod(rule="causal", confidence=0.85, strength=0.8)
    .build()
)
print(str(stmt))
# [Rain] -> [Flooding] ::mod(confidence=0.85, rule="causal", strength=0.8)
```

You can call `.mod()` multiple times — later calls override earlier values for the same key:

```python
stmt = (
    stl("[A]", "[B]")
    .mod(confidence=0.5)
    .mod(confidence=0.9, rule="causal")  # overrides confidence
    .build()
)
print(stmt.modifiers.confidence)  # 0.9
```

## Step 3: Anchor Formats

The builder accepts several anchor formats:

```python
# With brackets
stl("[Rain]", "[Flooding]")

# Without brackets (added automatically)
stl("Rain", "Flooding")

# With namespace
stl("Physics:Energy", "Physics:Mass")
stl("[Physics:Energy]", "[Physics:Mass]")
```

All produce valid statements with properly constructed `Anchor` objects.

## Step 4: Build Multi-Statement Documents

Use `stl_doc()` to combine multiple builders into a `ParseResult`:

```python
from stl_parser import stl, stl_doc

doc = stl_doc(
    stl("[Rain]", "[Flooding]").mod(rule="causal", confidence=0.85),
    stl("[Flooding]", "[Evacuation]").mod(rule="causal", confidence=0.90),
    stl("[Evacuation]", "[Safety]").mod(rule="causal", confidence=0.95),
)

print(f"Statements: {len(doc.statements)}")  # 3
print(doc.is_valid)                           # True

for s in doc.statements:
    print(f"  {s}")
```

You can mix `StatementBuilder` and pre-built `Statement` objects:

```python
pre_built = stl("[A]", "[B]").mod(confidence=0.9).build()

doc = stl_doc(
    pre_built,                                          # Statement object
    stl("[C]", "[D]").mod(rule="logical"),               # StatementBuilder
)
```

## Step 5: Custom Modifiers

Any key not in the standard modifier set is stored as a custom modifier:

```python
stmt = (
    stl("[Drug_Aspirin]", "[Effect_PainRelief]")
    .mod(confidence=0.92, rule="causal", dosage="500mg", trial_id="NCT123")
    .build()
)

print(stmt.modifiers.confidence)  # 0.92 (standard)
print(stmt.modifiers.custom)      # {"dosage": "500mg", "trial_id": "NCT123"}
```

## Step 6: Validation

The builder validates modifier values at two levels:

1. **Pydantic field validation** — enforces type and range constraints (e.g., confidence 0.0-1.0)
2. **Semantic validation** — checks for contradictions and completeness (via `.build()`)

```python
from stl_parser import stl

# This raises STLBuilderError — confidence must be 0.0-1.0
try:
    stl("[A]", "[B]").mod(confidence=1.5).build()
except Exception as e:
    print(f"Error: {e}")
```

Use `.no_validate()` to skip semantic validation (Step 2), while Pydantic field constraints still apply:

```python
# Skips semantic validation, but Pydantic still enforces field ranges
stmt = stl("[A]", "[B]").mod(confidence=0.95).no_validate().build()
```

## Step 7: Serialize Built Statements

Built statements work with all serialization functions:

```python
from stl_parser import stl, stl_doc, to_json, to_stl
from stl_parser.serializer import to_rdf

doc = stl_doc(
    stl("[Einstein]", "[Relativity]").mod(rule="empirical", confidence=0.98),
    stl("[Relativity]", "[TimeDilation]").mod(rule="logical", confidence=0.99),
)

# To STL text
print(to_stl(doc))

# To JSON
print(to_json(doc, indent=2))

# To RDF/Turtle
print(to_rdf(doc, format="turtle"))
```

## Step 8: Build with Namespaces

```python
doc = stl_doc(
    stl("[Physics:Energy]", "[Physics:Mass]").mod(rule="logical", confidence=0.99),
    stl("[Psychology:Energy]", "[Psychology:Motivation]").mod(rule="causal", confidence=0.80),
)

for s in doc.statements:
    print(f"  {s.source.namespace}:{s.source.name} -> {s.target.name}")
```

---

## Complete Example

```python
from stl_parser import stl, stl_doc, to_json

# Build a causal chain about climate
doc = stl_doc(
    stl("[CO2_Emissions]", "[Greenhouse_Effect]")
        .mod(rule="causal", confidence=0.95, strength=0.90,
             source="IPCC_AR6_2021"),

    stl("[Greenhouse_Effect]", "[Global_Warming]")
        .mod(rule="causal", confidence=0.93, strength=0.85),

    stl("[Global_Warming]", "[Sea_Level_Rise]")
        .mod(rule="causal", confidence=0.88, strength=0.75,
             time="2100", domain="climate_science"),

    stl("[Global_Warming]", "[Extreme_Weather]")
        .mod(rule="causal", confidence=0.85, strength=0.70),
)

print(f"Built {len(doc.statements)} statements\n")

# Print as STL
for s in doc.statements:
    print(s)

# Export as JSON
print("\n" + to_json(doc, indent=2))
```

---

**Next:** [Tutorial 3: Schema Validation](03-schema-validation.md)
