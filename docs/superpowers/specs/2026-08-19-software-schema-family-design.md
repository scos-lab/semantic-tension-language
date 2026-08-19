# STL Software Schema Family Design

**Date:** 2026-08-19

**Status:** Approved design, pending implementation-plan review

**Audience:** STL maintainers, schema authors, and AI agents describing small software projects

## 1. Purpose

Add a compact family of STL schemas that can describe the complete lifecycle of a small software project without turning one schema into an enterprise-scale ontology. The family covers product intent, architecture, delivery, operations, assurance, and the legal rules that govern software.

The implementation must remain useful with the current `.stl.schema` validator while defining a clear path to validating one STL document against several profiles.

## 2. Design principles

1. **Small core, explicit profiles.** Common software structure belongs in a core schema; lifecycle-specific concepts belong in focused profiles.
2. **Directional, named relationships.** STL edges describe a specific action or dependency through a required `relation` modifier.
3. **Typed anchors by prefix.** Until the schema engine supports first-class anchor types, prefixes such as `Service_`, `Test_`, and `Incident_` provide type information.
4. **Cross-profile references are valid.** A deployment may target a core service; a legal rule may govern a data store.
5. **Standards alignment, not duplication.** The vocabulary maps to C4, SPDX/CycloneDX, OpenAPI, OpenTelemetry, and SARIF concepts but does not reproduce those standards.
6. **Traceability over ceremony.** `source` is required where a claim needs evidence; routine structural edges do not require artificial confidence scores.
7. **Backward-compatible legal evolution.** The existing legal schema is widened additively in v1.1 rather than replaced with a software-only legal model.

## 3. Alternatives considered

### One monolithic software schema

Simple to select, but its anchor and modifier enumerations would grow quickly and unrelated concerns would be coupled. Rejected because small documents would inherit unnecessary vocabulary and constraints.

### Independent lifecycle schemas

Works with the current validator, but provides no shared vocabulary and weakens cross-lifecycle reasoning. Rejected as the long-term model, retained as the compatibility behavior when profile validation is not used.

### Core plus profiles — selected

A stable core carries project and architecture concepts. Delivery, operations, assurance, and legal schemas add focused vocabulary. A profile validator applies the relevant schema to each statement and supports cross-profile edges.

## 4. Schema family

### 4.1 `software-core.stl.schema`

Describes intent, ownership, architecture, source structure, data, and interfaces.

Anchor prefixes:

- `Project_`, `Requirement_`, `Decision_`
- `Person_`, `Team_`
- `System_`, `Service_`, `Component_`, `Module_`
- `API_`, `Endpoint_`, `DataStore_`, `Data_`
- `Package_`, `SourceFile_`

Relations:

- `owns`, `requires`, `implements`, `contains`
- `depends_on`, `calls`, `exposes`
- `reads`, `writes`, `documents`, `supersedes`

Required modifiers: `relation`. Optional modifiers: `confidence`, `source`, `description`, `technology`, `protocol`, `version`, `status`, `criticality`, `author`, `timestamp`.

### 4.2 `software-delivery.stl.schema`

Describes verification and the path from source to a running release.

Anchor prefixes:

- Core prefixes needed for cross-profile statements
- `Test_`, `TestSuite_`, `Pipeline_`, `Build_`
- `Artifact_`, `Release_`, `Environment_`, `Deployment_`

Relations:

- `tests`, `triggers`, `builds`, `produces`
- `packages`, `releases`, `deploys`, `deploys_to`
- `promotes_to`, `verifies`, `rolls_back`

Required modifiers: `relation`. Optional modifiers: `status`, `version`, `commit`, `source`, `timestamp`, `environment`, `tool`, `description`.

### 4.3 `software-operations.stl.schema`

Describes running software, observation, reliability, and incident response.

Anchor prefixes:

- Cross-profile `System_`, `Service_`, `Component_`, `Environment_`, and `Deployment_`
- `Instance_`, `Metric_`, `Log_`, `Trace_`, `Alert_`
- `SLO_`, `Runbook_`, `Incident_`, `Remediation_`

Relations:

- `runs_as`, `runs_on`, `observes`, `measures`
- `emits`, `monitors`, `triggers`, `violates`
- `causes`, `affects`, `mitigates`, `resolves`

Required modifiers: `relation`. Optional modifiers: `severity`, `status`, `value`, `unit`, `threshold`, `environment`, `source`, `time`, `timestamp`, `description`.

### 4.4 `software-assurance.stl.schema`

Describes security, privacy, quality, supply-chain provenance, licenses, controls, and compliance evidence.

Anchor prefixes:

- Cross-profile software and delivery anchors
- `Threat_`, `Risk_`, `Finding_`, `Vulnerability_`
- `Control_`, `Evidence_`, `License_`, `SBOM_`, `Attestation_`
- `ProcessingActivity_`, `DataCategory_`, `ComplianceRequirement_`

Relations:

- `threatens`, `affects`, `detects`, `reports`
- `mitigates`, `protects`, `satisfies`, `violates`
- `licensed_under`, `contains`, `derived_from`, `attests`
- `processes`, `stores`, `transfers`, `retains`

Required modifiers: `relation`. Optional modifiers: `severity`, `likelihood`, `impact`, `status`, `source`, `identifier`, `version`, `timestamp`, `description`.

### 4.5 `legal.stl.schema` v1.1

