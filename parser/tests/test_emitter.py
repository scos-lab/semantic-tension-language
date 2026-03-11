# -*- coding: utf-8 -*-
"""Tests for stl_parser.emitter module."""

import os
import sys
import tempfile
import threading
from io import StringIO

import pytest

from stl_parser.emitter import STLEmitter
from stl_parser.builder import stl
from stl_parser.models import Statement, Anchor, Modifier
from stl_parser.errors import STLEmitterError


class TestEmitterInit:
    """Tests for STLEmitter initialization."""

    def test_file_output(self, tmp_path):
        path = str(tmp_path / "test.stl")
        emitter = STLEmitter(log_path=path)
        assert emitter._file_handle is not None
        emitter.close()

    def test_stream_output(self):
        stream = StringIO()
        emitter = STLEmitter(stream=stream)
        assert emitter._stream is stream

    def test_no_output_raises(self):
        with pytest.raises(STLEmitterError):
            STLEmitter()

    def test_both_outputs(self, tmp_path):
        path = str(tmp_path / "test.stl")
        stream = StringIO()
        emitter = STLEmitter(log_path=path, stream=stream)
        assert emitter._file_handle is not None
        assert emitter._stream is stream
        emitter.close()


class TestEmit:
    """Tests for STLEmitter.emit()."""

    def test_basic_emit(self):
        stream = StringIO()
        emitter = STLEmitter(stream=stream)
        stmt = emitter.emit("[A]", "[B]", confidence=0.9)
        assert isinstance(stmt, Statement)
        assert stmt.source.name == "A"
        assert stmt.target.name == "B"

    def test_writes_to_stream(self):
        stream = StringIO()
        emitter = STLEmitter(stream=stream)
        emitter.emit("[A]", "[B]")
        output = stream.getvalue()
        assert "[A]" in output
        assert "[B]" in output
        assert "->" in output

    def test_writes_to_file(self, tmp_path):
        path = str(tmp_path / "test.stl")
        with STLEmitter(log_path=path) as emitter:
            emitter.emit("[A]", "[B]", confidence=0.9)

        with open(path, "r") as f:
            content = f.read()
        assert "[A]" in content
        assert "[B]" in content

    def test_auto_timestamp(self):
        stream = StringIO()
        emitter = STLEmitter(stream=stream, auto_timestamp=True)
        stmt = emitter.emit("[A]", "[B]")
        assert stmt.modifiers is not None
        assert stmt.modifiers.timestamp is not None

    def test_no_auto_timestamp(self):
        stream = StringIO()
        emitter = STLEmitter(stream=stream, auto_timestamp=False)
        stmt = emitter.emit("[A]", "[B]")
        assert stmt.modifiers is None

    def test_preserve_existing_timestamp(self):
        stream = StringIO()
        emitter = STLEmitter(stream=stream, auto_timestamp=True)
        stmt = emitter.emit("[A]", "[B]", timestamp="2025-01-01T00:00:00Z")
        assert stmt.modifiers.timestamp == "2025-01-01T00:00:00Z"

    def test_namespace_prefix(self):
        stream = StringIO()
        emitter = STLEmitter(stream=stream, namespace="Events")
        stmt = emitter.emit("[Start]", "[Running]")
        assert stmt.source.namespace == "Events"
        assert stmt.target.namespace == "Events"

    def test_no_double_namespace(self):
        stream = StringIO()
        emitter = STLEmitter(stream=stream, namespace="Events")
        stmt = emitter.emit("[Events:Start]", "[Running]")
        assert stmt.source.namespace == "Events"
        assert stmt.source.name == "Start"

    def test_auto_validate_valid(self):
        stream = StringIO()
        emitter = STLEmitter(stream=stream, auto_validate=True, auto_timestamp=False)
        stmt = emitter.emit("[A]", "[B]", confidence=0.9)
        assert stmt is not None

    def test_emit_statement(self):
        stream = StringIO()
        emitter = STLEmitter(stream=stream, auto_timestamp=False)
        pre_built = stl("[X]", "[Y]").mod(confidence=0.8).build()
        result = emitter.emit_statement(pre_built)
        assert result is pre_built
        output = stream.getvalue()
        assert "[X]" in output

    def test_source_modifier_no_collision(self):
        """Issue 2: source modifier must not collide with positional param."""
        stream = StringIO()
        emitter = STLEmitter(stream=stream, auto_timestamp=False)
        stmt = emitter.emit("[Study_X]", "[Finding_Y]",
                            source="doi:10.1234/study", confidence=0.82)
        assert stmt.modifiers.source == "doi:10.1234/study"
        assert stmt.modifiers.confidence == 0.82
        output = stream.getvalue()
        assert 'source="doi:10.1234/study"' in output


