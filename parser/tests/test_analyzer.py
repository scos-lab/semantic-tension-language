# -*- coding: utf-8 -*-
"""
Test suite for analyzer.py

Tests the statistical analysis of STL ParseResult objects.
"""

import pytest
import statistics

from stl_parser.models import Anchor, Modifier, Statement, ParseResult, AnchorType, PathType
from stl_parser.parser import parse
from stl_parser.analyzer import STLAnalyzer, analyze_parse_result
from stl_parser.graph import STLGraph


@pytest.fixture
def sample_parse_result_simple():
    """Returns a simple ParseResult for testing basic counts."""
    stmts = [
        Statement(source=Anchor(name="A"), target=Anchor(name="B")),
        Statement(source=Anchor(name="B"), target=Anchor(name="C")),
        Statement(source=Anchor(name="A"), target=Anchor(name="B")), # Duplicate
    ]
    return ParseResult(statements=stmts, is_valid=True)

@pytest.fixture
def sample_parse_result_complex():
    """Returns a more complex ParseResult for comprehensive analysis."""
    stmts = [
        # Statement 1
        Statement(
            source=Anchor(name="Theory_Relativity", type=AnchorType.CONCEPT),
            target=Anchor(name="Prediction_TimeDilation", type=AnchorType.CONCEPT),
            modifiers=Modifier(rule="logical", confidence=0.99, author="Einstein", domain="physics", timestamp="1905-01-01T00:00:00Z")
        ),
        # Statement 2
        Statement(
            source=Anchor(name="Prediction_TimeDilation", type=AnchorType.CONCEPT),
            target=Anchor(name="Experiment_GPS", type=AnchorType.EVENT),
            modifiers=Modifier(rule="empirical", confidence=0.95, domain="physics", strength=0.8)
        ),
        # Statement 3 (Missing provenance)
        Statement(
            source=Anchor(name="Study_X", type=AnchorType.EVENT),
            target=Anchor(name="Finding_Y", type=AnchorType.CONCEPT),
            modifiers=Modifier(confidence=0.85) # Missing source, author, timestamp
        ),
        # Statement 4 (Low confidence)
        Statement(
            source=Anchor(name="Hypothesis_Z", type=AnchorType.QUESTION),
            target=Anchor(name="Outcome_P", type=AnchorType.CONCEPT),
            modifiers=Modifier(confidence=0.4, rule="inferential")
        ),
        # Statement 5 (Custom modifier, different domain)
        Statement(
            source=Anchor(name="Agent_A", type=AnchorType.AGENT),
            target=Anchor(name="Action_B", type=AnchorType.EVENT),
            modifiers=Modifier(intent="explain", domain="biology", custom={"custom_key": "value"})
        ),
        # Statement 6 (Another physics statement)
        Statement(
            source=Anchor(name="Mass", namespace="Physics", type=AnchorType.CONCEPT),
            target=Anchor(name="Energy", namespace="Physics", type=AnchorType.CONCEPT),
            modifiers=Modifier(rule="definitional", confidence=1.0)
        ),
    ]
    return ParseResult(statements=stmts, is_valid=True)


