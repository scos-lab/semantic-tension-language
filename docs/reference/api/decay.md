# API: decay

Time-based confidence decay for knowledge freshness management.

**Module:** `stl_parser.decay`
**Import:** `from stl_parser import effective_confidence, decay_report, filter_by_confidence, DecayConfig, DecayReport`

---

## effective_confidence()

```python
effective_confidence(
    statement: Statement,
    half_life_days: float = 30.0,
    reference_time: Optional[datetime] = None
) -> Optional[float]
```

Compute a statement's effective confidence after exponential time decay.

**Formula:** `effective = confidence * 0.5^(age_days / half_life_days)`

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `statement` | `Statement` | — | Statement with `confidence` and `timestamp` modifiers |
| `half_life_days` | `float` | `30.0` | Days for confidence to halve (must be > 0) |
| `reference_time` | `datetime` | `None` | "Now" for age calculation (default: `utcnow`) |

**Returns:** Effective confidence (`float`), or `None` if statement has no confidence.

**Raises:** `STLDecayError` (E900) if `half_life_days <= 0`.

**Graceful degradation:** If timestamp is unparseable, returns original confidence unchanged.

**Example:**

```python
from stl_parser import parse, effective_confidence

result = parse('[A] -> [B] ::mod(confidence=0.95, timestamp="2020-01-01T00:00:00Z")')
decayed = effective_confidence(result.statements[0], half_life_days=365)
```

---

## decay_report()

```python
decay_report(
    parse_result: ParseResult,
    config: Optional[DecayConfig] = None
) -> DecayReport
```

Compute decay analysis for all statements in a document.

**Returns:** `DecayReport` with per-statement results and summary statistics (mean, median, min, max).

---

## filter_by_confidence()

```python
filter_by_confidence(
    parse_result: ParseResult,
    min_confidence: float = 0.5,
    half_life_days: float = 30.0,
    reference_time: Optional[datetime] = None
) -> ParseResult
```

Filter statements by effective confidence after decay. Keeps statements without confidence (doesn't filter out unknowns).

**Returns:** New `ParseResult`.

---

## DecayConfig

```python
class DecayConfig(BaseModel):
    half_life_days: float = 30.0          # Days to halve (> 0)
    min_threshold: float = 0.01           # Floor value [0.0, 1.0]
    reference_time: Optional[datetime] = None
```

---

## DecayReport

```python
class DecayReport(BaseModel):
    decayed_statements: List[DecayedStatement] = []
    config: DecayConfig
    total_statements: int = 0
    statements_with_timestamp: int = 0
    statements_decayed: int = 0
    summary: Dict[str, Any] = {}    # mean, median, min, max, count
```

---

## DecayedStatement

```python
class DecayedStatement(BaseModel):
    statement: Statement
    original_confidence: Optional[float] = None
    effective_confidence: Optional[float] = None
    age_days: Optional[float] = None
    decay_ratio: Optional[float] = None
```
