# -*- coding: utf-8 -*-
"""
STL Graph Construction

This module provides functionality to convert STL ParseResult objects
into graph structures using the networkx library. It allows for graph-based
analysis of STL statements.
"""

import networkx as nx
from typing import List, Dict, Any, Optional

from .models import ParseResult, Statement, Anchor
from .errors import STLGraphError, ErrorCode


class STLGraph:
    """
    Represents and analyzes STL statements as a directed graph.

    This class uses the networkx library to build a MultiDiGraph,
    allowing for multiple edges between the same two nodes, each
    representing a unique STL statement.
    """

    def __init__(self, parse_result: Optional[ParseResult] = None):
        """
        Initializes the STLGraph.

        Args:
            parse_result: An optional ParseResult object to build the graph from.
        """
        self.graph = nx.MultiDiGraph()
        if parse_result:
            self.build_graph(parse_result)

    def build_graph(self, parse_result: ParseResult) -> None:
        """
        Builds the graph from a ParseResult object.

        Each statement is converted into a directed edge. Nodes are anchor names.
        Modifiers are stored as edge attributes.

        Args:
            parse_result: The ParseResult object containing STL statements.
        """
        if not parse_result.is_valid:
            raise STLGraphError(
                code=ErrorCode.E300_GRAPH_CONSTRUCTION_FAILED,
                message="Cannot build graph from an invalid ParseResult."
            )

        for stmt in parse_result.statements:
            source_id = self._get_anchor_id(stmt.source)
            target_id = self._get_anchor_id(stmt.target)

            # Add nodes if they don't exist
            if not self.graph.has_node(source_id):
                self.graph.add_node(source_id, anchor=stmt.source.model_dump())
            if not self.graph.has_node(target_id):
                self.graph.add_node(target_id, anchor=stmt.target.model_dump())

            # Add edge with modifiers as attributes
            edge_attrs = stmt.modifiers.model_dump(exclude_unset=True) if stmt.modifiers else {}
            edge_attrs['statement_obj'] = stmt # Keep the original statement object
            
            self.graph.add_edge(source_id, target_id, **edge_attrs)

    def _get_anchor_id(self, anchor: Anchor) -> str:
        """
        Generates a unique string identifier for an anchor.
        Format: [Namespace:Name] or [Name]

        Args:
            anchor: The Anchor object.

        Returns:
            A unique string identifier for the anchor.
        """
        if anchor.namespace:
            return f"[{anchor.namespace}:{anchor.name}]"
        return f"[{anchor.name}]"

    def find_paths(self, source_id: str, target_id: str) -> List[List[str]]:
        """
        Finds all simple paths from a source node to a target node.

        Args:
            source_id: The identifier of the source anchor.
            target_id: The identifier of the target anchor.

        Returns:
            A list of paths, where each path is a list of anchor IDs.
        """
        if not self.graph.has_node(source_id):
            raise STLGraphError(code=ErrorCode.E302_INVALID_NODE, message=f"Source node '{source_id}' not in graph.")
        if not self.graph.has_node(target_id):
            raise STLGraphError(code=ErrorCode.E302_INVALID_NODE, message=f"Target node '{target_id}' not in graph.")
            
        return list(nx.all_simple_paths(self.graph, source=source_id, target=target_id))

    def find_cycles(self) -> List[List[str]]:
        """
        Finds all simple cycles in the graph.

        Returns:
            A list of cycles, where each cycle is a list of anchor IDs.
        """
        return list(nx.simple_cycles(self.graph))

    def get_node_degree(self, anchor_id: str) -> int:
        """
        Gets the total degree (in-degree + out-degree) of a node.

        Args:
            anchor_id: The identifier of the anchor.

        Returns:
            The total degree of the node.
        """
        if not self.graph.has_node(anchor_id):
            raise STLGraphError(code=ErrorCode.E302_INVALID_NODE, message=f"Node '{anchor_id}' not in graph.")
        return self.graph.degree(anchor_id)

    def get_node_centrality(self) -> Dict[str, float]:
        """
        Calculates the degree centrality for all nodes in the graph.

        Returns:
            A dictionary mapping anchor IDs to their degree centrality.
        """
        return nx.degree_centrality(self.graph)

    def get_subgraph(self, domain: str) -> 'STLGraph':
        """
        Creates a subgraph containing only statements from a specific domain.

        Args:
            domain: The domain to filter by (from the 'domain' modifier).

        Returns:
            A new STLGraph object representing the subgraph.
        """
        subgraph = STLGraph()
        
        for u, v, data in self.graph.edges(data=True):
            if data.get('domain') == domain:
                if not subgraph.graph.has_node(u):
                    subgraph.graph.add_node(u, **self.graph.nodes[u])
                if not subgraph.graph.has_node(v):
                    subgraph.graph.add_node(v, **self.graph.nodes[v])
                subgraph.graph.add_edge(u, v, **data)
        
        return subgraph

    def detect_conflicts(self, functional_relations: Optional[set] = None) -> List[Dict[str, Any]]:
        """
        Detects semantic conflicts in the graph.
        A conflict is defined as a source node having multiple different targets 
        for the same functional relation.

        Args:
            functional_relations: Set of relation types considered functional (unique target).
                                Defaults to {"has_color", "is_a", "located_in", "defined_as"}.

        Returns:
            A list of conflict dictionaries.
        """
        target_relations = functional_relations or {"has_color", "is_a", "located_in", "defined_as"}
        conflicts = []

        for node in self.graph.nodes():
            relations = {}
            for _, target, data in self.graph.out_edges(node, data=True):
                # Determine relation type from modifiers or path type
                rel_type = data.get('rule') or data.get('path_type') or "generic"
                # Check for explicit 'relation' modifier if available
                if 'relation' in data:
                    rel_type = data['relation']

                if rel_type in target_relations:
                    if rel_type not in relations:
                        relations[rel_type] = []
                    
                    # Get target label/id
                    target_label = target
                    if 'anchor' in self.graph.nodes[target]:
                         target_label = self.graph.nodes[target]['anchor'].get('name', target)

                    relations[rel_type].append({
                        'target': target_label,
                        'confidence': data.get('confidence', 1.0),
                        'data': data
                    })

            # Check for conflicts (multiple unique targets for same functional relation)
            for rel_type, targets in relations.items():
                if len(targets) > 1:
                    unique_targets = set(t['target'] for t in targets)
                    if len(unique_targets) > 1:
                        # Get source label
                        source_label = node
                        if 'anchor' in self.graph.nodes[node]:
                            source_label = self.graph.nodes[node]['anchor'].get('name', node)

                        conflicts.append({
                            'source': source_label,
                            'relation': rel_type,
                            'targets': targets,
                            'tension_score': sum(t['confidence'] for t in targets)
                        })

        return conflicts

    def calculate_tension_metrics(self) -> Dict[str, Any]:
        """
        Calculates graph-wide semantic tension metrics.

        Returns:
            A dictionary containing conflict count, total tension, and average tension.
        """
        conflicts = self.detect_conflicts()
        total_tension = sum(c['tension_score'] for c in conflicts)
        return {
            "conflict_count": len(conflicts),
            "total_tension_score": total_tension,
            "avg_tension_per_conflict": total_tension / len(conflicts) if conflicts else 0.0
        }
        
    @property
    def summary(self) -> Dict[str, int]:
        """
        Provides a summary of the graph.

        Returns:
            A dictionary with node and edge counts.
        """
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
        }

    @staticmethod
    def from_parse_result(parse_result: ParseResult) -> 'STLGraph':
        """
        Factory method to create an STLGraph from a ParseResult.
        
        Args:
            parse_result: The ParseResult to convert.
        
        Returns:
            A new STLGraph instance.
        """
        return STLGraph(parse_result)
