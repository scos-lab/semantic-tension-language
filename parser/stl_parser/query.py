# -*- coding: utf-8 -*-
"""
STL Query Module — Find, filter, select, and pointer operations on parsed STL documents.

All operations are read-only: they return new objects and never modify inputs.

Example usage::

    from stl_parser import parse, find, find_all, filter_statements, select, stl_pointer

    result = parse('''
    [Theory_X] -> [Prediction_A] ::mod(confidence=0.95, rule="logical")
    [Theory_X] -> [Prediction_B] ::mod(confidence=0.70, rule="causal")
    [Study_Y] -> [Finding_Z] ::mod(confidence=0.85, rule="empirical")
    ''')

    # Find first match
    stmt = find(result, source="Theory_X", confidence__gt=0.8)

    # Find all matches
    stmts = find_all(result, rule="logical")

    # Filter to new ParseResult
    filtered = filter_statements(result, confidence__gte=0.8)

    # Extract field values
    names = select(result, "source")  # ["Theory_X", "Theory_X", "Study_Y"]

    # Pointer access
    val = stl_pointer(result, "/0/modifiers/confidence")  # 0.95
"""

from __future__ import annotations

from typing import Any, Dict, List, NamedTuple, Optional, TYPE_CHECKING

from .errors import ErrorCode, STLQueryError

if TYPE_CHECKING:
    from .models import ParseResult, Statement


# ========================================
# CONSTANTS
# ========================================

# Fields resolved directly from Statement (not from Modifier)
SPECIAL_FIELDS = {
    "source": lambda stmt: stmt.source.name,
    "target": lambda stmt: stmt.target.name,
    "source_namespace": lambda stmt: stmt.source.namespace,
    "target_namespace": lambda stmt: stmt.target.namespace,
    "arrow": lambda stmt: stmt.arrow,
}

# Valid operator suffixes
VALID_OPERATORS = frozenset(
    {"eq", "gt", "gte", "lt", "lte", "ne", "contains", "startswith", "in"}
)


# ========================================
# INTERNAL DATA STRUCTURES
# ========================================

class FieldCondition(NamedTuple):
    """A single query condition: field + operator + value."""
    field_name: str
    operator: str
    value: Any


# ========================================
# INTERNAL HELPERS
# ========================================

def _parse_kwargs(**kwargs: Any) -> List[FieldCondition]:
    """Convert query kwargs into a list of FieldCondition objects.

    Keys may contain operator suffixes separated by '__'.
    For example, ``confidence__gt=0.8`` becomes
    ``FieldCondition('confidence', 'gt', 0.8)``.
    """
    conditions: List[FieldCondition] = []
    for key, value in kwargs.items():
        parts = key.rsplit("__", 1)
        if len(parts) == 2 and parts[1] in VALID_OPERATORS:
            field_name, operator = parts
        else:
            field_name = key
            operator = "eq"
        conditions.append(FieldCondition(field_name, operator, value))
    return conditions


def _resolve_field(stmt: "Statement", field_name: str) -> Any:
    """Resolve a field name to its value on a Statement.

    Resolution order:
    1. Special fields (source, target, etc.) → resolved from Statement
    2. Standard Modifier fields → getattr(stmt.modifiers, field_name)
    3. Custom Modifier fields → stmt.modifiers.custom.get(field_name)
    4. None if not found or modifiers is absent
    """
    # Special fields
    resolver = SPECIAL_FIELDS.get(field_name)
    if resolver is not None:
        return resolver(stmt)

    # Modifier fields
    if stmt.modifiers is None:
        return None

    # Standard modifier field
    val = getattr(stmt.modifiers, field_name, _SENTINEL)
    if val is not _SENTINEL and field_name != "custom":
        return val

    # Custom modifier field
    return stmt.modifiers.custom.get(field_name)


# Sentinel to distinguish "attribute doesn't exist" from "attribute is None"
_SENTINEL = object()


def _apply_operator(field_value: Any, operator: str, target_value: Any) -> bool:
    """Apply a comparison operator between field_value and target_value.

    None handling:
    - eq with None target → True if field is also None
    - ne → True if field is None (absent != any value)
    - All other operators → False when field is None
    """
    if operator == "eq":
        return field_value == target_value

    if operator == "ne":
        return field_value != target_value

    # For ordering/string operators, None never matches
    if field_value is None:
        return False

    if operator == "gt":
        return field_value > target_value
    if operator == "gte":
        return field_value >= target_value
    if operator == "lt":
        return field_value < target_value
    if operator == "lte":
        return field_value <= target_value
    if operator == "contains":
        return target_value in str(field_value)
    if operator == "startswith":
        return str(field_value).startswith(target_value)
    if operator == "in":
        return field_value in target_value

    raise STLQueryError(
        code=ErrorCode.E450_QUERY_INVALID_OPERATOR,
        message=f"Unknown query operator: '{operator}'",
    )


