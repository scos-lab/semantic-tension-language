# STL CLI Extensions STLC Specification

> **Version:** 1.0.0
> **Type:** Extension
> **Target:** `stl_parser/cli.py` (modify existing)
> **Author:** Syn-claude
> **Date:** 2026-02-11
> **Status:** Draft

---

## 1. Scope Definition

[CLI_Extension] -> [Scope] ::mod(
  intent="Add build, clean, and schema-validate commands to existing CLI",
  boundaries="Extend cli.py with 3 new commands, reuse existing modules",
  confidence=0.95
)

**Included:**
- `stl build` — construct a single STL statement from command-line arguments
- `stl clean` — clean and repair LLM output from a file
- `stl schema-validate` — validate an STL file against a schema file

**Excluded:**
- Modification of existing commands (validate, convert, analyze, parse)
- Interactive/REPL mode
- Batch processing of multiple files
- Remote/network file sources

**Architecture Decision:**
[CLI_Structure] -> [Flat_Commands] ::mod(
  rule="definitional",
  confidence=1.0,
  intent="Use hyphenated flat commands (schema-validate) not subcommand groups — consistent with existing pattern"
)

---

## 2. Architecture Overview

[CLI_Extension] -> [Builder_Module] ::mod(
  rule="causal",
  intent="build command uses builder.stl() to construct statements",
  confidence=0.95
)

[CLI_Extension] -> [LLM_Module] ::mod(
  rule="causal",
  intent="clean command uses llm.validate_llm_output() for processing",
  confidence=0.95
)

[CLI_Extension] -> [Schema_Module] ::mod(
  rule="causal",
  intent="schema-validate and clean --schema use schema.load_schema() + validate_against_schema()",
  confidence=0.95
)

[CLI_Extension] -> [Existing_CLI] ::mod(
  rule="causal",
  intent="Extends existing Typer app with new @app.command() decorators",
  confidence=0.95
)

```
New imports to add to cli.py:
  from .builder import stl as stl_builder
  from .llm import validate_llm_output
  from .schema import load_schema, validate_against_schema
```

---

## 3. Command Specifications

### 3.1 `stl build`

[Entry] -> [Build_Command] ::mod(
  intent="Construct a single STL statement from CLI arguments",
  confidence=0.95
)

```
ENTRY: stl build <source> <target> [--mod MOD_STRING] [--output FILE]

INPUT:
  source: str (Typer.Argument)
    → Source anchor string, e.g. "[Theory]" or "Theory"
    → Help: "Source anchor (e.g. '[A]' or 'A')"

  target: str (Typer.Argument)
    → Target anchor string
    → Help: "Target anchor (e.g. '[B]' or 'B')"

  mod_string: Optional[str] (Typer.Option("--mod", "-m"))
    → Comma-separated key=value pairs
    → Example: "confidence=0.9,rule=causal"
    → Help: "Modifier key=value pairs, comma-separated"

  output_path: Optional[Path] (Typer.Option("--output", "-o"))
    → Write to file instead of stdout
    → Help: "Write output to file instead of stdout"

TRANSFORM:
  1. Parse mod_string into dict:
     IF mod_string is not None:
       Split on ',' → for each pair, split on '=' (first occurrence)
       → key = left.strip()
       → value = right.strip()
       → Try to parse value:
           - Strip surrounding quotes → string
           - "true"/"false" → bool
           - Contains '.' and is numeric → float
           - Is numeric → int
           - Otherwise → string

  2. Build statement:
     builder = stl_builder(source, target)
     IF modifiers: builder = builder.mod(**parsed_modifiers)
     stmt = builder.build()

  3. Output:
     stl_line = str(stmt)
     IF output_path: write to file
     ELSE: print to stdout

ERROR:
  ON build failure: handle_error(e) → exit 1

EXIT:
  console.print("[bold green]Built:[/bold green]")
  print(stl_line)
```

### 3.2 `stl clean`

[Entry] -> [Clean_Command] ::mod(
  intent="Clean and repair LLM output from a file",
  confidence=0.95
)

```
ENTRY: stl clean <file_path> [--schema FILE] [--show-repairs] [--output FILE]

INPUT:
  file_path: Path (Typer.Argument, exists=True, readable=True)
    → Input file containing raw/noisy STL text
    → Help: "Path to file containing STL text to clean"

  schema_path: Optional[Path] (Typer.Option("--schema", "-s"))
    → Optional schema file for validation
    → Help: "Schema file for validation after cleaning"

  show_repairs: bool (Typer.Option("--show-repairs", is_flag=True))
    → Show repair actions as Rich table
    → Default: False

  output_path: Optional[Path] (Typer.Option("--output", "-o"))
    → Write cleaned output to file
    → Help: "Write cleaned output to file"

TRANSFORM:
  1. Read file content: text = file_path.read_text(encoding="utf-8")

  2. Load schema if provided:
     IF schema_path:
       schema_text = schema_path.read_text(encoding="utf-8")
       schema = load_schema(schema_text)
     ELSE: schema = None

  3. Process: result = validate_llm_output(text, schema=schema)

  4. Display summary:
     console.print(f"Statements found: {len(result.statements)}")
     console.print(f"Valid: {result.is_valid}")
     console.print(f"Repairs applied: {len(result.repairs)}")

  5. IF show_repairs AND result.repairs:
     Rich Table with columns: Type, Description, Original → Repaired
     FOR each repair in result.repairs:
       table.add_row(repair.type, repair.description, f"{repair.original} → {repair.repaired}")

  6. Output cleaned text:
     IF output_path: write result.cleaned_text to file
     ELSE: print result.cleaned_text

ERROR:
  ON file read failure: handle_error(e)
  ON schema load failure: handle_error(e)

EXIT:
  IF result.is_valid:
    console.print("[bold green]Cleaning complete.[/bold green]")
  ELSE:
    console.print("[bold yellow]Cleaning complete with errors.[/bold yellow]")
    FOR error in result.errors: print error
```