Keep the existing legal schema general-purpose and add concepts needed for software governance.

New source and target prefixes:

- `Contract_`, `License_`, `Policy_`, `Standard_`
- `Consent_`, `Authority_`, `Permission_`, `Prohibition_`
- `Exception_`, `Jurisdiction_`, `LegalInterpretation_`

New optional modifiers:

- `relation`, `jurisdiction`, `authority`, `status`
- `effective_date`, `expiry_date`, `citation`, `applicability`

The existing `confidence`, `rule`, and `source` requirements remain for compatibility. The confidence minimum is widened from 0.7 to 0.0 so contested interpretations can be represented honestly. The schema guide will distinguish authoritative text from interpretation and recommend high confidence only for accurately cited authoritative statements.

Legal-to-software edges use legal anchors as sources and software or assurance anchors as targets. Because the current legal schema cannot express external target types, such mixed edges are validated by the profile validator rather than by `legal.stl.schema` alone.

## 5. Namespaces and statement routing

Canonical namespaces are:

- `Software`
- `Delivery`
- `Operations`
- `Assurance`
- `Law`

The current schema `namespace` declaration is metadata unless an anchor block explicitly requires a namespace. The new schemas will use prefix patterns for compatibility and document canonical namespaces as a strong recommendation, not silently claim that the current validator enforces them.

The profile validator will route statements using the source namespace. If the source namespace is absent, it will infer a profile from the source anchor prefix. A target may belong to any registered profile. Unknown or ambiguous prefixes produce an error rather than being guessed.

## 6. Composite profile validation

Add a minimal API alongside existing single-schema validation:

```python
validate_against_profiles(parse_result, profiles)
```

`profiles` maps namespace/profile names to loaded `STLSchema` objects. For each statement, the validator:

1. Selects the source profile by namespace or anchor prefix.
2. Validates the source anchor and modifiers using that profile.
3. Accepts a target that matches any registered profile's target pattern.
4. Returns the existing `SchemaValidationResult` shape with profile context in messages.

This first version does not introduce schema inheritance, a new grammar, or cross-document resolution. Those are separate future enhancements.

## 7. Examples and documentation

Add one guide explaining selection, namespaces, anchor types, relations, and mappings to external standards. Add a small-project example that traces:

```text
requirement → component → endpoint → test → build → deployment
deployment → metric → alert → incident → remediation
law/policy → compliance requirement → control → software asset → evidence
package → license/vulnerability → risk/control
```

The example must parse and pass composite-profile validation.

Update the schema ecosystem index so domain-schema counts exclude `_template.stl.schema` and list the new family consistently.

## 8. Validator corrections required by this work

Implement only corrections directly needed for truthful schema behavior:

- Validate `boolean` fields as booleans.
- Validate `datetime` fields as ISO 8601 strings.
- Enforce `max_chain_length` and `allow_cycles`, or remove claims that they are enforced. The selected implementation is enforcement.
- Give distinct validation codes to document count, anchor, required-field, type/range, chain-length, cycle, and profile-routing failures.
- Keep `optional` as documentation: optional means permitted but not required.
- Do not reject unknown custom modifiers in this iteration; closed modifier sets require an explicit future grammar feature.

## 9. Error handling

Schema parsing continues to fail fast with `STLSchemaError`. Document validation accumulates independent errors so users can correct a document in one pass. Profile routing failures identify the statement index, source anchor, and known profiles. Cross-profile targets are checked against all registered target patterns and report the accepted prefixes when invalid.

No automatic repair occurs during schema validation. LLM cleanup and repair remain separate existing responsibilities.

## 10. Testing and success criteria

The work is complete when:

1. Every new or changed schema loads successfully.
2. Positive and negative fixtures cover every schema's anchor prefixes, required fields, enums, and numeric ranges.
3. A complete small-project example parses and passes profile validation.
4. Invalid or ambiguous profile routing fails with a specific error.
5. Cross-profile legal-to-software and assurance-to-core edges validate.
6. Boolean, datetime, chain-length, and cycle tests demonstrate the corrected behavior.
7. Existing parser tests remain green.
8. Documentation accurately distinguishes enforced constraints from conventions.

## 11. Standards mapping

- C4 supplies the hierarchy of system, service/container, component, and code-level elements.
- OpenAPI supplies API, endpoint, operation, protocol, and interface concepts.
- SPDX and CycloneDX supply package, artifact, SBOM, license, provenance, vulnerability, and attestation concepts.
- OpenTelemetry supplies service, instance, environment, metric, log, trace, and operational identity concepts.
- SARIF supplies finding, rule identifier, severity, evidence location, and remediation concepts.

The STL schemas provide a compact relationship layer and references to those artifacts. They are not replacement serialization formats for the external standards.

## 12. Out of scope

- Full import/export for SPDX, CycloneDX, OpenAPI, OpenTelemetry, or SARIF
- A universal enterprise architecture ontology
- Automated extraction from source repositories
- Jurisdiction-specific legal advice or legal-rule engines
- Schema inheritance or arbitrary composition syntax
- Enforcing closed modifier sets
- Visual diagram generation

## 13. Delivery sequence

1. Correct and test schema-validator behavior required by the design.
2. Add composite profile validation and tests.
3. Add the four software schemas and legal v1.1 extension.
4. Add the guide and end-to-end example.
5. Update indexes and run the full test suite.
