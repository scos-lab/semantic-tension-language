# API: graph & analyzer

Graph construction and analysis for STL documents.

**Module:** `stl_parser.graph`, `stl_parser.analyzer`
**Import:** `from stl_parser import STLGraph, STLAnalyzer`

---

## STLGraph

NetworkX-based directed multigraph built from STL statements.

### Constructor

```python
STLGraph(parse_result: Optional[ParseResult] = None)
```

### Factory Method

```python
STLGraph.from_parse_result(parse_result: ParseResult) -> STLGraph
```

### Methods

| Method | Parameters | Return Type | Description |
|--------|-----------|-------------|-------------|
| `build_graph(parse_result)` | `ParseResult` | `None` | Build graph from statements |
| `find_paths(source_id, target_id)` | `str, str` | `List[List[str]]` | Find all simple paths between nodes |
| `find_cycles()` | — | `List[List[str]]` | Find all simple cycles |
| `get_node_degree(anchor_id)` | `str` | `int` | Total degree (in + out) of a node |
| `get_node_centrality()` | — | `Dict[str, float]` | Degree centrality for all nodes |
| `get_subgraph(domain)` | `str` | `STLGraph` | Subgraph filtered by domain modifier |
| `detect_conflicts(functional_relations)` | `Optional[set]` | `List[Dict]` | Detect functional relation violations |
| `calculate_tension_metrics()` | — | `Dict[str, Any]` | Graph-wide tension scores |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `summary` | `Dict[str, int]` | Node and edge counts |

### Example

```python
from stl_parser import parse, STLGraph

result = parse("""
[A] -> [B] ::mod(rule="causal", confidence=0.9)
[B] -> [C] ::mod(rule="causal", confidence=0.8)
[C] -> [A] ::mod(rule="logical", confidence=0.7)
""")

graph = STLGraph(result)
print(graph.summary)            # {"nodes": 3, "edges": 3}
print(graph.find_cycles())      # [["A", "B", "C"]]
print(graph.get_node_centrality())
```

---

## STLAnalyzer

Comprehensive statistical analysis of STL documents.

### Constructor

```python
STLAnalyzer(
    parse_result: ParseResult,
    stl_graph: Optional[STLGraph] = None
)
```

Auto-constructs an `STLGraph` if none provided.

### Methods

| Method | Return Type | Description |
|--------|------------|-------------|
| `count_elements()` | `Dict[str, int]` | Total statements, unique anchors |
| `analyze_anchor_types()` | `Dict` | Source/target anchor type distribution |
| `analyze_path_types()` | `Dict[str, int]` | Path type distribution |
| `analyze_modifier_usage()` | `Dict` | Modifier frequency, min/max, common values |
| `analyze_confidence_metrics()` | `Dict` | Confidence/certainty stats (min, max, mean) |
| `identify_missing_provenance()` | `List[Dict]` | High-confidence statements missing source |
| `get_graph_metrics()` | `Dict` | Nodes, edges, cycles, centrality |
| `get_full_analysis_report()` | `Dict` | All metrics combined |

### Convenience Function

```python
from stl_parser.analyzer import analyze_parse_result

report = analyze_parse_result(result)
```

### Example

```python
from stl_parser import parse, STLAnalyzer

result = parse("""
[Rain] -> [Flooding] ::mod(rule="causal", confidence=0.85, strength=0.8)
[Smoking] -> [Lung_Cancer] ::mod(rule="causal", confidence=0.92)
[Water] -> [H2O] ::mod(rule="definitional", confidence=0.99)
""")

analyzer = STLAnalyzer(result)
report = analyzer.get_full_analysis_report()
print(report["counts"])
print(report["confidence_metrics"])
```
