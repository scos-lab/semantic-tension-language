# -*- coding: utf-8 -*-
"""
STL Confidence Decay — Query-Time Confidence Decay

Compute effective confidence based on statement age using exponential
half-life decay. Read-only: never modifies original Statement data.

Compiled from: docs/stlc/stl_decay_v1.0.0.stlc.md

Usage:
    >>> from stl_parser.decay import effective_confidence, decay_report
    >>> eff = effective_confidence(statement, half_life_days=30)
    >>> report = decay_report(parse_result)
"""

import math
import statistics as stats_module
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .models import Statement, ParseResult
from .errors import STLDecayError, ErrorCode


# ========================================
# DATA MODELS
# ========================================


class DecayConfig(BaseModel):
    """Configuration for confidence decay calculations."""

    half_life_days: float = Field(
        30.0, gt=0, description="Days for confidence to halve"
    )
    min_threshold: float = Field(
        0.01, ge=0.0, le=1.0, description="Floor — below this, effective confidence is 0.0"
    )
    reference_time: Optional[datetime] = Field(
        None, description="Reference 'now' for age calculation (default: utcnow)"
    )


class DecayedStatement(BaseModel):
    """Per-statement decay result wrapping the original statement."""

    statement: Statement
    original_confidence: Optional[float] = None
    effective_confidence: Optional[float] = None
    age_days: Optional[float] = None
    decay_ratio: Optional[float] = None


class DecayReport(BaseModel):
    """Batch decay analysis result."""

    decayed_statements: List[DecayedStatement] = Field(default_factory=list)
    config: DecayConfig = Field(default_factory=DecayConfig)
    total_statements: int = 0
    statements_with_timestamp: int = 0
    statements_decayed: int = 0
    summary: Dict[str, Any] = Field(default_factory=dict)


# ========================================
# TIMESTAMP PARSING
# ========================================


