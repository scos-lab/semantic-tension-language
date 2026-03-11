# Tutorial 8: CLI Tools

Learn how to use the `stl` command-line interface for common workflows.

**What you'll learn:**
- Validate, parse, and convert STL files
- Analyze graph structure
- Build statements from the terminal
- Clean LLM output
- Query, diff, and patch documents

**Prerequisites:** [Installation](../getting-started/installation.md) complete, `stl --help` works.

---

## Setup: Create Sample Files

Create `sample.stl`:

```stl
[Rain] -> [Flooding] ::mod(rule="causal", confidence=0.85, strength=0.8)
[Flooding] -> [Evacuation] ::mod(rule="causal", confidence=0.90, strength=0.85)
[Smoking] -> [Lung_Cancer] ::mod(rule="causal", confidence=0.92, source="doi:10.1234/study")
[Water] -> [H2O] ::mod(rule="definitional", confidence=0.99)
[Einstein] -> [Theory_Relativity] ::mod(rule="empirical", confidence=0.98, author="Einstein")
```

---

## Command 1: validate

Check if a file contains valid STL:

```bash
stl validate sample.stl
```

Output:

```
SUCCESS: STL file is valid.
  - Statements found: 5
```

If there are errors, each is listed with its error code and line number.

---

## Command 2: parse

Parse and output the structured result as JSON:

```bash
stl parse sample.stl
```

---

## Command 3: convert

Convert STL to other formats:

```bash
# To JSON
stl convert sample.stl --to json --output sample.json

# To RDF/Turtle
stl convert sample.stl --to rdf --format turtle --output sample.ttl

# To JSON-LD
stl convert sample.stl --to rdf --format json-ld --output sample.jsonld

# To N-Triples
stl convert sample.stl --to rdf --format nt --output sample.nt
```

Without `--output`, results print to stdout.

---

## Command 4: analyze

View graph statistics for an STL document:

```bash
stl analyze sample.stl
```

Output includes:
- Node and edge counts
- Graph density
- Cycle detection
- Node centrality rankings
- Tension metrics

---

## Command 5: build

Build a single statement from the command line:

```bash
# Simple statement
stl build "[Rain]" "[Flooding]"

# With modifiers
stl build "[Rain]" "[Flooding]" --mod "rule=causal,confidence=0.85,strength=0.8"

# Save to file
stl build "[Rain]" "[Flooding]" --mod "rule=causal,confidence=0.85" --output new.stl
```

Modifier values are auto-typed: numbers become floats/ints, `true`/`false` become booleans.

---

## Command 6: clean

Clean and repair LLM-generated output:

```bash
# Basic clean
stl clean llm_output.txt

# Show what was repaired
stl clean llm_output.txt --show-repairs

# Clean and validate against a schema
stl clean llm_output.txt --schema docs/schemas/causal.stl.schema

# Save cleaned output
stl clean llm_output.txt --output cleaned.stl
```

### Example: Create a messy file

Create `messy.txt`:

```
Here's some STL:
Einstein => Relativity mod(confience=0.98)
Rain --> Flooding ::mod(rule=causal, confidence=1.2)
```

```bash
stl clean messy.txt --show-repairs
```

The tool will:
1. Strip prose lines
2. Fix arrow syntax (`=>` → `->`, `-->` → `->`)
3. Add missing `::` prefix
4. Fix typos (`confience` → `confidence`)
5. Clamp values (`1.2` → `1.0`)

---

## Command 7: schema-validate

Validate a document against a domain schema:

```bash
stl schema-validate sample.stl --schema docs/schemas/causal.stl.schema
```

Exit code 0 means valid, 1 means validation errors.

---

## Command 8: query

Search and filter STL documents:

```bash
# Filter by modifier value
stl query sample.stl --where "rule=causal"

# Multiple conditions (AND logic)
stl query sample.stl --where "rule=causal,confidence__gte=0.9"

# Select specific fields
stl query sample.stl --select "source,target,confidence"

# Combine filter and select
stl query sample.stl --where "rule=causal" --select "source,target,confidence,strength"
```

