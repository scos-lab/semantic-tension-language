# How-To: Use STL for Event Logging

Use the STLEmitter to write structured event logs in STL format. Events are timestamped, typed, and queryable — a step up from plain text logs.

**Prerequisites:** Familiarity with [STL syntax](../reference/stl-syntax.md).

---

## Why STL for Logging?

- **Structured:** Every event is a typed relation with metadata
- **Queryable:** Filter, search, and aggregate events with the query API
- **Analyzable:** Build graphs from event streams to find causal patterns
- **Timestamped:** Auto-timestamps on every emitted statement

---

## Basic Event Logging

```python
from stl_parser.emitter import STLEmitter

with STLEmitter(log_path="events.stl") as emitter:
    emitter.emit("[User_Login]", "[Session_Start]",
                 confidence=1.0, domain="auth")

    emitter.emit("[API_Request]", "[Response_200]",
                 confidence=1.0, domain="api",
                 duration="PT0.250S")

    emitter.emit("[Error_Timeout]", "[Service_Unavailable]",
                 confidence=1.0, domain="api",
                 emotion="Neutral", intensity=0.8)
```

Output in `events.stl`:

```stl
[User_Login] -> [Session_Start] ::mod(confidence=1.0, domain="auth", timestamp="2026-02-12T10:00:00Z")
[API_Request] -> [Response_200] ::mod(confidence=1.0, domain="api", duration="PT0.250S", timestamp="2026-02-12T10:00:01Z")
[Error_Timeout] -> [Service_Unavailable] ::mod(confidence=1.0, domain="api", emotion="Neutral", intensity=0.8, timestamp="2026-02-12T10:00:02Z")
```

---

## Namespaced Logging

Use a namespace to prefix all anchors in a specific log:

```python
with STLEmitter(log_path="auth.stl", namespace="Auth") as emitter:
    emitter.emit("[Login]", "[Success]", confidence=1.0)
    # Writes: [Auth:Login] -> [Auth:Success] ::mod(...)

    emitter.emit("[Login]", "[Failure]",
                 confidence=1.0, cause="Invalid_Password")
    # Writes: [Auth:Login] -> [Auth:Failure] ::mod(...)
```

---

## Sections and Comments

Organize logs into logical sections:

```python
with STLEmitter(log_path="pipeline.stl") as emitter:
    emitter.section("Data Ingestion")
    emitter.comment("Processing batch 2026-02-12")

    emitter.emit("[Batch_001]", "[Ingested]",
                 confidence=1.0, domain="etl")

    emitter.section("Transformation")
    emitter.emit("[Batch_001]", "[Transformed]",
                 confidence=1.0, domain="etl")

    emitter.section("Load")
    emitter.emit("[Batch_001]", "[Loaded]",
                 confidence=1.0, domain="etl")
```

Output:

```stl
# === Data Ingestion ===
# Processing batch 2026-02-12
[Batch_001] -> [Ingested] ::mod(confidence=1.0, domain="etl", timestamp="...")
# === Transformation ===
[Batch_001] -> [Transformed] ::mod(confidence=1.0, domain="etl", timestamp="...")
# === Load ===
[Batch_001] -> [Loaded] ::mod(confidence=1.0, domain="etl", timestamp="...")
```

---

## Logging Pre-Built Statements

Emit statements built with the builder API:

```python
from stl_parser.builder import stl
from stl_parser.emitter import STLEmitter

stmt = stl("[Deploy_v2]", "[Production]").mod(
    confidence=1.0,
    domain="ops",
    author="CI_Pipeline",
    version="v2.3.1"
).build()

with STLEmitter(log_path="deploys.stl") as emitter:
    emitter.emit_statement(stmt)
```

---

## Streaming to stdout

Write to standard output instead of a file:

```python
import sys
from stl_parser.emitter import STLEmitter

emitter = STLEmitter(stream=sys.stdout)
emitter.emit("[Heartbeat]", "[Alive]", confidence=1.0)
emitter.close()
```

Or use a StringIO buffer:

```python
from io import StringIO
from stl_parser.emitter import STLEmitter

buffer = StringIO()
emitter = STLEmitter(stream=buffer)
emitter.emit("[Test]", "[Passed]", confidence=1.0)
emitter.close()

print(buffer.getvalue())
```

---

## Querying Event Logs

Read back and query logged events:

```python
from stl_parser import parse_file
from stl_parser.query import find, find_all, filter_statements

# Load the log
events = parse_file("events.stl")

# Find all error events
errors = find_all(events, source="Error_Timeout")

# Filter high-confidence events
high_conf = filter_statements(events, confidence__gte=0.9)
print(f"{len(high_conf.statements)} high-confidence events")

# Find events in a specific domain
api_events = filter_statements(events, domain="api")
```

---

## Analyzing Event Patterns

Build a graph from event logs to find patterns:

```python
from stl_parser import parse_file, STLGraph, STLAnalyzer

events = parse_file("events.stl")
graph = STLGraph(events)

# Find causal chains
paths = graph.find_paths("Error_Timeout", "Service_Unavailable")

# Most connected event types
centrality = graph.get_node_centrality()
for node, score in sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f"  {node}: {score:.3f}")

# Detect feedback loops
cycles = graph.find_cycles()
```

---

## Disabling Auto-Timestamp

If you manage timestamps yourself:

```python
emitter = STLEmitter(log_path="events.stl", auto_timestamp=False)
emitter.emit("[Event]", "[State]",
             confidence=1.0,
             timestamp="2026-02-12T10:00:00Z")  # Manual timestamp
emitter.close()
```

---

## Thread Safety

The STLEmitter uses `threading.Lock` internally, so it's safe to use from multiple threads:

```python
import threading
from stl_parser.emitter import STLEmitter

emitter = STLEmitter(log_path="concurrent.stl")

def worker(name):
    for i in range(10):
        emitter.emit(f"[Worker_{name}]", f"[Task_{i}]", confidence=1.0)

threads = [threading.Thread(target=worker, args=(f"T{i}",)) for i in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
emitter.close()
```

---

## See Also

- [Tutorial: Streaming I/O](../tutorials/06-streaming-io.md) — STLEmitter and STLReader tutorial
- [API: emitter](../reference/api/emitter.md) — Full API reference
- [How-To: Knowledge Graph Pipeline](knowledge-graph-pipeline.md) — Analyze event graphs
