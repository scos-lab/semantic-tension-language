# STL Confidence Decay STLC Specification

> **Version:** 1.0.0
> **Type:** Base
> **Target:** `stl_parser/decay.py`
> **Author:** Syn-claude
> **Date:** 2026-02-11
> **Status:** Draft

---

## 1. Scope Definition

[Decay_Module] -> [Scope] ::mod(
  intent="Query-time confidence decay based on statement age",
  boundaries="Read-only derived values — never modifies original Statement data",
  confidence=0.95
)

**Included:**
- `effective_confidence(statement, ...)` — compute single statement's decayed confidence
- `decay_report(parse_result, config)` — batch analysis with statistics
- `filter_by_confidence(parse_result, min_confidence, ...)` — filter statements by effective confidence
- `DecayConfig` — configuration model (half_life, threshold, reference_time)
- `DecayedStatement` — per-statement result with original vs effective confidence
- `DecayReport` — batch result with summary statistics

**Excluded:**
- Modification of original Statement/Modifier objects (immutable principle)
- Persistent storage of decay results
- Automatic re-decay scheduling or cron-like behavior
- UI/visualization of decay curves

**Design Principle:**
[Decay_Principle] -> [Immutability] ::mod(
  rule="definitional",
  confidence=1.0,
  intent="Decay computes derived values at query time, original data is never mutated"
)

---

## 2. Architecture Overview

[Decay_Module] -> [Models_Module] ::mod(
  rule="causal",
  intent="Reads Statement.modifiers.confidence and Statement.modifiers.timestamp",
  confidence=0.95
)

[Decay_Module] -> [Errors_Module] ::mod(
  rule="causal",
  intent="Uses STLDecayError for error reporting",
  confidence=0.95
)

[Decay_Module] -> [Stdlib_Datetime] ::mod(
  rule="causal",
  intent="Uses datetime for timestamp parsing and age calculation",
  confidence=0.95
)

```
Dependency chain:
  models.py (read-only access to Statement, Modifier, ParseResult)
  errors.py (STLDecayError, ErrorCode E900-E901)
  datetime (stdlib — no external deps)
```

---

## 3. Data Models

### 3.1 DecayConfig

[DecayConfig] -> [Configuration] ::mod(
  rule="definitional",
  confidence=0.95,
  intent="Parameterize decay behavior"
)

```
DecayConfig:
  half_life_days: float = 30.0
    → Period in days for confidence to halve
    → Must be > 0

  min_threshold: float = 0.01
    → Floor value — below this, effective confidence is clamped to 0.0
    → Range: [0.0, 1.0]

  reference_time: Optional[datetime] = None
    → "Now" for age calculation
    → If None, use datetime.now(timezone.utc)
```

### 3.2 DecayedStatement

[DecayedStatement] -> [Per_Statement_Result] ::mod(
  rule="definitional",
  confidence=0.95,
  intent="Wrap original statement with decay metadata"
)

```
DecayedStatement:
  statement: Statement
    → Original statement (never modified)

  original_confidence: Optional[float]
    → Value from statement.modifiers.confidence (None if no confidence)

  effective_confidence: Optional[float]
    → After decay calculation (None if no confidence on original)

  age_days: Optional[float]
    → Days elapsed since timestamp (None if no timestamp)

  decay_ratio: Optional[float]
    → effective / original (None if original is None or 0)
```

### 3.3 DecayReport

[DecayReport] -> [Batch_Result] ::mod(
  rule="definitional",
  confidence=0.95,
  intent="Aggregate decay analysis for entire document"
)

```
DecayReport:
  decayed_statements: List[DecayedStatement]
  config: DecayConfig
  total_statements: int
  statements_with_timestamp: int
  statements_decayed: int
    → Count where effective < original
  summary: Dict[str, Any]
    → Keys: mean, median, min, max of effective_confidence
    → Only computed over statements that have confidence
```

---

## 4. Function Specifications

### 4.1 effective_confidence

[Entry] -> [effective_confidence] ::mod(
  intent="Core function — compute single statement's decayed confidence",
  confidence=0.95
)

```
ENTRY: effective_confidence(statement, half_life_days=30.0, reference_time=None)

INPUT:
  statement: Statement
  half_life_days: float (default 30.0, must be > 0)
  reference_time: Optional[datetime] (default: utcnow)

VALIDATE:
  IF half_life_days <= 0:
    RAISE STLDecayError(E900, "half_life_days must be positive")

BRANCH:
  IF statement.modifiers is None OR statement.modifiers.confidence is None:
    EXIT → return None

  confidence = statement.modifiers.confidence

  IF statement.modifiers.timestamp is None:
    EXIT → return confidence (no decay — no timestamp to measure age)

TRANSFORM:
  1. Parse timestamp string → datetime object
     ON ERROR: RAISE STLDecayError(E901, "Invalid timestamp format: {timestamp}")

  2. Calculate age_days = (reference_time - parsed_timestamp).total_seconds() / 86400

  3. IF age_days <= 0 (future timestamp):
     EXIT → return confidence (no decay for future statements)

  4. Apply exponential decay:
     effective = confidence * (0.5 ** (age_days / half_life_days))

  5. Clamp: effective = max(0.0, min(1.0, effective))

EXIT → return effective (float)
```

### 4.2 decay_report

[Entry] -> [decay_report] ::mod(
  intent="Batch analysis — compute decay for all statements in a ParseResult",
  confidence=0.95
)

