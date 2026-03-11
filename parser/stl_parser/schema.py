# -*- coding: utf-8 -*-
"""
STL Schema — Schema Definition & Validation

Define, load, and validate STL documents against schema constraints.
Supports .stl.schema file format, dynamic Pydantic model generation,
and bidirectional Pydantic conversion.

Compiled from: docs/stlc/stl_schema_v1.0.0.stlc.md

Usage:
    >>> from stl_parser.schema import load_schema, validate_against_schema
    >>> schema = load_schema("events.stl.schema")
    >>> result = validate_against_schema(parse_result, schema)
"""

import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Type

from pydantic import BaseModel, Field, create_model

from .models import (
    Anchor,
    Modifier,
    Statement,
    ParseResult,
    ParseError,
    ParseWarning,
)
from .errors import STLSchemaError, ErrorCode


# ========================================
# DATA MODELS
# ========================================


class FieldConstraint(BaseModel):
    """Constraint definition for a single modifier field."""

    type: str = Field(description="Field type: float, string, enum, datetime, boolean, integer")
    min_value: Optional[float] = Field(None, description="Minimum value (for float/integer)")
    max_value: Optional[float] = Field(None, description="Maximum value (for float/integer)")
    enum_values: Optional[List[str]] = Field(None, description="Allowed values (for enum type)")
    pattern: Optional[str] = Field(None, description="Regex pattern (for string type)")


class SchemaAnchorConstraint(BaseModel):
    """Constraints for source or target anchors."""

    namespace_required: Optional[str] = Field(None, description="Required namespace value")
    namespace_optional: bool = Field(True, description="Whether namespace is optional")
    pattern: Optional[str] = Field(None, description="Regex pattern for anchor name")


class SchemaModifierConstraint(BaseModel):
    """Constraints for modifier fields."""

    required_fields: List[str] = Field(default_factory=list, description="Required modifier fields")
    optional_fields: List[str] = Field(default_factory=list, description="Optional modifier fields")
    field_constraints: Dict[str, FieldConstraint] = Field(
        default_factory=dict, description="Per-field type constraints"
    )


class SchemaConstraints(BaseModel):
    """Document-level constraints."""

    max_chain_length: Optional[int] = Field(None, description="Max chained path length")
    allow_cycles: Optional[bool] = Field(None, description="Whether cycles are allowed")
    min_statements: Optional[int] = Field(None, description="Minimum statement count")
    max_statements: Optional[int] = Field(None, description="Maximum statement count")


class STLSchema(BaseModel):
    """Top-level schema model for STL document validation."""

    name: str = Field(description="Schema name")
    version: str = Field(default="1.0", description="Schema version")
    namespace: Optional[str] = Field(None, description="Default namespace")
    source_anchor: SchemaAnchorConstraint = Field(default_factory=SchemaAnchorConstraint)
    target_anchor: SchemaAnchorConstraint = Field(default_factory=SchemaAnchorConstraint)
    modifier: SchemaModifierConstraint = Field(default_factory=SchemaModifierConstraint)
    constraints: SchemaConstraints = Field(default_factory=SchemaConstraints)


class SchemaError(BaseModel):
    """Single schema validation error."""

    code: str
    message: str
    statement_index: Optional[int] = None
    field: Optional[str] = None


class SchemaWarning(BaseModel):
    """Single schema validation warning."""

    code: str
    message: str
    statement_index: Optional[int] = None


class SchemaValidationResult(BaseModel):
    """Result of validating a ParseResult against a schema."""

    is_valid: bool = True
    errors: List[SchemaError] = Field(default_factory=list)
    warnings: List[SchemaWarning] = Field(default_factory=list)
    schema_name: str = ""
    schema_version: str = ""


# ========================================
# SCHEMA PARSING
# ========================================

# Simple recursive descent parser for .stl.schema format
# Avoids adding Lark dependency overhead for the relatively simple schema grammar

_TOKEN_RE = re.compile(
    r"""
    (?P<comment>\#[^\n]*)               |
    (?P<string>"[^"]*"|'[^']*')         |
    (?P<number>-?\d+(?:\.\d+)?)         |
    (?P<keyword>schema|anchor|modifier|constraints|namespace|source|target|
                required|optional|pattern|float|enum|string|datetime|boolean|integer|
                max_chain_length|allow_cycles|min_statements|max_statements|
                true|false)             |
    (?P<ident>[A-Za-z_]\w*(?:\.\w+)*)          |
    (?P<lbrace>\{)                      |
    (?P<rbrace>\})                      |
    (?P<lparen>\()                      |
    (?P<rparen>\))                      |
    (?P<colon>:)                        |
    (?P<comma>,)                        |
    (?P<lbracket>\[)                    |
    (?P<rbracket>\])                    |
    (?P<regex>/[^/]+/)                  |
    (?P<ws>\s+)
    """,
    re.VERBOSE,
)


