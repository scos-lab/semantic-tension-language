# STL Operational Protocol v1.0

> **Protocol Type:** Compiler-Facing Protocol for LLMs
> **Purpose:** Standard protocol for LLMs to generate valid STL (Semantic Tension Language) statements
> **Specification Base:** STL Core Specification v1.0 + Supplement
> **Target:** Large Language Models generating structured knowledge representations

---

## 0. What is STL

**STL (Semantic Tension Language)** is a calculable, universal standard for structuring knowledge through directional semantic relations.

### Core Principles
- **Human-readable yet machine-executable** - Designed for both human comprehension and computational processing
- **Traceable and verifiable** - Every statement can embed provenance, confidence, and evidence
- **Inference-friendly** - Supports reasoning, verification, and knowledge graph construction
- **Token-efficient** - Compact syntax optimized for LLM context windows

### Design Philosophy
STL introduces a **tension-path model** where knowledge flows directionally from source to target, carrying semantic magnitude and type information.

---

## 1. Fundamental Syntax

### 1.1 Basic Form

```
[Source_Anchor] → [Target_Anchor] ::mod(key=value, key=value, ...)
```

**Components:**
- **Anchor** (Node): `[AnchorName]` - Represents an entity, concept, event, or state
- **Arrow** (Path): `→` or `->` - Directional semantic relation
- **Modifier** (Metadata): `::mod(...)` - Optional provenance, confidence, temporal info, etc.

### 1.2 Syntax Rules

**Anchors:**
```
✓ [Concept_Gravity]           // Valid
✓ [Einstein]                  // Valid
✓ [Event_2025_Conference]     // Valid
✓ [Physics:Energy]            // Valid (namespaced)
✓ [黄帝内经]                   // Valid (Unicode supported)

✗ [Not Valid!]                // Invalid (special character)
✗ [Nested [Anchor]]           // Invalid (nesting)
✗ [ Spaced Name ]             // Invalid (whitespace)
✗ []                          // Invalid (empty)
```

**Arrows:**
- Use `→` (Unicode) or `->` (ASCII)
- Must connect exactly two anchors
- Direction matters: `[A] → [B]` ≠ `[B] → [A]`

**Modifiers:**
- Always prefixed with `::`
- Format: `::mod(key=value, key=value, ...)`
- Values: strings (quoted), numbers, booleans, ISO 8601 dates

---

## 2. Anchor System (9 Canonical Types)

### 2.1 Anchor Type Selection Matrix

**SEMANTIC LAYER** (Abstract concepts and relations)

| Type | When to Use | Examples | Naming Pattern |
|------|-------------|----------|----------------|
| **Concept** | Abstract ideas, theories, properties, categories | `[Freedom]`, `[Energy]`, `[Entropy]` | `[ConceptName]` |
| **Relational** | Logical or semantic relations | `[Cause]`, `[Effect]`, `[Identity]` | `[RelationName]` |

**ENTITY LAYER** (Concrete objects and events)

| Type | When to Use | Examples | Naming Pattern |
|------|-------------|----------|----------------|
| **Event** | Actions, processes, temporal events | `[War]`, `[Conference]`, `[Migration]` | `[EventName]` |
| **Entity** | Physical or perceivable objects | `[Apple]`, `[Table]`, `[Galaxy]` | `[EntityName]` |
| **Name** | Uniquely identified named entities | `[Einstein]`, `[London]`, `[Google]` | `[ProperName]` |

**STRUCTURAL LAYER** (Meta-linguistic and reasoning)

| Type | When to Use | Examples | Naming Pattern |
|------|-------------|----------|----------------|
| **Agent** | Active or cognitive subjects | `[Researcher]`, `[AI_System]`, `[Self]` | `[AgentName]` |
| **Question** | Points of inquiry, unresolved tension | `[Question]`, `[Why]`, `[Hypothesis]` | `[QuestionName]` |
| **Verifier** | Evaluation, testing, validation mechanisms | `[Test]`, `[Criterion]`, `[Observer]` | `[VerifierName]` |
| **PathSegment** | Intermediate states, transitions | `[Process]`, `[Transition]`, `[Bridge]` | `[SegmentName]` |

### 2.2 Anchor Naming Conventions

