# STL Documentation

Welcome to the documentation for **Semantic Tension Language (STL)** and its Python toolkit `stl-parser`.

STL is a calculable, universal standard for structuring knowledge through directional semantic relations. It introduces a **tension-path model** where knowledge flows directionally from source to target, carrying semantic magnitude and type information.

```stl
[Theory_Relativity] -> [Prediction_TimeDilation] ::mod(
  rule="logical",
  confidence=0.99,
  source="doi:10.1002/andp.19053221004",
  author="Einstein"
)
```

Unlike JSON or plain text, STL statements are **traceable, verifiable, and inference-ready**.

---

## Where to Start

### New to STL?

1. **[Installation](getting-started/installation.md)** — Install `stl-parser` in under a minute
2. **[Quickstart](getting-started/quickstart.md)** — Parse, build, and validate your first STL statements
3. **[Key Concepts](getting-started/key-concepts.md)** — Understand anchors, paths, modifiers, and the tension-path model

### Learning STL

Step-by-step tutorials covering every capability:

| # | Tutorial | What You'll Learn |
|---|----------|-------------------|
| 01 | [Parsing](tutorials/01-parsing.md) | Parse STL text and files, inspect results |
| 02 | [Building](tutorials/02-building.md) | Build statements programmatically |
| 03 | [Schema Validation](tutorials/03-schema-validation.md) | Validate documents against domain schemas |
| 04 | [LLM Pipeline](tutorials/04-llm-pipeline.md) | Clean and repair LLM-generated output |
| 05 | [Querying](tutorials/05-querying.md) | Query, filter, and select statements |
| 06 | [Streaming I/O](tutorials/06-streaming-io.md) | Read and write STL streams |
| 07 | [Diff & Patch](tutorials/07-diff-patch.md) | Compare and patch documents |
| 08 | [CLI Tools](tutorials/08-cli-tools.md) | Command-line workflows |

### Looking Something Up?

- **[API Reference](reference/)** — Complete function and class documentation
- **[CLI Reference](reference/cli.md)** — All 10 CLI commands with examples
- **[Modifier Reference](reference/modifiers.md)** — All 30+ modifier fields
- **[Error Codes](reference/error-codes.md)** — E001-E969, W001-W099 with fixes
- **[STL Syntax Card](reference/stl-syntax.md)** — One-page syntax quick reference

### Solving a Specific Problem?

- **[Custom Schemas](guides/custom-schemas.md)** — Create domain-specific validation schemas
- **[LLM Integration](guides/llm-integration.md)** — Use STL with ChatGPT, Claude, and other LLMs
- **[Knowledge Graph Pipeline](guides/knowledge-graph-pipeline.md)** — Build end-to-end knowledge graphs
- **[Event Logging](guides/event-logging.md)** — Use STL for structured event logging
- **[Confidence Decay](guides/confidence-decay.md)** — Manage knowledge freshness over time

---

## Specifications

- [STL Core Specification v1.0](../spec/stl-core-spec-v1.0.md) — The formal language specification
- [STL Core Specification Supplement](../spec/stl-core-spec-v1.0-supplement.md) — Extended features and semantics

## Project

- [Project Index](PROJECT_INDEX.md) — Module reference and architecture overview
- [Schema Ecosystem](schemas/) — 6 domain-specific schemas + template
- [GitHub Repository](https://github.com/scos-lab/semantic-tension-language)
