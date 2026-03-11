# Key Concepts

This guide explains the foundational concepts of Semantic Tension Language. After reading, you'll understand anchors, paths, modifiers, and how STL differs from other data formats.

## The Tension-Path Model

STL structures knowledge as **directed statements** where meaning flows from a source to a target:

```
[Source] -> [Target] ::mod(metadata)
```

This is called the **tension-path model**. Each statement represents a semantic relation — a piece of structured knowledge with direction, type, and provenance.

Think of it like this:

| Concept | STL Term | Example |
|---------|----------|---------|
| Nodes | **Anchors** | `[Einstein]`, `[Theory_Relativity]` |
| Edges | **Paths** (arrows) | `->` or `→` |
| Edge metadata | **Modifiers** | `::mod(confidence=0.98, rule="empirical")` |

Together, a collection of STL statements forms a **knowledge graph** — traceable, verifiable, and machine-processable.

## Anchors

An **anchor** is a node in the knowledge graph. It represents an entity, concept, event, or state.

### Syntax

```stl
[AnchorName]
[Namespace:AnchorName]
```

Rules:
- Enclosed in square brackets `[...]`
- Names use alphanumeric characters, underscores, and Unicode letters
- No spaces, no special characters (except `_`, `-`, and `:`)
- Maximum 64 characters recommended

### Naming Conventions

```stl
[Gravity]                    # Simple concept
[Theory_Relativity]          # Underscore separation
[UniversalGravitation]       # PascalCase
[Physics:Energy]             # Namespaced (disambiguates from Psychology:Energy)
[Event_2025_Summit]          # Dated event
```

### Unicode Support

STL natively supports Chinese, Arabic, and all Unicode scripts:

```stl
[黄帝内经] -> [素问] ::mod(rule="definitional", confidence=0.95)
```

### 9 Anchor Types

STL defines 9 canonical anchor types across three layers:

**Semantic Layer** — abstract concepts and relations

| Type | Purpose | Examples |
|------|---------|----------|
| **Concept** | Ideas, theories, categories | `[Freedom]`, `[Energy]`, `[Entropy]` |
| **Relational** | Logical or semantic relations | `[Cause]`, `[Effect]`, `[Identity]` |

**Entity Layer** — concrete objects and events

| Type | Purpose | Examples |
|------|---------|----------|
| **Event** | Actions, processes, temporal events | `[War]`, `[Conference]`, `[Migration]` |
| **Entity** | Physical or perceivable objects | `[Apple]`, `[Table]`, `[Galaxy]` |
| **Name** | Uniquely identified named entities | `[Einstein]`, `[London]`, `[Google]` |

**Structural Layer** — meta-linguistic and reasoning

| Type | Purpose | Examples |
|------|---------|----------|
| **Agent** | Active or cognitive subjects | `[Researcher]`, `[AI_System]` |
| **Question** | Points of inquiry, unresolved tension | `[Question]`, `[Hypothesis]` |
| **Verifier** | Evaluation and validation mechanisms | `[Test]`, `[Criterion]` |
| **PathSegment** | Intermediate states, transitions | `[Process]`, `[Transition]` |

Anchor types are optional classifications — the parser accepts any valid anchor name regardless of type.

## Paths (Arrows)

A **path** is the directional arrow connecting two anchors. Direction matters: `[A] -> [B]` is different from `[B] -> [A]`.

### Syntax

Two equivalent forms:

```stl
[A] -> [B]     # ASCII arrow
[A] → [B]      # Unicode arrow (U+2192)
```

### Path Types

Paths carry implicit semantic meaning based on context:

| Path Type | Meaning | Example |
|-----------|---------|---------|
| **Semantic** | Definition, categorization | `[Mammal] -> [Dog]` |
| **Causal** | Cause and effect | `[Rain] -> [Flooding]` |
| **Inferential** | Logical reasoning | `[Premise] -> [Conclusion]` |
| **Action** | Agency and intentionality | `[Researcher] -> [Publish]` |
| **Cognitive** | Epistemic relations | `[Observer] -> [Phenomenon]` |
| **Reflexive** | Self-reference | `[Self] -> [Self]` |

### Chained Paths

Multiple anchors can be chained in a single statement:

```stl
[Theory] -> [Experiment] -> [Observation] -> [Law]
```

This expands to three separate statements internally. Keep chains to 3-5 nodes maximum for readability.

## Modifiers

**Modifiers** attach metadata to a statement. They carry provenance, confidence, temporal context, and other dimensions.

### Syntax

```stl
[A] -> [B] ::mod(key=value, key=value, ...)
```

Rules:
- Always prefixed with `::`
- Key-value pairs inside `mod(...)`
- String values are quoted: `rule="causal"`
- Numeric values are unquoted: `confidence=0.85`
- Comma-separated

### Modifier Categories

STL defines 30+ standard modifier fields across 9 categories:

#### Logical (most important for knowledge graphs)

| Field | Type | Range | Purpose |
|-------|------|-------|---------|
| `confidence` | float | 0.0 - 1.0 | How confident is this statement? |
| `certainty` | float | 0.0 - 1.0 | How certain is the underlying knowledge? |
| `rule` | string | `"causal"`, `"logical"`, `"empirical"`, `"definitional"` | What type of relation? |
| `necessity` | string | `"Possible"`, `"Contingent"`, `"Necessary"` | Modal necessity |

#### Provenance (required for verifiable knowledge)

