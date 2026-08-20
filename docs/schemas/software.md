# Software Schema Family

The software schema family models a small project's complete lifecycle without forcing every statement through one large vocabulary.

## Choose a profile

| Profile | Namespace | Use for |
|---|---|---|
| `software-core` | `Software` | Requirements, ownership, architecture, source, data, and APIs |
| `software-delivery` | `Delivery` | Tests, pipelines, builds, artifacts, releases, and deployments |
| `software-operations` | `Operations` | Runtime instances, telemetry, SLOs, alerts, incidents, and remediation |
| `software-assurance` | `Assurance` | Security, privacy, supply chain, licenses, controls, and evidence |
| `legal` | `Law` | Laws, regulations, contracts, policies, legal duties, and interpretations |

Use one profile with `validate_against_schema()` for a focused document. Use `software.stl.profile` with `validate_against_profiles()` when statements cross lifecycle boundaries.

## Naming

Anchors use a type prefix and stable name:

```stl
[Software:Service_API]
[Delivery:Build_42]
[Operations:Incident_42]
[Assurance:Control_Encryption]
[Law:Regulation_DataProtection]
```

Namespaces are canonical routing keys during composite validation. The `namespace` declaration inside a schema remains metadata during single-schema validation unless an anchor block explicitly declares `namespace: required(...)`.

## Relationships

Every software-profile statement requires a `relation` modifier. Use the profile that owns the source anchor.

```stl
[Software:Service_API] -> [Software:Component_Auth]
  ::mod(relation="contains")

[Delivery:Test_Login] -> [Software:Endpoint_Login]
  ::mod(relation="tests", status="passing")

[Operations:Metric_Latency] -> [Software:Service_API]
  ::mod(relation="observes", unit="ms")

[Assurance:Control_Encryption] -> [Software:DataStore_Customers]
  ::mod(relation="protects")
```

The permitted relations are declared in each `.stl.schema` file. Unknown custom modifiers remain allowed by STL; declared fields receive type, range, and enum validation.

## Composite validation

```python
from stl_parser import parse_file, load_profile, validate_against_profiles

document = parse_file("docs/schemas/examples/small-software-project.stl")
profiles = load_profile("docs/schemas/software.stl.profile")

result = validate_against_profiles(document, profiles)
```

Routing uses the source namespace first. For an unnamespaced source, exactly one source-prefix pattern must match. Missing or ambiguous matches produce `E610`. A target may match the target pattern of any registered profile, which permits legal-to-software and assurance-to-delivery edges.

Software profiles declare typed `edge` rules; an unlisted source-prefix, relation, and target-prefix triple produces `E611`. Statement counts apply per routed profile, while cycle policy and the strictest chain limit apply to the complete graph. Optional interoperable fields cover Package URLs, SPDX/license expressions, CVE/CWE, OpenAPI operation IDs, Git commits, SLSA provenance, service names, SARIF rules, and artifact URIs.

## Legal and software governance

The legal schema remains general-purpose. Version 1.1 adds contracts, licenses, policies, standards, consent, permissions, prohibitions, exceptions, jurisdictions, and interpretations. It also adds legal status and effective-date metadata.

Authoritative text and legal interpretation are different claims. Keep `source` and `confidence` explicit; a lower confidence value is valid for contested interpretations.

```stl
[Law:Regulation_DataProtection] -> [Assurance:ComplianceRequirement_EncryptData]
  ::mod(
    relation="governs",
    rule="logical",
    confidence=0.95,
    source="https://example.test/law/data-protection",
    jurisdiction="EU"
  )
```

This vocabulary documents governance relationships; it is not a legal-advice or legal-rule engine.

## Standards mapping

| STL concepts | Related standard |
|---|---|
| System, service, component, module | C4 architecture abstractions |
| API, endpoint, protocol | OpenAPI |
| Package, SBOM, license, vulnerability, attestation | SPDX and CycloneDX |
| Instance, metric, log, trace, alert | OpenTelemetry semantic conventions |
| Finding, identifier, severity, remediation | SARIF |

STL provides compact relationships and references to external artifacts. It does not replace their native serialization formats.

## Enforcement boundaries

The validator enforces anchor patterns, required modifiers, declared field types and ranges, statement counts, acyclic constraints, and maximum chain length. Optional fields are documentation, not requirements. Composite validation does not implement schema inheritance, cross-document resolution, or closed custom-modifier sets.

See [`examples/small-software-project.stl`](examples/small-software-project.stl) for a complete lifecycle graph.
