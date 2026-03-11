# -*- coding: utf-8 -*-
"""
Test suite for validator.py

Tests the validation logic of the STL parser.
"""

import pytest
from datetime import datetime

from stl_parser.validator import (
    validate_anchor,
    validate_rule_type, validate_datetime_format,
    validate_necessity, validate_conditionality, validate_modifier,
    infer_anchor_type, infer_path_type, check_semantic_consistency,
    check_warnings, validate_statement, validate_parse_result, is_valid_statement,
    STLValidator
)
from stl_parser.models import (
    Anchor, AnchorType, PathType,
    Modifier, Statement, ParseResult,
    ParseError, ParseWarning
)
from pydantic import ValidationError
from stl_parser.errors import STLValidationError, STLWarning, ErrorCode, WarningCode


# Fixtures for common objects
@pytest.fixture
def minimal_statement():
    return Statement(source=Anchor(name="SourceAnchor"), target=Anchor(name="TargetAnchor"))

@pytest.fixture
def statement_with_modifier():
    return Statement(
        source=Anchor(name="Source"),
        target=Anchor(name="Target"),
        modifiers=Modifier(confidence=0.8, rule="causal")
    )

@pytest.fixture
def parse_result_with_statements(minimal_statement, statement_with_modifier):
    return ParseResult(statements=[minimal_statement, statement_with_modifier], is_valid=True)

@pytest.fixture
def parse_result_empty():
    return ParseResult(statements=[], is_valid=True)


class TestPydanticModelValidation:
    """Tests for direct Pydantic model validation (Anchor, Modifier)"""

    def test_anchor_name_empty_raises_validation_error(self):
        with pytest.raises(ValidationError) as excinfo:
            Anchor(name="")
        assert "Anchor name cannot be empty" in str(excinfo.value)

    def test_anchor_name_reserved_raises_validation_error(self):
        with pytest.raises(ValidationError) as excinfo:
            Anchor(name="NULL")
        assert "Anchor name 'NULL' is reserved" in str(excinfo.value)

    def test_anchor_name_invalid_pattern_raises_validation_error(self):
        with pytest.raises(ValidationError) as excinfo:
            Anchor(name="Invalid Name!")
        assert "Anchor name 'Invalid Name!' must be alphanumeric + underscore" in str(excinfo.value)

    def test_anchor_name_too_long_raises_validation_error(self):
        long_name = "A" * 65
        with pytest.raises(ValidationError) as excinfo:
            Anchor(name=long_name)
        assert "Anchor name too long: 65 > 64 characters" in str(excinfo.value)

    def test_anchor_namespace_invalid_pattern_raises_validation_error(self):
        with pytest.raises(ValidationError) as excinfo:
            Anchor(name="Name", namespace="Domain-Invalid")
        assert "Invalid namespace format: Domain-Invalid" in str(excinfo.value)
    
    def test_anchor_invalid_type_raises_validation_error(self):
        with pytest.raises(ValidationError) as excinfo:
            Anchor(name="Test", type="NON_EXISTENT_TYPE")
        assert "Input should be 'Concept', 'Relational', 'Event', 'Entity', 'Name', 'Agent', 'Question', 'Verifier' or 'PathSegment'" in str(excinfo.value)

    def test_modifier_confidence_out_of_range_raises_validation_error(self):
        with pytest.raises(ValidationError) as excinfo:
            Modifier(confidence=1.1)
        assert "Input should be less than or equal to 1" in str(excinfo.value)

        with pytest.raises(ValidationError) as excinfo:
            Modifier(confidence=-0.1)
        assert "Input should be greater than or equal to 0" in str(excinfo.value)

    def test_modifier_certainty_out_of_range_raises_validation_error(self):
        with pytest.raises(ValidationError) as excinfo:
            Modifier(certainty=1.1)
        assert "Input should be less than or equal to 1" in str(excinfo.value)

    def test_modifier_strength_out_of_range_raises_validation_error(self):
        with pytest.raises(ValidationError) as excinfo:
            Modifier(strength=1.1)
        assert "Input should be less than or equal to 1" in str(excinfo.value)

    def test_modifier_intensity_out_of_range_raises_validation_error(self):
        with pytest.raises(ValidationError) as excinfo:
            Modifier(intensity=1.1)
        assert "Input should be less than or equal to 1" in str(excinfo.value)

    def test_modifier_all_valid_fields(self):
        modifier = Modifier(
            confidence=0.9,
            certainty=0.8,
            strength=0.7,
            intensity=0.6,
        )
        assert modifier.confidence == 0.9
        assert modifier.certainty == 0.8
        assert modifier.strength == 0.7
        assert modifier.intensity == 0.6


