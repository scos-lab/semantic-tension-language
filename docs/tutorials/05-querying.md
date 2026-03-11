# Tutorial 5: Querying

Learn how to search, filter, and extract data from STL documents.

**What you'll learn:**
- Find statements with `find()` and `find_all()`
- Filter documents with `filter_statements()`
- Extract fields with `select()`
- Navigate with `stl_pointer()`
- Use comparison operators (`__gt`, `__gte`, `__contains`, etc.)

**Prerequisites:** [Tutorial 4: LLM Pipeline](04-llm-pipeline.md)

---

## Sample Data

All examples in this tutorial use this document:

```python
from stl_parser import parse

doc = parse("""
[Rain] -> [Flooding] ::mod(rule="causal", confidence=0.85, strength=0.8, location="Urban_Area")
[Smoking] -> [Lung_Cancer] ::mod(rule="causal", confidence=0.92, strength=0.85, source="doi:10.1234/study")
[Water] -> [H2O] ::mod(rule="definitional", confidence=0.99)
[Einstein] -> [Theory_Relativity] ::mod(rule="empirical", confidence=0.98, author="Einstein")
[Wind] -> [Erosion] ::mod(rule="causal", confidence=0.70, strength=0.5)
""")
```

## Step 1: Find the First Match

`find()` returns the first statement matching all conditions, or `None`:

```python
from stl_parser import find

# Find by source anchor name
stmt = find(doc, source="Rain")
print(stmt)
# [Rain] -> [Flooding] ::mod(...)

# Find by modifier value
stmt = find(doc, rule="definitional")
print(stmt.source.name)  # "Water"

# No match returns None
stmt = find(doc, source="Nonexistent")
print(stmt)  # None
```

## Step 2: Find All Matches

`find_all()` returns a list of all matching statements:

```python
from stl_parser import find_all

# All causal statements
causal = find_all(doc, rule="causal")
print(f"Causal: {len(causal)}")  # 3

for s in causal:
    print(f"  {s.source.name} -> {s.target.name}")
```

## Step 3: Comparison Operators

Use double-underscore suffixes for comparison operators:

```python
from stl_parser import find_all

# Greater than or equal
high_conf = find_all(doc, confidence__gte=0.90)
print(f"High confidence: {len(high_conf)}")  # 3

# Less than
low_conf = find_all(doc, confidence__lt=0.80)
print(f"Low confidence: {len(low_conf)}")  # 1 (Wind->Erosion at 0.70)

# Not equal
non_causal = find_all(doc, rule__ne="causal")
print(f"Non-causal: {len(non_causal)}")  # 2

# Contains (substring match)
theory = find_all(doc, target__contains="Theory")
print(f"Theory targets: {len(theory)}")  # 1
```

### All Available Operators

| Operator | Syntax | Meaning |
|----------|--------|---------|
| Equality | `field=value` | `field == value` |
| Greater than | `field__gt=value` | `field > value` |
| Greater or equal | `field__gte=value` | `field >= value` |
| Less than | `field__lt=value` | `field < value` |
| Less or equal | `field__lte=value` | `field <= value` |
| Not equal | `field__ne=value` | `field != value` |
| Contains | `field__contains=value` | `value in str(field)` |
| Starts with | `field__startswith=value` | `field.startswith(value)` |
| In list | `field__in=[v1, v2]` | `field in [v1, v2]` |

## Step 4: Multiple Conditions

All conditions are combined with AND logic:

```python
from stl_parser import find_all

# Causal AND high confidence
results = find_all(doc, rule="causal", confidence__gte=0.85)
print(f"High-confidence causal: {len(results)}")  # 2 (Rain, Smoking)
```

## Step 5: Filter Documents

`filter_statements()` returns a new `ParseResult` with only matching statements:

```python
from stl_parser import filter_statements, to_stl

# Get a filtered document
filtered = filter_statements(doc, rule="causal")

print(f"Original: {len(doc.statements)} statements")
print(f"Filtered: {len(filtered.statements)} statements")

# Serialize the filtered result
print(to_stl(filtered))
```

The original document is not modified.

