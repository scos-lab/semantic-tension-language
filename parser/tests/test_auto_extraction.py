#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test suite for STL auto-extraction functionality

Tests the automatic detection and extraction of STL content from mixed text,
code fences, and pure STL files.
"""

import pytest
from pathlib import Path

from stl_parser.parser import (
    parse_file,
    parse,
    _is_stl_line,
    _extract_stl_fences,
    _extract_stl_heuristic,
    _auto_extract_stl,
    _is_pure_stl,
    _merge_multiline_statements, # Added import
)


class TestSTLLineDetection:
    """Tests for _is_stl_line function."""

    def test_complete_stl_with_modifier(self):
        """Test detection of complete STL line with modifier."""
        line = "[Coffee] -> [Energy] ::mod(confidence=0.9)"
        result = _is_stl_line(line)
        assert result['is_stl'] is True
        assert result['confidence'] == 0.99
        assert result['type'] == 'complete_stl'
        assert result['features']['has_brackets'] is True
        assert result['features']['has_arrow'] is True
        assert result['features']['has_modifier'] is True

    def test_minimal_stl_without_modifier(self):
        """Test detection of minimal STL line without modifier."""
        line = "[Apple] -> [Fruit]"
        result = _is_stl_line(line)
        assert result['is_stl'] is True
        assert result['confidence'] == 0.95
        assert result['type'] == 'minimal_stl'
        assert result['features']['has_brackets'] is True
        assert result['features']['has_arrow'] is True
        assert result['features']['has_modifier'] is False

    def test_chained_stl_statement(self):
        """Test detection of chained STL statement."""
        line = "[A] -> [B] -> [C] -> [D]"
        result = _is_stl_line(line)
        assert result['is_stl'] is True
        assert result['confidence'] == 0.95
        assert result['features']['bracket_count'] == 4

    def test_stl_with_unicode_arrow(self):
        """Test detection with Unicode arrow."""
        line = "[A] → [B]"
        result = _is_stl_line(line)
        assert result['is_stl'] is True
        assert result['confidence'] == 0.95

    def test_comment_line(self):
        """Test that comment lines are not detected as STL."""
        line = "# This is a comment with [brackets] and -> arrow"
        result = _is_stl_line(line)
        assert result['is_stl'] is False
        assert result['confidence'] == 0.0
        assert result['type'] == 'comment'

    def test_markdown_link(self):
        """Test that Markdown links are not detected as STL."""
        line = "[Click here](https://example.com)"
        result = _is_stl_line(line)
        assert result['is_stl'] is False
        assert result['type'] == 'markdown_link'

    def test_markdown_list_with_arrow(self):
        """Test that Markdown lists are not detected as STL."""
        line = "- Item with -> arrow but no brackets"
        result = _is_stl_line(line)
        assert result['is_stl'] is False
        assert result['type'] == 'markdown_list'

    def test_markdown_quote(self):
        """Test that Markdown quotes are not detected as STL."""
        line = "> Quote with [brackets] and -> arrow"
        result = _is_stl_line(line)
        assert result['is_stl'] is False
        assert result['type'] == 'markdown_quote'

    def test_incomplete_stl_single_bracket(self):
        """Test detection of incomplete STL with only one bracket pair."""
        line = "[A] -> something"
        result = _is_stl_line(line)
        assert result['is_stl'] is False
        assert result['confidence'] == 0.2
        assert result['type'] == 'possible_syntax_error'

    def test_natural_language(self):
        """Test that natural language is not detected as STL."""
        line = "This is a regular sentence with no STL markers."
        result = _is_stl_line(line)
        assert result['is_stl'] is False
        assert result['confidence'] == 0.0
        assert result['type'] == 'natural_language'

    def test_empty_line(self):
        """Test that empty lines are not detected as STL."""
        line = "   "
        result = _is_stl_line(line)
        assert result['is_stl'] is False
        assert result['type'] == 'empty'

    def test_bracket_but_no_arrow(self):
        """Test line with brackets but no arrow."""
        line = "[Apple] is a fruit"
        result = _is_stl_line(line)
        assert result['is_stl'] is False
        assert result['confidence'] == 0.0


class TestCodeFenceExtraction:
    """Tests for _extract_stl_fences function."""

    def test_single_fence_extraction(self):
        """Test extraction from single code fence."""
        text = """# Document
Some text here

```stl
[A] -> [B]
[C] -> [D]
```