def _tokenize(text: str) -> List[Tuple[str, str]]:
    """Tokenize schema text into (type, value) pairs."""
    tokens = []
    pos = 0
    while pos < len(text):
        m = _TOKEN_RE.match(text, pos)
        if not m:
            raise STLSchemaError(
                code=ErrorCode.E600_SCHEMA_PARSE_ERROR,
                message=f"Unexpected character at position {pos}: '{text[pos]}'",
            )
        pos = m.end()
        kind = m.lastgroup
        val = m.group()
        if kind in ("ws", "comment"):
            continue
        tokens.append((kind, val))
    return tokens


class _SchemaParser:
    """Recursive descent parser for .stl.schema format."""

    def __init__(self, tokens: List[Tuple[str, str]]):
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> Optional[Tuple[str, str]]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _advance(self) -> Tuple[str, str]:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _expect(self, kind: str, value: str = None) -> str:
        tok = self._peek()
        if tok is None:
            raise STLSchemaError(
                code=ErrorCode.E600_SCHEMA_PARSE_ERROR,
                message=f"Unexpected end of input, expected {kind}" + (f" '{value}'" if value else ""),
            )
        if tok[0] != kind and tok[1] != value:
            if value:
                if tok[1] != value:
                    raise STLSchemaError(
                        code=ErrorCode.E600_SCHEMA_PARSE_ERROR,
                        message=f"Expected '{value}', got '{tok[1]}'",
                    )
            else:
                raise STLSchemaError(
                    code=ErrorCode.E600_SCHEMA_PARSE_ERROR,
                    message=f"Expected {kind}, got {tok[0]} '{tok[1]}'",
                )
        return self._advance()[1]

    def _expect_value(self, value: str) -> str:
        tok = self._peek()
        if tok is None or tok[1] != value:
            got = tok[1] if tok else "EOF"
            raise STLSchemaError(
                code=ErrorCode.E600_SCHEMA_PARSE_ERROR,
                message=f"Expected '{value}', got '{got}'",
            )
        return self._advance()[1]

    def parse(self) -> STLSchema:
        """Parse top-level schema definition."""
        self._expect_value("schema")
        tok = self._peek()
        name = self._advance()[1]
        # Version is optional
        version = "1.0"
        tok = self._peek()
        if tok and tok[0] == "ident":
            version = self._advance()[1]
        elif tok and tok[0] == "number":
            version = self._advance()[1]

        self._expect_value("{")

        schema = STLSchema(name=name, version=version)

        while self._peek() and self._peek()[1] != "}":
            tok = self._peek()
            keyword = tok[1]

            if keyword == "namespace":
                self._advance()
                val = self._advance()[1]
                schema.namespace = val.strip('"').strip("'")

            elif keyword == "anchor":
                self._advance()
                role_tok = self._advance()
                role = role_tok[1]
                self._expect_value("{")
                anchor_constraint = self._parse_anchor_block()
                self._expect_value("}")
                if role == "source":
                    schema.source_anchor = anchor_constraint
                elif role == "target":
                    schema.target_anchor = anchor_constraint

            elif keyword == "modifier":
                self._advance()
                self._expect_value("{")
                schema.modifier = self._parse_modifier_block()
                self._expect_value("}")

            elif keyword == "constraints":
                self._advance()
                self._expect_value("{")
                schema.constraints = self._parse_constraints_block()
                self._expect_value("}")

            else:
                # Skip unknown top-level keyword
                self._advance()

        self._expect_value("}")
        return schema

    def _parse_anchor_block(self) -> SchemaAnchorConstraint:
        """Parse anchor constraint block."""
        constraint = SchemaAnchorConstraint()

        while self._peek() and self._peek()[1] != "}":
            key = self._advance()[1]
            self._expect_value(":")

            if key == "namespace":
                tok = self._peek()
                if tok[1] == "required":
                    self._advance()
                    self._expect_value("(")
                    val = self._advance()[1].strip('"').strip("'")
                    self._expect_value(")")
                    constraint.namespace_required = val
                    constraint.namespace_optional = False
                elif tok[1] == "optional":
                    self._advance()
                    constraint.namespace_optional = True
                else:
                    val = self._advance()[1].strip('"').strip("'")
                    constraint.namespace_required = val
                    constraint.namespace_optional = False

            elif key == "pattern":
                val = self._advance()[1]
                # Strip regex delimiters
                if val.startswith("/") and val.endswith("/"):
                    val = val[1:-1]
                constraint.pattern = val

            else:
                # Skip unknown keys
                self._advance()

        return constraint

    def _parse_modifier_block(self) -> SchemaModifierConstraint:
        """Parse modifier constraint block."""
        mc = SchemaModifierConstraint()

        while self._peek() and self._peek()[1] != "}":
            key = self._advance()[1]
            self._expect_value(":")

            if key == "required":
                mc.required_fields = self._parse_string_list()
            elif key == "optional":
                mc.optional_fields = self._parse_string_list()
            else:
                # Field constraint: key: type(args)
                fc = self._parse_field_constraint()
                mc.field_constraints[key] = fc

        return mc

    def _parse_field_constraint(self) -> FieldConstraint:
        """Parse a single field type constraint like float(0.5, 1.0) or enum("a", "b")."""
        tok = self._advance()
        type_name = tok[1]

        fc = FieldConstraint(type=type_name)

        if self._peek() and self._peek()[1] == "(":
            self._advance()  # consume (
            args = []
            while self._peek() and self._peek()[1] != ")":
                val = self._advance()[1]
                if val == ",":
                    continue
                args.append(val.strip('"').strip("'"))
            self._expect_value(")")

            if type_name == "float" or type_name == "integer":
                if len(args) >= 1:
                    fc.min_value = float(args[0])
                if len(args) >= 2:
                    fc.max_value = float(args[1])
            elif type_name == "enum":
                fc.enum_values = args

        return fc

    def _parse_string_list(self) -> List[str]:
        """Parse [item1, item2, ...] list."""
        self._expect_value("[")
        items = []
        while self._peek() and self._peek()[1] != "]":
            val = self._advance()[1]
            if val == ",":
                continue
            items.append(val.strip('"').strip("'"))
        self._expect_value("]")
        return items

    def _parse_constraints_block(self) -> SchemaConstraints:
        """Parse constraints block."""
        sc = SchemaConstraints()

        while self._peek() and self._peek()[1] != "}":
            key = self._advance()[1]
            self._expect_value(":")
            val = self._advance()[1]

            if key == "max_chain_length":
                sc.max_chain_length = int(val)
            elif key == "allow_cycles":
                sc.allow_cycles = val.lower() == "true"
            elif key == "min_statements":
                sc.min_statements = int(val)
            elif key == "max_statements":
                sc.max_statements = int(val)

        return sc


