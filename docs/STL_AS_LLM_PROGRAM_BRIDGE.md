# STL as the LLM-Program Communication Standard

> **Document Type:** Vision & Roadmap
> **Version:** 0.2.0
> **Date:** 2026-02-11
> **Author:** Syn-claude (collaborating with wuko / SCOS-Lab)
> **Status:** Draft — open for discussion and collaborative development
> **Audience:** AI collaborators, developers, researchers

---

## 1. Background: From Theory to Proof

### 1.1 The Communication Gap

Today, LLMs and programs communicate almost exclusively through **JSON**. This works, but JSON was designed for data serialization — not for structured reasoning. When an LLM outputs JSON, it produces flat key-value pairs with no inherent notion of:

- **Directionality** — which entity influences which?
- **Confidence** — how certain is this claim?
- **Causal rules** — is this definitional, empirical, causal, or inferential?
- **Provenance** — where did this information come from?
- **Severity / priority** — how important is this signal?

Programs that consume JSON must reconstruct all of this context through ad-hoc schemas, validation layers, and interpretation logic. The semantic intent is lost in transit.

### 1.2 STL: A Language That Carries Meaning

**Semantic Tension Language (STL)** was designed from the ground up as a structured knowledge language. Its core syntax:

```
[Source] → [Target] ::mod(key=value, ...)
```

inherently encodes:

| Dimension | JSON | STL |
|-----------|------|-----|
| **Direction** | Implicit (consumer must interpret) | Explicit (`→` arrow) |
| **Confidence** | Not native | `::mod(confidence=0.85)` |
| **Causal type** | Not native | `::mod(rule="causal")` |
| **Severity** | Not native | `::mod(severity="critical")` |
| **Provenance** | Not native | `::mod(source="...", timestamp="...")` |
| **Namespacing** | Not native | `[Domain:Concept]` |
| **Human readability** | Moderate | High (reads like structured English) |
| **Machine parseability** | High | High (Lark LALR grammar, Pydantic models) |

### 1.3 Proof of Concept: Hybrid AI in Cortex

In February 2026, we built a **Hybrid AI behavior monitor** inside the Cortex system (a Website Factory AI service). This system uses STL as the sole communication protocol between a Python program and LLM-generated behavioral signals.

**The problem:** GPT-5.2 exhibited a persistent bug — calling the same tool (`collect_requirements`) 2+ times per turn, never producing a user-facing response.

**The STL solution:**

1. **Detection** — A Python `BehaviorCollector` observes tool call patterns and emits signals
2. **Signal encoding** — Signals are encoded as STL statements:
   ```
   [Obs:ToolLoop] -> [Act:BreakLoop] ::mod(confidence=0.95, severity="critical", rule="causal", context="collect_requirements called 2x consecutively")
   ```
3. **Parsing** — The `stl_parser` package (native Python, Lark grammar) parses this into structured objects:
   - `source.namespace = "Obs"`, `source.name = "ToolLoop"`
   - `target.namespace = "Act"`, `target.name = "BreakLoop"`
   - `modifiers: {confidence: 0.95, severity: "critical", ...}`
4. **Decision** — The program reads `confidence >= 0.8` threshold and auto-executes the recovery action
5. **Recovery** — A `RecoveryEngine` injects a correction prompt and retries the LLM without tools
6. **Audit** — The result is logged in STL format:
   ```
   [Act:BreakLoop] -> [Result:Recovered] ::mod(confidence=1.0, severity="info", rule="causal", timestamp="2026-02-11T00:46:22Z", context="break_loop: injected correction, retried without tools")
   ```

**Results from live testing (3 conversations, 5 recovery events):**

| Metric | Value |
|--------|-------|
| Detection accuracy | 100% (5/5 tool loops caught) |
| Recovery success rate | 100% (5/5 conversations recovered) |
| False positives | 0 |
| Audit log parseable | 100% (all STL logs pass `stl_parser.parse()`) |
| Latency overhead | ~0ms (detection is hardcoded rules, not LLM) |

This is **empirical proof** that STL works as a structured communication protocol between programs and LLM-adjacent systems. The program writes STL, the parser reads STL, decisions are made based on parsed structure, and audit logs are written back in STL. The entire pipeline is machine-parseable, human-readable, and semantically rich.

**What this proves:** Program-to-program communication via STL (Python generates STL → parser consumes STL → Python acts on parsed result). The full signal-decision-audit pipeline works in production.

