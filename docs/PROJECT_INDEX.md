# STL Project Index

> **Purpose:** Quick reference for AI partners and collaborators to understand the project structure, module responsibilities, and key APIs.
> **Version:** 1.7.0
> **Last Updated:** 2026-02-13

---

## 1. Directory Structure

```
semantic-tension-language/
│
├── LICENSE                         # Apache 2.0 (code) + CC BY 4.0 (spec)
├── README.md                       # Project overview and quick start
│
├── spec/                           # Language Specifications
│   ├── stl-core-spec-v1.0.md                 # Core syntax specification
│   └── stl-core-spec-v1.0-supplement.md      # Extended spec (anchor types, modifiers, validation)
│
├── docs/                           # Documentation
│   ├── PROJECT_INDEX.md                       # This file
│   ├── COMPLETION_REPORT_TOOLING_P1.md        # Priority 1 tooling delivery report
│   ├── IMPLEMENTATION_PLAN_TOOLING_P1.md      # Tooling implementation plan
│   ├── STL_AS_LLM_PROGRAM_BRIDGE.md           # Vision: STL as LLM-program bridge
│   ├── STL_TOOLING_FEATURES.md                  # Human-readable feature overview (Chinese)
│   └── stlc/                                  # STLC Semantic Specifications
│       ├── stl_builder_v1.0.0.stlc.md        # Builder module spec
│       ├── stl_schema_v1.0.0.stlc.md         # Schema module spec
│       ├── stl_llm_v1.0.0.stlc.md            # LLM module spec
│       ├── stl_emitter_v1.0.0.stlc.md        # Emitter module spec
│       ├── stl_decay_v1.0.0.stlc.md          # [P2] Decay module spec
│       ├── stl_cli_ext_v1.0.0.stlc.md        # [P2] CLI extensions spec
│       ├── stl_query_v1.0.0.stlc.md          # [P0] Query module spec
│       ├── stl_cli_query_v1.0.0.stlc.md      # [P1] CLI Query command spec
│       ├── stl_diff_v1.0.0.stlc.md           # [P2] Diff/Patch module spec
│       └── stl_reader_v1.0.0.stlc.md        # [P2] Streaming reader spec
│
├── docs/schemas/                       # Schema Ecosystem (domain schemas)
│   ├── README.md                                # Schema index & usage guide
│   ├── _template.stl.schema                     # Blank template for new domains
│   ├── tcm.stl.schema                           # Traditional Chinese Medicine
│   ├── scientific.stl.schema                    # Scientific research
│   ├── causal.stl.schema                        # Causal inference
│   ├── historical.stl.schema                    # Historical knowledge
│   ├── medical.stl.schema                       # Medical/clinical
│   └── legal.stl.schema                         # Legal reasoning
│
└── parser/                         # Python Package (pip installable)
    ├── pyproject.toml                         # Package config, dependencies, entry points
    ├── requirements.txt                       # Runtime deps (lark, pydantic, rdflib, networkx, typer, rich)
    ├── requirements-dev.txt                   # Dev deps (pytest, coverage, black, mypy, ruff)
    ├── README.md                              # Parser-specific README with API examples
    ├── CONTRIBUTING.md                        # Contribution guidelines
    ├── .github/workflows/ci.yml               # CI pipeline (Python 3.9-3.12)
    │
    ├── stl_parser/                            # Source package
    │   ├── __init__.py                        # Public API exports + version
    │   ├── grammar.py                         # Lark EBNF grammar definition
    │   ├── parser.py                          # Core parser (text/file → ParseResult)
    │   ├── models.py                          # Pydantic data models (Anchor, Modifier, Statement, ParseResult)
    │   ├── validator.py                       # Syntactic + semantic validation
    │   ├── serializer.py                      # JSON / JSON-LD / RDF serialization
    │   ├── graph.py                           # NetworkX graph construction
    │   ├── analyzer.py                        # Statistical analysis
    │   ├── errors.py                          # Error codes + exception hierarchy
    │   ├── _utils.py                          # Internal shared utilities
    │   ├── cli.py                             # Typer CLI (stl validate|convert|analyze|build|clean|schema-validate|query|diff|patch)
    │   ├── builder.py                         # [P1] Fluent statement builder API
    │   ├── schema.py                          # [P1] Schema definition & validation
    │   ├── llm.py                             # [P1] LLM output cleaning & auto-repair
    │   ├── emitter.py                         # [P1] Thread-safe event emitter
    │   ├── decay.py                           # [P2] Query-time confidence decay
    │   ├── query.py                           # [P0] Find, filter, select, pointer
    │   ├── diff.py                            # [P2] Semantic diff and patch
    │   └── reader.py                          # [P2] Streaming reader (complement to emitter)
    │
    └── tests/                                 # Test suite (530 passing, 88% coverage)
        ├── conftest.py                        # Pytest fixtures
        ├── test_parser.py                     # Core parser tests
        ├── test_validator.py                  # Validation tests
        ├── test_serializer.py                 # Serialization tests
        ├── test_graph.py                      # Graph tests
        ├── test_analyzer.py                   # Analyzer tests
        ├── test_cli.py                        # CLI tests (20 — including P2 commands)
        ├── test_cli_query.py                  # [P1] CLI query tests (30)
        ├── test_auto_extraction.py            # STL extraction from mixed text
        ├── test_multiline_merge.py            # Multi-line statement tests
        ├── test_empty.py                      # Edge case: empty input
        ├── test_builder.py                    # [P1] Builder tests (28)
        ├── test_schema.py                     # [P1] Schema tests (25)
        ├── test_llm.py                        # [P1] LLM tests (27)
        ├── test_emitter.py                    # [P1] Emitter tests (24)
        ├── test_utils.py                      # Utility tests (14)
        ├── test_decay.py                      # [P2] Decay tests (25)
        ├── test_query.py                      # [P0] Query tests (67)
        ├── test_diff.py                       # [P2] Diff/Patch tests (40)
        └── test_reader.py                     # [P2] Streaming reader tests (37)
```