def _parse_schema_text(text: str) -> STLSchema:
    """Parse schema text into STLSchema model."""
    tokens = _tokenize(text)
    parser = _SchemaParser(tokens)
    return parser.parse()


# ========================================
# PUBLIC API
# ========================================


def load_schema(source: str) -> STLSchema:
    """Load an STL schema from a file path or raw text.

    Args:
        source: File path (ending in .stl.schema) or raw schema text

    Returns:
        STLSchema model

    Raises:
        STLSchemaError: If schema cannot be parsed

    Example:
        >>> schema = load_schema("events.stl.schema")
        >>> schema = load_schema('schema EventLog v1.0 { ... }')
    """
    # Determine if source is a file path or raw text
    if (
        source.strip().endswith(".stl.schema")
        or source.strip().endswith(".schema")
    ) and os.path.isfile(source.strip()):
        try:
            with open(source.strip(), "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            raise STLSchemaError(
                code=ErrorCode.E600_SCHEMA_PARSE_ERROR,
                message=f"Failed to read schema file: {e}",
            ) from e
    else:
        text = source

    return _parse_schema_text(text)


def validate_against_schema(
    parse_result: ParseResult,
    schema: STLSchema,
) -> SchemaValidationResult:
    """Validate a ParseResult against an STL schema.

    Checks all statements against schema constraints including:
    - Anchor namespace and pattern requirements
    - Required modifier fields
    - Field type, range, and enum constraints
    - Document-level constraints (min/max statements)

    Args:
        parse_result: ParseResult to validate
        schema: STLSchema to validate against

    Returns:
        SchemaValidationResult with errors and warnings

    Example:
        >>> result = validate_against_schema(parsed, schema)
        >>> if result.is_valid:
        ...     print("Document conforms to schema")
    """
    errors: List[SchemaError] = []
    warnings: List[SchemaWarning] = []

    # Document-level constraints
    stmt_count = len(parse_result.statements)

    if schema.constraints.min_statements is not None:
        if stmt_count < schema.constraints.min_statements:
            errors.append(SchemaError(
                code="E601",
                message=f"Too few statements: {stmt_count} < {schema.constraints.min_statements}",
            ))

    if schema.constraints.max_statements is not None:
        if stmt_count > schema.constraints.max_statements:
            errors.append(SchemaError(
                code="E601",
                message=f"Too many statements: {stmt_count} > {schema.constraints.max_statements}",
            ))

    # Validate each statement
    for idx, stmt in enumerate(parse_result.statements):
        _validate_anchor_constraint(stmt.source, schema.source_anchor, "source", idx, errors)
        _validate_anchor_constraint(stmt.target, schema.target_anchor, "target", idx, errors)
        _validate_modifier_constraint(stmt, schema.modifier, idx, errors)

    return SchemaValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        schema_name=schema.name,
        schema_version=schema.version,
    )


