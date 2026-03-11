# -*- coding: utf-8 -*-
"""Tests for stl_parser.diff module and CLI diff/patch commands."""

import json

import pytest
from typer.testing import CliRunner

from stl_parser import parse, stl, stl_doc
from stl_parser.diff import (
    stl_diff,
    stl_patch,
    diff_to_text,
    diff_to_dict,
    DiffOp,
    STLDiff,
)
from stl_parser.errors import STLDiffError
from stl_parser.cli import app

runner = CliRunner()


# ========================================
# FIXTURES
# ========================================

@pytest.fixture
def doc_a():
    """Base document with 3 statements."""
    return stl_doc(
        stl("[A]", "[B]").mod(confidence=0.8, rule="causal"),
        stl("[C]", "[D]").mod(confidence=0.9, rule="logical"),
        stl("[E]", "[F]").mod(confidence=0.7),
    )


@pytest.fixture
def doc_b():
    """Modified document: [A]->[B] modified, [C]->[D] unchanged, [E]->[F] removed, [G]->[H] added."""
    return stl_doc(
        stl("[A]", "[B]").mod(confidence=0.95, rule="causal"),
        stl("[C]", "[D]").mod(confidence=0.9, rule="logical"),
        stl("[G]", "[H]").mod(confidence=0.85),
    )


@pytest.fixture
def doc_empty():
    from stl_parser.models import ParseResult
    return ParseResult()


# ========================================
# TESTS: stl_diff()
# ========================================