class TestAnchorValidation:
    """Tests for anchor validation functions still in validator.py."""
    
    def test_validate_anchor_complete_valid(self):
        anchor = Anchor(name="Valid", namespace="Test.Domain", type=AnchorType.CONCEPT)
        errors = validate_anchor(anchor)
        assert not errors

    def test_validate_anchor_invalid_type_logic(self):
        # Pydantic catches invalid enum values on init, but we test the logic if type were somehow invalid
        # We construct an Anchor without validation to test the validator function
        anchor = Anchor.model_construct(name="Test", type="INVALID")
        errors = validate_anchor(anchor)
        assert len(errors) == 1
        assert errors[0].code == ErrorCode.E108_INVALID_ANCHOR_TYPE


class TestModifierValidation:
    """Tests for modifier validation functions that are still in validator.py."""

    def test_validate_rule_type_valid(self):
        errors = validate_rule_type("causal")
        assert not errors
        errors = validate_rule_type("definitional")
        assert not errors

    def test_validate_rule_type_invalid(self):
        errors = validate_rule_type("non_existent_rule")
        assert len(errors) == 1
        assert errors[0].code == ErrorCode.E107_INVALID_RULE_TYPE

    @pytest.mark.parametrize("dt_string, is_valid", [
        ("2025-01-01", True),
        ("2025-01-01T10:30:00Z", True),
        ("2025-01-01T10:30:00+01:00", True),
        ("2025-01-01T10:30:00-05:00", True),
        ("2025/01/01", False), # Invalid format
        ("2025-1-1", False), # Invalid format
        ("2025-02-30", False), # Invalid date value
        ("2025-01-01T25:00:00Z", False), # Invalid time
    ])
    def test_validate_datetime_format(self, dt_string, is_valid):
        errors = validate_datetime_format(dt_string)
        if is_valid:
            assert not errors
        else:
            assert len(errors) == 1
            assert errors[0].code == ErrorCode.E112_INVALID_DATETIME_FORMAT

    def test_validate_necessity_valid(self):
        errors = validate_necessity("Necessary")
        assert not errors
        errors = validate_necessity("Possible")
        assert not errors

    def test_validate_necessity_invalid(self):
        errors = validate_necessity("Optional")
        assert len(errors) == 1
        assert errors[0].code == ErrorCode.E105_INVALID_MODIFIER_VALUE

    def test_validate_conditionality_valid(self):
        errors = validate_conditionality("Sufficient")
        assert not errors
        errors = validate_conditionality("Both")
        assert not errors

    def test_validate_conditionality_invalid(self):
        errors = validate_conditionality("Maybe")
        assert len(errors) == 1
        assert errors[0].code == ErrorCode.E105_INVALID_MODIFIER_VALUE

    def test_validate_modifier_all_fields(self):
        # Only testing fields that are still validated by validate_modifier
        modifier = Modifier(
            rule="logical",
            time="2025-01-01",
            necessity="Contingent",
            conditionality="Necessary",
            timestamp="2025-01-01T12:00:00Z"
        )
        errors = validate_modifier(modifier, "test_context")
        assert not errors

    def test_validate_modifier_invalid_rule_and_datetime(self):
        modifier = Modifier(rule="bad_rule", time="2025/01/01")
        errors = validate_modifier(modifier)
        assert len(errors) == 2
        assert errors[0].code == ErrorCode.E107_INVALID_RULE_TYPE
        assert errors[1].code == ErrorCode.E112_INVALID_DATETIME_FORMAT


