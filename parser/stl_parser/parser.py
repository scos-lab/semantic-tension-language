# -*- coding: utf-8 -*-
"""
STL Parser

This module provides the main parsing functionality for STL text.
It transforms Lark parse trees into Pydantic models.
"""

import re
from typing import List, Dict, Any, Optional
from lark import Transformer, Token, Tree
from lark.exceptions import LarkError, UnexpectedInput

from .grammar import stl_parser
from .models import (
    Anchor,
    Modifier,
    Statement,
    ParseResult,
    ParseError,
    ParseWarning,
)
from .errors import ErrorCode
from ._utils import (
    is_stl_line as _is_stl_line,
    extract_stl_fences as _extract_stl_fences,
    extract_stl_heuristic as _extract_stl_heuristic,
    auto_extract_stl as _auto_extract_stl,
    is_pure_stl as _is_pure_stl,
    merge_multiline_statements as _merge_multiline_statements,
    remap_line_numbers as _remap_line_numbers,
    remove_markdown_escapes as _remove_markdown_escapes,
)


class STLTransformer(Transformer):
    """Transforms Lark parse trees into STL Pydantic models.

    This transformer handles the conversion of parsed grammar rules
    into the structured data models defined in models.py.

    Methods correspond to grammar rules and are called automatically
    by Lark during tree traversal.
    """

    def __init__(self):
        """Initialize the transformer with state tracking."""
        super().__init__()
        self.warnings: List[ParseWarning] = []
        self.current_line: Optional[int] = None
        self.current_column: Optional[int] = None

    # ========================================
    # ANCHOR TRANSFORMATIONS
    # ========================================

    def anchor(self, items: List[Any]) -> Anchor:
        """Transform anchor rule: "[" anchor_name "]"

        Args:
            items: [Anchor object from anchor_name]

        Returns:
            Anchor object
        """
        # anchor_name has already been transformed to an Anchor
        anchor_obj = items[0]

        # Extract line/column from metadata if available (for error reporting)
        # Note: metadata is on the original tree, not the transformed object

        return anchor_obj

    def anchor_name(self, items: List[Any]) -> Anchor:
        """Transform anchor_name: simple_identifier or namespaced_identifier

        Args:
            items: [Anchor object from simple_identifier or namespaced_identifier]

        Returns:
            Anchor object
        """
        # Both simple_identifier and namespaced_identifier return Anchor objects
        return items[0]

    def simple_identifier(self, items: List[Token]) -> Anchor:
        """Transform simple identifier: "Name"

        Args:
            items: [IDENTIFIER token]

        Returns:
            Anchor with just name
        """
        name = str(items[0])
        return Anchor(name=name)

    def namespaced_identifier(self, items: List[Any]) -> Anchor:
        """Transform namespaced identifier: "Namespace:Name"

        Args:
            items: [namespace, IDENTIFIER token]

        Returns:
            Anchor with namespace and name
        """
        namespace = items[0]  # Already processed by namespace rule
        name = str(items[1])
        return Anchor(name=name, namespace=namespace)

    def namespace(self, items: List[Token]) -> str:
        """Transform namespace: "Domain.Subdomain"

        Args:
            items: List of IDENTIFIER tokens

        Returns:
            Dot-joined namespace string
        """
        return ".".join(str(token) for token in items)

    # ========================================
    # ARROW TRANSFORMATIONS
    # ========================================

    def arrow(self, items: List[Token]) -> str:
        """Transform arrow: Unicode rightwards arrow (U+2192) or ASCII ->

        Args:
            items: [arrow token]

        Returns:
            Arrow string (normalized to Unicode rightwards arrow)
        """
        arrow_str = str(items[0])
        # Normalize to Unicode arrow
        unicode_arrow = "\u2192"
        return unicode_arrow if arrow_str in (unicode_arrow, "->") else arrow_str

    # ========================================
    # MODIFIER TRANSFORMATIONS
    # ========================================

    def modifier(self, items: List[Any]) -> Modifier:
        """Transform modifier: "::mod(key=value, ...)"

        Args:
            items: [modifier_list dict]

        Returns:
            Modifier object
        """
        modifier_dict = items[0]  # Already processed by modifier_list
        return Modifier(**modifier_dict)

    def modifier_list(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Transform modifier_list: key=value pairs

        Args:
            items: List of {key: value} dicts

        Returns:
            Combined dictionary of all key-value pairs
        """
        result = {}
        for pair_dict in items:
            result.update(pair_dict)
        return result

    def modifier_pair(self, items: List[Any]) -> Dict[str, Any]:
        """Transform modifier_pair: key=value

        Args:
            items: [key string, value]

        Returns:
            {key: value} dictionary
        """
        key = items[0]
        value = items[1]
        return {key: value}

    def key(self, items: List[Token]) -> str:
        """Transform key: IDENTIFIER

        Args:
            items: [IDENTIFIER token]

        Returns:
            Key string
        """
        return str(items[0])

    def string_value(self, items: List[Token]) -> str:
        """Transform string_value: ESCAPED_STRING

        Args:
            items: [ESCAPED_STRING token]

        Returns:
            Unquoted string
        """
        # Remove surrounding quotes
        value = str(items[0])
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        return value

    def numeric_value(self, items: List[Token]) -> float:
        """Transform numeric_value: NUMBER

        Args:
            items: [NUMBER token]

        Returns:
            Float or int value
        """
        value_str = str(items[0])

        # Handle percentage
        if value_str.endswith("%"):
            return float(value_str[:-1]) / 100.0

        # Return int if no decimal, float otherwise
        if "." in value_str:
            return float(value_str)
        return int(value_str)

    def boolean_value(self, items: List[Token]) -> bool:
        """Transform boolean_value: "true" or "false"

        Args:
            items: [BOOLEAN token]

        Returns:
            Boolean value
        """
        return str(items[0]).lower() == "true"

    def datetime_value(self, items: List[Token]) -> str:
        """Transform datetime_value: ISO8601_DATETIME

        Args:
            items: [ISO8601_DATETIME token]

        Returns:
            ISO 8601 datetime string
        """
        return str(items[0])

    # ========================================
    # PATH EXPRESSION TRANSFORMATIONS
    # ========================================

    def path_expression(self, items: List[Any]) -> List[Statement]:
        """Transform path_expression: anchor (arrow anchor modifier?)+

        Handles both simple paths [A] -> [B] and chained paths [A] -> [B] -> [C].
        Chained paths are expanded into multiple Statement objects.

        Args:
            items: [anchor, arrow, anchor, modifier?, arrow, anchor, modifier?, ...]

        Returns:
            List of Statement objects
        """
        statements = []

        # First anchor
        source = items[0]
        idx = 1

        # Process each arrow + anchor (+ optional modifier)
        while idx < len(items):
            arrow = items[idx]
            target = items[idx + 1]
            idx += 2

            # Check if next item is a modifier
            modifier = None
            if idx < len(items) and isinstance(items[idx], Modifier):
                modifier = items[idx]
                idx += 1

            # Create statement
            stmt = Statement(
                source=source,
                target=target,
                arrow=arrow,
                modifiers=modifier,
                line=self.current_line,
                column=self.current_column,
            )
            statements.append(stmt)

            # For chained paths, target becomes next source
            source = target

        return statements

    # ========================================
    # STATEMENT TRANSFORMATIONS
    # ========================================

    def statement(self, items: List[Any]) -> Any:
        """Transform statement: path_expression or comment

        Args:
            items: [statements list] or [comment]

        Returns:
            List of Statement objects or None for comments
        """
        # If it's a comment, return None (will be filtered out)
        if len(items) == 1 and items[0] is None:
            return None

        # Otherwise it's a path_expression result (list of statements)
        return items[0]

    def comment(self, items: List[Token]) -> None:
        """Transform comment: COMMENT

        Comments are not included in the final result.

        Args:
            items: [COMMENT token]

        Returns:
            None
        """
        return None

    # ========================================
    # START RULE
    # ========================================

    def start(self, items: List[Any]) -> List[Statement]:
        """Transform start: statement+

        Args:
            items: List of statement results

        Returns:
            Flat list of all Statement objects
        """
        statements = []

        for item in items:
            if item is None:
                # Skip comments
                continue
            elif isinstance(item, list):
                # Flatten statement lists from path expressions
                statements.extend(item)
            else:
                # Single statement
                statements.append(item)

        return statements


# ========================================
# PUBLIC API
# ========================================

def parse(text: str) -> ParseResult:
    """Parse STL text into structured format.

    This is the main entry point for parsing STL text. It handles
    both syntax parsing and transformation into Pydantic models.

    Args:
        text: STL text to parse

    Returns:
        ParseResult containing statements, errors, and warnings

    Example:
        >>> result = parse('[A] -> [B] ::mod(confidence=0.95)')
        >>> print(result.statements[0])
        [A] (arrow) [B] ::mod(confidence=0.95)
    """
    transformer = STLTransformer()

    # Handle empty or whitespace/comment-only input as valid with no statements
    stripped_text = text.strip()
    if not stripped_text or all(line.strip().startswith('#') for line in text.split('\n') if line.strip()):
        return ParseResult(
            statements=[],
            errors=[],
            warnings=[],
            is_valid=True,
        )

    try:
        # Parse with Lark
        tree = stl_parser.parse(text)

        # Transform to models
        statements = transformer.transform(tree)

        # Create result
        result = ParseResult(
            statements=statements,
            errors=[],
            warnings=transformer.warnings,
            is_valid=True,
        )

        return result


    except UnexpectedInput as e:
        # Syntax error
        error = ParseError(
            code="E001",
            message=f"Unexpected input: {str(e)}",
            line=getattr(e, "line", None),
            column=getattr(e, "column", None),
            suggestion="Check syntax - expected anchor, arrow, or modifier",
        )

        return ParseResult(
            statements=[],
            errors=[error],
            warnings=[],
            is_valid=False,
        )

    except LarkError as e:
        # Other parsing error
        error = ParseError(
            code="E002",
            message=f"Parse error: {str(e)}",
            suggestion="Check STL syntax",
        )

        return ParseResult(
            statements=[],
            errors=[error],
            warnings=[],
            is_valid=False,
        )

    except Exception as e:
        # Unexpected error
        error = ParseError(
            code="E999",
            message=f"Unexpected error: {str(e)}",
            suggestion="Please report this issue",
        )

        return ParseResult(
            statements=[],
            errors=[error],
            warnings=[],
            is_valid=False,
        )


def parse_file(file_path: str, mode: str = 'auto', auto_extract: bool = True) -> ParseResult:
    """Parse STL file into structured format with automatic content extraction.

    Supports parsing both pure STL files and mixed-content files (e.g., Markdown
    with embedded STL statements).

    Args:
        file_path: Path to STL file
        mode: Extraction mode ('auto', 'fenced', 'heuristic', 'strict')
            - 'auto': Automatically detect best extraction strategy (default)
            - 'fenced': Extract from ```stl code fences only
            - 'heuristic': Use pattern matching to identify STL lines
            - 'strict': No extraction, treat entire file as pure STL
        auto_extract: Enable/disable automatic STL extraction (default: True)

    Returns:
        ParseResult containing statements, errors, warnings, and extraction metadata

    Example:
        >>> # Pure STL file
        >>> result = parse_file('pure.stl')
        >>> print(f"Parsed {len(result.statements)} statements")

        >>> # Mixed content with automatic extraction
        >>> result = parse_file('mixed.md', mode='auto')
        >>> print(f"Format: {result.extraction_metadata['format']}")
        >>> print(f"STL lines: {result.extraction_metadata['stl_lines']}")

        >>> # Force strict mode (no extraction)
        >>> result = parse_file('file.md', mode='strict')
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        # Remove Markdown escapes if this is a .md file
        # Convert to string in case file_path is a Path object
        if str(file_path).endswith('.md'):
            text = _remove_markdown_escapes(text)

        # Merge multi-line statements into single lines FIRST
        # This must happen BEFORE auto-extraction because heuristic mode
        # examines lines individually and would lose continuation lines
        text = _merge_multiline_statements(text)

        # Auto-extract STL if enabled
        extraction_metadata = None
        if auto_extract:
            text, extraction_metadata = _auto_extract_stl(text, mode)

        # Parse the (possibly extracted and merged) text
        result = parse(text)

        # Attach extraction metadata
        if extraction_metadata:
            # Store as custom attribute
            result.extraction_metadata = extraction_metadata

            # Remap line numbers to original file
            if 'line_mapping' in extraction_metadata and extraction_metadata['line_mapping']:
                result = _remap_line_numbers(result, extraction_metadata['line_mapping'])

            # If auto-extraction found syntax errors, the overall result should be invalid
            if extraction_metadata.get('detection_stats', {}).get('syntax_errors', 0) > 0:
                # Set is_valid to False, and append a general error to the ParseResult
                # The specific syntax errors are detailed in extraction_metadata
                result.is_valid = False
                result.errors.append(ParseError(
                    code=ErrorCode.E003_EXTRACTION_SYNTAX_ERROR,
                    message="Auto-extraction detected possible syntax errors in the original content.",
                    suggestion=f"Review lines that were identified as possible syntax errors in the original file (see extraction metadata). Number of syntax errors detected: {extraction_metadata.get('detection_stats', {}).get('syntax_errors', 0)}."
                ))

        return result

    except FileNotFoundError:
        error = ParseError(
            code="E400",
            message=f"File not found: {file_path}",
            suggestion="Check file path",
        )
        return ParseResult(
            statements=[],
            errors=[error],
            warnings=[],
            is_valid=False,
        )

    except Exception as e:
        error = ParseError(
            code="E401",
            message=f"Error reading file: {str(e)}",
        )
        return ParseResult(
            statements=[],
            errors=[error],
            warnings=[],
            is_valid=False,
        )


# ========================================
# CONVENIENCE FUNCTIONS
# ========================================

def parse_statement(text: str) -> Optional[Statement]:
    """Parse a single STL statement.

    Args:
        text: Single statement text

    Returns:
        Statement object or None if parsing failed

    Example:
        >>> stmt = parse_statement('[A] -> [B]')
        >>> print(stmt.source.name)
        A
    """
    result = parse(text)

    if result.is_valid and len(result.statements) > 0:
        return result.statements[0]

    return None


def is_valid_stl(text: str) -> bool:
    """Check if text is valid STL.

    Args:
        text: STL text to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> is_valid_stl('[A] -> [B]')
        True
        >>> is_valid_stl('invalid syntax')
        False
    """
    result = parse(text)
    return result.is_valid