def _matches(stmt: "Statement", conditions: List[FieldCondition]) -> bool:
    """Test if a statement satisfies ALL conditions (AND logic)."""
    for cond in conditions:
        field_value = _resolve_field(stmt, cond.field_name)
        if not _apply_operator(field_value, cond.operator, cond.value):
            return False
    return True


# ========================================
# PUBLIC API
# ========================================

def find(result: "ParseResult", **kwargs: Any) -> Optional["Statement"]:
    """Find the first statement matching all conditions.

    Args:
        result: ParseResult to search.
        **kwargs: Field conditions. Use plain ``field=value`` for equality,
            or ``field__op=value`` for other operators
            (gt, gte, lt, lte, ne, contains, startswith, in).

    Returns:
        First matching Statement, or None if no match.

    Example::

        stmt = find(result, source="Theory_X", confidence__gt=0.8)
    """
    conditions = _parse_kwargs(**kwargs)
    for stmt in result.statements:
        if _matches(stmt, conditions):
            return stmt
    return None


def find_all(result: "ParseResult", **kwargs: Any) -> List["Statement"]:
    """Find all statements matching all conditions.

    Args:
        result: ParseResult to search.
        **kwargs: Field conditions (same syntax as :func:`find`).

    Returns:
        List of matching Statements (empty list if none).

    Example::

        stmts = find_all(result, rule="causal")
    """
    conditions = _parse_kwargs(**kwargs)
    return [stmt for stmt in result.statements if _matches(stmt, conditions)]


def filter_statements(result: "ParseResult", **kwargs: Any) -> "ParseResult":
    """Filter a ParseResult to only matching statements.

    Returns a **new** ParseResult; the original is unmodified.

    Args:
        result: ParseResult to filter.
        **kwargs: Field conditions (same syntax as :func:`find`).

    Returns:
        New ParseResult containing only matching statements.

    Example::

        filtered = filter_statements(result, confidence__gte=0.8)
        print(filtered.to_stl())
    """
    from .models import ParseResult as _ParseResult

    matched = find_all(result, **kwargs)
    return _ParseResult(
        statements=matched,
        is_valid=result.is_valid,
    )


def select(result: "ParseResult", field: str) -> List[Any]:
    """Extract a single field value from every statement.

    Args:
        result: ParseResult to extract from.
        field: Field name to extract (e.g. ``"source"``, ``"confidence"``,
            ``"type"``).  Uses the same resolution as :func:`find`.

    Returns:
        List of values (includes None for statements where field is absent).

    Example::

        names = select(result, "source")       # ["A", "B", "C"]
        confs = select(result, "confidence")   # [0.95, None, 0.70]
    """
    return [_resolve_field(stmt, field) for stmt in result.statements]


def stl_pointer(result: "ParseResult", path: str) -> Any:
    """Access a nested value by slash-delimited path (inspired by JSON Pointer RFC 6901).

    Path format: ``/<statement_index>/<attribute>[/<sub_attribute>...]``

    Supported segments:
    - Integer index for statement selection: ``/0``, ``/1``
    - ``source``, ``target`` → Anchor object
    - ``source/name``, ``target/namespace`` → Anchor fields
    - ``modifiers`` → Modifier object
    - ``modifiers/<field_name>`` → standard or custom modifier field
    - ``arrow``, ``line``, ``column``, ``path_type`` → Statement fields

    Args:
        result: ParseResult to traverse.
        path: Slash-delimited path string.

    Returns:
        The resolved value.

    Raises:
        STLQueryError: If path is invalid or index is out of range.

    Example::

        stl_pointer(result, "/0/source/name")          # "Theory_X"
        stl_pointer(result, "/0/modifiers/confidence")  # 0.95
    """
    segments = [s for s in path.split("/") if s]

    if not segments:
        return result

    # First segment: statement index
    try:
        idx = int(segments[0])
    except ValueError:
        raise STLQueryError(
            code=ErrorCode.E451_QUERY_INVALID_PATH,
            message=f"First path segment must be a statement index (integer), got: '{segments[0]}'",
        )

    if idx < 0 or idx >= len(result.statements):
        raise STLQueryError(
            code=ErrorCode.E452_QUERY_INDEX_OUT_OF_RANGE,
            message=f"Statement index {idx} out of range (document has {len(result.statements)} statements)",
        )

    current: Any = result.statements[idx]

    # Walk remaining segments
    for i, segment in enumerate(segments[1:], start=1):
        if current is None:
            raise STLQueryError(
                code=ErrorCode.E451_QUERY_INVALID_PATH,
                message=f"Cannot traverse into None at segment '{segments[i-1]}' in path '{path}'",
            )

        # Try attribute access
        val = getattr(current, segment, _SENTINEL)
        if val is not _SENTINEL:
            current = val
            continue

        # Try custom dict access (for Modifier.custom)
        if hasattr(current, "custom") and isinstance(current.custom, dict):
            if segment in current.custom:
                current = current.custom[segment]
                continue

        raise STLQueryError(
            code=ErrorCode.E451_QUERY_INVALID_PATH,
            message=f"Invalid path segment '{segment}' at position {i} in path '{path}'",
        )

    return current
