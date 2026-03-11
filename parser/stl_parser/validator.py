# -*- coding: utf-8 -*-
"""
STL Parser Validator

This module provides validation functions for STL statements, anchors, and modifiers.
It performs both syntactic and semantic validation, checking that STL statements
follow the specification rules.

Validation includes:
- Anchor name and namespace validation
- Modifier value type and range validation
- Semantic consistency checks
- Path type inference
- Reserved name checks
"""

from typing import List, Optional, Set, Dict, Any, Tuple
import re
from datetime import datetime

from .models import (
    Anchor,
    AnchorType,
    PathType,
    Modifier,
    Statement,
    ParseResult,
    ParseError,
    ParseWarning,
)
from .errors import (
    STLValidationError,
    STLWarning,
    ErrorCode,
    WarningCode,
)


# ========================================
# CONSTANTS
# ========================================

# Reserved anchor names that cannot be used
RESERVED_NAMES: Set[str] = {
    "NULL", "UNDEFINED", "ANY", "NONE",
    "TRUE", "FALSE",
    "SYSTEM", "GLOBAL", "LOCAL",
}

# Valid rule types from STL specification
VALID_RULE_TYPES: Set[str] = {
    "causal", "correlative", "logical",
    "definitional", "empirical"
}

# Valid necessity values
VALID_NECESSITY_VALUES: Set[str] = {
    "Possible", "Contingent", "Necessary", "Impossible"
}

# Valid conditionality values
VALID_CONDITIONALITY_VALUES: Set[str] = {
    "Sufficient", "Necessary", "Both", "Neither"
}

# Regex patterns for validation
ISO8601_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})?)?$"
)


# ========================================
# ANCHOR VALIDATION
# ========================================







def validate_anchor(anchor: Anchor) -> List[STLValidationError]:
    """Validate complete anchor (name + namespace + type).

    Pydantic models handle name and namespace format validation on instantiation.
    This function primarily checks anchor type if specified.

    Args:
        anchor: Anchor to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Validate anchor type if specified
    if anchor.type:
        # Check if the value exists in the AnchorType enum values
        if anchor.type not in [t.value for t in AnchorType]:
            errors.append(STLValidationError(
                code=ErrorCode.E108_INVALID_ANCHOR_TYPE,
                message=f"Invalid anchor type '{anchor.type}'",
                anchor=anchor.name
            ))

    return errors


# ========================================
# MODIFIER VALIDATION
# ========================================




def validate_rule_type(rule: str, context: str = "") -> List[STLValidationError]:
    """Validate rule type is one of the standard types.

    Valid types: causal, correlative, logical, definitional, empirical

    Args:
        rule: Rule type to validate
        context: Context for error message

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    if rule not in VALID_RULE_TYPES:
        errors.append(STLValidationError(
            code=ErrorCode.E107_INVALID_RULE_TYPE,
            message=f"Invalid rule type '{rule}'",
            context={"rule": rule, "location": context},
            suggestion=f"Valid rules: {', '.join(sorted(VALID_RULE_TYPES))}"
        ))

    return errors


def validate_datetime_format(dt_string: str, context: str = "") -> List[STLValidationError]:
    """Validate datetime string is in ISO 8601 format.

    Valid formats:
    - YYYY-MM-DD
    - YYYY-MM-DDTHH:MM:SSZ
    - YYYY-MM-DDTHH:MM:SS+HH:MM

    Args:
        dt_string: Datetime string to validate
        context: Context for error message

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    if not ISO8601_PATTERN.match(dt_string):
        errors.append(STLValidationError(
            code=ErrorCode.E112_INVALID_DATETIME_FORMAT,
            message=f"Invalid datetime format '{dt_string}'",
            context={"datetime": dt_string, "location": context}
        ))
    else:
        # Try to parse to ensure it's a valid date
        try:
            # datetime.fromisoformat() in modern Python handles most ISO 8601 formats directly,
            # including those with timezone offsets (Z or +/-HH:MM).
            datetime.fromisoformat(dt_string)
        except ValueError as e:
            errors.append(STLValidationError(
                code=ErrorCode.E112_INVALID_DATETIME_FORMAT,
                message=f"Invalid datetime value '{dt_string}': {str(e)}",
                context={"datetime": dt_string, "location": context}
            ))

    return errors


def validate_necessity(necessity: str, context: str = "") -> List[STLValidationError]:
    """Validate necessity value.

    Valid values: Possible, Contingent, Necessary, Impossible

    Args:
        necessity: Necessity value to validate
        context: Context for error message

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    if necessity not in VALID_NECESSITY_VALUES:
        errors.append(STLValidationError(
            code=ErrorCode.E105_INVALID_MODIFIER_VALUE,
            message=f"Invalid necessity value '{necessity}'",
            context={"necessity": necessity, "location": context},
            suggestion=f"Valid values: {', '.join(sorted(VALID_NECESSITY_VALUES))}"
        ))

    return errors