More text"""
        stl_text, metadata = _extract_stl_fences(text)
        assert "[A] -> [B]" in stl_text
        assert "[C] -> [D]" in stl_text
        assert metadata['format'] == 'fenced'
        assert metadata['fence_count'] == 1
        assert metadata['stl_lines'] == 2
        assert len(metadata['line_mapping']) == 2
        assert metadata['line_mapping'][0] == 5
        assert metadata['line_mapping'][1] == 6

    def test_multiple_fences_extraction(self):
        """Test extraction from multiple code fences."""
        text = """# Part 1
```stl
[A] -> [B]
```

# Part 2
```stl
[C] -> [D]
```"""
        stl_text, metadata = _extract_stl_fences(text)
        assert "[A] -> [B]" in stl_text
        assert "[C] -> [D]" in stl_text
        assert metadata['fence_count'] == 2
        assert metadata['stl_lines'] == 2

    def test_no_fences(self):
        """Test extraction when no fences present."""
        text = "Just plain text with no fences"
        stl_text, metadata = _extract_stl_fences(text)
        assert stl_text == ""
        assert metadata['fence_count'] == 0
        assert metadata['stl_lines'] == 0

    def test_empty_fence(self):
        """Test extraction from empty code fence."""
        text = """```stl
```"""
        stl_text, metadata = _extract_stl_fences(text)
        assert stl_text == ""
        assert metadata['fence_count'] == 1
        assert metadata['stl_lines'] == 0

    def test_fence_with_language_option(self):
        """Test extraction from fence with language options."""
        text = """```stl linenos
[A] -> [B]
```"""
        stl_text, metadata = _extract_stl_fences(text)
        assert "[A] -> [B]" in stl_text
        assert metadata['fence_count'] == 1


class TestHeuristicExtraction:
    """Tests for _extract_stl_heuristic function."""

    def test_mixed_content_extraction(self):
        """Test extraction from mixed natural language and STL."""
        text = """This is a document about relationships.

[Coffee] -> [Energy] ::mod(confidence=0.9)

Some more text here.

[Study] -> [Knowledge]

And a conclusion."""
        stl_text, metadata = _extract_stl_heuristic(text)
        assert "[Coffee] -> [Energy]" in stl_text
        assert "[Study] -> [Knowledge]" in stl_text
        assert "This is a document" not in stl_text
        assert metadata['format'] == 'heuristic'
        assert metadata['stl_lines'] == 2
        assert metadata['detection_stats']['complete_stl'] == 1
        assert metadata['detection_stats']['minimal_stl'] == 1

    def test_extraction_skips_comments(self):
        """Test that comments are preserved but not counted as STL."""
        text = """# This is a comment
[A] -> [B]
# Another comment
[C] -> [D]"""
        stl_text, metadata = _extract_stl_heuristic(text)
        assert "# This is a comment" in stl_text
        assert "[A] -> [B]" in stl_text
        assert metadata['stl_lines'] == 2  # Only actual STL lines

    def test_extraction_skips_markdown(self):
        """Test that Markdown syntax is filtered out."""
        text = """# Heading
