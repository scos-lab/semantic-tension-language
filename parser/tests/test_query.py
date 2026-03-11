# -*- coding: utf-8 -*-
"""Tests for stl_parser.query module."""

import pytest

from stl_parser import parse, stl, stl_doc
from stl_parser.query import find, find_all, filter_statements, select, stl_pointer
from stl_parser.errors import STLQueryError


# ========================================
# FIXTURES
# ========================================

@pytest.fixture
def sample_result():
    """A ParseResult with diverse statements for testing."""
    return stl_doc(
        stl("[Theory_X]", "[Prediction_A]").mod(confidence=0.95, rule="logical"),
        stl("[Theory_X]", "[Prediction_B]").mod(confidence=0.70, rule="causal", strength=0.6),
        stl("[Study_Y]", "[Finding_Z]").mod(confidence=0.85, rule="empirical", source="doi:10.1234/study"),
        stl("[Events:Start]", "[Events:Running]").mod(confidence=0.90),
        stl("[A]", "[B]"),  # no modifiers
    )


@pytest.fixture
def custom_result():
    """A ParseResult with custom modifier fields."""
    return stl_doc(
        stl("[Mod_builder]", "[Cls_Foo]").mod(type="class", line=86, confidence=0.9),
        stl("[Mod_builder]", "[Fn_bar]").mod(type="function", line=120, confidence=0.8),
        stl("[Mod_models]", "[Cls_Anchor]").mod(type="class", line=55, confidence=0.95),
    )


# ========================================
# TESTS: find()
# ========================================

class TestFind:
    """Tests for find()."""

    def test_find_by_source(self, sample_result):
        stmt = find(sample_result, source="Theory_X")
        assert stmt is not None
        assert stmt.source.name == "Theory_X"
        assert stmt.target.name == "Prediction_A"  # first match

    def test_find_by_target(self, sample_result):
        stmt = find(sample_result, target="Finding_Z")
        assert stmt is not None
        assert stmt.source.name == "Study_Y"

    def test_find_by_source_and_target(self, sample_result):
        stmt = find(sample_result, source="Theory_X", target="Prediction_B")
        assert stmt is not None
        assert stmt.target.name == "Prediction_B"

    def test_find_no_match(self, sample_result):
        stmt = find(sample_result, source="Nonexistent")
        assert stmt is None

    def test_find_by_confidence(self, sample_result):
        stmt = find(sample_result, confidence=0.95)
        assert stmt is not None
        assert stmt.source.name == "Theory_X"

    def test_find_by_confidence_gt(self, sample_result):
        stmt = find(sample_result, confidence__gt=0.90)
        assert stmt is not None
        assert stmt.modifiers.confidence == 0.95

    def test_find_by_rule(self, sample_result):
        stmt = find(sample_result, rule="causal")
        assert stmt is not None
        assert stmt.target.name == "Prediction_B"

    def test_find_custom_field(self, custom_result):
        stmt = find(custom_result, type="function")
        assert stmt is not None
        assert stmt.target.name == "Fn_bar"

    def test_find_no_kwargs_returns_first(self, sample_result):
        stmt = find(sample_result)
        assert stmt is not None
        assert stmt.source.name == "Theory_X"
        assert stmt.target.name == "Prediction_A"

    def test_find_multiple_conditions_and(self, sample_result):
        stmt = find(sample_result, source="Theory_X", confidence__lt=0.8)
        assert stmt is not None
        assert stmt.modifiers.confidence == 0.70

    def test_find_no_modifiers_statement(self, sample_result):
        """Statement with no modifiers: modifier fields resolve to None."""
        stmt = find(sample_result, source="A")
        assert stmt is not None
        assert stmt.modifiers is None

    def test_find_no_modifiers_confidence_none(self, sample_result):
        """Querying confidence=None matches statement without modifiers."""
        stmt = find(sample_result, confidence=None)
        assert stmt is not None
        assert stmt.source.name == "A"


# ========================================
# TESTS: find_all()
# ========================================

class TestFindAll:
    """Tests for find_all()."""

    def test_find_all_by_source(self, sample_result):
        stmts = find_all(sample_result, source="Theory_X")
        assert len(stmts) == 2

    def test_find_all_no_match(self, sample_result):
        stmts = find_all(sample_result, source="Nonexistent")
        assert stmts == []

    def test_find_all_by_confidence_gte(self, sample_result):
        stmts = find_all(sample_result, confidence__gte=0.85)
        assert len(stmts) == 3  # 0.95, 0.85, 0.90

    def test_find_all_by_rule_in(self, sample_result):
        stmts = find_all(sample_result, rule__in=["causal", "logical"])
        assert len(stmts) == 2

    def test_find_all_custom_field(self, custom_result):
        stmts = find_all(custom_result, type="class")
        assert len(stmts) == 2


# ========================================
# TESTS: filter_statements()
# ========================================

