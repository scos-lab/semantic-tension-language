# How-To: Manage Confidence Decay

Use time-based confidence decay to manage knowledge freshness. Older statements automatically lose confidence over time, letting you filter stale knowledge from your graph.

**Prerequisites:** Familiarity with [STL syntax](../reference/stl-syntax.md) and the `confidence` / `timestamp` modifiers.

---

## The Decay Model

STL uses exponential decay:

```
effective_confidence = confidence * 0.5^(age_days / half_life_days)
```

- **confidence**: Original confidence value (0.0-1.0)
- **age_days**: Days since the statement's `timestamp`
- **half_life_days**: How many days for confidence to halve (default: 30)

A statement with `confidence=0.90` and `half_life_days=365`:
- After 1 year: `0.90 * 0.5 = 0.45`
- After 2 years: `0.90 * 0.25 = 0.225`
- After 5 years: `0.90 * 0.03 = 0.028`

---

## Single Statement Decay

```python
from stl_parser import parse, effective_confidence

result = parse("""
[Study_X] -> [Finding_Y] ::mod(
  confidence=0.90,
  timestamp="2024-01-15T00:00:00Z",
  source="doi:10.1234/study"
)
""")

stmt = result.statements[0]

# Default half-life: 30 days
decayed = effective_confidence(stmt)
print(f"Effective confidence: {decayed:.4f}")

# Custom half-life: 365 days (slower decay)
decayed_slow = effective_confidence(stmt, half_life_days=365)
print(f"With 365-day half-life: {decayed_slow:.4f}")
```

**Notes:**
- Returns `None` if the statement has no `confidence` modifier
- If `timestamp` is missing or unparseable, returns original confidence unchanged

---

## Batch Decay Report

Analyze decay across an entire document:

```python
from stl_parser import parse, decay_report
from stl_parser.decay import DecayConfig

result = parse("""
[Fresh_Study] -> [Finding_A] ::mod(confidence=0.95, timestamp="2026-02-01T00:00:00Z")
[Old_Study] -> [Finding_B] ::mod(confidence=0.90, timestamp="2020-06-15T00:00:00Z")
[Ancient_Source] -> [Claim_C] ::mod(confidence=0.85, timestamp="2015-01-01T00:00:00Z")
[No_Timestamp] -> [Claim_D] ::mod(confidence=0.80)
""")

config = DecayConfig(half_life_days=365, min_threshold=0.01)
report = decay_report(result, config=config)

print(f"Total statements: {report.total_statements}")
print(f"With timestamp: {report.statements_with_timestamp}")
print(f"Decayed: {report.statements_decayed}")
print(f"Summary: {report.summary}")

for ds in report.decayed_statements:
    name = ds.statement.source.name
    orig = ds.original_confidence
    eff = ds.effective_confidence
    age = ds.age_days
    if age is not None:
        print(f"  {name}: {orig} -> {eff:.4f} (age: {age:.0f} days)")
    else:
        print(f"  {name}: {orig} (no timestamp)")
```

---

## Filter Stale Knowledge

Remove statements whose effective confidence falls below a threshold:

```python
from stl_parser import parse, filter_by_confidence

result = parse("""
[Fresh] -> [A] ::mod(confidence=0.95, timestamp="2026-02-01T00:00:00Z")
[Old] -> [B] ::mod(confidence=0.90, timestamp="2020-01-01T00:00:00Z")
[Very_Old] -> [C] ::mod(confidence=0.80, timestamp="2015-01-01T00:00:00Z")
[No_Time] -> [D] ::mod(confidence=0.70)
""")

# Keep only statements with effective confidence >= 0.5
fresh = filter_by_confidence(result, min_confidence=0.5, half_life_days=365)
print(f"Kept {len(fresh.statements)} of {len(result.statements)} statements")
```

**Important:** Statements without a `confidence` modifier are kept (not filtered out).

---

## Choosing a Half-Life

| Domain | Suggested Half-Life | Rationale |
|--------|-------------------|-----------|
| Breaking news | 1-7 days | Facts change rapidly |
| Scientific studies | 365-730 days | Replications take time |
| Medical guidelines | 180-365 days | Updated regularly |
| Historical facts | 3650+ days | Rarely change |
| Definitions | No decay needed | Stable by nature |

```python
# News knowledge base
news_fresh = filter_by_confidence(news_result, min_confidence=0.3, half_life_days=7)

# Scientific knowledge base
science_fresh = filter_by_confidence(science_result, min_confidence=0.5, half_life_days=730)
```

---

## Custom Reference Time

By default, decay uses the current time. Override this for reproducible analysis:

```python
from datetime import datetime
from stl_parser import effective_confidence

# Calculate as if it were January 1, 2025
ref_time = datetime(2025, 1, 1)
decayed = effective_confidence(stmt, half_life_days=365, reference_time=ref_time)
```

The same parameter works with `decay_report()` and `filter_by_confidence()`:

```python
from stl_parser import filter_by_confidence

fresh = filter_by_confidence(
    result,
    min_confidence=0.5,
    half_life_days=365,
    reference_time=datetime(2025, 1, 1)
)
```

---

## DecayConfig Reference

```python
from stl_parser.decay import DecayConfig

config = DecayConfig(
    half_life_days=365.0,      # Days for confidence to halve (must be > 0)
    min_threshold=0.01,        # Below this, effective confidence is 0.0
    reference_time=None,       # Override "now" (default: utcnow)
)
```

---

## Combining Decay with Graph Analysis

Filter stale knowledge, then analyze what remains:

```python
from stl_parser import parse_file, filter_by_confidence, STLGraph, STLAnalyzer

# Load and filter
result = parse_file("knowledge.stl")
fresh = filter_by_confidence(result, min_confidence=0.5, half_life_days=365)

# Analyze only fresh knowledge
graph = STLGraph(fresh)
analyzer = STLAnalyzer(fresh)

print(f"Fresh graph: {graph.summary}")
report = analyzer.get_full_analysis_report()
print(f"Confidence range: {report['confidence_metrics']}")
```

---

## See Also

- [API: decay](../reference/api/decay.md) — Full API reference
- [Modifier Reference](../reference/modifiers.md) — `confidence` and `timestamp` fields
- [How-To: Knowledge Graph Pipeline](knowledge-graph-pipeline.md) — Build and analyze graphs
