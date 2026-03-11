"""
STL Parser - Semantic Tension Language Parser

A Python parser for the Semantic Tension Language (STL) specification.
"""

from .parser import parse, parse_file
from .models import (
    ParseResult,
    Statement,
    Anchor,
    Modifier,
    AnchorType,
    PathType,
)
from .validator import validate_parse_result
from .serializer import to_json, to_dict, from_json, from_dict, to_stl
from .graph import STLGraph
from .analyzer import STLAnalyzer
from .errors import STLError, STLParseError, STLWarning

# New modules (Priority 1 Tooling)
from .builder import stl, stl_doc, StatementBuilder
from .schema import load_schema, validate_against_schema, STLSchema, to_pydantic, from_pydantic
from .llm import clean, repair, validate_llm_output, prompt_template, LLMValidationResult
from .emitter import STLEmitter

# Priority 2 Tooling
from .decay import effective_confidence, decay_report, filter_by_confidence, DecayConfig, DecayReport

# Query
from .query import find, find_all, filter_statements, select, stl_pointer

# Diff/Patch
from .diff import stl_diff, stl_patch, diff_to_text, diff_to_dict, STLDiff

# Streaming I/O
from .reader import stream_parse, STLReader, ReaderStats

# Utilities (public)
from ._utils import sanitize_anchor_name

__version__ = "1.7.0"

__all__ = [
    # Main parsing functions
    "parse",
    "parse_file",
    # Data models
    "ParseResult",
    "Statement",
    "Anchor",
    "Modifier",
    "AnchorType",
    "PathType",
    # Validation
    "validate_parse_result",
    # Serialization
    "to_json",
    "to_dict",
    "from_json",
    "from_dict",
    "to_stl",
    # Graph and analysis
    "STLGraph",
    "STLAnalyzer",
    # Errors
    "STLError",
    "STLParseError",
    "STLWarning",
    # Builder (new)
    "stl",
    "stl_doc",
    "StatementBuilder",
    # Schema (new)
    "load_schema",
    "validate_against_schema",
    "STLSchema",
    "to_pydantic",
    "from_pydantic",
    # LLM (new)
    "clean",
    "repair",
    "validate_llm_output",
    "prompt_template",
    "LLMValidationResult",
    # Emitter (new)
    "STLEmitter",
    # Decay (P2)
    "effective_confidence",
    "decay_report",
    "filter_by_confidence",
    "DecayConfig",
    "DecayReport",
    # Query
    "find",
    "find_all",
    "filter_statements",
    "select",
    "stl_pointer",
    # Diff/Patch
    "stl_diff",
    "stl_patch",
    "diff_to_text",
    "diff_to_dict",
    "STLDiff",
    # Streaming I/O
    "stream_parse",
    "STLReader",
    "ReaderStats",
    # Utilities
    "sanitize_anchor_name",
]
