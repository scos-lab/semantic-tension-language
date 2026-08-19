from pathlib import Path

import pytest

from stl_parser import (
    Anchor,
    Modifier,
    ParseResult,
    Statement,
    load_schema,
    parse_file,
    validate_against_schema,
    validate_against_profiles,
)


SCHEMA_DIR = Path(__file__).parents[2] / "docs" / "schemas"


PROFILE_CASES = [
    (
        "software-core.stl.schema",
        "Service_API",
        "Component_Auth",
        "contains",
    ),
    (
        "software-delivery.stl.schema",
        "Build_42",
        "Artifact_API",
        "produces",
    ),
    (
        "software-operations.stl.schema",
        "Metric_Latency",
        "Service_API",
        "observes",
    ),
    (
        "software-assurance.stl.schema",
        "Control_Encryption",
        "DataStore_Customers",
        "protects",
    ),
]


def statement(source, target, relation=None):
    custom = {} if relation is None else {"relation": relation}
    return Statement(
        source=Anchor(name=source),
        target=Anchor(name=target),
        modifiers=Modifier(custom=custom),
    )


@pytest.mark.parametrize(("filename", "source", "target", "relation"), PROFILE_CASES)
def test_software_profile_accepts_its_contract(filename, source, target, relation):
    schema = load_schema(str(SCHEMA_DIR / filename))

    result = validate_against_schema(
        ParseResult(statements=[statement(source, target, relation)]), schema
    )

    assert result.is_valid is True


@pytest.mark.parametrize(("filename", "source", "target", "relation"), PROFILE_CASES)
def test_software_profile_rejects_missing_relation(filename, source, target, relation):
    schema = load_schema(str(SCHEMA_DIR / filename))

    result = validate_against_schema(
        ParseResult(statements=[statement(source, target)]), schema
    )

    assert result.is_valid is False
    assert any(error.code == "E607" for error in result.errors)


@pytest.mark.parametrize(("filename", "source", "target", "relation"), PROFILE_CASES)
def test_software_profile_rejects_unknown_relation(filename, source, target, relation):
    schema = load_schema(str(SCHEMA_DIR / filename))

    result = validate_against_schema(
        ParseResult(statements=[statement(source, target, "unknown")]), schema
    )

    assert result.is_valid is False
    assert any(error.code == "E603" for error in result.errors)


@pytest.mark.parametrize(("filename", "source", "target", "relation"), PROFILE_CASES)
def test_software_profile_rejects_unknown_source_prefix(filename, source, target, relation):
    schema = load_schema(str(SCHEMA_DIR / filename))

    result = validate_against_schema(
        ParseResult(statements=[statement("Unknown_Thing", target, relation)]), schema
    )

    assert result.is_valid is False
    assert any(error.code == "E606" for error in result.errors)


def test_legal_v1_1_supports_software_governance_concepts():
    schema = load_schema(str(SCHEMA_DIR / "legal.stl.schema"))
    statements = [
        Statement(
            source=Anchor(name=source),
            target=Anchor(name="Obligation_Compliance"),
            modifiers=Modifier(
                confidence=0.4,
                rule="logical",
                source="https://example.test/authority",
            ),
        )
        for source in ("Contract_Terms", "License_Apache", "Policy_Privacy")
    ]

    result = validate_against_schema(ParseResult(statements=statements), schema)

    assert schema.version == "v1.1"
    assert result.is_valid is True


def test_small_project_example_validates_across_all_profiles():
    example = SCHEMA_DIR / "examples" / "small-software-project.stl"
    document = parse_file(str(example))
    profiles = {
        "Software": load_schema(str(SCHEMA_DIR / "software-core.stl.schema")),
        "Delivery": load_schema(str(SCHEMA_DIR / "software-delivery.stl.schema")),
        "Operations": load_schema(str(SCHEMA_DIR / "software-operations.stl.schema")),
        "Assurance": load_schema(str(SCHEMA_DIR / "software-assurance.stl.schema")),
        "Law": load_schema(str(SCHEMA_DIR / "legal.stl.schema")),
    }

    result = validate_against_profiles(document, profiles)

    assert document.is_valid is True
    assert result.is_valid is True, [error.message for error in result.errors]
    assert {statement.source.namespace for statement in document.statements} == set(profiles)
