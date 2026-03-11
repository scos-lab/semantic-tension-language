# CLI Reference

Complete reference for the `stl` command-line tool (10 commands).

**Install:** `pip install -e .` from the `parser/` directory.
**Usage:** `stl <command> [options]`

---

## validate

Validate an STL file and report errors/warnings.

```
stl validate <file>
```

Exit code: 0 (valid), 1 (errors found).

---

## parse

Parse an STL file and output as JSON.

```
stl parse <file> [--json/-j]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--json / -j` | `True` | Output as JSON |

---

## convert

Convert STL to another format.

```
stl convert <file> --to <format> [--format <rdf_format>] [--output <path>]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--to / -t` | `json` | Output format: `json`, `rdf`, `turtle`, `xml`, `nt`, `json-ld` |
| `--format / -f` | `turtle` | RDF sub-format (when `--to rdf`) |
| `--output / -o` | stdout | Write to file |

**Examples:**

```bash
stl convert data.stl --to json --output data.json
stl convert data.stl --to rdf --format turtle --output data.ttl
stl convert data.stl --to rdf --format json-ld
```

---

## analyze

Show graph statistics for an STL file.

```
stl analyze <file>
```

Reports: node/edge counts, density, cycles, conflicts, centrality rankings, tension metrics.

---

## build

Build a single STL statement.

```
stl build <source> <target> [--mod <modifiers>] [--output <path>]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--mod / -m` | — | Comma-separated `key=value` pairs |
| `--output / -o` | stdout | Write to file |

Values are auto-typed: `0.85` → float, `true` → bool, `hello` → string.

**Example:**

```bash
stl build "[Rain]" "[Flooding]" --mod "rule=causal,confidence=0.85,strength=0.8"
```

---

## clean

Clean and repair LLM-generated STL output.

```
stl clean <file> [--schema <path>] [--show-repairs] [--output <path>]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--schema / -s` | — | Schema file for post-repair validation |
| `--show-repairs` | `False` | Display repair actions as table |
| `--output / -o` | stdout | Write cleaned output to file |

**Example:**

```bash
stl clean llm_output.txt --show-repairs --output cleaned.stl
```

---

## schema-validate

Validate an STL file against a domain schema.

```
stl schema-validate <file> --schema <schema_path>
```

| Flag | Default | Description |
|------|---------|-------------|
| `--schema / -s` | (required) | Path to `.stl.schema` file |

Exit code: 0 (valid), 1 (errors).

**Example:**

```bash
stl schema-validate knowledge.stl --schema docs/schemas/medical.stl.schema
```

---

## query

Search and filter STL documents.

```
stl query <file> [--where <conditions>] [--select <fields>] [--pointer <path>]
                 [--format <fmt>] [--count] [--limit <n>]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--where / -w` | — | Filter: `field=value,field__op=value` |
| `--select / -s` | — | Project: comma-separated field names |
| `--pointer / -p` | — | STL pointer path (e.g., `/0/source/name`) |
| `--format / -f` | `table` | Output: `table`, `json`, `stl`, `csv` |
| `--count` | `False` | Only print match count |
| `--limit` | — | Maximum results |

**Operators for --where:**

`=`, `__gt=`, `__gte=`, `__lt=`, `__lte=`, `__ne=`, `__contains=`, `__startswith=`, `__in=` (pipe-separated values)

**Examples:**

```bash
stl query data.stl --where "rule=causal,confidence__gte=0.8"
stl query data.stl --select "source,target,confidence" --format csv
stl query data.stl --pointer "/0/source/name"
stl query data.stl --where "confidence__gte=0.9" --count
```

---

## diff

Compare two STL files.

```
stl diff <file_a> <file_b> [--format <fmt>] [--summary] [--quiet]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--format / -f` | `text` | Output: `text`, `json` |
| `--summary / -s` | `False` | Only print summary counts |
| `--quiet` | `False` | Exit code only: 0=identical, 1=different |

**Example:**

```bash
stl diff v1.stl v2.stl
stl diff v1.stl v2.stl --format json > changes.json
```

---

## patch

Apply a diff to an STL file.

```
stl patch <file> <diff_file> [--output <path>]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--output / -o` | stdout | Write patched output to file |

The diff file must be JSON format (produced by `stl diff --format json`).

**Example:**

```bash
stl patch base.stl changes.json --output patched.stl
```