---

## 2. Module Reference

### 2.1 Core Parsing Pipeline

| Module | Purpose | Key API |
|--------|---------|---------|
| **grammar.py** | Lark EBNF grammar for STL v1.0 syntax | `STL_GRAMMAR` (string constant) |
| **parser.py** | Transform text into structured models | `parse(text) -> ParseResult`, `parse_file(path) -> ParseResult` |
| **models.py** | Pydantic data models for all STL elements | `Anchor`, `Modifier`, `Statement`, `ParseResult`, `AnchorType`, `PathType` |
| **validator.py** | Structural + semantic validation | `validate_statement(stmt) -> (errors, warnings)`, `validate_parse_result(result)` |

### 2.2 Serialization & Analysis

| Module | Purpose | Key API |
|--------|---------|---------|
| **serializer.py** | Multi-format output (JSON, JSON-LD, RDF/Turtle) | `to_json()`, `to_dict()`, `from_json()`, `from_dict()`, `to_stl()` |
| **graph.py** | NetworkX directed multigraph construction | `STLGraph(parse_result)` — `.nodes`, `.edges`, `.cycles()`, `.centrality()` |
| **analyzer.py** | Statistical insights from parsed documents | `STLAnalyzer(parse_result)` — `.summary()`, `.modifier_stats()`, `.confidence_distribution()` |

### 2.3 Tooling Modules (Priority 1 — New)

| Module | Purpose | Key API |
|--------|---------|---------|
| **builder.py** | Programmatic STL construction | `stl(source, target).mod(**kw).build() -> Statement`, `stl_doc(*builders) -> ParseResult` |
| **schema.py** | Schema definition & document validation | `load_schema(text) -> STLSchema`, `validate_against_schema(result, schema)`, `to_pydantic(schema)`, `from_pydantic(model)` |
| **llm.py** | LLM output cleaning, repair, validation | `clean(text)`, `repair(text)`, `validate_llm_output(text, schema=None) -> LLMValidationResult`, `prompt_template(schema=None)` |
| **emitter.py** | Thread-safe structured event logging | `STLEmitter(log_path=, stream=, namespace=, auto_timestamp=)` — `.emit(source_anchor, target_anchor, **mods)`, `.emit_statement(stmt)`, `.comment(text)`, `.section(name)` |

### 2.4 Query Module (Priority 0)

| Module | Purpose | Key API |
|--------|---------|---------|
| **query.py** | Find, filter, select, pointer operations on ParseResult | `find(result, **kw)`, `find_all(result, **kw)`, `filter_statements(result, **kw)`, `select(result, field)`, `stl_pointer(result, path)` |

ParseResult also has convenience methods: `.find()`, `.find_all()`, `.filter()`, `.select()`, `[index]`, `["name"]`.

### 2.5 Tooling Modules (Priority 2)