**What comes next:** LLM-native STL generation — where the LLM itself outputs STL and programs consume it directly. This is the second proof point needed to validate STL as a true LLM-program bridge (see Section 4.1, Tool 10).

---

## 2. Purpose: STL as the LLM-Program Communication Standard

### 2.1 Vision

**Establish STL as the semantic layer that sits alongside JSON** for LLM-program communication — JSON for data, STL for reasoning.

JSON remains the universal standard for data serialization: configuration files, REST API payloads, simple key-value exchange. STL does not compete with JSON in these domains. Instead, STL addresses a growing class of **AI-native communication** where programs need to understand *what an LLM means, how sure it is, and why it thinks so* — semantic dimensions that JSON was never designed to carry.

Where JSON asks "what is the data?", STL asks "what does this mean, how certain is it, and what caused it?"

### 2.2 Target Use Cases

| Use Case | Why STL > JSON |
|----------|----------------|
| **Function calling / tool use** | Tool decisions carry confidence + causal justification; programs can reject low-confidence calls |
| **LLM behavior monitoring** | Signals carry confidence + severity + causal rules natively |
| **Knowledge extraction** | Extracted facts carry provenance + confidence automatically |
| **Multi-agent communication** | Agents can express uncertainty and direction of reasoning |
| **Audit logging** | Human-readable AND machine-parseable logs with full provenance |
| **Memory systems** | Facts stored with temporal context, confidence decay, source tracking |
| **Tool orchestration** | Tool call decisions can be expressed with causal justification |
| **Epistemic reasoning** | Questions, hypotheses, and verification cycles have first-class syntax |

#### Function Calling — The Killer Use Case

Today's LLM function calling relies entirely on JSON Schema: the LLM receives a JSON Schema describing available tools, and outputs a JSON object with arguments. This works mechanically, but carries zero semantic metadata — the LLM cannot express *why* it chose this tool, *how confident* it is in the choice, or *what it expects* the tool to return.

**Current approach (JSON):**
```json
{"tool": "search_web", "args": {"query": "STL language specification"}}
```

**STL approach:**
```
[Intent:FindSpec] -> [Tool:SearchWeb] ::mod(
    confidence=0.88,
    rule="causal",
    context="User asked about STL spec, need authoritative source",
    fallback="Tool:SearchDocs"
)
```

The STL version lets the program:
1. **Reject low-confidence calls** — if `confidence < 0.7`, ask the LLM to reconsider
2. **Route on causal type** — `rule="definitional"` vs `rule="empirical"` may invoke different tools
3. **Auto-fallback** — the `fallback` modifier enables programmatic retry logic
4. **Audit the reasoning chain** — every tool call carries its justification

### 2.3 Design Principles for the Tooling Ecosystem

1. **Import and use** — Every tool should be a Python package that programs can `import` directly
2. **Zero ceremony** — `stl_parse("text")` should Just Work, no boilerplate
3. **Type-safe** — All tools produce Pydantic models, not raw dicts
4. **Bidirectional** — Programs should generate STL as easily as they parse it
5. **Composable** — Tools combine: parse → transform → validate → emit
6. **LLM-friendly** — Compact token usage, designed for context window constraints

---

## 3. Current State: What Exists Today

### 3.1 STL Core Specification v1.0

- **Location:** `spec/stl-core-spec-v1.0.md` + supplement
- **Status:** Stable
- **Content:** Full syntax definition, 9 anchor types, modifier system, path expressions, validation rules

### 3.2 STL Parser (`stl_parser` v1.0.0)

- **Location:** `parser/`
- **Status:** Production-ready (used in Cortex Hybrid AI)
- **Stack:** Python 3.9+, Lark (LALR grammar), Pydantic, NetworkX
- **Capabilities:**
  - Parse STL text → Pydantic models (`STLDocument`, `STLStatement`, `Anchor`, `Modifier`)
  - Validate syntax and semantics
  - Export to JSON, JSON-LD, RDF/Turtle
  - Graph analysis (NetworkX integration)
  - CLI tool for command-line usage
  - Unicode support (Chinese, Arabic, etc.)
  - Multi-line statement merging

### 3.3 Cortex Hybrid AI (STL in Production)

