# Modifier Reference

Complete reference for all 30+ standard modifier fields in STL.

---

## Temporal Modifiers

| Field | Type | Values | Example |
|-------|------|--------|---------|
| `time` | string | `"Past"`, `"Present"`, `"Future"`, or ISO 8601 | `time="2025-01-15"` |
| `duration` | string | ISO 8601 duration | `duration="PT5M"` |
| `frequency` | string | `"Once"`, `"Daily"`, `"Weekly"`, `"Recurring"` | `frequency="Daily"` |
| `tense` | string | `"Past"`, `"Present"`, `"Future"` | `tense="Past"` |

---

## Spatial Modifiers

| Field | Type | Values | Example |
|-------|------|--------|---------|
| `location` | string | Geographic identifier | `location="Melbourne"` |
| `domain` | string | Knowledge domain | `domain="physics"` |
| `scope` | string | `"Global"`, `"Local"`, `"Regional"`, `"Organizational"` | `scope="Global"` |

---

## Logical Modifiers

| Field | Type | Range | Example |
|-------|------|-------|---------|
| `confidence` | float | 0.0 - 1.0 | `confidence=0.85` |
| `certainty` | float | 0.0 - 1.0 | `certainty=0.95` |
| `necessity` | string | `"Possible"`, `"Contingent"`, `"Necessary"`, `"Impossible"` | `necessity="Necessary"` |
| `rule` | string | `"causal"`, `"logical"`, `"empirical"`, `"definitional"`, `"correlative"` | `rule="causal"` |

### Confidence Calibration

| Score | When to Use |
|-------|-------------|
| 0.95 - 1.0 | Definitional truths, mathematical facts |
| 0.85 - 0.94 | Well-established facts, strong evidence |
| 0.70 - 0.84 | Generally accepted, moderate evidence |
| 0.50 - 0.69 | Probable but uncertain, limited evidence |
| 0.30 - 0.49 | Speculative, weak evidence |
| 0.00 - 0.29 | Highly uncertain, hypothetical |

---

## Provenance Modifiers

| Field | Type | Values | Example |
|-------|------|--------|---------|
| `source` | string | URI, DOI, legal code reference | `source="doi:10.1234/study"` |
| `author` | string | Creator name | `author="Einstein"` |
| `timestamp` | string | ISO 8601 datetime | `timestamp="2025-01-15T10:00:00Z"` |
| `version` | string | Version identifier | `version="v1.2.3"` |

---

## Affective Modifiers

| Field | Type | Values | Example |
|-------|------|--------|---------|
| `emotion` | string | `"Joy"`, `"Fear"`, `"Anger"`, `"Empathy"`, `"Neutral"`, `"Hope"`, `"Sadness"` | `emotion="Joy"` |
| `intensity` | float | 0.0 - 1.0 | `intensity=0.8` |
| `valence` | string | `"Positive"`, `"Negative"`, `"Neutral"`, `"Mixed"` | `valence="Positive"` |

---

## Value Modifiers

| Field | Type | Values | Example |
|-------|------|--------|---------|
| `value` | string | `"Good"`, `"Neutral"`, `"Bad"`, `"Evil"`, `"Beneficial"` | `value="Good"` |
| `alignment` | string | `"Positive"`, `"Negative"`, `"Neutral"`, `"Mixed"` | `alignment="Positive"` |
| `priority` | string or int | `"High"`, `"Medium"`, `"Low"` or 1-10 | `priority="High"` |

---

## Causal Modifiers

| Field | Type | Range/Values | Example |
|-------|------|-------------|---------|
| `strength` | float | 0.0 - 1.0 | `strength=0.9` |
| `cause` | string | Description | `cause="Rain"` |
| `effect` | string | Description | `effect="Flooding"` |
| `conditionality` | string | `"Sufficient"`, `"Necessary"`, `"Both"`, `"Neither"` | `conditionality="Sufficient"` |

---

## Cognitive Modifiers

| Field | Type | Values | Example |
|-------|------|--------|---------|
| `intent` | string | `"Explain"`, `"Predict"`, `"Evaluate"`, `"Compare"`, `"Describe"` | `intent="Explain"` |
| `focus` | string | `"Subject"`, `"Predicate"`, `"Relationship"`, `"Context"` | `focus="Relationship"` |
| `perspective` | string | `"FirstPerson"`, `"SecondPerson"`, `"ThirdPerson"`, `"Objective"` | `perspective="Objective"` |

---

## Mood Modifiers

| Field | Type | Values | Example |
|-------|------|--------|---------|
| `mood` | string | `"Assertion"`, `"Question"`, `"Request"`, `"Doubt"`, `"Conditional"`, `"Imperative"` | `mood="Question"` |
| `modality` | string | `"Indicative"`, `"Subjunctive"`, `"Imperative"` | `modality="Subjunctive"` |

---

## Custom Modifiers

Any key not listed above is treated as a custom modifier:

```stl
[Drug_X] -> [Effect_Y] ::mod(
  confidence=0.85,
  dosage="500mg",
  trial_id="NCT12345678"
)
```

Custom modifiers are preserved by the parser and included in all serialization formats.

---

## Mandatory Fields by Context

| Context | Required | Recommended |
|---------|----------|-------------|
| Historical knowledge | `time`, `source`, `confidence` | `author`, `location`, `domain` |
| Scientific claims | `rule="empirical"`, `confidence`, `source` | `certainty`, `timestamp`, `author` |
| Definitional statements | `rule="definitional"`, `confidence=0.95+` | `domain`, `source` |
| Causal relations | `rule="causal"`, `strength`, `confidence` | `conditionality`, `time`, `source` |

---

## Anti-Patterns

- Do not set `confidence=1.0` unless the statement is a definitional truth
- Do not use `time="Past"` together with `tense="Future"` (contradictory)
- Do not use `value="Good"` together with `alignment="Negative"` (contradictory)
- Limit to 5-7 modifiers per statement; split across multiple `::mod()` blocks if needed