def _validate_anchor_constraint(
    anchor: Anchor,
    constraint: SchemaAnchorConstraint,
    role: str,
    stmt_idx: int,
    errors: List[SchemaError],
) -> None:
    """Validate an anchor against schema constraints."""
    # Namespace check
    if constraint.namespace_required is not None:
        if anchor.namespace != constraint.namespace_required:
            errors.append(SchemaError(
                code="E601",
                message=f"Statement {stmt_idx}: {role} anchor namespace must be "
                        f"'{constraint.namespace_required}', got '{anchor.namespace}'",
                statement_index=stmt_idx,
                field=f"{role}.namespace",
            ))
    elif not constraint.namespace_optional:
        if anchor.namespace is None:
            errors.append(SchemaError(
                code="E601",
                message=f"Statement {stmt_idx}: {role} anchor must have a namespace",
                statement_index=stmt_idx,
                field=f"{role}.namespace",
            ))

    # Pattern check
    if constraint.pattern:
        if not re.fullmatch(constraint.pattern, anchor.name):
            errors.append(SchemaError(
                code="E601",
                message=f"Statement {stmt_idx}: {role} anchor name '{anchor.name}' "
                        f"does not match pattern '{constraint.pattern}'",
                statement_index=stmt_idx,
                field=f"{role}.name",
            ))


def _validate_modifier_constraint(
    stmt: Statement,
    constraint: SchemaModifierConstraint,
    stmt_idx: int,
    errors: List[SchemaError],
) -> None:
    """Validate statement modifiers against schema constraints."""
    # Check required fields
    for field_name in constraint.required_fields:
        if stmt.modifiers is None:
            errors.append(SchemaError(
                code="E601",
                message=f"Statement {stmt_idx}: missing required modifier '{field_name}' (no modifiers)",
                statement_index=stmt_idx,
                field=field_name,
            ))
            continue

        val = getattr(stmt.modifiers, field_name, None)
        # Also check custom dict
        if val is None and field_name in stmt.modifiers.custom:
            val = stmt.modifiers.custom[field_name]
        if val is None:
            errors.append(SchemaError(
                code="E601",
                message=f"Statement {stmt_idx}: missing required modifier '{field_name}'",
                statement_index=stmt_idx,
                field=field_name,
            ))

    # Check field constraints
    if stmt.modifiers is None:
        return

    for field_name, fc in constraint.field_constraints.items():
        val = getattr(stmt.modifiers, field_name, None)
        if val is None and field_name in stmt.modifiers.custom:
            val = stmt.modifiers.custom[field_name]
        if val is None:
            continue  # Not present, skip (required check is separate)

        # Type/range check
        if fc.type in ("float", "integer"):
            if not isinstance(val, (int, float)):
                errors.append(SchemaError(
                    code="E603",
                    message=f"Statement {stmt_idx}: '{field_name}' must be numeric, got {type(val).__name__}",
                    statement_index=stmt_idx,
                    field=field_name,
                ))
                continue
            if fc.min_value is not None and val < fc.min_value:
                errors.append(SchemaError(
                    code="E603",
                    message=f"Statement {stmt_idx}: '{field_name}' value {val} < min {fc.min_value}",
                    statement_index=stmt_idx,
                    field=field_name,
                ))
            if fc.max_value is not None and val > fc.max_value:
                errors.append(SchemaError(
                    code="E603",
                    message=f"Statement {stmt_idx}: '{field_name}' value {val} > max {fc.max_value}",
                    statement_index=stmt_idx,
                    field=field_name,
                ))

        elif fc.type == "enum":
            if fc.enum_values and str(val) not in fc.enum_values:
                errors.append(SchemaError(
                    code="E603",
                    message=f"Statement {stmt_idx}: '{field_name}' value '{val}' not in "
                            f"allowed values {fc.enum_values}",
                    statement_index=stmt_idx,
                    field=field_name,
                ))

        elif fc.type == "string":
            if not isinstance(val, str):
                errors.append(SchemaError(
                    code="E603",
                    message=f"Statement {stmt_idx}: '{field_name}' must be string, got {type(val).__name__}",
                    statement_index=stmt_idx,
                    field=field_name,
                ))
            elif fc.pattern and not re.match(fc.pattern, val):
                errors.append(SchemaError(
                    code="E603",
                    message=f"Statement {stmt_idx}: '{field_name}' value '{val}' "
                            f"does not match pattern '{fc.pattern}'",
                    statement_index=stmt_idx,
                    field=field_name,
                ))


