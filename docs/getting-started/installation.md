# Installation

This guide covers how to install `stl-parser`, the Python toolkit for Semantic Tension Language.

## Requirements

- Python 3.9 or higher
- pip (included with Python)

## Install from Source

```bash
git clone https://github.com/scos-lab/semantic-tension-language.git
cd semantic-tension-language/parser
pip install -e .
```

This installs `stl-parser` in editable mode with all runtime dependencies:

| Dependency | Purpose |
|-----------|---------|
| [lark](https://github.com/lark-parser/lark) | Grammar parsing (EBNF) |
| [pydantic](https://github.com/pydantic/pydantic) | Type-safe data models (v2) |
| [rdflib](https://github.com/RDFLib/rdflib) | RDF/Turtle serialization |
| [networkx](https://github.com/networkx/networkx) | Graph analysis |
| [typer](https://github.com/tiangolo/typer) | CLI framework |
| [rich](https://github.com/Textualize/rich) | Terminal output formatting |

## Development Installation

For running tests, linting, and type checking:

```bash
pip install -e ".[dev]"
```

This adds: pytest, pytest-cov, hypothesis, black, mypy, ruff.

## Verify Installation

```bash
python -c "import stl_parser; print(stl_parser.__version__)"
```

Expected output:

```
1.7.0
```

## Verify CLI

```bash
stl --help
```

Expected output:

```
Usage: stl [OPTIONS] COMMAND [ARGS]...

A command-line tool for the Semantic Tension Language (STL) parser.

Commands:
  analyze          Analyzes an STL file and shows graph statistics.
  build            Build a single STL statement from CLI arguments.
  clean            Clean and repair STL text (LLM output pipeline).
  convert          Converts an STL file to another format.
  diff             Compute semantic diff between two STL files.
  parse            Parse an STL file and output the parsed result.
  patch            Apply a diff (JSON) to an STL file.
  query            Query an STL file with filters and field selection.
  schema-validate  Validate an STL file against a .stl.schema file.
  validate         Validates an STL file and reports any errors or...
```

## Quick Test

```python
from stl_parser import parse

result = parse('[Hello] -> [World] ::mod(confidence=1.0)')
assert result.is_valid
assert result.statements[0].source.name == "Hello"
print("STL parser is working!")
```

## Troubleshooting

**`ModuleNotFoundError: No module named 'stl_parser'`**
Make sure you ran `pip install -e .` from the `parser/` directory, not the repository root.

**`command not found: stl`**
The CLI requires the package to be installed (not just importable). Re-run `pip install -e .` and ensure your Python scripts directory is in your PATH.

**`ImportError: lark`**
Run `pip install lark>=1.1.0` or reinstall with `pip install -e .` which handles all dependencies.

---

Next: [Quickstart](quickstart.md) — Parse, build, and validate your first STL statements.
