# -*- coding: utf-8 -*-
"""Tests for the `stl query` CLI command."""

import csv
import io
import json

import pytest
from typer.testing import CliRunner

from stl_parser.cli import app, _parse_where_string

runner = CliRunner()


# ========================================
# FIXTURES
# ========================================

@pytest.fixture(scope="module")
def query_stl_file(tmpdir_factory):
    """Multi-statement STL file for query tests."""
    fn = tmpdir_factory.mktemp("query").join("data.stl")
    fn.write(
        '[Theory_X] -> [Prediction_A] ::mod(confidence=0.95, rule="logical")\n'
        '[Theory_X] -> [Prediction_B] ::mod(confidence=0.70, rule="causal")\n'
        '[Study_Y] -> [Finding_Z] ::mod(confidence=0.85, rule="empirical")\n'
        '[Events:Start] -> [Events:Running] ::mod(confidence=0.90)\n'
        '[A] -> [B]\n'
    )
    return str(fn)


@pytest.fixture(scope="module")
def invalid_stl_file(tmpdir_factory):
    """Invalid STL file for error tests."""
    fn = tmpdir_factory.mktemp("query_invalid").join("bad.stl")
    fn.write("[A] -> [B] ::mod(confidence=2.0)")
    return str(fn)


# ========================================
# TESTS: _parse_where_string()
# ========================================

class TestParseWhereString:
    """Unit tests for _parse_where_string()."""

    def test_simple_equality(self):
        result = _parse_where_string("source=Theory_X")
        assert result == {"source": "Theory_X"}

    def test_operator_suffix(self):
        result = _parse_where_string("confidence__gt=0.8")
        assert result == {"confidence__gt": 0.8}

    def test_multiple_conditions(self):
        result = _parse_where_string("confidence__gt=0.8,rule=causal")
        assert result == {"confidence__gt": 0.8, "rule": "causal"}

    def test_in_operator(self):
        result = _parse_where_string("rule__in=causal|logical")
        assert result == {"rule__in": ["causal", "logical"]}

    def test_empty_string(self):
        result = _parse_where_string("")
        assert result == {}

    def test_mixed_types(self):
        result = _parse_where_string("confidence=0.95,source=A")
        assert result == {"confidence": 0.95, "source": "A"}

    def test_quoted_value(self):
        result = _parse_where_string('rule="causal"')
        assert result == {"rule": "causal"}

    def test_integer_value(self):
        result = _parse_where_string("line=42")
        assert result == {"line": 42}

    def test_boolean_value(self):
        result = _parse_where_string("flag=true")
        assert result == {"flag": True}


# ========================================
# TESTS: stl query (integration via CliRunner)
# ========================================

