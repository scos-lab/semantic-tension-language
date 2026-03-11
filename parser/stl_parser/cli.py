# -*- coding: utf-8 -*-
"""
STL Parser Command-Line Interface (CLI)

This module provides a CLI for parsing, validating, and converting STL files.
"""

import typer
from typing_extensions import Annotated
from typing import Any, Dict, List, Optional
import csv
import io
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

from .parser import parse_file
from .validator import validate_parse_result
from .serializer import to_json, to_rdf
from .graph import STLGraph
from .errors import STLError
from .builder import stl as stl_builder
from .llm import validate_llm_output
from .schema import load_schema, validate_against_schema
from .query import find_all, filter_statements, select, stl_pointer
from .diff import stl_diff, stl_patch, diff_to_text, diff_to_dict

# Create a Typer app
app = typer.Typer(
    name="stl",
    help="A command-line tool for the Semantic Tension Language (STL) parser.",
    add_completion=False,
)

# Rich console for beautiful output
console = Console()


def handle_error(e: Exception):
    """Handles errors and prints them to the console."""
    if isinstance(e, typer.Exit):
        raise e  # Re-raise typer.Exit directly
    if isinstance(e, STLError):
        console.print(f"[bold red]Error [{e.code}]:[/bold red] {e.message}")
        if e.suggestion:
            console.print(f"[yellow]Suggestion:[/yellow] {e.suggestion}")
        if e.line:
            console.print(f"  at line {e.line}, column {e.column or '?'}")
    else:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")
    raise typer.Exit(code=1)


@app.command()
def validate(
    file_path: Annotated[Path, typer.Argument(help="Path to the STL file to validate.", exists=True, file_okay=True, dir_okay=False, readable=True)],
):
    """
    Validates an STL file and reports any errors or warnings.
    """
    try:
        parse_result = parse_file(file_path)
        
        # Perform validation
        validated_result = validate_parse_result(parse_result)
        
        if validated_result.is_valid and not validated_result.warnings:
            console.print("[bold green]SUCCESS: STL file is valid.[/bold green]")
            console.print(f"  - Statements found: {len(validated_result.statements)}")

        if validated_result.warnings:
            console.print(f"[bold yellow]Found {len(validated_result.warnings)} warning(s):[/bold yellow]")
            for warning in validated_result.warnings:
                console.print(f"  - [yellow][{warning.code}][/yellow] {warning.message} (line {warning.line or '?'})")
        
        if not validated_result.is_valid:
            console.print(f"[bold red]Found {len(validated_result.errors)} error(s):[/bold red]")
            for error in validated_result.errors:
                console.print(f"  - [red][{error.code}][/red] {error.message} (line {error.line or '?'})")
                if error.suggestion:
                    console.print(f"    [yellow]Suggestion:[/yellow] {error.suggestion}")
            raise typer.Exit(code=1)
            
    except typer.Exit:
        raise
    except Exception as e:
        handle_error(e)


@app.command(name="parse")
def parse_command(
    file_path: Annotated[Path, typer.Argument(help="Path to the STL file to parse.", exists=True, file_okay=True, dir_okay=False, readable=True)],
    output_json: Annotated[bool, typer.Option("--json", "-j", help="Output the parsed result as JSON.")] = True,
):
    """
    Parses an STL file and prints the structured result.
    (This is an alias for the 'convert' command to JSON format)
    """
    if output_json:
        convert(file_path, to_format="json")
    else:
        console.print("Please specify an output format. Defaulting to JSON.")
        convert(file_path, to_format="json")