**General Rules:**
- Use PascalCase for multi-word: `[UniversalGravitation]`
- Use underscore for separation: `[Theory_Relativity]`
- Preserve original case for names: `[AlbertEinstein]`
- Use namespace for disambiguation: `[Physics:Energy]`, `[Psychology:Energy]`

**Domain-Specific:**
- Chinese/Unicode fully supported: `[黄帝内经]`, `[素问]`
- Historical events: `[Event_2025_Summit]`
- Specific entities: `[Table_Living_Room]`
- Dated items: include year/date context when relevant

---

## 3. Path Expression Types

### 3.1 Path Type Selection

| Path Type | Semantic Function | When to Use | Example |
|-----------|-------------------|-------------|---------|
| **Semantic** | Definitional, categorical | Abstract meaning, subsumption, categorization | `[Concept_Mammal] → [Concept_Dog]` |
| **Action** | Agency and intentionality | Agent performing action | `[Researcher] → [Action_Publish]` |
| **Cognitive** | Epistemic relations | Perception, understanding, observation | `[Observer] → [Phenomenon]` |
| **Causal** | Cause-effect mechanisms | Causality, conditionality | `[Rain] → [Wet_Ground]` |
| **Inferential** | Logical reasoning | Inference, deduction, implication | `[Premise] → [Conclusion]` |
| **Reflexive** | Self-reference | Identity, self-awareness | `[Self] → [Self]` |

### 3.2 Path Composition

**Simple Path:**
```
[Theory_Gravity] → [Law_Motion]
```

**Chained Path (Manifestation Chain):**
```
[Theory] → [Experiment] → [Observation] → [Law]
```

**Multiple Paths (Tension Network):**
```
[Question] → [Answer]
[Answer] → [Verifier]
[Verifier] → [Question]
```

---

## 4. Modifier System (Complete Reference)

### 4.1 Standard Modifier Categories

#### 4.1.1 Temporal Modifiers

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `time` | Enum/DateTime | `"Past"`, `"Present"`, `"Future"`, ISO 8601 | `::mod(time="2025-01-15")` |
| `duration` | Duration | ISO 8601 Duration | `::mod(duration="PT5M")` |
| `frequency` | Enum | `"Once"`, `"Daily"`, `"Weekly"`, `"Recurring"` | `::mod(frequency="Daily")` |
| `tense` | Enum | `"Past"`, `"Present"`, `"Future"` | `::mod(tense="Past")` |

#### 4.1.2 Spatial Modifiers

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `location` | String | Geographic identifier | `::mod(location="Melbourne")` |
| `domain` | String | Domain identifier | `::mod(domain="physics")` |
| `scope` | Enum | `"Global"`, `"Local"`, `"Regional"` | `::mod(scope="Global")` |

#### 4.1.3 Logical Modifiers (CRITICAL for LLMs)

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `certainty` | Float | [0.0, 1.0] | `::mod(certainty=0.95)` |
| `confidence` | Float | [0.0, 1.0] | `::mod(confidence=0.85)` |
| `necessity` | Enum | `"Possible"`, `"Contingent"`, `"Necessary"` | `::mod(necessity="Necessary")` |
| `rule` | Enum | `"causal"`, `"logical"`, `"empirical"`, `"definitional"` | `::mod(rule="causal")` |

#### 4.1.4 Provenance Modifiers (REQUIRED for Verifiable Knowledge)

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `source` | URI | Document URI, reference | `::mod(source="doc://law/§3.2")` |
| `author` | String | Author or creator | `::mod(author="Einstein")` |
| `timestamp` | DateTime | ISO 8601, **event time** | `::mod(timestamp="2025-01-15T10:00:00Z")` |
| `recorded_at` | DateTime | ISO 8601, **auto** | `::mod(recorded_at="2026-03-25T12:00:00Z")` |
| `version` | String | Version identifier | `::mod(version="v1.2.3")` |

