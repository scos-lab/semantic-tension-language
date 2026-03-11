# Implementation Plan: STL Tooling Ecosystem (Priority 1)

> **Document Type:** Engineering Implementation Plan
> **Version:** 1.0.0
> **Date:** 2026-02-11
> **Author:** Syn-claude (collaborating with wuko / SCOS-Lab)
> **Status:** Approved — ready for implementation
> **Parent Document:** `docs/STL_AS_LLM_PROGRAM_BRIDGE.md` v0.2.0
> **Target:** `parser/stl_parser/` package

---

## 1. Context

STL has moved from theory to production (Cortex Hybrid AI, Feb 2026). The bridge document (v0.2.0) defines 4 Priority 1 tools needed to make STL a usable LLM-program communication protocol:

1. **stl-builder** — Programmatic STL generation
2. **stl-schema** — Formal schema definition & validation
3. **stl-llm** — LLM output cleaning & auto-repair
4. **stl-emitter** — Structured event emitter

**Architecture decision: Monorepo modules** — all new tools as modules inside existing `stl_parser/` package. Single `pip install`, shared Pydantic models, coherent versioning.

---

## 2. Existing Codebase Inventory

**Package:** `parser/stl_parser/` (v1.0.0, Python 3.9+)

| Module | Purpose | LOC | Key APIs |
|--------|---------|-----|----------|
| `models.py` | Pydantic models: Anchor, Modifier, Statement, ParseResult | ~731* | AnchorType (9), PathType (6), Modifier (30+ fields) |
| `grammar.py` | Lark EBNF grammar for STL syntax | ~120 | `STL_GRAMMAR` string, LALR parser |
| `parser.py` | Core parsing + auto-extraction from markdown | ~1000 | `parse()`, `parse_file()`, `parse_statement()`, `is_valid_stl()` |
| `validator.py` | Comprehensive validation | ~500 | `validate_statement()`, `check_semantic_consistency()`, `infer_anchor_type()` |
| `serializer.py` | JSON, RDF/Turtle, roundtrip | ~300 | `to_json()`, `to_rdf()`, `to_stl()`, `from_json()` |
| `graph.py` | NetworkX MultiDiGraph | ~200 | `build_graph()`, `find_paths()`, `find_cycles()`, `detect_conflicts()` |
| `analyzer.py` | Statistical analysis | ~250 | `count_elements()`, `analyze_anchor_types()`, `get_full_analysis_report()` |
| `errors.py` | Error codes E001-E499 + exceptions | ~150 | ErrorCode enum, STLError hierarchy |
| `cli.py` | Typer CLI | ~200 | `stl validate`, `stl parse`, `stl convert`, `stl analyze` |

*\* models.py contains ~375 lines of duplicate code (bug, see Phase 0)*

**Dependencies:** lark, pydantic (v2+), rdflib, networkx, typer, rich

**Test suite:** 12 test modules in `tests/` + root-level test files, pytest + coverage

### Existing Capabilities to Reuse (not duplicate)

| Capability | Location | Reused By |
|------------|----------|-----------|
| Anchor parsing (namespace support) | `models.Anchor` | builder.py |
| Modifier field validation | `validator.validate_modifier()` | builder.py, schema.py |
| Markdown extraction | `parser._extract_stl_fences()` | llm.py (via _utils) |
| Multi-line merging | `parser._merge_multiline_statements()` | llm.py (via _utils) |
| STL line detection | `parser._is_stl_line()` | llm.py (via _utils) |
| Statement validation | `validator.validate_statement()` | builder.py |
| STL text serialization | `serializer.to_stl()` | builder.py, emitter.py |
| Lark grammar pattern | `grammar.py` | schema.py (own grammar) |

---

## 3. Known Bugs to Fix First (Phase 0)

### 3.1 models.py — Duplicate methods

`Statement` class has `__eq__` and `__hash__` duplicated ~20 times (lines 268-644). Only the last definition is active (Python uses last). Delete all but first pair. Reduces file from ~731 to ~355 lines.

### 3.2 parser.py — Duplicate block + missing import

Duplicate `extraction_metadata` assignment block in `parse_file()`. Also references `ErrorCode.E003_EXTRACTION_SYNTAX_ERROR` without importing `ErrorCode`. Fix: keep one block, add import.

### 3.3 README.md — Incorrect API examples

| README Shows | Actual API |
|-------------|------------|
| `STLParser()` class | `parse()` module-level function |
| `result.to_rdf(format="turtle")` | `to_rdf(result, format="turtle")` |
| `stl stats` CLI command | `stl analyze` |
| `stl validate-dir` CLI command | Does not exist |