class TestCommentAPI:
    """Tests for comment() and section() methods (Issue 3)."""

    def test_comment_writes_to_stream(self):
        stream = StringIO()
        emitter = STLEmitter(stream=stream, auto_timestamp=False)
        emitter.comment("Module Details")
        output = stream.getvalue()
        assert output == "# Module Details\n"

    def test_section_writes_to_stream(self):
        stream = StringIO()
        emitter = STLEmitter(stream=stream, auto_timestamp=False)
        emitter.section("Dependencies")
        output = stream.getvalue()
        assert output == "\n# Dependencies\n"

    def test_comment_writes_to_file(self, tmp_path):
        path = str(tmp_path / "test.stl")
        with STLEmitter(log_path=path, auto_timestamp=False) as emitter:
            emitter.comment("Header")
            emitter.emit("[A]", "[B]")
        with open(path, "r") as f:
            content = f.read()
        assert "# Header\n" in content
        assert "[A]" in content

    def test_mixed_comments_and_statements(self):
        stream = StringIO()
        emitter = STLEmitter(stream=stream, auto_timestamp=False)
        emitter.section("Section 1")
        emitter.emit("[A]", "[B]", confidence=0.9)
        emitter.comment("End of section")
        output = stream.getvalue()
        lines = output.split("\n")
        assert lines[0] == ""  # section starts with blank line
        assert lines[1] == "# Section 1"
        assert "[A]" in lines[2]
        assert lines[3] == "# End of section"


class TestContextManager:
    """Tests for context manager protocol."""

    def test_context_manager(self, tmp_path):
        path = str(tmp_path / "test.stl")
        with STLEmitter(log_path=path) as emitter:
            emitter.emit("[A]", "[B]")
        # File should be closed after context
        assert emitter._file_handle.closed

    def test_close_explicit(self, tmp_path):
        path = str(tmp_path / "test.stl")
        emitter = STLEmitter(log_path=path)
        emitter.emit("[A]", "[B]")
        emitter.close()
        assert emitter._file_handle.closed


class TestThreadSafety:
    """Tests for thread-safe writing."""

    def test_concurrent_writes(self, tmp_path):
        path = str(tmp_path / "test.stl")
        num_threads = 10
        writes_per_thread = 10

        with STLEmitter(log_path=path, auto_timestamp=False) as emitter:
            def write_stmts(thread_id):
                for j in range(writes_per_thread):
                    emitter.emit(f"[T{thread_id}]", f"[S{j}]")

            threads = [
                threading.Thread(target=write_stmts, args=(i,))
                for i in range(num_threads)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

        # Verify all lines written
        with open(path, "r") as f:
            lines = [l for l in f.readlines() if l.strip()]
        assert len(lines) == num_threads * writes_per_thread

    def test_parseable_output(self, tmp_path):
        """Verify emitted file is parseable by the STL parser."""
        from stl_parser.parser import parse_file

        path = str(tmp_path / "test.stl")
        with STLEmitter(log_path=path, auto_timestamp=False) as emitter:
            emitter.emit("[A]", "[B]", confidence=0.9)
            emitter.emit("[C]", "[D]", rule="causal")

        result = parse_file(path)
        assert result.is_valid
        assert len(result.statements) == 2