def validate_conditionality(conditionality: str, context: str = "") -> List[STLValidationError]:
    """Validate conditionality value.

    Valid values: Sufficient, Necessary, Both, Neither

    Args:
        conditionality: Conditionality value to validate
        context: Context for error message

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    if conditionality not in VALID_CONDITIONALITY_VALUES:
        errors.append(STLValidationError(
            code=ErrorCode.E105_INVALID_MODIFIER_VALUE,
            message=f"Invalid conditionality value '{conditionality}'",
            context={"conditionality": conditionality, "location": context},
            suggestion=f"Valid values: {', '.join(sorted(VALID_CONDITIONALITY_VALUES))}"
        ))

    return errors


def validate_modifier(modifier: Modifier, context: str = "") -> List[STLValidationError]:
    """Validate all modifier fields.

    Pydantic models handle range validation for numeric types and some enum-like checks.
    This function focuses on validation that Pydantic's Field does not automatically cover,
    such as custom string-based enums and complex inter-field dependencies.

    Args:
        modifier: Modifier to validate
        context: Context for error message (e.g., statement location)

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Validate rule type (Pydantic Field does not validate against VALID_RULE_TYPES)
    if modifier.rule is not None:
        errors.extend(validate_rule_type(modifier.rule, context))

    # Validate datetime fields
    for field_name in ['time', 'timestamp']:
        field_value = getattr(modifier, field_name, None)
        if field_value is not None:
            errors.extend(validate_datetime_format(field_value, f"{context}.{field_name}"))

    # Validate necessity (Pydantic Field does not validate against VALID_NECESSITY_VALUES)
    if modifier.necessity is not None:
        errors.extend(validate_necessity(modifier.necessity, context))

    # Validate conditionality (Pydantic Field does not validate against VALID_CONDITIONALITY_VALUES)
    if modifier.conditionality is not None:
        errors.extend(validate_conditionality(modifier.conditionality, context))

    return errors


# ========================================
# SEMANTIC VALIDATION
# ========================================

def infer_anchor_type(anchor: Anchor) -> Optional[AnchorType]:
    """Infer anchor type from name patterns (heuristic).

    This is a simple heuristic that can be extended.

    Args:
        anchor: Anchor to analyze

    Returns:
        Inferred AnchorType, or None if cannot determine
    """
    name = anchor.name.lower()

    # Prioritize specific types before general ones

    # Agent indicators
    if any(keyword in name for keyword in ['agent', 'actor', 'person', 'user', 'system']):
        return AnchorType.AGENT

    # Event indicators
    if any(keyword in name for keyword in ['event', 'action', 'process', 'happened', 'occurred']):
        return AnchorType.EVENT

    # Question indicators
    if name.startswith('question') or name.endswith('question') or '?' in anchor.name:
        return AnchorType.QUESTION

    # Relational indicators
    if any(keyword in name for keyword in ['relation', 'relationship', 'between', 'link']):
        return AnchorType.RELATIONAL

    # Entity indicators (named entities, proper nouns)
    # Check after more specific types, as some specific types might also be proper nouns.
    # Check for articles with spaces to avoid matching words like "Albert"
    if anchor.name[0].isupper() and not name.startswith(('the ', 'a ', 'an ')):
        return AnchorType.NAME

    # Default to Concept for abstract ideas if no other type matches
    return AnchorType.CONCEPT


