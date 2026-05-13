# STL Operational Protocol v1.2

> **Protocol Type:** Compiler-Facing Protocol for LLMs
> **Purpose:** Standard protocol for LLMs to generate valid STL (Semantic Tension Language) statements
> **Specification Base:** STL Core Specification v1.0 + Supplement
> **Target:** Large Language Models generating structured knowledge representations
>
> **What's new in v1.2:** §5.2 *Confidence Calibration* rewritten as **6 canonical
> discrete levels** (`1.0` / `0.95` / `0.8` / `0.5` / `0.2` / `0.01`) instead of
> continuous bands. `1.0` is now reserved for **analytic truths only**
> (definitions, mathematical theorems, logical tautologies). Strong synthetic
> claims use `0.95`. LLMs SHOULD pick from the canonical set rather than
> inventing intermediate values (e.g., `0.85`, `0.92`).
>
> **What's new in v1.1:** §4.2 *Default Value Omission* — `confidence`, `rule`, and
> `strength` now carry well-defined defaults; omitting them is preferred for new
> authoring (≈17% token savings). Fully backward compatible. See §4.2.

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

### 4.0 Meta Semantic Fields (META_SEMANTIC_FIELDS)

Meta Semantic Fields are a special class of modifiers that define the **semantic nature of the edge itself** — i.e., *what kind of relationship* exists between the source and target nodes. They are distinct from attribute modifiers (confidence, description, timestamp) which describe *properties* of the edge.

Every well-formed STL edge should carry at least one meta semantic field. The `(meta_field, meta_value)` pair is the edge's semantic signature.

| Meta Field | Semantics | Example |
|------------|-----------|---------|
| `relation` | General relationship | `::mod(relation="师傅")`, `::mod(relation="causes")` |
| `status` | State of being | `::mod(status="deceased")`, `::mod(status="active")` |
| `role` | Role in a structure | `::mod(role="leader")`, `::mod(role="member")` |
| `type` | Type classification | `::mod(type="person")`, `::mod(type="location")` |
| `kind` | Kind/variety | `::mod(kind="weapon")`, `::mod(kind="herb")` |
| `is_a` | Taxonomic relationship | `::mod(is_a="martial_art")` |
| `action` | Action/behavior | `::mod(action="purchase")`, `::mod(action="喝酒")` |
| `predicate` | Generic predicate (legacy compat) | `::mod(predicate="teaches")` |
| `phase` | Phase/stage | `::mod(phase="current")`, `::mod(phase="completed")` |

**Supersede detection:** When two edges share the same `(source, meta_field, meta_value)` but have different targets, the newer edge (by `created_at`) is a candidate correction of the older one. Systems may flag the older edge as `suspected_supersede=true` to assist downstream reasoning.

**Constant name in code:** `META_SEMANTIC_FIELDS`

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

| Key | Type | Values | Default | Example |
|-----|------|--------|---------|---------|
| `certainty` | Float | [0.0, 1.0] | absent | `::mod(certainty=0.95)` |
| `confidence` | Float | [0.0, 1.0] | `1.0` (see §4.2) | `::mod(confidence=0.85)` |
| `necessity` | Enum | `"Possible"`, `"Contingent"`, `"Necessary"` | absent | `::mod(necessity="Necessary")` |
| `rule` | Enum | `"causal"`, `"logical"`, `"empirical"`, `"definitional"` | inferred from meta field (see §4.2.2) | `::mod(rule="causal")` |

> **Note on `confidence` — dual-purpose field:** `confidence` is both an **epistemic claim** (how true is this relationship?) and a **propagation weight factor** (how strongly does activation flow through this edge in STG?). The two roles are usually aligned, but be aware: lowering `confidence` reduces both the epistemic strength of the claim *and* the activation flow. For structured ground-truth ingest (e.g., direct quotes from authoritative APIs), `confidence=1.0` is the correct value — it preserves epistemic accuracy *and* hands propagation control to runtime `salience` (Hebbian-learned usage frequency). Under v1.1 defaults, this is the value applied when `confidence` is omitted. See §4.2 and §9.5.

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
> | `recorded_at` | **When this statement was recorded** (record time) | Conceptual (not implemented in code) | "This statement was written on 2026-03-25" |
> | STG `created_at` | **When the edge was ingested into STG** (ingest time) | STG engine (auto) | epoch float, internal |
>
> - `timestamp` is semantic — part of the knowledge itself
> - `recorded_at` is conceptual — it exists to clarify that `created_at` means "ingest time", not "when the knowledge was originally recorded". In practice `recorded_at ≈ created_at` because statements are typically ingested immediately after writing. Not implemented in code; not stored on edges.
> - STG `created_at` is infrastructure — when the edge entered the graph via `add_edge()` or `ingest_stl()`

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