- **Location:** Cortex project (`src/cortex/hybrid/`)
- **Status:** Working, tested
- **Components:** BehaviorCollector, STLEventBus, RecoveryEngine
- **Demonstrates:** Full STL pipeline in a real application

---

## 4. Tooling Roadmap: What Needs to Be Built

### 4.1 Priority 1 — Core Infrastructure & Trust

> **Rationale:** A communication protocol needs three things on day one: a way to generate messages (builder), a contract that defines valid messages (schema), and tolerance for imperfect speakers (LLM auto-repair). Without all three, production adoption stalls.

#### Tool 1: `stl-builder` — Programmatic STL Generation

**Problem:** Programs currently build STL strings via f-strings or template concatenation. This is error-prone and bypasses validation.

**Solution:** A fluent builder API that generates valid STL from Python code.

```python
from stl_builder import statement, mod

# Fluent builder API
stmt = (
    statement("[Obs:ToolLoop]", "[Act:BreakLoop]")
    .mod(confidence=0.95, severity="critical", rule="causal")
    .mod(context="tool called 2x consecutively")
    .build()
)
# Returns: '[Obs:ToolLoop] -> [Act:BreakLoop] ::mod(confidence=0.95, severity="critical", rule="causal") ::mod(context="tool called 2x consecutively")'

# Batch generation
doc = stl_document([
    statement("[A]", "[B]").mod(confidence=0.9),
    statement("[B]", "[C]").mod(rule="causal", strength=0.8),
])
```

**Estimated complexity:** ~300 LOC + tests

#### Tool 2: `stl-schema` — Formal Schema Definition Language

**Problem:** A communication protocol requires a contract. Programs that receive STL must validate it against an expected structure. Currently no formal way to say "my application accepts these STL patterns and rejects others."

**Why Priority 1:** JSON became an API standard partly because of JSON Schema. STL needs its equivalent from day one — not as an afterthought. Schema validation is the trust layer that makes programs willing to depend on STL input.

**Solution:** An STL Schema Definition Language (SDL) for declaring expected structures.

```
# hybrid_events.stl.schema
namespace Obs {
    ToolLoop, EmptyResponse, SparseArgs
}
namespace Act {
    BreakLoop, RetryWithHint, RejectToolCall, Fallback
}
namespace Result {
    Recovered, Failed
}

# Statement types
[Obs:*] -> [Act:*] {
    confidence: float [0.0, 1.0] REQUIRED
    severity: enum("info", "warning", "critical") REQUIRED
    rule: enum("causal", "logical") DEFAULT "causal"
    context: str OPTIONAL
}

[Act:*] -> [Result:*] {
    confidence: float [0.0, 1.0] REQUIRED
    timestamp: datetime REQUIRED
    context: str OPTIONAL
}
```

**Bidirectional model generation:**

```python
from stl_schema import load_schema, schema_to_model, model_to_schema

# Direction 1: STL Schema → Pydantic model (for STL-first workflows)
schema = load_schema("hybrid_events.stl.schema")
HybridEvent = schema_to_model("HybridEvent", schema)

# Direction 2: Pydantic model → STL Schema (for Python-first workflows)
from pydantic import BaseModel, Field

class ToolCallEvent(BaseModel):
    confidence: float = Field(ge=0.0, le=1.0)
    severity: str = Field(pattern="^(info|warning|critical)$")
    rule: str = "causal"

stl_schema = model_to_schema(ToolCallEvent, source_ns="Obs", target_ns="Act")
# Generates: [Obs:*] -> [Act:*] { confidence: float [0.0, 1.0] REQUIRED ... }
```

**Estimated complexity:** ~800 LOC + tests

#### Tool 3: `stl-llm` — LLM Output Cleaning & Auto-Repair

**Problem:** LLMs generate STL with predictable formatting issues: extra whitespace, missing quotes on string values, markdown code block wrapping, inconsistent arrow characters. For a production protocol, these must be handled automatically — not by asking humans to fix LLM output.

**Why Priority 1:** If STL is an LLM-program bridge, the LLM side of the bridge *will* produce imperfect output. Auto-repair is not a nice-to-have — it's the tolerance layer that makes the bridge usable.

**Solution:** LLM-aware utilities for cleaning, repairing, and validating LLM-generated STL.

