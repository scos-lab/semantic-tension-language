# -*- coding: utf-8 -*-
"""
STL Parser Internal Utilities

Shared utility functions used by parser.py and other modules.
Extracted from parser.py for reuse by llm.py and other new modules.

This module is internal (prefixed with _) and should not be imported
directly by users. The public API is in parser.py and __init__.py.
"""

import re
from typing import List, Dict, Any

from .models import ParseResult


# ========================================
# STL LINE DETECTION
# ========================================

def is_stl_line(line: str) -> Dict[str, Any]:
    """Detect if a line is likely an STL statement with confidence score.

    Uses hierarchical detection based on STL syntax features:
    - Brackets [] (required)
    - Arrow -> or → (required)
    - Modifier ::mod(...) (optional, increases confidence)

    Args:
        line: Single line of text to analyze

    Returns:
        Dictionary with detection results:
        {
            'is_stl': bool,
            'confidence': float (0.0-1.0),
            'type': str,
            'features': dict
        }

    Example:
        >>> is_stl_line('[A] -> [B] ::mod(confidence=0.9)')
        {'is_stl': True, 'confidence': 0.99, 'type': 'complete_stl', ...}
        >>> is_stl_line('[A] -> [B]')
        {'is_stl': True, 'confidence': 0.95, 'type': 'minimal_stl', ...}
        >>> is_stl_line('[Just a note]')
        {'is_stl': False, 'confidence': 0.0, 'type': 'not_stl', ...}
    """
    stripped = line.strip()

    # Check for empty line first
    if not stripped:
        return {'is_stl': False, 'confidence': 0.0, 'type': 'empty', 'features': {}}

    # Extract features
    features = {
        'has_brackets': '[' in stripped and ']' in stripped,
        'bracket_count': stripped.count('['),
        'has_arrow': '->' in stripped or '\u2192' in stripped,
        'has_modifier': '::mod(' in stripped,
        'is_comment': stripped.startswith('#'),
        'is_markdown_link': bool(re.match(r'\[.+?\]\(.+?\)', stripped)),
        'is_markdown_list': stripped.startswith(('-', '*', '+')) and not stripped.startswith('->'),
        'is_markdown_quote': stripped.startswith('>'),
    }

    # Priority 1: Exclude non-STL patterns
    if features['is_comment']:
        return {'is_stl': False, 'confidence': 0.0, 'type': 'comment', 'features': features}

    if features['is_markdown_link']:
        return {'is_stl': False, 'confidence': 0.0, 'type': 'markdown_link', 'features': features}

    if features['is_markdown_list']:
        return {'is_stl': False, 'confidence': 0.0, 'type': 'markdown_list', 'features': features}

    if features['is_markdown_quote']:
        return {'is_stl': False, 'confidence': 0.0, 'type': 'markdown_quote', 'features': features}

    # Priority 2: Check for STL required features
    if features['has_brackets'] and features['has_arrow']:
        # At least 2 brackets required for valid STL: [A] -> [B]
        if features['bracket_count'] >= 2:
            if features['has_modifier']:
                # Complete STL with modifier
                return {
                    'is_stl': True,
                    'confidence': 0.99,
                    'type': 'complete_stl',
                    'features': features
                }
            else:
                # Minimal STL without modifier
                return {
                    'is_stl': True,
                    'confidence': 0.95,
                    'type': 'minimal_stl',
                    'features': features
                }
        else:
            # Has arrow but not enough brackets - likely syntax error
            return {
                'is_stl': False,
                'confidence': 0.2,
                'type': 'possible_syntax_error',
                'features': features
            }

    # Distinguish natural language from other non-STL
    # Natural language typically has no STL markers at all
    if not features['has_brackets'] and not features['has_arrow']:
        return {'is_stl': False, 'confidence': 0.0, 'type': 'natural_language', 'features': features}

    # Other non-STL cases
    return {'is_stl': False, 'confidence': 0.0, 'type': 'not_stl', 'features': features}