---

## 4. Implementation Phases

### Phase 0: Bug Fixes

**Files:**
- `stl_parser/models.py` — remove ~375 duplicate lines
- `stl_parser/parser.py` — fix duplicate block, add ErrorCode import
- `parser/README.md` — fix API examples

**Verification:** `python -m pytest` — all existing tests must pass unchanged.

---

### Phase 1: _utils.py — Extract Shared Utilities

**New file:** `stl_parser/_utils.py` (~250 LOC)

Move from parser.py:
```python
# Functions to move (remove leading _ since module itself is internal):
is_stl_line()              # Heuristic STL detection
extract_stl_fences()       # Markdown fence extraction
extract_stl_heuristic()    # Pattern-based extraction
auto_extract_stl()         # Auto-detection
is_pure_stl()              # Purity check
remove_markdown_escapes()  # Markdown escape removal
merge_multiline_statements()  # Multi-line merging
remap_line_numbers()       # Line number remapping
```

**Modify:** `stl_parser/parser.py` — import from `_utils`, preserve backward compatibility:
```python
from ._utils import (
    is_stl_line as _is_stl_line,
    extract_stl_fences as _extract_stl_fences,
    # ... etc
)
```

**Modify:** `stl_parser/errors.py` — add new error code ranges:
```python
# Builder Errors (E500-E599)
E500_BUILDER_ERROR = "E500"
E501_INVALID_BUILDER_STATE = "E501"
E502_BUILDER_VALIDATION_FAILED = "E502"

# Schema Errors (E600-E699)
E600_SCHEMA_PARSE_ERROR = "E600"
E601_SCHEMA_VALIDATION_FAILED = "E601"
E602_INVALID_SCHEMA_FORMAT = "E602"
E603_SCHEMA_CONSTRAINT_VIOLATION = "E603"

# LLM Errors (E700-E799)
E700_LLM_CLEAN_ERROR = "E700"
E701_LLM_REPAIR_FAILED = "E701"
E702_UNREPAIRABLE_OUTPUT = "E702"

# Emitter Errors (E800-E899)
E800_EMITTER_ERROR = "E800"
E801_EMITTER_LOG_WRITE_FAILED = "E801"
```

Plus 4 new exception subclasses: `STLBuilderError`, `STLSchemaError`, `STLLLMError`, `STLEmitterError` (all inherit `STLError`).

**Verification:** All existing tests pass with zero changes (pure refactor).

---

### Phase 2: builder.py — Programmatic STL Generation

**New file:** `stl_parser/builder.py` (~300 LOC)

**API Design:**

```python
from stl_parser.builder import stl, stl_doc

# Single statement
stmt = (
    stl("[Obs:ToolLoop]", "[Act:BreakLoop]")
    .mod(confidence=0.95, severity="critical", rule="causal")
    .mod(context="tool called 2x consecutively")
    .build()
)
# Returns: Statement (existing Pydantic model)

# Access as STL text
print(stmt)  # [Obs:ToolLoop] -> [Act:BreakLoop] ::mod(confidence=0.95, ...)

# Batch document
doc = stl_doc(
    stl("[A]", "[B]").mod(confidence=0.9),
    stl("[B]", "[C]").mod(rule="causal", strength=0.8),
)
# Returns: ParseResult with multiple statements
```

**Key classes & functions:**

```python
class StatementBuilder:
    """Fluent builder for a single STL statement."""

    def __init__(self, source: str, target: str):
        # Handles: "[Obs:X]", "Obs:X", "[X]", "X"
        self._source = self._parse_anchor_str(source)
        self._target = self._parse_anchor_str(target)
        self._modifiers: Dict[str, Any] = {}

    @staticmethod
    def _parse_anchor_str(s: str) -> Anchor:
        """Parse anchor string into Anchor object.
        Strips brackets, splits on ':' for namespace."""

    def mod(self, **kwargs) -> 'StatementBuilder':
        """Add modifiers. Chainable."""
        self._modifiers.update(kwargs)
        return self

    def path_type(self, pt: PathType) -> 'StatementBuilder':
        """Set explicit path type."""

    def no_validate(self) -> 'StatementBuilder':
        """Skip build-time validation."""

    def build(self) -> Statement:
        """Build validated Statement. Raises STLBuilderError on invalid."""
        # Separates standard Modifier fields from custom fields
        # Validates via validate_statement()

def stl(source: str, target: str) -> StatementBuilder:
    """Factory function. Main entry point."""

def stl_doc(*builders) -> ParseResult:
    """Build ParseResult from multiple builders/statements."""
```

