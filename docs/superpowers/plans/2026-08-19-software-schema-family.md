# Software Schema Family Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a validated five-schema STL family that models the full lifecycle of a small software project, including reusable legal governance and cross-profile relationships.

**Architecture:** Extend the existing schema validator with truthful primitive/document validation, then add a profile router that selects a source schema while permitting targets from any registered profile. Add four focused software schemas, widen the general legal schema to v1.1, and prove the family with one end-to-end example and focused tests.

**Tech Stack:** Python 3.9+, Pydantic 2, NetworkX, pytest, STL `.stl.schema` files, Markdown

**Spec:** `docs/superpowers/specs/2026-08-19-software-schema-family-design.md`

## Global Constraints

- Keep existing public APIs backward compatible.
- Do not add dependencies; use Python standard-library datetime parsing and existing NetworkX.
- Keep unknown custom modifiers permitted.
- Treat `optional` fields as documented but not required.
- Use canonical namespaces `Software`, `Delivery`, `Operations`, `Assurance`, and `Law` without claiming single-schema namespace enforcement.
- Do not implement external-standard import/export, schema inheritance, automatic repository extraction, or a legal-rule engine.

---

### Task 1: Correct schema primitive and document validation

**Files:**
- Modify: `parser/stl_parser/errors.py`
- Modify: `parser/stl_parser/schema.py`
- Test: `parser/tests/test_schema.py`

**Interfaces:**
- Consumes: existing `validate_against_schema(parse_result: ParseResult, schema: STLSchema) -> SchemaValidationResult`
- Produces: validation codes `E604` through `E609`; enforced boolean, datetime, chain-length, and cycle constraints

- [ ] **Step 1: Write failing tests for boolean and datetime validation**

Add tests that load a schema with `enabled: boolean` and `observed_at: datetime`, create custom modifier values through `Modifier(custom=...)`, and assert invalid strings return `E604` while `True` and `2026-08-19T10:30:00Z` pass.

- [ ] **Step 2: Run the primitive tests and verify failure**

Run: `python -m pytest tests/test_schema.py -k "boolean or datetime" -v`

Expected: invalid values pass because these branches are not implemented.

- [ ] **Step 3: Implement exact primitive validation**

In `schema.py`, add `_is_iso8601(value: Any) -> bool` using `datetime.fromisoformat(value.replace("Z", "+00:00"))`. In `_validate_modifier_constraint`, reject non-`bool` boolean values and datetime values that are not ISO 8601 strings. Do not accept integers as booleans.

- [ ] **Step 4: Write failing chain and cycle tests**

Add a three-edge document for `max_chain_length: 2` and a two-edge `A -> B -> A` document for `allow_cycles: false`. Assert `E608` and `E609`, respectively.

- [ ] **Step 5: Implement document constraints**

Build a directed NetworkX graph from fully qualified anchor IDs. Use `nx.is_directed_acyclic_graph` for cycle rejection and `nx.dag_longest_path_length` for maximum edge count when acyclic. If cycles are allowed, skip longest-path enforcement because longest simple-path computation is intentionally out of scope.

- [ ] **Step 6: Assign distinct errors**

Add enum members and messages for `E604_SCHEMA_TYPE`, `E605_SCHEMA_DOCUMENT_COUNT`, `E606_SCHEMA_ANCHOR`, `E607_SCHEMA_REQUIRED_FIELD`, `E608_SCHEMA_CHAIN_LENGTH`, and `E609_SCHEMA_CYCLE`. Replace generic codes in their corresponding branches while retaining `E603` for range/enum constraint violations.

- [ ] **Step 7: Run focused and full schema tests**

Run: `python -m pytest tests/test_schema.py -v`

Expected: all schema tests pass.

- [ ] **Step 8: Commit**

```bash
git add parser/stl_parser/errors.py parser/stl_parser/schema.py parser/tests/test_schema.py
git commit -m "fix: enforce declared schema constraints"
```

### Task 2: Add composite profile validation

**Files:**
- Modify: `parser/stl_parser/schema.py`
- Modify: `parser/stl_parser/__init__.py`
- Test: `parser/tests/test_schema.py`

**Interfaces:**
- Consumes: `Dict[str, STLSchema]`, existing private anchor/modifier validators
- Produces: `validate_against_profiles(parse_result: ParseResult, profiles: Dict[str, STLSchema]) -> SchemaValidationResult`

- [ ] **Step 1: Write failing routing tests**

Create in-memory `Software` and `Delivery` schemas. Test namespace routing, prefix fallback for an unnamespaced `Service_API`, a valid cross-profile `Service_API -> Deployment_Prod` target, and ambiguous/unknown `Mystery_Item` failure with `E610`.

- [ ] **Step 2: Run the routing tests and verify import failure**

Run: `python -m pytest tests/test_schema.py -k profiles -v`

Expected: FAIL because `validate_against_profiles` is absent.

- [ ] **Step 3: Implement routing helpers**

Add `_anchor_id(anchor)`, `_matches_anchor(anchor, constraint)`, and `_select_profile(anchor, profiles)`. Selection order is exact namespace key, then exactly one matching source pattern; zero or multiple matches return a routing error.

- [ ] **Step 4: Implement profile validation**