# ========================================
# MARKDOWN CODE FENCE EXTRACTION
# ========================================

def extract_stl_fences(text: str) -> tuple[str, Dict[str, Any]]:
    """Extract STL code from Markdown code fences.

    Looks for ```stl ... ``` blocks and extracts their content.

    Args:
        text: Full text containing potential code fences

    Returns:
        Tuple of (extracted_stl_text, metadata)

    Example:
        >>> text = "# Doc\\n```stl\\n[A] -> [B]\\n```\\nMore text"
        >>> stl, meta = extract_stl_fences(text)
        >>> print(stl)
        [A] -> [B]
    """
    lines = text.split('\n')
    stl_lines = []
    line_mapping = []
    in_fence = False
    fence_count = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped == '```stl' or stripped.startswith('```stl '):
            in_fence = True
            fence_count += 1
        elif stripped == '```' and in_fence:
            in_fence = False
        elif in_fence:
            stl_lines.append(line)
            line_mapping.append(i + 1)  # 1-based line numbers

    metadata = {
        'format': 'fenced',
        'total_lines': len(lines),
        'stl_lines': len(stl_lines),
        'fence_count': fence_count,
        'line_mapping': line_mapping
    }

    return '\n'.join(stl_lines), metadata


# ========================================
# HEURISTIC EXTRACTION
# ========================================

def extract_stl_heuristic(text: str) -> tuple[str, Dict[str, Any]]:
    """Extract STL statements using heuristic detection.

    Scans each line and uses pattern matching to identify likely STL statements.
    Based on detection of brackets, arrows, and modifiers.

    Args:
        text: Full text with mixed content

    Returns:
        Tuple of (extracted_stl_text, metadata)

    Example:
        >>> text = "# Intro\\n[A] -> [B]\\nSome text\\n[C] -> [D] ::mod(confidence=0.9)"
        >>> stl, meta = extract_stl_heuristic(text)
        >>> print(meta['stl_lines'])
        2
    """
    lines = text.split('\n')
    stl_lines = []
    line_mapping = []
    detection_stats = {
        'complete_stl': 0,
        'minimal_stl': 0,
        'syntax_errors': 0,
        'not_stl': 0
    }

    for i, line in enumerate(lines):
        detection = is_stl_line(line)

        if detection['is_stl']:
            stl_lines.append(line)
            line_mapping.append(i + 1)
            detection_stats[detection['type']] += 1
        elif detection['type'] == 'comment':
            # Preserve comments in output but don't count as STL
            stl_lines.append(line)
            line_mapping.append(i + 1)
        elif detection['type'] == 'possible_syntax_error':
            detection_stats['syntax_errors'] += 1
        else:
            detection_stats['not_stl'] += 1

    # Count only actual STL lines (excluding comments)
    actual_stl_count = detection_stats['complete_stl'] + detection_stats['minimal_stl']

    metadata = {
        'format': 'heuristic',
        'total_lines': len(lines),
        'stl_lines': actual_stl_count,
        'line_mapping': line_mapping,
        'detection_stats': detection_stats
    }

    return '\n'.join(stl_lines), metadata


# ========================================
# PURE STL DETECTION
# ========================================

