# STL Tooling Priority 2 — Completion Report

> **Version:** 1.2.0
> **Date:** 2026-02-11
> **Author:** Syn-claude
> **Status:** Complete

---

## 1. Deliverables Summary

| Deliverable | Status | Files |
|-------------|--------|-------|
| STLC Spec: Decay | Done | `docs/stlc/stl_decay_v1.0.0.stlc.md` |
| STLC Spec: CLI Extensions | Done | `docs/stlc/stl_cli_ext_v1.0.0.stlc.md` |
| Confidence Decay module | Done | `stl_parser/decay.py` (106 LOC) |
| Decay tests | Done | `tests/test_decay.py` (25 tests, 98% coverage) |
| CLI extensions (3 commands) | Done | `stl_parser/cli.py` (~130 LOC added) |
| CLI tests | Done | `tests/test_cli.py` (9 new tests) |
| Error codes (E900-E999) | Done | `stl_parser/errors.py` |
| Exports + version bump | Done | `stl_parser/__init__.py` → v1.2.0 |
| Documentation updates | Done | `PROJECT_INDEX.md`, `STL_TOOLING_FEATURES.md` |

---

## 2. New Module: `decay.py`

### Purpose
Query-time confidence decay — compute effective confidence based on statement age using exponential half-life decay. **Read-only: never modifies original Statement data.**

### Formula
```
effective = confidence × 0.5^(age_days / half_life_days)
```

### Data Models

| Model | Fields |
|-------|--------|
| `DecayConfig` | `half_life_days` (default 30), `min_threshold` (default 0.01), `reference_time` |
| `DecayedStatement` | `statement`, `original_confidence`, `effective_confidence`, `age_days`, `decay_ratio` |
| `DecayReport` | `decayed_statements[]`, `config`, `total_statements`, `statements_with_timestamp`, `statements_decayed`, `summary{}` |

### Public API

| Function | Signature | Purpose |
|----------|-----------|---------|
| `effective_confidence` | `(statement, half_life_days=30, reference_time=None) -> Optional[float]` | Single statement decay |
| `decay_report` | `(parse_result, config=None) -> DecayReport` | Batch analysis with statistics |
| `filter_by_confidence` | `(parse_result, min_confidence=0.5, ...) -> ParseResult` | Filter by effective confidence |

### Edge Cases Handled
- No timestamp → return original confidence (no decay)
- No confidence → return None
- Future timestamp → return original (no decay)
- Malformed timestamp → graceful degradation, return original
- Very old statement → decays close to zero
- half_life_days <= 0 → raises `STLDecayError`

---

## 3. CLI Extensions

### New Commands

| Command | Purpose |
|---------|---------|
| `stl build <source> <target> [--mod MOD] [--output FILE]` | Construct STL statement from CLI arguments |
| `stl clean <file> [--schema FILE] [--show-repairs] [--output FILE]` | Clean and repair LLM-generated STL |
| `stl schema-validate <file> --schema <schema_file>` | Validate STL file against schema definition |

### Helper Added
`_parse_mod_string(mod_string)` — parses `"confidence=0.9,rule=causal"` into `{"confidence": 0.9, "rule": "causal"}` with auto-typing (float, int, bool, string).

---

## 4. Test Results

```
334 passed, 0 failed, 1 skipped
```

### New Tests Added: 34

| Test File | Tests Added | Tests Total |
|-----------|-------------|-------------|
| `test_decay.py` | 25 (new file) | 25 |
| `test_cli.py` | 9 (added) + 1 fix | 20 |

### Coverage

| Module | Coverage |
|--------|----------|
| `decay.py` | 98% |
| `cli.py` | 67% |
| **Overall** | **87%** |

---

## 5. Error Codes Added

| Code | Name | Meaning |
|------|------|---------|
| E900 | `E900_DECAY_ERROR` | General decay calculation error |
| E901 | `E901_INVALID_DECAY_TIMESTAMP` | Timestamp can't be parsed for decay |

Exception class: `STLDecayError(STLError)`

---

## 6. Workflow Followed

```
1. STLC Specifications (2 docs)
       ↓
   wuko approval ("开始执行")
       ↓
2. Compile decay.py + test_decay.py
       ↓  pytest: 25/25 pass
3. Extend cli.py + test_cli.py
       ↓  pytest: 334/334 pass (full suite)
4. Update __init__.py + docs
       ↓  version → 1.2.0
```

---

## 7. Files Modified/Created

| File | Action |
|------|--------|
| `parser/stl_parser/decay.py` | **CREATED** |
| `parser/stl_parser/errors.py` | **MODIFIED** — E900-E901, STLDecayError |
| `parser/stl_parser/cli.py` | **MODIFIED** — 3 commands + helper + imports |
| `parser/stl_parser/__init__.py` | **MODIFIED** — decay exports, v1.2.0 |
| `parser/tests/test_decay.py` | **CREATED** |
| `parser/tests/test_cli.py` | **MODIFIED** — 9 new tests + 1 fix |
| `docs/stlc/stl_decay_v1.0.0.stlc.md` | **CREATED** |
| `docs/stlc/stl_cli_ext_v1.0.0.stlc.md` | **CREATED** |
| `docs/PROJECT_INDEX.md` | **MODIFIED** |
| `docs/STL_TOOLING_FEATURES.md` | **MODIFIED** |
| `docs/COMPLETION_REPORT_TOOLING_P2.md` | **CREATED** (this file) |

---

## 8. Version History

| Version | Milestone |
|---------|-----------|
| 1.0.0 | Core parser, validator, serializer, graph, analyzer, CLI |
| 1.1.0 | P1 tooling — builder, schema, llm, emitter (4 modules, 98 tests) |
| **1.2.0** | **P2 tooling — confidence decay, CLI extensions (1 module, 3 commands, 34 new tests)** |
