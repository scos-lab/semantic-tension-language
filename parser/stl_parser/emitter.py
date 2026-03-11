# -*- coding: utf-8 -*-
"""
STL Emitter — Structured Event Emitter

Log STL statements to files and streams with automatic timestamp injection,
namespace prefixing, and thread-safe writing.

Compiled from: docs/stlc/stl_emitter_v1.0.0.stlc.md

Usage:
    >>> from stl_parser.emitter import STLEmitter
    >>> with STLEmitter(log_path="events.stl") as emitter:
    ...     emitter.emit("[Event_Start]", "[State_Running]", confidence=0.95)
"""

import threading
from datetime import datetime, timezone
from typing import Any, Optional, TextIO

from .models import Statement
from .builder import stl
from .validator import validate_statement
from .errors import STLEmitterError, ErrorCode


class STLEmitter:
    """Structured event emitter that writes STL statements to files/streams.

    Supports:
    - File output (append mode)
    - Stream output (stdout, StringIO, etc.)
    - Automatic timestamp injection
    - Namespace prefixing for anchors
    - Optional statement validation
    - Thread-safe writing
    - Context manager protocol

    Args:
        log_path: File path for STL log output
        namespace: Default namespace prefix for anchors
        stream: Stream object for output (e.g., sys.stdout)
        auto_timestamp: Auto-inject timestamp modifier (default True)
        auto_validate: Validate statements before emitting (default False)

    Raises:
        STLEmitterError: If neither log_path nor stream is provided

    Example:
        >>> with STLEmitter(log_path="log.stl", namespace="Events") as e:
        ...     e.emit("[Start]", "[Running]", confidence=0.9)
    """

    def __init__(
        self,
        log_path: Optional[str] = None,
        namespace: Optional[str] = None,
        stream: Optional[TextIO] = None,
        auto_timestamp: bool = True,
        auto_validate: bool = False,
    ):
        if log_path is None and stream is None:
            raise STLEmitterError(
                code=ErrorCode.E800_EMITTER_ERROR,
                message="At least one of log_path or stream must be provided",
            )

        self._log_path = log_path
        self._namespace = namespace
        self._stream = stream
        self._auto_timestamp = auto_timestamp
        self._auto_validate = auto_validate
        self._lock = threading.Lock()
        self._file_handle: Optional[TextIO] = None

        if log_path is not None:
            self._file_handle = open(log_path, "a", encoding="utf-8")

    def emit(self, source_anchor: str, target_anchor: str, **modifiers: Any) -> Statement:
        """Build and emit an STL statement.

        Constructs a statement using the builder, optionally injects
        timestamp and namespace, then writes to configured outputs.

        Args:
            source_anchor: Source anchor string
            target_anchor: Target anchor string
            **modifiers: Modifier key-value pairs

        Returns:
            The emitted Statement

        Raises:
            STLEmitterError: If validation fails (when auto_validate=True)

        Example:
            >>> stmt = emitter.emit("[A]", "[B]", confidence=0.9, rule="causal")
        """
        # Apply namespace prefix
        source_anchor = self._apply_namespace(source_anchor)
        target_anchor = self._apply_namespace(target_anchor)

        # Inject timestamp if enabled and not already present
        if self._auto_timestamp and "timestamp" not in modifiers:
            modifiers["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Build statement
        builder = stl(source_anchor, target_anchor)
        if modifiers:
            builder = builder.mod(**modifiers)

        if not self._auto_validate:
            builder = builder.no_validate()

        try:
            stmt = builder.build()
        except Exception as e:
            raise STLEmitterError(
                code=ErrorCode.E800_EMITTER_ERROR,
                message=f"Failed to build statement: {e}",
            ) from e

        # Validate if requested
        if self._auto_validate:
            errors, _warnings = validate_statement(stmt)
            if errors:
                error_msgs = "; ".join(str(e) for e in errors)
                raise STLEmitterError(
                    code=ErrorCode.E800_EMITTER_ERROR,
                    message=f"Emitter validation failed: {error_msgs}",
                )

        # Write
        self._write(stmt)
        return stmt

    def emit_statement(self, statement: Statement) -> Statement:
        """Emit a pre-built Statement.

        Writes the statement to configured outputs without modification.

        Args:
            statement: Pre-built Statement to emit

        Returns:
            The emitted Statement
        """
        self._write(statement)
        return statement

    def comment(self, text: str) -> None:
        """Write a comment line to configured outputs.

        Args:
            text: Comment text (without the # prefix)
        """
        self._write_raw(f"# {text}\n")

    def section(self, name: str) -> None:
        """Write a section separator comment.

        Args:
            name: Section name
        """
        self._write_raw(f"\n# {name}\n")

    def _apply_namespace(self, anchor_str: str) -> str:
        """Apply namespace prefix if configured and not already present."""
        if self._namespace is None:
            return anchor_str

        # Strip brackets for checking
        stripped = anchor_str.strip()
        has_brackets = stripped.startswith("[") and stripped.endswith("]")
        inner = stripped[1:-1] if has_brackets else stripped

        # Already has namespace
        if ":" in inner:
            return anchor_str

        # Apply prefix
        namespaced = f"{self._namespace}:{inner}"
        if has_brackets:
            return f"[{namespaced}]"
        return namespaced

    def _write(self, stmt: Statement) -> None:
        """Write statement to configured outputs (thread-safe)."""
        stl_line = str(stmt) + "\n"

        with self._lock:
            if self._file_handle is not None and not self._file_handle.closed:
                try:
                    self._file_handle.write(stl_line)
                    self._file_handle.flush()
                except Exception as e:
                    raise STLEmitterError(
                        code=ErrorCode.E801_EMITTER_LOG_WRITE_FAILED,
                        message=f"Failed to write to log file: {e}",
                    ) from e

            if self._stream is not None:
                self._stream.write(stl_line)
                self._stream.flush()

    def _write_raw(self, text: str) -> None:
        """Write raw text to configured outputs (thread-safe)."""
        with self._lock:
            if self._file_handle is not None and not self._file_handle.closed:
                try:
                    self._file_handle.write(text)
                    self._file_handle.flush()
                except Exception as e:
                    raise STLEmitterError(
                        code=ErrorCode.E801_EMITTER_LOG_WRITE_FAILED,
                        message=f"Failed to write to log file: {e}",
                    ) from e

            if self._stream is not None:
                self._stream.write(text)
                self._stream.flush()

    def close(self) -> None:
        """Close file handle if open."""
        if self._file_handle is not None and not self._file_handle.closed:
            self._file_handle.close()

    def __enter__(self) -> "STLEmitter":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