def is_pure_stl(text: str) -> bool:
    """Check if text appears to be pure STL without mixed content.

    A file is considered pure STL if all non-empty, non-comment lines
    appear to be STL statements and there are no Markdown-specific patterns.

    Args:
        text: Text to analyze

    Returns:
        True if likely pure STL, False otherwise
    """
    lines = text.split('\n')

    # Check for any Markdown-specific patterns
    has_stl_before_header = False
    for i, line in enumerate(lines):
        detection = is_stl_line(line)

        # Track if we've seen STL statements
        if detection['is_stl']:
            has_stl_before_header = True

        # If we find Markdown patterns (not plain comments), it's not pure STL
        if detection['type'] in ('markdown_link', 'markdown_list', 'markdown_quote'):
            return False

        # Detect Markdown headers (not STL comments)
        stripped = line.strip()
        if stripped.startswith('# ') and not stripped.startswith('##'):
            after_hash = stripped[2:].strip()
            if len(after_hash) < 50 and after_hash and after_hash[0].isupper():
                if not has_stl_before_header:
                    if i < 3:
                        return False

    # Filter to non-empty, non-comment lines
    non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]

    if not non_empty_lines:
        return True  # Empty or comment-only file

    # Check first few lines to determine
    sample_size = min(5, len(non_empty_lines))
    stl_count = 0

    for line in non_empty_lines[:sample_size]:
        detection = is_stl_line(line)
        if detection['is_stl']:
            stl_count += 1

    # If most sampled lines are STL, treat as pure STL
    return stl_count >= sample_size * 0.8


# ========================================
# AUTO-EXTRACTION
# ========================================

def auto_extract_stl(text: str, mode: str = 'auto') -> tuple[str, Dict[str, Any]]:
    """Automatically extract STL statements from mixed content.

    Supports multiple extraction modes:
    - 'auto': Automatically detect best strategy
    - 'fenced': Extract from ```stl code fences
    - 'heuristic': Use pattern matching
    - 'strict': No extraction (treat as pure STL)

    Args:
        text: Input text (may contain mixed content)
        mode: Extraction mode

    Returns:
        Tuple of (extracted_stl_text, metadata)

    Example:
        >>> text = "```stl\\n[A] -> [B]\\n```"
        >>> stl, meta = auto_extract_stl(text, mode='auto')
        >>> print(meta['format'])
        fenced
    """
    # Auto-detect mode
    if mode == 'auto':
        if re.search(r'^\s*```stl', text, re.MULTILINE):
            mode = 'fenced'
        elif is_pure_stl(text):
            mode = 'pure_stl'
        else:
            mode = 'heuristic'

    # Extract based on mode
    if mode == 'fenced':
        return extract_stl_fences(text)
    elif mode == 'heuristic':
        return extract_stl_heuristic(text)
    elif mode == 'pure_stl':
        metadata = {
            'format': 'pure_stl',
            'total_lines': len(text.split('\n')),
            'stl_lines': len(text.split('\n')),
            'line_mapping': list(range(1, len(text.split('\n')) + 1))
        }
        return text, metadata
    else:  # strict mode (explicit)
        metadata = {
            'format': 'strict',
            'total_lines': len(text.split('\n')),
            'stl_lines': len(text.split('\n')),
            'line_mapping': list(range(1, len(text.split('\n')) + 1))
        }
        return text, metadata


# ========================================
# MULTI-LINE STATEMENT MERGING
# ========================================

def merge_multiline_statements(text: str) -> str:
    """Merge multi-line STL statements into single lines.

    LLMs often format STL statements across multiple lines for readability:
        [A] -> [B] ::mod(
          rule="empirical",
          confidence=0.9
        )

    This function detects such multi-line statements (identified by unmatched
    parentheses) and merges them into single lines for parsing.

    Args:
        text: Input text that may contain multi-line statements

    Returns:
        Text with multi-line statements merged into single lines

    Example:
        >>> text = '[A] -> [B] ::mod(\\n  rule="test"\\n)'
        >>> merge_multiline_statements(text)
        '[A] -> [B] ::mod( rule="test" )'
    """
    lines = text.split('\n')
    merged = []
    buffer = []
    paren_depth = 0
    in_multiline = False

    for line in lines:
        stripped = line.strip()

        # Skip comment lines - don't count their parentheses
        if stripped.startswith('#'):
            if not in_multiline:
                merged.append(line)
            else:
                buffer.append(line)
            continue

        open_parens = line.count('(')
        close_parens = line.count(')')

        if in_multiline:
            buffer.append(line)
            paren_depth += open_parens - close_parens

            if paren_depth <= 0:
                merged_line = ' '.join(l.strip() for l in buffer if not l.strip().startswith('#'))
                merged.append(merged_line)
                buffer = []
                in_multiline = False
                paren_depth = 0
        else:
            paren_depth = open_parens - close_parens

            if paren_depth > 0:
                in_multiline = True
                buffer.append(line)
            else:
                merged.append(line)

    # Handle any unclosed multi-line statements (malformed input)
    if buffer:
        merged_line = ' '.join(l.strip() for l in buffer if not l.strip().startswith('#'))
        merged.append(merged_line)

    return '\n'.join(merged)


