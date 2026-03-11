# Tutorial 4: LLM Pipeline

Learn how to clean, repair, and validate LLM-generated STL output.

**What you'll learn:**
- Clean raw LLM output with `clean()`
- Repair structural issues with `repair()`
- Run the full 3-stage pipeline with `validate_llm_output()`
- Generate LLM prompt templates with `prompt_template()`
- Inspect repair actions

**Prerequisites:** [Tutorial 3: Schema Validation](03-schema-validation.md)

---

## The Problem

LLMs often produce malformed STL. Common issues include:

- Using `=>` or `-->` instead of `->`
- Omitting `::` prefix on modifiers
- Missing brackets around anchor names
- Unquoted string values
- Confidence values out of range (e.g., `1.5`)
- Spelling errors in modifier keys (e.g., `confience`)
- Wrapping output in code fences or adding prose

The LLM pipeline fixes these automatically through three stages: **clean → repair → parse**.

## Step 1: The Full Pipeline

`validate_llm_output()` runs all three stages in one call:

```python
from stl_parser import validate_llm_output

raw = "Einstein => Relativity mod(confience=1.5)"

result = validate_llm_output(raw)

print(f"Valid: {result.is_valid}")
print(f"Statements: {len(result.statements)}")
print(f"Repairs: {len(result.repairs)}")
print(f"Cleaned text: {result.cleaned_text}")

for r in result.repairs:
    print(f"  [{r.type}] {r.description}")
```

The result is an `LLMValidationResult` with:
- `is_valid` — whether the repaired text parsed successfully
- `statements` — parsed `Statement` objects
- `repairs` — list of `RepairAction` objects describing what was fixed
- `cleaned_text` — the text after cleaning and repair
- `original_text` — the original input

## Step 2: Stage 1 — Clean

The `clean()` function handles text-level normalization:

```python
from stl_parser.llm import clean

raw = """
Here's the STL output:

```stl
[Einstein] => [Relativity] ::mod(
  rule="empirical",
  confidence=0.98
)
```

This shows the relationship between Einstein and his theory.
"""

cleaned_text, repairs = clean(raw)
print(cleaned_text)
# [Einstein] -> [Relativity] ::mod(rule="empirical", confidence=0.98)

for r in repairs:
    print(f"  {r.description}")
```

Clean handles:
- Extracting STL from code fences
- Stripping prose lines
- Normalizing arrow variants (`=>`, `-->`, `→`) to `->`
- Merging multi-line statements
- Removing markdown escapes

## Step 3: Stage 2 — Repair

The `repair()` function fixes structural issues:

```python
from stl_parser.llm import repair

text = "[A] -> [B] mod(confidence=1.5, confience=0.8)"

repaired_text, repairs = repair(text)
print(repaired_text)

for r in repairs:
    print(f"  [{r.type}] {r.original} -> {r.repaired}")
    print(f"    {r.description}")
```

Repair handles:
- Adding missing `::` prefix before `mod(`
- Adding missing brackets around bare anchor names
- Clamping out-of-range values (e.g., `confidence=1.5` → `confidence=1.0`)
- Fixing common typos in modifier keys
- Quoting unquoted string values

## Step 4: Inspect Repair Actions

Each `RepairAction` provides detailed information:

```python
from stl_parser import validate_llm_output

result = validate_llm_output("A => B mod(confience=1.5)")

for r in result.repairs:
    print(f"Type:        {r.type}")
    print(f"Line:        {r.line}")
    print(f"Original:    {r.original}")
    print(f"Repaired:    {r.repaired}")
    print(f"Description: {r.description}")
    print()
```

## Step 5: Pipeline with Schema Validation

Add a schema to validate the repaired output against domain constraints:

```python
from stl_parser import validate_llm_output, load_schema

schema = load_schema("docs/schemas/causal.stl.schema")

result = validate_llm_output(
    "[Rain] -> [Flooding] mod(rule=causal, confidence=0.85, strength=0.8)",
    schema=schema
)

print(f"Valid: {result.is_valid}")
print(f"Schema result: {result.schema_result}")
```

## Step 6: Generate LLM Prompt Templates

Use `prompt_template()` to generate instruction prompts for LLMs:

```python
from stl_parser import prompt_template

# Basic prompt
prompt = prompt_template()
print(prompt)
# Outputs STL syntax instructions suitable as a system message
```

With a schema, the prompt includes domain-specific constraints:

```python
from stl_parser import prompt_template, load_schema

schema = load_schema("docs/schemas/medical.stl.schema")
prompt = prompt_template(schema=schema)
print(prompt)
# Includes: required fields, anchor patterns, value ranges
```

## Step 7: CLI Usage

```bash
# Clean a file with LLM output
stl clean llm_output.txt

# Show repair actions
stl clean llm_output.txt --show-repairs

# Clean and validate against schema
stl clean llm_output.txt --schema docs/schemas/causal.stl.schema

# Save cleaned output
stl clean llm_output.txt --output cleaned.stl
```

---

## Complete Example

```python
from stl_parser import validate_llm_output, load_schema

# Simulated messy LLM output
raw_llm_output = """
Based on medical knowledge:

```stl
Aspirin => PainRelief mod(
  rule=causal,
  confience=0.88,
  strength=0.80,
  source=doi:10.1234/pharma
)
Smoking --> LungCancer ::mod(
  rule="causal",
  confidence=1.2,
  strength=0.85
)
```

These are well-established medical relationships.
"""

# Run full pipeline
result = validate_llm_output(raw_llm_output)

print(f"Valid: {result.is_valid}")
print(f"Statements parsed: {len(result.statements)}")
print(f"Repairs applied: {len(result.repairs)}")
print()

# Show what was fixed
for r in result.repairs:
    print(f"  [{r.type}] {r.description}")

print()

# Show parsed statements
for stmt in result.statements:
    print(f"  {stmt}")
```

---

**Next:** [Tutorial 5: Querying](05-querying.md)
