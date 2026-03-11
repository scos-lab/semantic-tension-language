# -*- coding: utf-8 -*-
"""
STL Parser Error Definitions

This module defines all custom exceptions, error codes, and error formatting
utilities for the STL parser.

Error Code Ranges:
- E001-E099: Parse errors
- E100-E199: Validation errors
- E200-E299: Serialization errors
- E300-E399: Graph construction errors
- E400-E449: File I/O errors
- E450-E499: Query errors
- W001-W099: Warnings
"""

from typing import Optional, Dict, Any, List
from enum import Enum


# ========================================
# ERROR CODE ENUMS
# ========================================

class ErrorCode(str, Enum):
    """Standard error codes for STL parser.

    Error code ranges:
    - E001-E099: Parse errors
    - E100-E199: Validation errors
    - E200-E299: Serialization errors
    - E300-E399: Graph construction errors
    - E400-E449: File I/O errors
    - E450-E499: Query errors
    """

    # Parse Errors (E001-E099)
    E001_UNEXPECTED_TOKEN = "E001"
    E002_INVALID_SYNTAX = "E002"
    E003_EXTRACTION_SYNTAX_ERROR = "E003" # New error code
    E004_UNCLOSED_BRACKET = "E004"
    E005_INVALID_ARROW = "E005"
    E006_INVALID_MODIFIER = "E006"
    E007_MALFORMED_NAMESPACE = "E007"
    E008_INVALID_STRING = "E008"
    E009_INVALID_NUMBER = "E009"
    E010_INVALID_DATETIME = "E010"
    E011_UNEXPECTED_EOF = "E011"

    # Validation Errors (E100-E199)
    E100_INVALID_ANCHOR_NAME = "E100"
    E101_RESERVED_NAME = "E101"
    E102_ANCHOR_TOO_LONG = "E102"
    E103_INVALID_NAMESPACE_FORMAT = "E103"
    E104_INVALID_MODIFIER_KEY = "E104"
    E105_INVALID_MODIFIER_VALUE = "E105"
    E106_CONFIDENCE_OUT_OF_RANGE = "E106"
    E107_INVALID_RULE_TYPE = "E107"
    E108_INVALID_ANCHOR_TYPE = "E108"
    E109_INVALID_PATH_TYPE = "E109"
    E110_MISSING_REQUIRED_MODIFIER = "E110"
    E111_CONFLICTING_MODIFIERS = "E111"
    E112_INVALID_DATETIME_FORMAT = "E112"
    E113_SEMANTIC_INCONSISTENCY = "E113"
    E114_CIRCULAR_REFERENCE = "E114"
    E115_DANGLING_REFERENCE = "E115"

    # Serialization Errors (E200-E299)
    E200_SERIALIZATION_FAILED = "E200"
    E201_INVALID_JSON = "E201"
    E202_INVALID_JSON_LD = "E202"
    E203_INVALID_RDF = "E203"
    E204_DESERIALIZATION_FAILED = "E204"
    E205_MISSING_CONTEXT = "E205"
    E206_INCOMPATIBLE_VERSION = "E206"
    E207_ENCODING_ERROR = "E207"

    # Graph Errors (E300-E399)
    E300_GRAPH_CONSTRUCTION_FAILED = "E300"
    E301_INVALID_EDGE = "E301"
    E302_INVALID_NODE = "E302"
    E303_GRAPH_CYCLE_DETECTED = "E303"
    E304_DISCONNECTED_GRAPH = "E304"

    # File I/O Errors (E400-E449)
    E400_FILE_NOT_FOUND = "E400"
    E401_FILE_READ_ERROR = "E401"
    E402_FILE_WRITE_ERROR = "E402"
    E403_PERMISSION_DENIED = "E403"
    E404_INVALID_FILE_FORMAT = "E404"

    # Query Errors (E450-E499)
    E450_QUERY_INVALID_OPERATOR = "E450"
    E451_QUERY_INVALID_PATH = "E451"
    E452_QUERY_INDEX_OUT_OF_RANGE = "E452"
    E453_QUERY_TYPE_ERROR = "E453"

    # Builder Errors (E500-E599)
    E500_BUILDER_ERROR = "E500"
    E501_INVALID_BUILDER_STATE = "E501"
    E502_BUILDER_VALIDATION_FAILED = "E502"

    # Schema Errors (E600-E699)
    E600_SCHEMA_PARSE_ERROR = "E600"
    E601_SCHEMA_VALIDATION_FAILED = "E601"
    E602_INVALID_SCHEMA_FORMAT = "E602"
    E603_SCHEMA_CONSTRAINT_VIOLATION = "E603"

    # LLM Errors (E700-E799)
    E700_LLM_CLEAN_ERROR = "E700"
    E701_LLM_REPAIR_FAILED = "E701"
    E702_UNREPAIRABLE_OUTPUT = "E702"

    # Emitter Errors (E800-E899)
    E800_EMITTER_ERROR = "E800"
    E801_EMITTER_LOG_WRITE_FAILED = "E801"

    # Decay Errors (E900-E949)
    E900_DECAY_ERROR = "E900"
    E901_INVALID_DECAY_TIMESTAMP = "E901"

    # Diff/Patch Errors (E950-E959)
    E950_DIFF_TYPE_ERROR = "E950"
    E951_PATCH_STATEMENT_NOT_FOUND = "E951"
    E952_PATCH_CONFLICT = "E952"
    E953_PATCH_INVALID_OP = "E953"

    # Reader Errors (E960-E969)
    E960_READER_SOURCE_ERROR = "E960"
    E961_READER_PARSE_ERROR = "E961"
    E962_READER_CONTINUATION_OVERFLOW = "E962"