@app.command()
def convert(
    file_path: Annotated[Path, typer.Argument(help="Path to the STL file to convert.", exists=True, file_okay=True, dir_okay=False, readable=True)],
    to_format: Annotated[str, typer.Option("--to", "-t", help="The output format (json, rdf, turtle, xml, nt, json-ld).")] = "json",
    rdf_format: Annotated[str, typer.Option("--format", "-f", help="Specific RDF format (turtle, xml, nt, json-ld). Defaults to turtle for RDF.")] = "turtle",
    output_path: Annotated[Optional[Path], typer.Option("--output", "-o", help="Write output to file instead of stdout.")] = None,
):
    """
    Converts an STL file to another format (e.g., JSON, RDF/Turtle).
    """
    try:
        parse_result = parse_file(file_path)
        
        if not parse_result.is_valid:
            console.print("[bold red]STL file is invalid. Cannot convert.[/bold red]")
            for error in parse_result.errors:
                console.print(f"  - [red][{error.code}][/red] {error.message} (line {error.line or '?'})")
            raise typer.Exit(code=1)

        output_content = ""

        if to_format.lower() == "json":
            output_content = to_json(parse_result, indent=2)
        
        elif to_format.lower() in ("rdf", "turtle", "xml", "nt", "json-ld"):
            # Determine format
            fmt = rdf_format
            # If user specified a specific format in --to (e.g. --to turtle), use that
            if to_format.lower() != "rdf":
                 fmt = to_format.lower()
            
            output_content = to_rdf(parse_result, format=fmt)
            
        else:
            console.print(f"[bold red]Error:[/bold red] Unsupported format '{to_format}'. Supported: json, rdf, turtle, xml, nt, json-ld.")
            raise typer.Exit(code=1)

        # Output handling
        if output_path:
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(output_content)
                console.print(f"[bold green]Successfully converted to {output_path}[/bold green]")
            except Exception as e:
                console.print(f"[bold red]Error writing output file:[/bold red] {e}")
                raise typer.Exit(code=1)
        else:
            print(output_content)

    except typer.Exit:
        raise
    except Exception as e:
        handle_error(e)