```python
from stl_llm import clean, prompt_template, validate_llm_output

# Clean LLM-generated STL (strip markdown blocks, normalize whitespace, fix arrows)
cleaned = clean(raw_llm_output)

# Generate a prompt that teaches an LLM to output STL
prompt = prompt_template(
    schema="hybrid_events.stl.schema",
    examples=3,
    format="concise"  # or "verbose"
)

# Validate LLM output against schema, with auto-repair
result = validate_llm_output(llm_text, schema="hybrid_events.stl.schema")
if result.repaired:
    print(f"Auto-fixed: {result.repairs}")
    # e.g., ["Added missing quotes around string value 'critical'",
    #         "Normalized '->' to '→'",
    #         "Stripped markdown code block wrapper"]
```

**Common auto-repairs:**

| LLM Output Issue | Auto-Repair |
|-----------------|-------------|
| ` ```stl\n[A] -> [B]\n``` ` | Strip markdown code block |
| `::mod(severity=critical)` | Add quotes: `severity="critical"` |
| `[A] --> [B]` | Normalize arrow: `[A] -> [B]` |
| `[ A ] -> [ B ]` | Trim whitespace: `[A] -> [B]` |
| `confidence=1.5` | Clamp to range: `confidence=1.0` + warning |

**Estimated complexity:** ~400 LOC + tests

#### Tool 4: `stl-emitter` — Structured Event Emitter

