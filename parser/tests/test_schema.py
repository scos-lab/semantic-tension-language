# -*- coding: utf-8 -*-
"""Tests for stl_parser.schema module."""

import pytest
from pydantic import BaseModel, Field
from typing import Optional

from stl_parser.schema import (
    load_schema,
    validate_against_schema,
    to_pydantic,
    from_pydantic,
    STLSchema,
    FieldConstraint,
    SchemaAnchorConstraint,
    SchemaModifierConstraint,
    SchemaConstraints,
    SchemaValidationResult,
    validate_against_profiles,
)
from stl_parser.builder import stl, stl_doc
from stl_parser.models import ParseResult, Statement, Anchor, Modifier
from stl_parser.errors import STLSchemaError
from stl_parser.errors import get_error_info


# ========================================
# SCHEMA TEXT FIXTURES
# ========================================

BASIC_SCHEMA = """
schema EventLog v1.0 {
  namespace "Events"

  anchor source {
    pattern: /Event_.+/
  }

  anchor target {
    namespace: optional
  }

  modifier {
    required: [confidence, rule]
    optional: [source, author, timestamp]

    confidence: float(0.5, 1.0)
    rule: enum("causal", "empirical", "logical")
  }

  constraints {
    min_statements: 1
    max_statements: 100
  }
}
"""

MINIMAL_SCHEMA = """
schema Minimal v1.0 {
  modifier {
    required: [confidence]
  }
}
"""

NAMESPACE_REQUIRED_SCHEMA = """
schema Strict v1.0 {
  anchor source {
    namespace: required("Physics")
  }
  anchor target {
    namespace: optional
  }
  modifier {
    required: [rule]
  }
}
"""


class TestLoadSchema:
    """Tests for load_schema()."""

    def test_parse_basic_schema(self):
        schema = load_schema(BASIC_SCHEMA)
        assert schema.name == "EventLog"
        assert schema.version == "v1.0"
        assert schema.namespace == "Events"

    def test_parse_modifier_constraints(self):
        schema = load_schema(BASIC_SCHEMA)
        assert "confidence" in schema.modifier.required_fields
        assert "rule" in schema.modifier.required_fields
        assert "source" in schema.modifier.optional_fields

    def test_parse_field_constraints(self):
        schema = load_schema(BASIC_SCHEMA)
        fc = schema.modifier.field_constraints["confidence"]
        assert fc.type == "float"
        assert fc.min_value == 0.5
        assert fc.max_value == 1.0

    def test_parse_enum_constraint(self):
        schema = load_schema(BASIC_SCHEMA)
        fc = schema.modifier.field_constraints["rule"]
        assert fc.type == "enum"
        assert "causal" in fc.enum_values
        assert "empirical" in fc.enum_values

    def test_parse_anchor_pattern(self):
        schema = load_schema(BASIC_SCHEMA)
        assert schema.source_anchor.pattern == "Event_.+"

    def test_parse_constraints(self):
        schema = load_schema(BASIC_SCHEMA)
        assert schema.constraints.min_statements == 1
        assert schema.constraints.max_statements == 100

    def test_parse_minimal_schema(self):
        schema = load_schema(MINIMAL_SCHEMA)
        assert schema.name == "Minimal"
        assert "confidence" in schema.modifier.required_fields

    def test_parse_namespace_required(self):
        schema = load_schema(NAMESPACE_REQUIRED_SCHEMA)
        assert schema.source_anchor.namespace_required == "Physics"
        assert schema.source_anchor.namespace_optional is False

    def test_invalid_schema_raises(self):
        with pytest.raises(STLSchemaError):
            load_schema("not a valid schema")

    @pytest.mark.parametrize(
        "schema_text",
        [
            "schema X v1.0 { unknown { } }",
            "schema X v1.0 { anchor source { unknown: optional } }",
            "schema X v1.0 { constraints { unknown: 1 } }",
            "schema X v1.0 { modifier { value: enmu } }",
        ],
    )
    def test_rejects_unknown_schema_declarations(self, schema_text):
        with pytest.raises(STLSchemaError) as exc_info:
            load_schema(schema_text)

        assert exc_info.value.code == "E602"

    def test_missing_schema_path_reports_file_error(self, tmp_path):
        missing = tmp_path / "missing.stl.schema"

        with pytest.raises(STLSchemaError) as exc_info:
            load_schema(str(missing))

        assert exc_info.value.code == "E400"

    @pytest.mark.parametrize("code", [f"E{number}" for number in range(604, 611)])
    def test_new_schema_error_codes_have_public_messages(self, code):
        assert get_error_info(code) is not None


