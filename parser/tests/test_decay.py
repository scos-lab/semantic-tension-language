# -*- coding: utf-8 -*-
"""Tests for stl_parser.decay module."""

from datetime import datetime, timezone, timedelta

import pytest

from stl_parser.models import Anchor, Modifier, Statement, ParseResult
from stl_parser.decay import (
    effective_confidence,
    decay_report,
    filter_by_confidence,
    DecayConfig,
    DecayReport,
    DecayedStatement,
)
from stl_parser.errors import STLDecayError


def _make_stmt(confidence=None, timestamp=None, **extra_mods):
    """Helper to create a Statement with optional confidence and timestamp."""
    mods = None
    if confidence is not None or timestamp is not None or extra_mods:
        kwargs = {}
        if confidence is not None:
            kwargs["confidence"] = confidence
        if timestamp is not None:
            kwargs["timestamp"] = timestamp
        kwargs.update(extra_mods)
        mods = Modifier(**kwargs)
    return Statement(source=Anchor(name="A"), target=Anchor(name="B"), modifiers=mods)


# Fixed reference time for deterministic tests
REF_TIME = datetime(2026, 2, 11, 0, 0, 0, tzinfo=timezone.utc)


class TestEffectiveConfidence:
    """Tests for effective_confidence()."""

    def test_basic_decay(self):
        """30 days old with 30-day half-life → halved."""
        stmt = _make_stmt(confidence=1.0, timestamp="2026-01-12T00:00:00Z")
        eff = effective_confidence(stmt, half_life_days=30, reference_time=REF_TIME)
        assert eff == pytest.approx(0.5, abs=0.01)

    def test_60_day_half_life(self):
        """30 days old with 60-day half-life → ~0.707."""
        stmt = _make_stmt(confidence=1.0, timestamp="2026-01-12T00:00:00Z")
        eff = effective_confidence(stmt, half_life_days=60, reference_time=REF_TIME)
        # 0.5^(30/60) = 0.5^0.5 = 0.707
        assert eff == pytest.approx(0.707, abs=0.01)

    def test_no_timestamp_returns_original(self):
        """No timestamp → return original confidence (no decay)."""
        stmt = _make_stmt(confidence=0.9)
        eff = effective_confidence(stmt, reference_time=REF_TIME)
        assert eff == 0.9

    def test_no_confidence_returns_none(self):
        """No confidence → return None."""
        stmt = _make_stmt(timestamp="2026-01-01T00:00:00Z")
        eff = effective_confidence(stmt, reference_time=REF_TIME)
        assert eff is None

    def test_no_modifiers_returns_none(self):
        """No modifiers at all → return None."""
        stmt = Statement(source=Anchor(name="A"), target=Anchor(name="B"))
        eff = effective_confidence(stmt, reference_time=REF_TIME)
        assert eff is None

    def test_zero_age(self):
        """Just created (age=0) → return original."""
        stmt = _make_stmt(confidence=0.8, timestamp="2026-02-11T00:00:00Z")
        eff = effective_confidence(stmt, reference_time=REF_TIME)
        assert eff == pytest.approx(0.8, abs=0.001)

    def test_future_timestamp(self):
        """Future timestamp → return original (no decay)."""
        stmt = _make_stmt(confidence=0.8, timestamp="2026-03-01T00:00:00Z")
        eff = effective_confidence(stmt, reference_time=REF_TIME)
        assert eff == 0.8

    def test_very_old_statement(self):
        """Very old → decays close to zero."""
        stmt = _make_stmt(confidence=0.9, timestamp="2020-01-01T00:00:00Z")
        eff = effective_confidence(stmt, half_life_days=30, reference_time=REF_TIME)
        assert eff < 0.001

    def test_confidence_zero(self):
        """Confidence 0.0 → stays 0.0 after decay."""
        stmt = _make_stmt(confidence=0.0, timestamp="2026-01-01T00:00:00Z")
        eff = effective_confidence(stmt, reference_time=REF_TIME)
        assert eff == 0.0

    def test_invalid_half_life_raises(self):
        """half_life_days <= 0 raises STLDecayError."""
        stmt = _make_stmt(confidence=0.9, timestamp="2026-01-01T00:00:00Z")
        with pytest.raises(STLDecayError):
            effective_confidence(stmt, half_life_days=0)
        with pytest.raises(STLDecayError):
            effective_confidence(stmt, half_life_days=-10)

    def test_malformed_timestamp_returns_original(self):
        """Malformed timestamp → graceful degradation, returns original."""
        stmt = _make_stmt(confidence=0.9, timestamp="not-a-date")
        eff = effective_confidence(stmt, reference_time=REF_TIME)
        assert eff == 0.9

    def test_date_only_timestamp(self):
        """Date-only timestamp (no time) parses correctly."""
        stmt = _make_stmt(confidence=1.0, timestamp="2026-01-12")
        eff = effective_confidence(stmt, half_life_days=30, reference_time=REF_TIME)
        assert eff == pytest.approx(0.5, abs=0.01)