class TestSemanticValidation:
    """Tests for semantic validation functions."""

    def test_infer_anchor_type_event(self):
        anchor = Anchor(name="MeetingEvent")
        assert infer_anchor_type(anchor) == AnchorType.EVENT
        anchor = Anchor(name="ActionPublish")
        assert infer_anchor_type(anchor) == AnchorType.EVENT

    def test_infer_anchor_type_agent(self):
        anchor = Anchor(name="ResearcherAgent")
        assert infer_anchor_type(anchor) == AnchorType.AGENT

    def test_infer_anchor_type_question(self):
        # Anchor name must be valid by Pydantic
        anchor = Anchor(name="WhyQuestion")
        assert infer_anchor_type(anchor) == AnchorType.QUESTION

    def test_infer_anchor_type_name(self):
        anchor = Anchor(name="London")
        assert infer_anchor_type(anchor) == AnchorType.NAME
        anchor = Anchor(name="AlbertEinstein")
        assert infer_anchor_type(anchor) == AnchorType.NAME

    def test_infer_anchor_type_relational(self):
        anchor = Anchor(name="RelationshipBetween")
        assert infer_anchor_type(anchor) == AnchorType.RELATIONAL

    def test_infer_anchor_type_concept_default(self):
        anchor = Anchor(name="freedom") # Lowercase to avoid being caught as NAME (proper noun)
        assert infer_anchor_type(anchor) == AnchorType.CONCEPT

    def test_infer_path_type_causal(self):
        statement = Statement(
            source=Anchor(name="A"), target=Anchor(name="B"),
            modifiers=Modifier(rule="causal")
        )
        assert infer_path_type(statement) == PathType.CAUSAL

    def test_infer_path_type_inferential(self):
        statement = Statement(
            source=Anchor(name="A"), target=Anchor(name="B"),
            modifiers=Modifier(rule="logical")
        )
        assert infer_path_type(statement) == PathType.INFERENTIAL

    def test_infer_path_type_semantic(self):
        statement = Statement(
            source=Anchor(name="A"), target=Anchor(name="B"),
            modifiers=Modifier(rule="definitional")
        )
        assert infer_path_type(statement) == PathType.SEMANTIC

    def test_infer_path_type_action(self):
        statement = Statement(
            source=Anchor(name="A"), target=Anchor(name="B"),
            modifiers=Modifier(intent="Publish")
        )
        assert infer_path_type(statement) == PathType.ACTION

    def test_infer_path_type_cognitive(self):
        statement = Statement(
            source=Anchor(name="A"), target=Anchor(name="B"),
            modifiers=Modifier(focus="Relationship")
        )
        assert infer_path_type(statement) == PathType.COGNITIVE

    def test_infer_path_type_none(self):
        statement = Statement(source=Anchor(name="AnchorA"), target=Anchor(name="AnchorB"))
        assert infer_path_type(statement) is None

        statement = Statement(source=Anchor(name="AnchorA"), target=Anchor(name="AnchorB"), modifiers=Modifier(source="test"))
        assert infer_path_type(statement) is None


    def test_check_semantic_consistency_causal_missing_modifiers(self):
        statement = Statement(
            source=Anchor(name="Rain"),
            target=Anchor(name="WetGround"),
            path_type=PathType.CAUSAL,
            modifiers=Modifier() # No causal modifiers
        )
        errors = check_semantic_consistency(statement)
        assert len(errors) == 1
        assert errors[0].code == ErrorCode.E113_SEMANTIC_INCONSISTENCY

    def test_check_semantic_consistency_conflicting_modifiers(self):
        statement = Statement(
            source=Anchor(name="A"),
            target=Anchor(name="B"),
            modifiers=Modifier(rule="empirical", necessity="Necessary")
        )
        errors = check_semantic_consistency(statement)
        assert len(errors) == 1
        assert errors[0].code == ErrorCode.E111_CONFLICTING_MODIFIERS

    def test_check_semantic_consistency_definitional_low_confidence(self):
        statement = Statement(
            source=Anchor(name="A"),
            target=Anchor(name="B"),
            modifiers=Modifier(rule="definitional", confidence=0.8) # This is a warning, not an error
        )
        errors = check_semantic_consistency(statement)
        assert not errors # No errors, just a potential warning not handled here