@app.command()
def analyze(
    file_path: Annotated[Path, typer.Argument(help="Path to the STL file to analyze.", exists=True, file_okay=True, dir_okay=False, readable=True)],
):
    """
    Analyzes an STL file and shows graph statistics.
    """
    try:
        parse_result = parse_file(file_path)

        if not parse_result.is_valid:
            console.print("[bold red]STL file is invalid. Cannot analyze.[/bold red]")
            for error in parse_result.errors:
                console.print(f"  - [red][{error.code}][/red] {error.message} (line {error.line or '?'})")
            raise typer.Exit(code=1)

        # Build graph
        stl_graph = STLGraph(parse_result)
        summary = stl_graph.summary
        
        console.print("[bold cyan]Graph Analysis:[/bold cyan]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="dim")
        table.add_column("Value")
        
        table.add_row("Total Statements", str(len(parse_result.statements)))
        table.add_row("Total Nodes (Anchors)", str(summary["nodes"]))
        table.add_row("Total Edges (Relationships)", str(summary["edges"]))
        
        cycles = stl_graph.find_cycles()
        table.add_row("Cycles Found", str(len(cycles)))
        
        # Tension Analysis
        tension_metrics = stl_graph.calculate_tension_metrics()
        table.add_row("Semantic Conflicts", f"[red]{tension_metrics['conflict_count']}[/red]" if tension_metrics['conflict_count'] > 0 else "0")
        table.add_row("Total Tension Score", f"{tension_metrics['total_tension_score']:.2f}")
        
        console.print(table)
        
        if cycles:
            console.print("[bold yellow]Cycles:[/bold yellow]")
            for i, cycle in enumerate(cycles, 1):
                console.print(f"  {i}. {' -> '.join(cycle)} -> {cycle[0]}")

        if tension_metrics['conflict_count'] > 0:
            console.print(f"\n[bold red]Semantic Conflicts Detected ({tension_metrics['conflict_count']}):[/bold red]")
            conflicts = stl_graph.detect_conflicts()
            for i, c in enumerate(conflicts, 1):
                console.print(f"  {i}. [bold]{c['source']}[/bold] has conflicting targets for relation '[cyan]{c['relation']}[/cyan]':")
                for t in c['targets']:
                    console.print(f"     - [dim]{t['target']}[/dim] (conf: {t['confidence']:.2f})")

        # Centrality
        try:
            centrality = stl_graph.get_node_centrality()
            if centrality:
                console.print("\n[bold cyan]Top 5 Most Central Nodes (by degree):[/bold cyan]")
                sorted_centrality = sorted(centrality.items(), key=lambda item: item[1], reverse=True)
                
                centrality_table = Table(show_header=True, header_style="bold magenta")
                centrality_table.add_column("Rank", style="dim")
                centrality_table.add_column("Node")
                centrality_table.add_column("Centrality Score")

                for i, (node, score) in enumerate(sorted_centrality[:5], 1):
                    centrality_table.add_row(str(i), node, f"{score:.3f}")
                console.print(centrality_table)
        except Exception:
            console.print("\n[yellow]Could not compute centrality, graph may be empty or invalid.[/yellow]")


    except typer.Exit:
        raise
    except Exception as e:
        handle_error(e)


def _parse_mod_string(mod_string: str) -> dict:
    """Parse comma-separated key=value string into a dict.

    Values are auto-typed: float, int, bool, or string.
    """
    if not mod_string or not mod_string.strip():
        return {}

    result = {}
    for pair in mod_string.split(","):
        pair = pair.strip()
        if not pair:
            continue
        if "=" not in pair:
            continue
        key, raw_value = pair.split("=", 1)
        key = key.strip()
        raw_value = raw_value.strip()

        # Strip quotes
        if len(raw_value) >= 2 and raw_value[0] in ('"', "'") and raw_value[-1] == raw_value[0]:
            result[key] = raw_value[1:-1]
            continue

        # Bool
        if raw_value.lower() == "true":
            result[key] = True
            continue
        if raw_value.lower() == "false":
            result[key] = False
            continue

        # Float
        try:
            if "." in raw_value:
                result[key] = float(raw_value)
                continue
        except ValueError:
            pass

        # Int
        try:
            result[key] = int(raw_value)
            continue
        except ValueError:
            pass

        # String fallback
        result[key] = raw_value

    return result


@app.command()
def build(
    source: Annotated[str, typer.Argument(help="Source anchor (e.g. '[A]' or 'A').")],
    target: Annotated[str, typer.Argument(help="Target anchor (e.g. '[B]' or 'B').")],
    mod: Annotated[Optional[str], typer.Option("--mod", "-m", help="Modifier key=value pairs, comma-separated.")] = None,
    output_path: Annotated[Optional[Path], typer.Option("--output", "-o", help="Write output to file instead of stdout.")] = None,
):
    """
    Builds a single STL statement from command-line arguments.
    """
    try:
        builder = stl_builder(source, target)
        if mod:
            parsed_mods = _parse_mod_string(mod)
            if parsed_mods:
                builder = builder.mod(**parsed_mods)

        stmt = builder.build()
        stl_line = str(stmt)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(stl_line + "\n")
            console.print(f"[bold green]Built and saved to {output_path}[/bold green]")
        else:
            console.print("[bold green]Built:[/bold green]")
            print(stl_line)

    except typer.Exit:
        raise
    except Exception as e:
        handle_error(e)


@app.command()
def clean(
    file_path: Annotated[Path, typer.Argument(help="Path to file containing STL text to clean.", exists=True, file_okay=True, dir_okay=False, readable=True)],
    schema_path: Annotated[Optional[Path], typer.Option("--schema", "-s", help="Schema file for validation after cleaning.")] = None,
    show_repairs: Annotated[bool, typer.Option("--show-repairs", help="Show repair actions as a table.")] = False,
    output_path: Annotated[Optional[Path], typer.Option("--output", "-o", help="Write cleaned output to file.")] = None,
):
    """
    Cleans and repairs LLM-generated STL output from a file.
    """
    try:
        text = file_path.read_text(encoding="utf-8")

        schema = None
        if schema_path:
            schema_text = schema_path.read_text(encoding="utf-8")
            schema = load_schema(schema_text)

        result = validate_llm_output(text, schema=schema)

        # Summary
        console.print(f"  Statements found: {len(result.statements)}")
        console.print(f"  Valid: {result.is_valid}")
        console.print(f"  Repairs applied: {len(result.repairs)}")

        # Repair table
        if show_repairs and result.repairs:
            repair_table = Table(show_header=True, header_style="bold magenta")
            repair_table.add_column("Type", style="dim")
            repair_table.add_column("Description")
            for r in result.repairs:
                repair_table.add_row(r.type, r.description)
            console.print(repair_table)

        # Output
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result.cleaned_text)
            console.print(f"[bold green]Cleaned output saved to {output_path}[/bold green]")
        else:
            if result.cleaned_text.strip():
                print(result.cleaned_text)

        if result.is_valid:
            console.print("[bold green]Cleaning complete.[/bold green]")
        else:
            console.print("[bold yellow]Cleaning complete with errors.[/bold yellow]")
            for error in result.errors:
                console.print(f"  - [red]{error.code}[/red] {error.message}")

    except typer.Exit:
        raise
    except Exception as e:
        handle_error(e)