> **Note on `strength`:** `strength` is **descriptive metadata** for causal-graph analysis — it documents the *modeled* causal coupling between source and target. It is **not** a propagation weight. STG's spreading-activation formula uses `confidence × salience` only; `strength` does not influence retrieval dynamics. See §9.5 for full propagation semantics.
>
> **Default (v1.1, see §4.2.1):** absent — `strength` is required only when `rule="causal"`; on non-causal edges it carries no semantic content and SHOULD be omitted. (Earlier drafts of this protocol suggested a `0.5` placeholder; v1.1 treats omission as "no causal-strength claim" instead.)

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

### 4.2 Default Value Omission

To reduce token cost and visual clutter, certain modifiers carry well-defined
default values. When omitted, **parsers MUST apply the defaults below** before
passing the parsed edge to downstream consumers (STG ingest, validators,
RDF/JSON exporters).

**Design rationale.** STL is read and generated by LLMs at scale; modifier
repetition (`confidence=1.0` on every definitional edge, `rule="empirical"` on
every lesson edge) costs both tokens and visual signal-to-noise. Defaults let
authors omit the *expected* value and reserve explicit modifiers for
*deviations* — the same principle behind sensible-default schemas in modern
programming languages.

#### 4.2.1 Default Value Table

| Modifier | Default when omitted | Override |
|----------|----------------------|----------|
| `confidence` | `1.0` (assertive — "I am stating this as fact") | Write explicitly using one of the six canonical levels (§5.2): `0.95` / `0.8` / `0.5` / `0.2` / `0.01` |
| `rule` | Inferred from the meta-semantic field (see §4.2.2) | Write explicitly to override inference |
| `strength` | Absent (omitted from serialized output) | Required only when `rule="causal"`; previously implied `0.5` is now treated as "no claim" |
| `time` / `tense` | Absent | Write only when temporally relevant |

> **Important — `confidence=1.0` is reserved for analytic truths (v1.2).** Omitting
> `confidence` defaults to `1.0`, which means *analytic truth* (definitions,
> mathematical theorems, logical tautologies). Empirical / synthetic claims —
> even very strong ones — should write `confidence=0.95` explicitly to preserve
> the analytic/synthetic distinction. See §5.2 for the canonical level table
> and §5.4 for usage rules.

#### 4.2.2 Rule Inference from Meta-Semantic Field

When `rule` is omitted, parsers MUST infer it from the meta-semantic field
present on the edge:

| Meta field present | Companion fields | Inferred `rule` |
|--------------------|------------------|-----------------|
| `is_a` | — | `definitional` |
| `role` | — | `definitional` |
| `type` / `kind` | — | `definitional` |
| `action` | `cause` / `effect` / `strength` | `causal` |
| `action` | `lesson` | `empirical` |
| `action` | (other) | `empirical` |
| `status` | — | `empirical` |
| `phase` | — | `temporal` |
| `relation` / `predicate` | — | `definitional` |
| (no meta field) | — | `definitional` |

**Explicit override always wins.** If both `rule` and a meta-semantic field
are present on the same edge, the explicit `rule` value is used; inference
applies only when `rule` is absent.

#### 4.2.3 Equivalence Examples

These pairs are semantically equivalent — the right-hand form is preferred for
new authoring:

```
# Definitional (taxonomic)
[Cat] → [Mammal] ::mod(is_a="taxonomy", rule="definitional", confidence=1.0)
[Cat] → [Mammal] ::mod(is_a="taxonomy")                                           # ✓ default-omitted

# Causal
[Heavy_Rain] → [Flooding] ::mod(action="triggers", rule="causal", strength=0.8, confidence=0.85)
[Heavy_Rain] → [Flooding] ::mod(action="triggers", strength=0.8, confidence=0.85) # ✓

# Empirical lesson
[Refresh_Token] → [Auth_Failure] ::mod(action="causes", rule="empirical",
  lesson="Testing-mode OAuth tokens expire in 7 days", occurred_time="2026-04-23",
  confidence=0.95)
[Refresh_Token] → [Auth_Failure] ::mod(action="causes",
  lesson="Testing-mode OAuth tokens expire in 7 days", occurred_time="2026-04-23",
  confidence=0.95)                                                                # ✓
```

