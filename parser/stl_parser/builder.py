# -*- coding: utf-8 -*-
"""
STL Builder

Programmatic STL statement construction via fluent API.
Build Statement and ParseResult objects without parsing text.

Compiled from: docs/stlc/stl_builder_v1.0.0.stlc.md

Usage:
    >>> from stl_parser.builder import stl, stl_doc
    >>> stmt = stl("[A]", "[B]").mod(confidence=0.9, rule="causal").build()
    >>> doc = stl_doc(stl("[A]", "[B]"), stl("[C]", "[D]").mod(rule="logical"))
"""

from typing import Any, Dict, Optional, Union

from .models import Anchor, Modifier, Statement, ParseResult
from .validator import validate_statement
from .errors import STLBuilderError, ErrorCode


# Standard modifier field names (from Modifier.model_fields, excluding 'custom')
_STANDARD_MODIFIER_FIELDS = None


def _get_standard_fields() -> set:
    """Lazily compute standard modifier field names."""
    global _STANDARD_MODIFIER_FIELDS
    if _STANDARD_MODIFIER_FIELDS is None:
        _STANDARD_MODIFIER_FIELDS = set(Modifier.model_fields.keys()) - {"custom"}
    return _STANDARD_MODIFIER_FIELDS


def _parse_anchor_str(s: str) -> Anchor:
    """Parse an anchor string into an Anchor model.

    Supports formats:
        '[Obs:X]' -> Anchor(name='X', namespace='Obs')
        'Obs:X'   -> Anchor(name='X', namespace='Obs')
        '[X]'     -> Anchor(name='X')
        'X'       -> Anchor(name='X')

    Args:
        s: Anchor string to parse

    Returns:
        Anchor model instance

    Raises:
        STLBuilderError: If anchor string is empty or invalid
    """
    if not s or not s.strip():
        raise STLBuilderError(
            code=ErrorCode.E500_BUILDER_ERROR,
            message="Anchor string cannot be empty",
        )

    stripped = s.strip()

    # Remove surrounding brackets if present
    if stripped.startswith("[") and stripped.endswith("]"):
        stripped = stripped[1:-1]

    if not stripped:
        raise STLBuilderError(
            code=ErrorCode.E500_BUILDER_ERROR,
            message="Anchor name cannot be empty (got '[]')",
        )

    # Check for namespace (split on first ':')
    if ":" in stripped:
        parts = stripped.split(":", 1)
        namespace = parts[0].strip()
        name = parts[1].strip()
        if not name:
            raise STLBuilderError(
                code=ErrorCode.E500_BUILDER_ERROR,
                message=f"Anchor name cannot be empty after namespace '{namespace}:'",
            )
        return Anchor(name=name, namespace=namespace)
    else:
        return Anchor(name=stripped)


class StatementBuilder:
    """Fluent builder for constructing STL Statement objects.

    Usage:
        >>> builder = StatementBuilder(source, target)
        >>> stmt = builder.mod(confidence=0.9).mod(rule="causal").build()

    Use the stl() factory function instead of constructing directly.
    """

    def __init__(self, source: Anchor, target: Anchor):
        """Initialize builder with source and target anchors.

        Args:
            source: Source anchor
            target: Target anchor
        """
        self._source = source
        self._target = target
        self._modifiers: Dict[str, Any] = {}
        self._validate = True

    def mod(self, **kwargs: Any) -> "StatementBuilder":
        """Add modifier key-value pairs.

        Later calls override earlier ones for the same key.
        Returns self for method chaining.

        Args:
            **kwargs: Modifier key-value pairs

        Returns:
            self (for chaining)

        Example:
            >>> stl("[A]", "[B]").mod(confidence=0.9).mod(rule="causal")
        """
        self._modifiers.update(kwargs)
        return self

    def no_validate(self) -> "StatementBuilder":
        """Disable build-time validation.

        Returns:
            self (for chaining)
        """
        self._validate = False
        return self

    def build(self) -> Statement:
        """Build the Statement from accumulated state.

        Separates accumulated kwargs into standard Modifier fields
        and custom fields, constructs the Statement, and optionally
        validates it.

        Returns:
            Statement model instance

        Raises:
            STLBuilderError: If validation fails (when enabled)
        """
        modifier = None

        if self._modifiers:
            standard_fields = _get_standard_fields()

            # Separate standard vs custom modifier fields
            std_kwargs = {}
            custom_kwargs = {}

            for key, value in self._modifiers.items():
                if key in standard_fields:
                    std_kwargs[key] = value
                else:
                    custom_kwargs[key] = value

            try:
                if custom_kwargs:
                    modifier = Modifier(**std_kwargs, custom=custom_kwargs)
                else:
                    modifier = Modifier(**std_kwargs)
            except Exception as e:
                raise STLBuilderError(
                    code=ErrorCode.E502_BUILDER_VALIDATION_FAILED,
                    message=f"Invalid modifier values: {e}",
                ) from e

        stmt = Statement(
            source=self._source,
            target=self._target,
            modifiers=modifier,
        )

        if self._validate:
            errors, _warnings = validate_statement(stmt)
            if errors:
                error_msgs = "; ".join(str(e) for e in errors)
                raise STLBuilderError(
                    code=ErrorCode.E502_BUILDER_VALIDATION_FAILED,
                    message=f"Builder validation failed: {error_msgs}",
                )

        return stmt


def stl(source: str, target: str) -> StatementBuilder:
    """Create a StatementBuilder from anchor strings.

    This is the main entry point for programmatic STL construction.

    Args:
        source: Source anchor string ('[A]', 'A', 'Ns:A', '[Ns:A]')
        target: Target anchor string (same formats)

    Returns:
        StatementBuilder for fluent method chaining

    Example:
        >>> stmt = stl("[Theory]", "[Prediction]").mod(
        ...     confidence=0.95,
        ...     rule="logical"
        ... ).build()
    """
    source_anchor = _parse_anchor_str(source)
    target_anchor = _parse_anchor_str(target)
    return StatementBuilder(source_anchor, target_anchor)


def stl_doc(*builders: Union[StatementBuilder, Statement]) -> ParseResult:
    """Build multiple statements into a ParseResult.

    Accepts a mix of StatementBuilder and pre-built Statement objects.

    Args:
        *builders: StatementBuilder or Statement instances

    Returns:
        ParseResult containing all built statements

    Example:
        >>> doc = stl_doc(
        ...     stl("[A]", "[B]").mod(confidence=0.9),
        ...     stl("[C]", "[D]").mod(rule="causal"),
        ... )
        >>> len(doc.statements)
        2
    """
    statements = []

    for item in builders:
        if isinstance(item, StatementBuilder):
            statements.append(item.build())
        elif isinstance(item, Statement):
            statements.append(item)
        else:
            raise STLBuilderError(
                code=ErrorCode.E501_INVALID_BUILDER_STATE,
                message=f"stl_doc() expects StatementBuilder or Statement, got {type(item).__name__}",
            )

    return ParseResult(
        statements=statements,
        errors=[],
        warnings=[],
        is_valid=True,
    )