### Output Formats

```bash
# Table (default) — formatted with Rich
stl query sample.stl --where "rule=causal"

# JSON
stl query sample.stl --where "rule=causal" --format json

# STL (re-serialize matches)
stl query sample.stl --where "rule=causal" --format stl

# CSV
stl query sample.stl --select "source,target,confidence" --format csv
```

### Other Options

```bash
# Count matches only
stl query sample.stl --where "confidence__gte=0.9" --count

# Limit results
stl query sample.stl --where "rule=causal" --limit 3

# STL pointer (access specific value)
stl query sample.stl --pointer "/0/source/name"
```

### Operator Reference (for --where)

| Syntax | Meaning | Example |
|--------|---------|---------|
| `field=value` | Equals | `rule=causal` |
| `field__gt=value` | Greater than | `confidence__gt=0.8` |
| `field__gte=value` | Greater or equal | `confidence__gte=0.9` |
| `field__lt=value` | Less than | `confidence__lt=0.5` |
| `field__lte=value` | Less or equal | `confidence__lte=0.7` |
| `field__ne=value` | Not equal | `rule__ne=logical` |
| `field__contains=value` | Contains substring | `source__contains=doi` |
| `field__startswith=value` | Starts with | `source__startswith=Theory` |
| `field__in=a\|b` | In list (pipe-separated) | `rule__in=causal\|empirical` |

---

## Command 9: diff

Compare two STL files:

```bash
# Human-readable text diff
stl diff v1.stl v2.stl

# JSON diff (machine-readable)
stl diff v1.stl v2.stl --format json

# Summary only
stl diff v1.stl v2.stl --summary

# Quiet mode (exit code: 0=same, 1=different)
stl diff v1.stl v2.stl --quiet
```

### Example

Create `v1.stl`:

```stl
[Rain] -> [Flooding] ::mod(rule="causal", confidence=0.85)
[Wind] -> [Erosion] ::mod(rule="causal", confidence=0.70)
```

Create `v2.stl`:

```stl
[Rain] -> [Flooding] ::mod(rule="causal", confidence=0.90)
[Heat] -> [Drought] ::mod(rule="causal", confidence=0.75)
```

```bash
stl diff v1.stl v2.stl
```

Output:

```
~ [Rain] -> [Flooding]
    confidence: 0.85 -> 0.9
- [Wind] -> [Erosion] ::mod(confidence=0.7, rule="causal")
+ [Heat] -> [Drought] ::mod(confidence=0.75, rule="causal")

1 added, 1 removed, 1 modified, 0 unchanged
```

---

## Command 10: patch

Apply a JSON diff to an STL file:

```bash
# Generate JSON diff
stl diff v1.stl v2.stl --format json > changes.json

# Apply patch
stl patch v1.stl changes.json --output patched.stl

# Print to stdout
stl patch v1.stl changes.json
```

---

## Common Workflows

### Validate, Fix, Query Pipeline

```bash
# 1. Clean LLM output
stl clean raw_output.txt --output cleaned.stl

# 2. Validate against domain schema
stl schema-validate cleaned.stl --schema docs/schemas/medical.stl.schema

# 3. Query for relevant statements
stl query cleaned.stl --where "confidence__gte=0.8" --format json > results.json
```

### Version Comparison

```bash
# Compare versions
stl diff knowledge_v1.stl knowledge_v2.stl

# Save diff for later
stl diff knowledge_v1.stl knowledge_v2.stl --format json > v1_to_v2.json

# Reproduce v2 from v1
stl patch knowledge_v1.stl v1_to_v2.json --output knowledge_v2_reproduced.stl
```

### Build and Analyze

```bash
# Build statements
stl build "[CO2]" "[Warming]" --mod "rule=causal,confidence=0.95" --output climate.stl
stl build "[Warming]" "[SeaLevel]" --mod "rule=causal,confidence=0.88" >> climate.stl

# Analyze the graph
stl analyze climate.stl
```

---

**This concludes the tutorial series.** For complete API documentation, see the [Reference](../reference/) section.