**Test:** `tests/test_builder.py` (~150 LOC)

| Test | Description |
|------|-------------|
| `test_simple_build` | `stl("[A]", "[B]").build()` → valid Statement |
| `test_namespaced_build` | `stl("Obs:ToolLoop", "Act:BreakLoop")` parses namespaces |
| `test_mod_chaining` | `.mod(a=1).mod(b=2)` accumulates |
| `test_custom_modifiers` | Non-standard keys → `modifier.custom` dict |
| `test_build_validation_error` | `confidence=2.0` raises STLBuilderError |
| `test_no_validate` | `.no_validate().build()` skips validation |
| `test_stl_doc` | Multiple builders → ParseResult |
| `test_bracket_stripping` | `"[A]"` and `"A"` both work |
| `test_to_stl_roundtrip` | build → to_stl → parse → compare |

---

### Phase 3: schema.py — Schema Definition & Validation

**New file:** `stl_parser/schema.py` (~800 LOC) — largest module

**Schema file format (`.stl.schema`):**

```
namespace Obs { ToolLoop, EmptyResponse, Error }
namespace Act { BreakLoop, Retry, Escalate }
namespace Result { Recovered, Failed }

[Obs:*] -> [Act:*] {
    confidence: float [0.0, 1.0] REQUIRED
    severity: enum("info", "warning", "critical") REQUIRED
    rule: enum("causal", "logical") DEFAULT "causal"
    context: string OPTIONAL
}

[Act:*] -> [Result:*] {
    confidence: float [0.0, 1.0] REQUIRED
    timestamp: datetime REQUIRED
    context: string OPTIONAL
}
```

**Key components:**

**3a. Lark grammar for schema syntax** (follows grammar.py convention):
```python
SCHEMA_GRAMMAR = r"""
    ?start: schema_block+
    schema_block: namespace_decl | constraint_block
    namespace_decl: "namespace" IDENTIFIER "{" identifier_list "}"
    constraint_block: anchor_pattern "->" anchor_pattern "{" field_def+ "}"
    anchor_pattern: "[" ns_pattern ":" name_pattern "]" | "[" name_pattern "]"
    field_def: IDENTIFIER ":" type_spec constraint* field_attr*
    type_spec: "float" range_spec? | "int" range_spec? | "string" | "bool" | "datetime" | enum_spec
    ...
"""
```

**3b. Data models:**
```python
class FieldConstraint(BaseModel):
    name: str
    type: FieldType  # float, int, string, bool, datetime, enum
    required: bool = False
    default: Optional[Any] = None
    range_min: Optional[float] = None
    range_max: Optional[float] = None
    enum_values: Optional[List[str]] = None

class AnchorPattern(BaseModel):
    namespace: Optional[str] = None  # None or "*" = any
    name: Optional[str] = None       # None or "*" = any

class ConstraintBlock(BaseModel):
    source_pattern: AnchorPattern
    target_pattern: AnchorPattern
    fields: List[FieldConstraint]

class STLSchema(BaseModel):
    namespaces: Dict[str, Set[str]]
    constraints: List[ConstraintBlock]
```

**3c. Validation:**
```python
class SchemaValidator:
    def validate(self, parse_result: ParseResult) -> SchemaValidationResult:
        # For each statement:
        # 1. Match source/target anchors against namespace declarations
        # 2. Find matching constraint block (by anchor pattern)
        # 3. Check REQUIRED fields present
        # 4. Check types and ranges
        # 5. Apply DEFAULTs for missing optional fields
```

**3d. Bidirectional Pydantic support:**
```python
# Direction 1: Schema → Pydantic (STL-first)
schema = load_schema("events.stl.schema")
Model = schema.to_pydantic("EventModel")

# Direction 2: Pydantic → Schema (Python-first)
from pydantic import BaseModel, Field
class ToolCallEvent(BaseModel):
    confidence: float = Field(ge=0.0, le=1.0)
    severity: str = Field(pattern="^(info|warning|critical)$")

stl_schema = STLSchema.from_pydantic(ToolCallEvent, source_ns="Obs", target_ns="Act")
```

**Test:** `tests/test_schema.py` (~200 LOC) + `tests/fixtures/events.stl.schema`

---

### Phase 4: llm.py — LLM Output Cleaning & Auto-Repair

**New file:** `stl_parser/llm.py` (~400 LOC)

**API Design:**