#### 4.2.4 Backward Compatibility

The defaults extend, not replace, the existing grammar:

- **Explicit values remain valid.** `::mod(rule="empirical", confidence=1.0, ...)`
  is not deprecated and parses identically to its default-omitted form.
  Existing STG databases require no migration.
- **Parsers MUST apply defaults at the post-parse layer**, so downstream
  consumers receive a uniformly-filled edge regardless of which form the
  author wrote.
- **Canonical-output tools** (formatters, normalizers, round-trip
  serializers) SHOULD prefer the default-omitted form for new edges to
  maximize token efficiency, but MAY emit either form.

#### 4.2.5 Empirical Token Savings

Measured against five representative edge styles (definitional / causal /
empirical / role-spec) tokenized with `cl100k_base`:

| Edge style | Tokens before | Tokens after | Saving |
|------------|--------------:|-------------:|-------:|
| Definitional (`is_a`) | 28 | 16 | −43% |
| Causal | 34 | 29 | −15% |
| Empirical (with `lesson`) | 53 | 48 | −9% |
| Definitional + `description` | 35 | 30 | −14% |
| Role/spec | 38 | 32 | −16% |
| **Average** | — | — | **−17.6%** |

Savings scale with structural density: edges dominated by free-text fields
(long `lesson`, `description`) see smaller relative savings, while short
type/role edges see the largest gains.

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

**LLMs SHOULD pick `confidence` from these six canonical levels rather than
inventing intermediate values.** Reducing the calibration space to six discrete
points eliminates false precision (humans cannot reliably distinguish `0.85`
from `0.92`) and makes generation faster and more consistent.

| Confidence | Canonical Name | Semantics | When to Use |
|-----------:|---------------|-----------|-------------|
| **1.0** *(default — omit)* | **Assertive** | Analytic truth | Definitions, mathematical theorems, logical tautologies, taxonomic membership by definition. **NOT for empirical claims.** |
| **0.95** | **Confident** | Strong empirical + academic humility | Well-established empirical facts, direct quotes from authoritative sources, widely accepted scientific theories. The default level for synthetic claims. |
| **0.8** | **Likely** | Probable, moderate evidence | Generally accepted knowledge, reasonable inferences, claims with supporting evidence but room for revision. |
| **0.5** | **Unknown** | Maximum entropy / 50-50 | Genuine ignorance, evenly balanced competing hypotheses, insufficient information to lean either way. |
| **0.2** | **Doubtful** | Evidence against, leaning false | Weak supporting evidence, contested claims I lean against, hypotheses with significant counter-evidence. |
| **0.01** | **Disbelieved** | Recorded but rejected | Claims I record (e.g., user reports, historical hearsay) but do not believe. Often paired with `certainty` to express the agent's independent judgment (see below). |

#### The Analytic/Synthetic Distinction (Why `1.0` ≠ "very confident")

`1.0` is **not** "very strong belief" — it means **analytic**: true by virtue of
definition, mathematical proof, or logical structure. The claim "no empirical
fact is 100% certain" is correct for synthetic claims but inapplicable to
analytic ones.

| Statement type | Example | Canonical confidence |
|---------------|---------|---------------------|
| Analytic (definition) | `[Cat] → [Mammal] ::mod(is_a="taxonomy")` | `1.0` (omitted) |
| Analytic (math) | `[2_Plus_2] → [4]` | `1.0` (omitted) |
| Analytic (logic) | `[Triangle] → [Has_Three_Sides]` | `1.0` (omitted) |
| Synthetic (strong empirical) | `[Smoking] → [Lung_Cancer]` | `0.95` (explicit) |
| Synthetic (historical fact) | `[Einstein] → [General_Relativity]` | `0.95` (explicit) |
| Synthetic (moderate evidence) | `[Mediterranean_Diet] → [Longevity]` | `0.8` (explicit) |

If you are tempted to write `confidence=1.0` explicitly on an empirical edge:
that is the symptom of mistaking analytic for synthetic. Use `0.95` instead.

#### `certainty` as a Companion Field

