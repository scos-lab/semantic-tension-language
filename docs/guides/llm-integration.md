# How-To: Integrate STL with LLMs

Use STL's LLM pipeline to get structured knowledge from ChatGPT, Claude, and other language models. This guide covers prompt engineering, output cleaning, validation, and schema enforcement.

**Prerequisites:** Familiarity with [STL syntax](../reference/stl-syntax.md) and basic LLM API usage.

---

## Overview

The LLM integration pipeline has three stages:

```
Raw LLM Output → clean() → repair() → parse() → Validated STL
```

The `validate_llm_output()` function runs all three stages in one call.

---

## Step 1: Generate Prompt Templates

Use `prompt_template()` to generate STL-aware prompts for your LLM:

```python
from stl_parser.llm import prompt_template

# Basic prompt (no schema constraints)
prompt = prompt_template()
print(prompt)
```

With a domain schema:

```python
from stl_parser.schema import load_schema
from stl_parser.llm import prompt_template

schema = load_schema("scientific.stl.schema")
prompt = prompt_template(schema=schema)
```

The generated prompt includes STL syntax rules, modifier reference, and schema constraints — everything the LLM needs to produce valid output.

---

## Step 2: Call Your LLM

Append your domain question to the template and send to any LLM API:

```python
import openai  # or anthropic, etc.

system_prompt = prompt_template()
user_question = "Represent the causal chain from smoking to lung cancer, including evidence."

# OpenAI example
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_question}
    ]
)
raw_output = response.choices[0].message.content
```

```python
# Anthropic example
import anthropic

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    system=system_prompt,
    messages=[{"role": "user", "content": user_question}]
)
raw_output = response.content[0].text
```

---

## Step 3: Validate and Clean the Output

### Quick Validation (one call)

```python
from stl_parser.llm import validate_llm_output

result = validate_llm_output(raw_output)

if result.is_valid:
    print(f"Parsed {len(result.statements)} statements")
    for stmt in result.statements:
        print(f"  {stmt.source.name} -> {stmt.target.name}")
else:
    print("Validation failed:")
    for error in result.errors:
        print(f"  {error}")
```

### With Schema Enforcement

```python
from stl_parser.schema import load_schema
from stl_parser.llm import validate_llm_output

schema = load_schema("scientific.stl.schema")
result = validate_llm_output(raw_output, schema=schema)

if result.schema_result and not result.schema_result.is_valid:
    print("Schema violations:")
    for error in result.schema_result.errors:
        print(f"  {error.code}: {error.message}")
```

---

## Step 4: Inspect Repairs

The pipeline automatically fixes common LLM mistakes. Inspect what was repaired:

```python
result = validate_llm_output(raw_output)

for repair in result.repairs:
    print(f"[{repair.type}] {repair.description}")
    print(f"  Before: {repair.original}")
    print(f"  After:  {repair.repaired}")
```

Common repairs:
- Missing `::` prefix on modifiers
- Unquoted string values
- Markdown fences removed
- Extra whitespace normalized
- Mismatched brackets fixed

---

## Step 5: Manual Pipeline (Advanced)

For more control, run each stage separately:

```python
from stl_parser.llm import clean, repair
from stl_parser import parse

# Stage 1: Clean (remove markdown fences, normalize whitespace)
cleaned_text, clean_actions = clean(raw_output)

# Stage 2: Repair (fix common syntax errors)
repaired_text, repair_actions = repair(cleaned_text)

# Stage 3: Parse
result = parse(repaired_text)

print(f"Clean actions: {len(clean_actions)}")
print(f"Repair actions: {len(repair_actions)}")
print(f"Statements: {len(result.statements)}")
print(f"Errors: {len(result.errors)}")
```

---

## Full Example: Knowledge Extraction Pipeline

```python
from stl_parser.llm import prompt_template, validate_llm_output
from stl_parser.schema import load_schema
from stl_parser import to_json

# 1. Prepare prompt
schema = load_schema("scientific.stl.schema")
system_prompt = prompt_template(schema=schema)

# 2. Simulate LLM output (replace with actual API call)
llm_output = """
Here are the relationships:

[Smoking] -> [Lung_Cancer] ::mod(
  rule="causal",
  confidence=0.92,
  strength=0.88,
  source="doi:10.1016/cancer.2020.001"
)

[Lung_Cancer] -> [Mortality] ::mod(
  rule="causal",
  confidence=0.85,
  strength=0.75,
  source="WHO_Report_2023"
)

[Exercise] -> [Lung_Cancer] ::mod(
  rule="correlative",
  confidence=0.65,
  strength=0.40,
  source="doi:10.1016/prevention.2021.042"
)
"""

# 3. Validate and clean
result = validate_llm_output(llm_output, schema=schema)

if result.is_valid:
    # 4. Use the structured data
    print(to_json(result))

    for stmt in result.statements:
        conf = getattr(stmt.modifier, 'confidence', None)
        print(f"{stmt.source.name} -> {stmt.target.name} (confidence={conf})")
else:
    print("Failed to parse LLM output")
    for error in result.errors:
        print(f"  {error}")
```

---

## CLI Usage

Clean LLM output from the command line:

```bash
# Basic clean
stl clean llm_output.txt --output cleaned.stl

# With schema validation
stl clean llm_output.txt --schema scientific.stl.schema --output cleaned.stl

# Show what was repaired
stl clean llm_output.txt --show-repairs
```

---

## Tips for Better LLM Output

1. **Always use `prompt_template()`** — it includes syntax rules and modifier reference
2. **Add schema constraints** — the template includes required/optional fields from your schema
3. **Ask for few statements** — request 3-10 statements per call, not 100
4. **Request specific modifiers** — "Include confidence scores and source references"
5. **Iterate on failures** — if validation fails, feed errors back to the LLM for correction

---

## Error Handling

```python
from stl_parser.llm import validate_llm_output
from stl_parser.errors import STLLLMError

try:
    result = validate_llm_output(raw_output)
except STLLLMError as e:
    print(f"LLM pipeline error: {e}")
```

| Error Code | Meaning |
|------------|---------|
| E700 | Cannot clean the input text |
| E701 | Repair operation failed |
| E702 | Cleaned output fails validation |

---

## See Also

- [Tutorial: LLM Pipeline](../tutorials/04-llm-pipeline.md) — Step-by-step tutorial
- [API: llm](../reference/api/llm.md) — Full API reference
- [How-To: Custom Schemas](custom-schemas.md) — Create domain schemas for LLM validation
