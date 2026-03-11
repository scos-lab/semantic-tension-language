# STL Core Specification v1.0 - Supplement

**Document Version:** 1.0.0
**Status:** Draft
**Date:** 2025-01-15
**Authors:** STL Working Group
**Repository:** https://github.com/scos-lab/semantic-tension-language

---

## Table of Contents

1. [Anchor System Specification](#1-anchor-system-specification)
2. [Path Expression Formal Grammar](#2-path-expression-formal-grammar)
3. [Modifier Layer Complete Specification](#3-modifier-layer-complete-specification)
4. [Semantic Tension Definition](#4-semantic-tension-definition)
5. [Validation and Compliance Rules](#5-validation-and-compliance-rules)
6. [Serialization and Interoperability](#6-serialization-and-interoperability)
7. [Error Handling and Disambiguation](#7-error-handling-and-disambiguation)
8. [Best Practices and Style Guide](#8-best-practices-and-style-guide)
9. [Extension Mechanism](#9-extension-mechanism)
10. [Conformance Test Suite](#10-conformance-test-suite)

---

## 1. Anchor System Specification

### 1.1 Core Anchor Types

STL defines **nine canonical anchor types** organized into **three abstraction layers**:

#### 1.1.1 Semantic Layer

Represents abstract concepts, logical relations, or general knowledge units.

| Anchor Type | Description | Examples | Syntax Pattern |
|-------------|-------------|----------|----------------|
| **Concept Anchors** | Abstract ideas, theories, properties, or categories | `[Freedom]`, `[Energy]`, `[Entropy]`, `[Language]` | `[ConceptName]` |
| **Relational Anchors** | Logical or semantic relations between entities | `[Cause]`, `[Effect]`, `[Identity]`, `[Opposition]` | `[RelationName]` |

**Naming Convention:**
- Use PascalCase for multi-word concepts: `[CausalRelation]`
- Prefix with semantic domain for disambiguation: `[Physics_Energy]`

#### 1.1.2 Entity Layer

Refers to concrete objects, persons, events, or named entities.

| Anchor Type | Description | Examples | Syntax Pattern |
|-------------|-------------|----------|----------------|
| **Event Anchors** | Specific actions, processes, or temporal events | `[War]`, `[Conference]`, `[Migration]`, `[Computation]` | `[EventName]` |
| **Entity Anchors** | Concrete physical or perceivable objects | `[Apple]`, `[Table]`, `[Galaxy]`, `[Human]` | `[EntityName]` |
| **Name Anchors** | Uniquely identified named entities | `[Einstein]`, `[London]`, `[Google]`, `[TheBible]` | `[ProperName]` |

**Naming Convention:**
- Event anchors use gerund or noun form: `[Computation]`, `[Migration]`
- Entity anchors use singular form: `[Human]` not `[Humans]`
- Name anchors preserve original capitalization: `[AlbertEinstein]`

#### 1.1.3 Structural Layer

Represents meta-linguistic or reasoning structures.

| Anchor Type | Description | Examples | Syntax Pattern |
|-------------|-------------|----------|----------------|
| **Agent Anchors** | Active or cognitive subjects | `[Self]`, `[Researcher]`, `[AI_System]`, `[Society]` | `[AgentName]` |
| **Question Anchors** | Points of inquiry or unresolved cognitive tension | `[Question]`, `[Unknown]`, `[Why]`, `[Hypothesis]` | `[QuestionName]` |
| **Verifier Anchors** | Mechanisms of evaluation, testing, or validation | `[Verifier]`, `[Test]`, `[Criterion]`, `[Observer]` | `[VerifierName]` |
| **Path Segment Anchors** | Intermediate states or transitional nodes | `[Process]`, `[Transition]`, `[Bridge]`, `[IntermediateState]` | `[SegmentName]` |

**Naming Convention:**
- Agent anchors indicate active subjects: `[Researcher]`, `[AI_Agent]`
- Question anchors may be interrogative: `[Why]`, `[How]`, `[WhatIf]`
- Verifier anchors indicate evaluation: `[Validator]`, `[Observer]`

### 1.2 Derived Anchors

Derived anchors describe **multidimensional semantic features** that provide contextual texture to core anchors.

#### 1.2.1 Derived Anchor Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **Temporal Anchors** | Temporal points, intervals, or patterns | `[Past]`, `[Present]`, `[Future]`, `[Morning]`, `[2025-01-15]` |
| **Spatial Anchors** | Spatial location or positional relations | `[Here]`, `[There]`, `[Australia]`, `[Coordinate_XYZ]` |
| **Affective Anchors** | Emotional or psychological states | `[Joy]`, `[Fear]`, `[Anger]`, `[Empathy]` |
| **Value Anchors** | Moral, ethical, or systemic value orientations | `[Good]`, `[Evil]`, `[Profit]`, `[Fairness]` |
| **Modal Anchors** | Possibility, necessity, or conditionality | `[Possible]`, `[Necessary]`, `[Hypothetical]`, `[Conditional]` |
| **Quantitative Anchors** | Numerical magnitude or proportion | `[One]`, `[Many]`, `[50%]`, `[Majority]` |
| **Mood Anchors** | Attitude or speech-act mood | `[Assertion]`, `[Question]`, `[Request]`, `[Doubt]` |
| **Perspective Anchors** | Viewpoint or subjective stance | `[FirstPerson]`, `[ThirdPerson]`, `[Objective]`, `[Subjective]` |
| **State Anchors** | Stages or phases within a process | `[Begin]`, `[Transition]`, `[End]`, `[Stable]` |

#### 1.2.2 Usage of Derived Anchors

Derived anchors serve three primary functions:

1. **As Independent Nodes** in semantic graphs:
   ```
   [Morning] → [Activity] ::mod(frequency="Daily")
   ```

2. **As Attribute Sources** in modifiers (values only, not anchors):
   ```
   [Agent] → [Action] ::mod(time="Past", emotion="Joy")
   ```
   Note: The modifier references the *value* `"Past"` from the temporal dimension, not the anchor `[Past]` directly.

3. **As Dimensional Projections** in multi-dimensional graphs:
   ```
   [Event] → [Outcome]
     ::mod(time="Future")
     ::mod(emotion="Hope")
     ::mod(certainty=0.75)
   ```

### 1.3 Anchor Syntax Rules

#### 1.3.1 Formal Syntax (EBNF)

```ebnf
Anchor ::= "[" AnchorName "]"
AnchorName ::= Identifier | NamespacedIdentifier
Identifier ::= Letter (Letter | Digit | "_")*
NamespacedIdentifier ::= Namespace ":" Identifier
Namespace ::= Identifier ("." Identifier)*

Letter ::= [A-Za-z]
Digit ::= [0-9]
```

#### 1.3.2 Validity Rules

1. **Character Set**: Alphanumeric characters (A-Z, a-z, 0-9), underscores (`_`), and hyphens (`-`)
2. **Hyphen Rule**: Hyphens allowed after first character (e.g., `[my-concept]`); safe because anchors are bracket-delimited
3. **No Special Characters**: Prohibited: `!@#$%^&*()+={}[]|;:'",<>?/\`
3. **No Nesting**: Anchors cannot contain other anchors
4. **No Whitespace**: Internal whitespace must use underscores: `[Causal_Relation]`
5. **Case Sensitivity**: `[Cause]` and `[cause]` are different anchors
6. **Length Limit**: Maximum 64 characters (recommended)

#### 1.3.3 Reserved Anchor Names

The following anchor names are reserved for future use:
- `[NULL]`, `[UNDEFINED]`, `[ANY]`, `[NONE]`
- `[TRUE]`, `[FALSE]`
- `[SYSTEM]`, `[GLOBAL]`, `[LOCAL]`

---

## 2. Path Expression Formal Grammar

### 2.1 Path Syntax (EBNF)

```ebnf
PathExpression ::= Anchor Arrow Anchor Modifier?
Arrow ::= "→" | "->"
ChainedPath ::= PathExpression (Arrow Anchor Modifier?)*
Modifier ::= "::" "mod" "(" ModifierList ")"

(* Examples *)
SimpleStatement ::= "[Cause] → [Effect]"
ModifiedStatement ::= "[Cause] → [Effect] ::mod(confidence=0.9)"
ChainStatement ::= "[Concept] → [Event] → [Outcome] → [Value]"
```

### 2.2 Path Types

STL defines **six primary path types** based on semantic function:

| Type | Description | Example | Semantic Function |
|------|-------------|---------|-------------------|
| **Semantic Path** | Abstract or definitional relations | `[Concept_A] → [Concept_B]` | Defines meaning, subsumption, or categorization |
| **Action Path** | Relation between agent and action | `[Agent] → [Action]` | Represents agency and intentionality |
| **Cognitive Path** | Perception or understanding | `[Observer] → [Phenomenon]` | Models epistemic relations |
| **Causal Path** | Cause-effect mechanisms | `[Cause] → [Effect]` | Expresses causality and conditionality |
| **Inferential Path** | Logical or empirical reasoning | `[Premise] → [Conclusion]` | Represents inference and deduction |
| **Reflexive Path** | Self-reference or structural closure | `[Self] → [Self]` | Models identity and reflexivity |

### 2.3 Path Directionality

#### 2.3.1 Directionality Rules

1. **Explicit Direction**: All paths must have explicit directionality
2. **Source and Target**: `[Source] → [Target]`
3. **Asymmetry**: `[A] → [B]` ≠ `[B] → [A]`
4. **Bidirectional Relations** require two statements:
   ```
   [A] → [B] ::mod(relation="mutual")
   [B] → [A] ::mod(relation="mutual")
   ```

#### 2.3.2 Semantic Tension Vector

Every path embodies a **semantic tension vector**:

```
T = (direction, magnitude, type)

where:
  direction: [Source] → [Target]
  magnitude: strength ∈ [0.0, 1.0] (default: 1.0)
  type: {semantic, causal, inferential, cognitive, ...}
```

### 2.4 Path Composition

#### 2.4.1 Manifestation Chains

Multiple paths can compose sequentially to form **manifestation chains**:

```
[Concept] → [Event] → [Outcome] → [Value]
```

**Properties:**
- **Transitivity**: If `A → B` and `B → C`, then the chain `A → B → C` represents the full manifestation
- **Semantic Accumulation**: Each step adds semantic depth
- **Provenance Traceability**: Each segment can have independent modifiers

**Example:**
```
[Theory_Gravity] → [Experiment_FallingApple] ::mod(time="1687", location="England")
[Experiment_FallingApple] → [Observation_Acceleration] ::mod(confidence=0.95)
[Observation_Acceleration] → [Law_UniversalGravitation] ::mod(certainty=0.98)
```

#### 2.4.2 Tension Networks

When multiple paths intersect or form cycles, they create **tension networks**:

```
[Question] → [Answer]
[Answer] → [Verifier]
[Verifier] → [Question]
```

**Properties:**
- **Cycle Detection**: Identify closed loops for epistemic cycles
- **Stability Analysis**: Evaluate convergence or divergence
- **Feedback Structures**: Model reflexive reasoning

### 2.5 Path Validity Rules

1. **Well-Formedness**: Both source and target must be valid anchors
2. **No Dangling Paths**: Every path must connect exactly two anchors
3. **No Self-Loops** (unless explicitly reflexive): `[A] → [A]` requires justification
4. **Type Consistency**: Path type should align with anchor types (e.g., `[Agent] → [Action]` is an Action Path)

---

## 3. Modifier Layer Complete Specification

### 3.1 Formal Syntax (EBNF)

```ebnf
Modifier ::= "::" "mod" "(" ModifierList ")"
ModifierList ::= ModifierPair ("," ModifierPair)*
ModifierPair ::= Key "=" Value

Key ::= Identifier
Value ::= StringValue | NumericValue | BooleanValue | DateTimeValue | ReferenceValue | FunctionValue

StringValue ::= '"' [^"]* '"'
NumericValue ::= Integer | Float | Percentage
Integer ::= Digit+
Float ::= Digit+ "." Digit+
Percentage ::= Float "%"
BooleanValue ::= "true" | "false"
DateTimeValue ::= ISO8601DateTime
ReferenceValue ::= AnchorName  (* Reference to derived anchor value *)
FunctionValue ::= Identifier "(" ArgumentList ")"

ISO8601DateTime ::= YYYY "-" MM "-" DD ["T" HH ":" MM ":" SS ["Z" | Timezone]]
```

### 3.2 Standard Modifier Categories

#### 3.2.1 Temporal Modifiers

Express time-related attributes.

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `time` | Enum / DateTime | `"Past"`, `"Present"`, `"Future"`, ISO 8601 | `::mod(time="2025-01-15")` |
| `duration` | Duration | ISO 8601 Duration | `::mod(duration="PT5M")` |
| `frequency` | Enum | `"Once"`, `"Daily"`, `"Weekly"`, `"Recurring"` | `::mod(frequency="Daily")` |
| `tense` | Enum | `"Past"`, `"Present"`, `"Future"`, `"PastPerfect"` | `::mod(tense="Past")` |

**Example:**
```
[Event_Meeting] → [Outcome_Decision] ::mod(time="2025-01-15T14:30:00Z", duration="PT2H")
```

#### 3.2.2 Spatial Modifiers

Indicate location or domain.

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `location` | String | Geographic identifier, coordinates | `::mod(location="Melbourne")` |
| `domain` | String | Domain identifier | `::mod(domain="physics")` |
| `scope` | Enum | `"Global"`, `"Local"`, `"Regional"`, `"Organizational"` | `::mod(scope="Global")` |

**Example:**
```
[Research] → [Publication] ::mod(location="University_Cambridge", scope="Global")
```

#### 3.2.3 Affective Modifiers

Represent emotional or psychological states.

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `emotion` | Enum | `"Joy"`, `"Fear"`, `"Anger"`, `"Empathy"`, `"Neutral"`, `"Hope"`, `"Sadness"` | `::mod(emotion="Joy")` |
| `intensity` | Enum / Float | `"Low"`, `"Medium"`, `"High"` or [0.0, 1.0] | `::mod(intensity=0.8)` |
| `valence` | Enum | `"Positive"`, `"Negative"`, `"Neutral"`, `"Mixed"` | `::mod(valence="Positive")` |

**Example:**
```
[Agent] → [Action_Help] ::mod(emotion="Empathy", intensity="High", valence="Positive")
```

#### 3.2.4 Logical Modifiers

Encode certainty, necessity, and rules.

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `certainty` | Float | [0.0, 1.0] | `::mod(certainty=0.95)` |
| `confidence` | Float | [0.0, 1.0] | `::mod(confidence=0.85)` |
| `necessity` | Enum | `"Possible"`, `"Contingent"`, `"Necessary"`, `"Impossible"` | `::mod(necessity="Necessary")` |
| `rule` | Enum | `"causal"`, `"correlative"`, `"logical"`, `"definitional"`, `"empirical"` | `::mod(rule="causal")` |

**Example:**
```
[Hypothesis] → [Conclusion] ::mod(certainty=0.75, rule="empirical")
```

#### 3.2.5 Mood Modifiers

Mark grammatical or attitudinal mood.

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `mood` | Enum | `"Assertion"`, `"Question"`, `"Request"`, `"Doubt"`, `"Conditional"`, `"Imperative"` | `::mod(mood="Question")` |
| `modality` | Enum | `"Indicative"`, `"Subjunctive"`, `"Imperative"` | `::mod(modality="Subjunctive")` |

**Example:**
```
[Agent] → [Action] ::mod(mood="Request", modality="Imperative")
```

#### 3.2.6 Value Modifiers

Convey moral, ethical, or evaluative stance.

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `value` | Enum / String | `"Good"`, `"Neutral"`, `"Bad"`, `"Evil"`, `"Beneficial"`, custom | `::mod(value="Good")` |
| `alignment` | Enum | `"Positive"`, `"Negative"`, `"Neutral"`, `"Mixed"` | `::mod(alignment="Positive")` |
| `priority` | Enum / Integer | `"High"`, `"Medium"`, `"Low"` or [1-10] | `::mod(priority="High")` |

**Example:**
```
[Action_Charity] → [Outcome_Help] ::mod(value="Good", alignment="Positive", priority=9)
```

#### 3.2.7 Cognitive Modifiers

Indicate intent or focus.

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `intent` | Enum / String | `"Explain"`, `"Predict"`, `"Evaluate"`, `"Compare"`, `"Describe"` | `::mod(intent="Explain")` |
| `focus` | Enum / String | `"Subject"`, `"Predicate"`, `"Relationship"`, `"Context"` | `::mod(focus="Relationship")` |
| `perspective` | Enum | `"FirstPerson"`, `"SecondPerson"`, `"ThirdPerson"`, `"Objective"` | `::mod(perspective="FirstPerson")` |

**Example:**
```
[Researcher] → [Hypothesis] ::mod(intent="Evaluate", perspective="Objective")
```

#### 3.2.8 Causal Modifiers

Specify causal relations.

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `cause` | String | Anchor name or description | `::mod(cause="Rain")` |
| `effect` | String | Anchor name or description | `::mod(effect="Flooding")` |
| `strength` | Float | [0.0, 1.0] | `::mod(strength=0.9)` |
| `conditionality` | Enum | `"Sufficient"`, `"Necessary"`, `"Both"`, `"Neither"` | `::mod(conditionality="Sufficient")` |

**Example:**
```
[Rain] → [Flooding] ::mod(cause="Heavy_Rainfall", effect="Urban_Flooding", strength=0.85, conditionality="Sufficient")
```

#### 3.2.9 Quantitative Modifiers

Express magnitude or probability.

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `quantity` | Integer / Float | Numeric value | `::mod(quantity=100)` |
| `probability` | Float | [0.0, 1.0] | `::mod(probability=0.7)` |
| `scale` | Enum | `"Small"`, `"Medium"`, `"Large"`, `"Massive"` | `::mod(scale="Large")` |
| `proportion` | Percentage | 0%-100% | `::mod(proportion=75%)` |

**Example:**
```
[Population] → [Growth] ::mod(quantity=1000000, probability=0.85, scale="Large")
```

### 3.3 Provenance Modifiers

Essential for verifiable knowledge.

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `source` | URI | Document URI, reference | `::mod(source="doc://law/§3.2")` |
| `author` | String | Author or creator | `::mod(author="Einstein")` |
| `timestamp` | DateTime | ISO 8601 | `::mod(timestamp="2025-01-15T10:00:00Z")` |
| `version` | String | Version identifier | `::mod(version="v1.2.3")` |

**Example:**
```
[Theory] → [Experiment] ::mod(source="doi:10.1234/example", author="Smith", timestamp="2024-12-01")
```

### 3.4 Modifier Layering

Modifiers can be **hierarchically stacked** to express multi-dimensional tension:

```
[Action] → [Result]
  ::mod(time="Present")
  ::mod(value="Neutral")
  ::mod(confidence=0.85)
  ::mod(source="doc://report.pdf")
```

**Evaluation Order:**
1. Structural modifiers (time, location)
2. Logical modifiers (certainty, necessity)
3. Affective/value modifiers (emotion, value)
4. Provenance modifiers (source, author)

### 3.5 Modifier Validation Rules

1. **Type Consistency**: Values must match declared types
2. **Range Validity**: Numeric values must be within specified ranges
3. **No Contradictions**: Cannot have `time="Past"` AND `time="Future"`
4. **Reference Resolution**: Referenced anchors must exist
5. **Reserved Keys**: Cannot override reserved modifier keys

---

## 4. Semantic Tension Definition

### 4.1 Formal Definition

**Semantic Tension** is the directional manifestation of meaning between two anchors, represented as a vector with three components:

```
T = ⟨direction, magnitude, type⟩

where:
  direction ∈ {[Source] → [Target]}
  magnitude ∈ [0.0, 1.0]  (default: 1.0)
  type ∈ {semantic, causal, inferential, cognitive, action, reflexive}
```

### 4.2 Tension Properties

#### 4.2.1 Directionality

- **Forward Tension**: `[A] → [B]` indicates semantic flow from A to B
- **Asymmetry**: `T(A→B) ≠ T(B→A)` in general
- **Reflexivity**: `T(A→A)` represents self-referential tension

#### 4.2.2 Magnitude

Magnitude represents the **strength or intensity** of the semantic relation:

- **Strong Tension** (0.8-1.0): Definitive, necessary, or highly confident relations
- **Medium Tension** (0.5-0.7): Probable or contextual relations
- **Weak Tension** (0.0-0.4): Speculative or low-confidence relations

**Encoding:**
```
[Cause] → [Effect] ::mod(strength=0.9)  // Strong causal relation
[Hypothesis] → [Prediction] ::mod(confidence=0.6)  // Medium confidence
```

#### 4.2.3 Tension Type Taxonomy

| Type | Description | Example |
|------|-------------|---------|
| **Semantic** | Definitional or categorical | `[Concept_Mammal] → [Concept_Dog]` |
| **Causal** | Cause-effect relationship | `[Rain] → [Wet_Ground]` |
| **Inferential** | Logical deduction | `[Premise] → [Conclusion]` |
| **Cognitive** | Epistemic or perceptual | `[Observer] → [Perception]` |
| **Action** | Agent-action relation | `[Agent] → [Action]` |
| **Reflexive** | Self-reference | `[Self] → [Self]` |

### 4.3 Tension Networks

When multiple paths intersect or form cycles, they constitute a **Tension Network**.

#### 4.3.1 Network Definition

```
TensionNetwork = {P₁, P₂, ..., Pₙ}

where each Pᵢ is a path expression with tension vector Tᵢ
```

#### 4.3.2 Network Properties

1. **Closure**: A network is closed if it forms a complete cycle
2. **Stability**: Network is stable if tensions converge
3. **Coherence**: Network is coherent if no contradictory tensions exist

**Example - Epistemic Cycle:**
```
[Question] → [Answer] ::mod(type="inferential", strength=0.8)
[Answer] → [Verifier] ::mod(type="cognitive", strength=0.9)
[Verifier] → [Question] ::mod(type="reflexive", strength=0.7)

Network Closure: {Q→A, A→V, V→Q}
Network Type: Epistemic feedback loop
```

#### 4.3.3 Cycle Detection

**Algorithm:**
1. Build directed graph from path expressions
2. Apply depth-first search (DFS) for cycle detection
3. Classify cycles as:
   - **Productive**: Epistemic refinement loops
   - **Contradictory**: Logical inconsistencies
   - **Neutral**: Definitional equivalences

### 4.4 Tension Computation

For advanced applications, tension magnitude can be computed from modifier attributes:

```
T_magnitude = f(certainty, confidence, strength)

Example:
T = w₁·certainty + w₂·confidence + w₃·strength

where w₁ + w₂ + w₃ = 1.0 (weighted combination)
```

---

## 5. Validation and Compliance Rules

### 5.1 Structural Validity

#### 5.1.1 Anchor Validity

**Valid Anchors:**
```
✓ [Concept_Gravity]
✓ [Einstein]
✓ [Event_2025_Conference]
✓ [Physics:Energy]
```

**Invalid Anchors:**
```
✗ [Not Valid!]         // Special character
✗ [Nested [Anchor]]    // Nesting
✗ [ SpacedName ]       // Internal whitespace
✗ []                   // Empty
✗ [123StartWithDigit]  // Starts with digit
```

#### 5.1.2 Path Validity

**Valid Paths:**
```
✓ [A] → [B]
✓ [Concept] → [Event] → [Outcome]
✓ [Agent] → [Action] ::mod(time="Past")
```

**Invalid Paths:**
```
✗ [A] [B]              // Missing arrow
✗ [A] → → [B]          // Double arrow
✗ → [B]                // Missing source
✗ [A] →                // Missing target
```

#### 5.1.3 Modifier Validity

**Valid Modifiers:**
```
✓ ::mod(time="Past")
✓ ::mod(confidence=0.95)
✓ ::mod(time="2025-01-15", location="Melbourne")
✓ ::mod(certainty=0.8, source="doc://ref.pdf")
```

**Invalid Modifiers:**
```
✗ ::mod(unknown_key="value")           // Undefined key
✗ ::mod(confidence="not_a_number")     // Type mismatch
✗ ::mod(certainty=1.5)                 // Out of range
✗ ::mod(time="Past", time="Future")    // Contradiction
✗ mod(key="value")                     // Missing ::
```

### 5.2 Semantic Validity

#### 5.2.1 Reference Resolution

All references must resolve to existing anchors:

```
✓ [Agent] → [Action] ::mod(emotion="Joy")  // "Joy" is a value
✗ [Agent] → [Action] ::mod(emotion="[NonExistent]")  // Invalid reference
```

#### 5.2.2 Consistency Checking

**Temporal Consistency:**
```
✗ ::mod(time="Past", tense="Future")  // Contradiction
✓ ::mod(time="Past", tense="Past")    // Consistent
```

**Logical Consistency:**
```
✗ ::mod(certainty=0.0, confidence=1.0)  // Inconsistent
✓ ::mod(certainty=0.9, confidence=0.85) // Consistent
```

**Value Consistency:**
```
✗ ::mod(value="Good", alignment="Negative")  // Inconsistent
✓ ::mod(value="Good", alignment="Positive")  // Consistent
```

### 5.3 Validation Checklist

Compliant STL parsers must validate the following:

```
□ Anchor Format Compliance
  - Valid character set
  - No nesting
  - No reserved names
  - Length within limits

□ Path Directionality
  - Explicit arrow present
  - Valid source and target anchors
  - No dangling paths

□ Modifier Syntax
  - Correct :: prefix
  - Valid key-value pairs
  - Proper comma separation

□ Type Matching
  - String values quoted
  - Numeric values in range
  - DateTime in ISO 8601
  - Boolean values lowercase

□ Semantic Consistency
  - No contradictory modifiers
  - Reference resolution
  - Range validity
  - No circular definitions (unless intentional)

□ Provenance Tracking
  - Source URIs valid
  - Timestamps in ISO 8601
  - Author strings non-empty
```

### 5.4 Validation Modes

STL parsers should support three validation modes:

1. **Strict Mode**: Reject any invalid statement with error
2. **Lenient Mode**: Accept with warnings, apply fallback values
3. **Validation Mode**: Report detailed errors with suggestions, do not execute

---

## 6. Serialization and Interoperability

### 6.1 JSON Serialization

#### 6.1.1 Base JSON Format

```json
{
  "stl_version": "1.0",
  "statement": {
    "anchor_from": {
      "name": "Agent",
      "type": "AgentAnchor",
      "namespace": null
    },
    "anchor_to": {
      "name": "Action",
      "type": "EventAnchor",
      "namespace": null
    },
    "path": {
      "type": "ActionPath",
      "direction": "forward"
    },
    "modifiers": {
      "time": "Past",
      "confidence": 0.92,
      "value": "Good"
    }
  }
}
```

#### 6.1.2 JSON-LD Format

```json
{
  "@context": {
    "@vocab": "https://stl.scos-lab.org/ns/core#",
    "stl": "https://stl.scos-lab.org/ns/core#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "@type": "STLStatement",
  "@id": "urn:uuid:12345678-1234-1234-1234-123456789abc",
  "stl:anchorFrom": {
    "@id": "stl:Concept_Gravity",
    "@type": "stl:ConceptAnchor"
  },
  "stl:anchorTo": {
    "@id": "stl:Phenomenon_Falling",
    "@type": "stl:EntityAnchor"
  },
  "stl:pathType": "SemanticPath",
  "stl:modifiers": {
    "stl:time": "Past",
    "stl:confidence": {
      "@type": "xsd:float",
      "@value": 0.92
    },
    "stl:source": {
      "@id": "doc://law/§3.2"
    }
  }
}
```

### 6.2 RDF Serialization

#### 6.2.1 Turtle Format

```turtle
@prefix stl: <https://stl.scos-lab.org/ns/core#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<urn:uuid:example-statement-001>
  a stl:STLStatement ;
  stl:anchorFrom <stl:Concept_Gravity> ;
  stl:anchorTo <stl:Phenomenon_Falling> ;
  stl:pathType stl:SemanticPath ;
  stl:modTime "Past" ;
  stl:modConfidence "0.92"^^xsd:float ;
  stl:modSource <doc://law/§3.2> .

<stl:Concept_Gravity>
  a stl:ConceptAnchor ;
  rdfs:label "Gravity" .

<stl:Phenomenon_Falling>
  a stl:EntityAnchor ;
  rdfs:label "Falling" .
```

#### 6.2.2 RDF Triple Mapping

| STL Component | RDF Mapping |
|---------------|-------------|
| Anchor | RDF Resource (URI) |
| Path | RDF Property |
| Modifier | Datatype Property or Object Property |
| Statement | Named Graph or Reification |

### 6.3 Attribute Standardization Table

| Attribute | STL Key | Canonical Format | JSON Type | RDF Datatype | Example |
|-----------|---------|------------------|-----------|--------------|---------|
| Time | `time` | ISO 8601 / Enum | string | xsd:dateTime / xsd:string | `"2025-01-15"` |
| Confidence | `confidence` | Float [0,1] | number | xsd:float | `0.92` |
| Location | `location` | String / GeoJSON | string | xsd:string | `"Melbourne"` |
| Emotion | `emotion` | Enum | string | stl:EmotionType | `"Empathy"` |
| Source | `source` | URI | string | xsd:anyURI | `"doc://law/§3.2"` |
| Certainty | `certainty` | Float [0,1] | number | xsd:float | `0.85` |
| Value | `value` | Enum / String | string | stl:ValueType | `"Good"` |

### 6.4 Round-Trip Conversion

Compliant implementations must ensure **round-trip fidelity**:

```
STL → JSON → STL (identical)
STL → RDF → STL (semantically equivalent)
```

**Test Cases:**
```
Original: [Agent] → [Action] ::mod(time="Past", confidence=0.9)

JSON Serialization → Deserialization:
Result: [Agent] → [Action] ::mod(time="Past", confidence=0.9) ✓

RDF Serialization → Deserialization:
Result: [Agent] → [Action] ::mod(time="Past", confidence=0.9) ✓
```

---

## 7. Error Handling and Disambiguation

### 7.1 Error Categories

#### 7.1.1 Syntax Errors

| Error Code | Type | Description | Example |
|------------|------|-------------|---------|
| `E001` | MalformedAnchor | Invalid anchor format | `[Not Valid!]` |
| `E002` | MissingArrow | Path missing arrow | `[A] [B]` |
| `E003` | InvalidModifier | Malformed modifier syntax | `mod(key="value")` |
| `E004` | TypeMismatch | Value type doesn't match key | `::mod(confidence="high")` |

**Error Message Format:**
```
Error E001: MalformedAnchor
  Location: Line 5, Column 12
  Found: [Not Valid!]
  Expected: [ValidName] (alphanumeric + underscore only)
  Suggestion: Use [Not_Valid] or [NotValid]
```

#### 7.1.2 Semantic Errors

| Error Code | Type | Description | Example |
|------------|------|-------------|---------|
| `E101` | UnresolvedReference | Referenced anchor doesn't exist | `::mod(emotion="[Missing]")` |
| `E102` | CircularDefinition | Problematic circular dependency | `[A]→[B]→[A]` without context |
| `E103` | Contradiction | Conflicting modifiers | `time="Past"` AND `time="Future"` |
| `E104` | RangeViolation | Value outside valid range | `confidence=1.5` |

#### 7.1.3 Warning Categories

| Warning Code | Type | Description | Recommendation |
|--------------|------|-------------|----------------|
| `W001` | AmbiguousReference | Multiple possible interpretations | Add namespace |
| `W002` | MissingProvenance | No source/author specified | Add `source` modifier |
| `W003` | LowConfidence | Confidence < 0.5 | Consider validation |
| `W004` | UnusedAnchor | Anchor defined but never used | Remove or connect |

### 7.2 Disambiguation Strategies

#### 7.2.1 Namespace Resolution

When anchor names conflict:

```
Ambiguous: [Energy]

Disambiguated:
  [Physics:Energy]
  [Psychology:Energy]
  [Economics:Energy]
```

#### 7.2.2 Context-Based Resolution

Use modifiers to clarify:

```
Ambiguous: [Paris]

Disambiguated:
  [Paris] ::mod(domain="geography", location="France")
  [Paris] ::mod(domain="mythology", context="Greek")
```

#### 7.2.3 Type-Based Resolution

Use anchor type declarations:

```
JSON:
{
  "anchor_from": {
    "name": "Energy",
    "type": "ConceptAnchor",
    "namespace": "physics"
  }
}
```

### 7.3 Error Recovery Modes

1. **Fail-Fast**: Stop parsing on first error
2. **Error Collection**: Collect all errors, report at end
3. **Best-Effort**: Skip invalid statements, continue parsing
4. **Interactive**: Prompt user for disambiguation

---

## 8. Best Practices and Style Guide

### 8.1 Naming Conventions

#### 8.1.1 Anchor Naming

**Concepts:**
- Use PascalCase: `[ConceptName]`
- Be specific: `[Gravity]` not `[Thing]`
- Multi-word: `[UniversalGravitation]`

**Events:**
- Use noun or gerund form: `[Conference]`, `[Computing]`
- Include temporal markers when relevant: `[Event_2025_Summit]`

**Entities:**
- Singular form: `[Human]` not `[Humans]`
- Specific identifiers: `[Table_Living_Room]`

**Names:**
- Preserve original: `[AlbertEinstein]`, `[NewYork]`
- No spaces: `[New_York]` or `[NewYork]`

**Agents:**
- Active form: `[Researcher]`, `[AI_Agent]`
- Role-based: `[Observer]`, `[Evaluator]`

#### 8.1.2 Modifier Keys

- Use `snake_case`: `certainty`, `is_verified`, `time_created`
- Be descriptive: `confidence_level` over `conf`
- Avoid abbreviations unless standard: `URI` is acceptable

### 8.2 Statement Composition

#### 8.2.1 One Statement, One Claim

**Good:**
```
[Theory_Relativity] → [Prediction_TimeDilation] ::mod(confidence=0.99)
[Prediction_TimeDilation] → [Experiment_GPS] ::mod(verified="true")
```

**Avoid:**
```
[Theory_Relativity] → [Experiment_GPS] ::mod(confidence=0.99, verified="true")
// Skips intermediate step
```

#### 8.2.2 Explicit Over Implicit

**Good:**
```
[Cause_Rain] → [Effect_Flooding] ::mod(
  rule="causal",
  strength=0.85,
  conditionality="Sufficient",
  location="Urban_Area"
)
```

**Avoid:**
```
[Rain] → [Flooding]  // Too implicit, missing context
```

#### 8.2.3 Provenance for Verifiability

Always include provenance for factual claims:

```
[Study_X] → [Finding_Y] ::mod(
  source="doi:10.1234/example",
  author="Smith et al.",
  timestamp="2024-12-01",
  confidence=0.92
)
```

### 8.3 Documentation Standards

#### 8.3.1 Inline Comments

While STL itself doesn't support comments, documentation should accompany statements:

```markdown
## Statement Set: Newtonian Mechanics

### Statement 1: Gravity Definition
[Concept_Gravity] → [Force_Attraction] ::mod(domain="physics", rule="definitional")

**Purpose:** Establish fundamental definition
**Source:** Newton's Principia Mathematica
**Confidence:** 1.0 (definitional)
```

#### 8.3.2 Statement Grouping

Organize related statements:

```
# Physics Domain - Gravitational Relations

[Concept_Gravity] → [Force_Attraction]
[Force_Attraction] → [Phenomenon_Orbit]
[Phenomenon_Orbit] → [Entity_Planet]
```

### 8.4 Anti-Patterns

#### 8.4.1 Over-Chaining

**Avoid:**
```
[A] → [B] → [C] → [D] → [E] → [F] → [G]
// Too long, loses semantic clarity
```

**Prefer:**
```
[A] → [B] → [C]
[C] → [D] → [E]
[E] → [F] → [G]
// Break into manageable chains
```

#### 8.4.2 Modifier Overload

**Avoid:**
```
[A] → [B] ::mod(
  time="Past",
  location="NYC",
  emotion="Joy",
  value="Good",
  certainty=0.8,
  confidence=0.9,
  source="...",
  author="...",
  version="...",
  priority=5,
  // ... 20 more modifiers
)
// Too many dimensions at once
```

**Prefer:**
```
[A] → [B] ::mod(time="Past", location="NYC", source="...")
[A] → [B] ::mod(emotion="Joy", value="Good")
// Split into focused statements
```

#### 8.4.3 Ambiguous Anchors

**Avoid:**
```
[Thing] → [Stuff]  // Too vague
[X] → [Y]  // Meaningless
```

**Prefer:**
```
[Concept_Matter] → [Property_Mass]
[Theory_X] → [Prediction_Y]
```

---

## 9. Extension Mechanism

### 9.1 Version Management

#### 9.1.1 Version Format

```
STL_VERSION = MAJOR.MINOR.PATCH

MAJOR: Breaking changes to syntax or semantics
MINOR: Backward-compatible additions
PATCH: Bug fixes and clarifications
```

#### 9.1.2 Version Declaration

In serialized formats:

```json
{
  "stl_version": "1.0.0",
  "statement": { ... }
}
```

#### 9.1.3 Version Compatibility

| Version | Compatible With | Breaking Changes |
|---------|-----------------|------------------|
| 1.0.0 | - | Initial release |
| 1.1.0 | 1.0.x | No (additive only) |
| 1.2.0 | 1.0.x, 1.1.x | No (additive only) |
| 2.0.0 | - | Yes (new anchor types, syntax changes) |

### 9.2 Custom Anchor Types

#### 9.2.1 Registration Process

1. **Namespace Declaration:**
   ```
   https://example.org/stl/types/
   ```

2. **Type Definition:**
   ```json
   {
     "namespace": "example.org",
     "type_name": "BiologicalPathway",
     "parent_type": "ConceptAnchor",
     "description": "Represents biological pathways",
     "attributes": {
       "pathway_id": "string",
       "organism": "string"
     }
   }
   ```

3. **Usage:**
   ```
   [example.org:BiologicalPathway_Glycolysis] → [Outcome_ATP_Production]
   ```

#### 9.2.2 Custom Type Schema

```json
{
  "custom_types": [
    {
      "name": "BiologicalPathway",
      "namespace": "bio.example.org",
      "base_type": "ConceptAnchor",
      "required_modifiers": ["organism", "pathway_id"],
      "optional_modifiers": ["tissue_type", "condition"],
      "validation_rules": {
        "pathway_id": "^PATH:\\d+$"
      }
    }
  ]
}
```

### 9.3 Custom Modifier Keys

#### 9.3.1 Registration Format

```json
{
  "custom_modifiers": [
    {
      "key": "pathway_confidence",
      "namespace": "bio.example.org",
      "type": "float",
      "range": [0.0, 1.0],
      "default": 0.5,
      "description": "Confidence in pathway activation"
    }
  ]
}
```

#### 9.3.2 Usage

```
[Stimulus_Glucose] → [BiologicalPathway_Glycolysis]
  ::mod(pathway_confidence=0.95, organism="Homo_sapiens")
```

### 9.4 Extension Best Practices

1. **Namespace Isolation**: Always use namespaces for custom types
2. **Backward Compatibility**: Extend, don't replace standard types
3. **Documentation**: Provide clear specification for custom extensions
4. **Validation**: Define validation rules for custom attributes
5. **Registration**: Maintain public registry of extensions

---

## 10. Conformance Test Suite

### 10.1 Parsing Tests

#### 10.1.1 Valid Anchor Parsing

```
TEST_ANCHORS_VALID = [
  "[Concept]",
  "[Einstein]",
  "[Event_2025_Conference]",
  "[Namespace:Type_Name]",
  "[Under_Score_Name]",
  "[CamelCaseName]"
]

Expected: All parse successfully
```

#### 10.1.2 Invalid Anchor Parsing

```
TEST_ANCHORS_INVALID = [
  "[Not Valid!]",           // Special character
  "[Nested [Anchor]]",      // Nesting
  "[ Spaced ]",             // Whitespace
  "[]",                     // Empty
  "[123Digit]",             // Starts with digit
  "[Longer_Than_64_Characters_Name_That_Exceeds_Maximum_Length_Limit_Test]"
]

Expected: All raise MalformedAnchor error
```

### 10.2 Path Expression Tests

#### 10.2.1 Valid Path Parsing

```
TEST_PATHS_VALID = [
  "[A] → [B]",
  "[A] -> [B]",
  "[A] → [B] → [C]",
  "[Agent] → [Action] ::mod(time='Past')"
]

Expected: All parse successfully
```

#### 10.2.2 Invalid Path Parsing

```
TEST_PATHS_INVALID = [
  "[A] [B]",              // Missing arrow
  "[A] → → [B]",          // Double arrow
  "→ [B]",                // Missing source
  "[A] →"                 // Missing target
]

Expected: All raise InvalidPath error
```

### 10.3 Modifier Tests

#### 10.3.1 Valid Modifier Parsing

```
TEST_MODIFIERS_VALID = [
  "::mod(time='Past')",
  "::mod(confidence=0.95)",
  "::mod(time='2025-01-15', location='Melbourne')",
  "::mod(certainty=0.8, source='doc://ref.pdf', author='Smith')"
]

Expected: All parse successfully
```

#### 10.3.2 Type Validation

```
TEST_TYPE_VALIDATION = [
  ("::mod(confidence=0.95)", PASS),
  ("::mod(confidence='high')", FAIL, TypeMismatch),
  ("::mod(certainty=1.5)", FAIL, RangeViolation),
  ("::mod(time='2025-01-15')", PASS),
  ("::mod(time='invalid-date')", FAIL, InvalidFormat)
]
```

### 10.4 Semantic Consistency Tests

#### 10.4.1 Contradiction Detection

```
TEST_CONTRADICTIONS = [
  ("::mod(time='Past', time='Future')", CONTRADICTION),
  ("::mod(value='Good', alignment='Negative')", INCONSISTENT),
  ("::mod(certainty=0.0, confidence=1.0)", WARN)
]

Expected: Detect and report contradictions
```

#### 10.4.2 Reference Resolution

```
TEST_REFERENCES = [
  ("[A] → [B]", PASS),
  ("[A] → [Undefined]", FAIL, UnresolvedReference),
  ("[Namespace:Custom] → [B]", PASS_IF_REGISTERED)
]
```

### 10.5 Serialization Tests

#### 10.5.1 Round-Trip JSON

```python
def test_json_roundtrip(statement):
    json_output = serialize_to_json(statement)
    reconstructed = deserialize_from_json(json_output)
    assert statement == reconstructed
```

#### 10.5.2 Round-Trip RDF

```python
def test_rdf_roundtrip(statement):
    rdf_output = serialize_to_rdf(statement)
    reconstructed = deserialize_from_rdf(rdf_output)
    assert semantically_equivalent(statement, reconstructed)
```

### 10.6 Interoperability Tests

#### 10.6.1 Cross-Format Conversion

```
STL → JSON → RDF → JSON → STL

Expected: Semantic equivalence maintained
```

#### 10.6.2 Multi-Parser Consensus

```
Parser_A(statement) == Parser_B(statement) == Parser_C(statement)

Expected: All conformant parsers produce identical AST
```

### 10.7 Performance Benchmarks

#### 10.7.1 Parsing Performance

```
Benchmark: Parse 10,000 statements
  - Simple statements (no modifiers): < 100ms
  - Complex statements (5+ modifiers): < 500ms
  - Chained paths (5+ nodes): < 200ms
```

#### 10.7.2 Validation Performance

```
Benchmark: Validate 10,000 statements
  - Syntax validation: < 200ms
  - Semantic validation: < 1000ms
  - Full validation (syntax + semantic): < 1200ms
```

---

## Appendix A: Complete EBNF Grammar

```ebnf
(* STL v1.0 Complete Grammar *)

STLDocument ::= Statement+

Statement ::= PathExpression | Comment
Comment ::= "#" [^\n]* "\n"

PathExpression ::= Anchor Arrow Anchor Modifier? |
                   ChainedPath

ChainedPath ::= Anchor (Arrow Anchor Modifier?)+

Anchor ::= "[" AnchorName "]"
AnchorName ::= Identifier | NamespacedIdentifier
Identifier ::= Letter (Letter | Digit | "_")*
NamespacedIdentifier ::= Namespace ":" Identifier
Namespace ::= Identifier ("." Identifier)*

Arrow ::= "→" | "->"

Modifier ::= "::" "mod" "(" ModifierList ")"
ModifierList ::= ModifierPair ("," ModifierPair)*
ModifierPair ::= Key "=" Value

Key ::= Identifier
Value ::= StringValue | NumericValue | BooleanValue | DateTimeValue

StringValue ::= '"' [^"]* '"' | "'" [^']* "'"
NumericValue ::= Integer | Float | Percentage
Integer ::= "-"? Digit+
Float ::= "-"? Digit+ "." Digit+
Percentage ::= Float "%"
BooleanValue ::= "true" | "false"
DateTimeValue ::= ISO8601DateTime

Letter ::= [A-Za-z]
Digit ::= [0-9]

ISO8601DateTime ::= Year "-" Month "-" Day ["T" Hour ":" Minute ":" Second ["Z" | Timezone]]
Year ::= Digit{4}
Month ::= "01".."12"
Day ::= "01".."31"
Hour ::= "00".."23"
Minute ::= "00".."59"
Second ::= "00".."59"
Timezone ::= ("+" | "-") Hour ":" Minute
```

---

## Appendix B: Standard Modifier Registry

| Key | Type | Values | Default | Required | Category |
|-----|------|--------|---------|----------|----------|
| `time` | Enum/DateTime | Past, Present, Future, ISO 8601 | Present | No | Temporal |
| `duration` | Duration | ISO 8601 Duration | - | No | Temporal |
| `location` | String | Geographic identifier | - | No | Spatial |
| `domain` | String | Domain identifier | - | No | Spatial |
| `emotion` | Enum | Joy, Fear, Anger, Empathy, ... | Neutral | No | Affective |
| `intensity` | Float | [0.0, 1.0] | 0.5 | No | Affective |
| `value` | Enum | Good, Neutral, Bad | Neutral | No | Value |
| `confidence` | Float | [0.0, 1.0] | 1.0 | No | Logical |
| `certainty` | Float | [0.0, 1.0] | 1.0 | No | Logical |
| `necessity` | Enum | Possible, Contingent, Necessary | Contingent | No | Logical |
| `rule` | Enum | causal, correlative, logical, ... | - | No | Logical |
| `mood` | Enum | Assertion, Question, Request, ... | Assertion | No | Mood |
| `source` | URI | Document reference | - | Recommended | Provenance |
| `author` | String | Author name | - | No | Provenance |
| `timestamp` | DateTime | ISO 8601 | - | No | Provenance |

---

## Appendix C: Example Repository

### Example 1: Simple Semantic Statement
```
[Concept_Gravity] → [Force_Attraction] ::mod(domain="physics", rule="definitional")
```

### Example 2: Causal Chain
```
[Rain] → [Wet_Ground] ::mod(rule="causal", confidence=0.95, location="Urban_Area")
[Wet_Ground] → [Slippery_Surface] ::mod(rule="causal", strength=0.85)
[Slippery_Surface] → [Risk_Falling] ::mod(rule="causal", certainty=0.8)
```

### Example 3: Epistemic Cycle
```
[Question_Climate] → [Answer_Warming] ::mod(confidence=0.9, source="IPCC_2024")
[Answer_Warming] → [Verifier_Data] ::mod(certainty=0.95)
[Verifier_Data] → [Question_Climate] ::mod(type="reflexive", strength=0.7)
```

### Example 4: Traditional Chinese Medicine (TCM)
```
[湿淫] → [苦味] ::mod(role="main", principle="燥湿除浊", domain="TCM")
[湿淫] → [热性] ::mod(role="main", principle="助苦以燥", domain="TCM")
[湿淫] → [酸味] ::mod(role="assist", function="敛护", domain="TCM")
[湿淫] → [淡味] ::mod(role="assist", function="渗泄利湿", domain="TCM")
```

### Example 5: Multi-Dimensional Statement
```
[Agent_Researcher] → [Action_Publish] ::mod(
  time="2025-01-15T14:00:00Z",
  location="University_Cambridge",
  emotion="Satisfaction",
  value="Beneficial",
  confidence=0.92,
  source="doi:10.1234/example",
  author="Smith",
  domain="science"
)
```

---

## Appendix D: Implementation Checklist

### For STL Parser Implementations

```
□ Core Components
  ✓ Anchor parser (all 9 types)
  ✓ Path expression parser
  ✓ Modifier parser
  ✓ EBNF grammar compliance

□ Validation
  ✓ Syntax validation
  ✓ Semantic validation
  ✓ Type checking
  ✓ Range validation
  ✓ Reference resolution

□ Serialization
  ✓ JSON export
  ✓ JSON import
  ✓ JSON-LD export
  ✓ RDF/Turtle export
  ✓ Round-trip fidelity

□ Error Handling
  ✓ Syntax error reporting
  ✓ Semantic error detection
  ✓ Warning generation
  ✓ Error recovery modes

□ Extensions
  ✓ Custom anchor types
  ✓ Custom modifier keys
  ✓ Namespace support
  ✓ Version declaration

□ Testing
  ✓ Unit tests (parsing)
  ✓ Integration tests (serialization)
  ✓ Conformance tests
  ✓ Performance benchmarks
```

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-15 | Initial supplement release |

---

## References

1. Wuko (2025). "Semantic Tension Language (STL) v1.0: A Structural Protocol for Provenanced Knowledge"
2. STL Core Specification v1.0: https://github.com/scos-lab/semantic-tension-language
3. W3C RDF 1.1 Specification: https://www.w3.org/TR/rdf11-concepts/
4. JSON-LD 1.1: https://www.w3.org/TR/json-ld11/
5. ISO 8601 Date and Time Format: https://www.iso.org/iso-8601-date-and-time-format.html

---

**Document Status:** This supplement extends the STL Core Specification v1.0 with comprehensive implementation guidelines, validation rules, and interoperability standards.

**License:** CC BY 4.0
**Contributing:** Please submit issues and proposals to https://github.com/scos-lab/semantic-tension-language