class TestQueryCommand:
    """Integration tests for `stl query`."""

    def test_query_default_table(self, query_stl_file):
        """Default: table output with all statements."""
        result = runner.invoke(app, ["query", query_stl_file])
        assert result.exit_code == 0
        assert "5 statement(s)" in result.stdout

    def test_query_where_source(self, query_stl_file):
        """Filter by source name."""
        result = runner.invoke(app, ["query", query_stl_file, "-w", "source=Theory_X"])
        assert result.exit_code == 0
        assert "2 statement(s)" in result.stdout
        assert "Theory_X" in result.stdout

    def test_query_where_confidence_gt(self, query_stl_file):
        """Filter by confidence > 0.8."""
        result = runner.invoke(app, ["query", query_stl_file, "-w", "confidence__gt=0.8"])
        assert result.exit_code == 0
        assert "3 statement(s)" in result.stdout

    def test_query_select_fields(self, query_stl_file):
        """Select specific fields."""
        result = runner.invoke(app, ["query", query_stl_file, "-s", "source,confidence"])
        assert result.exit_code == 0
        assert "Source" in result.stdout
        assert "Confidence" in result.stdout

    def test_query_count(self, query_stl_file):
        """--count returns just the number."""
        result = runner.invoke(app, ["query", query_stl_file, "-w", "source=Theory_X", "-c"])
        assert result.exit_code == 0
        assert result.stdout.strip() == "2"

    def test_query_pointer_source_name(self, query_stl_file):
        """Pointer returns scalar value."""
        result = runner.invoke(app, ["query", query_stl_file, "-p", "/0/source/name"])
        assert result.exit_code == 0
        assert result.stdout.strip() == "Theory_X"

    def test_query_pointer_confidence(self, query_stl_file):
        """Pointer returns modifier value."""
        result = runner.invoke(app, ["query", query_stl_file, "-p", "/0/modifiers/confidence"])
        assert result.exit_code == 0
        assert result.stdout.strip() == "0.95"

    def test_query_pointer_out_of_range(self, query_stl_file):
        """Pointer with bad index → exit 1."""
        result = runner.invoke(app, ["query", query_stl_file, "-p", "/99/source/name"])
        assert result.exit_code == 1
        assert "E452" in result.stdout

    def test_query_format_json(self, query_stl_file):
        """JSON output is valid JSON."""
        result = runner.invoke(app, ["query", query_stl_file, "-f", "json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) == 5

    def test_query_format_stl(self, query_stl_file):
        """STL output contains anchor names."""
        result = runner.invoke(app, ["query", query_stl_file, "-f", "stl"])
        assert result.exit_code == 0
        assert "[Theory_X]" in result.stdout
        assert "[Prediction_A]" in result.stdout
        assert "->" in result.stdout

    def test_query_format_csv(self, query_stl_file):
        """CSV output has header and rows."""
        result = runner.invoke(app, ["query", query_stl_file, "-f", "csv"])
        assert result.exit_code == 0
        reader = csv.reader(io.StringIO(result.stdout))
        rows = list(reader)
        assert rows[0] == ["source", "target", "confidence", "rule"]
        assert len(rows) == 6  # header + 5 data rows

    def test_query_no_match(self, query_stl_file):
        """No match → exit 0, empty result."""
        result = runner.invoke(app, ["query", query_stl_file, "-w", "source=Nonexistent"])
        assert result.exit_code == 0
        assert "0 statement(s)" in result.stdout

    def test_query_limit(self, query_stl_file):
        """--limit caps results."""
        result = runner.invoke(app, ["query", query_stl_file, "-w", "confidence__gte=0.8", "-l", "1"])
        assert result.exit_code == 0
        assert "1 statement(s)" in result.stdout

    def test_query_json_with_select(self, query_stl_file):
        """JSON + select returns dicts with selected keys only."""
        result = runner.invoke(app, ["query", query_stl_file, "-f", "json", "-s", "source"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data) == 5
        assert set(data[0].keys()) == {"source"}

    def test_query_invalid_file(self, invalid_stl_file):
        """Invalid STL file → exit 1."""
        result = runner.invoke(app, ["query", invalid_stl_file])
        assert result.exit_code == 1
        assert "parse errors" in result.stdout

    def test_query_count_all(self, query_stl_file):
        """--count without --where counts all statements."""
        result = runner.invoke(app, ["query", query_stl_file, "-c"])
        assert result.exit_code == 0
        assert result.stdout.strip() == "5"

    def test_query_where_rule_in(self, query_stl_file):
        """--where with __in operator."""
        result = runner.invoke(app, ["query", query_stl_file, "-w", "rule__in=causal|logical"])
        assert result.exit_code == 0
        assert "2 statement(s)" in result.stdout

    def test_query_csv_with_select(self, query_stl_file):
        """CSV + select uses selected fields as columns."""
        result = runner.invoke(app, ["query", query_stl_file, "-f", "csv", "-s", "source,target"])
        assert result.exit_code == 0
        reader = csv.reader(io.StringIO(result.stdout))
        rows = list(reader)
        assert rows[0] == ["source", "target"]
        assert len(rows) == 6

    def test_query_pointer_statement(self, query_stl_file):
        """Pointer to statement index returns STL string."""
        result = runner.invoke(app, ["query", query_stl_file, "-p", "/0"])
        assert result.exit_code == 0
        assert "[Theory_X]" in result.stdout

    def test_query_appears_in_help(self):
        """query command appears in main help."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "query" in result.stdout

    def test_query_unsupported_format(self, query_stl_file):
        """Unsupported --format → exit 1."""
        result = runner.invoke(app, ["query", query_stl_file, "-f", "yaml"])
        assert result.exit_code == 1
        assert "Unsupported format" in result.stdout