class WarningCode(str, Enum):
    """Warning codes for non-critical issues."""

    W001_DEPRECATED_SYNTAX = "W001"
    W002_UNUSUAL_ANCHOR_NAME = "W002"
    W003_LOW_CONFIDENCE = "W003"
    W004_MISSING_MODIFIER = "W004"
    W005_INCONSISTENT_STYLE = "W005"
    W006_DUPLICATE_STATEMENT = "W006"
    W007_UNUSED_ANCHOR = "W007"
    W008_COMPLEX_NAMESPACE = "W008"
    W009_PERFORMANCE_WARNING = "W009"


# ========================================
# ERROR MESSAGES AND SUGGESTIONS
# ========================================

ERROR_MESSAGES: Dict[str, Dict[str, str]] = {
    # Parse Errors
    "E001": {
        "message": "Unexpected token",
        "suggestion": "Check syntax - expected anchor, arrow, or modifier"
    },
    "E002": {
        "message": "Invalid syntax",
        "suggestion": "Verify STL syntax follows: [Anchor] -> [Anchor] ::mod(...)"
    },
    "E003": {
        "message": "Auto-extraction detected syntax errors",
        "suggestion": "Review lines marked as possible syntax errors in extraction metadata."
    },
    "E004": { # Old E003
        "message": "Unclosed bracket",
        "suggestion": "Ensure all anchor brackets are properly closed"
    },
    "E005": { # Old E004
        "message": "Invalid arrow syntax",
        "suggestion": "Use '->' or '\u2192' for path arrows"
    },
    "E006": { # Old E005
        "message": "Invalid modifier syntax",
        "suggestion": "Modifiers must follow format: ::mod(key=value, ...)"
    },
    "E007": { # Old E006
        "message": "Malformed namespace",
        "suggestion": "Namespace format: [Namespace:Name] or [A.B.C:Name]"
    },
    "E008": { # Old E007
        "message": "Invalid string value",
        "suggestion": "String values must be quoted with \" or '"
    },
    "E009": { # Old E008
        "message": "Invalid number format",
        "suggestion": "Numbers can be integers, floats, or percentages (e.g., 0.95 or 95%)"
    },
    "E010": { # Old E009
        "message": "Invalid datetime format",
        "suggestion": "Use ISO 8601: YYYY-MM-DDTHH:MM:SSZ"
    },
    "E011": { # Old E010
        "message": "Unexpected end of file",
        "suggestion": "Statement appears incomplete"
    },

    # Validation Errors
    "E100": {
        "message": "Invalid anchor name",
        "suggestion": "Anchor names must be alphanumeric + underscore, or Unicode letters"
    },
    "E101": {
        "message": "Reserved name used",
        "suggestion": "Avoid reserved names: NULL, UNDEFINED, ANY, NONE, TRUE, FALSE, SYSTEM, GLOBAL, LOCAL"
    },
    "E102": {
        "message": "Anchor name too long",
        "suggestion": "Anchor names should be <= 64 characters"
    },
    "E103": {
        "message": "Invalid namespace format",
        "suggestion": "Namespace can contain letters, numbers, dots, and underscores"
    },
    "E104": {
        "message": "Invalid modifier key",
        "suggestion": "Use standard modifier keys or check spelling"
    },
    "E105": {
        "message": "Invalid modifier value type",
        "suggestion": "Check value type matches field requirements"
    },
    "E106": {
        "message": "Confidence value out of range",
        "suggestion": "Confidence must be between 0.0 and 1.0"
    },
    "E107": {
        "message": "Invalid rule type",
        "suggestion": "Valid rules: causal, correlative, logical, definitional, empirical"
    },
    "E108": {
        "message": "Invalid anchor type",
        "suggestion": "Valid types: Concept, Relational, Event, Entity, Name, Agent, Question, Verifier, PathSegment"
    },
    "E109": {
        "message": "Invalid path type",
        "suggestion": "Valid types: Semantic, Action, Cognitive, Causal, Inferential, Reflexive"
    },
    "E110": {
        "message": "Missing required modifier",
        "suggestion": "Some path types require specific modifiers"
    },
    "E111": {
        "message": "Conflicting modifiers",
        "suggestion": "Some modifier combinations are incompatible"
    },
    "E112": {
        "message": "Invalid datetime format",
        "suggestion": "Use ISO 8601: YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DD"
    },
    "E113": {
        "message": "Semantic inconsistency",
        "suggestion": "Statement semantics conflict with anchor types or path type"
    },
    "E114": {
        "message": "Circular reference detected",
        "suggestion": "Graph contains cycles that may cause issues"
    },
    "E115": {
        "message": "Dangling reference",
        "suggestion": "Anchor referenced but never defined"
    },

    # Serialization Errors
    "E200": {
        "message": "Serialization failed",
        "suggestion": "Check data structure is valid before serializing"
    },
    "E201": {
        "message": "Invalid JSON format",
        "suggestion": "JSON must be well-formed"
    },
    "E202": {
        "message": "Invalid JSON-LD format",
        "suggestion": "Check JSON-LD context and structure"
    },
    "E203": {
        "message": "Invalid RDF format",
        "suggestion": "Check RDF/Turtle syntax"
    },
    "E204": {
        "message": "Deserialization failed",
        "suggestion": "Input data may be corrupted or incompatible"
    },
    "E205": {
        "message": "Missing JSON-LD context",
        "suggestion": "JSON-LD requires @context field"
    },
    "E206": {
        "message": "Incompatible version",
        "suggestion": "Data was created with incompatible STL version"
    },
    "E207": {
        "message": "Encoding error",
        "suggestion": "Ensure UTF-8 encoding"
    },

    # Graph Errors
    "E300": {
        "message": "Graph construction failed",
        "suggestion": "Check statements are valid"
    },
    "E301": {
        "message": "Invalid edge",
        "suggestion": "Edge must connect two valid nodes"
    },
    "E302": {
        "message": "Invalid node",
        "suggestion": "Node must have valid anchor"
    },
    "E303": {
        "message": "Graph cycle detected",
        "suggestion": "Consider if cycle is intentional"
    },
    "E304": {
        "message": "Disconnected graph",
        "suggestion": "Graph has isolated components"
    },

    # File I/O Errors
    "E400": {
        "message": "File not found",
        "suggestion": "Check file path is correct"
    },
    "E401": {
        "message": "File read error",
        "suggestion": "Check file permissions and format"
    },
    "E402": {
        "message": "File write error",
        "suggestion": "Check write permissions and disk space"
    },
    "E403": {
        "message": "Permission denied",
        "suggestion": "Check file/directory permissions"
    },
    "E404": {
        "message": "Invalid file format",
        "suggestion": "Expected .stl file"
    },

    # Query Errors
    "E450": {
        "message": "Invalid query operator",
        "suggestion": "Valid operators: eq, gt, gte, lt, lte, ne, contains, startswith, in"
    },
    "E451": {
        "message": "Invalid pointer path",
        "suggestion": "Path segments must resolve to existing attributes"
    },
    "E452": {
        "message": "Statement index out of range",
        "suggestion": "Check document has enough statements for the given index"
    },
    "E453": {
        "message": "Query type error",
        "suggestion": "Comparison operator is incompatible with field value type"
    },
    # Diff/Patch Errors
    "E950": {
        "message": "Diff type error",
        "suggestion": "Input must be a ParseResult object"
    },
    "E951": {
        "message": "Patch statement not found",
        "suggestion": "The statement to remove or modify was not found in the target document"
    },
    "E952": {
        "message": "Patch conflict",
        "suggestion": "Patch conflicts with the current document state"
    },
    "E953": {
        "message": "Invalid patch operation",
        "suggestion": "The patch operation is not recognized or malformed"
    },
    # Reader Errors
    "E960": {
        "message": "Reader source error",
        "suggestion": "Check that the file exists and is readable"
    },
    "E961": {
        "message": "Reader parse error",
        "suggestion": "Line could not be parsed as a valid STL statement"
    },
    "E962": {
        "message": "Multi-line continuation overflow",
        "suggestion": "Statement continuation exceeds 20 lines — check for unclosed parentheses"
    },
}