### 3.3 `stl schema-validate`

[Entry] -> [Schema_Validate_Command] ::mod(
  intent="Validate an STL file against a schema definition",
  confidence=0.95
)

```
ENTRY: stl schema-validate <file_path> --schema <schema_path>

INPUT:
  file_path: Path (Typer.Argument, exists=True, readable=True)
    → STL file to validate
    → Help: "Path to the STL file to validate"

  schema_path: Path (Typer.Option("--schema", "-s"), exists=True, readable=True)
    → Schema file (required)
    → Help: "Path to the .stl.schema file"

TRANSFORM:
  1. Parse STL file: parse_result = parse_file(file_path)
     IF not parse_result.is_valid:
       console.print("[bold red]STL file has parse errors.[/bold red]")
       FOR error in parse_result.errors: print error
       EXIT code=1

  2. Load schema:
     schema_text = schema_path.read_text(encoding="utf-8")
     schema = load_schema(schema_text)

  3. Validate: validation = validate_against_schema(parse_result, schema)

  4. Display results:
     console.print(f"Schema: {validation.schema_name} v{validation.schema_version}")
     console.print(f"Statements: {len(parse_result.statements)}")

     IF validation.is_valid:
       console.print("[bold green]VALID: All statements conform to schema.[/bold green]")
     ELSE:
       console.print(f"[bold red]INVALID: {len(validation.errors)} error(s)[/bold red]")
       Rich Table: columns [Code, Message, Statement]
       FOR error in validation.errors:
         table.add_row(error.code, error.message, str(error.statement_index or "—"))

     IF validation.warnings:
       console.print(f"[bold yellow]{len(validation.warnings)} warning(s)[/bold yellow]")
       FOR warning in validation.warnings:
         console.print(f"  [{warning.code}] {warning.message}")

ERROR:
  ON parse_file failure: handle_error(e)
  ON schema load failure: handle_error(e)

EXIT:
  IF validation.is_valid: exit code=0
  ELSE: exit code=1
```

---

## 4. Modifier String Parsing (Internal Helper)

[Helper] -> [Parse_Mod_String] ::mod(
  intent="Parse comma-separated key=value string into dict",
  confidence=0.95
)

```
FUNCTION: _parse_mod_string(mod_string: str) -> Dict[str, Any]

INPUT: "confidence=0.9,rule=causal,author=\"Einstein\""

TRANSFORM:
  1. Split on ',' (respecting quoted strings)
  2. For each token:
     a. Split on first '='
     b. key = left.strip()
     c. raw_value = right.strip()
     d. Detect type:
        - Starts and ends with '"' or "'" → strip quotes → str
        - "true" / "false" (case-insensitive) → bool
        - Matches float pattern (contains '.') → float
        - Matches int pattern → int
        - Otherwise → str

OUTPUT: {"confidence": 0.9, "rule": "causal", "author": "Einstein"}

EDGE CASES:
  - Empty string → empty dict
  - Value with '=' in it → only split on first '='
  - Quoted value with comma → handle correctly
```

---

## 5. Consistency with Existing CLI

[Consistency] -> [Existing_Patterns] ::mod(
  rule="definitional",
  confidence=1.0
)

All new commands follow existing patterns:

| Pattern | How Applied |
|---------|-------------|
| `Annotated[Path, typer.Argument(...)]` | File path arguments with exists/readable checks |
| `handle_error(e)` | Error handling → formatted output + exit code 1 |
| `Rich Table` | Structured output (repairs, validation errors) |
| `console.print()` | Colored status messages |
| `typer.Exit(code=1)` | Non-zero exit for failures |
| `try/except` wrapping | Each command has try-except with handle_error fallback |

---

## 6. Usage Examples

### Build
```bash
# Simple statement
stl build "[Theory]" "[Prediction]"
# Output: [Theory] -> [Prediction]

# With modifiers
stl build "[A]" "[B]" --mod "confidence=0.9,rule=causal"
# Output: [A] -> [B] ::mod(confidence=0.9, rule="causal")

# To file
stl build "[A]" "[B]" --mod "confidence=0.9" --output statement.stl
```

### Clean
```bash
# Basic cleaning
stl clean llm_output.txt
# Shows: summary + cleaned text

# With repairs display
stl clean llm_output.txt --show-repairs
# Shows: summary + repair table + cleaned text

# With schema validation
stl clean llm_output.txt --schema events.stl.schema --output cleaned.stl
```

### Schema Validate
```bash
# Validate against schema
stl schema-validate research.stl --schema academic.stl.schema
# Output: VALID/INVALID with details
```