When you record a claim you do not believe (low `confidence`), or when source
reliability and content truth diverge, pair `confidence` with `certainty`:

| Scenario | `confidence` | `certainty` |
|----------|-------------:|-------------:|
| User claims meditation cured chronic pain | `0.95` (user clearly said it) | `0.35` (agent doubts the causal claim) |
| Apocryphal historical anecdote | `0.95` (well-documented as *told*) | `0.2` (agent doubts it occurred) |
| Agent's own honest skepticism | `0.2` | — (not needed; `confidence` alone suffices) |

`certainty` is only required when source-reliability and content-truth diverge.
For most edges, omit it.

#### Intermediate Values Are Discouraged But Legal

The protocol does **not** reject `confidence=0.85` or `0.72`. Existing STG
databases contain thousands of such values from earlier protocol versions and
remain fully valid. The recommendation is for **new** authoring: prefer the
canonical set so retrieval, calibration analysis, and cross-agent reasoning
operate on a small uniform value space.

### 5.3 Mandatory Fields by Context

> **v1.1 reminder:** `rule` and `confidence` may be omitted when they match the
> §4.2 defaults (`confidence=1.0`; `rule` inferred from the meta-semantic field).
> The lists below mark fields as *required when stated*, i.e. you must either
> include the explicit value **or** ensure the §4.2 default produces it.

**For Historical Knowledge:**
```
REQUIRED:    time (ISO 8601 or "Past"), source
RECOMMENDED: confidence (if <1.0), author, location, domain
```

**For Scientific Claims:**
```
REQUIRED:    source
EFFECTIVE:   rule="empirical"  (use meta field action= + lesson, or write rule explicitly)
RECOMMENDED: confidence (if <1.0), certainty, timestamp, author
```

**For Definitional Statements:**
```
EFFECTIVE:   rule="definitional"  (use meta field is_a= / role=, or write rule explicitly)
RECOMMENDED: confidence (if <1.0; usually omit since 1.0 is the assertive default),
             domain, source
```

**For Causal Relations:**
```
REQUIRED:    strength
EFFECTIVE:   rule="causal"  (use meta field action= + cause/effect, or write rule explicitly)
RECOMMENDED: confidence (if <1.0), conditionality, time, source
```

### 5.4 Best Practices for LLMs

#### DO:
✅ **Reserve `confidence=1.0` (omission) for analytic truths only** — definitions, mathematical theorems, logical tautologies. For strong empirical claims, write `confidence=0.95` (§5.2)
✅ **Pick `confidence` from the six canonical levels** — `1.0` / `0.95` / `0.8` / `0.5` / `0.2` / `0.01` (§5.2)
✅ **Use `source` for verifiable statements**
✅ **Break complex relations into simple chains**
✅ **Use namespaces for disambiguation** (`[Physics:Energy]` vs `[Psychology:Energy]`)
✅ **Preserve original language** (Chinese, Arabic, etc. are fully supported)
✅ **Use `time` for temporal context**
✅ **Pair `confidence` + `certainty` when source-reliability and content-truth diverge** (§5.2)
✅ **Prefer meta-field-driven `rule` inference** — omit `rule` when the meta field unambiguously implies it (see §4.2.2)

#### DON'T:
❌ **Don't omit confidence for non-analytic claims** — omission means `1.0` (analytic). Empirical claims need explicit `0.95` or lower
❌ **Don't write `confidence=1.0` explicitly on empirical edges** — that's a category error (analytic vs synthetic, §5.2)
❌ **Don't invent intermediate confidence values** — prefer canonical `0.95` / `0.8` / `0.5` / `0.2` / `0.01` over `0.85` / `0.72` / `0.43` / etc.
❌ **Don't write `rule=...` when the meta field already implies it** — let inference fill it in
❌ **Don't include `strength` on non-causal edges** — it has no semantic content there (§4.1.7, §4.2.1)
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

### 9.4 Self-Loop as Node Intrinsic Property Carrier

A **self-loop edge** (`[Node] → [Node]`) marked with `action="intrinsic_properties"` is the canonical way to write **node-identity attributes** in STL — id values, registration codes, dimensional facts, fixed metadata that belong to the node itself rather than to any specific outgoing relationship.

This self-loop is **surface syntax only**. STL-consuming engines materialize the modifiers into node-level attribute storage; **no graph edge is created**.

