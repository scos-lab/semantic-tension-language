# API: llm

Three-stage pipeline for cleaning and repairing LLM-generated STL output.

**Module:** `stl_parser.llm`
**Import:** `from stl_parser import clean, repair, validate_llm_output, prompt_template, LLMValidationResult`

---

## validate_llm_output()

```python
validate_llm_output(
    raw_text: str,
    schema: Optional[STLSchema] = None
) -> LLMValidationResult
```

Run the full 3-stage pipeline: **clean → repair → parse** (+ optional schema validation).

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `raw_text` | `str` | — | Raw LLM output text |
| `schema` | `STLSchema` | `None` | Optional schema for post-repair validation |

**Returns:** `LLMValidationResult`

**Example:**

```python
from stl_parser import validate_llm_output
result = validate_llm_output("A => B mod(confience=1.5)")
print(result.is_valid, len(result.repairs))
```

---

## clean()

```python
clean(raw_text: str) -> Tuple[str, List[RepairAction]]
```

Stage 1: Text-level normalization.

**Handles:** Code fence extraction, prose stripping, arrow normalization (`=>` → `->`), multi-line merge, markdown escape removal.

**Returns:** Tuple of (cleaned text, list of repair actions).

---

## repair()

```python
repair(text: str) -> Tuple[str, List[RepairAction]]
```

Stage 2: Structural repair.

**Handles:** Missing `::` prefix, missing brackets, unquoted strings, out-of-range value clamping, modifier key typo correction.

**Returns:** Tuple of (repaired text, list of repair actions).

---

## prompt_template()

```python
prompt_template(schema: Optional[STLSchema] = None) -> str
```

Generate an instruction prompt for LLMs describing STL syntax. If a schema is provided, includes domain-specific constraints.

**Returns:** String suitable as a system message.

---

## LLMValidationResult

```python
class LLMValidationResult(BaseModel):
    statements: List[Statement] = []
    errors: List[ParseError] = []
    warnings: List[ParseWarning] = []
    is_valid: bool = True
    repairs: List[RepairAction] = []
    cleaned_text: str = ""
    original_text: str = ""
    schema_result: Optional[Any] = None
```

---

## RepairAction

```python
class RepairAction(BaseModel):
    type: str           # Repair type identifier
    line: Optional[int] # Line number
    original: str       # Text before repair
    repaired: str       # Text after repair
    description: str    # Human-readable description
```
