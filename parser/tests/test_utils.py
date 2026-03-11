# -*- coding: utf-8 -*-
"""Tests for public utility functions."""

import pytest
from stl_parser import sanitize_anchor_name


class TestSanitizeAnchorName:
    """Tests for sanitize_anchor_name()."""

    def test_hyphens_replaced(self):
        assert sanitize_anchor_name("stl-parser") == "stl_parser"

    def test_dots_replaced(self):
        assert sanitize_anchor_name("v1.0.0") == "v1_0_0"

    def test_slashes_replaced(self):
        assert sanitize_anchor_name("src/core.py") == "src_core_py"

    def test_multiple_special_chars(self):
        assert sanitize_anchor_name("@scope/my-pkg") == "scope_my_pkg"

    def test_collapse_underscores(self):
        assert sanitize_anchor_name("a--b..c") == "a_b_c"

    def test_strip_edges(self):
        assert sanitize_anchor_name("-leading-") == "leading"

    def test_empty_returns_unknown(self):
        assert sanitize_anchor_name("") == "Unknown"

    def test_only_special_chars_returns_unknown(self):
        assert sanitize_anchor_name("---") == "Unknown"

    def test_unicode_chinese_preserved(self):
        assert sanitize_anchor_name("黄帝内经") == "黄帝内经"

    def test_unicode_arabic_preserved(self):
        assert sanitize_anchor_name("كتاب") == "كتاب"

    def test_already_valid_unchanged(self):
        assert sanitize_anchor_name("Theory_Relativity") == "Theory_Relativity"

    def test_mixed_valid_and_invalid(self):
        assert sanitize_anchor_name("file:src/builder.py") == "file_src_builder_py"

    def test_numbers_preserved(self):
        assert sanitize_anchor_name("Event_2025") == "Event_2025"

    def test_single_valid_char(self):
        assert sanitize_anchor_name("A") == "A"
