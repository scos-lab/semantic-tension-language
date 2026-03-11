# Anchor Type Reference

Complete reference for the 9 canonical anchor types in STL. Anchors are the nodes of the tension-path model — every STL statement connects a source anchor to a target anchor.

**Import:** `from stl_parser import Anchor, AnchorType`

---

## Anchor Model

```python
class Anchor(BaseModel):
    name: str               # Required: alphanumeric + underscore + Unicode (max 64 chars)
    namespace: Optional[str] # Optional: dot-separated hierarchy (e.g., "Physics.Quantum")
    type: Optional[AnchorType]  # Optional: one of 9 canonical types
```

**String representation:**

```python
Anchor(name="Energy")                              # → [Energy]
Anchor(name="Energy", namespace="Physics")          # → [Physics:Energy]
```

**Reserved names** (rejected by validator): `NULL`, `UNDEFINED`, `ANY`, `NONE`, `TRUE`, `FALSE`, `SYSTEM`, `GLOBAL`, `LOCAL`.

---

## The 9 Canonical Types

### Semantic Layer (abstract concepts and relations)

#### Concept

Abstract ideas, theories, properties, categories.

```stl
[Freedom] -> [Democracy] ::mod(rule="logical", confidence=0.80)
[Entropy] -> [Disorder] ::mod(rule="definitional", confidence=0.98)
[Energy] -> [Mass] ::mod(rule="logical", confidence=0.99)
```

**When to use:** The entity represents an abstract idea, theory, property, or category that cannot be physically pointed to.

**Naming:** `[ConceptName]` or `[Concept_Descriptive_Name]`

#### Relational

Logical or semantic relations themselves used as anchors.

```stl
[Cause] -> [Effect] ::mod(rule="definitional", confidence=0.99)
[Identity] -> [Equivalence] ::mod(rule="logical", confidence=0.95)
```

**When to use:** The anchor represents a relation type, logical connector, or semantic role — typically used in meta-level reasoning about the structure of knowledge itself.

**Naming:** `[RelationName]`

---

### Entity Layer (concrete objects and events)

#### Event

Actions, processes, temporal events.

```stl
[World_War_II] -> [Cold_War] ::mod(rule="causal", confidence=0.90, time="1945")
[Conference_2025] -> [Publication] ::mod(rule="causal", confidence=0.75)
[Migration] -> [Cultural_Change] ::mod(rule="causal", confidence=0.70)
```

**When to use:** The anchor represents something that happened or happens — an action, process, or occurrence with temporal extent.

**Naming:** `[EventName]` or `[Event_YYYY_Description]`

#### Entity

Physical or perceivable objects.

```stl
[Apple] -> [Fruit] ::mod(rule="definitional", confidence=0.99)
[Galaxy] -> [Stars] ::mod(rule="definitional", confidence=0.95)
[Table] -> [Furniture] ::mod(rule="definitional", confidence=0.99)
```

**When to use:** The anchor represents a concrete, physical, or perceivable object — something that exists in the material world.

**Naming:** `[EntityName]` or `[Entity_Qualifier]`

#### Name

Uniquely identified named entities (proper nouns).

```stl
[Einstein] -> [Theory_Relativity] ::mod(rule="empirical", confidence=0.99, author="Einstein")
[London] -> [United_Kingdom] ::mod(rule="definitional", confidence=0.99)
[Google] -> [Search_Engine] ::mod(rule="definitional", confidence=0.95)
```

**When to use:** The anchor is a proper noun — a specific person, place, organization, or named thing with a unique real-world identity.

**Naming:** `[ProperName]` — preserve original casing. Use `[AlbertEinstein]` or `[Albert_Einstein]`.

---

### Structural Layer (meta-linguistic and reasoning)

#### Agent

Active or cognitive subjects capable of action.

```stl
[Researcher] -> [Experiment] ::mod(intent="Evaluate", confidence=0.85)
[AI_System] -> [Prediction] ::mod(intent="Predict", confidence=0.70)
[Self] -> [Observation] ::mod(perspective="FirstPerson")
```

**When to use:** The anchor represents an entity that can act, decide, or reason — a human, organization, or system with agency.

**Naming:** `[AgentName]` or `[Agent_Role]`

#### Question

Points of inquiry, unresolved tension.

```stl
[Question_Consciousness] -> [Theory_IIT] ::mod(rule="logical", confidence=0.60)
[Hypothesis_DarkEnergy] -> [Observation] ::mod(rule="empirical", confidence=0.50)
[Why_Gravity] -> [Spacetime_Curvature] ::mod(rule="logical", confidence=0.95)
```