class TestSTLAnalyzer:
    """Tests the STLAnalyzer class methods."""

    def test_count_elements_simple(self, sample_parse_result_simple):
        """Test counting elements with a simple ParseResult."""
        analyzer = STLAnalyzer(sample_parse_result_simple)
        counts = analyzer.count_elements()
        
        assert counts["total_statements"] == 3
        assert counts["unique_anchors"] == 3 # A, B, C
        assert counts["unique_statement_hashes"] == 2 # (A->B), (B->C), (A->B) is duplicate

    def test_count_elements_complex(self, sample_parse_result_complex):
        """Test counting elements with a complex ParseResult."""
        analyzer = STLAnalyzer(sample_parse_result_complex)
        counts = analyzer.count_elements()
        
        assert counts["total_statements"] == 6
        assert counts["unique_anchors"] == 11 # Theory_Relativity, Prediction_TimeDilation, Experiment_GPS, Study_X, Finding_Y, Hypothesis_Z, Outcome_P, Agent_A, Action_B, Physics:Mass, Physics:Energy
        assert counts["unique_statement_hashes"] == 6

    def test_analyze_anchor_types(self, sample_parse_result_complex):
        """Test analysis of anchor types."""
        analyzer = STLAnalyzer(sample_parse_result_complex)
        anchor_types_dist = analyzer.analyze_anchor_types()
        
        assert anchor_types_dist["overall_anchor_types"].get("Concept", 0) == 7
        assert anchor_types_dist["overall_anchor_types"].get("Event", 0) == 3
        assert anchor_types_dist["overall_anchor_types"].get("Agent", 0) == 1
        assert anchor_types_dist["overall_anchor_types"].get("Question", 0) == 1
        assert anchor_types_dist["overall_anchor_types"].get("Name", 0) == 0 # No single-word PascalCase anchors besides explicitly typed ones

    def test_analyze_path_types(self, sample_parse_result_complex):
        """Test analysis of path types."""
        analyzer = STLAnalyzer(sample_parse_result_complex)
        path_types_dist = analyzer.analyze_path_types()
        
        assert path_types_dist.get(PathType.INFERENTIAL.value) == 3
        assert path_types_dist.get(PathType.SEMANTIC.value) == 1
        assert path_types_dist.get(PathType.ACTION.value) == 1
        assert path_types_dist.get("UNKNOWN") == 1 # For statement 3

    def test_analyze_modifier_usage(self, sample_parse_result_complex):
        """Test analysis of modifier usage."""
        analyzer = STLAnalyzer(sample_parse_result_complex)
        modifier_usage = analyzer.analyze_modifier_usage()
        
        assert modifier_usage["confidence"]["frequency"] == 5 # Corrected count
        assert modifier_usage["confidence"]["min"] == 0.4
        assert modifier_usage["confidence"]["max"] == 1.0
        assert pytest.approx(modifier_usage["confidence"]["mean"], 0.001) == (0.99 + 0.95 + 0.85 + 0.4 + 1.0) / 5

        assert modifier_usage["rule"]["frequency"] == 4
        assert ("logical", 1) in modifier_usage["rule"]["most_common_values"]
        assert ("empirical", 1) in modifier_usage["rule"]["most_common_values"]
        
        assert modifier_usage["domain"]["frequency"] == 3
        assert ("physics", 2) in modifier_usage["domain"]["most_common_values"]

        # Test custom modifier
        assert modifier_usage["custom"]["frequency"] == 1 # Corrected key
        assert modifier_usage["custom"]["most_common_values"][0] == ("{'custom_key': 'value'}", 1) # Custom modifier is a dict, now stringified

    def test_analyze_confidence_metrics(self, sample_parse_result_complex):
        """Test calculation of confidence and certainty metrics."""
        analyzer = STLAnalyzer(sample_parse_result_complex)
        metrics = analyzer.analyze_confidence_metrics()
        
        assert metrics["confidence"]["count"] == 5 # Corrected count
        assert metrics["confidence"]["min"] == 0.4
        assert metrics["confidence"]["max"] == 1.0
        assert pytest.approx(metrics["confidence"]["mean"], 0.001) == (0.99 + 0.95 + 0.85 + 0.4 + 1.0) / 5

    def test_identify_missing_provenance(self, sample_parse_result_complex):
        """Test identification of missing provenance."""
        analyzer = STLAnalyzer(sample_parse_result_complex)
        missing_provenance = analyzer.identify_missing_provenance()
        
        assert len(missing_provenance) == 3 # Statements 2, 3, 6
        # Assert specific statements are present, regardless of exact string formatting
        statements_str_list = [mp['statement'] for mp in missing_provenance]
        
        # Check if the relevant parts of the statement strings are present
        assert any("[Prediction_TimeDilation] -> [Experiment_GPS]" in s for s in statements_str_list)
        assert any("[Study_X] -> [Finding_Y]" in s for s in statements_str_list)
        assert any("[Physics:Mass] -> [Physics:Energy]" in s for s in statements_str_list)

    def test_get_graph_metrics(self, sample_parse_result_complex):
        """Test retrieving graph metrics."""
        analyzer = STLAnalyzer(sample_parse_result_complex)
        graph_metrics = analyzer.get_graph_metrics()
        
        assert graph_metrics["nodes"] == 11
        assert graph_metrics["edges"] == 6
        assert graph_metrics["cycles_count"] == 0
        assert len(graph_metrics["top_central_nodes"]) == 5

    def test_get_full_analysis_report(self, sample_parse_result_complex):
        """Test generation of a full analysis report."""
        analyzer = STLAnalyzer(sample_parse_result_complex)
        report = analyzer.get_full_analysis_report()
        
        assert "counts" in report
        assert "anchor_types_distribution" in report
        assert "path_types_distribution" in report
        assert "modifier_usage" in report
        assert "confidence_metrics" in report
        assert "missing_provenance_high_confidence" in report
        assert "graph_metrics" in report

        assert report["counts"]["total_statements"] == 6
        assert report["graph_metrics"]["nodes"] == 11

    def test_analyze_parse_result_convenience(self, sample_parse_result_complex):
        """Test convenience function analyze_parse_result."""
        report = analyze_parse_result(sample_parse_result_complex)
        
        assert "counts" in report
        assert report["counts"]["total_statements"] == 6
        assert report["graph_metrics"]["nodes"] == 11
