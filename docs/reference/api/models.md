# API: models

Pydantic v2 data models for STL structures.

**Module:** `stl_parser.models`
**Import:** `from stl_parser import Anchor, Modifier, Statement, ParseResult, AnchorType, PathType`

---

## Anchor

```python
class Anchor(BaseModel):
    name: str                          # Required, 1-64 chars
    namespace: Optional[str] = None    # Optional namespace prefix
    type: Optional[AnchorType] = None  # Optional type classification
```

**Validation Rules:**
- `name`: Alphanumeric + underscore + Unicode letters. No special chars except `_`. Max 64 chars. Cannot be empty or a reserved word.
- `namespace`: Alphanumeric + dots. Optional.

**Methods:**
- `__str__()` — Returns `[Namespace:Name]` or `[Name]`
- `__hash__()` — Hashable for use in sets/dicts

**Example:**

```python
from stl_parser import Anchor
a = Anchor(name="Einstein")
print(str(a))  # [Einstein]

a2 = Anchor(name="Energy", namespace="Physics")
print(str(a2))  # [Physics:Energy]
```

---

## AnchorType

```python
class AnchorType(str, Enum):
    CONCEPT = "Concept"
    RELATIONAL = "Relational"
    EVENT = "Event"
    ENTITY = "Entity"
    NAME = "Name"
    AGENT = "Agent"
    QUESTION = "Question"
    VERIFIER = "Verifier"
    PATH_SEGMENT = "PathSegment"
```

---

## PathType

```python
class PathType(str, Enum):
    SEMANTIC = "Semantic"
    ACTION = "Action"
    COGNITIVE = "Cognitive"
    CAUSAL = "Causal"
    INFERENTIAL = "Inferential"
    REFLEXIVE = "Reflexive"
```

---

## Modifier

```python
class Modifier(BaseModel):
    # Temporal
    time: Optional[str] = None
    duration: Optional[str] = None
    frequency: Optional[str] = None
    tense: Optional[str] = None

    # Spatial
    location: Optional[str] = None
    domain: Optional[str] = None
    scope: Optional[str] = None

    # Logical
    certainty: Optional[float] = None    # 0.0-1.0
    confidence: Optional[float] = None   # 0.0-1.0
    necessity: Optional[str] = None
    rule: Optional[str] = None

    # Provenance
    source: Optional[str] = None
    author: Optional[str] = None
    timestamp: Optional[str] = None
    version: Optional[str] = None

    # Affective
    emotion: Optional[str] = None
    intensity: Optional[float] = None    # 0.0-1.0
    valence: Optional[str] = None

    # Value
    value: Optional[str] = None
    alignment: Optional[str] = None
    priority: Optional[Any] = None

    # Causal
    cause: Optional[str] = None
    effect: Optional[str] = None
    strength: Optional[float] = None     # 0.0-1.0
    conditionality: Optional[str] = None

    # Cognitive
    intent: Optional[str] = None
    focus: Optional[str] = None
    perspective: Optional[str] = None

    # Mood
    mood: Optional[str] = None
    modality: Optional[str] = None

    # Custom
    custom: Dict[str, Any] = {}
```

Pydantic `extra="allow"` — any non-standard keys parsed from STL text are stored as extra fields, accessible via `getattr()`.

---

## Statement

```python
class Statement(BaseModel):
    source: Anchor
    target: Anchor
    arrow: str = "→"                        # "→" or "->"
    modifiers: Optional[Modifier] = None
    path_type: Optional[PathType] = None
    line: Optional[int] = None
    column: Optional[int] = None
```

**Methods:**
- `__str__()` — Returns STL text: `[A] -> [B] ::mod(...)`
- `__eq__()` — Semantic equality (ignores line/column)
- `__hash__()` — Based on string representation

---

## ParseResult

```python
class ParseResult(BaseModel):
    statements: List[Statement] = []
    errors: List[ParseError] = []
    warnings: List[ParseWarning] = []
    is_valid: bool = True
    extraction_metadata: Optional[Dict[str, Any]] = None
```

**Methods:**

| Method | Return Type | Description |
|--------|------------|-------------|
| `to_json(**kwargs)` | `str` | Serialize to JSON |
| `to_dict()` | `dict` | Serialize to dictionary |
| `to_stl()` | `str` | Serialize to STL text |
| `find(**kwargs)` | `Optional[Statement]` | Convenience delegate to `query.find()` |
| `filter(**kwargs)` | `ParseResult` | Convenience delegate to `query.filter_statements()` |

---

## ParseError

```python
class ParseError(BaseModel):
    code: str          # E001-E199
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None
```

---

## ParseWarning

```python
class ParseWarning(BaseModel):
    code: str          # W001-W099
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
```