**When to use:** The anchor represents an open question, hypothesis, or unresolved inquiry — a point of epistemic tension that drives investigation.

**Naming:** `[Question_Topic]`, `[Hypothesis_Description]`, `[Why_Subject]`

#### Verifier

Evaluation, testing, and validation mechanisms.

```stl
[Test_Reproducibility] -> [Study_X] ::mod(intent="Evaluate", confidence=0.80)
[Criterion_Falsifiability] -> [Theory_Y] ::mod(rule="logical", confidence=0.90)
[Observer] -> [Phenomenon] ::mod(perspective="Objective")
```

**When to use:** The anchor represents a mechanism, criterion, or agent that validates, tests, or evaluates other knowledge.

**Naming:** `[VerifierName]`, `[Test_Description]`, `[Criterion_Name]`

#### PathSegment

Intermediate states, transitions, and process stages.

```stl
[Raw_Data] -> [Cleaned_Data] ::mod(rule="causal", confidence=0.95)
[Hypothesis] -> [Experiment] ::mod(rule="logical", confidence=0.85)
[Draft] -> [Review] -> [Publication] ::mod(rule="causal", confidence=0.80)
```

**When to use:** The anchor represents an intermediate state in a process — a transition point, stage, or bridge between other anchors.

**Naming:** `[SegmentName]`, `[Stage_Description]`, `[Process_Step]`

---

## Type Selection Decision Tree

```
Is this a proper noun (person, place, org)?
├── YES → Name
└── NO
    Can it perform actions / make decisions?
    ├── YES → Agent
    └── NO
        Is it a physical, perceivable object?
        ├── YES → Entity
        └── NO
            Did it happen / does it have temporal extent?
            ├── YES → Event
            └── NO
                Is it an open question or hypothesis?
                ├── YES → Question
                └── NO
                    Does it validate or test something?
                    ├── YES → Verifier
                    └── NO
                        Is it an intermediate process stage?
                        ├── YES → PathSegment
                        └── NO
                            Is it a relation type itself?
                            ├── YES → Relational
                            └── NO → Concept
```

---

## Naming Conventions

| Rule | Example | Notes |
|------|---------|-------|
| PascalCase for multi-word | `[UniversalGravitation]` | Preferred for compound concepts |
| Underscore separation | `[Theory_Relativity]` | Also acceptable |
| Preserve case for names | `[AlbertEinstein]` | Don't lowercase proper nouns |
| Namespace for disambiguation | `[Physics:Energy]` | Required when same name in multiple domains |
| Unicode supported | `[黄帝内经]`, `[素問]` | Chinese, Arabic, Japanese, etc. |
| Date suffix for events | `[Event_2025_Summit]` | Helps distinguish temporal anchors |
| Max 64 characters | — | Enforced by parser |

**Valid characters:** Letters (any script), digits, underscores, hyphens (`-`). No spaces, no special characters except `:` (namespace separator) and `-` (hyphen, not as first character).

---

## Namespaces

Namespaces disambiguate anchors that share the same name across domains.

```stl
[Physics:Energy] -> [Physics:Mass] ::mod(rule="logical", confidence=0.99)
[Psychology:Energy] -> [Psychology:Motivation] ::mod(rule="causal", confidence=0.75)
[Economics:Energy] -> [Economics:Oil_Market] ::mod(rule="empirical", confidence=0.80)
```

**Hierarchical namespaces** use dots:

```python
Anchor(name="Quark", namespace="Physics.Quantum")   # → [Physics.Quantum:Quark]
Anchor(name="TCP", namespace="Network.Transport")    # → [Network.Transport:TCP]
```

---

## Working with Anchor Types in Python

```python
from stl_parser import parse, AnchorType

result = parse('[Einstein] -> [Theory_Relativity] ::mod(confidence=0.99)')
stmt = result.statements[0]

# Access anchor properties
print(stmt.source.name)        # "Einstein"
print(stmt.source.namespace)   # None
print(stmt.source.type)        # None (type is inferred, not always set)

# Create typed anchors directly
from stl_parser import Anchor

a = Anchor(name="Einstein", type=AnchorType.NAME)
print(a.type)  # AnchorType.NAME

# Anchors are hashable (usable in sets/dicts)
anchors = {a}
```

**Note:** The parser does not automatically infer anchor types from names. Types can be set explicitly when constructing anchors programmatically or via schema validation.