#### Convention

```
[Elden_Ring] → [Elden_Ring] ::mod(
  action="intrinsic_properties",
  appid="1245620",
  release_year="2022",
  price_usd="59.99",
  confidence=0.99
)
```

The modifier bag (`appid`, `release_year`, `price_usd`, ...) carries the node's intrinsic attributes. Each attribute key is a free-form string; downstream tooling reads them by key.

#### When to use

- A node has **N attributes** that would otherwise be repeated on every outgoing business edge (e.g. each game emits 35+ edges, each carrying `appid="..."` redundantly)
- Attributes are **identity-level** — they describe what the node *is*, not how it relates to anything
- You want a single canonical source for these attributes

#### When NOT to use

- The attribute is a relationship to another node → use a normal edge (`[Game] → [Studio] ::mod(action="developed_by")`)
- The attribute might supersede over time and you need explicit history → use normal edges with `occurred_time` so supersede detection catches updates
- One or two attributes only — boilerplate cost is acceptable on the existing edges

#### Runtime contract

STL-consuming engines (e.g. STG) **MUST**:

1. **Materialize modifiers to node-level attribute storage** — write the user-facing attribute keys into the source node's attribute store (e.g. `nodes.metadata_json` in STG's SQLite schema)
2. **NOT create a graph edge** — the self-loop is not stored in `_edges`, `_edges_lookup`, or the graph topology. Subsequent `get_edges(source=X)` and `_graph.has_edge(X, X)` queries must not return it
3. **Strip carrier-internal modifier keys** before materialization — at minimum `action` and `edge_class` describe the carrier convention itself, not the node identity, and must not pollute attribute storage
4. **Discard edge-only fields** — `confidence`, `strength`, `rule`, `time` are edge fields with no semantic meaning on a non-existent edge; engines may silently drop them. (Authors typically still write `confidence=0.99, rule="definitional"` for STL syntactic completeness; the values are accepted but not retained.)
5. **Render distinctly in node detail views** — UIs should surface attributes as a `Properties:` section in node detail output, separate from outgoing/incoming edge listings

Engines **MAY** retain a defensive filter on legacy or manually-created self-loop intrinsic-property edges (i.e. edges that arrived by paths other than `ingest_stl`), excluding them from propagation and community detection. This is a robustness measure for edges that exist contrary to clause 2.

#### Why this is a self-loop, not direct attribute syntax

STL's surface form is uniformly `[A] → [B] ::mod(...)`. Introducing a separate node-attribute syntax (e.g. `[Node] ::attrs(...)`) would fragment the language. Self-loops with a reserved `action` value let LLMs and humans write attributes using the same single-rule grammar; the engine handles the surface-to-storage translation.

The cost is the materialization step (one branch in `ingest_stl`); the benefit is **zero new STL syntax** and a clean separation between the language layer (everything is an edge) and the storage layer (nodes have attributes, edges have modifiers).

#### Anti-pattern

```
# ❌ Don't put intrinsic properties on a regular outgoing edge
[Elden_Ring] → [Souls_Like] ::mod(action="has_tag", appid="1245620", release_year="2022")
# appid/release_year aren't about the Souls_Like tag — they're about the node itself.
# When you have 35 outgoing edges, you'd repeat appid 35 times.
```

```
# ✅ Use a self-loop instead — engine materializes to node attributes
[Elden_Ring] → [Elden_Ring] ::mod(action="intrinsic_properties", appid="1245620", release_year="2022", confidence=0.99)
[Elden_Ring] → [Souls_Like] ::mod(action="has_tag", confidence=0.95)
```

#### Reference implementation

STG implements this contract as of stg-engine commit `7a94bb4` (2026-05-10). `ingest_stl` detects the self-loop pattern and routes through `_try_materialize_intrinsic_properties`, which calls `add_node(**stripped_modifiers)` and short-circuits the normal `add_edge` path. `nodes.metadata_json` becomes the canonical attribute store, queryable via SQLite `JSON_EXTRACT` and rendered by `stg node <name>` as a `Properties:` section.

### 9.5 Propagation Semantics (Reference: STG)

In STG — the reference STL-consuming graph engine — spreading activation across edges uses this formula:

```
propagation_weight = confidence × salience × virtual_factor
```

where:

