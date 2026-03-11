# -*- coding: utf-8 -*-
"""Tests for STL Reader — streaming parser module."""

import threading
import time
from io import StringIO
from pathlib import Path

import pytest

from stl_parser.reader import stream_parse, STLReader, ReaderStats
from stl_parser.errors import STLReaderError
from stl_parser import parse, STLEmitter


# ========================================
# FIXTURES
# ========================================

@pytest.fixture
def stl_file(tmp_path):
    """Create a temporary STL file with 3 statements."""
    p = tmp_path / "test.stl"
    p.write_text(
        '[A] -> [B] ::mod(confidence=0.9, rule="causal")\n'
        '[C] -> [D] ::mod(confidence=0.7, rule="logical")\n'
        '[E] -> [F] ::mod(confidence=0.5, rule="empirical")\n',
        encoding="utf-8",
    )
    return p


@pytest.fixture
def mixed_file(tmp_path):
    """File with statements, comments, and blank lines."""
    p = tmp_path / "mixed.stl"
    p.write_text(
        "# Header comment\n"
        "\n"
        '[A] -> [B] ::mod(confidence=0.9)\n'
        "# Middle comment\n"
        "\n"
        '[C] -> [D] ::mod(confidence=0.7)\n'
        "\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def multiline_file(tmp_path):
    """File with multi-line statements."""
    p = tmp_path / "multiline.stl"
    p.write_text(
        '[A] -> [B] ::mod(\n'
        '  confidence=0.9,\n'
        '  rule="causal"\n'
        ')\n'
        '[C] -> [D]\n',
        encoding="utf-8",
    )
    return p


# ========================================
# stream_parse — Core Functionality (T01–T09)
# ========================================

class TestStreamParseCore:
    """T01–T09: Basic stream_parse functionality."""

    def test_stream_parse_file(self, stl_file):
        """T01: Generator yields correct number of statements from file."""
        stmts = list(stream_parse(stl_file))
        assert len(stmts) == 3
        assert stmts[0].source.name == "A"
        assert stmts[1].source.name == "C"
        assert stmts[2].source.name == "E"

    def test_stream_parse_stringio(self):
        """T02: Yields statements from StringIO."""
        sio = StringIO(
            '[X] -> [Y] ::mod(confidence=0.8)\n'
            '[Z] -> [W]\n'
        )
        stmts = list(stream_parse(sio))
        assert len(stmts) == 2
        assert stmts[0].source.name == "X"

    def test_stream_parse_iterable(self):
        """T03: Yields statements from list of line strings."""
        lines = [
            '[A] -> [B] ::mod(confidence=0.9)',
            '[C] -> [D]',
        ]
        stmts = list(stream_parse(lines))
        assert len(stmts) == 2

    def test_stream_parse_filepath_string(self, stl_file):
        """T04: Accepts string path."""
        stmts = list(stream_parse(str(stl_file)))
        assert len(stmts) == 3

    def test_stream_parse_path_object(self, stl_file):
        """T05: Accepts Path object."""
        stmts = list(stream_parse(Path(stl_file)))
        assert len(stmts) == 3

    def test_stream_parse_empty_file(self, tmp_path):
        """T06: Empty file yields nothing."""
        p = tmp_path / "empty.stl"
        p.write_text("", encoding="utf-8")
        stmts = list(stream_parse(p))
        assert stmts == []

    def test_stream_parse_comments_skipped(self, tmp_path):
        """T07: Comment lines are not yielded."""
        p = tmp_path / "comments.stl"
        p.write_text(
            "# comment 1\n# comment 2\n[A] -> [B]\n# trailing\n",
            encoding="utf-8",
        )
        stmts = list(stream_parse(p))
        assert len(stmts) == 1

    def test_stream_parse_blank_lines_skipped(self, tmp_path):
        """T08: Blank/whitespace-only lines are not yielded."""
        p = tmp_path / "blanks.stl"
        p.write_text(
            "\n\n[A] -> [B]\n   \n\n[C] -> [D]\n\n",
            encoding="utf-8",
        )
        stmts = list(stream_parse(p))
        assert len(stmts) == 2

    def test_stream_parse_mixed_content(self, mixed_file):
        """T09: Only statements yielded from mixed content."""
        stmts = list(stream_parse(mixed_file))
        assert len(stmts) == 2
        assert stmts[0].source.name == "A"
        assert stmts[1].source.name == "C"


# ========================================
# stream_parse — Multi-line Merging (T10–T12)
# ========================================

class TestMultilineMerging:
    """T10–T12: Multi-line statement handling."""

    def test_multiline_modifier(self, multiline_file):
        """T10: Statement split across 2 lines is merged and parsed."""
        stmts = list(stream_parse(multiline_file))
        assert len(stmts) == 2
        assert stmts[0].source.name == "A"
        assert stmts[0].modifiers.confidence == 0.9
        assert stmts[0].modifiers.rule == "causal"

    def test_multiline_deep_nesting(self, tmp_path):
        """T11: Statement split across 3+ lines."""
        p = tmp_path / "deep.stl"
        p.write_text(
            '[A] -> [B] ::mod(\n'
            '  confidence=0.9,\n'
            '  rule="causal",\n'
            '  source="doi:10.1234"\n'
            ')\n',
            encoding="utf-8",
        )
        stmts = list(stream_parse(p))
        assert len(stmts) == 1
        assert stmts[0].modifiers.confidence == 0.9
        assert stmts[0].modifiers.source == "doi:10.1234"

    def test_multiline_overflow_skip(self, tmp_path):
        """T12a: Overflow raises on on_error='raise'."""
        # 25 continuation lines (exceeds 20-line limit)
        lines = ['[A] -> [B] ::mod(\n']
        for i in range(24):
            lines.append(f'  field{i}="val",\n')
        lines.append(')\n')
        p = tmp_path / "overflow.stl"
        p.write_text("".join(lines), encoding="utf-8")

        with pytest.raises(STLReaderError) as exc_info:
            list(stream_parse(p, on_error="raise"))
        assert "E962" in str(exc_info.value)


# ========================================
# stream_parse — Where Filtering (T13–T16)
# ========================================

class TestWhereFiltering:
    """T13–T16: Built-in where filtering."""

    def test_where_exact_match(self, stl_file):
        """T13: Exact match filter."""
        stmts = list(stream_parse(stl_file, where={"source": "A"}))
        assert len(stmts) == 1
        assert stmts[0].source.name == "A"

    def test_where_gt_operator(self, stl_file):
        """T14: Greater-than operator."""
        stmts = list(stream_parse(stl_file, where={"confidence__gt": 0.8}))
        assert len(stmts) == 1
        assert stmts[0].modifiers.confidence == 0.9

    def test_where_multiple_conditions(self, stl_file):
        """T15: Multiple conditions (AND logic)."""
        stmts = list(stream_parse(
            stl_file,
            where={"rule": "causal", "confidence__gte": 0.5},
        ))
        assert len(stmts) == 1
        assert stmts[0].source.name == "A"

    def test_where_no_matches(self, stl_file):
        """T16: No matches yields empty."""
        stmts = list(stream_parse(stl_file, where={"source": "Nonexistent"}))
        assert stmts == []


# ========================================
# stream_parse — Error Handling (T17–T19)
# ========================================

class TestErrorHandling:
    """T17–T19: Error handling modes."""

    def test_on_error_skip(self, tmp_path):
        """T17: Invalid lines skipped by default."""
        p = tmp_path / "mixed_errors.stl"
        p.write_text(
            '[A] -> [B] ::mod(confidence=0.9)\n'
            'this is not valid STL at all\n'
            '[C] -> [D]\n',
            encoding="utf-8",
        )
        stmts = list(stream_parse(p))
        assert len(stmts) == 2

    def test_on_error_raise(self, tmp_path):
        """T18: Raises on invalid line when on_error='raise'."""
        p = tmp_path / "bad.stl"
        p.write_text(
            'this is garbage\n',
            encoding="utf-8",
        )
        with pytest.raises(STLReaderError) as exc_info:
            list(stream_parse(p, on_error="raise"))
        assert "E961" in str(exc_info.value)

    def test_source_not_found(self):
        """T19: Non-existent file raises E960."""
        with pytest.raises(STLReaderError) as exc_info:
            list(stream_parse("/nonexistent/path/file.stl"))
        assert "E960" in str(exc_info.value)


# ========================================
# STLReader — Context Manager (T20–T25)
# ========================================

class TestSTLReaderContextManager:
    """T20–T25: STLReader class."""

    def test_reader_context_manager(self, stl_file):
        """T20: Context manager opens and closes properly."""
        with STLReader(stl_file) as reader:
            stmts = list(reader)
        assert len(stmts) == 3

    def test_reader_iter(self, stl_file):
        """T21: Yields statements through iteration."""
        reader = STLReader(stl_file)
        stmts = list(reader)
        assert len(stmts) == 3
        reader.close()

    def test_reader_stats(self, mixed_file):
        """T22: Stats reflect all counts."""
        with STLReader(mixed_file) as reader:
            _ = list(reader)
            stats = reader.stats
        assert stats.statements_yielded == 2
        assert stats.comments_seen == 2
        assert stats.blank_lines == 3  # 3 blank lines in mixed_file
        assert stats.lines_processed == 7

    def test_reader_read_all(self, stl_file):
        """T23: read_all() returns ParseResult."""
        with STLReader(stl_file) as reader:
            result = reader.read_all()
        assert len(result.statements) == 3
        assert result.is_valid is True

    def test_reader_read_all_with_where(self, stl_file):
        """T24: read_all() with where filter."""
        with STLReader(stl_file, where={"rule": "causal"}) as reader:
            result = reader.read_all()
        assert len(result.statements) == 1
        assert result.statements[0].source.name == "A"

    def test_reader_close_explicit(self, stl_file):
        """T25: Explicit close releases resources."""
        reader = STLReader(stl_file)
        _ = list(reader)
        reader.close()
        assert reader._closed is True


# ========================================
# STLReader — Tail Mode (T26–T28)
# ========================================

class TestTailMode:
    """T26–T28: Tail mode functionality."""

    def test_tail_reads_new_content(self, tmp_path):
        """T26: Tail reader picks up content written after start."""
        p = tmp_path / "tail_test.stl"
        # Write initial content
        p.write_text(
            '[A] -> [B] ::mod(confidence=0.9)\n'
            '[C] -> [D] ::mod(confidence=0.8)\n',
            encoding="utf-8",
        )

        collected = []

        def reader_thread():
            with STLReader(p, tail=True, tail_interval=0.05) as reader:
                for stmt in reader:
                    collected.append(stmt)
                    if len(collected) >= 4:
                        reader.close()
                        break

        t = threading.Thread(target=reader_thread)
        t.start()

        # Give reader time to read initial content
        time.sleep(0.2)

        # Append new content
        with open(p, "a", encoding="utf-8") as f:
            f.write('[E] -> [F] ::mod(confidence=0.7)\n')
            f.flush()
            f.write('[G] -> [H] ::mod(confidence=0.6)\n')
            f.flush()

        t.join(timeout=5)
        assert len(collected) == 4

    def test_tail_only_for_files(self):
        """T27: Tail mode rejects non-file sources."""
        with pytest.raises(ValueError, match="tail mode requires a file path"):
            STLReader(StringIO(""), tail=True)

    def test_tail_interval_custom(self, tmp_path):
        """T28: Custom tail_interval is stored."""
        p = tmp_path / "dummy.stl"
        p.write_text("", encoding="utf-8")
        reader = STLReader(p, tail=True, tail_interval=0.1)
        assert reader._tail_interval == 0.1
        reader.close()


# ========================================
# Emitter → Reader Integration (T29–T32)
# ========================================

class TestEmitterReaderIntegration:
    """T29–T32: Round-trip with STLEmitter."""

    def test_emitter_reader_roundtrip(self, tmp_path):
        """T29: Emit 5 statements, read back all 5."""
        p = tmp_path / "roundtrip.stl"
        with STLEmitter(log_path=str(p), auto_timestamp=False) as emitter:
            for i in range(5):
                emitter.emit(f"[Src_{i}]", f"[Tgt_{i}]", confidence=0.5 + i * 0.1)

        stmts = list(stream_parse(p))
        assert len(stmts) == 5
        for i, stmt in enumerate(stmts):
            assert stmt.source.name == f"Src_{i}"
            assert stmt.target.name == f"Tgt_{i}"

    def test_emitter_reader_with_namespace(self, tmp_path):
        """T30: Namespaced emitter output reads correctly."""
        p = tmp_path / "ns.stl"
        with STLEmitter(log_path=str(p), namespace="Agent", auto_timestamp=False) as emitter:
            emitter.emit("[Start]", "[Running]", confidence=0.9)

        stmts = list(stream_parse(p))
        assert len(stmts) == 1
        assert stmts[0].source.namespace == "Agent"
        assert stmts[0].source.name == "Start"

    def test_emitter_reader_with_comments(self, tmp_path):
        """T31: Reader skips emitter comments, yields only statements."""
        p = tmp_path / "comments.stl"
        with STLEmitter(log_path=str(p), auto_timestamp=False) as emitter:
            emitter.comment("This is a section header")
            emitter.emit("[A]", "[B]", confidence=0.9)
            emitter.comment("End of section")
            emitter.emit("[C]", "[D]", confidence=0.8)

        stmts = list(stream_parse(p))
        assert len(stmts) == 2

    def test_emitter_reader_with_timestamp(self, tmp_path):
        """T32: Emitter auto_timestamp is preserved in reader output."""
        p = tmp_path / "ts.stl"
        with STLEmitter(log_path=str(p), auto_timestamp=True) as emitter:
            emitter.emit("[A]", "[B]", confidence=0.9)

        stmts = list(stream_parse(p))
        assert len(stmts) == 1
        assert stmts[0].modifiers.timestamp is not None


# ========================================
# Memory Efficiency (T33)
# ========================================

class TestMemoryEfficiency:
    """T33: Verify generator-based memory pattern."""

    def test_large_file_generator(self, tmp_path):
        """T33: 1000-statement file streams correctly without full list."""
        p = tmp_path / "large.stl"
        with open(p, "w", encoding="utf-8") as f:
            for i in range(1000):
                f.write(f'[Src_{i}] -> [Tgt_{i}] ::mod(confidence=0.{i % 10})\n')

        count = 0
        for stmt in stream_parse(p):
            count += 1
            # Not collecting into list — constant memory
        assert count == 1000


# ========================================
# Edge Cases (T34–T35)
# ========================================

class TestEdgeCases:
    """T34–T35: Unicode and namespace edge cases."""

    def test_unicode_statements(self, tmp_path):
        """T34: Chinese/Arabic anchor names parse correctly."""
        p = tmp_path / "unicode.stl"
        p.write_text(
            '[黄帝内经] -> [素问] ::mod(confidence=0.95)\n',
            encoding="utf-8",
        )
        stmts = list(stream_parse(p))
        assert len(stmts) == 1
        assert stmts[0].source.name == "黄帝内经"
        assert stmts[0].target.name == "素问"

    def test_namespaced_anchors(self, tmp_path):
        """T35: Namespaced anchors parse correctly."""
        p = tmp_path / "ns.stl"
        p.write_text(
            '[Physics:Energy] -> [Physics:Mass] ::mod(rule="logical")\n',
            encoding="utf-8",
        )
        stmts = list(stream_parse(p))
        assert len(stmts) == 1
        assert stmts[0].source.namespace == "Physics"
        assert stmts[0].source.name == "Energy"


# ========================================
# ReaderStats model (supplementary)
# ========================================

class TestReaderStats:
    """Supplementary: ReaderStats model."""

    def test_default_values(self):
        stats = ReaderStats()
        assert stats.lines_processed == 0
        assert stats.statements_yielded == 0
        assert stats.errors_skipped == 0
        assert stats.comments_seen == 0
        assert stats.blank_lines == 0

    def test_reader_stats_errors(self, tmp_path):
        """Stats track skipped errors."""
        p = tmp_path / "errors.stl"
        p.write_text(
            '[A] -> [B]\n'
            'invalid line\n'
            'also bad\n'
            '[C] -> [D]\n',
            encoding="utf-8",
        )
        with STLReader(p) as reader:
            _ = list(reader)
            stats = reader.stats
        assert stats.statements_yielded == 2
        assert stats.errors_skipped == 2