```python
from stl_parser.llm import clean, repair, validate_llm_output, prompt_template

# Step 1: Clean raw LLM output
cleaned = clean(raw_llm_output)

# Step 2: Full pipeline (clean + repair + parse + validate)
result = validate_llm_output(raw_output, schema=optional_schema)
print(result.statements)     # parsed statements
print(result.repairs)        # list of RepairAction
print(result.was_repaired)   # True if any repairs applied

# Step 3: Generate teaching prompt
prompt = prompt_template(schema="events.stl.schema", examples=3)
```

**Auto-repair rules:**

| LLM Output Issue | Auto-Repair | Rule Name |
|-----------------|-------------|-----------|
| `` ```stl\n...\n``` `` | Strip markdown code block | `strip_fences` |
| `::mod(severity=critical)` | Add quotes: `severity="critical"` | `quote_strings` |
| `[A] --> [B]` | Normalize arrow: `[A] -> [B]` | `normalize_arrow` |
| `[ A ] -> [ B ]` | Trim whitespace: `[A] -> [B]` | `trim_brackets` |
| `confidence=1.5` | Clamp: `confidence=1.0` + warning | `clamp_range` |
| `[A -> [B]` | Add missing `]`: `[A] -> [B]` | `fix_brackets` |
| `mod(...)` (missing `::`) | Add prefix: `::mod(...)` | `fix_mod_prefix` |

**Data models:**
```python
@dataclass
class RepairAction:
    line: Optional[int]
    original: str
    repaired: str
    rule: str

@dataclass
class LLMValidationResult:
    parse_result: ParseResult
    repairs: List[RepairAction]
    raw_input: str
    cleaned_input: str
```

**Reuses from _utils:** `remove_markdown_escapes()`, `extract_stl_fences()`, `merge_multiline_statements()`, `is_stl_line()`

**Test:** `tests/test_llm.py` (~200 LOC)

---

### Phase 5: emitter.py — Structured Event Emitter

**New file:** `stl_parser/emitter.py` (~400 LOC)

**API Design:**

```python
from stl_parser.emitter import STLEmitter

# File-based emitter
emitter = STLEmitter(log_path="events.log", namespace="MyApp")
emitter.emit(source="Obs:Error", target="Act:Retry", confidence=0.9, severity="warning")
# Writes to file: [MyApp.Obs:Error] -> [MyApp.Act:Retry] ::mod(confidence=0.9, severity="warning", timestamp="2026-02-11T...")

# Context manager
with STLEmitter(log_path="events.log", namespace="App") as e:
    e.emit("Obs:Start", "Act:Init", confidence=1.0)
    e.emit("Obs:Error", "Act:Retry", confidence=0.8, severity="warning")

# Stream-based (stdout)
emitter = STLEmitter(stream=sys.stdout)

# Batch
emitter.emit_batch([
    {"source": "Obs:A", "target": "Act:B", "confidence": 0.9},
    {"source": "Obs:C", "target": "Act:D", "confidence": 0.8},
])
```

**Features:**
- Write to file (append mode) or stream (stdout default)
- Auto-timestamp injection (`auto_timestamp=True` by default)
- Namespace prefixing
- Uses `builder.stl()` internally
- Context manager support
- Event counter

**Test:** `tests/test_emitter.py` (~150 LOC)

---

### Phase 6: CLI Extension + __init__.py

**Modify:** `stl_parser/cli.py`

New commands:
```
stl build <source> <target> --mod "confidence=0.95,severity=critical"
stl clean <file> [--schema FILE] [--output FILE]
stl schema validate <file> --schema <schema_file>
stl schema generate <schema_file> [--output FILE]
```

**Modify:** `stl_parser/__init__.py`

New exports:
```python
# Builder
from .builder import stl, stl_doc, StatementBuilder
# Schema
from .schema import STLSchema, load_schema, validate_against_schema
# LLM
from .llm import clean, repair, validate_llm_output, prompt_template
# Emitter
from .emitter import STLEmitter
```

---

### Phase 7: Integration Tests

**New file:** `tests/test_integration.py` (~150 LOC)

| Test Class | Tests |
|-----------|-------|
| `TestBuilderToParser` | Roundtrip: build → to_stl → parse → compare |
| `TestBuilderToSchema` | Builder output validates against schema |
| `TestLLMPipeline` | Messy LLM output → clean → repair → parse → validate |
| `TestEmitterRoundtrip` | Emit to file → read file → parse → verify |
| `TestFullPipeline` | Build → emit → parse → schema validate → graph analyze |

---

## 5. Build Order & Dependencies

```
Phase 0 (bugs) ──→ Phase 1 (_utils + errors) ──→ Phase 2 (builder)
                                                       │
                                                       ├──→ Phase 3 (schema)
                                                       │         │
                                                       ├──→ Phase 4 (llm) ←── uses schema optionally
                                                       │
                                                       └──→ Phase 5 (emitter)

Phase 2-5 ──→ Phase 6 (CLI + exports) ──→ Phase 7 (integration tests)
```

