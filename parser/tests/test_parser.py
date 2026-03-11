# -*- coding: utf-8 -*-
"""
Test suite for parser.py and grammar.py

Tests the core parsing functionality of the STL parser.
"""

import pytest
from lark.exceptions import LarkError, UnexpectedInput

from stl_parser.parser import parse, parse_file, _remove_markdown_escapes # Added import
from stl_parser.grammar import parse_stl_text
from stl_parser.models import ParseResult, Statement, Anchor, Modifier, ParseError
from stl_parser.errors import ErrorCode


class TestGrammarParser:
    """Tests directly against the Lark grammar and parse_stl_text function."""

    def test_parse_simple_statement(self):
        text = "[A] -> [B]"
        tree = parse_stl_text(text)
        # For a single statement, Lark might return 'statement' directly as the root
        # or 'start' wrapping a single 'statement'. We handle both.
        if tree.data == "start":
            assert len(tree.children) == 1
            statement_node = tree.children[0]
        else: # Likely tree.data is "statement"
            statement_node = tree

        assert statement_node.data == "statement"
        assert statement_node.children[0].data == "path_expression"

    def test_parse_chained_statement(self):
        text = "[A] -> [B] -> [C]"
        tree = parse_stl_text(text)
        if tree.data == "start":
            assert len(tree.children) == 1
            statement_node = tree.children[0]
        else:
            statement_node = tree

        assert statement_node.data == "statement"
        assert statement_node.children[0].data == "path_expression"
        assert len(statement_node.children[0].children) == 5 # anchor, arrow, anchor, arrow, anchor

    def test_parse_statement_with_modifier(self):
        text = '[A] -> [B] ::mod(confidence=0.9)'
        tree = parse_stl_text(text)
        if tree.data == "start":
            assert len(tree.children) == 1
            statement_node = tree.children[0]
        else:
            statement_node = tree

        assert statement_node.data == "statement"
        assert statement_node.children[0].data == "path_expression"
        assert statement_node.children[0].children[3].data == "modifier" # Check modifier exists

    def test_parse_unicode_characters(self):
        text = "[黄帝内经] -> [素问]"
        tree = parse_stl_text(text)
        if tree.data == "start":
            assert len(tree.children) == 1
            statement_node = tree.children[0]
        else:
            statement_node = tree

        assert statement_node.data == "statement"
        # Accessing the Token('IDENTIFIER', '黄帝内经')
        assert statement_node.children[0].children[0].children[0].children[0].children[0].value == "黄帝内经"
        # Correct path for the target anchor (children[2] is the target anchor)
        assert statement_node.children[0].children[2].children[0].children[0].children[0].value == "素问"

    def test_parse_namespaced_identifier(self):
        text = "[Physics:Energy] -> [Quantum:Mass]"
        tree = parse_stl_text(text)
        if tree.data == "start":
            assert len(tree.children) == 1
            statement_node = tree.children[0]
        else:
            statement_node = tree

        assert statement_node.data == "statement"
        assert statement_node.children[0].children[0].children[0].children[0].data == "namespaced_identifier"
        assert statement_node.children[0].children[0].children[0].children[0].children[0].data == "namespace" # Namespace node
        assert statement_node.children[0].children[0].children[0].children[0].children[1].value == "Energy" # Identifier token

    def test_parse_comment_line(self):
        text = "# This is a comment"
        tree = parse_stl_text(text)
        # For a single comment, Lark might return 'comment' directly, or 'start' wrapping 'comment'
        if tree.data == "start":
            assert len(tree.children) == 1
            statement_node = tree.children[0] # This will be the statement node
        else:
            statement_node = tree # Assume tree.data is "statement"

        assert statement_node.data == "statement"
        assert statement_node.children[0].data == "comment"

    def test_parse_empty_string_returns_empty_start_tree(self):
        # Grammar `?start: statement*` allows empty input, resulting in a 'start' tree with no children
        tree = parse_stl_text("")
        assert tree.data == "start"
        assert len(tree.children) == 0

    def test_parse_invalid_syntax_raises_error(self):
        with pytest.raises(LarkError):
            parse_stl_text("[A - > B]") # Malformed arrow
        with pytest.raises(LarkError):
            parse_stl_text("A -> B") # Missing brackets


