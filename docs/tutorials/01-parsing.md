# Tutorial 1: Parsing STL

Learn how to parse STL text and files into structured Python objects.

**What you'll learn:**
- Parse STL text with `parse()`
- Parse STL files with `parse_file()`
- Inspect `ParseResult`, `Statement`, `Anchor`, and `Modifier` objects
- Handle errors and warnings
- Work with multi-line statements and mixed-content files

**Prerequisites:** [Installation](../getting-started/installation.md) complete.

---

## Step 1: Parse STL Text

```python
from stl_parser import parse

text = '[Einstein] -> [Theory_Relativity] ::mod(rule="empirical", confidence=0.98)'
result = parse(text)

print(result.is_valid)                    # True
print(len(result.statements))            # 1
print(len(result.errors))                # 0
```

The `parse()` function returns a `ParseResult` containing statements, errors, and warnings.

## Step 2: Inspect Statements

Each `Statement` has a source anchor, target anchor, and optional modifiers:

```python
stmt = result.statements[0]

# Source anchor
print(stmt.source.name)       # "Einstein"
print(stmt.source.namespace)   # None

# Target anchor
print(stmt.target.name)        # "Theory_Relativity"

# Arrow
print(stmt.arrow)              # "→"

# Modifiers
print(stmt.modifiers.rule)        # "empirical"
print(stmt.modifiers.confidence)  # 0.98
```

## Step 3: Parse Multiple Statements

```python
result = parse("""
[Rain] -> [Flooding] ::mod(rule="causal", confidence=0.85, strength=0.8)
[Flooding] -> [Evacuation] ::mod(rule="causal", confidence=0.90)
[Smoking] -> [Lung_Cancer] ::mod(rule="causal", confidence=0.92, source="doi:10.1234/example")
""")

print(f"Parsed {len(result.statements)} statements")  # 3

for stmt in result.statements:
    print(f"  {stmt.source.name} -> {stmt.target.name} (conf={stmt.modifiers.confidence})")
```

## Step 4: Parse Multi-Line Statements

The parser automatically merges multi-line statements — useful for LLM output:

```python
result = parse("""
[Theory_Relativity] -> [Prediction_TimeDilation] ::mod(
  rule="logical",
  confidence=0.99,
  author="Einstein",
  source="doi:10.1002/andp.19053221004",
  timestamp="1905-09-26"
)
""")

stmt = result.statements[0]
print(stmt.modifiers.author)      # "Einstein"
print(stmt.modifiers.timestamp)   # "1905-09-26"
```

## Step 5: Parse Unicode Content

STL natively supports Chinese, Arabic, and all Unicode scripts:

```python
result = parse("""
[黄帝内经] -> [素问] ::mod(rule="definitional", confidence=0.95, domain="TCM")
""")

stmt = result.statements[0]
print(stmt.source.name)   # "黄帝内经"
print(stmt.target.name)   # "素问"
```

## Step 6: Namespaced Anchors

Use namespaces to disambiguate anchors across domains:

```python
result = parse("""
[Physics:Energy] -> [Physics:Mass] ::mod(rule="logical", confidence=0.99)
[Psychology:Energy] -> [Psychology:Motivation] ::mod(rule="causal", confidence=0.80)
""")

for stmt in result.statements:
    print(f"  {stmt.source.namespace}:{stmt.source.name} -> {stmt.target.name}")
# Output:
#   Physics:Energy -> Mass
#   Psychology:Energy -> Motivation
```

## Step 7: Handle Parse Errors

When the parser encounters invalid syntax, errors are captured rather than thrown:

```python
result = parse('[A] -> ::mod(confidence=0.5)')

print(result.is_valid)   # False
for error in result.errors:
    print(f"  [{error.code}] {error.message}")
    if error.suggestion:
        print(f"    Suggestion: {error.suggestion}")
```

Warnings indicate potential issues that don't prevent parsing:

```python
if result.warnings:
    for warning in result.warnings:
        print(f"  [{warning.code}] {warning.message}")
```

## Step 8: Parse Files

Use `parse_file()` to parse `.stl` files directly:

```python
from stl_parser import parse_file

result = parse_file("knowledge_base.stl")
print(f"Valid: {result.is_valid}, Statements: {len(result.statements)}")
```

### Extraction Modes

`parse_file()` supports extracting STL from mixed-content files (e.g., Markdown):

```python
# Auto-detect (default) — tries fenced blocks first, then heuristic
result = parse_file("notes.md", mode="auto")

# Only extract from ```stl code fences
result = parse_file("notes.md", mode="fenced")

# Pattern matching to find STL lines
result = parse_file("notes.md", mode="heuristic")

# Treat entire file as pure STL (no extraction)
result = parse_file("pure.stl", mode="strict")
```

## Step 9: Serialize Results

Convert parsed results to different formats:

```python
from stl_parser import parse, to_json, to_stl, to_dict
from stl_parser.serializer import to_rdf

result = parse('[Water] -> [H2O] ::mod(rule="definitional", confidence=0.99)')

# To JSON string
print(to_json(result, indent=2))

# Back to STL text
print(to_stl(result))
# Output: [Water] -> [H2O] ::mod(confidence=0.99, rule="definitional")

# To Python dict
d = to_dict(result)

# To RDF/Turtle
print(to_rdf(result, format="turtle"))
```

## Step 10: Custom Modifiers

Any modifier key not in the standard set is stored as an extra field on the Modifier object:

```python
result = parse('[Drug_X] -> [Effect_Y] ::mod(confidence=0.85, dosage="500mg", trial_id="NCT123")')

stmt = result.statements[0]
print(stmt.modifiers.confidence)                  # 0.85 (standard field)
print(getattr(stmt.modifiers, "dosage"))          # "500mg" (extra field)
print(getattr(stmt.modifiers, "trial_id"))        # "NCT123" (extra field)
```

---

## Complete Example

```python
from stl_parser import parse, to_json

text = """
# Physics knowledge graph
[Theory_Relativity] -> [Prediction_TimeDilation] ::mod(
  rule="logical", confidence=0.99, author="Einstein"
)
[Prediction_TimeDilation] -> [Experiment_GPS] ::mod(
  rule="empirical", confidence=0.97, source="doi:10.1103/PhysRevLett.45.2081"
)
[Experiment_GPS] -> [Observation_ClockOffset] ::mod(
  rule="causal", confidence=0.98, strength=0.99
)
"""

result = parse(text)

if result.is_valid:
    print(f"Parsed {len(result.statements)} statements successfully\n")
    for stmt in result.statements:
        src = stmt.source.name
        tgt = stmt.target.name
        conf = stmt.modifiers.confidence
        rule = stmt.modifiers.rule
        print(f"  {src} -> {tgt}  [{rule}, conf={conf}]")
else:
    print("Parse errors:")
    for err in result.errors:
        print(f"  {err.code}: {err.message}")
```

---

**Next:** [Tutorial 2: Building STL Programmatically](02-building.md)