| Module | Purpose | Key API |
|--------|---------|---------|
| **decay.py** | Query-time confidence decay based on statement age | `effective_confidence(stmt, half_life_days=30)`, `decay_report(result, config)`, `filter_by_confidence(result, min_confidence=0.5)` |
| **diff.py** | Semantic diff and patch for STL documents | `stl_diff(a, b) -> STLDiff`, `stl_patch(doc, diff) -> ParseResult`, `diff_to_text(diff)`, `diff_to_dict(diff)` |
| **reader.py** | Streaming memory-efficient reader (Emitter complement) | `stream_parse(source, where=, on_error=)`, `STLReader(source, where=, tail=)`, `ReaderStats` |

### 2.6 Infrastructure

| Module | Purpose | Key API |
|--------|---------|---------|
| **errors.py** | Error codes E001-E999, warning codes W001-W099, exception hierarchy | `STLError`, `STLParseError`, `STLValidationError`, `STLBuilderError`, `STLSchemaError`, `STLLLMError`, `STLEmitterError`, `STLDecayError`, `STLDiffError`, `STLReaderError`, `ErrorCode` |
| **_utils.py** | Shared internal utilities (extraction, line detection, sanitization) | `is_stl_line()`, `extract_stl_fences()`, `auto_extract_stl()`, `merge_multiline_statements()`, `is_pure_stl()`, `sanitize_anchor_name()` |
| **cli.py** | Command-line interface (Typer + Rich) | `stl validate`, `stl convert`, `stl analyze`, `stl build`, `stl clean`, `stl schema-validate`, `stl query`, `stl diff`, `stl patch` |

---

## 3. Module Dependency Graph

```
models.py          (foundation — no internal deps)
    │
    ├── grammar.py         (no deps)
    │       │
    │       └── parser.py  (grammar + models + _utils)
    │
    ├── _utils.py          (models)
    │
    ├── errors.py          (no deps)
    │
    ├── validator.py       (models + errors)
    │
    ├── serializer.py      (models)
    │
    ├── graph.py           (models + networkx)
    │       │
    │       └── analyzer.py (graph + models)
    │
    ├── builder.py         (models + validator + errors)
    │       │
    │       └── emitter.py (builder + validator + errors)
    │
    ├── schema.py          (models + errors)
    │
    ├── llm.py             (parser + _utils + schema[optional] + errors)
    │
    ├── decay.py           (models + errors)
    │
    ├── query.py           (models + errors)
    │
    ├── diff.py            (models + errors)
    │
    └── reader.py          (parser + query + errors)

cli.py                     (depends on all modules)
```

---

## 4. Data Flow

### 4.1 Parse Pipeline (text → models)

```
Raw STL Text
    │
    ▼
_utils.auto_extract_stl()     ← extract STL from mixed content
    │
    ▼
grammar.py (Lark EBNF)        ← tokenize + parse to CST
    │
    ▼
parser.py (TreeTransformer)    ← CST → Pydantic models
    │
    ▼
ParseResult                    ← statements[] + errors[] + warnings[]
    │
    ├──▶ validator.py          ← structural + semantic validation
    ├──▶ serializer.py         ← JSON / JSON-LD / RDF output
    ├──▶ graph.py              ← NetworkX directed multigraph
    ├──▶ analyzer.py           ← statistical metrics
    ├──▶ query.py              ← find / filter / select / pointer
    ├──▶ diff.py               ← semantic diff / patch
    └──▶ reader.py             ← streaming read (Emitter complement)
```

### 4.2 Builder Pipeline (code → STL)

```
Python code
    │
    ▼
stl("[Source]", "[Target]")    ← factory function
    │
    ▼
StatementBuilder.mod(**kw)     ← accumulate modifiers
    │
    ▼
StatementBuilder.build()       ← create Statement model
    │                             (optionally validates)
    ▼
Statement                      ← ready for emit / serialize
```

### 4.3 LLM Pipeline (noisy text → clean STL)

```
Raw LLM Output (markdown, malformed STL)
    │
    ▼
clean()                        ← strip fences, normalize arrows, remove prose
    │
    ▼
repair()                       ← fix brackets, ::mod prefix, quote strings,
    │                             clamp values, fix typos
    ▼
parse()                        ← standard parser
    │
    ▼
validate_against_schema()      ← optional schema check
    │
    ▼
LLMValidationResult            ← statements + repairs[] + is_valid
```

---

## 5. Key Models (models.py)