> **Three temporal layers — do not confuse:**
>
> | Field | Meaning | Set by | Example |
> |-------|---------|--------|---------|
> | `timestamp` | **When the event happened** (event time) | Author (manual) | "Einstein published on 1905-09-26" |
> | `recorded_at` | **When this statement was recorded** (record time) | System (auto) | "This edge was written on 2026-03-25" |
> | STG `created_at` | **When the edge was ingested into STG** (storage time) | STG engine (auto) | epoch float, internal |
>
> - `timestamp` is semantic — part of the knowledge itself
> - `recorded_at` is provenance — when the knowledge was captured
> - STG `created_at` is infrastructure — when the edge entered the graph (may differ from `recorded_at` if imported later)

#### 4.1.5 Affective Modifiers

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `emotion` | Enum | `"Joy"`, `"Fear"`, `"Anger"`, `"Empathy"`, `"Neutral"` | `::mod(emotion="Joy")` |
| `intensity` | Float | [0.0, 1.0] | `::mod(intensity=0.8)` |
| `valence` | Enum | `"Positive"`, `"Negative"`, `"Neutral"` | `::mod(valence="Positive")` |

#### 4.1.6 Value Modifiers

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `value` | Enum/String | `"Good"`, `"Neutral"`, `"Bad"` | `::mod(value="Good")` |
| `alignment` | Enum | `"Positive"`, `"Negative"`, `"Neutral"` | `::mod(alignment="Positive")` |
| `priority` | Enum/Integer | `"High"`, `"Medium"`, `"Low"` or [1-10] | `::mod(priority="High")` |

#### 4.1.7 Causal Modifiers

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `cause` | String | Cause description | `::mod(cause="Rain")` |
| `effect` | String | Effect description | `::mod(effect="Flooding")` |
| `strength` | Float | [0.0, 1.0] | `::mod(strength=0.9)` |
| `conditionality` | Enum | `"Sufficient"`, `"Necessary"`, `"Both"` | `::mod(conditionality="Sufficient")` |

#### 4.1.8 Cognitive Modifiers

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `intent` | Enum/String | `"Explain"`, `"Predict"`, `"Evaluate"` | `::mod(intent="Explain")` |
| `focus` | Enum/String | `"Subject"`, `"Predicate"`, `"Relationship"` | `::mod(focus="Relationship")` |
| `perspective` | Enum | `"FirstPerson"`, `"ThirdPerson"`, `"Objective"` | `::mod(perspective="Objective")` |

#### 4.1.9 Mood Modifiers

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `mood` | Enum | `"Assertion"`, `"Question"`, `"Request"`, `"Doubt"` | `::mod(mood="Question")` |
| `modality` | Enum | `"Indicative"`, `"Subjunctive"`, `"Imperative"` | `::mod(modality="Subjunctive")` |

---

## 5. LLM Generation Guidelines

### 5.1 Decision Tree for Statement Generation

```
START
│
├─ Is this a FACT or INTERPRETATION?
│  ├─ FACT → Use Concept/Entity/Event anchors
│  └─ INTERPRETATION → Use Question/Verifier/Agent anchors
│
├─ What is the SEMANTIC FUNCTION?
│  ├─ Definition → Use Semantic Path + ::mod(rule="definitional")
│  ├─ Causation → Use Causal Path + ::mod(rule="causal", strength=...)
│  ├─ Inference → Use Inferential Path + ::mod(rule="logical", certainty=...)
│  └─ Action → Use Action Path + ::mod(intent=..., perspective=...)
│
├─ Is PROVENANCE available?
│  └─ YES → MUST include ::mod(source="...", author="...", timestamp="...")
│
├─ Is there UNCERTAINTY?
│  └─ YES → MUST include ::mod(confidence=0.0-1.0, certainty=0.0-1.0)
│
└─ Is this TEMPORAL?
   └─ YES → MUST include ::mod(time="..." or ISO date)
```

### 5.2 Confidence Score Calibration

**LLMs MUST use these calibrated confidence scores:**

| Confidence | When to Use |
|------------|-------------|
| **0.95-1.0** | Definitional truths, mathematical facts, direct quotes from source |
| **0.85-0.94** | Well-established facts with strong evidence, widely accepted theories |
| **0.70-0.84** | Generally accepted knowledge, moderate evidence |
| **0.50-0.69** | Probable but uncertain, limited evidence, interpretative |
| **0.30-0.49** | Speculative, weak evidence, contested interpretations |
| **0.0-0.29** | Highly uncertain, hypothetical, contradictory evidence |

