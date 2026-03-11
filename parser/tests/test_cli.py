#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test suite for cli.py

Tests the command-line interface using Typer's CliRunner.
"""

import pytest
from typer.testing import CliRunner
import json
import os

from stl_parser.cli import app

runner = CliRunner()

@pytest.fixture(scope="module")
def valid_stl_file(tmpdir_factory):
    """Creates a temporary valid STL file for testing."""
    fn = tmpdir_factory.mktemp("data").join("valid.stl")
    content = "[A] -> [B] ::mod(confidence=0.9)\n[B] -> [C] -> [D]"
    fn.write(content)
    return str(fn)

@pytest.fixture(scope="module")
def invalid_stl_file(tmpdir_factory):
    """Creates a temporary invalid STL file for testing."""
    fn = tmpdir_factory.mktemp("data").join("invalid.stl")
    fn.write("[A] -> [B] ::mod(confidence=2.0)") # Invalid confidence
    return str(fn)
    
@pytest.fixture(scope="module")
def cyclic_stl_file(tmpdir_factory):
    """Creates a temporary STL file with a cycle for testing analysis."""
    fn = tmpdir_factory.mktemp("data").join("cyclic.stl")
    content = "[A] -> [B]\n[B] -> [C]\n[C] -> [A]"
    fn.write(content)
    return str(fn)


@pytest.fixture(scope="module")
def empty_stl_file(tmpdir_factory):
    """Creates a temporary empty STL file for testing."""
    fn = tmpdir_factory.mktemp("data").join("empty.stl")
    fn.write("")
    return str(fn)


class TestCli:
    """Tests the CLI commands."""

    def test_validate_valid_file(self, valid_stl_file):
        """Test the 'validate' command with a valid file."""
        result = runner.invoke(app, ["validate", valid_stl_file])
        assert result.exit_code == 0
        assert "Found" in result.stdout
        assert "warning(s)" in result.stdout

    def test_validate_empty_file(self, empty_stl_file):
        """Test the 'validate' command with an empty file."""
        result = runner.invoke(app, ["validate", empty_stl_file])
        assert result.exit_code == 0
        assert "SUCCESS: STL file is valid." in result.stdout
        assert "Statements found: 0" in result.stdout

    def test_validate_invalid_file(self, invalid_stl_file):
        """Test the 'validate' command with an invalid file."""
        # The parser will catch the pydantic error first
        result = runner.invoke(app, ["validate", invalid_stl_file])
        assert result.exit_code == 1
        assert "Error" in result.stdout
        assert "less than or equal to 1" in result.stdout

    def test_validate_file_not_found(self):
        """Test the 'validate' command with a non-existent file."""
        result = runner.invoke(app, ["validate", "nonexistent.stl"])
        assert result.exit_code != 0
        assert "does not exist" in result.stderr

    def test_convert_to_json(self, valid_stl_file):
        """Test the 'convert' command to JSON format."""
        result = runner.invoke(app, ["convert", valid_stl_file, "--to", "json"])
        assert result.exit_code == 0
        
        # Verify the output is valid JSON
        try:
            data = json.loads(result.stdout)
            assert "statements" in data
            assert len(data["statements"]) == 3
            assert data["statements"][0]["source"]["name"] == "A"
        except json.JSONDecodeError:
            pytest.fail("CLI 'convert' command did not produce valid JSON.")

    def test_parse_command(self, valid_stl_file):
        """Test the 'parse' command, which is an alias for 'convert --to json'."""
        result = runner.invoke(app, ["parse", valid_stl_file])
        assert result.exit_code == 0
        
        try:
            data = json.loads(result.stdout)
            assert len(data["statements"]) == 3
        except json.JSONDecodeError:
            pytest.fail("CLI 'parse' command did not produce valid JSON.")

    def test_convert_unsupported_format(self, valid_stl_file):
        """Test the 'convert' command with an unsupported format."""
        result = runner.invoke(app, ["convert", valid_stl_file, "--to", "yaml"])
        assert result.exit_code == 1
        assert "Unsupported format 'yaml'" in result.stdout

    def test_analyze_valid_file(self, valid_stl_file):
        """Test the 'analyze' command with a valid file."""
        result = runner.invoke(app, ["analyze", valid_stl_file])
        assert result.exit_code == 0
        assert "Graph Analysis" in result.stdout
        assert "Total Statements" in result.stdout
        assert "Total Nodes (Anchors)" in result.stdout
        assert "Total Edges (Relationships)" in result.stdout
        assert "Top 5 Most Central Nodes" in result.stdout
        assert "Cycles Found" in result.stdout

    def test_analyze_cyclic_file(self, cyclic_stl_file):
        """Test the 'analyze' command with a file containing cycles."""
        result = runner.invoke(app, ["analyze", cyclic_stl_file])
        assert result.exit_code == 0
        assert "Cycles Found" in result.stdout
        assert "1" in result.stdout # Should find 1 cycle
        assert "Cycles:" in result.stdout
        assert "-> [A]" in result.stdout
        assert "-> [B]" in result.stdout
        assert "-> [C]" in result.stdout

    def test_analyze_invalid_file(self, invalid_stl_file):
        """Test the 'analyze' command with an invalid file, expecting it to fail gracefully."""
        result = runner.invoke(app, ["analyze", invalid_stl_file])
        assert result.exit_code == 1
        assert "STL file is invalid. Cannot analyze." in result.stdout
        assert "Error" in result.stdout
        
    def test_main_help_message(self):
        """Test that the main help message can be displayed."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Usage: stl" in result.stdout
        assert "A command-line tool for the Semantic Tension Language (STL) parser." in result.stdout
        assert "validate" in result.stdout
        assert "convert" in result.stdout
        assert "analyze" in result.stdout

    # ---- build command ----

    def test_build_basic(self):
        """Test the 'build' command with simple source and target."""
        result = runner.invoke(app, ["build", "A", "B"])
        assert result.exit_code == 0
        assert "Built" in result.stdout
        assert "[A]" in result.stdout
        assert "[B]" in result.stdout
        assert "->" in result.stdout

    def test_build_with_modifiers(self):
        """Test 'build' with --mod option."""
        result = runner.invoke(app, ["build", "Theory", "Prediction", "--mod", "confidence=0.9,rule=causal"])
        assert result.exit_code == 0
        assert "Built" in result.stdout
        assert "[Theory]" in result.stdout
        assert "[Prediction]" in result.stdout
        assert "confidence=0.9" in result.stdout
        assert "causal" in result.stdout

    def test_build_to_file(self, tmpdir_factory):
        """Test 'build' with --output writes to file."""
        outdir = tmpdir_factory.mktemp("build_out")
        outfile = str(outdir.join("built.stl"))
        result = runner.invoke(app, ["build", "X", "Y", "--output", outfile])
        assert result.exit_code == 0
        assert "saved to" in result.stdout
        with open(outfile, "r", encoding="utf-8") as f:
            content = f.read()
        assert "[X]" in content
        assert "[Y]" in content

    # ---- clean command ----

    def test_clean_basic(self, tmpdir_factory):
        """Test the 'clean' command with a file containing STL text."""
        fn = tmpdir_factory.mktemp("clean").join("noisy.txt")
        fn.write("Here is some STL:\n[A] -> [B] ::mod(confidence=0.9)\nEnd of output.")
        result = runner.invoke(app, ["clean", str(fn)])
        assert result.exit_code == 0
        assert "Statements found:" in result.stdout

    def test_clean_show_repairs(self, tmpdir_factory):
        """Test 'clean' with --show-repairs flag."""
        fn = tmpdir_factory.mktemp("clean2").join("noisy.txt")
        fn.write("[A] -> [B] ::mod(confidence=0.9)")
        result = runner.invoke(app, ["clean", str(fn), "--show-repairs"])
        assert result.exit_code == 0
        assert "Statements found:" in result.stdout

    def test_clean_to_file(self, tmpdir_factory):
        """Test 'clean' with --output writes cleaned text to file."""
        fn = tmpdir_factory.mktemp("clean3").join("noisy.txt")
        fn.write("[A] -> [B] ::mod(confidence=0.9)")
        outfile = str(tmpdir_factory.mktemp("clean3_out").join("cleaned.stl"))
        result = runner.invoke(app, ["clean", str(fn), "--output", outfile])
        assert result.exit_code == 0
        assert os.path.exists(outfile)

    # ---- schema-validate command ----

    def test_schema_validate_valid(self, tmpdir_factory):
        """Test 'schema-validate' with a valid STL file and matching schema."""
        stl_dir = tmpdir_factory.mktemp("schema_test")
        stl_file = stl_dir.join("test.stl")
        stl_file.write("[Theory] -> [Prediction] ::mod(confidence=0.9)")

        schema_file = stl_dir.join("test.stl.schema")
        schema_file.write(
            'schema TestSchema v1.0 {\n'
            '  modifier {\n'
            '    required: [confidence]\n'
            '  }\n'
            '}\n'
        )

        result = runner.invoke(app, ["schema-validate", str(stl_file), "--schema", str(schema_file)])
        assert result.exit_code == 0
        assert "VALID" in result.stdout

    def test_schema_validate_parse_error(self, invalid_stl_file, tmpdir_factory):
        """Test 'schema-validate' with an invalid STL file → exit 1."""
        schema_dir = tmpdir_factory.mktemp("schema_test2")
        schema_file = schema_dir.join("test.stl.schema")
        schema_file.write(
            'schema TestSchema v1.0 {\n'
            '  modifier {\n'
            '    required: [confidence]\n'
            '  }\n'
            '}\n'
        )
        result = runner.invoke(app, ["schema-validate", str(invalid_stl_file), "--schema", str(schema_file)])
        assert result.exit_code == 1

    def test_help_shows_new_commands(self):
        """Test that --help lists the new build, clean, and schema-validate commands."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "build" in result.stdout
        assert "clean" in result.stdout
        assert "schema-validate" in result.stdout
