# -*- coding: utf-8 -*-
"""Tests for stl_parser.llm module."""

import pytest

from stl_parser.llm import (
    clean,
    repair,
    validate_llm_output,
    prompt_template,
    RepairAction,
    LLMValidationResult,
)
from stl_parser.schema import load_schema


class TestClean:
    """Tests for clean()."""

    def test_extract_from_fences(self):
        raw = "Here is output:\n```stl\n[A] -> [B]\n```\nDone."
        text, repairs = clean(raw)
        assert "[A] -> [B]" in text
        assert any(r.type == "strip_fence" for r in repairs)

    def test_normalize_arrows(self):
        raw = "[A] => [B]"
        text, repairs = clean(raw)
        assert "=>" not in text
        assert "->" in text
        assert any(r.type == "normalize_arrow" for r in repairs)

    def test_em_dash_arrow(self):
        raw = "[A] \u2014> [B]"
        text, repairs = clean(raw)
        assert "->" in text

    def test_strip_prose(self):
        raw = "Here is the STL:\n[A] -> [B] ::mod(confidence=0.9)\nThat was the output."
        text, repairs = clean(raw)
        assert "Here is" not in text
        assert "That was" not in text
        assert "[A] -> [B]" in text
        assert any(r.type == "strip_prose" for r in repairs)

    def test_merge_multiline(self):
        raw = "[A] -> [B] ::mod(\n  confidence=0.9\n)"
        text, repairs = clean(raw)
        assert "confidence=0.9" in text
        # After merge, should be single line
        stl_lines = [l for l in text.split("\n") if l.strip()]
        assert len(stl_lines) == 1

    def test_fix_whitespace(self):
        raw = "[A]  ->   [B]   ::mod(confidence=0.9)  "
        text, repairs = clean(raw)
        # No double spaces
        assert "  " not in text

    def test_preserve_comments(self):
        raw = "# This is a comment\n[A] -> [B]"
        text, repairs = clean(raw)
        assert "# This is a comment" in text

    def test_empty_input(self):
        text, repairs = clean("")
        assert text == ""
        assert len(repairs) == 0


class TestRepair:
    """Tests for repair()."""

    def test_fix_missing_brackets(self):
        text, repairs = repair("A -> [B]")
        assert "[A]" in text
        assert any(r.type == "add_brackets" for r in repairs)

    def test_fix_missing_brackets_target(self):
        text, repairs = repair("[A] -> B")
        assert "[B]" in text

    def test_fix_mod_prefix(self):
        text, repairs = repair("[A] -> [B] mod(confidence=0.9)")
        assert "::mod(" in text
        assert any(r.type == "fix_mod_prefix" for r in repairs)

    def test_quote_unquoted_strings(self):
        text, repairs = repair('[A] -> [B] ::mod(rule=causal)')
        assert 'rule="causal"' in text
        assert any(r.type == "quote_string" for r in repairs)

    def test_dont_quote_numbers(self):
        text, repairs = repair("[A] -> [B] ::mod(confidence=0.9)")
        assert "confidence=0.9" in text
        assert not any(r.type == "quote_string" for r in repairs)

    def test_dont_quote_booleans(self):
        text, repairs = repair("[A] -> [B] ::mod(deterministic=true)")
        assert "deterministic=true" in text

    def test_clamp_high_value(self):
        text, repairs = repair("[A] -> [B] ::mod(confidence=1.5)")
        assert "confidence=1.0" in text
        assert any(r.type == "clamp_value" for r in repairs)

    def test_clamp_negative_value(self):
        text, repairs = repair("[A] -> [B] ::mod(strength=-0.5)")
        assert "strength=0.0" in text

    def test_fix_typo(self):
        text, repairs = repair('[A] -> [B] ::mod(confience=0.9)')
        assert "confidence=0.9" in text
        assert any(r.type == "fix_typo" for r in repairs)

    def test_no_repair_needed(self):
        text, repairs = repair('[A] -> [B] ::mod(confidence=0.9, rule="causal")')
        assert len(repairs) == 0


class TestValidateLlmOutput:
    """Tests for validate_llm_output()."""

    def test_basic_pipeline(self):
        result = validate_llm_output('[A] -> [B] ::mod(confidence=0.9)')
        assert isinstance(result, LLMValidationResult)
        assert result.is_valid is True
        assert len(result.statements) == 1

    def test_full_pipeline_with_repairs(self):
        raw = "Output:\n```stl\nA => B mod(confience=1.5)\n```"
        result = validate_llm_output(raw)
        # Should have cleaned, repaired, and parsed
        assert len(result.repairs) > 0
        assert result.original_text == raw

    def test_multiple_statements(self):
        raw = "[A] -> [B] ::mod(confidence=0.9)\n[C] -> [D]"
        result = validate_llm_output(raw)
        assert len(result.statements) == 2

    def test_with_schema(self):
        schema = load_schema("""
        schema Test v1.0 {
          modifier {
            required: [confidence]
          }
        }
        """)
        result = validate_llm_output(
            '[A] -> [B] ::mod(confidence=0.9)',
            schema=schema,
        )
        assert result.is_valid is True
        assert result.schema_result is not None

    def test_schema_failure(self):
        schema = load_schema("""
        schema Test v1.0 {
          modifier {
            required: [confidence, rule]
          }
        }
        """)
        result = validate_llm_output(
            '[A] -> [B] ::mod(confidence=0.9)',
            schema=schema,
        )
        assert result.is_valid is False

    def test_invalid_syntax(self):
        result = validate_llm_output("not stl at all")
        # After stripping prose, nothing left → empty but valid (no statements)
        assert len(result.statements) == 0

    def test_repairs_list(self):
        result = validate_llm_output("[A] => [B]")
        assert isinstance(result.repairs, list)
        for r in result.repairs:
            assert isinstance(r, RepairAction)
            assert r.type
            assert r.description


class TestPromptTemplate:
    """Tests for prompt_template()."""

    def test_basic_template(self):
        template = prompt_template()
        assert "STL" in template
        assert "Source_Anchor" in template
        assert "confidence" in template

    def test_template_with_schema(self):
        schema = load_schema("""
        schema Events v1.0 {
          namespace "Events"
          modifier {
            required: [confidence, rule]
            confidence: float(0.5, 1.0)
            rule: enum("causal", "empirical")
          }
          anchor source {
            pattern: /^Event_/
          }
        }
        """)
        template = prompt_template(schema)
        assert "Events" in template
        assert "confidence" in template
        assert "causal" in template
        assert "Event_" in template
