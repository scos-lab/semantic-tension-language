# -*- coding: utf-8 -*-
"""Tests for stl_parser.builder module."""

import pytest
from stl_parser.builder import stl, stl_doc, StatementBuilder, _parse_anchor_str
from stl_parser.models import Anchor, Modifier, Statement, ParseResult
from stl_parser.errors import STLBuilderError


class TestParseAnchorStr:
    """Tests for _parse_anchor_str()."""

    def test_simple_name(self):
        anchor = _parse_anchor_str("A")
        assert anchor.name == "A"
        assert anchor.namespace is None

    def test_bracketed_name(self):
        anchor = _parse_anchor_str("[A]")
        assert anchor.name == "A"
        assert anchor.namespace is None

    def test_namespaced(self):
        anchor = _parse_anchor_str("Obs:X")
        assert anchor.name == "X"
        assert anchor.namespace == "Obs"

    def test_bracketed_namespaced(self):
        anchor = _parse_anchor_str("[Obs:X]")
        assert anchor.name == "X"
        assert anchor.namespace == "Obs"

    def test_underscore_name(self):
        anchor = _parse_anchor_str("[Theory_Relativity]")
        assert anchor.name == "Theory_Relativity"

    def test_dotted_namespace(self):
        anchor = _parse_anchor_str("[A.B:Name]")
        assert anchor.name == "Name"
        assert anchor.namespace == "A.B"

    def test_strips_whitespace(self):
        anchor = _parse_anchor_str("  [A]  ")
        assert anchor.name == "A"

    def test_empty_string_raises(self):
        with pytest.raises(STLBuilderError):
            _parse_anchor_str("")

    def test_empty_brackets_raises(self):
        with pytest.raises(STLBuilderError):
            _parse_anchor_str("[]")

    def test_empty_after_namespace_raises(self):
        with pytest.raises(STLBuilderError):
            _parse_anchor_str("Ns:")

    def test_brackets_and_no_brackets_identical(self):
        a1 = _parse_anchor_str("A")
        a2 = _parse_anchor_str("[A]")
        assert a1.name == a2.name
        assert a1.namespace == a2.namespace


class TestStatementBuilder:
    """Tests for StatementBuilder and stl() factory."""

    def test_basic_build(self):
        stmt = stl("[A]", "[B]").build()
        assert isinstance(stmt, Statement)
        assert stmt.source.name == "A"
        assert stmt.target.name == "B"

    def test_mod_accumulation(self):
        stmt = stl("[A]", "[B]").mod(confidence=0.9).mod(rule="causal").build()
        assert stmt.modifiers is not None
        assert stmt.modifiers.confidence == 0.9
        assert stmt.modifiers.rule == "causal"

    def test_mod_override(self):
        stmt = stl("[A]", "[B]").mod(confidence=0.5).mod(confidence=0.9).build()
        assert stmt.modifiers.confidence == 0.9

    def test_no_modifiers(self):
        stmt = stl("[A]", "[B]").build()
        assert stmt.modifiers is None

    def test_namespace_parsing(self):
        stmt = stl("Obs:X", "Act:Y").build()
        assert stmt.source.name == "X"
        assert stmt.source.namespace == "Obs"
        assert stmt.target.name == "Y"
        assert stmt.target.namespace == "Act"

    def test_custom_modifiers(self):
        stmt = stl("[A]", "[B]").mod(
            confidence=0.9,
            my_custom_field="hello",
        ).build()
        assert stmt.modifiers.confidence == 0.9
        assert stmt.modifiers.custom == {"my_custom_field": "hello"}

    def test_all_standard_modifiers(self):
        stmt = stl("[A]", "[B]").mod(
            confidence=0.9,
            rule="causal",
            strength=0.8,
            source="test",
            author="tester",
        ).build()
        assert stmt.modifiers.confidence == 0.9
        assert stmt.modifiers.rule == "causal"
        assert stmt.modifiers.strength == 0.8
        assert stmt.modifiers.source == "test"
        assert stmt.modifiers.author == "tester"

    def test_invalid_confidence_raises(self):
        with pytest.raises(STLBuilderError):
            stl("[A]", "[B]").mod(confidence=2.0).build()

    def test_no_validate_skips(self):
        # With no_validate, even invalid rule types won't error at build time
        # (Pydantic validation for confidence range still applies, but
        # semantic validation from validator is skipped)
        stmt = stl("[A]", "[B]").no_validate().mod(rule="invalid_rule").build()
        assert stmt.modifiers.rule == "invalid_rule"

    def test_chaining(self):
        builder = stl("[A]", "[B]")
        result = builder.mod(confidence=0.9)
        assert result is builder  # Returns self

    def test_str_roundtrip(self):
        stmt = stl("[A]", "[B]").mod(confidence=0.9, rule="causal").build()
        text = str(stmt)
        assert "[A]" in text
        assert "[B]" in text
        assert "confidence=0.9" in text
        assert 'rule="causal"' in text

    def test_custom_modifiers_in_str(self):
        """Issue 1: custom fields must appear in str(Statement)."""
        stmt = stl("[Mod:builder]", "[Cls:Foo]").mod(
            confidence=0.95,
            type="class",
            line=86,
            signature="build()",
        ).build()
        text = str(stmt)
        assert "confidence=0.95" in text
        assert 'type="class"' in text
        assert "line=86" in text
        assert 'signature="build()"' in text

    def test_only_custom_modifiers_in_str(self):
        """Edge case: ONLY custom fields, no standard fields."""
        stmt = stl("[A]", "[B]").mod(
            category="source",
            depth=3,
        ).build()
        text = str(stmt)
        assert "::mod(" in text
        assert 'category="source"' in text
        assert "depth=3" in text

    def test_custom_modifiers_roundtrip_to_stl(self):
        """Issue 5: stl_doc().to_stl() must preserve custom fields."""
        doc = stl_doc(
            stl("[A]", "[B]").mod(confidence=0.9, type="class", line=42),
        )
        text = doc.to_stl()
        assert "confidence=0.9" in text
        assert 'type="class"' in text
        assert "line=42" in text


class TestStlDoc:
    """Tests for stl_doc()."""

    def test_basic_doc(self):
        doc = stl_doc(
            stl("[A]", "[B]"),
            stl("[C]", "[D]"),
        )
        assert isinstance(doc, ParseResult)
        assert len(doc.statements) == 2
        assert doc.is_valid is True

    def test_mixed_builders_and_statements(self):
        pre_built = stl("[X]", "[Y]").build()
        doc = stl_doc(
            stl("[A]", "[B]"),
            pre_built,
        )
        assert len(doc.statements) == 2

    def test_empty_doc(self):
        doc = stl_doc()
        assert len(doc.statements) == 0
        assert doc.is_valid is True

    def test_single_statement(self):
        doc = stl_doc(stl("[A]", "[B]").mod(confidence=0.9))
        assert len(doc.statements) == 1

    def test_invalid_type_raises(self):
        with pytest.raises(STLBuilderError):
            stl_doc("not a builder")

    def test_doc_with_modifiers(self):
        doc = stl_doc(
            stl("[A]", "[B]").mod(rule="causal", confidence=0.9),
            stl("[C]", "[D]").mod(rule="logical", confidence=0.8),
        )
        assert doc.statements[0].modifiers.rule == "causal"
        assert doc.statements[1].modifiers.rule == "logical"