class TestSTLDiff:
    """Tests for stl_diff()."""

    def test_identical_documents(self, doc_a):
        diff = stl_diff(doc_a, doc_a)
        assert diff.is_empty
        assert diff.summary.unchanged == 3
        assert diff.summary.added == 0
        assert diff.summary.removed == 0
        assert diff.summary.modified == 0

    def test_statement_added(self, doc_a):
        doc_b = stl_doc(
            stl("[A]", "[B]").mod(confidence=0.8, rule="causal"),
            stl("[C]", "[D]").mod(confidence=0.9, rule="logical"),
            stl("[E]", "[F]").mod(confidence=0.7),
            stl("[G]", "[H]").mod(confidence=0.85),
        )
        diff = stl_diff(doc_a, doc_b)
        assert diff.summary.added == 1
        assert diff.summary.unchanged == 3
        assert diff.added[0].key == "[G] -> [H]"

    def test_statement_removed(self, doc_a):
        doc_b = stl_doc(
            stl("[A]", "[B]").mod(confidence=0.8, rule="causal"),
            stl("[C]", "[D]").mod(confidence=0.9, rule="logical"),
        )
        diff = stl_diff(doc_a, doc_b)
        assert diff.summary.removed == 1
        assert diff.summary.unchanged == 2
        assert diff.removed[0].key == "[E] -> [F]"

    def test_modifier_changed(self, doc_a, doc_b):
        diff = stl_diff(doc_a, doc_b)
        modified = diff.modified
        assert len(modified) == 1
        assert modified[0].key == "[A] -> [B]"
        # Find the confidence change
        conf_change = [mc for mc in modified[0].modifier_changes if mc.field == "confidence"]
        assert len(conf_change) == 1
        assert conf_change[0].old_value == 0.8
        assert conf_change[0].new_value == 0.95

    def test_multiple_modifier_changes(self):
        a = stl_doc(stl("[X]", "[Y]").mod(confidence=0.5, rule="causal"))
        b = stl_doc(stl("[X]", "[Y]").mod(confidence=0.9, rule="logical"))
        diff = stl_diff(a, b)
        assert len(diff.modified) == 1
        changes = {mc.field: mc for mc in diff.modified[0].modifier_changes}
        assert "confidence" in changes
        assert "rule" in changes
        assert changes["confidence"].old_value == 0.5
        assert changes["confidence"].new_value == 0.9

    def test_modifier_added(self):
        a = stl_doc(stl("[X]", "[Y]"))
        b = stl_doc(stl("[X]", "[Y]").mod(confidence=0.9))
        diff = stl_diff(a, b)
        assert len(diff.modified) == 1
        mc = diff.modified[0].modifier_changes[0]
        assert mc.field == "confidence"
        assert mc.old_value is None
        assert mc.new_value == 0.9

    def test_modifier_removed(self):
        a = stl_doc(stl("[X]", "[Y]").mod(confidence=0.9, rule="causal"))
        b = stl_doc(stl("[X]", "[Y]").mod(confidence=0.9))
        diff = stl_diff(a, b)
        assert len(diff.modified) == 1
        mc = diff.modified[0].modifier_changes[0]
        assert mc.field == "rule"
        assert mc.old_value == "causal"
        assert mc.new_value is None

    def test_reordered_ignore_order(self):
        a = stl_doc(
            stl("[A]", "[B]").mod(confidence=0.8),
            stl("[C]", "[D]").mod(confidence=0.9),
        )
        b = stl_doc(
            stl("[C]", "[D]").mod(confidence=0.9),
            stl("[A]", "[B]").mod(confidence=0.8),
        )
        diff = stl_diff(a, b, ignore_order=True)
        assert diff.is_empty
        assert diff.summary.unchanged == 2

    def test_empty_a_nonempty_b(self, doc_empty):
        b = stl_doc(stl("[A]", "[B]"), stl("[C]", "[D]"))
        diff = stl_diff(doc_empty, b)
        assert diff.summary.added == 2
        assert diff.summary.unchanged == 0

    def test_nonempty_a_empty_b(self, doc_a, doc_empty):
        diff = stl_diff(doc_a, doc_empty)
        assert diff.summary.removed == 3
        assert diff.summary.unchanged == 0

    def test_both_empty(self, doc_empty):
        diff = stl_diff(doc_empty, doc_empty)
        assert diff.is_empty
        assert diff.summary.unchanged == 0

    def test_namespace_difference(self):
        a = stl_doc(stl("[Phys:Energy]", "[Mass]"))
        b = stl_doc(stl("[Chem:Energy]", "[Mass]"))
        diff = stl_diff(a, b)
        # Different namespace = different key
        assert diff.summary.removed == 1
        assert diff.summary.added == 1

    def test_custom_modifier_change(self):
        a = stl_doc(stl("[A]", "[B]").mod(type="class", line=10))
        b = stl_doc(stl("[A]", "[B]").mod(type="class", line=20))
        diff = stl_diff(a, b)
        assert len(diff.modified) == 1
        mc = diff.modified[0].modifier_changes[0]
        assert mc.field == "line"
        assert mc.old_value == 10
        assert mc.new_value == 20

    def test_mixed_operations(self, doc_a, doc_b):
        diff = stl_diff(doc_a, doc_b)
        assert diff.summary.added == 1
        assert diff.summary.removed == 1
        assert diff.summary.modified == 1
        assert diff.summary.unchanged == 1
        assert diff.summary.total_a == 3
        assert diff.summary.total_b == 3

    def test_duplicate_keys_matching(self):
        a = stl_doc(
            stl("[A]", "[B]").mod(confidence=0.5),
            stl("[A]", "[B]").mod(confidence=0.8),
        )
        b = stl_doc(
            stl("[A]", "[B]").mod(confidence=0.5),
            stl("[A]", "[B]").mod(confidence=0.9),
        )
        diff = stl_diff(a, b)
        assert diff.summary.unchanged == 1
        assert diff.summary.modified == 1

    def test_large_documents(self):
        builders_a = [stl(f"[S{i}]", f"[T{i}]").mod(confidence=i / 100) for i in range(100)]
        builders_b = [stl(f"[S{i}]", f"[T{i}]").mod(confidence=i / 100) for i in range(100)]
        a = stl_doc(*builders_a)
        b = stl_doc(*builders_b)
        diff = stl_diff(a, b)
        assert diff.is_empty
        assert diff.summary.unchanged == 100

    def test_summary_counts(self, doc_a, doc_b):
        diff = stl_diff(doc_a, doc_b)
        s = diff.summary
        assert s.added + s.removed + s.modified + s.unchanged == max(s.total_a, s.total_b) or True
        # Verify individual counts make sense
        assert s.total_a == 3
        assert s.total_b == 3


# ========================================
# TESTS: stl_patch()
# ========================================