# ========================================
# PYDANTIC CONVERSION
# ========================================


def to_pydantic(schema: STLSchema) -> Type[BaseModel]:
    """Generate a dynamic Pydantic model from an STL schema.

    Creates a model class with typed fields based on the schema's
    modifier constraints.

    Args:
        schema: STLSchema to convert

    Returns:
        Dynamic Pydantic BaseModel subclass

    Example:
        >>> EventMod = to_pydantic(schema)
        >>> mod = EventMod(confidence=0.9, rule="causal")
    """
    field_definitions = {}

    for field_name, fc in schema.modifier.field_constraints.items():
        python_type = _schema_type_to_python(fc)
        field_kwargs = {}

        if fc.min_value is not None:
            field_kwargs["ge"] = fc.min_value
        if fc.max_value is not None:
            field_kwargs["le"] = fc.max_value

        is_required = field_name in schema.modifier.required_fields
        if not is_required:
            python_type = Optional[python_type]
            field_kwargs["default"] = None

        field_definitions[field_name] = (python_type, Field(**field_kwargs))

    model_name = schema.name + "Modifier"
    return create_model(model_name, **field_definitions)


def from_pydantic(model_class: Type[BaseModel], name: str = "Extracted") -> STLSchema:
    """Extract an STLSchema from a Pydantic model class.

    Introspects model fields to build schema constraints.

    Args:
        model_class: Pydantic BaseModel subclass
        name: Schema name

    Returns:
        STLSchema

    Example:
        >>> class MyMod(BaseModel):
        ...     confidence: float = Field(ge=0.0, le=1.0)
        ...     rule: str
        >>> schema = from_pydantic(MyMod, name="MySchema")
    """
    required_fields = []
    optional_fields = []
    field_constraints = {}

    for field_name, field_info in model_class.model_fields.items():
        # Determine if required
        is_required = field_info.is_required()
        if is_required:
            required_fields.append(field_name)
        else:
            optional_fields.append(field_name)

        # Build field constraint
        fc = _python_field_to_constraint(field_info)
        if fc:
            field_constraints[field_name] = fc

    return STLSchema(
        name=name,
        modifier=SchemaModifierConstraint(
            required_fields=required_fields,
            optional_fields=optional_fields,
            field_constraints=field_constraints,
        ),
    )


def _schema_type_to_python(fc: FieldConstraint) -> type:
    """Map schema type to Python type."""
    type_map = {
        "float": float,
        "integer": int,
        "string": str,
        "boolean": bool,
        "datetime": str,
    }
    return type_map.get(fc.type, Any)


def _python_field_to_constraint(field_info) -> Optional[FieldConstraint]:
    """Convert Pydantic field info to FieldConstraint."""
    annotation = field_info.annotation

    # Unwrap Optional
    origin = getattr(annotation, "__origin__", None)
    if origin is type(None):
        return None

    # Handle Optional[X] (Union[X, None])
    args = getattr(annotation, "__args__", None)
    if args and type(None) in args:
        # Get the non-None type
        real_types = [a for a in args if a is not type(None)]
        if real_types:
            annotation = real_types[0]

    type_name = "string"
    if annotation is float:
        type_name = "float"
    elif annotation is int:
        type_name = "integer"
    elif annotation is bool:
        type_name = "boolean"
    elif annotation is str:
        type_name = "string"

    fc = FieldConstraint(type=type_name)

    # Extract ge/le from metadata
    for meta in field_info.metadata:
        if hasattr(meta, "ge") and meta.ge is not None:
            fc.min_value = float(meta.ge)
        if hasattr(meta, "le") and meta.le is not None:
            fc.max_value = float(meta.le)

    return fc