def _parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Parse an ISO 8601 timestamp string to a datetime object.

    Handles common formats:
    - 2026-01-15T10:00:00Z
    - 2026-01-15T10:00:00+00:00
    - 2026-01-15

    Returns None on parse failure (graceful degradation).
    """
    if not ts_str:
        return None

    # Normalize trailing Z to +00:00 for fromisoformat
    normalized = ts_str.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(normalized)
        # If naive (no timezone), assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


# ========================================
# CORE FUNCTIONS
# ========================================


def effective_confidence(
    statement: Statement,
    half_life_days: float = 30.0,
    reference_time: Optional[datetime] = None,
) -> Optional[float]:
    """Compute a statement's effective confidence after time-based decay.

    Uses exponential half-life decay: effective = confidence * 0.5^(age / half_life).
    Read-only — never modifies the original statement.

    Args:
        statement: The statement to compute decay for.
        half_life_days: Days for confidence to halve (must be > 0).
        reference_time: "Now" for age calculation (default: utcnow).

    Returns:
        Effective confidence (float), or None if statement has no confidence.

    Raises:
        STLDecayError: If half_life_days <= 0.
    """
    if half_life_days <= 0:
        raise STLDecayError(
            code=ErrorCode.E900_DECAY_ERROR,
            message="half_life_days must be positive",
        )

    # No modifiers or no confidence → None
    if statement.modifiers is None or statement.modifiers.confidence is None:
        return None

    confidence = statement.modifiers.confidence

    # No timestamp → return original (no decay possible)
    if statement.modifiers.timestamp is None:
        return confidence

    # Parse timestamp
    parsed_ts = _parse_timestamp(statement.modifiers.timestamp)
    if parsed_ts is None:
        # Graceful degradation: can't parse → return original
        return confidence

    # Calculate age
    if reference_time is None:
        reference_time = datetime.now(timezone.utc)

    age_seconds = (reference_time - parsed_ts).total_seconds()
    age_days = age_seconds / 86400.0

    # Future timestamp or zero age → no decay
    if age_days <= 0:
        return confidence

    # Exponential decay
    effective = confidence * math.pow(0.5, age_days / half_life_days)

    # Clamp
    return max(0.0, min(1.0, effective))


def decay_report(
    parse_result: ParseResult,
    config: Optional[DecayConfig] = None,
) -> DecayReport:
    """Compute decay analysis for all statements in a ParseResult.

    Args:
        parse_result: The parsed document to analyze.
        config: Decay configuration (default: DecayConfig()).

    Returns:
        DecayReport with per-statement results and summary statistics.
    """
    if config is None:
        config = DecayConfig()

    reference_time = config.reference_time or datetime.now(timezone.utc)

    decayed_statements: List[DecayedStatement] = []
    effective_values: List[float] = []
    statements_with_ts = 0
    statements_decayed = 0

    for stmt in parse_result.statements:
        original_conf = None
        eff_conf = None
        age_days = None
        decay_ratio = None

        if stmt.modifiers is not None:
            original_conf = stmt.modifiers.confidence

            # Compute age
            if stmt.modifiers.timestamp is not None:
                parsed_ts = _parse_timestamp(stmt.modifiers.timestamp)
                if parsed_ts is not None:
                    statements_with_ts += 1
                    age_seconds = (reference_time - parsed_ts).total_seconds()
                    age_days = age_seconds / 86400.0

        # Compute effective confidence
        eff_conf = effective_confidence(stmt, config.half_life_days, reference_time)

        # Apply min_threshold
        if eff_conf is not None and eff_conf < config.min_threshold:
            eff_conf = 0.0

        # Compute decay ratio
        if original_conf is not None and original_conf > 0 and eff_conf is not None:
            decay_ratio = eff_conf / original_conf

        # Track decayed count
        if (
            original_conf is not None
            and eff_conf is not None
            and eff_conf < original_conf
        ):
            statements_decayed += 1

        if eff_conf is not None:
            effective_values.append(eff_conf)

        decayed_statements.append(
            DecayedStatement(
                statement=stmt,
                original_confidence=original_conf,
                effective_confidence=eff_conf,
                age_days=age_days,
                decay_ratio=decay_ratio,
            )
        )

    # Summary statistics
    summary: Dict[str, Any] = {}
    if effective_values:
        summary["mean"] = stats_module.mean(effective_values)
        summary["median"] = stats_module.median(effective_values)
        summary["min"] = min(effective_values)
        summary["max"] = max(effective_values)
        summary["count"] = len(effective_values)

    return DecayReport(
        decayed_statements=decayed_statements,
        config=config,
        total_statements=len(parse_result.statements),
        statements_with_timestamp=statements_with_ts,
        statements_decayed=statements_decayed,
        summary=summary,
    )


def filter_by_confidence(
    parse_result: ParseResult,
    min_confidence: float = 0.5,
    half_life_days: float = 30.0,
    reference_time: Optional[datetime] = None,
) -> ParseResult:
    """Filter statements by effective confidence after decay.

    Statements without confidence are kept (not filtered out).

    Args:
        parse_result: The parsed document to filter.
        min_confidence: Minimum effective confidence to keep.
        half_life_days: Days for confidence to halve.
        reference_time: "Now" for age calculation.

    Returns:
        New ParseResult containing only statements meeting the threshold.
    """
    if reference_time is None:
        reference_time = datetime.now(timezone.utc)

    kept: List[Statement] = []

    for stmt in parse_result.statements:
        eff = effective_confidence(stmt, half_life_days, reference_time)
        if eff is None:
            # No confidence info → keep (don't filter out unknowns)
            kept.append(stmt)
        elif eff >= min_confidence:
            kept.append(stmt)

    return ParseResult(
        statements=kept,
        errors=parse_result.errors,
        warnings=parse_result.warnings,
        is_valid=parse_result.is_valid,
    )