def infer_path_type(statement: Statement) -> Optional[PathType]:
    """Infer path type from modifiers and anchor types.

    Uses modifier.rule and other context to determine path type.

    Args:
        statement: Statement to analyze

    Returns:
        Inferred PathType, or None if cannot determine
    """
    if not statement.modifiers:
        return None

    # Check rule modifier
    if statement.modifiers.rule == "causal":
        return PathType.CAUSAL

    if statement.modifiers.rule == "logical":
        return PathType.INFERENTIAL

    if statement.modifiers.rule == "definitional":
        return PathType.SEMANTIC

    # Check for action indicators
    if statement.modifiers.intent:
        return PathType.ACTION

    # Check for cognitive indicators
    if statement.modifiers.focus or statement.modifiers.perspective:
        return PathType.COGNITIVE

    return None


def check_semantic_consistency(statement: Statement) -> List[STLValidationError]:
    """Check semantic consistency of statement.

    Validates that:
    - Modifiers are appropriate for the path type
    - Anchor types are consistent with path type
    - Required modifiers are present for certain path types

    Args:
        statement: Statement to validate

    Returns:
        List of validation errors (empty if consistent)
    """
    errors = []

    if not statement.modifiers:
        return errors

    # If path type is specified, check consistency
    if statement.path_type:
        # Causal paths should have causal modifiers
        if statement.path_type == PathType.CAUSAL:
            if not any([
                statement.modifiers.cause,
                statement.modifiers.effect,
                statement.modifiers.strength,
                statement.modifiers.rule == "causal"
            ]):
                errors.append(STLValidationError(
                    code=ErrorCode.E113_SEMANTIC_INCONSISTENCY,
                    message="Causal path should have causal modifiers (cause, effect, strength, or rule='causal')",
                    context={"path_type": "Causal", "statement": str(statement)}
                ))

    # Check for conflicting modifiers
    if statement.modifiers.rule == "empirical" and statement.modifiers.necessity == "Necessary":
        errors.append(STLValidationError(
            code=ErrorCode.E111_CONFLICTING_MODIFIERS,
            message="Empirical rules should not have necessity='Necessary' (empirical truths are contingent)",
            context={"rule": "empirical", "necessity": "Necessary"}
        ))

    # Check confidence with rule type
    if statement.modifiers.confidence is not None and statement.modifiers.rule == "definitional":
        if statement.modifiers.confidence < 0.95:
            # This is a warning, not an error
            pass  # Could add to warnings list

    return errors


# ========================================
# WARNINGS
# ========================================

def check_warnings(statement: Statement) -> List[STLWarning]:
    """Check for non-critical issues that should generate warnings.

    Args:
        statement: Statement to check

    Returns:
        List of warnings
    """
    warnings = []

    # Check for low confidence
    if statement.modifiers and statement.modifiers.confidence is not None:
        if statement.modifiers.confidence < 0.5:
            warnings.append(STLWarning(
                code=WarningCode.W003_LOW_CONFIDENCE,
                message=f"Low confidence value ({statement.modifiers.confidence})",
                line=statement.line,
                column=statement.column,
                context={"confidence": statement.modifiers.confidence}
            ))

    # Check for missing recommended modifiers
    if not statement.modifiers:
        warnings.append(STLWarning(
            code=WarningCode.W004_MISSING_MODIFIER,
            message="Statement has no modifiers (consider adding confidence or rule)",
            line=statement.line,
            column=statement.column
        ))

    # Check for unusual anchor names
    for anchor in [statement.source, statement.target]:
        if len(anchor.name) < 2:
            warnings.append(STLWarning(
                code=WarningCode.W002_UNUSUAL_ANCHOR_NAME,
                message=f"Very short anchor name '{anchor.name}'",
                line=statement.line,
                context={"anchor": anchor.name}
            ))

        if re.search(r'\d{3,}', anchor.name):
            warnings.append(STLWarning(
                code=WarningCode.W002_UNUSUAL_ANCHOR_NAME,
                message=f"Anchor name '{anchor.name}' contains many digits",
                line=statement.line,
                context={"anchor": anchor.name}
            ))

    return warnings


# ========================================
# STATEMENT VALIDATION
# ========================================