### 5.3 Mandatory Fields by Context

**For Historical Knowledge:**
```
REQUIRED: time (ISO 8601 or "Past"), source, confidence
RECOMMENDED: author, location, domain
```

**For Scientific Claims:**
```
REQUIRED: rule="empirical", confidence, source
RECOMMENDED: certainty, timestamp, author
```

**For Definitional Statements:**
```
REQUIRED: rule="definitional", confidence=0.95+
RECOMMENDED: domain, source
```

**For Causal Relations:**
```
REQUIRED: rule="causal", strength, confidence
RECOMMENDED: conditionality, time, source
```

### 5.4 Best Practices for LLMs

#### DO:
✅ **Always include `confidence` for factual claims**
✅ **Use `source` for verifiable statements**
✅ **Break complex relations into simple chains**
✅ **Use namespaces for disambiguation** (`[Physics:Energy]` vs `[Psychology:Energy]`)
✅ **Preserve original language** (Chinese, Arabic, etc. are fully supported)
✅ **Use `time` for temporal context**
✅ **Calibrate confidence accurately** (don't default to 1.0)

#### DON'T:
❌ **Don't omit confidence for uncertain claims**
❌ **Don't chain more than 5 nodes in one statement**
❌ **Don't use special characters in anchor names** (except `_` and `:`)
❌ **Don't conflate concepts with interpretations**
❌ **Don't use vague anchors** (`[Thing]`, `[Stuff]`, `[X]`)
❌ **Don't contradict modifiers** (e.g., `time="Past"` + `tense="Future"`)
❌ **Don't overload modifiers** (max 5-7 per statement)

---

## 6. Validation Checklist

### 6.1 Structural Validation

```
□ Anchors
  ✓ Valid characters only (A-Z, a-z, 0-9, _, :)
  ✓ No nesting: [Valid], not [Nested [Invalid]]
  ✓ No whitespace: [Valid_Name], not [ Invalid Name ]
  ✓ Not empty: [Valid], not []

□ Paths
  ✓ Arrow present: [A] → [B], not [A] [B]
  ✓ Both source and target: [A] → [B], not → [B] or [A] →
  ✓ Direction explicit: [A] → [B] ≠ [B] → [A]

□ Modifiers
  ✓ :: prefix present: ::mod(...), not mod(...)
  ✓ Valid key-value pairs
  ✓ Proper comma separation
  ✓ String values quoted: "value", not value
  ✓ Numeric values in range: confidence=0.95, not confidence=1.5
```

### 6.2 Semantic Validation

```
□ Consistency
  ✓ No contradictory time: not (time="Past" AND tense="Future")
  ✓ No contradictory value: not (value="Good" AND alignment="Negative")
  ✓ Confidence/certainty coherent: not (confidence=1.0 AND certainty=0.0)

□ Completeness
  ✓ Provenance for factual claims: source, author, timestamp
  ✓ Confidence for uncertain claims
  ✓ Time for historical/temporal statements
  ✓ Domain for disambiguation

□ Type Appropriateness
  ✓ Float values are 0.0-1.0: confidence, certainty, strength, intensity
  ✓ DateTime in ISO 8601: "2025-01-15T14:00:00Z"
  ✓ Enums match spec: emotion="Joy" not emotion="happy"
```

---

## 7. Examples (Best Practices)

### 7.1 Historical Knowledge (Chinese Classical Text)

```
[黄帝内经] → [素问] ::mod(
  rule="definitional",
  confidence=0.95,
  domain="traditional_chinese_medicine",
  time="Past"
)

[素问] → [经络理论] ::mod(
  rule="definitional",
  confidence=0.90,
  source="黄帝内经·素问",
  domain="TCM_theory"
)

[黄帝内经] → [西汉] ::mod(
  rule="empirical",
  confidence=0.82,
  time="-0026-01-01T00:00:00Z",
  source="历史文献考证"
)

[素问] → [王冰] ::mod(
  rule="empirical",
  confidence=0.88,
  author="王冰",
  time="0762-01-01T00:00:00Z",
  source="唐·王冰注"
)
```

### 7.2 Scientific Knowledge (Physics)

```
[Theory_Relativity] → [Prediction_TimeDilation] ::mod(
  rule="logical",
  confidence=0.99,
  certainty=0.98,
  author="Einstein",
  source="doi:10.1002/andp.19053221004",
  timestamp="1905-09-26",
  domain="physics"
)

[Prediction_TimeDilation] → [Experiment_GPS] ::mod(
  rule="empirical",
  confidence=0.97,
  strength=0.95,
  source="doi:10.1103/PhysRevLett.45.2081",
  timestamp="1980-12-22"
)

[Experiment_GPS] → [Observation_ClockOffset] ::mod(
  rule="causal",
  confidence=0.98,
  cause="Gravitational_Time_Dilation",
  effect="Clock_Offset_38_Microseconds_Per_Day",
  strength=0.99
)
```

### 7.3 Causal Chain

```
[Heavy_Rain] → [Urban_Flooding] ::mod(
  rule="causal",
  confidence=0.85,
  strength=0.80,
  conditionality="Sufficient",
  location="Urban_Area",
  time="2025-01-15"
)

[Urban_Flooding] → [Road_Closure] ::mod(
  rule="causal",
  confidence=0.90,
  strength=0.85,
  conditionality="Necessary"
)

[Road_Closure] → [Traffic_Disruption] ::mod(
  rule="causal",
  confidence=0.95,
  strength=0.90,
  conditionality="Both"
)
```

### 7.4 Epistemic Cycle (Question-Answer-Verification)

```
[Question_Climate_Change] → [Answer_Anthropogenic_Warming] ::mod(
  rule="empirical",
  confidence=0.95,
  source="IPCC_AR6_2021",
  timestamp="2021-08-09",
  certainty=0.95
)

[Answer_Anthropogenic_Warming] → [Verifier_Temperature_Data] ::mod(
  rule="empirical",
  confidence=0.97,
  source="NOAA_Global_Temperature_Dataset",
  strength=0.95
)

[Verifier_Temperature_Data] → [Question_Climate_Change] ::mod(
  rule="logical",
  confidence=0.90,
  strength=0.85,
  intent="Validate"
)
```

### 7.5 Multi-Dimensional Statement

```
[Agent_Researcher] → [Action_Publish_Paper] ::mod(
  time="2025-01-15T14:30:00Z",
  location="University_Cambridge",
  domain="artificial_intelligence",
  emotion="Satisfaction",
  intensity=0.75,
  value="Beneficial",
  alignment="Positive",
  confidence=0.92,
  source="doi:10.1234/example.2025",
  author="Smith_J",
  perspective="FirstPerson",
  intent="Contribute"
)
```

---

## 8. Anti-Patterns (What NOT to Do)

### 8.1 Vague Anchors
```
❌ BAD:  [Thing] → [Stuff]
✅ GOOD: [Concept_Matter] → [Property_Mass]

❌ BAD:  [X] → [Y]
✅ GOOD: [Theory_X] → [Prediction_Y]
```

### 8.2 Missing Critical Modifiers
```
❌ BAD:  [Study_X] → [Finding_Y]
✅ GOOD: [Study_X] → [Finding_Y] ::mod(
           confidence=0.82,
           source="doi:10.1234/study",
           timestamp="2024-12-01"
         )
```

### 8.3 Over-Chaining
```
❌ BAD:  [A] → [B] → [C] → [D] → [E] → [F] → [G] → [H]
✅ GOOD: [A] → [B] → [C]
         [C] → [D] → [E]
         [E] → [F] → [G]
```

### 8.4 Modifier Overload
```
❌ BAD:  [A] → [B] ::mod(
           time="Past", location="NYC", emotion="Joy",
           value="Good", certainty=0.8, confidence=0.9,
           source="...", author="...", version="...",
           priority=5, intensity=0.7, strength=0.8,
           ... // 15 more modifiers
         )

✅ GOOD: [A] → [B] ::mod(time="Past", location="NYC", source="...")
         [A] → [B] ::mod(emotion="Joy", intensity=0.7)
```

### 8.5 Contradictory Modifiers
```
❌ BAD:  ::mod(time="Past", tense="Future")
❌ BAD:  ::mod(value="Good", alignment="Negative")
❌ BAD:  ::mod(confidence=0.0, certainty=1.0)
```

### 8.6 Wrong Confidence Calibration
```
❌ BAD:  [Hypothesis_X] → [Conclusion_Y] ::mod(confidence=1.0)
✅ GOOD: [Hypothesis_X] → [Conclusion_Y] ::mod(confidence=0.65)

❌ BAD:  [Definition_Mass] → [Concept_Matter] ::mod(confidence=0.5)
✅ GOOD: [Definition_Mass] → [Concept_Matter] ::mod(
           rule="definitional",
           confidence=0.98
         )
```

---

## 9. Advanced Features

### 9.1 Modifier Layering

Multiple `::mod()` blocks for multi-dimensional tension:

```
[Action] → [Result]
  ::mod(time="Present")
  ::mod(confidence=0.85)
  ::mod(source="doc://report.pdf")
```

Evaluation order: Structural → Logical → Affective → Provenance

### 9.2 Namespace Usage

Disambiguate anchors across domains:

```
[Physics:Energy] → [Physics:Mass] ::mod(rule="logical")
[Psychology:Energy] → [Psychology:Motivation] ::mod(rule="causal")
[Economics:Energy] → [Economics:Oil_Market] ::mod(rule="empirical")
```

### 9.3 Tension Networks

Model reflexive reasoning with cycles:

```
[Question_Consciousness] → [Theory_Integrated_Information]
[Theory_Integrated_Information] → [Experiment_Neural_Correlates]
[Experiment_Neural_Correlates] → [Observation_Phi_Value]
[Observation_Phi_Value] → [Question_Consciousness]
```

Properties: Cycle detection, stability analysis, feedback structures

---

## 10. Quality Assurance Protocol

### 10.1 Pre-Generation Checklist

Before generating STL, LLM must verify:

```
□ SOURCE MATERIAL AVAILABLE?
  → YES: Include source, author, timestamp
  → NO: Lower confidence score

□ TEMPORAL CONTEXT KNOWN?
  → YES: Include time (ISO 8601 or enum)
  → NO: Omit or use generic "Past"

□ CERTAINTY LEVEL ASSESSED?
  → HIGH: confidence=0.85-1.0
  → MEDIUM: confidence=0.50-0.84
  → LOW: confidence=0.0-0.49

□ DOMAIN AMBIGUITY?
  → YES: Use namespace ([Domain:Anchor])
  → NO: Simple anchor name

□ CAUSAL RELATION?
  → YES: Include rule="causal", strength, conditionality
  → NO: Use appropriate rule type
```

### 10.2 Post-Generation Validation

After generating STL, LLM must check:

```
□ SYNTAX VALID?
  ✓ All anchors have valid format
  ✓ All arrows present and directional
  ✓ All modifiers have :: prefix

□ SEMANTICS CONSISTENT?
  ✓ No contradictory modifiers
  ✓ Confidence/certainty coherent
  ✓ Time/tense aligned

□ COMPLETENESS?
  ✓ Factual claims have source
  ✓ Uncertain claims have confidence
  ✓ Historical statements have time

□ READABILITY?
  ✓ Anchor names clear and specific
  ✓ Not over-chained (max 5 nodes)
  ✓ Not modifier-overloaded (max 7 keys)
```

---

## 11. Error Handling

### 11.1 Common Errors and Fixes

| Error Code | Error | Fix |
|------------|-------|-----|
| E001 | MalformedAnchor: `[Not Valid!]` | Remove special chars: `[Not_Valid]` |
| E002 | MissingArrow: `[A] [B]` | Add arrow: `[A] → [B]` |
| E003 | InvalidModifier: `mod(key="value")` | Add `::` prefix: `::mod(key="value")` |
| E004 | TypeMismatch: `confidence="high"` | Use float: `confidence=0.9` |
| E101 | UnresolvedReference | Define referenced anchor first |
| E103 | Contradiction: `time="Past"` + `time="Future"` | Remove one modifier |
| E104 | RangeViolation: `confidence=1.5` | Use valid range: `confidence=0.95` |

### 11.2 Warning Conditions

| Warning Code | Condition | Recommendation |
|--------------|-----------|----------------|
| W001 | AmbiguousReference: `[Energy]` | Add namespace: `[Physics:Energy]` |
| W002 | MissingProvenance | Add `source` modifier |
| W003 | LowConfidence: `confidence=0.3` | Verify or rephrase claim |
| W004 | UnusedAnchor | Connect to graph or remove |

---

## 12. Serialization Context

While LLMs generate STL text, the backend compiles to:

- **JSON**: Base structured format
- **JSON-LD**: Linked data with @context
- **RDF/Turtle**: Semantic web format

**LLM Responsibility:** Generate valid STL text
**Backend Responsibility:** Compilation, validation, persistence

---

## 13. Quick Reference Card

### Minimal Valid Statement
```
[Source] → [Target]
```

### Recommended Statement (Factual)
```
[Source] → [Target] ::mod(
  confidence=0.85,
  source="reference",
  time="2025-01-15"
)
```

### Complete Statement (All Dimensions)
```
[Source] → [Target] ::mod(
  rule="causal",
  confidence=0.90,
  strength=0.85,
  time="2025-01-15T14:00:00Z",
  location="Location",
  domain="domain_name",
  source="doi:10.1234/ref",
  author="AuthorName",
  timestamp="2025-01-15T14:00:00Z"
)
```

---

## 14. One-Line Mnemonic

**Generate STL to be: PRECISE · TRACEABLE · CALIBRATED**

- **PRECISE**: Clear anchors, explicit relations, appropriate modifiers
- **TRACEABLE**: Source, author, timestamp for verifiable knowledge
- **CALIBRATED**: Accurate confidence scores reflecting true uncertainty

---

## Appendix A: Modifier Quick Reference

| Category | Must-Have Keys | Optional Keys |
|----------|----------------|---------------|
| **Temporal** | `time` | `duration`, `frequency`, `tense` |
| **Spatial** | `location` or `domain` | `scope` |
| **Logical** | `confidence` | `certainty`, `necessity`, `rule` |
| **Provenance** | `source` | `author`, `timestamp`, `version` |
| **Affective** | `emotion` | `intensity`, `valence` |
| **Value** | `value` | `alignment`, `priority` |
| **Causal** | `strength` | `cause`, `effect`, `conditionality` |
| **Cognitive** | `intent` | `focus`, `perspective` |
| **Mood** | `mood` | `modality` |

---

## Appendix B: Confidence Calibration Examples

| Statement | Confidence | Rationale |
|-----------|------------|-----------|
| `[Water] → [H2O] ::mod(rule="definitional")` | 0.99 | Definitional truth |
| `[Einstein] → [Theory_Relativity] ::mod(author="Einstein")` | 0.98 | Historical fact, well-documented |
| `[Smoking] → [Lung_Cancer] ::mod(rule="causal")` | 0.92 | Strong empirical evidence |
| `[Diet_Mediterranean] → [Longevity] ::mod(rule="causal")` | 0.75 | Moderate evidence, correlational |
| `[Dark_Matter] → [Modified_Gravity] ::mod(rule="logical")` | 0.60 | Theoretical, competing models |
| `[Consciousness] → [Quantum_Microtubules] ::mod(rule="causal")` | 0.35 | Speculative, contested |

---

## Appendix C: Domain-Specific Templates

### Medical/Clinical
```
[Drug_X] → [Effect_Y] ::mod(
  rule="causal",
  confidence=0.XX,
  strength=0.XX,
  source="doi:...",
  timestamp="YYYY-MM-DD",
  domain="medicine"
)
```

### Legal
```
[Law_Article_X] → [Regulation_Y] ::mod(
  rule="definitional",
  confidence=0.95,
  source="legal_code://section",
  time="YYYY-MM-DD",
  domain="law"
)
```

### Historical
```
[Event_X] → [Era_Y] ::mod(
  rule="empirical",
  confidence=0.XX,
  time="YYYY-MM-DD",
  location="Location",
  source="historical_record",
  domain="history"
)
```

### Traditional Chinese Medicine
```
[湿邪] → [苦味药] ::mod(
  rule="causal",
  confidence=0.85,
  source="黄帝内经·素问",
  domain="TCM",
  principle="燥湿除浊"
)
```

---

**Version:** 1.0.0
**Date:** 2025-01-20
**Status:** Production
**Specification Compliance:** STL Core v1.0 + Supplement v1.0
**License:** CC BY 4.0
