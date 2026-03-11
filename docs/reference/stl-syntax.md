# STL Syntax Quick Reference

One-page reference card for STL (Semantic Tension Language) syntax.

---

## Statement Structure

```
[Source] -> [Target] ::mod(key=value, key=value, ...)
```

| Component | Syntax | Required |
|-----------|--------|----------|
| Source anchor | `[Name]` or `[Namespace:Name]` | Yes |
| Arrow | `->` or `→` | Yes |
| Target anchor | `[Name]` or `[Namespace:Name]` | Yes |
| Modifier block | `::mod(key=value, ...)` | No |

---

## Anchors

```
[Simple_Name]                    # Basic anchor
[Physics:Energy]                 # Namespaced anchor
[Physics.Quantum:Quark]          # Hierarchical namespace
[黄帝内经]                        # Unicode anchor
```

**Valid characters:** Letters (any script), digits, underscores, hyphens (`-`, not as first character). Max 64 characters.

**Invalid:**
```
[]                   # Empty
[ Spaced ]           # Whitespace
[Not Valid!]         # Special characters
[Nested [Anchor]]    # Nesting
```

**Reserved names:** `NULL`, `UNDEFINED`, `ANY`, `NONE`, `TRUE`, `FALSE`, `SYSTEM`, `GLOBAL`, `LOCAL`

---

## Arrows

```
[A] -> [B]           # ASCII arrow
[A] → [B]            # Unicode arrow (U+2192)
```

Both forms are identical. Direction matters: `[A] -> [B]` is not the same as `[B] -> [A]`.

---

## Modifiers

```
[A] -> [B] ::mod(confidence=0.85, rule="causal")
```

### Value Types

| Type | Syntax | Examples |
|------|--------|---------|
| String | `"quoted"` | `rule="causal"`, `source="doi:10.1234"` |
| Float | bare number | `confidence=0.85`, `strength=0.9` |
| Integer | bare number | `priority=5` |
| Boolean | `true` / `false` | `verified=true` |
| DateTime | ISO 8601 string | `timestamp="2025-01-15T10:00:00Z"` |

### Standard Modifier Fields

**Temporal:** `time`, `duration`, `frequency`, `tense`

**Spatial:** `location`, `domain`, `scope`

**Logical:** `confidence` (0.0-1.0), `certainty` (0.0-1.0), `necessity`, `rule`

**Provenance:** `source`, `author`, `timestamp`, `version`

**Affective:** `emotion`, `intensity` (0.0-1.0), `valence`

**Value:** `value`, `alignment`, `priority`

**Causal:** `strength` (0.0-1.0), `cause`, `effect`, `conditionality`

**Cognitive:** `intent`, `focus`, `perspective`

**Mood:** `mood`, `modality`

Any key not listed above is treated as a **custom modifier** and preserved by the parser.

---

## Chained Paths

```
[A] -> [B] -> [C] ::mod(confidence=0.85)
```

Equivalent to two statements. The modifier applies to the last edge (`[B] -> [C]`).

Keep chains to 3-5 nodes maximum. Break longer chains into separate statements.

---

## Multi-line Modifiers

```
[Rain] -> [Flooding] ::mod(
  rule="causal",
  confidence=0.85,
  strength=0.80,
  location="Urban_Area"
)
```

Whitespace and newlines inside `::mod(...)` are ignored.

---

## Multiple Modifier Blocks

```
[Action] -> [Result]
  ::mod(time="Present")
  ::mod(confidence=0.85)
  ::mod(source="doc://report.pdf")
```

Multiple `::mod()` blocks on the same statement are merged. Limit to 5-7 modifier fields per statement total.

---

## Comments

```
# This is a comment
[A] -> [B] ::mod(confidence=0.9)  # Inline comment
```

Comments begin with `#` and extend to end of line.

---

## Rule Types

| Value | Meaning | Example |
|-------|---------|---------|
| `"causal"` | Cause-effect relationship | Rain causes flooding |
| `"logical"` | Logical implication or deduction | Premises imply conclusion |
| `"empirical"` | Evidence-based observation | Experiment confirms theory |
| `"definitional"` | Definition or categorization | Water is H2O |
| `"correlative"` | Statistical correlation | Exercise correlates with health |

---

## Confidence Calibration

| Range | Usage |
|-------|-------|
| 0.95 - 1.0 | Definitional truths, mathematical facts |
| 0.85 - 0.94 | Well-established facts, strong evidence |
| 0.70 - 0.84 | Generally accepted, moderate evidence |
| 0.50 - 0.69 | Probable but uncertain, limited evidence |
| 0.30 - 0.49 | Speculative, weak evidence |
| 0.00 - 0.29 | Highly uncertain, hypothetical |

---

## 9 Anchor Types

| Type | Layer | Purpose |
|------|-------|---------|
| Concept | Semantic | Abstract ideas, theories, categories |
| Relational | Semantic | Logical or semantic relations |
| Event | Entity | Actions, processes, temporal events |
| Entity | Entity | Physical or perceivable objects |
| Name | Entity | Proper nouns (people, places, orgs) |
| Agent | Structural | Active subjects with agency |
| Question | Structural | Open inquiries, hypotheses |
| Verifier | Structural | Evaluation and testing mechanisms |
| PathSegment | Structural | Intermediate states, transitions |

---

## 6 Path Types

| Type | Semantic Function |
|------|-------------------|
| Semantic | Definitional, categorical |
| Action | Agency and intentionality |
| Cognitive | Epistemic relations |
| Causal | Cause-effect mechanisms |
| Inferential | Logical reasoning |
| Reflexive | Self-reference |

---

## Complete Example

```stl
# Scientific knowledge representation
[Theory_Relativity] -> [Prediction_TimeDilation] ::mod(
  rule="logical",
  confidence=0.99,
  author="Einstein",
  source="doi:10.1002/andp.19053221004",
  domain="physics"
)

[Prediction_TimeDilation] -> [Experiment_GPS] ::mod(
  rule="empirical",
  confidence=0.97,
  strength=0.95
)

# Causal chain
[Heavy_Rain] -> [Flooding] ::mod(
  rule="causal",
  confidence=0.85,
  strength=0.80,
  conditionality="Sufficient"
)
```

---

## File Extensions

| Extension | Purpose |
|-----------|---------|
| `.stl` | STL document |
| `.stl.schema` | STL domain schema |

---

## See Also

- [Modifier Reference](modifiers.md) — All 30+ modifier fields
- [Anchor Type Reference](anchor-types.md) — Detailed type guidance
- [Error Codes](error-codes.md) — All error and warning codes
- [CLI Reference](cli.md) — Command-line tools