class TestWarningChecks:
    """Tests for warning generation functions."""

    def test_check_warnings_low_confidence(self):
        statement = Statement(
            source=Anchor(name="ValidSource"),
            target=Anchor(name="ValidTarget"),
            modifiers=Modifier(confidence=0.4)
        )
        warnings = check_warnings(statement)
        assert any(w.code == WarningCode.W003_LOW_CONFIDENCE for w in warnings)
        assert not any(w.code == WarningCode.W004_MISSING_MODIFIER for w in warnings) # Ensure only this warning
        assert not any(w.code == WarningCode.W002_UNUSUAL_ANCHOR_NAME for w in warnings) # Ensure only this warning

    def test_check_warnings_missing_modifier(self):
        statement = Statement(source=Anchor(name="ValidSource"), target=Anchor(name="ValidTarget"))
        warnings = check_warnings(statement)
        assert any(w.code == WarningCode.W004_MISSING_MODIFIER for w in warnings)
        assert not any(w.code == WarningCode.W002_UNUSUAL_ANCHOR_NAME for w in warnings) # Ensure only this warning

    def test_check_warnings_short_anchor_name(self):
        statement = Statement(source=Anchor(name="X"), target=Anchor(name="Y"))
        warnings = check_warnings(statement)
        assert any(w.code == WarningCode.W002_UNUSUAL_ANCHOR_NAME for w in warnings)
        short_name_warnings = [w for w in warnings if w.code == WarningCode.W002_UNUSUAL_ANCHOR_NAME]
        assert len(short_name_warnings) == 2

    def test_check_warnings_anchor_name_many_digits(self):
        statement = Statement(source=Anchor(name="Event12345"), target=Anchor(name="Outcome"))
        warnings = check_warnings(statement)
        assert any(w.code == WarningCode.W002_UNUSUAL_ANCHOR_NAME for w in warnings)
        many_digits_warnings = [w for w in warnings if w.code == WarningCode.W002_UNUSUAL_ANCHOR_NAME and "many digits" in w.message]
        assert len(many_digits_warnings) == 1


class TestStatementValidation:
    """Tests for validate_statement function."""

    def test_validate_statement_valid(self, statement_with_modifier):
        errors, warnings = validate_statement(statement_with_modifier)
        assert not errors
        assert not warnings # Assuming no warnings for this fixture

    def test_validate_statement_with_errors_and_warnings(self):
        # Test an invalid anchor type, which is still checked by validate_anchor
        # Use model_construct to bypass Pydantic validation
        invalid_type_anchor = Anchor.model_construct(name="TestAnchor", type="NON_EXISTENT_TYPE")
        statement = Statement(
            source=invalid_type_anchor,
            target=Anchor(name="ValidTarget"),
            modifiers=Modifier(confidence=0.3) # This should trigger a low confidence warning
        )

        errors, warnings = validate_statement(statement)
        assert len(errors) == 1
        assert errors[0].code == ErrorCode.E108_INVALID_ANCHOR_TYPE
        assert len(warnings) == 1
        assert warnings[0].code == WarningCode.W003_LOW_CONFIDENCE