@app.command(name="schema-validate")
def schema_validate(
    file_path: Annotated[Path, typer.Argument(help="Path to the STL file to validate.", exists=True, file_okay=True, dir_okay=False, readable=True)],
    schema_path: Annotated[Path, typer.Option("--schema", "-s", help="Path to the .stl.schema file.")],
):
    """
    Validates an STL file against a schema definition.
    """
    try:
        parse_result = parse_file(file_path)

        if not parse_result.is_valid:
            console.print("[bold red]STL file has parse errors.[/bold red]")
            for error in parse_result.errors:
                console.print(f"  - [red][{error.code}][/red] {error.message} (line {error.line or '?'})")
            raise typer.Exit(code=1)

        schema_text = schema_path.read_text(encoding="utf-8")
        schema = load_schema(schema_text)

        validation = validate_against_schema(parse_result, schema)

        console.print(f"  Schema: {validation.schema_name} v{validation.schema_version}")
        console.print(f"  Statements: {len(parse_result.statements)}")

        if validation.is_valid:
            console.print("[bold green]VALID: All statements conform to schema.[/bold green]")
        else:
            console.print(f"[bold red]INVALID: {len(validation.errors)} error(s)[/bold red]")

            error_table = Table(show_header=True, header_style="bold magenta")
            error_table.add_column("Code", style="dim")
            error_table.add_column("Message")
            error_table.add_column("Statement")

            for err in validation.errors:
                stmt_idx = str(err.statement_index) if err.statement_index is not None else "-"
                error_table.add_row(err.code, err.message, stmt_idx)

            console.print(error_table)
            raise typer.Exit(code=1)

        if validation.warnings:
            console.print(f"[bold yellow]{len(validation.warnings)} warning(s)[/bold yellow]")
            for w in validation.warnings:
                console.print(f"  - [{w.code}] {w.message}")

    except typer.Exit:
        raise
    except Exception as e:
        handle_error(e)


def _parse_where_string(where: str) -> Dict[str, Any]:
    """Parse --where string into kwargs for query functions.

    Input:  "confidence__gt=0.8,rule=causal"
    Output: {"confidence__gt": 0.8, "rule": "causal"}

    The __op suffix is preserved in the key (unlike _parse_mod_string).
    Special: __in operator splits the value on '|' to produce a list.
    """
    if not where or not where.strip():
        return {}

    result: Dict[str, Any] = {}
    for pair in where.split(","):
        pair = pair.strip()
        if not pair:
            continue
        if "=" not in pair:
            continue
        key, raw_value = pair.split("=", 1)
        key = key.strip()
        raw_value = raw_value.strip()

        # __in operator: split value on '|'
        if key.endswith("__in"):
            result[key] = [v.strip().strip("\"'") for v in raw_value.split("|")]
            continue

        # Strip quotes
        if len(raw_value) >= 2 and raw_value[0] in ('"', "'") and raw_value[-1] == raw_value[0]:
            result[key] = raw_value[1:-1]
            continue

        # Bool
        if raw_value.lower() == "true":
            result[key] = True
            continue
        if raw_value.lower() == "false":
            result[key] = False
            continue

        # Float
        try:
            if "." in raw_value:
                result[key] = float(raw_value)
                continue
        except ValueError:
            pass

        # Int
        try:
            result[key] = int(raw_value)
            continue
        except ValueError:
            pass

        # String fallback
        result[key] = raw_value

    return result


# Default columns for table/csv when --select is not used
_DEFAULT_FIELDS = ["source", "target", "confidence", "rule"]


def _render_table(statements: list, fields: List[str], console_obj: Console) -> None:
    """Render matching statements as a Rich table."""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim")
    for f in fields:
        table.add_column(f.replace("_", " ").title())

    for i, stmt in enumerate(statements):
        from .query import _resolve_field
        row = [str(i)]
        for f in fields:
            val = _resolve_field(stmt, f)
            row.append(str(val) if val is not None else "")
        table.add_row(*row)

    console_obj.print(table)