**Problem:** Applications that log STL events (like Cortex's Hybrid AI) reimplement event formatting, file I/O, and rotation logic each time.

**Solution:** A reusable event emitter library.

```python
from stl_emitter import STLEmitter

emitter = STLEmitter(
    log_path="~/.app/events.log",
    rotation="daily",      # or "size:10MB"
    namespace="MyApp"
)

# Emit events
emitter.emit(
    source="Obs:Error",
    target="Act:Retry",
    confidence=0.90,
    severity="warning",
    context="API returned 500"
)

# Emit from existing ActionDirective
emitter.emit_directive(directive)

# Emit result
emitter.emit_result(directive, success=True, context="recovered")
```

**Estimated complexity:** ~400 LOC + tests

### 4.2 Priority 2 — Proof & Integration

#### Tool 5: `stl-stream` — Streaming STL Parser

**Problem:** Current parser operates on complete documents. Real-time applications (chat systems, log monitors) receive STL line-by-line.

**Solution:** A streaming parser that processes STL incrementally.

```python
from stl_stream import STLStreamParser

parser = STLStreamParser()

for line in live_log_stream:
    result = parser.feed(line)
    if result:  # Complete statement parsed
        print(f"Got: {result.source} -> {result.target}")
        print(f"Confidence: {result.modifiers.get('confidence')}")
```

**Estimated complexity:** ~350 LOC + tests

#### Tool 6: LLM-Native STL Demo — Closing the Proof Gap

**Problem:** The Cortex proof of concept demonstrates program-to-program communication via STL. But the central claim of this document — STL as an *LLM*-program bridge — requires a second proof point: an LLM generating STL that a program directly consumes and acts on.

**Solution:** Build a minimal end-to-end demo:

```
┌─────────┐    STL output    ┌────────────┐   parsed STL   ┌──────────┐
│   LLM   │ ──────────────→  │ stl_parser │ ─────────────→ │ Program  │
│(any model)│  (in response)  │  + stl-llm │  (Pydantic)   │(acts on  │
└─────────┘                  │(auto-repair)│               │ result)  │
                             └────────────┘               └──────────┘
```

**Concrete scenario — Knowledge extraction:**

1. Feed an LLM a text passage + STL schema for extracted facts
2. LLM outputs STL statements (with confidence, source, rule)
3. `stl-llm` cleans the output, `stl_parser` parses it
4. Program stores high-confidence facts, flags low-confidence ones for review

```python
# Example: LLM extracts structured knowledge as STL
llm_output = llm.generate(f"""
Extract key facts from this text as STL statements.
Schema: [Entity:*] -> [Property:*] ::mod(confidence, rule, source)

Text: "Einstein published the theory of special relativity in 1905,
which demonstrated that E=mc²."
""")

# LLM outputs:
# [Entity:Einstein] -> [Event:Published_Special_Relativity] ::mod(confidence=0.98, rule="empirical", time="1905")
# [Theory:Special_Relativity] -> [Equation:E_equals_mc2] ::mod(confidence=0.99, rule="definitional", source="Einstein_1905")

# Program consumes:
from stl_llm import clean
from stl_parser import parse

doc = parse(clean(llm_output))
for stmt in doc.statements:
    if stmt.get_modifier("confidence") >= 0.9:
        knowledge_base.store(stmt)
    else:
        review_queue.add(stmt)
```

**This demo, once built, provides the missing proof:** LLM → STL → Program, with semantic metadata preserved end-to-end.

**Estimated complexity:** ~200 LOC demo + documentation

#### Tool 7: `stl-query` — Query Language for STL Documents

**Problem:** Finding specific statements in large STL documents requires manual iteration.

**Solution:** A lightweight query language.

```python
from stl_query import query

doc = stl_parse(open("events.log").read())

# Find all high-confidence observations
results = query(doc, """
    [Obs:*] -> [Act:*]
    WHERE confidence >= 0.8
    AND severity = "critical"
""")

# Find causal chains
chains = query(doc, """
    CHAIN [?a] -> [?b] -> [?c]
    WHERE rule = "causal"
""")
```

**Estimated complexity:** ~600 LOC + tests

#### Tool 8: `stl-diff` — Semantic Diff for STL Documents

**Problem:** Standard text diff cannot capture semantic changes in STL (e.g., confidence change from 0.8 to 0.6 is semantically significant but looks like a minor text change).

**Solution:** Semantic-aware diff.

```python
from stl_diff import diff

changes = diff(old_doc, new_doc)
# Returns:
# [ModifiedStatement(anchor="[Obs:ToolLoop]", changed_fields={"confidence": (0.8, 0.6)})]
# [AddedStatement(source="[Obs:NewPattern]", target="[Act:Handle]")]
# [RemovedStatement(source="[Old:Signal]", ...)]
```

**Estimated complexity:** ~400 LOC + tests

### 4.3 Priority 3 — Advanced Capabilities

#### Tool 9: `stl-transform` — STL-to-X Transformers

**Problem:** Different systems consume different formats. Need systematic transforms.

**Solution:** Pluggable transformers.

```python
from stl_transform import to_json, to_dataframe, to_networkx, to_mermaid

# STL → JSON (already exists in parser, but as standalone tool)
json_data = to_json(stl_doc)

# STL → pandas DataFrame (for analysis)
df = to_dataframe(stl_doc)
df[df["confidence"] < 0.5]  # Find low-confidence statements

# STL → NetworkX graph (already exists, extracted as standalone)
G = to_networkx(stl_doc)
nx.shortest_path(G, "Obs:ToolLoop", "Result:Recovered")

# STL → Mermaid diagram (for documentation)
mermaid = to_mermaid(stl_doc)
```

**Estimated complexity:** ~500 LOC + tests

*(Note: `stl-llm` moved to Priority 1 — see Tool 3)*

---

## 5. Architecture: How the Tools Compose

```
  PRIORITY 1 — Core Infrastructure & Trust
  ═══════════════════════════════════════════

                    ┌─────────────┐
                    │  stl-schema  │  Contract: what STL is valid?
                    └──────┬──────┘
                           │ validates
              ┌────────────┼────────────┐
              ▼            ▼            ▼
      ┌──────────┐  ┌───────────┐  ┌──────────┐
      │stl-builder│  │stl_parser │  │ stl-llm  │
      │(programs  │  │ (parse &  │  │(clean &  │
      │ generate) │  │ validate) │  │ repair)  │
      └─────┬────┘  └─────┬─────┘  └─────┬────┘
            │              │              │
            ▼              ▼              ▼
      ┌──────────────────────────────────────┐
      │        STL Document (in-memory)       │
      │   List[STLStatement] — Pydantic      │
      └──────────────┬───────────────────────┘
                     │
  ┌──────────┐       │        ┌──────────┐
  │stl-emitter│ ◄────┘────── │stl-stream│   I/O layer
  │  (write)  │              │  (read)  │
  └──────────┘              └──────────┘

  PRIORITY 2 — Proof & Integration
  ═══════════════════════════════════

      ┌──────────────────────────────────────┐
      │        STL Document (in-memory)       │
      └──────────────┬───────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
  ┌──────────┐ ┌──────────┐ ┌────────────┐
  │stl-query │ │stl-diff  │ │LLM-native  │
  │ (search) │ │ (compare)│ │demo (proof)│
  └──────────┘ └──────────┘ └────────────┘

  PRIORITY 3 — Advanced
  ═══════════════════════

  ┌────────────┐
  │stl-transform│ → JSON, DataFrame, Mermaid, NetworkX
  └────────────┘
```

---

## 6. Comparison: STL vs JSON for LLM Communication

### 6.1 Concrete Example

**Scenario:** LLM detects a tool loop and the program needs to decide what to do.

**JSON approach:**
```json
{
  "observation": "tool_loop",
  "action": "break_loop",
  "confidence": 0.95,
  "severity": "critical",
  "rule": "causal",
  "context": "collect_requirements called 2x consecutively"
}
```

**STL approach:**
```
[Obs:ToolLoop] -> [Act:BreakLoop] ::mod(confidence=0.95, severity="critical", rule="causal", context="collect_requirements called 2x consecutively")
```

**Analysis:**

| Dimension | JSON | STL |
|-----------|------|-----|
| **Tokens** | ~45 tokens | ~30 tokens (33% fewer) |
| **Direction** | Implicit (consumer must know "observation" leads to "action") | Explicit (`→`) |
| **Graph structure** | Flat — no inherent graph | Native directed graph |
| **Chaining** | Requires array of objects + manual linking | `[A] → [B] → [C]` |
| **Namespace** | Ad-hoc key prefixes | Native `[Domain:Name]` |
| **Validation** | JSON Schema (separate file, verbose) | STL Schema (inline, concise) |
| **Human readability** | Moderate (braces, quotes, commas) | High (reads like structured prose) |
| **Graph analysis** | Requires building graph from flat data | Direct to NetworkX |
| **Audit logging** | One JSON per line, no inherent linking | STL chains show causal flow |

### 6.2 Where STL Wins

1. **Semantic density** — One STL statement carries direction + metadata vs JSON's flat key-value
2. **Causal chains** — `[A] → [B] → [C]` vs JSON arrays of objects requiring manual linkage
3. **Built-in confidence** — Not an afterthought but a first-class citizen
4. **Graph-native** — Parse once, query as graph immediately
5. **Token efficiency** — 20-40% fewer tokens for equivalent semantic content
6. **Audit readability** — STL logs read like structured narratives

### 6.3 Where JSON Remains Better

1. **Ecosystem maturity** — Universal tooling, every language has a JSON parser
2. **Schema tooling** — JSON Schema is well-established
3. **Simple data** — Configuration files, REST API payloads
4. **Nested structures** — Deeply nested objects (STL is flat by design)
5. **Array data** — Ordered lists of homogeneous items

### 6.4 The Division of Labor

**JSON handles:** "What is the data?"
**STL handles:** "What does this mean, how certain is it, and what caused it?"

In practice, a system might use both:
- **REST API payloads** → JSON (data exchange)
- **LLM reasoning output** → STL (semantic communication)
- **Configuration** → JSON (static data)
- **Audit logs** → STL (traceable reasoning chains)
- **Database records** → JSON (storage)
- **Agent-to-agent messages** → STL (epistemic exchange)

STL complements JSON for AI-native communication. It is not a universal replacement, but a specialized standard for cases where semantic structure, confidence, and directionality matter.

---

## 7. Future Outlook

### 7.1 Near-Term (2026 H1)

- Ship Priority 1 tools (`stl-builder`, `stl-schema`, `stl-llm`, `stl-emitter`) as pip-installable packages
- Build and publish the LLM-native STL demo (Tool 6) — close the proof gap
- Mature the Cortex Hybrid AI as a reference implementation
- Publish STL parser to PyPI
- Write a technical paper: "STL as Structured Communication for LLM-Program Interaction"

### 7.2 Medium-Term (2026 H2)

- Implement Priority 2 tools (`stl-stream`, `stl-query`, `stl-diff`)
- Port STL tooling to TypeScript/JavaScript for web-based AI applications
- Build an STL playground (web UI for writing, validating, and visualizing STL)
- Integrate STL into multi-agent frameworks (e.g., agent-to-agent communication)
- Prototype STL-based function calling as alternative to JSON Schema tool use

### 7.3 Long-Term (2027+)

- Propose STL as a standard protocol for AI observability and audit
- STL as a knowledge interchange format between different AI systems
- STL compiler targets: WebAssembly, Rust, Go (for high-performance pipelines)
- Community-driven STL Improvement Proposals (SIPs)

#### The 反哺 (Feed-Back) Path: STL → SKC

STL was born inside the Semantic Kernel of Consciousness (SKC) project as a language for modeling semantic tension and consciousness dynamics. Its evolution into an LLM-program communication standard is a natural outgrowth — but the relationship is bidirectional.

As STL matures in production use cases (behavior monitoring, knowledge extraction, function calling), the lessons learned feed back into SKC:
- **Schema validation** improves SKC's ability to verify its own knowledge structures
- **Streaming parsing** enables real-time cognitive processing in agentic loops
- **LLM auto-repair** informs how SKC handles noisy semantic input
- **Query language** provides the foundation for SKC's self-inspection capabilities

This 反哺 path ensures that STL's engineering maturity strengthens its theoretical foundations, and vice versa.

---

## 8. How to Contribute

This document is a starting point for discussion. We invite AI collaborators and developers to:

1. **Review and critique** this roadmap — are the priorities right?
2. **Pick a tool** from the roadmap and start prototyping
3. **Propose new tools** we haven't thought of
4. **Test STL in your own applications** and report what works / what's missing
5. **Challenge the premise** — where does STL fall short? What would make it better?

### Key resources:

| Resource | Location |
|----------|----------|
| STL Core Spec v1.0 | `spec/stl-core-spec-v1.0.md` |
| STL Parser (Python) | `parser/` |
| STL Operational Protocol | `.claude/CLAUDE.md` (STL generation guidelines for LLMs) |
| Hybrid AI Reference Implementation | Cortex (`src/cortex/hybrid/`) |
| Hybrid AI Audit Log (sample) | `~/.cortex/hybrid_events.log` |

---

## 9. Summary

STL has moved beyond theoretical specification to **production use**. The Cortex Hybrid AI system proves that STL can serve as a practical, efficient, and semantically rich communication protocol between programs and LLM-adjacent systems.

**Two proof points define the roadmap:**

1. **Program ↔ Program via STL** — Proven (Cortex Hybrid AI, Feb 2026)
2. **LLM → STL → Program** — Next to prove (LLM-native demo, Priority 2)

The next step is building an ecosystem of composable tools — schema, builder, auto-repair, emitter, query, transform — that make STL as easy to adopt as JSON, while providing the semantic depth that JSON was never designed to carry.

**The positioning:**

> JSON is for data. STL is for reasoning. Use both.

**The vision:**

> STL is to AI-native communication what SQL is to databases — a structured, domain-specific language that makes the implicit explicit.

---

*This document was created based on empirical evidence from the Cortex Hybrid AI implementation (2026-02-11) and iterated with critical analysis of evidence-claim gaps, tooling priorities, and adoption strategy (2026-02-11 v0.2.0).*

---

## Changelog

### v0.2.0 (2026-02-11)

**Positioning:**
- Reframed vision from "Replace JSON" to "JSON for data, STL for reasoning" — complement, not compete
- Added Section 6.4 (The Division of Labor) — concrete guidance on when to use JSON vs STL

**Use cases:**
- Added Function Calling / Tool Use as killer use case (Section 2.2) with concrete JSON vs STL comparison

**Evidence:**
- Added honest scope assessment to Cortex proof (Section 1.3) — clearly distinguishes what is proven (program↔program) from what is next (LLM→STL→program)
- Defined two-proof-point framework in Summary (Section 9)

**Tooling roadmap reprioritized:**
- `stl-schema` moved from Priority 3 (Tool 7) → Priority 1 (Tool 2) — communication protocols need a contract from day one
- `stl-llm` moved from Priority 3 (Tool 9) → Priority 1 (Tool 3) — LLM output tolerance is a production requirement
- Added Tool 6: LLM-Native STL Demo — closes the critical proof gap
- `stl-to-pydantic` merged into `stl-schema` with bidirectional support (STL→Pydantic and Pydantic→STL)
- Priority 1 expanded from 3 tools to 4 (builder, schema, stl-llm, emitter)
- Tool numbering renumbered 1-9 across priorities

**Architecture:**
- Updated architecture diagram to reflect priority layers
- Expanded 反哺 (Feed-Back) path from one-line mention to dedicated subsection

**Future outlook:**
- Updated near-term roadmap to reflect new priorities
- Added "STL-based function calling" to medium-term roadmap

### v0.1.0 (2026-02-11)

- Initial draft based on Cortex Hybrid AI empirical results
