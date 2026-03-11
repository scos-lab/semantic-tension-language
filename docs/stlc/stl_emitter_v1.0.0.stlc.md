# STL Emitter STLC Specification

> **Version:** 1.0.0
> **Type:** Base
> **Target:** `stl_parser/emitter.py`
> **Author:** Syn-claude
> **Date:** 2026-02-11
> **Status:** Draft

---

## 1. Scope Definition

[Emitter_Module] -> [Scope] ::mod(
  intent="Structured event emitter for logging STL statements to files/streams",
  boundaries="Build statements via builder, inject metadata, write to output targets",
  confidence=0.90
)

**Included:**
- `STLEmitter` class — main emitter with log_path, namespace, stream configuration
- `emit(source, target, **modifiers)` — build and write single STL statement
- `emit_statement(statement)` — write pre-built Statement
- Automatic timestamp injection
- Namespace prefixing for source/target anchors
- Context manager protocol (`__enter__`/`__exit__`)
- Thread-safe file writing
- Stream output (stdout, stderr, custom stream)

**Excluded:**
- Statement construction logic (delegated to builder.py)
- Schema validation (can be composed externally)
- Log rotation or file management
- Network/remote output targets

---

## 2. Architecture Overview

[STLEmitter] -> [Builder_Module] ::mod(
  rule="causal",
  intent="Emitter uses builder.stl() to construct statements",
  confidence=0.95
)

[STLEmitter] -> [Serializer_Module] ::mod(
  rule="causal",
  intent="Emitter uses str(statement) for serialization to STL text",
  confidence=0.95
)

[STLEmitter] -> [Output_Target] ::mod(
  rule="causal",
  intent="Emitter writes serialized STL to file and/or stream",
  confidence=0.95
)

---

## 3. Data Models

[EmitterConfig] -> [Model_Definition] ::mod(
  rule="definitional",
  type="model",
  schema="Internal config: log_path (Optional[str]), namespace (Optional[str]), stream (Optional[TextIO]), auto_timestamp (bool=True), auto_validate (bool=False)",
  confidence=0.90
)

---

## 4. Computational Flow

### 4.1 Constructor: STLEmitter(log_path=None, namespace=None, stream=None, auto_timestamp=True, auto_validate=False)

[Entry_Init] -> [Input_log_path] ::mod(
  rule="definitional",
  type="input",
  format="String",
  schema="Optional[str] — file path for STL log output",
  confidence=1.0
)

[Entry_Init] -> [Input_namespace] ::mod(
  rule="definitional",
  type="input",
  format="String",
  schema="Optional[str] — default namespace prefix for anchors",
  confidence=1.0
)

[Entry_Init] -> [Input_stream] ::mod(
  rule="definitional",
  type="input",
  format="Object",
  schema="Optional[TextIO] — stream object (e.g., sys.stdout, StringIO)",
  confidence=1.0
)

[Entry_Init] -> [Input_auto_timestamp] ::mod(
  rule="definitional",
  type="input",
  format="Boolean",
  schema="bool — whether to auto-inject timestamp modifier (default True)",
  confidence=1.0
)

[Entry_Init] -> [Input_auto_validate] ::mod(
  rule="definitional",
  type="input",
  format="Boolean",
  schema="bool — whether to validate statements before emitting (default False)",
  confidence=1.0
)

[Input_log_path] -> [Branch_Has_Output] ::mod(
  rule="logical",
  type="branching",
  condition="log_path is not None or stream is not None",
  on_success="Store_Config",
  on_fail="Error_No_Output",
  confidence=1.0
)

[Branch_Has_Output] -> [Store_Config] ::mod(
  rule="causal",
  type="transformation",
  intent="Store configuration in instance attributes",
  output="self._log_path, self._namespace, self._stream, self._auto_timestamp, self._auto_validate, self._lock (threading.Lock)",
  confidence=1.0
)

[Store_Config] -> [Branch_Has_Log_Path] ::mod(
  rule="logical",
  type="branching",
  condition="log_path is not None",
  on_success="Open_File_Handle",
  on_fail="Exit_Init",
  confidence=1.0
)

[Branch_Has_Log_Path] -> [Open_File_Handle] ::mod(
  rule="causal",
  type="mutation",
  intent="Open file in append mode for writing",
  input="log_path",
  output="self._file_handle",
  algorithm="open(log_path, 'a', encoding='utf-8')",
  side_effect="File opened for appending",
  confidence=0.95
)

[Open_File_Handle] -> [Exit_Init] ::mod(
  rule="definitional",
  confidence=1.0
)

[Branch_Has_Log_Path] -> [Exit_Init] ::mod(
  rule="definitional",
  confidence=1.0
)

[Branch_Has_Output] -> [Error_No_Output] ::mod(
  rule="causal",
  type="output",
  error_type="STLEmitterError",
  error_message="At least one of log_path or stream must be provided",
  confidence=1.0
)