WARNING_MESSAGES: Dict[str, Dict[str, str]] = {
    "W001": {
        "message": "Deprecated syntax",
        "suggestion": "Consider updating to current STL syntax"
    },
    "W002": {
        "message": "Unusual anchor name",
        "suggestion": "Anchor name contains unusual characters or patterns"
    },
    "W003": {
        "message": "Low confidence value",
        "suggestion": "Confidence < 0.5 may indicate uncertain relationship"
    },
    "W004": {
        "message": "Missing recommended modifier",
        "suggestion": "Consider adding modifiers like confidence or rule"
    },
    "W005": {
        "message": "Inconsistent style",
        "suggestion": "Use consistent arrow style (-> vs \u2192) throughout document"
    },
    "W006": {
        "message": "Duplicate statement",
        "suggestion": "This statement appears multiple times"
    },
    "W007": {
        "message": "Unused anchor",
        "suggestion": "Anchor defined but never used in paths"
    },
    "W008": {
        "message": "Complex namespace hierarchy",
        "suggestion": "Consider simplifying namespace structure"
    },
    "W009": {
        "message": "Performance warning",
        "suggestion": "Large graph may impact performance"
    },
}


# ========================================
# EXCEPTION CLASSES
# ========================================

class STLError(Exception):
    """Base exception for all STL parser errors.

    Attributes:
        code: Error code (e.g., "E001")
        message: Error message
        line: Line number where error occurred (optional)
        column: Column number where error occurred (optional)
        context: Additional context information (optional)
        suggestion: Suggestion for fixing the error (optional)
    """

    def __init__(
        self,
        code: str,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None
    ):
        self.code = code
        self.message = message
        self.line = line
        self.column = column
        self.context = context or {}
        self.suggestion = suggestion or self._get_default_suggestion(code)

        super().__init__(self._format_message())

    def _get_default_suggestion(self, code: str) -> Optional[str]:
        """Get default suggestion for error code."""
        error_info = ERROR_MESSAGES.get(code)
        return error_info.get("suggestion") if error_info else None

    def _format_message(self) -> str:
        """Format complete error message."""
        parts = [f"[{self.code}] {self.message}"]

        if self.line is not None:
            if self.column is not None:
                parts.append(f"at line {self.line}, column {self.column}")
            else:
                parts.append(f"at line {self.line}")

        if self.suggestion:
            parts.append(f"\nSuggestion: {self.suggestion}")

        return " ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        return {
            "code": self.code,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "context": self.context,
            "suggestion": self.suggestion
        }


