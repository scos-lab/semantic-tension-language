# -*- coding: utf-8 -*-
"""
STL Reader — Streaming, memory-efficient reader for STL files and streams.

The read-side complement to :class:`STLEmitter` (write-side), completing
the streaming I/O loop.  Yields :class:`Statement` objects one at a time
via a Python generator — never materialises the full list in memory.

Example usage::

    from stl_parser.reader import stream_parse, STLReader

    # Generator-based streaming
    for stmt in stream_parse("events.stl"):
        print(stmt.source.name, stmt.modifiers.confidence)

    # With filtering
    for stmt in stream_parse("kb.stl", where={"confidence__gt": 0.8}):
        process(stmt)

    # Context manager with stats
    with STLReader("events.stl") as reader:
        for stmt in reader:
            handle(stmt)
        print(reader.stats)

    # Tail mode (watch for new content)
    with STLReader("agent.stl", tail=True) as reader:
        for stmt in reader:
            alert(stmt)
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, List, Literal, Optional, Tuple, Union, TextIO

from pydantic import BaseModel, Field

from .errors import ErrorCode, STLReaderError
from .query import _parse_kwargs, _matches, FieldCondition

# TYPE_CHECKING would create circular import; use lazy import for parse/models.


# ========================================
# DATA MODELS
# ========================================

class ReaderStats(BaseModel):
    """Running statistics for an STLReader session."""
    lines_processed: int = 0
    statements_yielded: int = 0
    errors_skipped: int = 0
    comments_seen: int = 0
    blank_lines: int = 0


# ========================================
# INTERNAL HELPERS
# ========================================

_MAX_CONTINUATION_LINES = 20


def _line_iter(
    source: Union[str, Path, TextIO, Iterable[str]],
) -> Generator[Tuple[int, str], None, None]:
    """Resolve source type and yield ``(line_number, line_text)`` pairs.

    Handles file paths, open file handles, StringIO, and plain iterables
    of strings.  Files are opened lazily and closed when the generator
    is exhausted or garbage-collected.
    """
    if isinstance(source, (str, Path)):
        path = Path(source)
        try:
            fh = open(path, "r", encoding="utf-8")
        except FileNotFoundError:
            raise STLReaderError(
                code=ErrorCode.E960_READER_SOURCE_ERROR,
                message=f"File not found: {path}",
            )
        except PermissionError:
            raise STLReaderError(
                code=ErrorCode.E960_READER_SOURCE_ERROR,
                message=f"Permission denied: {path}",
            )
        try:
            for lineno, line in enumerate(fh, 1):
                yield lineno, line.rstrip("\n").rstrip("\r")
        finally:
            fh.close()
    elif hasattr(source, "readline"):
        # TextIO / StringIO
        for lineno, line in enumerate(source, 1):
            text = line.rstrip("\n").rstrip("\r") if isinstance(line, str) else line
            yield lineno, text
    else:
        # Iterable[str]
        for lineno, line in enumerate(source, 1):
            yield lineno, line.rstrip("\n").rstrip("\r")


def _merge_continuation(
    line_iter: Generator[Tuple[int, str], None, None],
    stats: Optional[ReaderStats] = None,
) -> Generator[Tuple[int, str], None, None]:
    """Buffer multi-line statements (unclosed parentheses) and yield merged lines.

    Tracks parenthesis depth.  When depth > 0 at end of a line, buffers
    until depth returns to 0.  Safety limit: 20 continuation lines.
    """
    buffer: List[str] = []
    start_lineno = 0
    paren_depth = 0

    for lineno, line in line_iter:
        stripped = line.strip()

        if stats:
            stats.lines_processed += 1

        # Pass through blank lines and comments when not in continuation
        if not buffer:
            if not stripped:
                if stats:
                    stats.blank_lines += 1
                yield lineno, line
                continue
            if stripped.startswith("#"):
                if stats:
                    stats.comments_seen += 1
                yield lineno, line
                continue

        # In continuation: skip blanks/comments inside multi-line
        if buffer:
            if not stripped:
                continue
            if stripped.startswith("#"):
                if stats:
                    stats.comments_seen += 1
                continue

        # Track parentheses
        open_p = line.count("(")
        close_p = line.count(")")

        if not buffer:
            paren_depth = open_p - close_p
            if paren_depth > 0:
                # Start multi-line
                buffer.append(line)
                start_lineno = lineno
            else:
                yield lineno, line
        else:
            buffer.append(line)
            paren_depth += open_p - close_p

            if len(buffer) > _MAX_CONTINUATION_LINES:
                raise STLReaderError(
                    code=ErrorCode.E962_READER_CONTINUATION_OVERFLOW,
                    message=f"Multi-line statement starting at line {start_lineno} exceeds {_MAX_CONTINUATION_LINES}-line limit",
                    line_number=start_lineno,
                )

            if paren_depth <= 0:
                merged = " ".join(l.strip() for l in buffer)
                yield start_lineno, merged
                buffer = []
                paren_depth = 0

    # Flush any remaining buffer (unclosed parens — best-effort)
    if buffer:
        merged = " ".join(l.strip() for l in buffer)
        yield start_lineno, merged


def _parse_single_line(line: str, line_number: int) -> "Statement":
    """Parse one complete STL line into a Statement.

    Uses the main ``parse()`` function.  Raises :class:`STLReaderError`
    if the line cannot be parsed.
    """
    from .parser import parse

    result = parse(line)
    if result.statements:
        return result.statements[0]

    msg = f"Could not parse line {line_number}: {line!r}"
    if result.errors:
        msg = f"Parse error at line {line_number}: {result.errors[0].message}"
    raise STLReaderError(
        code=ErrorCode.E961_READER_PARSE_ERROR,
        message=msg,
        line_number=line_number,
    )


# ========================================
# PUBLIC API
# ========================================

def stream_parse(
    source: Union[str, Path, TextIO, Iterable[str]],
    *,
    where: Optional[Dict[str, Any]] = None,
    on_error: Literal["skip", "raise"] = "skip",
) -> Generator["Statement", None, None]:
    """Yield :class:`Statement` objects one at a time from *source*.

    Memory-efficient: reads and parses one line at a time — never loads
    the entire file into memory.

    Args:
        source: File path (str or Path), open file handle / StringIO,
            or any iterable of line strings.
        where: Optional Django-style filter criteria.  Uses the same
            operators as :func:`find` / :func:`filter_statements`
            (``__gt``, ``__gte``, ``__lt``, ``__lte``, ``__ne``,
            ``__contains``, ``__startswith``, ``__in``).
        on_error: ``"skip"`` (default) silently skips unparseable lines;
            ``"raise"`` raises :class:`STLReaderError` immediately.

    Yields:
        :class:`Statement` objects.

    Raises:
        STLReaderError: If *source* cannot be opened (E960), or if
            ``on_error="raise"`` and a line fails to parse (E961),
            or if a multi-line continuation exceeds the limit (E962).

    Example::

        for stmt in stream_parse("events.stl", where={"confidence__gt": 0.8}):
            print(stmt)
    """
    conditions = _parse_kwargs(**where) if where else []
    lines = _line_iter(source)
    merged = _merge_continuation(lines)

    for line_number, line in merged:
        stripped = line.strip()

        # Skip comments and blank lines
        if not stripped or stripped.startswith("#"):
            continue

        # Parse
        try:
            stmt = _parse_single_line(line, line_number)
        except STLReaderError:
            if on_error == "raise":
                raise
            continue

        # Filter
        if conditions and not _matches(stmt, conditions):
            continue

        yield stmt


class STLReader:
    """Context manager for streaming STL file reading with stats and tail mode.

    Args:
        source: File path or open stream.
        where: Optional Django-style filter criteria.
        on_error: ``"skip"`` or ``"raise"`` for unparseable lines.
        tail: If ``True``, watch the file for new content (like ``tail -f``).
            Only available for file paths.
        tail_interval: Seconds between polls in tail mode (default 0.5).

    Example::

        with STLReader("events.stl") as reader:
            for stmt in reader:
                process(stmt)
            print(reader.stats)

        # Tail mode
        with STLReader("agent.stl", tail=True, tail_interval=0.1) as reader:
            for stmt in reader:
                handle_realtime(stmt)
    """

    def __init__(
        self,
        source: Union[str, Path, TextIO],
        *,
        where: Optional[Dict[str, Any]] = None,
        on_error: Literal["skip", "raise"] = "skip",
        tail: bool = False,
        tail_interval: float = 0.5,
    ) -> None:
        self._source = source
        self._where = where
        self._on_error = on_error
        self._tail = tail
        self._tail_interval = tail_interval
        self._stats = ReaderStats()
        self._file_handle: Optional[TextIO] = None
        self._closed = False

        if tail and not isinstance(source, (str, Path)):
            raise ValueError("tail mode requires a file path (str or Path), not a stream")

    def __enter__(self) -> "STLReader":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def __iter__(self) -> Generator["Statement", None, None]:
        if self._tail:
            yield from self._iter_tail()
        else:
            yield from self._iter_normal()

    @property
    def stats(self) -> ReaderStats:
        """Current running statistics snapshot."""
        return self._stats.model_copy()

    def close(self) -> None:
        """Close any open file handles and stop iteration."""
        self._closed = True
        if self._file_handle is not None:
            self._file_handle.close()
            self._file_handle = None

    def read_all(self) -> "ParseResult":
        """Consume the generator and return a batch :class:`ParseResult`.

        Convenience method: streams with filtering, then materialises.
        """
        from .models import ParseResult as _ParseResult

        stmts = list(self)
        return _ParseResult(statements=stmts, is_valid=True)

    # ---- internal iteration ----

    def _iter_normal(self) -> Generator["Statement", None, None]:
        """Non-tail iteration with stats tracking."""
        conditions = _parse_kwargs(**self._where) if self._where else []
        lines = _line_iter(self._source)
        merged = _merge_continuation(lines, stats=self._stats)

        for line_number, line in merged:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            try:
                stmt = _parse_single_line(line, line_number)
            except STLReaderError:
                self._stats.errors_skipped += 1
                if self._on_error == "raise":
                    raise
                continue

            if conditions and not _matches(stmt, conditions):
                continue

            self._stats.statements_yielded += 1
            yield stmt

    def _iter_tail(self) -> Generator["Statement", None, None]:
        """Tail-mode iteration: polls file for new content."""
        path = Path(self._source) if isinstance(self._source, str) else self._source
        conditions = _parse_kwargs(**self._where) if self._where else []

        buffer: List[str] = []
        paren_depth = 0

        try:
            self._file_handle = open(path, "r", encoding="utf-8")
        except FileNotFoundError:
            raise STLReaderError(
                code=ErrorCode.E960_READER_SOURCE_ERROR,
                message=f"File not found: {path}",
            )

        try:
            while not self._closed:
                raw_line = self._file_handle.readline()
                if not raw_line:
                    # EOF — wait for more content
                    time.sleep(self._tail_interval)
                    continue

                line = raw_line.rstrip("\n").rstrip("\r")
                self._stats.lines_processed += 1
                stripped = line.strip()

                # Skip blanks and comments (outside of continuation)
                if not buffer:
                    if not stripped:
                        self._stats.blank_lines += 1
                        continue
                    if stripped.startswith("#"):
                        self._stats.comments_seen += 1
                        continue

                # Track parentheses for multi-line
                open_p = line.count("(")
                close_p = line.count(")")

                if not buffer:
                    paren_depth = open_p - close_p
                    if paren_depth > 0:
                        buffer.append(line)
                        continue
                    # Single-line statement
                    merged_line = line
                else:
                    buffer.append(line)
                    paren_depth += open_p - close_p
                    if paren_depth > 0:
                        if len(buffer) > _MAX_CONTINUATION_LINES:
                            self._stats.errors_skipped += 1
                            buffer = []
                            paren_depth = 0
                            if self._on_error == "raise":
                                raise STLReaderError(
                                    code=ErrorCode.E962_READER_CONTINUATION_OVERFLOW,
                                    message=f"Multi-line continuation exceeds {_MAX_CONTINUATION_LINES}-line limit",
                                )
                        continue
                    merged_line = " ".join(l.strip() for l in buffer)
                    buffer = []
                    paren_depth = 0

                # Parse
                try:
                    stmt = _parse_single_line(merged_line, self._stats.lines_processed)
                except STLReaderError:
                    self._stats.errors_skipped += 1
                    if self._on_error == "raise":
                        raise
                    continue

                # Filter
                if conditions and not _matches(stmt, conditions):
                    continue

                self._stats.statements_yielded += 1
                yield stmt
        finally:
            if self._file_handle is not None:
                self._file_handle.close()
                self._file_handle = None
