# Schema Engine Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden STL schema validation and add typed edges, reusable profile manifests, standards identifiers, and faithful Pydantic conversion.

**Architecture:** Extend the existing recursive-descent schema parser with fail-closed grammar constructs and edge rules. Keep composite profile loading and validation in `schema.py`, preserving existing public APIs while adding `load_profile()` and richer constraints.

**Tech Stack:** Python 3.9+, Pydantic 2, NetworkX, pytest, Ruff

**Spec:** `docs/superpowers/specs/2026-08-20-schema-engine-hardening-design.md`

## Global Constraints

- Preserve existing schema and parser behavior unless the previous behavior silently accepted invalid declarations.
- Add no third-party dependencies.
- Use TDD for every behavior change.
- Touch only schema, analyzer, package metadata/export, software schemas, their tests, and corresponding documentation/configuration.

---

### Task 1: Fail-closed parsing and strict primitives

**Files:** `parser/stl_parser/schema.py`, `parser/stl_parser/errors.py`, `parser/tests/test_schema.py`

**Interfaces:** Preserve `load_schema()` and `validate_against_schema()`; produce strict schema parse errors and integer behavior.

- [ ] Add failing tests for unknown top-level keys, anchor keys, constraint keys, field types, missing schema paths, and integer values `1`, `1.0`, `1.5`, `True`, and `"1"`.
- [ ] Run focused tests and confirm failures are caused by permissive behavior.
- [ ] Implement strict parser branches, path detection, and separate float/integer validation.
- [ ] Run `python -m pytest tests/test_schema.py -q` and commit.

### Task 2: Composite document constraints

**Files:** `parser/stl_parser/schema.py`, `parser/tests/test_schema.py`

**Interfaces:** `validate_against_profiles(ParseResult, Dict[str, STLSchema]) -> SchemaValidationResult` applies routed count constraints and merged graph constraints.

- [ ] Add failing tests for per-profile minimum/maximum counts, strictest maximum chain, and cycle rejection.
- [ ] Implement routed subsets and merged graph constraints without changing single-schema validation.
- [ ] Run schema tests and commit.

### Task 3: Typed edge rules

**Files:** `parser/stl_parser/schema.py`, `parser/tests/test_schema.py`, `docs/schemas/software-*.stl.schema`

**Interfaces:** Add `SchemaEdgeRule`; parse repeatable `edge` blocks; validate source prefix, relation, and target prefix triples.

- [ ] Add failing parse and validation tests for valid and invalid triples and backward compatibility.
- [ ] Implement the grammar, model, and validation helper.
- [ ] Add representative edge rules to all four software schemas.
- [ ] Run schema and software-schema tests and commit.

### Task 4: Declarative profile manifests

**Files:** `parser/stl_parser/schema.py`, `parser/stl_parser/__init__.py`, `parser/tests/test_software_schemas.py`, `docs/schemas/software.stl.profile`

**Interfaces:** Add `load_profile(source: str) -> Dict[str, STLSchema]` and export it.

- [ ] Add failing tests for valid loading, missing include, duplicate namespace, and end-to-end validation.
- [ ] Implement strict manifest parsing and relative schema resolution.
- [ ] Add the software-family manifest and switch the example test/documentation to it.
- [ ] Run focused tests and commit.

### Task 5: Standards identifiers and Pydantic fidelity

**Files:** `docs/schemas/software-*.stl.schema`, `parser/stl_parser/schema.py`, `parser/tests/test_schema.py`, `parser/tests/test_software_schemas.py`

**Interfaces:** Preserve schema field patterns through validation and Pydantic conversion; add optional standard identifier fields.

- [ ] Add failing tests for representative identifiers, Literal enums, datetime values, string patterns, strict integer models, and reverse conversion.
- [ ] Implement schema string-pattern parsing, faithful Python types, and reverse mapping.
- [ ] Add identifier constraints to the appropriate software schemas.
- [ ] Run focused tests and commit.

### Task 6: Version, analyzer, lint, and documentation

**Files:** `parser/stl_parser/__init__.py`, `parser/stl_parser/analyzer.py`, `parser/pyproject.toml`, relevant tests and schema documentation.

**Interfaces:** Runtime version matches installed metadata; analyzer inference is callable; touched files pass Ruff.

- [ ] Add failing version and analyzer regression tests.
- [ ] Implement metadata version loading and the missing analyzer import.
- [ ] Migrate Ruff configuration and clean only touched files.
- [ ] Update schema/API/software documentation for strict parsing, typed edges, manifests, identifiers, and composite constraints.
- [ ] Run the full test suite, touched-file Ruff checks, `git diff --check`, and commit.

### Task 7: Delivery

**Files:** No new behavior.

- [ ] Review the full diff against the design and correct any uncovered issue with a failing test.
- [ ] Run the complete suite and static checks fresh.
- [ ] Merge into `main`, rerun tests, remove the worktree, and push the fork.