class STLParseError(STLError):
    """Parse-time errors (E001-E099).

    Raised when STL text cannot be parsed due to syntax errors.
    """

    def __init__(
        self,
        code: str,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        token: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get("context", {})
        if token:
            context["token"] = token

        super().__init__(
            code=code,
            message=message,
            line=line,
            column=column,
            context=context,
            suggestion=kwargs.get("suggestion")
        )


class STLValidationError(STLError):
    """Validation errors (E100-E199).

    Raised when parsed STL is syntactically valid but semantically invalid.
    """

    def __init__(
        self,
        code: str,
        message: str,
        anchor: Optional[str] = None,
        modifier_key: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get("context", {})
        if anchor:
            context["anchor"] = anchor
        if modifier_key:
            context["modifier_key"] = modifier_key

        super().__init__(
            code=code,
            message=message,
            line=kwargs.get("line"),
            column=kwargs.get("column"),
            context=context,
            suggestion=kwargs.get("suggestion")
        )


class STLSerializationError(STLError):
    """Serialization errors (E200-E299).

    Raised when serialization or deserialization fails.
    """

    def __init__(
        self,
        code: str,
        message: str,
        format: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get("context", {})
        if format:
            context["format"] = format

        super().__init__(
            code=code,
            message=message,
            context=context,
            suggestion=kwargs.get("suggestion")
        )


class STLGraphError(STLError):
    """Graph construction errors (E300-E399).

    Raised when graph construction or analysis fails.
    """

    def __init__(
        self,
        code: str,
        message: str,
        node: Optional[str] = None,
        edge: Optional[tuple] = None,
        **kwargs
    ):
        context = kwargs.get("context", {})
        if node:
            context["node"] = node
        if edge:
            context["edge"] = edge

        super().__init__(
            code=code,
            message=message,
            context=context,
            suggestion=kwargs.get("suggestion")
        )


class STLQueryError(STLError):
    """Query errors (E450-E499).

    Raised when query operations fail (invalid operator, bad path, etc.).
    """
    pass


class STLFileError(STLError):
    """File I/O errors (E400-E449).

    Raised when file operations fail.
    """

    def __init__(
        self,
        code: str,
        message: str,
        file_path: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get("context", {})
        if file_path:
            context["file_path"] = file_path

        super().__init__(
            code=code,
            message=message,
            context=context,
            suggestion=kwargs.get("suggestion")
        )


class STLBuilderError(STLError):
    """Builder errors (E500-E599).

    Raised when programmatic STL statement building fails.
    """
    pass


class STLSchemaError(STLError):
    """Schema errors (E600-E699).

    Raised when schema parsing or validation fails.
    """
    pass


class STLLLMError(STLError):
    """LLM processing errors (E700-E799).

    Raised when LLM output cleaning or repair fails.
    """
    pass


class STLEmitterError(STLError):
    """Emitter errors (E800-E899).

    Raised when event emission fails.
    """
    pass


class STLDecayError(STLError):
    """Decay errors (E900-E949).

    Raised when confidence decay calculation fails.
    """
    pass


class STLDiffError(STLError):
    """Diff/Patch errors (E950-E959).

    Raised when diff computation or patch application fails.
    """
    pass


class STLReaderError(STLError):
    """Reader errors (E960-E969).

    Raised when streaming reader encounters unrecoverable errors.
    """

    def __init__(
        self,
        code: str,
        message: str,
        line_number: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            code=code,
            message=message,
            line=line_number,
            context=kwargs.get("context"),
            suggestion=kwargs.get("suggestion"),
        )
        self.line_number = line_number


class STLWarning:
    """Warning for non-critical issues.

    Unlike errors, warnings don't prevent processing but indicate
    potential issues or style violations.
    """

    def __init__(
        self,
        code: str,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None
    ):
        self.code = code
        self.message = message
        self.line = line
        self.column = column
        self.context = context or {}
        self.suggestion = suggestion or self._get_default_suggestion(code)

    def _get_default_suggestion(self, code: str) -> Optional[str]:
        """Get default suggestion for warning code."""
        warning_info = WARNING_MESSAGES.get(code)
        return warning_info.get("suggestion") if warning_info else None

    def to_dict(self) -> Dict[str, Any]:
        """Convert warning to dictionary format."""
        return {
            "code": self.code,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "context": self.context,
            "suggestion": self.suggestion
        }

    def __str__(self) -> str:
        """Format warning message."""
        parts = [f"[{self.code}] {self.message}"]

        if self.line is not None:
            if self.column is not None:
                parts.append(f"at line {self.line}, column {self.column}")
            else:
                parts.append(f"at line {self.line}")

        if self.suggestion:
            parts.append(f"\nSuggestion: {self.suggestion}")

        return " ".join(parts)


# ========================================
# ERROR FORMATTING UTILITIES
# ========================================

def format_error_context(
    text: str,
    line: int,
    column: int,
    context_lines: int = 2
) -> str:
    """Format error context with surrounding lines.

    Args:
        text: Source text
        line: Error line number (1-based)
        column: Error column number (1-based)
        context_lines: Number of context lines to show before/after

    Returns:
        Formatted context string with error marker

    Example:
        >>> format_error_context("line1\nline2\nerror here\nline4", 3, 7)
        1 | line1
        2 | line2
        3 | error here
          |       ^
        4 | line4
    """
    lines = text.split('\n')
    if line < 1 or line > len(lines):
        return ""

    # Calculate range
    start = max(0, line - 1 - context_lines)
    end = min(len(lines), line + context_lines)

    # Build output
    result = []
    max_line_num_width = len(str(end))

    for i in range(start, end):
        line_num = i + 1
        line_content = lines[i]

        # Format line number and content
        result.append(f"{line_num:>{max_line_num_width}} | {line_content}")

        # Add error marker
        if line_num == line:
            marker_padding = " " * max_line_num_width
            marker_position = " " * (column - 1) if column > 0 else ""
            result.append(f"{marker_padding} | {marker_position}^")

    return "\n".join(result)


def create_error_report(errors: List[STLError]) -> str:
    """Create formatted error report from list of errors.

    Args:
        errors: List of STLError instances

    Returns:
        Formatted error report string
    """
    if not errors:
        return "No errors"

    report = [f"Found {len(errors)} error(s):\n"]

    for i, error in enumerate(errors, 1):
        report.append(f"{i}. {error}")
        report.append("")  # Blank line between errors

    return "\n".join(report)


def create_warning_report(warnings: List[STLWarning]) -> str:
    """Create formatted warning report from list of warnings.

    Args:
        warnings: List of STLWarning instances

    Returns:
        Formatted warning report string
    """
    if not warnings:
        return "No warnings"

    report = [f"Found {len(warnings)} warning(s):\n"]

    for i, warning in enumerate(warnings, 1):
        report.append(f"{i}. {warning}")
        report.append("")  # Blank line between warnings

    return "\n".join(report)


# ========================================
# CONVENIENCE FUNCTIONS
# ========================================

def get_error_info(code: str) -> Optional[Dict[str, str]]:
    """Get error message and suggestion for error code.

    Args:
        code: Error code (e.g., "E001")

    Returns:
        Dict with 'message' and 'suggestion', or None if code not found
    """
    return ERROR_MESSAGES.get(code)


def get_warning_info(code: str) -> Optional[Dict[str, str]]:
    """Get warning message and suggestion for warning code.

    Args:
        code: Warning code (e.g., "W001")

    Returns:
        Dict with 'message' and 'suggestion', or None if code not found
    """
    return WARNING_MESSAGES.get(code)


def is_parse_error(code: str) -> bool:
    """Check if error code is a parse error."""
    return code.startswith("E0") and int(code[1:3]) < 100


def is_validation_error(code: str) -> bool:
    """Check if error code is a validation error."""
    return code.startswith("E1")


def is_serialization_error(code: str) -> bool:
    """Check if error code is a serialization error."""
    return code.startswith("E2")


def is_graph_error(code: str) -> bool:
    """Check if error code is a graph error."""
    return code.startswith("E3")


def is_file_error(code: str) -> bool:
    """Check if error code is a file I/O error."""
    return code.startswith("E4")
