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
)
from stl_parser.builder import stl, stl_doc
from stl_parser.models import ParseResult, Statement, Anchor, Modifier
from stl_parser.errors import STLSchemaError


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