def _render_json(statements: list, fields: Optional[List[str]]) -> str:
    """Render statements as JSON string."""
    from .query import _resolve_field

    if fields:
        rows = []
        for stmt in statements:
            rows.append({f: _resolve_field(stmt, f) for f in fields})
        return json.dumps(rows, indent=2, ensure_ascii=False, default=str)
    else:
        # Full statement dicts
        rows = []
        for stmt in statements:
            rows.append(json.loads(stmt.model_dump_json()))
        return json.dumps(rows, indent=2, ensure_ascii=False)


def _render_csv(statements: list, fields: List[str]) -> str:
    """Render statements as CSV string with header."""
    from .query import _resolve_field

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(fields)
    for stmt in statements:
        row = []
        for f in fields:
            val = _resolve_field(stmt, f)
            row.append(val if val is not None else "")
        writer.writerow(row)
    return buf.getvalue()


@app.command()
def query(
    file_path: Annotated[Path, typer.Argument(help="Path to the STL file to query.", exists=True, file_okay=True, dir_okay=False, readable=True)],
    where: Annotated[Optional[str], typer.Option("--where", "-w", help="Filter conditions (comma-separated field=value or field__op=value).")] = None,
    select_fields: Annotated[Optional[str], typer.Option("--select", "-s", help="Comma-separated field names to project.")] = None,
    pointer: Annotated[Optional[str], typer.Option("--pointer", "-p", help="STL pointer path (e.g. /0/source/name).")] = None,
    fmt: Annotated[str, typer.Option("--format", "-f", help="Output format: table, json, stl, csv.")] = "table",
    count: Annotated[bool, typer.Option("--count", "-c", help="Only print the count of matching statements.")] = False,
    limit: Annotated[Optional[int], typer.Option("--limit", "-l", help="Maximum number of results.")] = None,
):
    """
    Queries an STL file: filter, select, and format results.
    """
    try:
        parse_result = parse_file(file_path)

        if not parse_result.is_valid:
            console.print("[bold red]STL file has parse errors.[/bold red]")
            for error in parse_result.errors:
                console.print(f"  - [red][{error.code}][/red] {error.message} (line {error.line or '?'})")
            raise typer.Exit(code=1)

        # Pointer mode — standalone, ignores other options
        if pointer is not None:
            val = stl_pointer(parse_result, pointer)
            # For complex objects, use STL string representation
            if hasattr(val, '__str__') and hasattr(val, 'source'):
                print(str(val))
            elif hasattr(val, 'name'):
                print(str(val))
            else:
                print(val)
            return

        # Filter
        if where:
            kwargs = _parse_where_string(where)
            filtered = filter_statements(parse_result, **kwargs)
        else:
            filtered = parse_result

        stmts = list(filtered.statements)

        # Limit
        if limit is not None and limit > 0:
            stmts = stmts[:limit]

        # Count mode
        if count:
            print(len(stmts))
            return

        # Determine fields
        fields = [f.strip() for f in select_fields.split(",")] if select_fields else _DEFAULT_FIELDS

        # Render
        if fmt == "table":
            _render_table(stmts, fields, console)
            console.print(f"[dim]{len(stmts)} statement(s)[/dim]")
        elif fmt == "json":
            fields_for_json = [f.strip() for f in select_fields.split(",")] if select_fields else None
            print(_render_json(stmts, fields_for_json))
        elif fmt == "csv":
            print(_render_csv(stmts, fields), end="")
        elif fmt == "stl":
            from .models import ParseResult as _PR
            temp = _PR(statements=stmts, is_valid=filtered.is_valid)
            print(temp.to_stl())
        else:
            console.print(f"[bold red]Error:[/bold red] Unsupported format '{fmt}'. Supported: table, json, stl, csv.")
            raise typer.Exit(code=1)

    except typer.Exit:
        raise
    except Exception as e:
        handle_error(e)