- **`confidence`** is the epistemic-confidence modifier on the edge (`[0.0, 1.0]`, set by the author at ingest time)
- **`salience`** is a runtime quantity maintained by Hebbian learning. New edges initialize `salience = confidence`; usage strengthens it, disuse weakens it
- **`virtual_factor`** = `0.5` for auto-generated structural bridges (`edge_class="virtual"`), `1.0` otherwise

#### What this means for STL authors

| Modifier | Role in propagation | Authored? |
|----------|---------------------|-----------|
| `confidence` | **Direct factor** in propagation weight | ✅ Yes — by author at ingest time |
| `salience` | **Direct factor** in propagation weight | ❌ No — maintained by the engine via Hebbian learning |
| `strength` | **Not used** by propagation. Descriptive metadata for causal-graph analysis only (§4.1.7) | ✅ Yes — by author, but with no effect on retrieval dynamics |

#### Common confusion: `strength` is not a propagation weight

It is tempting to read `strength=0.9` on a causal edge as "this edge should propagate strongly." It does not. STG (and conformant engines) ignore `strength` during spreading activation. To make an edge propagate more strongly:

- ✅ **Raise its `confidence`** if epistemically justified
- ✅ **Let real usage drive `salience` upward** via Hebbian learning
- ❌ **Do not** encode propagation intent in `strength` — engines will not honor it

Reserve `strength` for what its name suggests: a *descriptive label of causal coupling* for auditability and downstream reasoning (e.g., causal-graph analysis tools that read STL).

#### Confidence is dual-purpose

Authors should be aware that `confidence` simultaneously acts as:

1. An **epistemic claim** about the truth of the relationship (read by humans, audit tools, validation logic)
2. A **propagation weight factor** affecting activation flow at retrieval time