class TestDecayReport:
    """Tests for decay_report()."""

    def test_basic_report(self):
        """Report with mixed statements."""
        stmts = [
            _make_stmt(confidence=1.0, timestamp="2026-01-12T00:00:00Z"),  # 30 days old
            _make_stmt(confidence=0.8, timestamp="2026-02-11T00:00:00Z"),  # just created
            _make_stmt(confidence=0.5),  # no timestamp
        ]
        result = ParseResult(statements=stmts, is_valid=True)
        config = DecayConfig(half_life_days=30, reference_time=REF_TIME)

        report = decay_report(result, config)

        assert report.total_statements == 3
        assert report.statements_with_timestamp == 2
        assert report.statements_decayed == 1  # only first one decayed
        assert len(report.decayed_statements) == 3
        assert "mean" in report.summary
        assert "median" in report.summary

    def test_empty_result(self):
        """Empty ParseResult → empty report."""
        result = ParseResult(statements=[], is_valid=True)
        report = decay_report(result)

        assert report.total_statements == 0
        assert report.statements_decayed == 0
        assert report.summary == {}

    def test_no_confidence_statements(self):
        """Statements without confidence → no summary stats for confidence."""
        stmts = [
            Statement(source=Anchor(name="A"), target=Anchor(name="B")),
            Statement(source=Anchor(name="C"), target=Anchor(name="D")),
        ]
        result = ParseResult(statements=stmts, is_valid=True)
        report = decay_report(result)

        assert report.total_statements == 2
        assert report.summary == {}

    def test_min_threshold(self):
        """Very decayed statements get clamped to 0.0 by min_threshold."""
        stmts = [
            _make_stmt(confidence=0.9, timestamp="2020-01-01T00:00:00Z"),  # very old
        ]
        result = ParseResult(statements=stmts, is_valid=True)
        config = DecayConfig(half_life_days=30, min_threshold=0.01, reference_time=REF_TIME)

        report = decay_report(result, config)

        assert report.decayed_statements[0].effective_confidence == 0.0

    def test_default_config(self):
        """decay_report with default config (no config arg)."""
        stmts = [_make_stmt(confidence=0.9)]
        result = ParseResult(statements=stmts, is_valid=True)
        report = decay_report(result)

        assert report.config.half_life_days == 30.0
        assert report.total_statements == 1

    def test_decay_ratio(self):
        """Decay ratio = effective / original."""
        stmts = [
            _make_stmt(confidence=1.0, timestamp="2026-01-12T00:00:00Z"),  # 30 days → ~0.5
        ]
        result = ParseResult(statements=stmts, is_valid=True)
        config = DecayConfig(half_life_days=30, reference_time=REF_TIME)

        report = decay_report(result, config)

        ds = report.decayed_statements[0]
        assert ds.decay_ratio == pytest.approx(0.5, abs=0.01)
        assert ds.age_days == pytest.approx(30.0, abs=0.1)

    def test_summary_statistics(self):
        """Summary has mean, median, min, max."""
        stmts = [
            _make_stmt(confidence=1.0, timestamp="2026-01-12T00:00:00Z"),  # ~0.5
            _make_stmt(confidence=0.8, timestamp="2026-02-11T00:00:00Z"),  # ~0.8
        ]
        result = ParseResult(statements=stmts, is_valid=True)
        config = DecayConfig(half_life_days=30, reference_time=REF_TIME)

        report = decay_report(result, config)

        assert report.summary["count"] == 2
        assert report.summary["min"] == pytest.approx(0.5, abs=0.02)
        assert report.summary["max"] == pytest.approx(0.8, abs=0.02)


class TestFilterByConfidence:
    """Tests for filter_by_confidence()."""

    def test_basic_filter(self):
        """Filter keeps fresh, removes old."""
        stmts = [
            _make_stmt(confidence=1.0, timestamp="2026-01-12T00:00:00Z"),  # ~0.5
            _make_stmt(confidence=0.8, timestamp="2026-02-11T00:00:00Z"),  # ~0.8
        ]
        result = ParseResult(statements=stmts, is_valid=True)

        filtered = filter_by_confidence(
            result, min_confidence=0.7, half_life_days=30, reference_time=REF_TIME
        )

        assert len(filtered.statements) == 1
        assert filtered.statements[0].modifiers.confidence == 0.8

    def test_keeps_no_confidence_statements(self):
        """Statements without confidence are kept (not filtered)."""
        stmts = [
            Statement(source=Anchor(name="A"), target=Anchor(name="B")),
            _make_stmt(confidence=0.1, timestamp="2020-01-01T00:00:00Z"),  # very old
        ]
        result = ParseResult(statements=stmts, is_valid=True)

        filtered = filter_by_confidence(
            result, min_confidence=0.5, half_life_days=30, reference_time=REF_TIME
        )

        assert len(filtered.statements) == 1
        assert filtered.statements[0].modifiers is None

    def test_all_pass(self):
        """All statements pass threshold → all kept."""
        stmts = [
            _make_stmt(confidence=0.9, timestamp="2026-02-10T00:00:00Z"),
            _make_stmt(confidence=0.8, timestamp="2026-02-10T00:00:00Z"),
        ]
        result = ParseResult(statements=stmts, is_valid=True)

        filtered = filter_by_confidence(
            result, min_confidence=0.1, half_life_days=30, reference_time=REF_TIME
        )

        assert len(filtered.statements) == 2

    def test_none_pass(self):
        """All below threshold → empty result."""
        stmts = [
            _make_stmt(confidence=0.1, timestamp="2020-01-01T00:00:00Z"),
            _make_stmt(confidence=0.2, timestamp="2020-01-01T00:00:00Z"),
        ]
        result = ParseResult(statements=stmts, is_valid=True)

        filtered = filter_by_confidence(
            result, min_confidence=0.5, half_life_days=30, reference_time=REF_TIME
        )

        assert len(filtered.statements) == 0

    def test_empty_input(self):
        """Empty ParseResult → empty filtered result."""
        result = ParseResult(statements=[], is_valid=True)
        filtered = filter_by_confidence(result, min_confidence=0.5)
        assert len(filtered.statements) == 0
        assert filtered.is_valid is True

    def test_preserves_errors_warnings(self):
        """Filtered result preserves original errors and warnings."""
        result = ParseResult(
            statements=[_make_stmt(confidence=0.9)],
            is_valid=True,
            errors=[],
            warnings=[],
        )
        filtered = filter_by_confidence(result, reference_time=REF_TIME)
        assert filtered.is_valid is True