```python
class Anchor(BaseModel):
    name: str                          # e.g. "Theory_Relativity"
    anchor_type: AnchorType = CONCEPT  # 9 canonical types
    namespace: Optional[str]           # e.g. "Physics"

class Modifier(BaseModel):
    # 30+ optional fields organized by category:
    # Temporal:   time, duration, frequency, tense
    # Spatial:    location, domain, scope
    # Logical:    confidence, certainty, necessity, rule
    # Provenance: source, author, timestamp, version
    # Affective:  emotion, intensity, valence
    # Value:      value, alignment, priority
    # Causal:     cause, effect, strength, conditionality
    # Cognitive:  intent, focus, perspective
    # Mood:       mood, modality
    custom: Dict[str, Any] = {}        # arbitrary user-defined fields

class Statement(BaseModel):
    source: Anchor
    target: Anchor
    arrow: str = "->"
    modifiers: Optional[Modifier]
    path_type: Optional[PathType]
    line: Optional[int]
    column: Optional[int]

class ParseResult(BaseModel):
    statements: List[Statement]
    errors: List[ParseError]
    warnings: List[ParseWarning]
    is_valid: bool
    metadata: Dict[str, Any]
```

---

## 6. Error Code Ranges

| Range | Domain | Module |
|-------|--------|--------|
| E001–E099 | Parse errors | parser.py |
| E100–E199 | Validation errors | validator.py |
| E200–E299 | Serialization errors | serializer.py |
| E300–E399 | Graph errors | graph.py |
| E400–E449 | File I/O errors | parser.py |
| E450–E499 | Query errors | query.py |
| E500–E599 | Builder errors | builder.py |
| E600–E699 | Schema errors | schema.py |
| E700–E799 | LLM errors | llm.py |
| E800–E899 | Emitter errors | emitter.py |
| E900–E949 | Decay errors | decay.py |
| E950–E959 | Diff/Patch errors | diff.py |
| E960–E969 | Reader errors | reader.py |
| W001–W099 | Warnings | validator.py |

---

## 7. Quick Start Examples

### Parse STL text
```python
from stl_parser import parse
result = parse('[Theory_Relativity] -> [Prediction_TimeDilation] ::mod(confidence=0.99)')
stmt = result.statements[0]
print(stmt.source.name)  # "Theory_Relativity"
```

### Build STL programmatically
```python
from stl_parser import stl, stl_doc
stmt = stl("[A]", "[B]").mod(confidence=0.9, rule="causal").build()
doc = stl_doc(stl("[A]", "[B]").mod(confidence=0.9), stl("[C]", "[D]"))
```

### Clean LLM output
```python
from stl_parser import validate_llm_output
result = validate_llm_output("```stl\nA => B mod(confience=1.5)\n```")
print(f"Valid: {result.is_valid}, Repairs: {len(result.repairs)}")
```

### Validate against schema
```python
from stl_parser import load_schema, validate_against_schema, parse
schema = load_schema('schema Events v1.0 { modifier { required: [confidence] } }')
result = parse('[A] -> [B] ::mod(confidence=0.9)')
validation = validate_against_schema(result, schema)
```

### Emit events
```python
from stl_parser import STLEmitter
with STLEmitter(log_path="events.stl", namespace="Events") as emitter:
    emitter.emit("[Start]", "[Running]", confidence=0.95, rule="causal")
```

### Sanitize anchor names
```python
from stl_parser import sanitize_anchor_name
sanitize_anchor_name("stl-parser")     # → "stl_parser"
sanitize_anchor_name("src/core.py")    # → "src_core_py"
sanitize_anchor_name("黄帝内经")        # → "黄帝内经"
```

### Query and filter statements
```python
from stl_parser import parse, find, find_all, filter_statements, select, stl_pointer

result = parse(stl_text)
stmt = result.find(source="Theory_X", confidence__gt=0.8)       # first match
stmts = result.find_all(rule="causal")                          # all matches
filtered = result.filter(confidence__gte=0.8)                   # new ParseResult
names = result.select("source")                                 # ["A", "B", ...]
val = stl_pointer(result, "/0/modifiers/confidence")            # 0.95
first = result[0]                                               # by index
matches = result["Theory_X"]                                    # by source name
```

### Diff and patch documents
```python
from stl_parser import parse, stl_diff, stl_patch, diff_to_text

a = parse('[A] -> [B] ::mod(confidence=0.8)')
b = parse('[A] -> [B] ::mod(confidence=0.95)')
diff = stl_diff(a, b)
print(diff_to_text(diff))
# ~ [A] -> [B]
#     confidence: 0.8 -> 0.95
patched = stl_patch(a, diff)  # patched ≡ b
```

### Stream-parse STL files
```python
from stl_parser import stream_parse, STLReader

# Generator-based streaming (memory-efficient for large files)
for stmt in stream_parse("events.stl", where={"confidence__gt": 0.8}):
    print(stmt.source.name)

# Context manager with stats and tail mode
with STLReader("agent.stl", tail=True) as reader:
    for stmt in reader:
        process(stmt)
```