def validate_statement(statement: Statement) -> Tuple[List[STLValidationError], List[STLWarning]]:
    """Validate a complete statement.

    Performs all validation checks:
    - Anchor validation (source and target)
    - Modifier validation
    - Semantic consistency
    - Warning checks

    Args:
        statement: Statement to validate

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []

    # Validate source anchor
    errors.extend(validate_anchor(statement.source))

    # Validate target anchor
    errors.extend(validate_anchor(statement.target))

    # Validate modifiers if present
    if statement.modifiers:
        context = f"{statement.source.name} -> {statement.target.name}"
        errors.extend(validate_modifier(statement.modifiers, context))

    # Check semantic consistency
    errors.extend(check_semantic_consistency(statement))

    # Check for warnings
    warnings.extend(check_warnings(statement))

    return errors, warnings


# ========================================
# VALIDATOR CLASS
# ========================================

class STLValidator:
    """Main validator class for STL parse results.

    This class provides comprehensive validation of ParseResult objects,
    checking all statements for syntactic and semantic correctness.

    Usage:
        validator = STLValidator()
        result = validator.validate(parse_result)
    """

    def __init__(self, strict: bool = False):
        """Initialize validator.

        Args:
            strict: If True, treat warnings as errors
        """
        self.strict = strict
        self.errors: List[STLValidationError] = []
        self.warnings: List[STLWarning] = []

    def validate(self, parse_result: ParseResult) -> ParseResult:
        """Validate a ParseResult.

        Adds validation errors and warnings to the ParseResult.

        Args:
            parse_result: ParseResult to validate

        Returns:
            Updated ParseResult with validation errors and warnings
        """
        self.errors = []
        self.warnings = []

        # Validate each statement
        for statement in parse_result.statements:
            stmt_errors, stmt_warnings = validate_statement(statement)
            self.errors.extend(stmt_errors)
            self.warnings.extend(stmt_warnings)

        # Check for duplicate statements
        self._check_duplicates(parse_result.statements)

        # Convert validation errors to ParseError objects
        for error in self.errors:
            parse_result.errors.append(ParseError(
                code=error.code,
                message=error.message,
                line=error.line,
                column=error.column,
                suggestion=error.suggestion
            ))

        # Convert warnings to ParseWarning objects
        for warning in self.warnings:
            parse_result.warnings.append(ParseWarning(
                code=warning.code,
                message=warning.message,
                line=warning.line,
                column=warning.column
            ))

        # Update is_valid flag
        if parse_result.errors or (self.strict and parse_result.warnings):
            parse_result.is_valid = False

        return parse_result

    def _check_duplicates(self, statements: List[Statement]) -> None:
        """Check for duplicate statements and add warnings.

        Args:
            statements: List of statements to check
        """
        seen = {}

        for i, stmt in enumerate(statements):
            # Create a simple key for comparison
            key = (
                stmt.source.namespace,
                stmt.source.name,
                stmt.target.namespace,
                stmt.target.name
            )

            if key in seen:
                self.warnings.append(STLWarning(
                    code=WarningCode.W006_DUPLICATE_STATEMENT,
                    message=f"Duplicate statement: {stmt.source} -> {stmt.target}",
                    line=stmt.line,
                    context={
                        "first_occurrence": seen[key],
                        "duplicate_line": stmt.line
                    }
                ))
            else:
                seen[key] = stmt.line or i


# ========================================
# CONVENIENCE FUNCTIONS
# ========================================

def validate_parse_result(parse_result: ParseResult, strict: bool = False) -> ParseResult:
    """Convenience function to validate a ParseResult.

    Args:
        parse_result: ParseResult to validate
        strict: If True, treat warnings as errors

    Returns:
        Updated ParseResult with validation errors and warnings

    Example:
        >>> from stl_parser.parser import parse
        >>> from stl_parser.validator import validate_parse_result
        >>> result = parse('[A] -> [B]')
        >>> validated_result = validate_parse_result(result)
        >>> print(f"Valid: {validated_result.is_valid}")
    """
    validator = STLValidator(strict=strict)
    return validator.validate(parse_result)


def is_valid_statement(statement: Statement) -> bool:
    """Check if a statement is valid.

    Args:
        statement: Statement to check

    Returns:
        True if valid, False otherwise

    Example:
        >>> from stl_parser.models import Statement, Anchor
        >>> stmt = Statement(source=Anchor(name="A"), target=Anchor(name="B"))
        >>> is_valid_statement(stmt)
        True
    """
    errors, _ = validate_statement(statement)
    return len(errors) == 0