These two roles are usually aligned (uncertain knowledge should propagate weakly), so the dual purpose is rarely a problem. But for structured ground-truth ingest scenarios — where every edge is a direct quote from an authoritative source — setting `confidence=1.0` is semantically correct *and* hands propagation control entirely to `salience` (i.e., to the engine's learning of which facts matter through use).

#### Other STL-consuming engines

This section describes STG's propagation contract. Other STL consumers may choose different propagation models (some may, for example, fold `strength` into the weight). When implementing a non-STG STL engine, document the propagation semantics explicitly — STL the language does not mandate any particular formula.

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

### Recommended Statement (Factual, v1.1 default-omitted form)
```
[Source] → [Target] ::mod(
  is_a="...",                    # meta field → rule="definitional" inferred
  source="reference",
  time="2025-01-15"
)
# confidence omitted → 1.0 (assertive); rule omitted → "definitional"
```

### Recommended Statement (Uncertain Claim)
```
[Source] → [Target] ::mod(
  action="...",                  # meta field → rule="causal" or "empirical" inferred
  confidence=0.85,               # explicit because not 1.0
  source="reference",
  time="2025-01-15"
)
```

### Complete Statement (All Dimensions, explicit form for clarity)
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

| Category | Must-Have Keys | Optional Keys | v1.1 Defaults |
|----------|----------------|---------------|---------------|
| **Meta Semantic** | one of: `relation`, `status`, `role`, `type`, `kind`, `is_a`, `action`, `predicate`, `phase` | — | — |
| **Temporal** | `time` (when temporally relevant) | `duration`, `frequency`, `tense` | absent |
| **Spatial** | `location` or `domain` | `scope` | absent |
| **Logical** | — | `confidence`, `certainty`, `necessity`, `rule` | `confidence` → `1.0`; `rule` → inferred from meta field (§4.2.2) |
| **Provenance** | `source` (for verifiable claims) | `author`, `timestamp`, `version` | absent |
| **Affective** | `emotion` (when affect is relevant) | `intensity`, `valence` | absent |
| **Value** | `value` (when value-laden) | `alignment`, `priority` | absent |
| **Causal** | `strength` (only when `rule="causal"`) | `cause`, `effect`, `conditionality` | `strength` → absent on non-causal edges |
| **Cognitive** | `intent` (when intent is relevant) | `focus`, `perspective` | absent |
| **Mood** | `mood` (when mood is non-assertion) | `modality` | absent |

---

## Appendix B: Confidence Calibration Examples (v1.2 canonical levels)

Each example shows the **v1.2-compliant STL form**: analytic edges omit
`confidence` (default `1.0`); synthetic edges write the canonical level
explicitly.

| Statement (as authored) | Level | Effective `confidence` | Rationale |
|------------------------|-------|-----------------------:|-----------|
| `[Water] → [H2O] ::mod(is_a="chemical_definition")` | Assertive | `1.0` (default) | Analytic — true by chemical definition |
| `[Triangle] → [Three_Sides] ::mod(is_a="geometric_property")` | Assertive | `1.0` (default) | Analytic — true by geometric definition |
| `[Smoking] → [Lung_Cancer] ::mod(action="causes", confidence=0.95)` | Confident | `0.95` | Strong empirical (synthetic) — explicit `0.95` |
| `[Einstein] → [General_Relativity] ::mod(author="Einstein", confidence=0.95)` | Confident | `0.95` | Well-documented historical fact (synthetic) |
| `[Diet_Mediterranean] → [Longevity] ::mod(action="contributes_to", confidence=0.8)` | Likely | `0.8` | Moderate correlational evidence |
| `[Dark_Matter] → [Modified_Gravity] ::mod(rule="logical", confidence=0.5)` | Unknown | `0.5` | Competing models, no decisive evidence |
| `[Consciousness] → [Quantum_Microtubules] ::mod(action="implements", confidence=0.2)` | Doubtful | `0.2` | Speculative, contested, evidence leans against |
| `[User_Report:Meditation] → [Chronic_Pain_Cure] ::mod(action="causes", confidence=0.95, certainty=0.35)` | Confident + low certainty | `0.95` / `0.35` | User clearly made the claim (high `confidence`) but agent doubts the causation (low `certainty`) |

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

**Version:** 1.2.0
**Date:** 2026-05-13
**Status:** Production
**Specification Compliance:** STL Core v1.0 + Supplement v1.0
**License:** CC BY 4.0

### Changelog

**v1.2.0 (2026-05-13)**
- §5.2 *Confidence Score Calibration* rewritten — replaces 6 continuous bands
  with **6 canonical discrete levels**: `1.0` / `0.95` / `0.8` / `0.5` / `0.2` /
  `0.01`. LLMs SHOULD pick from the canonical set rather than inventing
  intermediate values (e.g., `0.85`, `0.72`).
- Introduced the **analytic/synthetic distinction**: `confidence=1.0` (the
  default when omitted) is now reserved for *analytic truths* (definitions,
  math, logic). Strong empirical/synthetic claims use `confidence=0.95`
  explicitly. This honors the principle "no empirical fact is 100% certain"
  while preserving 100% truth for definitional statements.
- §5.2 gained guidance on **`certainty` as a companion field** — paired with
  `confidence` when source-reliability and content-truth diverge (e.g., a
  reliably-reported user claim that the agent doubts).
- §4.2.1 default-value table updated with an analytic/synthetic callout.
- §5.4 DO/DON'T expanded: prefer canonical levels; don't invent intermediates;
  don't write `confidence=1.0` on empirical edges.
- Appendix B *Confidence Calibration Examples* rewritten using canonical
  levels and the analytic/synthetic frame.
- **Backward compatible.** Existing STG databases with `confidence=0.85` /
  `0.72` / `0.99` etc. remain fully valid; the canonical levels are a SHOULD
  for new authoring, not a MUST for parsing.

**v1.1.0 (2026-05-13)**
- Added §4.2 *Default Value Omission* — `confidence` defaults to `1.0`,
  `rule` is inferred from the meta-semantic field, `strength` is absent on
  non-causal edges. Backward compatible: explicit values continue to parse
  identically.
- §4.1.3 logical-modifier table now lists per-key defaults.
- §4.1.7 `strength` note updated: previously-suggested `0.5` placeholder is
  superseded by "absent" on non-causal edges (no semantic content).
- §5.3 "Mandatory Fields by Context" rewritten — `rule` and `confidence` are
  marked `EFFECTIVE` / `RECOMMENDED` rather than `REQUIRED` when the §4.2
  defaults produce the intended value.
- §5.4 DO/DON'T updated to prefer default-omitted authoring.
- §13 Quick Reference Card now shows v1.1 default-omitted form alongside the
  explicit complete form.
- Appendix A gained a `v1.1 Defaults` column.
- Token-efficiency: ≈17.6% average reduction on representative edge styles
  (cl100k_base; §4.2.5).

**v1.0.0 (2025-01-20)** — Initial production release.
