# -*- coding: utf-8 -*-
"""
STL LLM — LLM Output Cleaning & Auto-Repair

Clean, repair, and validate raw LLM-generated STL output.
Three-stage pipeline: clean → repair → parse, with optional schema validation.

Compiled from: docs/stlc/stl_llm_v1.0.0.stlc.md

Usage:
    >>> from stl_parser.llm import validate_llm_output, clean, repair, prompt_template
    >>> result = validate_llm_output(raw_llm_text)
    >>> print(f"Valid: {result.is_valid}, Repairs: {len(result.repairs)}")
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from .models import Statement, ParseResult, ParseError, ParseWarning
from .parser import parse
from ._utils import (
    extract_stl_fences,
    merge_multiline_statements,
    is_stl_line,
)
from .errors import STLLLMError, ErrorCode


# ========================================
# DATA MODELS
# ========================================


class RepairAction(BaseModel):
    """Records a single repair action applied to the text."""

    type: str = Field(description="Repair type identifier")
    line: Optional[int] = Field(None, description="Line number where repair was applied")
    original: str = Field(description="Original text before repair")
    repaired: str = Field(description="Text after repair")
    description: str = Field(description="Human-readable description of the repair")


class LLMValidationResult(BaseModel):
    """Result of validating LLM-generated STL output."""

    statements: List[Statement] = Field(default_factory=list)
    errors: List[ParseError] = Field(default_factory=list)
    warnings: List[ParseWarning] = Field(default_factory=list)
    is_valid: bool = True
    repairs: List[RepairAction] = Field(default_factory=list)
    cleaned_text: str = ""
    original_text: str = ""
    schema_result: Optional[Any] = Field(None, description="SchemaValidationResult if schema provided")


# ========================================
# ARROW NORMALIZATION
# ========================================

# Common LLM arrow variants to normalize
_ARROW_VARIANTS = [
    ("\u2794", "->"),   # ➔
    ("\u27a1", "->"),   # ➡
    ("\u279c", "->"),   # ➜
    ("\u2b95", "->"),   # ⮕
    ("\uff1d\uff1e", "->"),  # ＝＞ (fullwidth =>)
    ("=>", "->"),
    ("- >", "->"),
    ("\u2014>", "->"),  # —> (em-dash arrow)
    ("\u2013>", "->"),  # –> (en-dash arrow)
]


# ========================================
# COMMON TYPO CORRECTIONS
# ========================================

_MODIFIER_TYPOS = {
    "confience": "confidence",
    "confindence": "confidence",
    "confidece": "confidence",
    "strenght": "strength",
    "stength": "strength",
    "timestap": "timestamp",
    "timestmp": "timestamp",
    "authro": "author",
    "auther": "author",
    "soruce": "source",
    "souce": "source",
    "certianty": "certainty",
    "certinty": "certainty",
    "conditionalty": "conditionality",
    "intensty": "intensity",
}

# Fields with [0.0, 1.0] range
_CLAMPABLE_FIELDS = {"confidence", "certainty", "strength", "intensity"}


# ========================================
# CLEAN STAGE
# ========================================


def clean(raw_text: str) -> Tuple[str, List[RepairAction]]:
    """Clean raw LLM output text for STL parsing.

    Applies: fence extraction, arrow normalization, whitespace fixing,
    multi-line merging, prose stripping.

    Args:
        raw_text: Raw LLM output text

    Returns:
        Tuple of (cleaned_text, list of repair actions)

    Example:
        >>> text, repairs = clean("```stl\\n[A] => [B]\\n```")
        >>> print(text)
        [A] -> [B]
    """
    repairs = []
    text = raw_text

    # 1. Extract from code fences if present
    if re.search(r"```(?:stl)?", text):
        fenced, _meta = extract_stl_fences(text)
        if fenced.strip():
            repairs.append(RepairAction(
                type="strip_fence",
                original=text[:80] + "..." if len(text) > 80 else text,
                repaired=fenced[:80] + "..." if len(fenced) > 80 else fenced,
                description="Extracted STL from code fences",
            ))
            text = fenced

    # 2. Normalize arrows
    for variant, replacement in _ARROW_VARIANTS:
        if variant in text:
            new_text = text.replace(variant, replacement)
            if new_text != text:
                repairs.append(RepairAction(
                    type="normalize_arrow",
                    original=variant,
                    repaired=replacement,
                    description=f"Replaced arrow variant '{variant}' with '{replacement}'",
                ))
                text = new_text

    # 3. Fix whitespace
    lines = text.split("\n")
    fixed_lines = []
    for line in lines:
        fixed = re.sub(r"  +", " ", line).rstrip()
        if fixed != line:
            repairs.append(RepairAction(
                type="fix_whitespace",
                original=line[:60],
                repaired=fixed[:60],
                description="Normalized whitespace",
            ))
        fixed_lines.append(fixed)
    text = "\n".join(fixed_lines)

    # 4. Merge multi-line statements
    merged = merge_multiline_statements(text)
    if merged != text:
        repairs.append(RepairAction(
            type="merge_multiline",
            original="(multi-line statements)",
            repaired="(merged to single lines)",
            description="Merged multi-line statements",
        ))
        text = merged

    # 5. Strip prose lines (keep STL and comments)
    lines = text.split("\n")
    stl_lines = []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        detection = is_stl_line(line)
        if detection["is_stl"] or detection["type"] == "comment":
            stl_lines.append(line)
        elif detection["type"] in ("natural_language", "markdown_link", "markdown_list", "markdown_quote"):
            repairs.append(RepairAction(
                type="strip_prose",
                line=i + 1,
                original=line[:60],
                repaired="(removed)",
                description=f"Removed non-STL line ({detection['type']})",
            ))

    text = "\n".join(stl_lines)

    return text, repairs


# ========================================
# REPAIR STAGE
# ========================================


def repair(text: str) -> Tuple[str, List[RepairAction]]:
    """Repair common structural errors in STL text.

    Applies: bracket fixing, string quoting, modifier prefix fixing,
    value clamping, typo correction.

    Args:
        text: Cleaned STL text that may still have structural errors

    Returns:
        Tuple of (repaired_text, list of repair actions)

    Example:
        >>> text, repairs = repair("[A] -> [B] mod(confidence=1.5)")
        >>> print(text)
        [A] -> [B] ::mod(confidence=1.0)
    """
    repairs = []
    lines = text.split("\n")
    repaired_lines = []

    for i, line in enumerate(lines):
        original = line

        # 1. Fix missing :: prefix on mod()
        line = _fix_mod_prefix(line, i + 1, repairs)

        # 2. Fix missing brackets on anchors
        line = _fix_missing_brackets(line, i + 1, repairs)

        # 3. Fix unquoted string values in modifiers
        line = _fix_unquoted_strings(line, i + 1, repairs)

        # 4. Clamp out-of-range numeric values
        line = _clamp_values(line, i + 1, repairs)

        # 5. Fix common typos in modifier keys
        line = _fix_typos(line, i + 1, repairs)

        repaired_lines.append(line)

    return "\n".join(repaired_lines), repairs


def _fix_mod_prefix(line: str, line_num: int, repairs: List[RepairAction]) -> str:
    """Fix missing :: prefix on mod()."""
    # Match 'mod(' not preceded by '::'
    pattern = r"(?<!:)(?<!:)\bmod\("
    if re.search(pattern, line):
        new_line = re.sub(pattern, "::mod(", line)
        if new_line != line:
            repairs.append(RepairAction(
                type="fix_mod_prefix",
                line=line_num,
                original="mod(",
                repaired="::mod(",
                description="Added :: prefix to mod()",
            ))
            return new_line
    return line


def _fix_missing_brackets(line: str, line_num: int, repairs: List[RepairAction]) -> str:
    """Fix missing brackets around anchor names."""
    # Pattern: word(s) -> [Target] or [Source] -> word(s)
    # Only fix if there's an arrow and at least one bracket pair

    if "->" not in line and "\u2192" not in line:
        return line

    arrow = "->" if "->" in line else "\u2192"
    parts = line.split(arrow, 1)
    if len(parts) != 2:
        return line

    left = parts[0].strip()
    right_full = parts[1]

    # Check right side for ::mod
    right_parts = right_full.split("::mod", 1)
    right = right_parts[0].strip()
    mod_suffix = "::mod" + right_parts[1] if len(right_parts) > 1 else ""

    changed = False

    # Fix left side if no brackets
    if left and not left.startswith("["):
        # Only fix if it looks like an anchor name (word chars, possibly with namespace)
        if re.match(r"^[\w:\-]+$", left):
            new_left = f"[{left}]"
            repairs.append(RepairAction(
                type="add_brackets",
                line=line_num,
                original=left,
                repaired=new_left,
                description=f"Added brackets to source anchor '{left}'",
            ))
            left = new_left
            changed = True

    # Fix right side if no brackets
    if right and not right.startswith("["):
        if re.match(r"^[\w:\-]+$", right):
            new_right = f"[{right}]"
            repairs.append(RepairAction(
                type="add_brackets",
                line=line_num,
                original=right,
                repaired=new_right,
                description=f"Added brackets to target anchor '{right}'",
            ))
            right = new_right
            changed = True

    if changed:
        if mod_suffix:
            return f"{left} {arrow} {right} {mod_suffix}"
        return f"{left} {arrow} {right}"

    return line


def _fix_unquoted_strings(line: str, line_num: int, repairs: List[RepairAction]) -> str:
    """Quote unquoted string values in ::mod()."""
    # Find ::mod(...) content
    mod_match = re.search(r"::mod\((.+)\)", line)
    if not mod_match:
        return line

    mod_content = mod_match.group(1)
    new_pairs = []
    changed = False

    for pair in re.finditer(r"(\w+)\s*=\s*([^,\)]+)", mod_content):
        key = pair.group(1)
        val = pair.group(2).strip()

        # Skip already quoted, numeric, or boolean
        if val.startswith('"') or val.startswith("'"):
            new_pairs.append(f'{key}={val}')
            continue
        if re.match(r"^-?\d+\.?\d*$", val):
            new_pairs.append(f"{key}={val}")
            continue
        if val.lower() in ("true", "false"):
            new_pairs.append(f"{key}={val}")
            continue

        # Needs quoting
        repairs.append(RepairAction(
            type="quote_string",
            line=line_num,
            original=f"{key}={val}",
            repaired=f'{key}="{val}"',
            description=f"Quoted unquoted string value for '{key}'",
        ))
        new_pairs.append(f'{key}="{val}"')
        changed = True

    if changed:
        new_mod = "::mod(" + ", ".join(new_pairs) + ")"
        prefix = line[:mod_match.start()]
        suffix = line[mod_match.end():]
        return prefix + new_mod + suffix

    return line


def _clamp_values(line: str, line_num: int, repairs: List[RepairAction]) -> str:
    """Clamp out-of-range numeric values for known [0.0, 1.0] fields."""
    for field in _CLAMPABLE_FIELDS:
        pattern = rf"({field}\s*=\s*)(-?\d+\.?\d*)"
        match = re.search(pattern, line)
        if match:
            val = float(match.group(2))
            if val > 1.0:
                clamped = "1.0"
                repairs.append(RepairAction(
                    type="clamp_value",
                    line=line_num,
                    original=f"{field}={match.group(2)}",
                    repaired=f"{field}={clamped}",
                    description=f"Clamped {field} from {val} to {clamped}",
                ))
                line = line[:match.start()] + f"{field}={clamped}" + line[match.end():]
            elif val < 0.0:
                clamped = "0.0"
                repairs.append(RepairAction(
                    type="clamp_value",
                    line=line_num,
                    original=f"{field}={match.group(2)}",
                    repaired=f"{field}={clamped}",
                    description=f"Clamped {field} from {val} to {clamped}",
                ))
                line = line[:match.start()] + f"{field}={clamped}" + line[match.end():]
    return line


def _fix_typos(line: str, line_num: int, repairs: List[RepairAction]) -> str:
    """Fix common typos in modifier keys."""
    # Only fix within ::mod() context
    mod_match = re.search(r"::mod\((.+)\)", line)
    if not mod_match:
        return line

    mod_content = mod_match.group(1)
    new_content = mod_content

    for typo, correct in _MODIFIER_TYPOS.items():
        pattern = rf"\b{typo}\b"
        if re.search(pattern, new_content):
            repairs.append(RepairAction(
                type="fix_typo",
                line=line_num,
                original=typo,
                repaired=correct,
                description=f"Fixed typo: '{typo}' → '{correct}'",
            ))
            new_content = re.sub(pattern, correct, new_content)

    if new_content != mod_content:
        prefix = line[:mod_match.start()]
        suffix = line[mod_match.end():]
        return prefix + "::mod(" + new_content + ")" + suffix

    return line


# ========================================
# MAIN PIPELINE
# ========================================


def validate_llm_output(
    raw_text: str,
    schema=None,
) -> LLMValidationResult:
    """Full pipeline: clean → repair → parse → optional schema validation.

    Args:
        raw_text: Raw LLM output text
        schema: Optional STLSchema for schema validation

    Returns:
        LLMValidationResult with statements, errors, repairs

    Example:
        >>> result = validate_llm_output("```stl\\n[A] => [B]\\n```")
        >>> print(result.is_valid)
        True
    """
    # Stage 1: Clean
    cleaned_text, clean_repairs = clean(raw_text)

    # Stage 2: Repair
    repaired_text, repair_repairs = repair(cleaned_text)

    # Stage 3: Parse
    parse_result = parse(repaired_text)

    # Stage 4: Optional schema validation
    schema_result = None
    if schema is not None:
        try:
            from .schema import validate_against_schema
            schema_result = validate_against_schema(parse_result, schema)
        except ImportError:
            pass

    # Compile result
    all_repairs = clean_repairs + repair_repairs

    return LLMValidationResult(
        statements=parse_result.statements,
        errors=parse_result.errors,
        warnings=parse_result.warnings,
        is_valid=parse_result.is_valid and (schema_result is None or schema_result.is_valid),
        repairs=all_repairs,
        cleaned_text=repaired_text,
        original_text=raw_text,
        schema_result=schema_result,
    )


# ========================================
# PROMPT TEMPLATE
# ========================================

_BASE_TEMPLATE = """Generate valid STL (Semantic Tension Language) statements using this syntax:

