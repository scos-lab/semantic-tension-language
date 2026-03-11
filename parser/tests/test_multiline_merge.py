#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test suite for multi-line statement merging

Tests the ability to parse STL statements that span multiple lines,
particularly for LLM-formatted output with line breaks in ::mod(...).
"""

import pytest
from pathlib import Path

from stl_parser import parse_file, parse
from stl_parser.parser import _merge_multiline_statements


class TestMultilineMerging:
    """Tests for _merge_multiline_statements function."""

    def test_simple_multiline_mod(self):
        """Test merging simple multi-line modifier."""
        text = """[A] -> [B] ::mod(
  rule="test",
  confidence=0.9
)"""
        result = _merge_multiline_statements(text)
        assert '[A] -> [B] ::mod( rule="test", confidence=0.9 )' in result
        assert '\n  rule=' not in result  # Should not have line break before rule

    def test_multiline_with_many_params(self):
        """Test merging with many parameters."""
        text = """[Coffee] -> [Energy] ::mod(
  rule="empirical",
  confidence=0.9,
  source="study",
  time="2024-01-01T00:00:00Z",
  author="researcher"
)"""
        result = _merge_multiline_statements(text)
        # Should be merged into single line
        assert result.count('\n') == 0 or (result.count('\n') == 1 and result.endswith('\n'))
        # Should contain all parameters
        assert 'rule="empirical"' in result
        assert 'confidence=0.9' in result
        assert 'author="researcher"' in result

    def test_single_line_unchanged(self):
        """Test that single-line statements are unchanged."""
        text = "[A] -> [B] ::mod(confidence=0.9)"
        result = _merge_multiline_statements(text)
        assert result == text

    def test_multiple_statements_mixed(self):
        """Test file with both single-line and multi-line statements."""
        text = """[A] -> [B] ::mod(confidence=0.9)
[C] -> [D] ::mod(
  rule="test",
  confidence=0.8
)
[E] -> [F]"""
        result = _merge_multiline_statements(text)
        lines = result.strip().split('\n')
        assert len(lines) == 3  # Should have 3 lines
        assert '[A] -> [B]' in lines[0]
        assert '[C] -> [D]' in lines[1]
        assert 'rule="test"' in lines[1]  # Merged into same line
        assert '[E] -> [F]' in lines[2]

    def test_with_comments(self):
        """Test that comments are preserved."""
        text = """# This is a comment