class TestCoreParser:
    """Tests the high-level parse function in parser.py."""

    def test_parse_valid_stl(self):
        text = "[A] -> [B] ::mod(confidence=0.8)"
        result = parse(text)
        assert isinstance(result, ParseResult)
        assert result.is_valid is True
        assert len(result.statements) == 1
        assert result.statements[0].source.name == "A"
        assert result.statements[0].target.name == "B"
        assert result.statements[0].modifiers.confidence == 0.8

    def test_parse_invalid_stl(self):
        text = "[A -> B]" # Missing brackets for target
        result = parse(text)
        assert isinstance(result, ParseResult)
        assert result.is_valid is False
        assert len(result.statements) == 0
        assert len(result.errors) == 1
        assert result.errors[0].code == "E001" # Unexpected input

    def test_parse_empty_string(self):
        # This behavior is now handled by the parse function directly
        result = parse("")
        assert isinstance(result, ParseResult)
        assert result.is_valid is True
        assert len(result.statements) == 0
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_parse_whitespace_only(self):
        result = parse("   \n\t  ")
        assert isinstance(result, ParseResult)
        assert result.is_valid is True
        assert len(result.statements) == 0
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_parse_comments_only(self):
        result = parse("# comment 1\n# comment 2")
        assert isinstance(result, ParseResult)
        assert result.is_valid is True
        assert len(result.statements) == 0
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    @pytest.mark.skip(reason="`parse` function does not run validation; warnings are generated by `validate_parse_result`.")
    def test_parse_with_warnings(self):
        # Example that should trigger a warning (e.g., low confidence, short anchor name)
        text = '[A] -> [B] ::mod(confidence=0.4)' # Low confidence warning
        result = parse(text)
        assert isinstance(result, ParseResult)
        assert result.is_valid is True # Still valid, just has warning
        assert len(result.statements) == 1
        assert len(result.warnings) > 0 # Expect at least one warning
        assert result.warnings[0].code == "W003_LOW_CONFIDENCE"

    def test_parse_multiline_statement(self):
        text = """
        [A] -> [B] ::mod(
          confidence=0.9,
          rule="causal"
        )
        """
        result = parse(text)
        assert result.is_valid
        assert len(result.statements) == 1
        assert result.statements[0].source.name == "A"
        assert result.statements[0].modifiers.confidence == 0.9

    def test_parse_file_valid_stl(self, tmp_path):
        file_content = "[X] -> [Y]"
        test_file = tmp_path / "test.stl"
        test_file.write_text(file_content)
        
        result = parse_file(str(test_file))
        assert result.is_valid
        assert len(result.statements) == 1
        assert result.statements[0].source.name == "X"

    def test_parse_file_invalid_stl(self, tmp_path):
        file_content = "[X -> Y]" # Invalid syntax
        test_file = tmp_path / "test.stl"
        test_file.write_text(file_content)
        
        result = parse_file(str(test_file))
        assert not result.is_valid
        assert len(result.errors) > 0

    def test_parse_file_not_found(self):
        result = parse_file("non_existent_file.stl")
        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.errors[0].code == ErrorCode.E400_FILE_NOT_FOUND # File not found error


class TestMarkdownEscapeHandling:
    
    def test_escape_removal_basic(self):
        """Test that backslashes are removed before special characters."""
        # Using standard strings to be explicit
        # \\x5BA\\x5D becomes [A] in memory
        text = r"\[A\] \-\> \[B\]"
        expected = "[A] -> [B]"
        assert _remove_markdown_escapes(text) == expected

    def test_escape_inside_string_protected(self):
        """Test that escapes INSIDE quoted strings are NOT removed."""
        # text represents: value="[\\]"
        # This contains a backslash followed by a bracket inside a string.
        # Markdown escape removal should NOT touch this.
        text = r'value="[\\]"'
        assert _remove_markdown_escapes(text) == text

    def test_mixed_content(self):
        """Test escaping outside strings but preserving inside."""
        # Input: \[A\] -> [B] ::mod(val="\[")
        text = r'\[A\] -> [B] ::mod(val="\[")'
        expected = r'[A] -> [B] ::mod(val="\[")'
        assert _remove_markdown_escapes(text) == expected