```
ENTRY: decay_report(parse_result, config=None)

INPUT:
  parse_result: ParseResult
  config: Optional[DecayConfig] (default: DecayConfig())

TRANSFORM:
  1. IF config is None: config = DecayConfig()
  2. reference_time = config.reference_time or datetime.now(timezone.utc)

  3. FOR each statement in parse_result.statements:
     a. Compute effective = effective_confidence(statement, config.half_life_days, reference_time)
     b. Compute age_days from timestamp (if present)
     c. Compute original_confidence from modifiers
     d. Compute decay_ratio = effective / original (if both present and original > 0)
     e. IF effective is not None AND effective < config.min_threshold:
        effective = 0.0
     f. Build DecayedStatement(...)

  4. Compute summary statistics over statements that have effective_confidence:
     mean, median, min, max

  5. Count: total, with_timestamp, decayed (where effective < original)

EXIT → return DecayReport(...)
```

### 4.3 filter_by_confidence

[Entry] -> [filter_by_confidence] ::mod(
  intent="Filter — return only statements whose effective confidence meets threshold",
  confidence=0.95
)

```
ENTRY: filter_by_confidence(parse_result, min_confidence=0.5, half_life_days=30.0, reference_time=None)

INPUT:
  parse_result: ParseResult
  min_confidence: float (threshold, range [0.0, 1.0])
  half_life_days: float (default 30.0)
  reference_time: Optional[datetime]

TRANSFORM:
  1. reference_time = reference_time or datetime.now(timezone.utc)
  2. kept_statements = []
  3. FOR each statement in parse_result.statements:
     a. effective = effective_confidence(statement, half_life_days, reference_time)
     b. IF effective is None:
        → Include statement (no confidence info — don't filter out)
     c. ELIF effective >= min_confidence:
        → Include statement
     d. ELSE:
        → Exclude statement

EXIT → return ParseResult(
  statements=kept_statements,
  errors=parse_result.errors,
  warnings=parse_result.warnings,
  is_valid=parse_result.is_valid,
  metadata={**parse_result.metadata, "decay_filtered": True, "min_confidence": min_confidence}
)
```

---

## 5. Error Handling

[Decay_Errors] -> [Error_Codes] ::mod(
  rule="definitional",
  confidence=1.0
)

```
Error Code Range: E900-E999

E900_DECAY_ERROR:
  → General decay calculation failure
  → Example: unexpected exception during decay

E901_INVALID_DECAY_TIMESTAMP:
  → Timestamp string cannot be parsed for age calculation
  → Example: "not-a-date" in timestamp field
  → Note: This is a soft error — function should handle gracefully
    (return original confidence, log warning) rather than hard-fail

Exception Class: STLDecayError(STLError)
```

---

## 6. Edge Cases

[Edge_Cases] -> [Specification] ::mod(
  rule="definitional",
  confidence=0.95
)

| Case | Behavior |
|------|----------|
| No modifiers on statement | `effective_confidence` returns None |
| Has confidence but no timestamp | Returns original confidence (no decay) |
| Has timestamp but no confidence | Returns None |
| Future timestamp (age < 0) | Returns original confidence (no decay) |
| Age = 0 (just created) | Returns original confidence (decay factor = 1.0) |
| Very old (age >> half_life) | Returns value near 0.0, clamped to 0.0 if < min_threshold |
| half_life_days = 0 or negative | Raises STLDecayError(E900) |
| Malformed timestamp string | Returns original confidence, does not raise (graceful degradation) |
| Empty ParseResult | `decay_report` returns empty report, `filter_by_confidence` returns empty result |
| Statement with confidence=0.0 | Returns 0.0 (decay of zero is zero) |

---

## 7. Mathematical Foundation

[Decay_Formula] -> [Exponential_Decay] ::mod(
  rule="definitional",
  confidence=1.0,
  domain="mathematics"
)

```
Exponential half-life decay:

  effective(t) = C₀ × 0.5^(t / t½)

Where:
  C₀  = original confidence value [0.0, 1.0]
  t   = age in days (reference_time - timestamp)
  t½  = half_life_days (configurable, default 30)

Properties:
  - At t = 0:    effective = C₀           (no decay)
  - At t = t½:   effective = C₀ / 2       (halved)
  - At t = 2t½:  effective = C₀ / 4       (quartered)
  - At t = ∞:    effective → 0            (fully decayed)
  - Monotonically decreasing for t > 0
  - Always in [0, C₀] for t ≥ 0
```

---

## 8. Usage Examples

### Single Statement Decay
```python
from stl_parser.decay import effective_confidence
from stl_parser import parse

result = parse('[A] -> [B] ::mod(confidence=0.9, timestamp="2026-01-01T00:00:00Z")')
stmt = result.statements[0]

# 41 days later (Feb 11), with default 30-day half-life:
eff = effective_confidence(stmt, half_life_days=30)
# eff ≈ 0.9 * 0.5^(41/30) ≈ 0.9 * 0.384 ≈ 0.346
```

### Batch Report
```python
from stl_parser.decay import decay_report, DecayConfig

config = DecayConfig(half_life_days=60, min_threshold=0.1)
report = decay_report(result, config)

print(f"Total: {report.total_statements}")
print(f"Decayed: {report.statements_decayed}")
print(f"Mean effective confidence: {report.summary['mean']:.2f}")
```

### Filtering
```python
from stl_parser.decay import filter_by_confidence

fresh = filter_by_confidence(result, min_confidence=0.5, half_life_days=30)
print(f"Statements still above 0.5: {len(fresh.statements)}")
```