For each statement, validate source and modifiers against its selected profile. Accept the target if it matches at least one registered target constraint. Aggregate errors in one `SchemaValidationResult` with `schema_name="CompositeProfiles"` and comma-separated schema versions.

- [ ] **Step 5: Export the API**

Import `validate_against_profiles` from `.schema` in `parser/stl_parser/__init__.py` and add it to `__all__`.

- [ ] **Step 6: Run profile and regression tests**

Run: `python -m pytest tests/test_schema.py -v`

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add parser/stl_parser/schema.py parser/stl_parser/__init__.py parser/tests/test_schema.py
git commit -m "feat: validate STL documents against schema profiles"
```

### Task 3: Add the software schema family and legal v1.1

**Files:**
- Create: `docs/schemas/software-core.stl.schema`
- Create: `docs/schemas/software-delivery.stl.schema`
- Create: `docs/schemas/software-operations.stl.schema`
- Create: `docs/schemas/software-assurance.stl.schema`
- Modify: `docs/schemas/legal.stl.schema`
- Create: `parser/tests/test_software_schemas.py`

**Interfaces:**
- Consumes: `load_schema`, `validate_against_schema`, `validate_against_profiles`
- Produces: five loadable profiles with required `relation` modifier and profile-specific relation enums

- [ ] **Step 1: Write schema contract tests**

Parameterize all five paths and assert they load. For each software profile, test one valid statement, one invalid prefix, one missing `relation`, and one invalid relation. Assert legal reports version `v1.1`, accepts `Contract_`, `License_`, and `Policy_`, and accepts confidence `0.4` when source/rule are present.

- [ ] **Step 2: Run tests and verify missing-schema failures**

Run: `python -m pytest tests/test_software_schemas.py -v`

Expected: four missing files and legal v1.0 assertions fail.

- [ ] **Step 3: Add the four software schemas**

Encode the exact anchor prefixes and relation lists from the design. Use a union of relevant cross-profile prefixes in target patterns. Require `relation`, define it as an enum, define used numeric/string fields, and set `min_statements: 1`, `max_statements: 1000`.

- [ ] **Step 4: Extend legal additively**

Change the version to `v1.1`, widen source/target patterns with the approved legal prefixes, lower confidence minimum to `0.0`, and add the approved optional modifier constraints without removing existing fields or enum values.

- [ ] **Step 5: Run schema contracts**

Run: `python -m pytest tests/test_software_schemas.py -v`

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add docs/schemas parser/tests/test_software_schemas.py
git commit -m "feat: add software lifecycle schema family"
```

### Task 4: Add end-to-end example and schema guide

**Files:**
- Create: `docs/schemas/examples/small-software-project.stl`
- Create: `docs/schemas/software.md`
- Modify: `docs/schemas/README.md`
- Modify: `docs/reference/api/schema.md`
- Test: `parser/tests/test_software_schemas.py`

**Interfaces:**
- Consumes: the five schema files and `validate_against_profiles`
- Produces: a parseable, composite-valid example and user-facing selection/mapping guidance

- [ ] **Step 1: Write the failing end-to-end test**

Load the example with `parse_file`, load all five profiles, call `validate_against_profiles`, and assert parsing and validation are both valid. Also assert the example contains every canonical namespace.

- [ ] **Step 2: Run the example test and verify file-not-found failure**

Run: `python -m pytest tests/test_software_schemas.py -k end_to_end -v`

Expected: FAIL because the example does not exist.

- [ ] **Step 3: Write the example**

Include complete paths for requirement-to-deployment, deployment-to-incident, legal-to-control-to-evidence, and package-to-license/vulnerability. Every statement has a permitted relation and required legal provenance.

- [ ] **Step 4: Write documentation**

Document schema selection, canonical namespaces, anchor and relation tables, cross-profile validation, single-schema compatibility, external-standard mappings, and explicit enforcement limits. Update the schema index and clarify that `_template.stl.schema` is not counted as a domain schema.

- [ ] **Step 5: Run documentation example tests**

Run: `python -m pytest tests/test_software_schemas.py -v`

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add docs/schemas docs/reference/api/schema.md parser/tests/test_software_schemas.py
git commit -m "docs: add software schema guide and example"
```

### Task 5: Full verification and fork delivery

**Files:**
- Modify only files needed to correct failures caused by Tasks 1–4

**Interfaces:**
- Consumes: complete implementation
- Produces: clean test run and pushed fork branch

- [ ] **Step 1: Install the package test environment**

Run: `python -m pip install -e ".[dev]"`

Expected: editable install succeeds without new dependencies.

- [ ] **Step 2: Run the full suite**

Run: `python -m pytest -q`

Expected: all existing and new tests pass.

- [ ] **Step 3: Run repository consistency checks**

Run: `git diff --check` and `git status --short`

Expected: no whitespace errors; only intended committed changes.

- [ ] **Step 4: Review the commit range**

Run: `git log --oneline upstream/main..HEAD` and `git diff --stat upstream/main...HEAD`

Expected: design, validator, profiles, schemas, and documentation commits only.

- [ ] **Step 5: Push the fork**

Run: `git push origin main`

Expected: `origin/main` contains the verified implementation.