## Step 6: Extract Fields with Select

`select()` extracts a single field value from every statement:

```python
from stl_parser import select

# Extract source names
sources = select(doc, field="source")
print(sources)  # ["Rain", "Smoking", "Water", "Einstein", "Wind"]

# Extract confidence values
confs = select(doc, field="confidence")
print(confs)  # [0.85, 0.92, 0.99, 0.98, 0.7]

# Extract a field that some statements lack
strengths = select(doc, field="strength")
print(strengths)  # [0.8, 0.85, None, None, 0.5]
```

### Special Fields

| Field | Resolves To |
|-------|------------|
| `"source"` | `stmt.source.name` |
| `"target"` | `stmt.target.name` |
| `"source_namespace"` | `stmt.source.namespace` |
| `"target_namespace"` | `stmt.target.namespace` |
| `"arrow"` | `stmt.arrow` |
| Any other | Modifier field (standard or custom) |

## Step 7: Navigate with STL Pointer

`stl_pointer()` accesses nested values using slash-delimited paths, inspired by JSON Pointer (RFC 6901):

```python
from stl_parser import stl_pointer

# Access first statement's source name
name = stl_pointer(doc, "/0/source/name")
print(name)  # "Rain"

# Access second statement's confidence
conf = stl_pointer(doc, "/1/modifiers/confidence")
print(conf)  # 0.92

# Access arrow of third statement
arrow = stl_pointer(doc, "/2/arrow")
print(arrow)  # "→"
```

Path format: `/<statement_index>/<attribute>[/<sub_attribute>...]`

## Step 8: Query via CLI

```bash
# Filter by condition
stl query knowledge.stl --where "rule=causal"

# Multiple conditions
stl query knowledge.stl --where "rule=causal,confidence__gte=0.8"

# Select specific fields
stl query knowledge.stl --select "source,target,confidence"

# Output as JSON
stl query knowledge.stl --where "rule=causal" --format json

# Output as CSV
stl query knowledge.stl --select "source,target,confidence" --format csv

# Just count matches
stl query knowledge.stl --where "confidence__gte=0.9" --count

# Limit results
stl query knowledge.stl --where "rule=causal" --limit 5

# Use STL pointer
stl query knowledge.stl --pointer "/0/source/name"
```

## Step 9: Query on ParseResult Methods

`ParseResult` also has convenience methods that delegate to the query module:

```python
# These are equivalent:
stmt = find(doc, source="Rain")
stmt = doc.find(source="Rain")

# Filter
filtered = doc.filter(rule="causal")
```

---

## Complete Example

```python
from stl_parser import parse, find, find_all, filter_statements, select, stl_pointer

doc = parse("""
[Rain] -> [Flooding] ::mod(rule="causal", confidence=0.85, strength=0.8)
[Smoking] -> [Lung_Cancer] ::mod(rule="causal", confidence=0.92, strength=0.85)
[Water] -> [H2O] ::mod(rule="definitional", confidence=0.99)
[Einstein] -> [Theory_Relativity] ::mod(rule="empirical", confidence=0.98)
[Wind] -> [Erosion] ::mod(rule="causal", confidence=0.70, strength=0.5)
""")

# Find high-confidence causal statements
strong = find_all(doc, rule="causal", confidence__gte=0.85)
print(f"Strong causal relations ({len(strong)}):")
for s in strong:
    print(f"  {s.source.name} -> {s.target.name} (conf={s.modifiers.confidence})")

# Extract all confidence values and compute average
confs = [c for c in select(doc, field="confidence") if c is not None]
avg = sum(confs) / len(confs)
print(f"\nAverage confidence: {avg:.2f}")

# Filter to causal-only document
causal_doc = filter_statements(doc, rule="causal")
print(f"\nCausal subset: {len(causal_doc.statements)} of {len(doc.statements)} statements")

# Navigate specific values
print(f"\nFirst source: {stl_pointer(doc, '/0/source/name')}")
print(f"Third confidence: {stl_pointer(doc, '/2/modifiers/confidence')}")
```

---

**Next:** [Tutorial 6: Streaming I/O](06-streaming-io.md)
