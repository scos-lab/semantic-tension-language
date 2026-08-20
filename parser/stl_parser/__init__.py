"""STL Parser - Semantic Tension Language Parser

A Python parser for the Semantic Tension Language (STL) specification.
"""

from importlib.metadata import PackageNotFoundError, version

# Utilities (public)
from ._utils import sanitize_anchor_name
from .analyzer import STLAnalyzer

# New modules (Priority 1 Tooling)
from .builder import StatementBuilder, stl, stl_doc

# Priority 2 Tooling
from .decay import (
    DecayConfig,
    DecayReport,
    decay_report,
    effective_confidence,
    filter_by_confidence,
)

# Diff/Patch
from .diff import STLDiff, diff_to_dict, diff_to_text, stl_diff, stl_patch
from .emitter import STLEmitter
from .errors import STLError, STLParseError, STLWarning
from .graph import STLGraph
from .llm import LLMValidationResult, clean, prompt_template, repair, validate_llm_output
from .models import (
    Anchor,
    AnchorType,
    Modifier,
    ParseResult,
    PathType,
    Statement,
)
from .parser import parse, parse_file

# Query
from .query import filter_statements, find, find_all, select, stl_pointer

# Streaming I/O
from .reader import ReaderStats, STLReader, stream_parse
from .schema import (
    STLSchema,
    from_pydantic,
    load_profile,
    load_schema,
    to_pydantic,
    validate_against_profiles,
    validate_against_schema,
)
from .serializer import from_dict, from_json, to_dict, to_json, to_stl
from .validator import validate_parse_result

try:
    __version__ = version("stl-parser")
except PackageNotFoundError:
    __version__ = "1.7.3"

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
    "load_profile",
    "validate_against_schema",
    "validate_against_profiles",
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