class TestValidateAgainstSchema:
    """Tests for validate_against_schema()."""

    def test_valid_document(self):
        schema = load_schema(BASIC_SCHEMA)
        doc = stl_doc(
            stl("[Event_Flood]", "[Result_Damage]").mod(
                confidence=0.9, rule="causal"
            ),
        )
        result = validate_against_schema(doc, schema)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_missing_required_field(self):
        schema = load_schema(BASIC_SCHEMA)
        doc = stl_doc(
            stl("[Event_Flood]", "[Result_Damage]").no_validate().mod(
                confidence=0.9
                # Missing 'rule'
            ),
        )
        result = validate_against_schema(doc, schema)
        assert result.is_valid is False
        assert any("rule" in e.message for e in result.errors)

    def test_confidence_out_of_range(self):
        schema = load_schema(BASIC_SCHEMA)
        # Build with no_validate to bypass Pydantic range check
        stmt = Statement(
            source=Anchor(name="Event_X"),
            target=Anchor(name="Result_Y"),
            modifiers=Modifier(confidence=0.3, rule="causal"),
        )
        doc = ParseResult(statements=[stmt], is_valid=True)
        result = validate_against_schema(doc, schema)
        assert result.is_valid is False
        assert any("confidence" in e.message and "min" in e.message for e in result.errors)

    def test_enum_violation(self):
        schema = load_schema(BASIC_SCHEMA)
        stmt = Statement(
            source=Anchor(name="Event_X"),
            target=Anchor(name="Result_Y"),
            modifiers=Modifier(confidence=0.9, rule="invalid_rule"),
        )
        doc = ParseResult(statements=[stmt], is_valid=True)
        result = validate_against_schema(doc, schema)
        assert result.is_valid is False
        assert any("rule" in e.message and "not in" in e.message for e in result.errors)

    def test_anchor_pattern_mismatch(self):
        schema = load_schema(BASIC_SCHEMA)
        doc = stl_doc(
            stl("[BadName]", "[Result]").mod(confidence=0.9, rule="causal"),
        )
        result = validate_against_schema(doc, schema)
        assert result.is_valid is False
        assert any("pattern" in e.message for e in result.errors)

    def test_too_few_statements(self):
        schema = load_schema(BASIC_SCHEMA)
        doc = ParseResult(statements=[], is_valid=True)
        result = validate_against_schema(doc, schema)
        assert result.is_valid is False
        assert any("Too few" in e.message for e in result.errors)

    def test_namespace_required_violation(self):
        schema = load_schema(NAMESPACE_REQUIRED_SCHEMA)
        stmt = Statement(
            source=Anchor(name="Energy"),  # No namespace
            target=Anchor(name="Mass"),
            modifiers=Modifier(rule="logical"),
        )
        doc = ParseResult(statements=[stmt], is_valid=True)
        result = validate_against_schema(doc, schema)
        assert result.is_valid is False
        assert any("namespace" in e.message for e in result.errors)

    def test_namespace_required_valid(self):
        schema = load_schema(NAMESPACE_REQUIRED_SCHEMA)
        stmt = Statement(
            source=Anchor(name="Energy", namespace="Physics"),
            target=Anchor(name="Mass"),
            modifiers=Modifier(rule="logical"),
        )
        doc = ParseResult(statements=[stmt], is_valid=True)
        result = validate_against_schema(doc, schema)
        assert result.is_valid is True

    def test_no_modifiers_required_fields(self):
        schema = load_schema(MINIMAL_SCHEMA)
        stmt = Statement(
            source=Anchor(name="A"),
            target=Anchor(name="B"),
            # No modifiers at all
        )
        doc = ParseResult(statements=[stmt], is_valid=True)
        result = validate_against_schema(doc, schema)
        assert result.is_valid is False
        assert any("confidence" in e.message for e in result.errors)

    @pytest.mark.parametrize(
        ("field_type", "value"),
        [("boolean", "true"), ("datetime", "19/08/2026")],
    )
    def test_rejects_invalid_declared_primitive_type(self, field_type, value):
        schema = load_schema(f"""
        schema Primitive v1.0 {{
          modifier {{
            required: [value]
            value: {field_type}
          }}
        }}
        """)
        doc = ParseResult(statements=[Statement(
            source=Anchor(name="A"),
            target=Anchor(name="B"),
            modifiers=Modifier(custom={"value": value}),
        )])

        result = validate_against_schema(doc, schema)

        assert result.is_valid is False
        assert [error.code for error in result.errors] == ["E604"]

    @pytest.mark.parametrize(
        ("field_type", "value"),
        [("boolean", True), ("datetime", "2026-08-19T10:30:00Z")],
    )
    def test_accepts_valid_declared_primitive_type(self, field_type, value):
        schema = load_schema(f"""
        schema Primitive v1.0 {{
          modifier {{
            required: [value]
            value: {field_type}
          }}
        }}
        """)
        doc = ParseResult(statements=[Statement(
            source=Anchor(name="A"),
            target=Anchor(name="B"),
            modifiers=Modifier(custom={"value": value}),
        )])

        assert validate_against_schema(doc, schema).is_valid is True

    def test_enforces_max_chain_length(self):
        schema = load_schema("""
        schema ShortPaths v1.0 {
          modifier { required: [] }
          constraints { max_chain_length: 2 }
        }
        """)
        doc = ParseResult(statements=[
            Statement(source=Anchor(name="A"), target=Anchor(name="B")),
            Statement(source=Anchor(name="B"), target=Anchor(name="C")),
            Statement(source=Anchor(name="C"), target=Anchor(name="D")),
        ])

        result = validate_against_schema(doc, schema)

        assert result.is_valid is False
        assert any(error.code == "E608" for error in result.errors)

    def test_rejects_cycles_when_disallowed(self):
        schema = load_schema("""
        schema Acyclic v1.0 {
          modifier { required: [] }
          constraints { allow_cycles: false }
        }
        """)
        doc = ParseResult(statements=[
            Statement(source=Anchor(name="A"), target=Anchor(name="B")),
            Statement(source=Anchor(name="B"), target=Anchor(name="A")),
        ])

        result = validate_against_schema(doc, schema)

        assert result.is_valid is False
        assert any(error.code == "E609" for error in result.errors)

    @pytest.mark.parametrize(
        ("value", "expected_valid"),
        [(1, True), (1.0, False), (1.5, False), (True, False), ("1", False)],
    )
    def test_integer_fields_are_strict(self, value, expected_valid):
        schema = load_schema("""
        schema IntegerValue v1.0 {
          modifier {
            required: [count]
            count: integer(0, 10)
          }
        }
        """)
        document = ParseResult(statements=[Statement(
            source=Anchor(name="A"),
            target=Anchor(name="B"),
            modifiers=Modifier(custom={"count": value}),
        )])

        result = validate_against_schema(document, schema)

        assert result.is_valid is expected_valid
        if not expected_valid:
            assert any(error.code == "E604" for error in result.errors)


