# Semantic Tension Language (STL)

**STL** is a calculable, universal standard for structuring knowledge through directional semantic relations. It introduces a **tension-path model** where knowledge flows directionally from source to target, carrying semantic magnitude and type information.

Unlike JSON or plain text, STL statements are not just data — they are **traceable, verifiable, and inference-ready**.

```stl
[Theory_Relativity] -> [Prediction_TimeDilation] ::mod(
  rule="logical",
  confidence=0.99,
  source="doi:10.1002/andp.19053221004",
  author="Einstein"
)
```

---

## Key Features

- **Human-readable yet machine-executable** — Designed for both human comprehension and computational processing
- **Traceable and verifiable** — Every statement can embed provenance, confidence, and evidence
- **Inference-friendly** — Supports reasoning, verification, and knowledge graph construction
- **Token-efficient** — Compact syntax optimized for LLM context windows
- **Unicode-native** — Full support for Chinese, Arabic, and all Unicode scripts

## Python Tooling (stl-parser)

A comprehensive Python toolkit for working with STL, with feature parity to the JSON ecosystem:

| Capability | Description |
|-----------|-------------|
| **Parse & Serialize** | `parse()`, `to_json()`, `to_stl()`, `to_rdf()` |
| **Build Programmatically** | `stl("[A]", "[B]").mod(confidence=0.9).build()` |
| **Schema Validation** | `.stl.schema` format + 6 domain schemas (TCM, medical, legal, ...) |
| **LLM Output Repair** | `clean()` + `repair()` + `validate_llm_output()` — 3-stage pipeline |
| **Query & Filter** | `find()`, `filter()`, `select()`, `stl_pointer()` — Django-style operators |
| **Diff & Patch** | `stl_diff()`, `stl_patch()` — semantic-level comparison |
| **Streaming I/O** | `STLEmitter` (write) + `STLReader` (read) + tail mode |
| **Graph Analysis** | NetworkX integration, cycle detection, centrality analysis |
| **Confidence Decay** | Time-based knowledge freshness with configurable half-life |
| **CLI** | `stl validate`, `stl query`, `stl diff`, `stl patch`, and more |

### Quick Install

```bash
git clone https://github.com/scos-lab/semantic-tension-language.git
cd semantic-tension-language/parser
pip install -e .
```

### Quick Example

```python
from stl_parser import parse, stl, stl_doc, validate_llm_output

# Parse STL text
result = parse('[Einstein] -> [Theory_Relativity] ::mod(confidence=0.98, rule="empirical")')
print(result.statements[0].source.name)  # "Einstein"

# Build programmatically
stmt = stl("[Rain]", "[Flooding]").mod(confidence=0.85, rule="causal", strength=0.8).build()
print(str(stmt))  # [Rain] -> [Flooding] ::mod(confidence=0.85, ...)

# Clean LLM output
llm_result = validate_llm_output("A => B mod(confience=1.5)")
print(f"Valid: {llm_result.is_valid}, Repairs: {len(llm_result.repairs)}")
```

### CLI

```bash
stl validate input.stl                     # Validate
stl query input.stl --where "rule=causal"  # Query
stl diff a.stl b.stl                       # Compare
stl patch a.stl diff.json                  # Apply patch
```

---

## Documentation

### Specifications
- [STL Core Specification v1.0](./spec/stl-core-spec-v1.0.md)
- [STL Core Specification Supplement](./spec/stl-core-spec-v1.0-supplement.md)

### Developer Documentation
- [Getting Started](./docs/getting-started/) — Installation, quickstart, key concepts
- [Tutorials](./docs/tutorials/) — Step-by-step guides for each capability
- [API Reference](./docs/reference/) — Complete API and CLI documentation
- [How-To Guides](./docs/guides/) — Task-oriented guides for common workflows

### Project Resources
- [Project Index](./docs/PROJECT_INDEX.md) — Module reference and architecture overview
- [Tooling Features (Chinese)](./docs/STL_TOOLING_FEATURES.md) — Detailed feature overview
- [Schema Ecosystem](./docs/schemas/) — Domain-specific schema library
- [STL as LLM-Program Bridge](./docs/STL_AS_LLM_PROGRAM_BRIDGE.md) — Vision document

---

## Repository Structure

```
semantic-tension-language/
├── spec/                    # Language specifications (v1.0)
├── docs/                    # Documentation library
│   ├── getting-started/     # Installation, quickstart, key concepts
│   ├── tutorials/           # Step-by-step learning guides
│   ├── reference/           # API reference and CLI docs
│   ├── guides/              # How-to guides
│   ├── schemas/             # Domain schema library (6 domains)
│   └── stlc/                # STLC semantic specifications (10 specs)
└── parser/                  # Python package (stl-parser)
    ├── stl_parser/          # Source (19 modules)
    └── tests/               # Test suite (530 tests, 88% coverage)
```

---

## License

- **Code:** Apache License 2.0
- **Specification:** CC BY 4.0

## Contributing

STL is an open standard. We welcome issues, discussions, and contributions. See [parser/CONTRIBUTING.md](./parser/CONTRIBUTING.md) for guidelines.

## Citation

```
Wuko. (2025). Semantic Tension Language (STL): A Theoretical Framework
for Structured and Interpretable Knowledge Representation (v1.0).
Zenodo. https://doi.org/10.5281/zenodo.17585432
```