class TestFilterStatements:
    """Tests for filter_statements()."""

    def test_filter_returns_parse_result(self, sample_result):
        filtered = filter_statements(sample_result, confidence__gt=0.8)
        from stl_parser.models import ParseResult
        assert isinstance(filtered, ParseResult)

    def test_filter_correct_count(self, sample_result):
        filtered = filter_statements(sample_result, confidence__gt=0.8)
        assert len(filtered.statements) == 3  # 0.95, 0.85, 0.90

    def test_filter_original_unmodified(self, sample_result):
        original_count = len(sample_result.statements)
        filter_statements(sample_result, confidence__gt=0.99)
        assert len(sample_result.statements) == original_count

    def test_filter_to_stl(self, sample_result):
        filtered = filter_statements(sample_result, rule="causal")
        stl_text = filtered.to_stl()
        assert "Prediction_B" in stl_text
        assert "Prediction_A" not in stl_text

    def test_chained_filter(self, sample_result):
        step1 = filter_statements(sample_result, source="Theory_X")
        step2 = filter_statements(step1, confidence__gt=0.8)
        assert len(step2.statements) == 1
        assert step2.statements[0].modifiers.confidence == 0.95


# ========================================
# TESTS: select()
# ========================================

class TestSelect:
    """Tests for select()."""

    def test_select_source(self, sample_result):
        names = select(sample_result, "source")
        assert names == ["Theory_X", "Theory_X", "Study_Y", "Start", "A"]

    def test_select_target(self, sample_result):
        names = select(sample_result, "target")
        assert names == ["Prediction_A", "Prediction_B", "Finding_Z", "Running", "B"]

    def test_select_confidence(self, sample_result):
        confs = select(sample_result, "confidence")
        assert confs == [0.95, 0.70, 0.85, 0.90, None]

    def test_select_custom_field(self, custom_result):
        types = select(custom_result, "type")
        assert types == ["class", "function", "class"]

    def test_select_absent_field(self, sample_result):
        vals = select(sample_result, "nonexistent_field")
        assert all(v is None for v in vals)

    def test_select_source_namespace(self, sample_result):
        ns = select(sample_result, "source_namespace")
        assert ns[3] == "Events"  # [Events:Start]
        assert ns[0] is None  # [Theory_X] has no namespace


# ========================================
# TESTS: stl_pointer()
# ========================================

class TestSTLPointer:
    """Tests for stl_pointer()."""

    def test_pointer_source_name(self, sample_result):
        val = stl_pointer(sample_result, "/0/source/name")
        assert val == "Theory_X"

    def test_pointer_target_name(self, sample_result):
        val = stl_pointer(sample_result, "/2/target/name")
        assert val == "Finding_Z"

    def test_pointer_modifiers_confidence(self, sample_result):
        val = stl_pointer(sample_result, "/0/modifiers/confidence")
        assert val == 0.95

    def test_pointer_modifiers_rule(self, sample_result):
        val = stl_pointer(sample_result, "/1/modifiers/rule")
        assert val == "causal"

    def test_pointer_namespace(self, sample_result):
        val = stl_pointer(sample_result, "/3/source/namespace")
        assert val == "Events"

    def test_pointer_no_namespace(self, sample_result):
        val = stl_pointer(sample_result, "/0/source/namespace")
        assert val is None

    def test_pointer_custom_field(self, custom_result):
        val = stl_pointer(custom_result, "/0/modifiers/type")
        assert val == "class"

    def test_pointer_custom_line(self, custom_result):
        val = stl_pointer(custom_result, "/0/modifiers/line")
        assert val == 86

    def test_pointer_index_out_of_range(self, sample_result):
        with pytest.raises(STLQueryError) as exc_info:
            stl_pointer(sample_result, "/99/source/name")
        assert "E452" in str(exc_info.value)

    def test_pointer_invalid_path_segment(self, sample_result):
        with pytest.raises(STLQueryError) as exc_info:
            stl_pointer(sample_result, "/0/nonexistent")
        assert "E451" in str(exc_info.value)

    def test_pointer_non_integer_index(self, sample_result):
        with pytest.raises(STLQueryError) as exc_info:
            stl_pointer(sample_result, "/abc/source/name")
        assert "E451" in str(exc_info.value)

    def test_pointer_statement_object(self, sample_result):
        """Pointer to statement index alone returns the Statement object."""
        val = stl_pointer(sample_result, "/0")
        assert val.source.name == "Theory_X"

    def test_pointer_empty_path(self, sample_result):
        """Empty path returns the ParseResult itself."""
        val = stl_pointer(sample_result, "/")
        assert val is sample_result


# ========================================
# TESTS: ParseResult convenience methods
# ========================================