class TestValidateAgainstProfiles:
    SOFTWARE = """
    schema SoftwareCore v1.0 {
      anchor source { pattern: /Service_.+/ }
      anchor target { pattern: /(Service|Component)_.+/ }
      modifier {
        required: [relation]
        relation: enum("contains", "deploys_to")
      }
    }
    """
    DELIVERY = """
    schema SoftwareDelivery v1.0 {
      anchor source { pattern: /Deployment_.+/ }
      anchor target { pattern: /Deployment_.+/ }
      modifier {
        required: [relation]
        relation: enum("deploys_to")
      }
    }
    """

    def profiles(self):
        return {
            "Software": load_schema(self.SOFTWARE),
            "Delivery": load_schema(self.DELIVERY),
        }

    @staticmethod
    def with_constraints(schema_text, constraints):
        body, _ = schema_text.rsplit("}", 1)
        return load_schema(f"{body} constraints {{ {constraints} }} }}")

    def test_routes_by_namespace_and_accepts_cross_profile_target(self):
        doc = ParseResult(statements=[Statement(
            source=Anchor(name="Service_API", namespace="Software"),
            target=Anchor(name="Deployment_Production", namespace="Delivery"),
            modifiers=Modifier(custom={"relation": "deploys_to"}),
        )])

        result = validate_against_profiles(doc, self.profiles())

        assert result.is_valid is True
        assert result.schema_name == "CompositeProfiles"

    def test_routes_unnamespaced_source_by_unique_prefix(self):
        doc = ParseResult(statements=[Statement(
            source=Anchor(name="Service_API"),
            target=Anchor(name="Component_Auth"),
            modifiers=Modifier(custom={"relation": "contains"}),
        )])

        assert validate_against_profiles(doc, self.profiles()).is_valid is True

    def test_rejects_target_prefix_that_conflicts_with_its_namespace(self):
        doc = ParseResult(statements=[Statement(
            source=Anchor(name="Service_API", namespace="Software"),
            target=Anchor(name="Deployment_Production", namespace="Software"),
            modifiers=Modifier(custom={"relation": "deploys_to"}),
        )])

        result = validate_against_profiles(doc, self.profiles())

        assert result.is_valid is False
        assert any(error.code == "E606" for error in result.errors)

    def test_rejects_unknown_explicit_source_namespace(self):
        doc = ParseResult(statements=[Statement(
            source=Anchor(name="Service_API", namespace="Unknown"),
            target=Anchor(name="Component_Auth", namespace="Software"),
            modifiers=Modifier(custom={"relation": "contains"}),
        )])

        result = validate_against_profiles(doc, self.profiles())

        assert [error.code for error in result.errors] == ["E610"]

    @pytest.mark.parametrize("source_name", ["Mystery_Item", "Shared_Item"])
    def test_rejects_unknown_or_ambiguous_source_profile(self, source_name):
        profiles = self.profiles()
        if source_name == "Shared_Item":
            shared = """
            schema Shared v1.0 {
              anchor source { pattern: /Shared_.+/ }
              anchor target { pattern: /Shared_.+/ }
              modifier { required: [] }
            }
            """
            profiles["First"] = load_schema(shared)
            profiles["Second"] = load_schema(shared.replace("Shared v1.0", "SharedTwo v1.0"))
        doc = ParseResult(statements=[Statement(
            source=Anchor(name=source_name),
            target=Anchor(name="Service_API"),
        )])

        result = validate_against_profiles(doc, profiles)

        assert result.is_valid is False
        assert [error.code for error in result.errors] == ["E610"]

    @pytest.mark.parametrize(
        ("constraint", "statement_count"),
        [("min_statements: 2", 1), ("max_statements: 1", 2)],
    )
    def test_enforces_statement_counts_per_routed_profile(self, constraint, statement_count):
        software = self.with_constraints(self.SOFTWARE, constraint)
        statements = [
            Statement(
                source=Anchor(name=f"Service_API_{index}", namespace="Software"),
                target=Anchor(name="Component_Auth", namespace="Software"),
                modifiers=Modifier(custom={"relation": "contains"}),
            )
            for index in range(statement_count)
        ]

        result = validate_against_profiles(
            ParseResult(statements=statements),
            {"Software": software, "Delivery": load_schema(self.DELIVERY)},
        )

        assert result.is_valid is False
        assert any(error.code == "E605" for error in result.errors)

    def test_composite_uses_strictest_chain_limit(self):
        software = self.with_constraints(self.SOFTWARE, "max_chain_length: 3")
        delivery = self.with_constraints(self.DELIVERY, "max_chain_length: 2")
        statements = [
            Statement(
                source=Anchor(name=f"Service_{source}", namespace="Software"),
                target=Anchor(name=f"Service_{target}", namespace="Software"),
                modifiers=Modifier(custom={"relation": "contains"}),
            )
            for source, target in (("A", "B"), ("B", "C"), ("C", "D"))
        ]

        result = validate_against_profiles(
            ParseResult(statements=statements),
            {"Software": software, "Delivery": delivery},
        )

        assert any(error.code == "E608" for error in result.errors)

    def test_composite_rejects_cycles_if_any_profile_disallows_them(self):
        software = self.with_constraints(self.SOFTWARE, "allow_cycles: false")
        document = ParseResult(statements=[
            Statement(
                source=Anchor(name="Service_API", namespace="Software"),
                target=Anchor(name="Deployment_Prod", namespace="Delivery"),
                modifiers=Modifier(custom={"relation": "deploys_to"}),
            ),
            Statement(
                source=Anchor(name="Deployment_Prod", namespace="Delivery"),
                target=Anchor(name="Service_API", namespace="Software"),
                modifiers=Modifier(custom={"relation": "deploys_to"}),
            ),
        ])

        result = validate_against_profiles(
            document, {"Software": software, "Delivery": load_schema(self.DELIVERY)}
        )

        assert any(error.code == "E609" for error in result.errors)


