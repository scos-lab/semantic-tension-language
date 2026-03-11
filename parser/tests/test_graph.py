#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test suite for graph.py

Tests the construction and analysis of STL graphs using networkx.
"""

import pytest
import networkx as nx

from stl_parser.models import Anchor, Modifier, Statement, ParseResult
from stl_parser.parser import parse
from stl_parser.graph import STLGraph
from stl_parser.errors import STLGraphError


@pytest.fixture
def sample_parse_result_linear():
    """Returns a valid ParseResult with a linear path."""
    stmts = [
        Statement(source=Anchor(name="A"), target=Anchor(name="B"), modifiers=Modifier(confidence=0.9)),
        Statement(source=Anchor(name="B"), target=Anchor(name="C"), modifiers=Modifier(confidence=0.8)),
        Statement(source=Anchor(name="C"), target=Anchor(name="D"), modifiers=Modifier(confidence=0.7)),
    ]
    return ParseResult(statements=stmts, is_valid=True)

@pytest.fixture
def sample_parse_result_cyclic():
    """Returns a valid ParseResult with a cycle."""
    stmts = [
        Statement(source=Anchor(name="A"), target=Anchor(name="B")),
        Statement(source=Anchor(name="B"), target=Anchor(name="C")),
        Statement(source=Anchor(name="C"), target=Anchor(name="A")), # Cycle
    ]
    return ParseResult(statements=stmts, is_valid=True)
    
@pytest.fixture
def sample_parse_result_with_domains():
    """Returns a valid ParseResult with different domains."""
    stmts = [
        Statement(source=Anchor(name="A"), target=Anchor(name="B"), modifiers=Modifier(domain="physics")),
        Statement(source=Anchor(name="B"), target=Anchor(name="C"), modifiers=Modifier(domain="physics")),
        Statement(source=Anchor(name="C"), target=Anchor(name="D"), modifiers=Modifier(domain="chemistry")),
    ]
    return ParseResult(statements=stmts, is_valid=True)


class TestSTLGraph:
    """Tests the STLGraph class methods."""

    def test_graph_construction(self, sample_parse_result_linear):
        """Test that the graph is built correctly from a ParseResult."""
        stl_graph = STLGraph(sample_parse_result_linear)
        
        assert isinstance(stl_graph.graph, nx.MultiDiGraph)
        assert stl_graph.graph.number_of_nodes() == 4
        assert stl_graph.graph.number_of_edges() == 3
        
        assert "[A]" in stl_graph.graph
        assert "[B]" in stl_graph.graph
        assert "[C]" in stl_graph.graph
        assert "[D]" in stl_graph.graph
        
        # Check edge attributes
        edge_data = stl_graph.graph.get_edge_data("[A]", "[B]")[0] # Get first edge
        assert edge_data['confidence'] == 0.9

    def test_invalid_parse_result_construction(self):
        """Test that graph construction fails with an invalid ParseResult."""
        invalid_result = ParseResult(statements=[], is_valid=False)
        with pytest.raises(STLGraphError) as excinfo:
            STLGraph(invalid_result)
        assert excinfo.value.code == "E300"

    def test_get_anchor_id(self):
        """Test the generation of unique anchor IDs."""
        stl_graph = STLGraph()
        anchor1 = Anchor(name="Test")
        anchor2 = Anchor(name="Test", namespace="Domain")
        
        assert stl_graph._get_anchor_id(anchor1) == "[Test]"
        assert stl_graph._get_anchor_id(anchor2) == "[Domain:Test]"

    def test_find_paths(self, sample_parse_result_linear):
        """Test finding all simple paths between two nodes."""
        stl_graph = STLGraph(sample_parse_result_linear)
        paths = stl_graph.find_paths("[A]", "[D]")
        
        assert len(paths) == 1
        assert paths[0] == ["[A]", "[B]", "[C]", "[D]"]
        
        paths_b_d = stl_graph.find_paths("[B]", "[D]")
        assert len(paths_b_d) == 1
        assert paths_b_d[0] == ["[B]", "[C]", "[D]"]

    def test_find_paths_nonexistent_nodes(self, sample_parse_result_linear):
        """Test find_paths with nodes that are not in the graph."""
        stl_graph = STLGraph(sample_parse_result_linear)
        
        with pytest.raises(STLGraphError) as excinfo:
            stl_graph.find_paths("[X]", "[A]")
        assert excinfo.value.code == "E302"
        
        with pytest.raises(STLGraphError) as excinfo:
            stl_graph.find_paths("[A]", "[Y]")
        assert excinfo.value.code == "E302"

    def test_find_cycles(self, sample_parse_result_cyclic):
        """Test finding cycles in the graph."""
        stl_graph = STLGraph(sample_parse_result_cyclic)
        cycles = stl_graph.find_cycles()
        
        assert len(cycles) == 1
        # The order might vary, so check for presence of all nodes
        assert sorted(cycles[0]) == ["[A]", "[B]", "[C]"]

    def test_no_cycles(self, sample_parse_result_linear):
        """Test cycle detection in a graph with no cycles."""
        stl_graph = STLGraph(sample_parse_result_linear)
        cycles = stl_graph.find_cycles()
        assert len(cycles) == 0

    def test_node_degree(self, sample_parse_result_linear):
        """Test getting the degree of a node."""
        stl_graph = STLGraph(sample_parse_result_linear)
        
        assert stl_graph.get_node_degree("[A]") == 1  # Out-degree 1
        assert stl_graph.get_node_degree("[B]") == 2  # In-degree 1, Out-degree 1
        assert stl_graph.get_node_degree("[D]") == 1  # In-degree 1
        
        with pytest.raises(STLGraphError):
            stl_graph.get_node_degree("[X]")

    def test_degree_centrality(self, sample_parse_result_linear):
        """Test calculating degree centrality."""
        stl_graph = STLGraph(sample_parse_result_linear)
        centrality = stl_graph.get_node_centrality()
        
        assert isinstance(centrality, dict)
        assert "[A]" in centrality
        assert "[B]" in centrality
        assert centrality["[B]"] > centrality["[A]"]

    def test_get_subgraph(self, sample_parse_result_with_domains):
        """Test creating a subgraph based on a domain."""
        stl_graph = STLGraph(sample_parse_result_with_domains)
        physics_subgraph = stl_graph.get_subgraph(domain="physics")
        
        assert isinstance(physics_subgraph, STLGraph)
        assert physics_subgraph.graph.number_of_nodes() == 3 # A, B, C
        assert physics_subgraph.graph.number_of_edges() == 2 # A->B, B->C
        assert "[D]" not in physics_subgraph.graph
        
        chemistry_subgraph = stl_graph.get_subgraph(domain="chemistry")
        assert chemistry_subgraph.graph.number_of_nodes() == 2 # C, D
        assert chemistry_subgraph.graph.number_of_edges() == 1 # C->D
        assert "[A]" not in chemistry_subgraph.graph

    def test_summary(self, sample_parse_result_linear):
        """Test the graph summary property."""
        stl_graph = STLGraph(sample_parse_result_linear)
        summary = stl_graph.summary
        
        assert summary["nodes"] == 4
        assert summary["edges"] == 3

    def test_from_parse_result_factory(self, sample_parse_result_linear):
        """Test creating an STLGraph using the factory method."""
        stl_graph = STLGraph.from_parse_result(sample_parse_result_linear)
        assert isinstance(stl_graph, STLGraph)
        assert stl_graph.summary["nodes"] == 4

    def test_detect_conflicts(self):
        """Test detecting semantic conflicts."""
        stmts = [
            Statement(source=Anchor(name="Apple"), target=Anchor(name="Red"), modifiers=Modifier(rule="has_color", confidence=0.9)),
            Statement(source=Anchor(name="Apple"), target=Anchor(name="Green"), modifiers=Modifier(rule="has_color", confidence=0.8)),
            Statement(source=Anchor(name="Apple"), target=Anchor(name="Fruit"), modifiers=Modifier(rule="is_a")), # No conflict
        ]
        parse_result = ParseResult(statements=stmts, is_valid=True)
        stl_graph = STLGraph(parse_result)
        
        conflicts = stl_graph.detect_conflicts(functional_relations={"has_color"})
        assert len(conflicts) == 1
        assert conflicts[0]["source"] == "Apple"
        assert conflicts[0]["relation"] == "has_color"
        assert len(conflicts[0]["targets"]) == 2
        assert abs(conflicts[0]["tension_score"] - 1.7) < 0.001

    def test_calculate_tension_metrics(self):
        """Test calculating tension metrics."""
        stmts = [
            Statement(source=Anchor(name="Sky"), target=Anchor(name="Blue"), modifiers=Modifier(rule="has_color", confidence=1.0)),
            Statement(source=Anchor(name="Sky"), target=Anchor(name="Green"), modifiers=Modifier(rule="has_color", confidence=0.5)),
        ]
        parse_result = ParseResult(statements=stmts, is_valid=True)
        stl_graph = STLGraph(parse_result)
        
        # 'has_color' is in default functional relations
        metrics = stl_graph.calculate_tension_metrics()
        
        assert metrics["conflict_count"] == 1
        assert abs(metrics["total_tension_score"] - 1.5) < 0.001
        assert abs(metrics["avg_tension_per_conflict"] - 1.5) < 0.001
