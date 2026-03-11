# STL — Semantic Tension Language

> **Mission:** Replace JSON as the standard interchange format for AI-to-AI and AI-to-program communication.
> STL is a calculable, universal standard for structuring knowledge through directional semantic relations — traceable, verifiable, inference-ready, and token-efficient.

---

## Project Overview

| Item | Value |
|------|-------|
| **Package** | `stl-parser` v1.7.0 |
| **Python** | >=3.9 |
| **License** | Apache 2.0 (code), CC BY 4.0 (spec) |
| **Repo** | `https://github.com/scos-lab/semantic-tension-language` |
| **Source** | 19 modules, ~8,300 LOC |
| **Tests** | 23 test files, ~530 tests, 88% coverage |
| **Docs** | 54 files, ~13,500 lines |

---

## Repository Structure

```
semantic-tension-language/
├── spec/                          # Language specifications
│   ├── stl-core-spec-v1.0.md         # Core syntax spec
│   ├── stl-core-spec-v1.0-supplement.md  # Extended spec (anchors, modifiers, validation)
│   └── STLC_COMPILER_INTERFACE_PROTOCOL.md
├── parser/                        # Python package (stl-parser)
│   ├── stl_parser/                    # Source modules (see Module Map below)
│   ├── tests/                         # pytest suite (23 files)
│   ├── pyproject.toml                 # Package config + tool settings
│   ├── requirements.txt               # Runtime deps
│   └── requirements-dev.txt           # Dev deps
├── docs/                          # Documentation library
│   ├── getting-started/               # installation, quickstart, key-concepts
│   ├── tutorials/                     # 8 step-by-step tutorials (01-parsing ~ 08-cli-tools)
│   ├── reference/api/                 # 12 API module docs
│   ├── reference/                     # cli.md, modifiers.md, anchor-types.md, stl-syntax.md, error-codes.md
│   ├── guides/                        # 5 how-to guides
│   ├── schemas/                       # 6 domain schemas + template
│   ├── stlc/                          # 10 STLC semantic specifications
│   ├── PROJECT_INDEX.md               # Architecture overview
│   └── STL_AS_LLM_PROGRAM_BRIDGE.md  # Vision document
├── README.md
├── LICENSE
└── .claude/CLAUDE.md              # This file
```

---

## Module Map (`parser/stl_parser/`)

### Core
| Module | Purpose |
|--------|---------|
| `parser.py` | Lark-based STL parser → `parse(text)`, `parse_file(path)` |
| `grammar.py` | Lark EBNF grammar definition |
| `models.py` | Pydantic v2 models: `Anchor`, `Modifier`, `Statement`, `ParseResult` |
| `errors.py` | Error codes (E001-E969) + exception hierarchy |
| `_utils.py` | Shared utilities (multiline merge, sanitize, etc.) |
| `validator.py` | Syntax / semantic / provenance validation |
| `serializer.py` | Export: JSON, RDF (Turtle/XML/N-Triples/JSON-LD), STL |

### Tooling
| Module | Purpose |
|--------|---------|
| `builder.py` | Fluent API: `stl("[A]", "[B]").mod(confidence=0.9).build()` |
| `schema.py` | `.stl.schema` format — load, validate documents against domain schemas |
| `llm.py` | LLM output pipeline: `clean()` → `repair()` → `validate_llm_output()` |
| `emitter.py` | Thread-safe event writer: `STLEmitter(path, namespace)` |
| `reader.py` | Streaming reader: `stream_parse()`, `STLReader` with tail mode |
| `query.py` | Django-style query: `find()`, `find_all()`, `filter_statements()`, `select()`, `stl_pointer()` |
| `diff.py` | Semantic diff/patch: `stl_diff()`, `stl_patch()`, `diff_to_text()` |
| `decay.py` | Time-based confidence decay: `effective_confidence()`, `decay_report()` |

### Analysis & CLI
| Module | Purpose |
|--------|---------|
| `graph.py` | NetworkX graph: cycles, centrality, paths |
| `analyzer.py` | Statistical analysis reports |
| `cli.py` | Typer CLI — 10 commands: validate, convert, query, diff, patch, analyze, build, clean, schema-validate |

---

## STL Syntax Quick Reference

```stl
# Basic form
[Source] -> [Target] ::mod(key=value, key=value)

# With namespace
[Physics:Energy] -> [Physics:Mass] ::mod(rule="logical", confidence=0.99)

# Chained
[Theory] -> [Experiment] -> [Observation]

# Multi-modifier layers
[Action] -> [Result]
  ::mod(confidence=0.85, rule="causal")
  ::mod(source="doi:10.1234/ref", author="Smith")

# Unicode
[黄帝内经] -> [素问] ::mod(domain="TCM", confidence=0.95)
```

**Anchors:** `[Name]` or `[Namespace:Name]` — alphanumeric, `_`, `:`, Unicode. No spaces, no nesting, no special chars.

**Arrows:** `→` (Unicode) or `->` (ASCII)