class TestToPydantic:
    """Tests for to_pydantic()."""

    def test_generates_model(self):
        schema = load_schema(BASIC_SCHEMA)
        Model = to_pydantic(schema)
        assert issubclass(Model, BaseModel)
        assert Model.__name__ == "EventLogModifier"

    def test_required_fields(self):
        schema = load_schema(BASIC_SCHEMA)
        Model = to_pydantic(schema)
        # Required fields should not have defaults
        assert Model.model_fields["confidence"].is_required()

    def test_field_validation(self):
        schema = load_schema(BASIC_SCHEMA)
        Model = to_pydantic(schema)
        # Valid instance
        instance = Model(confidence=0.9, rule="causal")
        assert instance.confidence == 0.9

    def test_field_range_validation(self):
        schema = load_schema(BASIC_SCHEMA)
        Model = to_pydantic(schema)
        with pytest.raises(Exception):
            # confidence below min 0.5
            Model(confidence=0.1, rule="causal")


class TestFromPydantic:
    """Tests for from_pydantic()."""

    def test_basic_extraction(self):
        class MyMod(BaseModel):
            confidence: float = Field(ge=0.0, le=1.0)
            rule: str

        schema = from_pydantic(MyMod, name="MySchema")
        assert schema.name == "MySchema"
        assert "confidence" in schema.modifier.required_fields
        assert "rule" in schema.modifier.required_fields

    def test_optional_fields(self):
        class MyMod(BaseModel):
            confidence: float = Field(ge=0.0, le=1.0)
            rule: Optional[str] = None

        schema = from_pydantic(MyMod, name="Test")
        assert "confidence" in schema.modifier.required_fields
        assert "rule" in schema.modifier.optional_fields

    def test_field_constraint_extraction(self):
        class MyMod(BaseModel):
            confidence: float = Field(ge=0.5, le=1.0)

        schema = from_pydantic(MyMod, name="Test")
        fc = schema.modifier.field_constraints.get("confidence")
        assert fc is not None
        assert fc.type == "float"
