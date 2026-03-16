# STL for AI Agents

> Drop this file into your AI agent's system prompt, instructions, or context.
> After reading it, your agent will be able to write valid STL immediately.

---

## What is STL?

STL (Semantic Tension Language) is a compact notation for structured knowledge. Think of it as **typed, directed edges with metadata** — more expressive than JSON key-value pairs, more token-efficient than verbose schemas.

```
[Source] → [Target] ::mod(key=value, key=value)
```

That's it. Source connects to Target with optional metadata.

---

## Syntax in 60 Seconds

**Anchors** — entities, concepts, events, wrapped in brackets:
```
[Photosynthesis]          # simple
[Physics:Energy]          # namespaced (for disambiguation)
[Albert_Einstein]         # underscore-separated
[黄帝内经]                 # Unicode supported
```

Rules: alphanumeric, `_`, `:` only. No spaces inside brackets. No nesting.

**Arrow** — directional, meaning flows from source to target:
```
[Rain] → [Wet_Ground]    # Unicode arrow
[Rain] -> [Wet_Ground]   # ASCII arrow (equivalent)
```

Direction matters: `[A] → [B]` is not the same as `[B] → [A]`.

**Modifiers** — metadata attached with `::mod(...)`:
```
[Smoking] → [Lung_Cancer] ::mod(
  rule="causal",
  confidence=0.92,
  strength=0.85,
  source="doi:10.1056/NEJMra1603471"
)
```

Values: strings must be quoted (`"causal"`), numbers are bare (`0.92`), floats range 0.0–1.0.

---

## Key Modifiers

You don't need to memorize all modifiers. These six cover 90% of use cases:

| Modifier | Type | Purpose |
|----------|------|---------|
| `confidence` | Float 0–1 | How certain is this relationship? |
| `rule` | String | `"causal"` / `"logical"` / `"empirical"` / `"definitional"` |
| `strength` | Float 0–1 | How strong is the causal/logical link? |
| `source` | String | Where does this knowledge come from? |
| `description` | String | Human-readable explanation |
| `time` | String | Temporal context (ISO 8601 or `"Past"` / `"Present"` / `"Future"`) |

Other available modifiers: `author`, `timestamp`, `domain`, `location`, `certainty`, `emotion`, `intensity`, `intent`, `lesson`, `cause`, `effect`, `conditionality`.

### Confidence Calibration

| Range | Use When |
|-------|----------|
| 0.95–1.0 | Definitions, math facts, direct quotes |
| 0.85–0.94 | Well-established facts, strong evidence |
| 0.70–0.84 | Generally accepted, moderate evidence |
| 0.50–0.69 | Uncertain, limited evidence |
| < 0.50 | Speculative, contested |

---

## Examples

**Causal relationship:**
```stl
[Heavy_Rain] → [Urban_Flooding] ::mod(
  rule="causal",
  confidence=0.85,
  strength=0.80,
  source="NOAA flood data"
)
```

**Definition:**
```stl
[Entropy] → [Measure_Of_Disorder] ::mod(
  rule="definitional",
  confidence=0.97,
  domain="thermodynamics"
)
```

**Empirical finding with source:**
```stl
[Theory_Relativity] → [Prediction_Time_Dilation] ::mod(
  rule="logical",
  confidence=0.99,
  source="doi:10.1002/andp.19053221004",
  author="Einstein"
)
```

**Lesson learned:**
```stl
[Premature_Optimization] → [Project_Delay] ::mod(
  rule="empirical",
  confidence=0.88,
  lesson="Optimize only after profiling. Early optimization adds complexity without measurable gain."
)
```

**Chain (break long chains into segments of ≤ 5):**
```stl
[Observation] → [Hypothesis] → [Experiment] → [Conclusion]
```

**Multiple modifier blocks (layering):**
```stl
[Drug_X] → [Reduced_Inflammation]
  ::mod(rule="causal", confidence=0.82, strength=0.75)
  ::mod(source="doi:10.1234/trial2024", timestamp="2024-06-15")
```

---

## Common Mistakes

```
[Not Valid!]               → WRONG: special characters
[ Spaced Name ]            → WRONG: spaces inside brackets
[A] [B]                    → WRONG: missing arrow
mod(confidence=0.9)        → WRONG: missing :: prefix
::mod(confidence="high")   → WRONG: confidence must be a float
::mod(confidence=1.5)      → WRONG: floats must be 0.0–1.0
[A] → [B] ::mod()          → WRONG: empty modifier adds nothing
```

---

## When to Use STL

STL is useful whenever you need to express **structured relationships with metadata** — knowledge graphs, causal chains, fact databases, decision logs, learning records, or any scenario where you want traceability and confidence attached to knowledge.

Use STL instead of bullet points or free text when:
- The information has a clear **source → target** direction
- You need to track **confidence** or **provenance**
- The knowledge may be **queried, compared, or reasoned over** later

Use plain text when: the content is narrative, conversational, or doesn't have directional structure.

---

## Tooling (Optional)

STL has a Python parser for validation, conversion, and analysis:

```bash
pip install stl-parser
```

```python
from stl_parser import parse, stl

# Parse STL text
result = parse('[Rain] -> [Flooding] ::mod(confidence=0.85)')

# Build programmatically
stmt = stl("[Rain]", "[Flooding]").mod(confidence=0.85, rule="causal").build()
```

Tooling is optional. The syntax is simple enough to generate correctly without validation.

---

## Full Specification

For the complete language spec, modifier reference, domain schemas, and advanced features:
https://github.com/scos-lab/semantic-tension-language

---

*STL is an open standard by [SCOS-Lab](https://github.com/scos-lab). Spec: CC BY 4.0, Code: Apache 2.0.*
