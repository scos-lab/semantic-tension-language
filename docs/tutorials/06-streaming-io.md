# Tutorial 6: Streaming I/O

Learn how to write and read STL statements as streams — useful for logging, real-time data, and large files.

**What you'll learn:**
- Write statements with `STLEmitter`
- Stream-read with `stream_parse()` and `STLReader`
- Use auto-timestamp and namespace features
- Filter while streaming
- Use tail mode for real-time monitoring

**Prerequisites:** [Tutorial 5: Querying](05-querying.md)

---

## Step 1: Write with STLEmitter

`STLEmitter` is a context manager for writing STL statements to files:

```python
from stl_parser import STLEmitter

with STLEmitter("events.stl") as emitter:
    emitter.emit("[Sensor_A]", "[Reading_Temperature]",
                 confidence=0.95, rule="empirical", domain="IoT")
    emitter.emit("[Sensor_B]", "[Reading_Humidity]",
                 confidence=0.90, rule="empirical", domain="IoT")
```

This creates `events.stl` with one statement per line, each with an auto-generated timestamp.

## Step 2: Auto-Timestamp

By default, `STLEmitter` injects a `timestamp` modifier on every statement:

```python
with STLEmitter("log.stl") as emitter:
    emitter.emit("[User_Login]", "[Session_Start]", confidence=1.0)
    # Writes: [User_Login] -> [Session_Start] ::mod(confidence=1.0, timestamp="2026-02-12T10:30:00Z")
```

To disable:

```python
with STLEmitter("log.stl", auto_timestamp=False) as emitter:
    emitter.emit("[A]", "[B]", confidence=0.9)
    # No timestamp added
```

## Step 3: Namespace Prefix

Set a default namespace that applies to all emitted anchors:

```python
with STLEmitter("medical.stl", namespace="Med") as emitter:
    emitter.emit("[Symptom_Fever]", "[Condition_Infection]",
                 rule="causal", confidence=0.80)
    # Writes: [Med:Symptom_Fever] -> [Med:Condition_Infection] ::mod(...)
```

## Step 4: Write Comments and Sections

```python
with STLEmitter("knowledge.stl") as emitter:
    emitter.section("Physics")
    emitter.emit("[Gravity]", "[Acceleration]", rule="causal", confidence=0.99)
    emitter.emit("[Mass]", "[Weight]", rule="logical", confidence=0.98)

    emitter.section("Chemistry")
    emitter.comment("Basic element relationships")
    emitter.emit("[Water]", "[H2O]", rule="definitional", confidence=0.99)
```

Output:

```stl
# Physics

[Gravity] -> [Acceleration] ::mod(confidence=0.99, rule="causal", timestamp="...")
[Mass] -> [Weight] ::mod(confidence=0.98, rule="logical", timestamp="...")

# Chemistry

# Basic element relationships
[Water] -> [H2O] ::mod(confidence=0.99, rule="definitional", timestamp="...")
```

## Step 5: Emit Pre-Built Statements

```python
from stl_parser import stl, STLEmitter

stmt = stl("[A]", "[B]").mod(confidence=0.9, rule="causal").build()

with STLEmitter("output.stl") as emitter:
    emitter.emit_statement(stmt)
```

## Step 6: Write to stdout

Use the `stream` parameter instead of `log_path`:

```python
import sys
from stl_parser import STLEmitter

with STLEmitter(stream=sys.stdout, auto_timestamp=False) as emitter:
    emitter.emit("[A]", "[B]", confidence=0.9)
    # Prints directly to terminal
```

## Step 7: Stream-Read with stream_parse()

`stream_parse()` is a generator that yields statements one at a time — memory-efficient for large files:

```python
from stl_parser import stream_parse

for stmt in stream_parse("events.stl"):
    print(f"{stmt.source.name} -> {stmt.target.name}")
```

### Filter While Streaming

Apply query filters during streaming:

```python
# Only yield high-confidence statements
for stmt in stream_parse("events.stl", where={"confidence__gte": 0.9}):
    print(f"  {stmt}")
```

### Error Handling

```python
# Skip unparseable lines (default)
for stmt in stream_parse("messy.stl", on_error="skip"):
    print(stmt)

# Raise on first error
try:
    for stmt in stream_parse("messy.stl", on_error="raise"):
        print(stmt)
except Exception as e:
    print(f"Error: {e}")
```

## Step 8: STLReader Context Manager

`STLReader` provides more control and statistics:

```python
from stl_parser import STLReader

with STLReader("events.stl") as reader:
    for stmt in reader:
        print(f"{stmt.source.name} -> {stmt.target.name}")

    # Access statistics
    stats = reader.stats
    print(f"\nLines processed: {stats.lines_processed}")
    print(f"Statements yielded: {stats.statements_yielded}")
    print(f"Errors skipped: {stats.errors_skipped}")
```

### Read All at Once

```python
with STLReader("events.stl", where={"rule": "causal"}) as reader:
    result = reader.read_all()
    print(f"Loaded {len(result.statements)} causal statements")
```

## Step 9: Tail Mode

`STLReader` supports tail mode for real-time monitoring — like `tail -f`:

```python
from stl_parser import STLReader

# Watch for new statements (polls every 0.5 seconds)
with STLReader("live_events.stl", tail=True, tail_interval=0.5) as reader:
    for stmt in reader:
        print(f"NEW: {stmt.source.name} -> {stmt.target.name}")
        # This loop blocks, waiting for new lines appended to the file
        # Press Ctrl+C to stop
```

Tail mode is useful for monitoring live STL event logs written by an `STLEmitter` in another process.

## Step 10: Stream from Various Sources

`stream_parse()` accepts multiple source types:

```python
from stl_parser import stream_parse
from io import StringIO

# From file path
for stmt in stream_parse("data.stl"):
    pass

# From StringIO
text = StringIO('[A] -> [B] ::mod(confidence=0.9)\n[C] -> [D] ::mod(confidence=0.8)')
for stmt in stream_parse(text):
    pass

# From list of strings
lines = [
    '[A] -> [B] ::mod(confidence=0.9)',
    '[C] -> [D] ::mod(confidence=0.8)',
]
for stmt in stream_parse(lines):
    pass
```

---

## Complete Example

```python
from stl_parser import STLEmitter, STLReader, stream_parse
import tempfile
import os

# Create a temp file
path = tempfile.mktemp(suffix=".stl")

# Write structured events
with STLEmitter(path, namespace="Sys", auto_timestamp=True) as emitter:
    emitter.section("System Events")
    emitter.emit("[Event_UserLogin]", "[Session_Active]",
                 confidence=1.0, rule="causal")
    emitter.emit("[Event_APICall]", "[Response_Success]",
                 confidence=0.95, rule="empirical", domain="api")
    emitter.emit("[Event_Error]", "[Alert_Triggered]",
                 confidence=0.80, rule="causal", domain="monitoring")

# Stream-read with filter
print("High-confidence events:")
for stmt in stream_parse(path, where={"confidence__gte": 0.9}):
    print(f"  {stmt.source.name} -> {stmt.target.name}")

# Read with statistics
print("\nFull stats:")
with STLReader(path) as reader:
    stmts = list(reader)
    stats = reader.stats
    print(f"  Statements: {stats.statements_yielded}")
    print(f"  Lines processed: {stats.lines_processed}")

os.unlink(path)
```

---

**Next:** [Tutorial 7: Diff & Patch](07-diff-patch.md)