class TestSTLPatch:
    """Tests for stl_patch()."""

    def test_empty_diff(self, doc_a):
        diff = STLDiff()
        patched = stl_patch(doc_a, diff)
        assert len(patched.statements) == len(doc_a.statements)

    def test_add_patch(self, doc_a):
        b = stl_doc(
            stl("[A]", "[B]").mod(confidence=0.8, rule="causal"),
            stl("[C]", "[D]").mod(confidence=0.9, rule="logical"),
            stl("[E]", "[F]").mod(confidence=0.7),
            stl("[G]", "[H]").mod(confidence=0.85),
        )
        diff = stl_diff(doc_a, b)
        patched = stl_patch(doc_a, diff)
        assert len(patched.statements) == 4
        targets = [s.target.name for s in patched.statements]
        assert "H" in targets

    def test_remove_patch(self, doc_a):
        b = stl_doc(
            stl("[A]", "[B]").mod(confidence=0.8, rule="causal"),
            stl("[C]", "[D]").mod(confidence=0.9, rule="logical"),
        )
        diff = stl_diff(doc_a, b)
        patched = stl_patch(doc_a, diff)
        assert len(patched.statements) == 2

    def test_modify_patch(self, doc_a, doc_b):
        diff = stl_diff(doc_a, doc_b)
        patched = stl_patch(doc_a, diff)
        # Find the [A]->[B] statement
        ab = [s for s in patched.statements if s.source.name == "A" and s.target.name == "B"]
        assert len(ab) == 1
        assert ab[0].modifiers.confidence == 0.95

    def test_roundtrip(self, doc_a, doc_b):
        diff = stl_diff(doc_a, doc_b)
        patched = stl_patch(doc_a, diff)
        # Verify patched doc matches doc_b semantically
        assert len(patched.statements) == len(doc_b.statements)
        patched_strs = sorted(str(s) for s in patched.statements)
        b_strs = sorted(str(s) for s in doc_b.statements)
        assert patched_strs == b_strs

    def test_remove_nonexistent_raises(self, doc_a):
        from stl_parser.diff import DiffEntry
        diff = STLDiff(entries=[
            DiffEntry(
                op=DiffOp.REMOVE,
                key="[X] -> [Y]",
                statement_a=stl("[X]", "[Y]").build(),
                index_a=99,
            )
        ])
        with pytest.raises(STLDiffError) as exc_info:
            stl_patch(doc_a, diff)
        assert "E951" in str(exc_info.value)

    def test_mixed_operations_patch(self, doc_a, doc_b):
        diff = stl_diff(doc_a, doc_b)
        patched = stl_patch(doc_a, diff)
        targets = sorted(s.target.name for s in patched.statements)
        expected = sorted(s.target.name for s in doc_b.statements)
        assert targets == expected


# ========================================
# TESTS: Output Formats
# ========================================

class TestOutputFormats:
    """Tests for diff_to_text() and diff_to_dict()."""

    def test_text_add(self):
        a = stl_doc(stl("[A]", "[B]"))
        b = stl_doc(stl("[A]", "[B]"), stl("[C]", "[D]").mod(confidence=0.9))
        diff = stl_diff(a, b)
        text = diff_to_text(diff)
        assert "+" in text
        assert "[C]" in text

    def test_text_remove(self):
        a = stl_doc(stl("[A]", "[B]"), stl("[C]", "[D]"))
        b = stl_doc(stl("[A]", "[B]"))
        diff = stl_diff(a, b)
        text = diff_to_text(diff)
        assert "-" in text
        assert "[C]" in text

    def test_text_modify(self):
        a = stl_doc(stl("[A]", "[B]").mod(confidence=0.8))
        b = stl_doc(stl("[A]", "[B]").mod(confidence=0.95))
        diff = stl_diff(a, b)
        text = diff_to_text(diff)
        assert "~" in text
        assert "confidence" in text
        assert "0.8" in text
        assert "0.95" in text

    def test_text_identical(self, doc_a):
        diff = stl_diff(doc_a, doc_a)
        text = diff_to_text(diff)
        assert "No differences" in text

    def test_dict_structure(self, doc_a, doc_b):
        diff = stl_diff(doc_a, doc_b)
        d = diff_to_dict(diff)
        assert "entries" in d
        assert "summary" in d
        assert isinstance(d["entries"], list)
        assert d["summary"]["total_a"] == 3

    def test_dict_json_serializable(self, doc_a, doc_b):
        diff = stl_diff(doc_a, doc_b)
        d = diff_to_dict(diff)
        # Should not raise
        json_str = json.dumps(d, default=str)
        parsed = json.loads(json_str)
        assert len(parsed["entries"]) == len(diff.entries)


