# -*- coding: utf-8 -*-
"""
STL Parser Analyzer

This module provides tools for statistical analysis of STL ParseResult objects.
It calculates various metrics and insights from parsed STL statements.
"""

from collections import Counter
from typing import Dict, Any, List, Optional
import statistics

from .models import ParseResult, Statement, AnchorType, PathType
from .graph import STLGraph # For graph-based metrics


class STLAnalyzer:
    """
    Performs statistical analysis on an STL ParseResult object.
    """

    def __init__(self, parse_result: ParseResult, stl_graph: Optional[STLGraph] = None):
        """
        Initializes the STLAnalyzer.

        Args:
            parse_result: The ParseResult object to analyze.
            stl_graph: An optional STLGraph object for graph-based metrics.
        """
        self.parse_result = parse_result
        self.statements = parse_result.statements
        self.stl_graph = stl_graph
        if self.stl_graph is None and parse_result.is_valid and parse_result.statements:
            try:
                self.stl_graph = STLGraph(parse_result)
            except Exception:
                # Graph might not be buildable for some invalid results, ignore for analyzer
                self.stl_graph = None

    def count_elements(self) -> Dict[str, int]:
        """
        Counts total statements, unique anchors, and unique statement hashes.

        Returns:
            A dictionary with counts.
        """
        unique_anchors = set()
        unique_statement_hashes = set()

        for stmt in self.statements:
            unique_anchors.add(str(stmt.source))
            unique_anchors.add(str(stmt.target))
            unique_statement_hashes.add(hash(stmt)) # Using hash for unique statements

        return {
            "total_statements": len(self.statements),
            "unique_anchors": len(unique_anchors),
            "unique_statement_hashes": len(unique_statement_hashes),
        }

    def analyze_anchor_types(self) -> Dict[str, Dict[str, int]]:
        """
        Analyzes the distribution of canonical anchor types.

        Returns:
            A dictionary containing counts for source, target, and overall anchor types.
        """
        source_types = Counter()
        target_types = Counter()
        overall_types = Counter()

        for stmt in self.statements:
            if stmt.source.type:
                source_types[stmt.source.type.value] += 1
                overall_types[stmt.source.type.value] += 1
            else:
                overall_types[self._infer_anchor_type_from_name(stmt.source)] += 1

            if stmt.target.type:
                target_types[stmt.target.type.value] += 1
                overall_types[stmt.target.type.value] += 1
            else:
                overall_types[self._infer_anchor_type_from_name(stmt.target)] += 1
        
        return {
            "source_anchor_types": dict(source_types),
            "target_anchor_types": dict(target_types),
            "overall_anchor_types": dict(overall_types),
        }

    def analyze_path_types(self) -> Dict[str, int]:
        """
        Analyzes the distribution of canonical path types.

        Returns:
            A dictionary with counts for each path type.
        """
        path_types_counter = Counter()

        for stmt in self.statements:
            # Prioritize explicit path_type if set
            if stmt.path_type:
                path_types_counter[stmt.path_type.value] += 1
            elif stmt.modifiers:
                # Infer from rule if path_type is not explicitly set
                if stmt.modifiers.rule == "causal":
                    path_types_counter[PathType.CAUSAL.value] += 1
                elif stmt.modifiers.rule == "logical":
                    path_types_counter[PathType.INFERENTIAL.value] += 1
                elif stmt.modifiers.rule == "definitional":
                    path_types_counter[PathType.SEMANTIC.value] += 1
                elif stmt.modifiers.rule == "empirical":
                    path_types_counter[PathType.INFERENTIAL.value] += 1 # Empirical usually leads to inference
                elif stmt.modifiers.rule == "inferential": # Added this line
                    path_types_counter[PathType.INFERENTIAL.value] += 1
                elif stmt.modifiers.intent: # Action path
                    path_types_counter[PathType.ACTION.value] += 1
                elif stmt.modifiers.focus or stmt.modifiers.perspective: # Cognitive path
                    path_types_counter[PathType.COGNITIVE.value] += 1
                else: # If modifiers are present but no specific rule/intent/focus/perspective match
                    path_types_counter["UNKNOWN"] += 1 
            else:
                path_types_counter["UNKNOWN"] += 1

        return dict(path_types_counter)

    def analyze_modifier_usage(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyzes the usage frequency and value distribution of modifiers.

        Returns:
            A dictionary with modifier statistics (frequency, common values, min/max for numeric).
        """
        modifier_counts = Counter()
        modifier_values: Dict[str, List[Any]] = {}

        for stmt in self.statements:
            if stmt.modifiers:
                # Use model_dump to get all fields including custom ones
                mod_dict = stmt.modifiers.model_dump(exclude_unset=True)
                for key, value in mod_dict.items():
                    modifier_counts[key] += 1
                    modifier_values.setdefault(key, []).append(value)
        
        stats: Dict[str, Dict[str, Any]] = {}
        for key, count in modifier_counts.items():
            value_list = modifier_values[key]
            key_stats: Dict[str, Any] = {"frequency": count}

            # For numeric values, calculate min, max, avg
            numeric_values = [v for v in value_list if isinstance(v, (int, float))]
            if numeric_values:
                key_stats["min"] = min(numeric_values)
                key_stats["max"] = max(numeric_values)
                if len(numeric_values) > 1:
                    key_stats["mean"] = statistics.mean(numeric_values)
                elif len(numeric_values) == 1:
                    key_stats["mean"] = numeric_values[0] # Handle single value mean
            
            # For all values, get most common
            # Convert non-hashable values (like dicts) to string representation for Counter
            hashable_value_list = []
            for v in value_list:
                if isinstance(v, (dict, list)):
                    hashable_value_list.append(str(v)) # Convert to string for hashing
                else:
                    hashable_value_list.append(v)

            value_counts = Counter(hashable_value_list)
            key_stats["most_common_values"] = value_counts.most_common(3) # Top 3 common values

            stats[key] = key_stats
        
        return stats

    def analyze_confidence_metrics(self) -> Dict[str, Any]:
        """
        Calculates statistics for confidence and certainty modifiers.

        Returns:
            A dictionary with min, max, mean, and count for confidence and certainty.
        """
        confidence_values = []
        certainty_values = []

        for stmt in self.statements:
            if stmt.modifiers and stmt.modifiers.confidence is not None:
                confidence_values.append(stmt.modifiers.confidence)
            if stmt.modifiers and stmt.modifiers.certainty is not None:
                certainty_values.append(stmt.modifiers.certainty)
        
        metrics: Dict[str, Any] = {}

        if confidence_values:
            metrics["confidence"] = {
                "count": len(confidence_values),
                "min": min(confidence_values),
                "max": max(confidence_values),
                "mean": statistics.mean(confidence_values) if len(confidence_values) > 0 else 0
            }
        if certainty_values:
            metrics["certainty"] = {
                "count": len(certainty_values),
                "min": min(certainty_values),
                "max": max(certainty_values),
                "mean": statistics.mean(certainty_values) if len(certainty_values) > 0 else 0
            }
        
        return metrics

    def identify_missing_provenance(self) -> List[Dict[str, Any]]:
        """
        Identifies statements with high confidence but missing provenance information.

        Returns:
            A list of dictionaries, each describing a statement with missing provenance.
        """
        missing_provenance_statements = []
        for stmt in self.statements:
            if stmt.modifiers and stmt.modifiers.confidence is not None and stmt.modifiers.confidence >= 0.85:
                # Check for critical provenance fields
                if not any([stmt.modifiers.source, stmt.modifiers.author, stmt.modifiers.timestamp]):
                    missing_provenance_statements.append({
                        "statement": str(stmt),
                        "confidence": stmt.modifiers.confidence,
                        "line": stmt.line,
                        "column": stmt.column,
                    })
        return missing_provenance_statements

    def get_graph_metrics(self) -> Dict[str, Any]:
        """
        Provides basic graph metrics if an STLGraph is available.

        Returns:
            A dictionary of graph metrics (nodes, edges, cycles, centrality).
        """
        if self.stl_graph:
            summary = self.stl_graph.summary
            cycles = self.stl_graph.find_cycles()
            centrality = self.stl_graph.get_node_centrality()

            # Convert centrality keys (Anchor IDs) to simple names if possible or keep full ID
            centrality_formatted = {
                k: v for k, v in centrality.items()
            }
            
            return {
                "nodes": summary["nodes"],
                "edges": summary["edges"],
                "cycles_count": len(cycles),
                "top_central_nodes": sorted(centrality_formatted.items(), key=lambda item: item[1], reverse=True)[:5],
            }
        return {}

    def get_full_analysis_report(self) -> Dict[str, Any]:
        """
        Generates a comprehensive analysis report.

        Returns:
            A dictionary containing all calculated metrics.
        """
        report = {
            "counts": self.count_elements(),
            "anchor_types_distribution": self.analyze_anchor_types(),
            "path_types_distribution": self.analyze_path_types(),
            "modifier_usage": self.analyze_modifier_usage(),
            "confidence_metrics": self.analyze_confidence_metrics(),
            "missing_provenance_high_confidence": self.identify_missing_provenance(),
        }
        
        graph_metrics = self.get_graph_metrics()
        if graph_metrics:
            report["graph_metrics"] = graph_metrics

        return report

    def _infer_anchor_type_from_name(self, anchor) -> AnchorType:
        """Helper to infer anchor type from name for analysis, if not explicit."""
        if anchor.type: # If type is already explicitly set, use it
            return anchor.type

        name = anchor.name
        # Check for specific patterns first
        if name.startswith("Event_") or "event" in name.lower() or "process" in name.lower() or "action" in name.lower():
            return AnchorType.EVENT
        if name.startswith("Question_") or "question" in name.lower() or "hypothesis" in name.lower() or "?" in name:
            return AnchorType.QUESTION
        if name.startswith("Agent_") or "agent" in name.lower() or "actor" in name.lower():
            return AnchorType.AGENT
        if name.startswith("Verifier_") or "verifier" in name.lower() or "test" in name.lower():
            return AnchorType.VERIFIER
        if name.startswith("Process_") or "process" in name.lower() or "transition" in name.lower():
            return AnchorType.PATH_SEGMENT

        # Proper noun check (PascalCase for single words often indicates a Name)
        if name and name[0].isupper() and (name.lower() != name) and ("_" not in name) and (not re.search(r'[A-Z][a-z]', name[1:])):
             return AnchorType.NAME
        
        return AnchorType.CONCEPT # Default to Concept for abstract ideas or unclassified


# Convenience function
def analyze_parse_result(parse_result: ParseResult, stl_graph: Optional[STLGraph] = None) -> Dict[str, Any]:
    """
    Convenience function to get a full analysis report for a ParseResult.
    """
    analyzer = STLAnalyzer(parse_result, stl_graph)
    return analyzer.get_full_analysis_report()