**Modifiers:** `::mod(key=value, ...)` — strings quoted, numbers bare, floats 0.0–1.0.

**Key modifier categories:**
- Logical: `confidence`, `certainty`, `rule` (causal/logical/empirical/definitional)
- Provenance: `source`, `author`, `timestamp`, `version`
- Temporal: `time`, `duration`, `tense`
- Spatial: `location`, `domain`, `scope`
- Causal: `strength`, `conditionality`, `cause`, `effect`

---

## Development Commands

```bash
# Install (editable)
cd parser && pip install -e ".[dev]"

# Run tests
cd parser && pytest

# Run tests without coverage
cd parser && pytest --no-cov

# Run specific test
cd parser && pytest tests/test_parser.py -k "test_name"

# Lint
cd parser && ruff check stl_parser/

# Format
cd parser && black stl_parser/ tests/

# Type check
cd parser && mypy stl_parser/

# CLI usage
stl validate input.stl
stl convert input.stl --to json
stl query input.stl --where "confidence__gt=0.8"
stl diff a.stl b.stl
stl build "[A]" "[B]" --mod "confidence=0.9"
stl clean llm_output.txt
stl schema-validate input.stl --schema docs/schemas/scientific.stl.schema
```

---

## Key Technical Details

### Data Model Hierarchy
```
ParseResult
  └── statements: List[Statement]
        ├── source: Anchor (name, namespace?, type?)
        ├── target: Anchor
        ├── arrow: str ("→" or "->")
        └── modifiers: List[Modifier]
              ├── standard fields (confidence, rule, time, source, ...)
              └── custom dict (anything non-standard)
```

### Dependencies
- **lark** — Parser generator (EBNF grammar)
- **pydantic v2** — Data validation and models
- **rdflib** — RDF serialization
- **networkx** — Graph analysis
- **typer + rich** — CLI

### Error Code Ranges
| Range | Category |
|-------|----------|
| E001-E099 | Parse errors |
| E100-E199 | Validation errors |
| E200-E299 | Serialization errors |
| E300-E399 | Graph errors |
| E400-E449 | File I/O errors |
| E450-E499 | Query errors |
| E500-E599 | Builder errors |
| E600-E699 | Schema errors |
| E700-E799 | LLM pipeline errors |
| E800-E899 | Emitter errors |
| E900-E949 | Decay errors |
| E950-E959 | Diff/Patch errors |
| E960-E969 | Reader errors |
| W001-W099 | Warnings |

### Domain Schemas (in `docs/schemas/`)
`tcm.stl.schema` | `medical.stl.schema` | `legal.stl.schema` | `scientific.stl.schema` | `historical.stl.schema` | `causal.stl.schema`

---

## Conventions

- **Code style:** Black (line-length=100), Ruff, mypy strict
- **Test naming:** `test_<module>.py` with `Test*` classes and `test_*` functions
- **Error handling:** Use `STLError` / `STLParseError` with `ErrorCode` enums
- **Modifier validation vs transport:** Validate known fields strictly, serialize ALL faithfully (including custom)
- **Builder vs Parser custom fields:** Parser stores custom as Pydantic extra fields (`getattr()`); Builder stores in `custom` dict
- **Schema `namespace` field:** Top-level is metadata only — use anchor block `namespace: required(...)` for enforcement
- **Builder datetime:** `time="Past"` (enum) rejected as invalid; use ISO dates or `.no_validate()`

---

## Architecture Decisions

1. **Lark grammar** for parsing — not regex, not hand-rolled (except schema parser which uses recursive descent for simplicity)
2. **Pydantic v2** for all data models — strict validation, JSON serialization built in
3. **LLM pipeline is 3-stage:** clean (normalize) → repair (fix common errors) → parse (strict). Each stage tracked via `RepairAction`
4. **Query uses Django-style operators:** `confidence__gt=0.8`, `source__contains="doi"`, `rule__in=causal|logical`
5. **Diff identity key:** `(source.ns, source.name, target.ns, target.name, arrow)` — same key = MODIFY, different = ADD/REMOVE
6. **STLEmitter** is thread-safe (threading.Lock), params are `source_anchor`/`target_anchor` (not `source`/`target` to avoid collision)
7. **STLReader tail mode:** polling-based (`time.sleep`), file position tracking via `readline()`, portable across OSes

---

## Why STL Over JSON

| Dimension | JSON | STL |
|-----------|------|-----|
| **Semantic direction** | None (key-value is flat) | Built-in: `[A] → [B]` is directional |
| **Provenance** | Manual field conventions | Native: `::mod(source=..., author=..., timestamp=...)` |
| **Confidence** | Not expressible | Native: `::mod(confidence=0.85)` |
| **Inference** | Requires external schema | Graph-native: cycle detection, path finding, centrality |
| **Token efficiency** | Verbose (braces, quotes, colons) | Compact: fewer tokens per semantic unit |
| **Traceability** | None | Every statement carries verifiable metadata |
| **LLM-friendly** | LLMs often produce malformed JSON | STL has built-in repair pipeline for LLM output |