[Link](http://example.com)
[A] -> [B]
- List item with -> arrow
[C] -> [D]
> Quote with [brackets]"""
        stl_text, metadata = _extract_stl_heuristic(text)
        assert "[A] -> [B]" in stl_text
        assert "[C] -> [D]" in stl_text
        assert "[Link](http://example.com)" not in stl_text
        assert "List item" not in stl_text
        assert metadata['stl_lines'] == 2

    def test_no_stl_content(self):
        """Test extraction when no STL content present."""
        text = """Just regular text.
No STL here.
Only natural language."""
        stl_text, metadata = _extract_stl_heuristic(text)
        assert stl_text.strip() == ""
        assert metadata['stl_lines'] == 0

    def test_line_number_mapping(self):
        """Test that line numbers are correctly mapped."""
        text = """Line 1: regular text
Line 2: [A] -> [B]
Line 3: more text
Line 4: [C] -> [D]"""
        stl_text, metadata = _extract_stl_heuristic(text)
        assert len(metadata['line_mapping']) == 2
        assert metadata['line_mapping'][0] == 2
        assert metadata['line_mapping'][1] == 4


class TestAutoExtraction:
    """Tests for _auto_extract_stl coordinator function."""

    def test_auto_mode_detects_fences(self):
        """Test that auto mode detects and uses fence extraction."""
        text = """```stl
[A] -> [B]
```"""
        stl_text, metadata = _auto_extract_stl(text, mode='auto')
        assert metadata['format'] == 'fenced'
        assert "[A] -> [B]" in stl_text

    def test_auto_mode_detects_pure_stl(self):
        """Test that auto mode detects pure STL files."""
        text = """[A] -> [B]
[C] -> [D]"""
        stl_text, metadata = _auto_extract_stl(text, mode='auto')
        assert metadata['format'] == 'pure_stl'
        assert stl_text == text

    def test_auto_mode_falls_back_to_heuristic(self):
        """Test that auto mode falls back to heuristic for mixed content."""
        text = """Some text
[A] -> [B]
More text"""
        stl_text, metadata = _auto_extract_stl(text, mode='auto')
        assert metadata['format'] == 'heuristic'
        assert "[A] -> [B]" in stl_text

    def test_fenced_mode(self):
        """Test explicit fenced mode."""
        text = """```stl
[A] -> [B]
```"""
        stl_text, metadata = _auto_extract_stl(text, mode='fenced')
        assert metadata['format'] == 'fenced'

    def test_heuristic_mode(self):
        """Test explicit heuristic mode."""
        text = "[A] -> [B]\nSome text"
        stl_text, metadata = _auto_extract_stl(text, mode='heuristic')
        assert metadata['format'] == 'heuristic'

    def test_strict_mode(self):
        """Test explicit strict mode (no extraction)."""
        text = "Some text\n[A] -> [B]"
        stl_text, metadata = _auto_extract_stl(text, mode='strict')
        assert metadata['format'] == 'strict'
        assert stl_text == text  # No extraction


class TestPureSTLDetection:
    """Tests for _is_pure_stl function."""

    def test_pure_stl_file(self):
        """Test detection of pure STL content."""
        text = """[A] -> [B]
[C] -> [D] ::mod(confidence=0.9)
# Comment
[E] -> [F]"""
        assert _is_pure_stl(text) is True

    def test_mixed_content_file(self):
        """Test detection of mixed content."""
        text = """Some regular text
[A] -> [B]
More text"""
        assert _is_pure_stl(text) is False

    def test_pure_stl_with_empty_lines(self):
        """Test pure STL with empty lines."""
        text = """[A] -> [B]

[C] -> [D]

# Comment
"""
        assert _is_pure_stl(text) is True

    def test_markdown_headers_make_not_pure(self):
        """Test that Markdown headers indicate not pure STL."""
        text = """# Heading
[A] -> [B]"""
        assert _is_pure_stl(text) is False


@pytest.fixture
def tmpdir_factory_fixture(tmpdir):
    """Provides temp directory for test files."""
    return tmpdir


class TestParseFileIntegration:
    """Integration tests for parse_file with auto-extraction."""

    def test_parse_pure_stl_file(self, tmpdir):
        """Test parsing pure STL file."""
        file_path = tmpdir.join("pure.stl")
        file_path.write("[A] -> [B]\n[C] -> [D]")

        result = parse_file(str(file_path), auto_extract=True)
        assert result.is_valid is True
        assert len(result.statements) == 2
        assert result.extraction_metadata is not None
        assert result.extraction_metadata['format'] == 'pure_stl'

    def test_parse_fenced_markdown_file(self, tmpdir):
        """Test parsing Markdown file with STL code fences."""
        file_path = tmpdir.join("document.md")
        content = """# My Document

Here's some STL:

```stl
[Coffee] -> [Energy] ::mod(confidence=0.9)
[Study] -> [Knowledge]
```

More text here."""
        file_path.write(content)

        result = parse_file(str(file_path), mode='auto', auto_extract=True)
        assert result.is_valid is True
        assert len(result.statements) == 2
        assert result.extraction_metadata['format'] == 'fenced'
        assert result.extraction_metadata['fence_count'] == 1

    def test_parse_mixed_content_heuristic(self, tmpdir):
        """Test parsing mixed content with heuristic extraction."""
        file_path = tmpdir.join("mixed.txt")
        content = """This is about relationships.

[Apple] -> [Fruit]

Apples are healthy.

[Coffee] -> [Energy]"""
        file_path.write(content)

        result = parse_file(str(file_path), mode='heuristic', auto_extract=True)
        assert result.is_valid is True
        assert len(result.statements) == 2
        assert result.extraction_metadata['format'] == 'heuristic'

    def test_parse_with_auto_extract_disabled(self, tmpdir):
        """Test parsing with auto_extract disabled."""
        file_path = tmpdir.join("mixed.txt")
        content = """Some text
[A] -> [B]"""
        file_path.write(content)

        result = parse_file(str(file_path), auto_extract=False)
        # Should fail to parse because of mixed content
        assert result.is_valid is False

    def test_line_number_remapping(self, tmpdir):
        """Test that error line numbers are correctly remapped."""
        file_path = tmpdir.join("mixed.md")
        content = """# Heading
Some text

[A] -> [B]
[C] -> [Invalid Syntax Here
More text"""
        file_path.write(content)

        result = parse_file(str(file_path), mode='heuristic', auto_extract=True)
        assert result.is_valid is False
        # Check that error line number points to original file
        if result.errors:
            # Error should reference line 5 or 6 (original file), not line 1 or 2 (extracted)
            assert any(error.line >= 4 for error in result.errors)

    def test_parse_empty_file(self, tmpdir):
        """Test parsing empty file."""
        file_path = tmpdir.join("empty.stl")
        file_path.write("")

        result = parse_file(str(file_path), auto_extract=True)
        # Empty file should be valid but have no statements
        assert len(result.statements) == 0

    def test_parse_only_natural_language(self, tmpdir):
        """Test parsing file with only natural language."""
        file_path = tmpdir.join("natural.txt")
        content = """This is just regular text.
No STL content here.
Only natural language."""
        file_path.write(content)

        result = parse_file(str(file_path), mode='heuristic', auto_extract=True)
        # Should be valid but empty
        assert len(result.statements) == 0
        assert result.extraction_metadata['stl_lines'] == 0


class TestConfidenceScoring:
    """Tests for confidence scoring in detection."""

    def test_complete_stl_highest_confidence(self):
        """Complete STL should have highest confidence."""
        complete = _is_stl_line("[A] -> [B] ::mod(confidence=0.9)")
        minimal = _is_stl_line("[A] -> [B]")
        assert complete['confidence'] > minimal['confidence']

    def test_syntax_error_low_confidence(self):
        """Syntax errors should have low confidence."""
        result = _is_stl_line("[A] -> incomplete")
        assert result['confidence'] < 0.5
        assert result['is_stl'] is False

    def test_natural_language_zero_confidence(self):
        """Natural language should have zero confidence."""
        result = _is_stl_line("Just regular text")
        assert result['confidence'] == 0.0


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_stl_with_special_characters(self):
        """Test STL with special characters in anchor names."""
        line = "[Node-1] -> [Node_2] ::mod(type='test')"
        result = _is_stl_line(line)
        assert result['is_stl'] is True

    def test_very_long_chain(self):
        """Test detection of very long STL chain."""
        line = "[A] -> [B] -> [C] -> [D] -> [E] -> [F]"
        result = _is_stl_line(line)
        assert result['is_stl'] is True
        assert result['features']['bracket_count'] == 6

    def test_nested_brackets_in_modifier(self):
        """Test STL with nested brackets in modifier."""
        line = "[A] -> [B] ::mod(data=[1,2,3])"
        result = _is_stl_line(line)
        assert result['is_stl'] is True

    def test_unicode_in_anchors(self):
        """Test STL with Unicode characters in anchors."""
        line = "[咖啡] -> [能量]"
        result = _is_stl_line(line)
        assert result['is_stl'] is True

class TestRegressionCases:
    """Tests for specific regression scenarios."""

    def test_markdown_code_block_inside_string(self):
        """
        Test that "```stl" inside a string value doesn't trigger fenced mode.
        Regression test for bug found in stl_test_1.md where a log file describing
        STL syntax contained the text "```stl" inside a value string, causing
        the parser to incorrectly switch to fenced mode and find 0 statements.
        """
        text = """
[Regex_Pattern_Design] -> [Initial_Character_Set] ::mod(
  rule="definitional",
  confidence=1.0,
  value="Extract STL from Markdown ```stl code blocks"
)
"""
        # Simulate pipeline: Merge first, then extract
        merged_text = _merge_multiline_statements(text)
        stl_text, metadata = _auto_extract_stl(merged_text, mode='auto')
        
        # It should NOT be fenced mode because ```stl is not at start of line
        assert metadata['format'] != 'fenced'
        
        # It should find the statement
        assert "[Regex_Pattern_Design]" in stl_text
        assert "```stl" in stl_text # The string content should be preserved