# ========================================
# LINE NUMBER REMAPPING
# ========================================

def remap_line_numbers(result: ParseResult, line_mapping: List[int]) -> ParseResult:
    """Remap line numbers in parse errors/warnings to original file line numbers.

    When STL is extracted from mixed content, the line numbers in parse errors
    refer to the extracted text. This function remaps them to the original file.

    Args:
        result: ParseResult with line numbers from extracted text
        line_mapping: List mapping extracted line numbers to original line numbers

    Returns:
        ParseResult with remapped line numbers
    """
    if not line_mapping:
        return result

    # Remap error line numbers
    for error in result.errors:
        if error.line is not None and 0 < error.line <= len(line_mapping):
            error.line = line_mapping[error.line - 1]

    # Remap warning line numbers
    for warning in result.warnings:
        if warning.line is not None and 0 < warning.line <= len(line_mapping):
            warning.line = line_mapping[warning.line - 1]

    # Remap statement line numbers if they exist
    for statement in result.statements:
        if statement.line is not None and 0 < statement.line <= len(line_mapping):
            statement.line = line_mapping[statement.line - 1]

    return result


# ========================================
# MARKDOWN ESCAPE REMOVAL
# ========================================

def remove_markdown_escapes(text: str) -> str:
    """Remove Markdown escape characters from STL text, protecting quoted strings.

    Markdown editors automatically escape special characters used in STL syntax
    (like [, ], ->, (, ), ", ', _) with backslashes. This function removes those
    escapes to allow proper parsing, but carefully preserves backslashes inside
    quoted strings.

    Args:
        text: Raw text that may contain Markdown escapes

    Returns:
        Text with Markdown escapes removed

    Example:
        >>> remove_markdown_escapes(r'\\[Coffee\\]')
        '[Coffee]'
    """
    pattern = r'("[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')|\\([\[\]\-\>\:\(\)\"\'\._\*\#\{\}\|])'

    def replace(match):
        if match.group(1):
            return match.group(1)
        else:
            return match.group(2)

    return re.sub(pattern, replace, text)


# ========================================
# ANCHOR NAME SANITIZATION
# ========================================


def sanitize_anchor_name(name: str) -> str:
    """Sanitize a string for use as an STL anchor name.

    Replaces characters invalid in STL anchors (hyphens, dots, slashes,
    special chars) with underscores, collapses runs, and strips edges.

    Args:
        name: Raw string (e.g. file path, package name, version string)

    Returns:
        A valid STL anchor name, or "Unknown" if the result would be empty.

    Examples:
        >>> sanitize_anchor_name("stl-parser")
        'stl_parser'
        >>> sanitize_anchor_name("src/core.py")
        'src_core_py'
        >>> sanitize_anchor_name("黄帝内经")
        '黄帝内经'
    """
    # Keep only characters valid in STL anchors (word chars + CJK + Arabic)
    result = re.sub(r'[^A-Za-z0-9_\u4e00-\u9fff\u0600-\u06ff]', '_', name)
    # Collapse multiple underscores
    result = re.sub(r'_+', '_', result)
    # Strip leading/trailing underscores
    result = result.strip('_')
    return result if result else "Unknown"