[Source_Anchor] -> [Target_Anchor] ::mod(key=value, key=value, ...)

Rules:
- Anchors: Use [BracketedNames] with PascalCase or underscore_separation
- Arrows: Use -> between source and target
- Modifiers: Optional, prefixed with ::mod(...)
- String values must be quoted: rule="causal"
- Numeric values: confidence=0.95 (no quotes)
- Boolean values: deterministic=true (no quotes)

Common modifier keys:
- confidence: float [0.0-1.0] — how certain is this relation
- rule: string — "causal", "logical", "empirical", "definitional"
- source: string — reference URI or citation
- author: string — who established this relation
- timestamp: string — ISO 8601 datetime
- strength: float [0.0-1.0] — causal strength
- domain: string — knowledge domain

Example:
[Theory_Relativity] -> [Prediction_TimeDilation] ::mod(rule="logical", confidence=0.99)
"""


def prompt_template(schema=None) -> str:
    """Generate an STL instruction prompt for LLMs.

    Args:
        schema: Optional STLSchema to add schema-specific constraints

    Returns:
        Prompt template string

    Example:
        >>> prompt = prompt_template()
        >>> # Use as system message for LLM
    """
    template = _BASE_TEMPLATE

    if schema is not None:
        template += "\n\nSchema-specific constraints:\n"
        template += f"Schema: {schema.name} v{schema.version}\n"

        if schema.namespace:
            template += f"- Default namespace: {schema.namespace}\n"

        if schema.modifier.required_fields:
            template += f"- Required modifier fields: {', '.join(schema.modifier.required_fields)}\n"

        for field_name, fc in schema.modifier.field_constraints.items():
            if fc.type == "enum" and fc.enum_values:
                template += f"- {field_name}: must be one of {fc.enum_values}\n"
            elif fc.type in ("float", "integer"):
                parts = [f"- {field_name}: {fc.type}"]
                if fc.min_value is not None:
                    parts.append(f"min={fc.min_value}")
                if fc.max_value is not None:
                    parts.append(f"max={fc.max_value}")
                template += " ".join(parts) + "\n"

        if schema.source_anchor.pattern:
            template += f"- Source anchor names must match: /{schema.source_anchor.pattern}/\n"

        if schema.target_anchor.pattern:
            template += f"- Target anchor names must match: /{schema.target_anchor.pattern}/\n"

    return template