### Query-time confidence decay
```python
from stl_parser import parse, effective_confidence, decay_report, filter_by_confidence
result = parse('[A] -> [B] ::mod(confidence=0.9, timestamp="2026-01-12T00:00:00Z")')
eff = effective_confidence(result.statements[0], half_life_days=30)
report = decay_report(result)
fresh = filter_by_confidence(result, min_confidence=0.5)
```

---

## 8. STLC Workflow Reference

All 4 new modules were built following the **STLC Multi-AI Collaboration** workflow:

```
1. Requirements (docs/IMPLEMENTATION_PLAN_TOOLING_P1.md)
       ↓
2. STLC Semantic Design (docs/stlc/*.stlc.md)
       ↓
3. Review & Approve (wuko approval gate)
       ↓
4. Compile to Python (stl_parser/*.py + tests/)
       ↓
5. Verify (pytest — 530 pass, 88% coverage)
```

Each `.stlc.md` file is the **contract** for its corresponding `.py` module. Any future changes should update the STLC spec first.

---

## 9. Development Commands

```bash
cd parser

# Install
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v

# Coverage
python -m pytest tests/ -v --cov=stl_parser --cov-report=term

# CLI
stl validate input.stl
stl convert input.stl --to json
stl analyze input.stl
stl build "[Source]" "[Target]" --mod "confidence=0.9,rule=causal"
stl clean llm_output.txt --show-repairs
stl schema-validate input.stl --schema events.stl.schema
stl query input.stl --where "confidence__gt=0.8" --format table
stl query input.stl --select "source,confidence" --format json
stl query input.stl --pointer "/0/source/name"
stl query input.stl --where "rule=causal" --count
stl diff a.stl b.stl
stl diff a.stl b.stl --format json
stl diff a.stl b.stl --quiet
stl patch a.stl diff.json --output patched.stl
```

---

## 10. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02 | Initial release — parser, validator, serializer, graph, analyzer, CLI |
| 1.1.0 | 2026-02-11 | Priority 1 tooling — builder, schema, llm, emitter (4 new modules, 98 new tests) |
| 1.2.0 | 2026-02-11 | Priority 2 tooling — confidence decay module, CLI extensions (build, clean, schema-validate) |
| 1.3.0 | 2026-02-12 | Bug fixes — custom field serialization, emit() param collision, comment API, sanitize utility (22 new tests) |
| 1.4.0 | 2026-02-12 | P0 Query module — find, find_all, filter, select, stl_pointer + ParseResult convenience methods (67 new tests) |
| 1.5.0 | 2026-02-12 | P1 CLI Query — `stl query` command with --where, --select, --pointer, --format, --count, --limit (30 new tests) |
| 1.6.0 | 2026-02-13 | P2 Diff/Patch — `stl_diff`, `stl_patch`, `diff_to_text`, `diff_to_dict` + CLI `stl diff`/`stl patch` (40 new tests) |
| 1.7.0 | 2026-02-13 | P2 Streaming Reader — `stream_parse`, `STLReader` with tail mode, where filtering (37 new tests) |
| 1.7.0+ | 2026-02-14 | Schema Ecosystem — audited schema.py, fixed `re.fullmatch` bug, created 6 domain schemas (tcm, scientific, causal, historical, medical, legal) |

---

## 11. Development Roadmap

For the full roadmap with JSON ecosystem comparison, see [STL_TOOLING_FEATURES.md](STL_TOOLING_FEATURES.md) Section 八.

| Priority | Feature | Status | Reference |
|----------|---------|--------|-----------|
| **P0-a** | STL Pointer + Query API (`find`, `find_all`, `filter_statements`, `select`, `stl_pointer`, ParseResult methods) | **Done v1.4.0** | JSON Pointer RFC 6901 |
| **P0-b/c** | Query expression language (`stl_query(result, "source.name == 'X'")`) | Planned | JSONPath RFC 9535 |
| **P1** | CLI Query tool (`stl query`) | **Done v1.5.0** | jq |
| **P2** | STL Diff / Patch (`stl_diff`, `stl_patch`, `stl diff`, `stl patch`) | **Done v1.6.0** | JSON Patch RFC 6902, JSON Merge Patch RFC 7396 |
| **P2-b** | Streaming Reader (`stream_parse`, `STLReader`, tail mode) | **Done v1.7.0** | JSON Lines / ndjson |
| **—** | Schema Ecosystem (6 domain schemas + template) | **Done v1.7.0+** | JSON Schema Store |
| **P3** | IDE Support (VS Code extension, LSP, syntax highlighting) | Planned (low priority) | — |

---

**End of Index**