@app.command(name="diff")
def diff_command(
    file_a: Annotated[Path, typer.Argument(help="Source STL file (before).", exists=True, file_okay=True, dir_okay=False, readable=True)],
    file_b: Annotated[Path, typer.Argument(help="Target STL file (after).", exists=True, file_okay=True, dir_okay=False, readable=True)],
    fmt: Annotated[str, typer.Option("--format", "-f", help="Output format: text (default), json.")] = "text",
    summary_only: Annotated[bool, typer.Option("--summary", "-s", help="Only print summary counts.")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Exit code only: 0 = identical, 1 = different.")] = False,
):
    """
    Computes semantic diff between two STL files.
    """
    try:
        result_a = parse_file(file_a)
        result_b = parse_file(file_b)

        for label, result in [("A", result_a), ("B", result_b)]:
            if not result.is_valid:
                console.print(f"[bold red]File {label} has parse errors.[/bold red]")
                for error in result.errors:
                    console.print(f"  - [red][{error.code}][/red] {error.message}")
                raise typer.Exit(code=1)

        diff = stl_diff(result_a, result_b)

        if quiet:
            raise typer.Exit(code=0 if diff.is_empty else 1)

        if summary_only:
            s = diff.summary
            console.print(f"{s.added} added, {s.removed} removed, {s.modified} modified, {s.unchanged} unchanged")
            return

        if fmt == "json":
            print(json.dumps(diff_to_dict(diff), indent=2, ensure_ascii=False, default=str))
        elif fmt == "text":
            print(diff_to_text(diff))
        else:
            console.print(f"[bold red]Error:[/bold red] Unsupported format '{fmt}'. Supported: text, json.")
            raise typer.Exit(code=1)

    except typer.Exit:
        raise
    except Exception as e:
        handle_error(e)


@app.command(name="patch")
def patch_command(
    file_path: Annotated[Path, typer.Argument(help="STL file to patch.", exists=True, file_okay=True, dir_okay=False, readable=True)],
    diff_file: Annotated[Path, typer.Argument(help="Diff JSON file (from 'stl diff --format json').", exists=True, file_okay=True, dir_okay=False, readable=True)],
    output_path: Annotated[Optional[Path], typer.Option("--output", "-o", help="Write patched output to file.")] = None,
):
    """
    Applies a diff (JSON) to an STL file, producing a patched document.
    """
    try:
        result = parse_file(file_path)

        if not result.is_valid:
            console.print("[bold red]STL file has parse errors.[/bold red]")
            for error in result.errors:
                console.print(f"  - [red][{error.code}][/red] {error.message}")
            raise typer.Exit(code=1)

        # Load the diff JSON and reconstruct STLDiff
        diff_json = json.loads(diff_file.read_text(encoding="utf-8"))

        # Re-parse: convert diff JSON back to STLDiff by diffing the original
        # against a reconstructed target. For now, we use the simpler approach:
        # parse both files from the diff's statement strings.
        from .diff import STLDiff, DiffEntry, DiffOp, DiffSummary, ModifierChange
        from .parser import parse as _parse

        entries = []
        for e in diff_json.get("entries", []):
            stmt_a = None
            stmt_b = None
            if "statement_a" in e:
                pr = _parse(e["statement_a"])
                if pr.statements:
                    stmt_a = pr.statements[0]
            if "statement_b" in e:
                pr = _parse(e["statement_b"])
                if pr.statements:
                    stmt_b = pr.statements[0]

            mod_changes = []
            for mc in e.get("modifier_changes", []):
                mod_changes.append(ModifierChange(
                    field=mc["field"],
                    old_value=mc.get("old_value"),
                    new_value=mc.get("new_value"),
                ))

            entries.append(DiffEntry(
                op=DiffOp(e["op"]),
                key=e["key"],
                statement_a=stmt_a,
                statement_b=stmt_b,
                index_a=e.get("index_a"),
                index_b=e.get("index_b"),
                modifier_changes=mod_changes,
            ))

        raw_summary = diff_json.get("summary", {})
        diff = STLDiff(
            entries=entries,
            summary=DiffSummary(**raw_summary),
        )

        patched = stl_patch(result, diff)
        stl_text = patched.to_stl()

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(stl_text + "\n")
            console.print(f"[bold green]Patched output saved to {output_path}[/bold green]")
        else:
            print(stl_text)

    except typer.Exit:
        raise
    except Exception as e:
        handle_error(e)


if __name__ == "__main__":
    app()