[Error_No_Output] -> [Exit_Init_Error] ::mod(
  rule="definitional",
  confidence=1.0
)

### 4.2 Method: emit(source, target, **modifiers) -> Statement

[Entry_emit] -> [Input_Source] ::mod(
  rule="definitional",
  type="input",
  format="String",
  schema="Anchor string: '[X]' | 'Ns:X' | 'X'",
  confidence=1.0
)

[Entry_emit] -> [Input_Target] ::mod(
  rule="definitional",
  type="input",
  format="String",
  schema="Anchor string: same formats as source",
  confidence=1.0
)

[Entry_emit] -> [Input_Modifiers] ::mod(
  rule="definitional",
  type="input",
  format="Object",
  schema="Dict[str, Any] — modifier key-value pairs",
  confidence=1.0
)

[Input_Source] -> [Apply_Namespace] ::mod(
  rule="causal",
  type="transformation",
  intent="Prefix namespace to source and target if namespace configured and not already present",
  input="{source, target, self._namespace}",
  output="{namespaced_source, namespaced_target}",
  algorithm="If self._namespace and ':' not in anchor_str: prepend 'namespace:' to anchor name",
  confidence=0.90
)

[Input_Target] -> [Apply_Namespace] ::mod(
  rule="causal",
  confidence=0.90
)

[Apply_Namespace] -> [Branch_Auto_Timestamp] ::mod(
  rule="logical",
  type="branching",
  condition="self._auto_timestamp is True and 'timestamp' not in modifiers",
  on_success="Inject_Timestamp",
  on_fail="Build_Statement",
  confidence=1.0
)

[Branch_Auto_Timestamp] -> [Inject_Timestamp] ::mod(
  rule="causal",
  type="transformation",
  intent="Add current ISO 8601 timestamp to modifiers",
  input="modifiers",
  output="modifiers with timestamp=datetime.utcnow().isoformat() + 'Z'",
  algorithm="modifiers['timestamp'] = datetime.utcnow().isoformat() + 'Z'",
  confidence=0.95
)

[Inject_Timestamp] -> [Build_Statement] ::mod(
  rule="causal",
  confidence=1.0
)

[Branch_Auto_Timestamp] -> [Build_Statement] ::mod(
  rule="causal",
  confidence=1.0
)

[Build_Statement] -> [Call_Builder] ::mod(
  rule="causal",
  type="transformation",
  intent="Use builder.stl() to construct Statement",
  input="{namespaced_source, namespaced_target, modifiers}",
  output="Statement",
  algorithm="builder.stl(namespaced_source, namespaced_target).mod(**modifiers).build()",
  confidence=0.95
)

[Call_Builder] -> [Branch_Auto_Validate] ::mod(
  rule="logical",
  type="branching",
  condition="self._auto_validate is True",
  on_success="Validate_Statement",
  on_fail="Serialize_Statement",
  confidence=1.0
)

[Branch_Auto_Validate] -> [Validate_Statement] ::mod(
  rule="causal",
  type="validation",
  intent="Validate statement using validator.validate_statement()",
  constraint="No validation errors",
  on_success="Serialize_Statement",
  on_fail="Error_Validation_Failed",
  confidence=0.90
)

[Validate_Statement] -> [Serialize_Statement] ::mod(
  rule="causal",
  confidence=1.0
)

[Branch_Auto_Validate] -> [Serialize_Statement] ::mod(
  rule="causal",
  confidence=1.0
)

[Serialize_Statement] -> [Serialize_To_STL] ::mod(
  rule="causal",
  type="transformation",
  intent="Convert Statement to STL text line",
  input="statement",
  output="stl_line: str",
  algorithm="str(statement) + '\\n'",
  confidence=0.95
)

[Serialize_To_STL] -> [Write_Output] ::mod(
  rule="causal",
  type="mutation",
  intent="Write STL line to configured output targets",
  input="stl_line",
  side_effect="Line written to file and/or stream",
  confidence=0.95
)

[Write_Output] -> [Write_To_File] ::mod(
  rule="causal",
  type="mutation",
  intent="Write to file if file handle exists",
  algorithm="With self._lock: self._file_handle.write(stl_line); self._file_handle.flush()",
  side_effect="STL line appended to log file",
  confidence=0.95
)

[Write_Output] -> [Write_To_Stream] ::mod(
  rule="causal",
  type="mutation",
  intent="Write to stream if stream configured",
  algorithm="self._stream.write(stl_line); self._stream.flush()",
  side_effect="STL line written to stream",
  confidence=0.95
)

[Write_To_File] -> [Return_Statement] ::mod(
  rule="causal",
  confidence=1.0
)

[Write_To_Stream] -> [Return_Statement] ::mod(
  rule="causal",
  confidence=1.0
)