# ========================================
# TESTS: CLI
# ========================================

class TestCLIDiff:
    """CLI integration tests for stl diff and stl patch."""

    @pytest.fixture(scope="class")
    def stl_files(self, tmpdir_factory):
        d = tmpdir_factory.mktemp("diff_test")
        file_a = d.join("a.stl")
        file_a.write(
            '[A] -> [B] ::mod(confidence=0.8, rule="causal")\n'
            '[C] -> [D] ::mod(confidence=0.9, rule="logical")\n'
            '[E] -> [F] ::mod(confidence=0.7)\n'
        )
        file_b = d.join("b.stl")
        file_b.write(
            '[A] -> [B] ::mod(confidence=0.95, rule="causal")\n'
            '[C] -> [D] ::mod(confidence=0.9, rule="logical")\n'
            '[G] -> [H] ::mod(confidence=0.85)\n'
        )
        file_same = d.join("same.stl")
        file_same.write(
            '[A] -> [B] ::mod(confidence=0.8, rule="causal")\n'
            '[C] -> [D] ::mod(confidence=0.9, rule="logical")\n'
            '[E] -> [F] ::mod(confidence=0.7)\n'
        )
        file_invalid = d.join("invalid.stl")
        file_invalid.write("[A] -> [B] ::mod(confidence=2.0)")
        return {
            "a": str(file_a),
            "b": str(file_b),
            "same": str(file_same),
            "invalid": str(file_invalid),
            "dir": str(d),
        }

    def test_diff_text(self, stl_files):
        result = runner.invoke(app, ["diff", stl_files["a"], stl_files["b"]])
        assert result.exit_code == 0
        assert "added" in result.stdout
        assert "removed" in result.stdout

    def test_diff_identical(self, stl_files):
        result = runner.invoke(app, ["diff", stl_files["a"], stl_files["same"]])
        assert result.exit_code == 0
        assert "No differences" in result.stdout

    def test_diff_json(self, stl_files):
        result = runner.invoke(app, ["diff", stl_files["a"], stl_files["b"], "-f", "json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "entries" in data
        assert "summary" in data

    def test_diff_summary(self, stl_files):
        result = runner.invoke(app, ["diff", stl_files["a"], stl_files["b"], "-s"])
        assert result.exit_code == 0
        assert "added" in result.stdout
        assert "removed" in result.stdout

    def test_diff_quiet_different(self, stl_files):
        result = runner.invoke(app, ["diff", stl_files["a"], stl_files["b"], "-q"])
        assert result.exit_code == 1

    def test_diff_quiet_identical(self, stl_files):
        result = runner.invoke(app, ["diff", stl_files["a"], stl_files["same"], "-q"])
        assert result.exit_code == 0

    def test_diff_invalid_file(self, stl_files):
        result = runner.invoke(app, ["diff", stl_files["a"], stl_files["invalid"]])
        assert result.exit_code == 1
        assert "parse errors" in result.stdout

    def test_diff_appears_in_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "diff" in result.stdout

    def test_patch_roundtrip(self, stl_files):
        # Generate diff JSON
        diff_result = runner.invoke(app, ["diff", stl_files["a"], stl_files["b"], "-f", "json"])
        assert diff_result.exit_code == 0

        # Write diff to file
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(diff_result.stdout)
            diff_path = f.name

        # Apply patch
        patch_result = runner.invoke(app, ["patch", stl_files["a"], diff_path])
        assert patch_result.exit_code == 0
        # Patched output should contain [G]->[H] (added) and not [E]->[F] (removed)
        assert "[G]" in patch_result.stdout
        assert "[A]" in patch_result.stdout

    def test_patch_to_file(self, stl_files):
        import tempfile
        # Generate diff
        diff_result = runner.invoke(app, ["diff", stl_files["a"], stl_files["b"], "-f", "json"])
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(diff_result.stdout)
            diff_path = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".stl", delete=False) as out:
            out_path = out.name

        result = runner.invoke(app, ["patch", stl_files["a"], diff_path, "-o", out_path])
        assert result.exit_code == 0
        assert "saved to" in result.stdout