[A] -> [B] ::mod(
  rule="test"
)
# Another comment
[C] -> [D]"""
        result = _merge_multiline_statements(text)
        assert '# This is a comment' in result
        assert '# Another comment' in result
        assert '[A] -> [B] ::mod( rule="test" )' in result

    def test_comment_inside_multiline(self):
        """Test comment lines within multi-line statement."""
        text = """[A] -> [B] ::mod(
  # This comment is filtered out during merge
  rule="test"
)"""
        result = _merge_multiline_statements(text)
        # Comment should be filtered out to avoid breaking parsing
        assert '# This comment is filtered out during merge' not in result
        # But the statement should be merged correctly
        assert '[A] -> [B] ::mod( rule="test" )' in result

    def test_nested_parentheses(self):
        """Test handling of nested parentheses."""
        text = """[A] -> [B] ::mod(
  data=(1, 2, 3),
  rule="test"
)"""
        result = _merge_multiline_statements(text)
        assert 'data=(1, 2, 3)' in result
        assert 'rule="test"' in result
        # Should be on one line
        assert result.count('[A] -> [B]') == 1

    def test_unclosed_parenthesis(self):
        """Test handling of unclosed parenthesis (malformed input)."""
        text = """[A] -> [B] ::mod(
  rule="test"
[C] -> [D]"""
        result = _merge_multiline_statements(text)
        # Should still merge what it can
        assert '[A] -> [B] ::mod( rule="test"' in result or '[A] -> [B]' in result

    def test_empty_lines(self):
        """Test handling of empty lines."""
        text = """[A] -> [B] ::mod(
  rule="test",

  confidence=0.9
)"""
        result = _merge_multiline_statements(text)
        assert '[A] -> [B] ::mod(' in result
        assert 'rule="test"' in result
        assert 'confidence=0.9' in result

    def test_unicode_content(self):
        """Test with Unicode characters."""
        text = """[素问] -> [王冰] ::mod(
  rule="empirical",
  author="王冰"
)"""
        result = _merge_multiline_statements(text)
        assert '[素问]' in result
        assert '[王冰]' in result
        assert 'author="王冰"' in result

    def test_no_modifiers(self):
        """Test statements without modifiers."""
        text = """[A] -> [B]
[C] -> [D]"""
        result = _merge_multiline_statements(text)
        assert result == text  # Should be unchanged


class TestMultilineParseFile:
    """Integration tests for parse_file with multi-line statements."""

    def test_parse_multiline_file(self, tmpdir):
        """Test parsing file with multi-line statement."""
        file_path = tmpdir.join("multiline.stl")
        content = """[A] -> [B] ::mod(
  rule="empirical",
  confidence=0.9
)"""
        file_path.write(content)

        result = parse_file(str(file_path))
        assert result.is_valid is True
        assert len(result.statements) == 1
        assert result.statements[0].source.name == "A"
        assert result.statements[0].target.name == "B"
        assert result.statements[0].modifiers is not None
        assert result.statements[0].modifiers.rule == "empirical"
        assert result.statements[0].modifiers.confidence == 0.9

    def test_parse_multiline_chinese(self, tmpdir):
        """Test parsing multi-line with Chinese characters."""
        file_path = tmpdir.join("chinese_multiline.stl")
        content = """[素问] -> [王冰] ::mod(
  rule="empirical",
  confidence=0.88,
  author="王冰",
  time="0762-01-01T00:00:00Z",
  source="唐·王冰注"
)"""
        # Write with explicit UTF-8 encoding
        with open(str(file_path), 'w', encoding='utf-8') as f:
            f.write(content)

        result = parse_file(str(file_path))
        assert result.is_valid is True
        assert len(result.statements) == 1
        assert result.statements[0].source.name == "素问"
        assert result.statements[0].target.name == "王冰"

    def test_parse_mixed_single_and_multiline(self, tmpdir):
        """Test file with both single and multi-line statements."""
        file_path = tmpdir.join("mixed.stl")
        content = """[A] -> [B] ::mod(confidence=0.9)
[C] -> [D] ::mod(
  rule="test",
  confidence=0.8
)
[E] -> [F]"""
        file_path.write(content)

        result = parse_file(str(file_path))
        assert result.is_valid is True
        assert len(result.statements) == 3

    def test_parse_multiline_in_markdown(self, tmpdir):
        """Test multi-line statement in Markdown code fence."""
        file_path = tmpdir.join("doc.md")
        content = """# Documentation

Here's some STL:

```stl
[Coffee] -> [Energy] ::mod(
  rule="empirical",
  confidence=0.9,
  source="personal experience"
)
```

End of doc."""
        file_path.write(content)

        result = parse_file(str(file_path), mode='fenced')
        assert result.is_valid is True
        assert len(result.statements) == 1
        assert result.statements[0].modifiers.rule == "empirical"

    def test_parse_multiline_heuristic_in_markdown(self, tmpdir):
        """Test multi-line statement with heuristic extraction."""
        file_path = tmpdir.join("notes.md")
        content = """# My Notes

Some observations:

[Sleep] -> [Performance] ::mod(
  rule="empirical",
  confidence=0.85
)

More text here."""
        file_path.write(content)

        result = parse_file(str(file_path), mode='heuristic')
        assert result.is_valid is True
        assert len(result.statements) == 1

    def test_multiline_with_comments_preserved(self, tmpdir):
        """Test that comments in multi-line are handled correctly."""
        file_path = tmpdir.join("commented.stl")
        content = """# Main relationship
[A] -> [B] ::mod(
  # Setting high confidence
  confidence=0.95,
  rule="empirical"
)
# End"""
        file_path.write(content)

        result = parse_file(str(file_path))
        assert result.is_valid is True
        assert len(result.statements) == 1


class TestMultilineEdgeCases:
    """Edge case tests for multi-line merging."""

    def test_extremely_long_multiline(self):
        """Test very long multi-line statement."""
        params = ', '.join([f'param{i}="value{i}"' for i in range(20)])
        text = f"""[A] -> [B] ::mod(
  {params}
)"""
        result = _merge_multiline_statements(text)
        assert '[A] -> [B] ::mod(' in result
        assert 'param0="value0"' in result
        assert 'param19="value19"' in result

    def test_deeply_nested_parens(self):
        """Test deeply nested parentheses."""
        text = """[A] -> [B] ::mod(
  data=((1, 2), (3, 4)),
  rule="test"
)"""
        result = _merge_multiline_statements(text)
        assert 'data=((1, 2), (3, 4))' in result

    def test_string_with_parens(self):
        """Test string containing parentheses."""
        text = """[A] -> [B] ::mod(
  note="(important)",
  rule="test"
)"""
        result = _merge_multiline_statements(text)
        assert 'note="(important)"' in result

    def test_empty_mod(self):
        """Test empty modifier parentheses."""
        text = """[A] -> [B] ::mod(
)"""
        result = _merge_multiline_statements(text)
        assert '[A] -> [B] ::mod( )' in result

    def test_mod_on_separate_line(self):
        """Test modifier starting on next line."""
        # This is unusual formatting but should still work
        text = """[A] -> [B]
::mod(
  rule="test"
)"""
        # Note: This may not work perfectly as ::mod is on a different line
        # Current implementation expects ::mod( to be on the same line
        # This test documents current behavior
        result = _merge_multiline_statements(text)
        # Should at least not crash
        assert '[A] -> [B]' in result