[Return_Statement] -> [Output_Statement] ::mod(
  rule="definitional",
  type="output",
  format="Object",
  schema="models.Statement",
  intent="Return the emitted Statement for further use",
  confidence=1.0
)

[Output_Statement] -> [Exit_emit] ::mod(
  rule="definitional",
  confidence=1.0
)

[Validate_Statement] -> [Error_Validation_Failed] ::mod(
  rule="causal",
  type="output",
  error_type="STLEmitterError",
  error_message="Emitter validation failed: {details}",
  confidence=0.90
)

[Error_Validation_Failed] -> [Exit_emit_Error] ::mod(
  rule="definitional",
  confidence=1.0
)

### 4.3 Method: emit_statement(statement) -> Statement

[Entry_emit_statement] -> [Input_Statement] ::mod(
  rule="definitional",
  type="input",
  format="Object",
  schema="models.Statement",
  confidence=1.0
)

[Input_Statement] -> [Serialize_To_STL] ::mod(
  rule="causal",
  type="transformation",
  intent="Convert pre-built Statement to STL text line",
  input="statement",
  output="stl_line: str",
  algorithm="str(statement) + '\\n'",
  confidence=0.95
)

[Serialize_To_STL] -> [Write_Output] ::mod(
  rule="causal",
  type="mutation",
  intent="Write to configured outputs (same as emit())",
  side_effect="Line written to file and/or stream",
  confidence=0.95
)

[Write_Output] -> [Return_Statement] ::mod(
  rule="definitional",
  type="output",
  format="Object",
  schema="models.Statement",
  confidence=1.0
)

[Return_Statement] -> [Exit_emit_statement] ::mod(
  rule="definitional",
  confidence=1.0
)

### 4.4 Context Manager: __enter__ / __exit__

[Entry_enter] -> [Return_Self] ::mod(
  rule="definitional",
  type="output",
  format="Object",
  schema="STLEmitter (self)",
  intent="Enable 'with STLEmitter(...) as emitter:' pattern",
  confidence=1.0
)

[Return_Self] -> [Exit_enter] ::mod(
  rule="definitional",
  confidence=1.0
)

[Entry_exit] -> [Close_File] ::mod(
  rule="causal",
  type="mutation",
  intent="Close file handle if open",
  algorithm="if self._file_handle: self._file_handle.close()",
  side_effect="File handle closed, data flushed to disk",
  confidence=0.95
)

[Close_File] -> [Exit_exit] ::mod(
  rule="definitional",
  confidence=1.0
)

### 4.5 Method: close()

[Entry_close] -> [Close_Resources] ::mod(
  rule="causal",
  type="mutation",
  intent="Explicitly close file handle (for non-context-manager usage)",
  algorithm="if self._file_handle and not self._file_handle.closed: self._file_handle.close()",
  side_effect="File handle closed",
  confidence=1.0
)

[Close_Resources] -> [Exit_close] ::mod(
  rule="definitional",
  confidence=1.0
)

---

## 5. Dependencies (Reuse, Not Duplicate)

| Dependency | Module | Purpose |
|------------|--------|---------|
| `stl()` | `builder.py` | Statement construction factory |
| `StatementBuilder` | `builder.py` | Fluent builder (used internally by stl()) |
| `Statement` | `models.py` | Statement data model |
| `validate_statement()` | `validator.py` | Optional statement validation |
| `STLEmitterError` | `errors.py` | Emitter-specific exceptions |
| `ErrorCode.E800-E801` | `errors.py` | Emitter error codes |
| `threading.Lock` | stdlib | Thread-safe file writes |
| `datetime` | stdlib | Timestamp generation |

---

## 6. Verification Criteria

- [ ] `STLEmitter(log_path="test.stl")` creates emitter with file output
- [ ] `STLEmitter(stream=sys.stdout)` creates emitter with stream output
- [ ] `STLEmitter()` raises STLEmitterError (no output target)
- [ ] `emitter.emit("[A]", "[B]", confidence=0.9)` writes valid STL line to file
- [ ] Auto-timestamp: emitted statement has `timestamp` modifier when `auto_timestamp=True`
- [ ] No auto-timestamp: `timestamp` not injected when `auto_timestamp=False`
- [ ] Existing timestamp preserved: if `timestamp` passed in modifiers, not overwritten
- [ ] Namespace prefixing: `STLEmitter(namespace="Events")` prefixes anchors → `[Events:A]`
- [ ] No double-prefix: already-namespaced `"Events:A"` not prefixed again
- [ ] `emit_statement(stmt)` writes pre-built statement without modification
- [ ] Context manager: `with STLEmitter(...) as e:` properly opens and closes
- [ ] Thread safety: concurrent `emit()` calls don't interleave output
- [ ] File content is valid STL parseable by `parser.parse_file()`
- [ ] `auto_validate=True` rejects invalid statements with STLEmitterError