class TestSTLValidatorClass:
    """Tests for STLValidator class and convenience functions."""

    def test_validator_init_strict(self):
        validator = STLValidator(strict=True)
        assert validator.strict is True

    def test_validate_parse_result_no_errors_or_warnings(self):
        # Create a parse result with valid statements that generate no warnings
        stmt1 = Statement(source=Anchor(name="SourceA"), target=Anchor(name="TargetB"), modifiers=Modifier(confidence=0.9))
        stmt2 = Statement(source=Anchor(name="SourceC"), target=Anchor(name="TargetD"), modifiers=Modifier(rule="causal"))
        parse_result = ParseResult(statements=[stmt1, stmt2], is_valid=True)

        validator = STLValidator()
        result = validator.validate(parse_result)
        assert result.is_valid is True
        assert not result.errors
        assert not result.warnings

    def test_validate_parse_result_with_errors(self):
        # Create a ParseResult that would generate errors from validate_statement (e.g., invalid anchor type)
        invalid_type_anchor = Anchor.model_construct(name="TestAnchor", type="NON_EXISTENT_TYPE")
        invalid_statement = Statement(source=invalid_type_anchor, target=Anchor(name="ValidTarget"))
        parse_result = ParseResult(statements=[invalid_statement], is_valid=True)
        
        validator = STLValidator()
        result = validator.validate(parse_result)
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].code == ErrorCode.E108_INVALID_ANCHOR_TYPE

    def test_validate_parse_result_with_warnings(self):
        # Create a ParseResult that would generate warnings (e.g., missing modifier)
        # Using longer anchor names to avoid W002
        statement_with_warning = Statement(source=Anchor(name="SourceAnchor"), target=Anchor(name="TargetAnchor")) # Missing modifier
        parse_result = ParseResult(statements=[statement_with_warning], is_valid=True)

        validator = STLValidator()
        result = validator.validate(parse_result)
        assert result.is_valid is True # Still valid, just warnings
        assert not result.errors
        # Assert presence of specific warning
        assert any(w.code == WarningCode.W004_MISSING_MODIFIER for w in result.warnings)
        # And no other unexpected warnings for this specific setup
        assert len(result.warnings) == 1 

    def test_validate_parse_result_strict_mode_with_warnings(self):
        # Create a ParseResult with warnings
        statement_with_warning = Statement(source=Anchor(name="SourceAnchor"), target=Anchor(name="TargetAnchor"))
        parse_result = ParseResult(statements=[statement_with_warning], is_valid=True)

        validator = STLValidator(strict=True)
        result = validator.validate(parse_result)
        assert result.is_valid is False # Should be invalid in strict mode
        assert not result.errors # No errors, but warnings treated as errors
        assert any(w.code == WarningCode.W004_MISSING_MODIFIER for w in result.warnings)
        assert len(result.warnings) == 1


    def test_check_duplicates(self):
        # Use valid, non-warning statements
        stmt1 = Statement(source=Anchor(name="AnchorA"), target=Anchor(name="AnchorB"), line=1, modifiers=Modifier(confidence=0.9))
        stmt2 = Statement(source=Anchor(name="AnchorA"), target=Anchor(name="AnchorB"), line=2, modifiers=Modifier(confidence=0.9)) # Duplicate of stmt1
        stmt3 = Statement(source=Anchor(name="AnchorC"), target=Anchor(name="AnchorD"), line=3, modifiers=Modifier(confidence=0.9))
        parse_result = ParseResult(statements=[stmt1, stmt2, stmt3], is_valid=True)

        validator = STLValidator()
        result = validator.validate(parse_result)
        assert result.is_valid is True # Duplicates are warnings, not errors
        assert not result.errors
        assert any(w.code == WarningCode.W006_DUPLICATE_STATEMENT for w in result.warnings)
        assert len([w for w in result.warnings if w.code == WarningCode.W006_DUPLICATE_STATEMENT]) == 1 # Only one duplicate warning
        assert result.warnings[0].line == 2 # Warning points to the duplicate line


    def test_validate_parse_result_empty(self, parse_result_empty):
        validator = STLValidator()
        result = validator.validate(parse_result_empty)
        assert result.is_valid is True
        assert not result.errors
        assert not result.warnings

    def test_convenience_validate_parse_result(self):
        # Using a statement that should not generate warnings or errors
        stmt = Statement(source=Anchor(name="SourceNode"), target=Anchor(name="TargetNode"), modifiers=Modifier(confidence=0.9))
        parse_result = ParseResult(statements=[stmt], is_valid=True)
        result = validate_parse_result(parse_result)
        assert result.is_valid is True
        assert not result.errors
        assert not result.warnings

    def test_is_valid_statement_valid(self):
        # Using a valid statement that generates no warnings
        statement = Statement(source=Anchor(name="SourceNode"), target=Anchor(name="TargetNode"), modifiers=Modifier(confidence=0.9))
        assert is_valid_statement(statement) is True

    def test_is_valid_statement_invalid(self):
        # Test a case that validate_statement would catch (e.g., invalid anchor type)
        # Use model_construct to bypass Pydantic validation
        invalid_type_anchor = Anchor.model_construct(name="TestAnchor", type="NON_EXISTENT_TYPE")
        invalid_statement = Statement(source=invalid_type_anchor, target=Anchor(name="B"))
        assert is_valid_statement(invalid_statement) is False