**Note:** Phase 3, 4, 5 can be built in parallel after Phase 2 completes. Phase 3 (schema) is the critical path due to complexity.

---

## 6. File Inventory

### New Files (11)

| File | Phase | LOC |
|------|-------|-----|
| `stl_parser/_utils.py` | 1 | ~250 |
| `stl_parser/builder.py` | 2 | ~300 |
| `stl_parser/schema.py` | 3 | ~800 |
| `stl_parser/llm.py` | 4 | ~400 |
| `stl_parser/emitter.py` | 5 | ~400 |
| `tests/test_builder.py` | 2 | ~150 |
| `tests/test_schema.py` | 3 | ~200 |
| `tests/test_llm.py` | 4 | ~200 |
| `tests/test_emitter.py` | 5 | ~150 |
| `tests/test_integration.py` | 7 | ~150 |
| `tests/fixtures/events.stl.schema` | 3 | ~10 |

### Modified Files (6)

| File | Phase | Changes |
|------|-------|---------|
| `stl_parser/models.py` | 0 | Remove ~375 duplicate lines |
| `stl_parser/parser.py` | 0+1 | Fix dup block, import from _utils |
| `stl_parser/errors.py` | 1 | Add E500-E899 + 4 exception subclasses |
| `stl_parser/__init__.py` | 6 | Add new exports |
| `stl_parser/cli.py` | 6 | Add build, clean, schema commands |
| `parser/README.md` | 0 | Fix API examples |

### Total: ~3,150 LOC new code

---

## 7. Verification Protocol

### Per-Phase Verification

After each phase:
```bash
cd C:\Users\T\source\repos\STL\semantic-tension-language\parser
python -m pytest tests/ -v --tb=short
```

### Final Verification (after Phase 7)

```bash
# Full test suite with coverage
python -m pytest tests/ -v --cov=stl_parser --cov-report=term

# Smoke test all new modules
python -c "
from stl_parser import stl, stl_doc, parse, to_stl
stmt = stl('[Obs:ToolLoop]', '[Act:BreakLoop]').mod(confidence=0.95, severity='critical').build()
print('Builder OK:', stmt)

doc = parse(to_stl(stl_doc(stl('[A]', '[B]').mod(confidence=0.9))))
print('Roundtrip OK:', len(doc.statements), 'statements')
"

python -c "
from stl_parser import clean, validate_llm_output
messy = '\`\`\`stl\n[A] --> [B] ::mod(confidence=1.5)\n\`\`\`'
result = validate_llm_output(messy)
print('LLM OK:', result.was_repaired, result.repairs)
"

python -c "
from stl_parser import STLEmitter
import io
buf = io.StringIO()
e = STLEmitter(stream=buf, namespace='Test')
e.emit('Obs:X', 'Act:Y', confidence=0.9)
print('Emitter OK:', buf.getvalue())
"
```

### MCP Validator Check

```python
# Validate a builder-generated statement with MCP stl tools
from stl_parser import stl
stmt = stl('[Obs:Test]', '[Act:Verify]').mod(confidence=0.95, rule='causal').build()
# Use mcp__local-ayos__validate_stl with str(stmt)
```

---

## 8. Risk Register

| Risk | Mitigation |
|------|-----------|
| schema.py Lark grammar complexity | Start with minimal grammar, iterate. Test with fixture files early. |
| Breaking existing tests in Phase 1 refactor | Pure move + import alias. Run tests after every file change. |
| models.py cleanup breaks serialization | The duplicate methods are dead code (Python uses last def). Removal is safe. |
| LLM repair heuristics too aggressive | Each repair is a separate rule with its own test. Can disable individually. |
| Circular imports between new modules | Dependency graph is acyclic: builder ← schema, builder ← emitter, _utils ← llm. schema import in llm.py is lazy (inside function). |

---

## 9. Post-Implementation Next Steps

After Priority 1 tooling is complete:

1. **LLM-Native Demo** (Tool 6 from bridge document) — build the proof-of-concept showing LLM → STL → Program
2. **Publish to PyPI** — `pip install stl-parser` with all new modules
3. **Priority 2 tools** — stl-stream, stl-query, stl-diff
4. **Bridge document v0.3.0** — update with implementation status and lessons learned

---

*This plan was designed based on thorough codebase exploration of the existing stl_parser package (11 modules, 12 test files, pyproject.toml configuration) on 2026-02-11.*
