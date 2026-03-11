# API: emitter

Thread-safe streaming writer for STL statements.

**Module:** `stl_parser.emitter`
**Import:** `from stl_parser import STLEmitter`

---

## STLEmitter

```python
STLEmitter(
    log_path: Optional[str] = None,
    namespace: Optional[str] = None,
    stream: Optional[TextIO] = None,
    auto_timestamp: bool = True,
    auto_validate: bool = False
)
```

Context manager for writing STL statements to files or streams.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `log_path` | `str` | `None` | File path for output (append mode) |
| `namespace` | `str` | `None` | Default namespace prefix for anchors |
| `stream` | `TextIO` | `None` | Stream object (e.g., `sys.stdout`) |
| `auto_timestamp` | `bool` | `True` | Inject `timestamp` modifier on each statement |
| `auto_validate` | `bool` | `False` | Validate statements before emitting |

At least one of `log_path` or `stream` must be provided.

**Raises:** `STLEmitterError` (E800-E801)

---

### .emit()

```python
STLEmitter.emit(
    source_anchor: str,
    target_anchor: str,
    **modifiers: Any
) -> Statement
```

Build and emit an STL statement. Applies namespace prefix and optionally injects timestamp.

**Returns:** The emitted `Statement`.

**Example:**

```python
with STLEmitter("events.stl") as emitter:
    emitter.emit("[Sensor_A]", "[Reading]", confidence=0.95, rule="empirical")
```

---

### .emit_statement()

```python
STLEmitter.emit_statement(statement: Statement) -> Statement
```

Emit a pre-built `Statement` without modification.

---

### .comment()

```python
STLEmitter.comment(text: str) -> None
```

Write a comment line (`# text`) to outputs.

---

### .section()

```python
STLEmitter.section(name: str) -> None
```

Write a section separator comment (`\n# name\n`).

---

### Context Manager

```python
with STLEmitter("output.stl", namespace="Sys") as emitter:
    emitter.section("Events")
    emitter.emit("[Login]", "[Session]", confidence=1.0)
    emitter.comment("End of events")
```

Thread-safe: uses `threading.Lock` internally for concurrent emit calls.