class TestParseResultMethods:
    """Tests for ParseResult.find(), .find_all(), .filter(), .select(), __getitem__."""

    def test_result_find(self, sample_result):
        stmt = sample_result.find(source="Study_Y")
        assert stmt is not None
        assert stmt.source.name == "Study_Y"

    def test_result_find_all(self, sample_result):
        stmts = sample_result.find_all(rule="causal")
        assert len(stmts) == 1

    def test_result_filter(self, sample_result):
        filtered = sample_result.filter(confidence__gte=0.85)
        assert len(filtered.statements) == 3

    def test_result_select(self, sample_result):
        names = sample_result.select("source")
        assert len(names) == 5

    def test_getitem_int(self, sample_result):
        stmt = sample_result[0]
        assert stmt.source.name == "Theory_X"

    def test_getitem_negative_int(self, sample_result):
        stmt = sample_result[-1]
        assert stmt.source.name == "A"

    def test_getitem_slice(self, sample_result):
        stmts = sample_result[1:3]
        assert len(stmts) == 2
        assert stmts[0].target.name == "Prediction_B"

    def test_getitem_str(self, sample_result):
        stmts = sample_result["Theory_X"]
        assert len(stmts) == 2

    def test_getitem_str_no_match(self, sample_result):
        stmts = sample_result["Nonexistent"]
        assert stmts == []

    def test_getitem_invalid_type(self, sample_result):
        with pytest.raises(TypeError):
            sample_result[3.14]

    def test_chained_methods(self, sample_result):
        """filter().find() chain works."""
        filtered = sample_result.filter(source="Theory_X")
        stmt = filtered.find(confidence__gt=0.8)
        assert stmt is not None
        assert stmt.modifiers.confidence == 0.95


# ========================================
# TESTS: Operators
# ========================================

class TestOperators:
    """Tests for all query operators."""

    def test_eq(self, sample_result):
        assert find(sample_result, confidence=0.95) is not None

    def test_gt(self, sample_result):
        assert find(sample_result, confidence__gt=0.94) is not None

    def test_gte(self, sample_result):
        assert find(sample_result, confidence__gte=0.95) is not None

    def test_lt(self, sample_result):
        assert find(sample_result, confidence__lt=0.75) is not None
        assert find(sample_result, confidence__lt=0.75).modifiers.confidence == 0.70

    def test_lte(self, sample_result):
        assert find(sample_result, confidence__lte=0.70) is not None

    def test_ne(self, sample_result):
        stmts = find_all(sample_result, rule__ne="logical")
        # causal, empirical, and 2 with None rule (no rule or no modifiers)
        source_names = [s.source.name for s in stmts]
        assert "Theory_X" in source_names  # the causal one

    def test_contains(self, sample_result):
        stmt = find(sample_result, source__contains="Theory")
        assert stmt is not None
        assert stmt.source.name == "Theory_X"

    def test_startswith(self, sample_result):
        stmts = find_all(sample_result, source__startswith="Theory")
        assert len(stmts) == 2

    def test_in_operator(self, sample_result):
        stmts = find_all(sample_result, rule__in=["causal", "empirical"])
        assert len(stmts) == 2

    def test_none_with_gt_returns_false(self, sample_result):
        """Statement with no modifiers should not match confidence__gt."""
        stmts = find_all(sample_result, confidence__gt=0.0)
        # [A] -> [B] has no modifiers, should NOT be in results
        source_names = [s.source.name for s in stmts]
        assert "A" not in source_names


# ========================================
# TESTS: Edge Cases
# ========================================

class TestEdgeCases:
    """Edge case tests."""

    def test_empty_parse_result(self):
        from stl_parser.models import ParseResult
        empty = ParseResult()
        assert find(empty, source="A") is None
        assert find_all(empty, source="A") == []
        assert len(filter_statements(empty, source="A").statements) == 0
        assert select(empty, "source") == []

    def test_statement_no_modifiers(self):
        result = stl_doc(stl("[A]", "[B]"))
        assert find(result, confidence=None) is not None
        assert find(result, confidence__gt=0.5) is None

    def test_large_document(self):
        """Performance: 1000 statements should not be slow."""
        builders = [stl(f"[S{i}]", f"[T{i}]").mod(confidence=i/1000) for i in range(1000)]
        result = stl_doc(*builders)
        stmts = find_all(result, confidence__gt=0.999)
        assert len(stmts) == 0  # max confidence is 0.999
        # The last statement has confidence 0.999
        stmt = find(result, source="S999")
        assert stmt is not None

    def test_contains_on_modifier_source(self, sample_result):
        """source field on modifier (provenance), not source anchor."""
        stmt = find(sample_result, source__startswith="doi:")
        # "source" resolves to stmt.source.name, not modifier.source
        # So this checks anchor name starting with "doi:" — which is None
        assert stmt is None

    def test_parse_roundtrip_with_query(self):
        """Parse → filter → to_stl produces valid STL."""
        text = '[A] -> [B] ::mod(confidence=0.9, rule="causal")\n[C] -> [D] ::mod(confidence=0.5)'
        result = parse(text)
        filtered = filter_statements(result, confidence__gt=0.8)
        stl_text = filtered.to_stl()
        assert "[A]" in stl_text
        assert "[C]" not in stl_text
        # Re-parse the filtered output
        re_parsed = parse(stl_text)
        assert len(re_parsed.statements) == 1