| Field | Type | Purpose |
|-------|------|---------|
| `source` | string | Reference URI (DOI, URL, legal code) |
| `author` | string | Creator of the knowledge |
| `timestamp` | string | When the knowledge was created (ISO 8601) |
| `version` | string | Version identifier |

#### Temporal

| Field | Type | Purpose |
|-------|------|---------|
| `time` | string | When: `"Past"`, `"Present"`, `"Future"`, or ISO 8601 date |
| `duration` | string | How long (ISO 8601 duration) |
| `frequency` | string | How often: `"Once"`, `"Daily"`, `"Recurring"` |

#### Causal

| Field | Type | Purpose |
|-------|------|---------|
| `strength` | float | Causal strength (0.0 - 1.0) |
| `cause` | string | Cause description |
| `effect` | string | Effect description |
| `conditionality` | string | `"Sufficient"`, `"Necessary"`, `"Both"` |

#### Spatial

| Field | Type | Purpose |
|-------|------|---------|
| `location` | string | Geographic identifier |
| `domain` | string | Knowledge domain |
| `scope` | string | `"Global"`, `"Local"`, `"Regional"` |

#### Affective, Value, Cognitive, Mood

Additional categories for emotion (`emotion`, `intensity`, `valence`), value judgments (`value`, `alignment`, `priority`), cognitive framing (`intent`, `focus`, `perspective`), and mood (`mood`, `modality`).

See the [Modifier Reference](../reference/modifiers.md) for the complete list.

### Custom Modifiers

Any key not in the standard set is stored as a custom modifier:

```stl
[Drug_X] -> [Effect_Y] ::mod(
  confidence=0.85,
  dosage="500mg",
  trial_id="NCT12345678"
)
```

Here `dosage` and `trial_id` are custom fields — the parser preserves them as extra attributes accessible via `getattr(stmt.modifiers, "dosage")`.

## Confidence Calibration

Confidence scores should reflect genuine uncertainty, not default to 1.0:

| Score | When to Use |
|-------|-------------|
| **0.95 - 1.0** | Definitional truths, mathematical facts |
| **0.85 - 0.94** | Well-established facts, strong evidence |
| **0.70 - 0.84** | Generally accepted, moderate evidence |
| **0.50 - 0.69** | Probable but uncertain, limited evidence |
| **0.30 - 0.49** | Speculative, weak evidence |
| **0.00 - 0.29** | Highly uncertain, hypothetical |

Example:

```stl
# Definitional truth — very high confidence
[Water] -> [H2O] ::mod(rule="definitional", confidence=0.99)

# Strong empirical evidence
[Smoking] -> [Lung_Cancer] ::mod(rule="causal", confidence=0.92, strength=0.85)

# Speculative hypothesis
[Consciousness] -> [Quantum_Microtubules] ::mod(rule="causal", confidence=0.35)
```

## How STL Differs from Other Formats

### vs. JSON

JSON stores data. STL stores **knowledge with provenance**.

```json
{"source": "Einstein", "target": "Relativity", "confidence": 0.98}
```

```stl
[Einstein] -> [Theory_Relativity] ::mod(confidence=0.98, source="doi:10.1002/andp.19053221004")
```

STL adds: directionality, typed relations, built-in provenance, confidence semantics, graph structure.

### vs. RDF/Turtle

RDF represents triples (subject-predicate-object). STL represents **tension paths with rich metadata**.

```turtle
:Einstein :developed :TheoryRelativity .
```

```stl
[Einstein] -> [Theory_Relativity] ::mod(
  rule="empirical", confidence=0.98,
  source="doi:10.1002/andp.19053221004", time="1905-09-26"
)
```

STL adds: human readability, first-class confidence, temporal context, LLM compatibility.

### vs. OWL/Description Logic

OWL focuses on ontology (class hierarchies, logical axioms). STL focuses on **knowledge statements with provenance and uncertainty**. They are complementary — STL can feed into OWL ontologies via RDF serialization.

## The Python Data Model

The parser maps STL syntax to Pydantic models:

| STL Syntax | Python Model | Access Pattern |
|------------|-------------|----------------|
| `[Name]` | `Anchor` | `anchor.name`, `anchor.namespace` |
| `::mod(...)` | `Modifier` | `modifier.confidence`, `modifier.rule` |
| `[A] -> [B] ::mod(...)` | `Statement` | `stmt.source`, `stmt.target`, `stmt.modifiers` |
| Full document | `ParseResult` | `result.statements`, `result.is_valid`, `result.errors` |

```python
from stl_parser import parse

result = parse('[A] -> [B] ::mod(confidence=0.9, rule="causal")')

# ParseResult
result.is_valid       # True
result.statements     # [Statement(...)]
result.errors         # []
result.warnings       # []

# Statement
stmt = result.statements[0]
stmt.source           # Anchor(name="A")
stmt.target           # Anchor(name="B")
stmt.modifiers        # Modifier(confidence=0.9, rule="causal")

# Anchor
stmt.source.name      # "A"
stmt.source.namespace  # None

# Modifier
stmt.modifiers.confidence  # 0.9
stmt.modifiers.rule        # "causal"
stmt.modifiers.custom      # {} (custom dict, used by builder)
```

---

## What's Next?

- **[Tutorials](../tutorials/)** — Step-by-step guides for each capability
- **[API Reference](../reference/)** — Complete function and class documentation
- **[STL Syntax Card](../reference/stl-syntax.md)** — One-page quick reference
