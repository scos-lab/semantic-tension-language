# Schema Engine Hardening Design

**Date:** 2026-08-20

**Status:** Approved for implementation

## Goal

Make STL schemas fail closed, validate composite documents completely, express typed relationships and reusable profile bundles, preserve constraints through Pydantic conversion, and align software identifiers with established standards.

## Parser and primitive correctness

Schema parsing will reject unknown top-level blocks, anchor keys, constraint keys, and field types with `E602`. Supported modifier field types remain `float`, `integer`, `string`, `enum`, `datetime`, and `boolean`. Integer validation will accept only Python integers other than booleans. Missing path-like schema inputs will raise a clear `E400` file-not-found error rather than being parsed as schema text.

## Composite constraints

`validate_against_profiles()` will group statements by their selected source profile. Each profile's minimum and maximum statement counts apply to that routed subset. Graph constraints apply to the complete composite document using the strictest registered settings: cycles are rejected if any profile sets `allow_cycles: false`, and the smallest declared `max_chain_length` is enforced.

## Typed edge rules

The schema grammar gains repeatable edge blocks:

```text
edge {
    source: [Service, Component]
    relation: [contains, calls]
    target: [Component, Endpoint]
}
```

Entries refer to anchor prefix types without the trailing underscore. When edge rules exist, every statement must match at least one source/relation/target triple. Schemas without edge blocks retain current behavior.

## Profile manifests

A `.stl.profile` manifest declares a named, versioned bundle:

```text
profile SmallSoftwareProject v1.0 {
    include: [software-core, software-delivery, software-operations,
              software-assurance, legal]
}
```

`load_profile(path)` resolves included schemas relative to the manifest directory and returns a `Dict[str, STLSchema]` keyed by each schema's namespace. Duplicate or missing namespaces and missing schema files are errors. This is a local composition format; remote resolution and inheritance remain out of scope.

## Standards identifiers

The software schemas add optional, typed string fields for `purl`, `spdx_id`, `license_expression`, `cve`, `cwe`, `operation_id`, `commit`, `slsa_provenance`, `service_name`, `sarif_rule`, and `artifact_uri`. Regex constraints provide basic structural validation without attempting full external-standard parsing.

## Pydantic fidelity and versioning

`to_pydantic()` maps enum constraints to `Literal`, datetime to `datetime`, integer to strict `int`, and string patterns to Pydantic pattern constraints. `from_pydantic()` recognizes Literal enums and datetime annotations. Package runtime version comes from `importlib.metadata`, with the project version as fallback for source-only execution.

## Additional correctness and quality

Import `re` in the analyzer to fix the reachable `NameError`. Clean Ruff findings in files touched by this work, migrate Ruff configuration to `[tool.ruff.lint]`, and document the remaining repository-wide lint baseline rather than performing unrelated mass formatting.

## Success criteria

- Invalid schema keywords and types fail to load.
- Strict integer cases behave correctly.
- Composite statement and graph constraints are enforced.
- Typed edge rules reject invalid triples while preserving old schemas.
- A manifest loads and validates the five software profiles.
- Identifier patterns accept representative valid values and reject malformed ones.
- Pydantic conversion preserves enums, datetime, patterns, and strict integers.
- Runtime and package versions agree.
- Missing schema paths return a file error.
- Analyzer inference no longer raises `NameError`.
- All tests pass; touched files pass Ruff; documentation matches behavior.

## Out of scope

- Remote schema registries
- Full SPDX, CycloneDX, OpenAPI, OpenTelemetry, SLSA, or SARIF import/export
- Arbitrary schema inheritance
- General logical expressions beyond typed edge triples
- Repository-wide reformatting
