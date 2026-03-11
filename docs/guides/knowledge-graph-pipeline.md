# How-To: Build a Knowledge Graph Pipeline

Build an end-to-end pipeline that takes text, converts it to STL, constructs a knowledge graph, and runs analysis. This guide covers the complete flow from raw data to graph insights.

**Prerequisites:** Familiarity with [parsing](../tutorials/01-parsing.md) and [building](../tutorials/02-building.md) tutorials.

---

## Pipeline Overview

```
Raw Text / LLM → STL Statements → Parse → Graph → Analysis
                                    ↓
                            JSON / RDF Export
```

---

## Step 1: Build STL from Data

### From structured data

```python
from stl_parser.builder import stl, stl_doc
from stl_parser import to_json

# Build a knowledge document programmatically
doc = stl_doc(
    stl("[Water] -> [H2O]").mod(rule="definitional", confidence=0.99),
    stl("[Rain] -> [Flooding]").mod(rule="causal", confidence=0.85, strength=0.80),
    stl("[Flooding] -> [Road_Closure]").mod(rule="causal", confidence=0.90, strength=0.85),
    stl("[Road_Closure] -> [Traffic_Disruption]").mod(rule="causal", confidence=0.95, strength=0.90),
    stl("[Deforestation] -> [Flooding]").mod(rule="causal", confidence=0.75, strength=0.60),
)
```

### From LLM output

```python
from stl_parser.llm import validate_llm_output

result = validate_llm_output(llm_text)
if result.is_valid:
    doc = result  # LLMValidationResult has .statements
```

### From file

```python
from stl_parser import parse_file

doc = parse_file("knowledge.stl")
```

---

## Step 2: Construct the Graph

```python
from stl_parser import STLGraph

graph = STLGraph(doc)

# Basic statistics
print(graph.summary)
# {"nodes": 5, "edges": 4}
```

---

## Step 3: Analyze the Graph

### Path analysis

Find all paths between two concepts:

```python
paths = graph.find_paths("Rain", "Traffic_Disruption")
for path in paths:
    print(" -> ".join(path))
# Rain -> Flooding -> Road_Closure -> Traffic_Disruption
```

### Cycle detection

```python
cycles = graph.find_cycles()
if cycles:
    for cycle in cycles:
        print("Cycle:", " -> ".join(cycle))
else:
    print("No cycles detected")
```

### Centrality analysis

Find the most connected nodes:

```python
centrality = graph.get_node_centrality()
sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
for node, score in sorted_nodes[:5]:
    print(f"  {node}: {score:.3f}")
```

### Node degree

```python
degree = graph.get_node_degree("Flooding")
print(f"Flooding has {degree} connections")
```

---

## Step 4: Full Analysis Report

Use `STLAnalyzer` for comprehensive statistics:

```python
from stl_parser import STLAnalyzer

analyzer = STLAnalyzer(doc)
report = analyzer.get_full_analysis_report()

# Element counts
print(report["counts"])
# {"total_statements": 5, "unique_anchors": 6}

# Confidence statistics
print(report["confidence_metrics"])
# {"min": 0.75, "max": 0.99, "mean": 0.888, ...}

# Path type distribution
print(report["path_types"])

# Modifier usage frequency
print(report["modifier_usage"])

# Graph metrics (nodes, edges, cycles, centrality)
print(report["graph_metrics"])
```

### Find missing provenance

Identify high-confidence claims without source references:

```python
missing = analyzer.identify_missing_provenance()
for item in missing:
    print(f"Statement {item['index']}: confidence={item['confidence']} but no source")
```

---

## Step 5: Filter by Domain

Extract a subgraph for a specific domain:

```python
from stl_parser.builder import stl, stl_doc
from stl_parser import STLGraph

doc = stl_doc(
    stl("[Physics:Energy] -> [Physics:Mass]").mod(rule="logical", confidence=0.99, domain="physics"),
    stl("[Biology:Cell] -> [Biology:Organism]").mod(rule="definitional", confidence=0.95, domain="biology"),
    stl("[Physics:Force] -> [Physics:Acceleration]").mod(rule="logical", confidence=0.98, domain="physics"),
)

graph = STLGraph(doc)

# Get only physics subgraph
physics_graph = graph.get_subgraph("physics")
print(physics_graph.summary)
# {"nodes": 4, "edges": 2}
```

---

## Step 6: Detect Conflicts

Find functional relation violations (where a source should have only one target):

```python
# Define which relations are functional (one source → one target)
functional = {"definitional", "identity"}

conflicts = graph.detect_conflicts(functional_relations=functional)
for conflict in conflicts:
    print(f"Conflict: {conflict}")
```

---

## Step 7: Calculate Tension Metrics

Get graph-wide tension scores:

```python
metrics = graph.calculate_tension_metrics()
print(metrics)
# {"tension_density": 0.75, "max_tension": 0.95, ...}
```

---

## Step 8: Export Results

### To JSON

```python
from stl_parser import to_json

print(to_json(doc, indent=2))
```

### To RDF/Turtle

```python
from stl_parser.serializer import to_rdf

turtle = to_rdf(doc, format="turtle")
print(turtle)
```

### To STL text

```python
from stl_parser import to_stl

print(to_stl(doc))
```

---

## Full Pipeline Example

```python
from stl_parser.builder import stl, stl_doc
from stl_parser import STLGraph, STLAnalyzer, to_json
from stl_parser.serializer import to_rdf

# 1. Build knowledge
doc = stl_doc(
    stl("[Smoking] -> [Lung_Cancer]").mod(
        rule="causal", confidence=0.92, strength=0.88,
        source="doi:10.1016/cancer.2020"
    ),
    stl("[Lung_Cancer] -> [Mortality]").mod(
        rule="causal", confidence=0.85, strength=0.75
    ),
    stl("[Exercise] -> [Lung_Cancer]").mod(
        rule="correlative", confidence=0.65, strength=0.40
    ),
    stl("[Genetics] -> [Lung_Cancer]").mod(
        rule="causal", confidence=0.70, strength=0.55
    ),
)

# 2. Build graph
graph = STLGraph(doc)
print(f"Graph: {graph.summary}")

# 3. Analyze
analyzer = STLAnalyzer(doc)
report = analyzer.get_full_analysis_report()

# 4. Find key insights
print(f"\nMost central nodes:")
centrality = graph.get_node_centrality()
for node, score in sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:3]:
    print(f"  {node}: {score:.3f}")

print(f"\nConfidence stats: {report['confidence_metrics']}")

paths = graph.find_paths("Smoking", "Mortality")
print(f"\nPaths from Smoking to Mortality:")
for path in paths:
    print(f"  {' -> '.join(path)}")

# 5. Export
with open("output.json", "w") as f:
    f.write(to_json(doc, indent=2))
```

---

## See Also

- [Tutorial: Parsing](../tutorials/01-parsing.md) — Parse STL documents
- [API: graph](../reference/api/graph.md) — STLGraph and STLAnalyzer reference
- [How-To: Confidence Decay](confidence-decay.md) — Temporal knowledge management
- [How-To: LLM Integration](llm-integration.md) — Get STL from language models
