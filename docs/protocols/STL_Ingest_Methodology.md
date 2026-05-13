# STL Ingest Methodology v1.2

> **What's new in v1.2 (2026-05-13):** Aligned with STL Operational Protocol
> v1.2.
>
> - `confidence` default changes from `0.5` to **`1.0`** (assertive — reserved
>   for analytic truths). Strong empirical claims now use canonical `0.95`.
> - `confidence` is no longer "required" — omission means `1.0` (analytic).
>   It MUST be written explicitly only for non-1.0 values.
> - `rule` can be **omitted and inferred** from the meta-semantic field
>   (Operational Protocol §4.2.2). Writing `rule="..."` is still legal and
>   wins over inference.
> - Six canonical confidence levels replace continuous bands: `1.0` / `0.95`
>   / `0.8` / `0.5` / `0.2` / `0.01`. See §8 below and Operational Protocol §5.2.
>
> Backward compatible — existing edges with explicit values continue to parse
> identically.

> **Protocol Type:** Methodology for converting knowledge sources into high-quality STL edges
> **Prerequisite:** STL Operational Protocol v1.0
> **Scope:** All ingest pathways — manual, LLM-assisted, automated pipeline
> **Core Principle:** Every edge must carry semantic meaning, not just structural connection

---

## 0. Why This Document Exists

STL edges can be syntactically valid but semantically empty. A syntactically correct edge:

```stl
[A] -> [B] ::mod(confidence=0.9, path="file.c")
```

passes all parsers but tells you nothing about WHY A connects to B. This document defines what makes an edge **semantically complete** and how to achieve that in automated ingest.

---

## 1. The Three Categories of an STL Edge

Every well-formed edge carries three categories of information:

```
Meta Semantic Field     — WHAT is the relationship?         (the edge's soul)      REQUIRED
Computational Modifier  — HOW does the STG engine use it?   (the edge's weight)    REQUIRED
Informational Modifier  — WHAT context do humans need?      (the edge's metadata)  AS NEEDED
```

### 1.1 Meta Semantic Fields (REQUIRED — the edge's soul)

Meta semantic fields define **the nature of the relationship** between source and target. Without one, the edge is an empty shell — you know A connects to B but not why.

| Field | Semantics | When to Use | Example |
|-------|-----------|-------------|---------|
| `is_a` | Classification / taxonomy | A is a kind of B | `is_a="scheduling_algorithm"` |
| `action` | Behavioral / causal | A does something to/toward B | `action="triggers"`, `action="reclaims"` |
| `role` | Functional role | A plays a role in B | `role="entry_point"`, `role="guardian"` |
| `status` | State of being | A has a state relative to B | `status="deprecated"`, `status="active"` |
| `phase` | Temporal stage | A is in a stage of B's lifecycle | `phase="initialization"`, `phase="cleanup"` |
| `relation` | General (use sparingly) | Only when no specific field fits | `relation="depends_on"` |

**Rules:**
- Every edge MUST carry at least one meta semantic field
- Choose the MOST SPECIFIC field that fits (don't default to `relation`)
- The value should be a concise verb or noun phrase, not a sentence
- Multiple meta fields on one edge are allowed when genuinely orthogonal (e.g., `role="handler"` + `phase="runtime"`)

**Retired fields** (merged into the above):
- ~~`type`~~, ~~`kind`~~ → use `is_a` instead
- ~~`predicate`~~ → use `action` or `role` instead

### 1.2 Computational Modifiers (the edge's weight)

These are not just metadata — **the STG engine reads them at runtime** and they directly affect propagation, pruning, and ranking.

| Modifier | Type | STG Engine Uses It For | Required? | Default | Example |
|----------|------|----------------------|-----------|---------|---------|
| `confidence` | Float 0-1 | Propagation weight; initial salience; pruning threshold | Only for non-1.0 values | **`1.0`** (analytic) | `confidence=0.95` |
| `strength` | Float 0-1 | Causal link strength (amplifies propagation on causal edges) | Only when `rule="causal"` | absent | `strength=0.9` |

**`confidence` defaults to `1.0` when omitted (Operational Protocol §4.2.1).**
`1.0` is reserved for **analytic truths** — definitions, mathematical
theorems, logical tautologies, taxonomic membership by definition. For
empirical/synthetic claims, write `confidence` explicitly using one of the
six **canonical levels**:

| Confidence | Canonical Name | Use When |
|-----------:|---------------|----------|
| **1.0** *(default — omit)* | **Assertive** | Analytic truth: definition, math, logic. NOT for empirical claims. |
| **0.95** | **Confident** | Strong empirical evidence; direct quote from authoritative source; widely accepted theory. The default for synthetic claims. |
| **0.8** | **Likely** | Moderate evidence; reasonable inference; room for revision. |
| **0.5** | **Unknown** | Maximum entropy / 50-50; genuine ignorance. |
| **0.2** | **Doubtful** | Evidence against; weak supporting evidence. |
| **0.01** | **Disbelieved** | Recorded but rejected (often paired with `certainty`). |

Pick from the canonical set rather than inventing intermediate values
(`0.85`, `0.72`, etc.). Existing edges with non-canonical values remain
valid; the canonical set is a SHOULD for new authoring.

**The analytic/synthetic distinction (why `1.0` is not just "very confident"):**

```stl
# Analytic — true by definition. confidence defaults to 1.0; omit it.
[Cat] -> [Mammal] ::mod(is_a="taxonomy")
[Triangle] -> [Three_Sides] ::mod(is_a="geometric_property")

# Synthetic — empirical claim, even very strong ones. Write 0.95 explicitly.
[Smoking] -> [Lung_Cancer] ::mod(action="causes", confidence=0.95)
[Einstein] -> [General_Relativity] ::mod(author="Einstein", confidence=0.95)
```

Writing `confidence=1.0` on an empirical edge is a category error — you are
claiming analytic truth where only synthetic evidence exists.

**Note:** `salience` is also a computational field but is **auto-managed** by the engine (initialized from confidence, adjusted by Hebbian learning and decay). Do not set it manually.

### 1.3 Informational Modifiers (AS NEEDED — the edge's metadata)

These provide context for humans and LLMs reading the edge. The STG engine stores them but does not compute with them.

| Modifier | Purpose | Example |
|----------|---------|---------|
| `rule` | How was this knowledge obtained? (`"causal"` / `"definitional"` / `"logical"` / `"empirical"`). **May be omitted** — parsers infer from the meta-semantic field (Operational Protocol §4.2.2): `is_a`/`role` → `definitional`; `action` + `cause`/`effect` → `causal`; `action` + `lesson` → `empirical`; etc. | `rule="causal"` |
| `cause` | What triggers the effect? | `cause="memory exhausted"` |
| `effect` | What is the result? | `effect="process killed"` |
| `lesson` | What was learned from experience? | `lesson="bloom filter avoids scanning cold pages"` |
| `description` | Human-readable explanation | `description="..."` |
| `text` | Verbatim source text (lossless) | `text="CFS uses a time-ordered rbtree..."` |
| `path` | File path (relative to project root) | `path="mm/oom_kill.c"` |
| `symbol` | Function or struct name | `symbol="out_of_memory"` |
| `subsystem` | Kernel/project subsystem | `subsystem="mm"` |
| `source` | External reference (URL, sysfs path, RFC) | `source="/sys/class/bdi/..."` |
| `domain` | Knowledge domain | `domain="memory_management"` |
| `timestamp` | When the event/fact occurred | `timestamp="2026-04-15"` |
| `author` | Who established this knowledge | `author="Ingo Molnar"` |
| `certainty` | Agent's belief in objective truth (distinct from confidence) | `certainty=0.7` |

### How the three categories work together

v1.2 form (prefer this — defaults omitted):

```stl
[kswapd] -> [Page_Reclaim] ::mod(
  action="performs",                 ← Meta Semantic Field: WHAT is the relationship
                                     ← confidence omitted → 1.0 (assertive)
                                     ← rule omitted → "definitional" (inferred from is_a-style action)
  path="mm/vmscan.c",                ← Informational: where the code lives
  symbol="kswapd",                   ← Informational: which function
  description="..."                  ← Informational: human explanation
)

[Memory_Pressure] -> [OOM_Kill] ::mod(
  action="triggers",                 ← Meta Semantic Field: WHAT
  strength=0.95,                     ← Computational: causal strength (required for causal edges)
  confidence=0.95,                   ← Explicit: synthetic empirical claim, not analytic
                                     ← rule omitted → "causal" (inferred from action + strength)
  cause="all reclaim failed",        ← Informational: context
  effect="victim process killed"     ← Informational: context
)
```

The pre-v1.2 explicit form remains valid:

```stl
[kswapd] -> [Page_Reclaim] ::mod(
  action="performs", confidence=0.99, rule="definitional",
  path="mm/vmscan.c", symbol="kswapd", description="..."
)
```

Use it when you want maximum clarity for human readers, or when overriding
the inferred `rule`. For most authoring, prefer the default-omitted form.

| Category | Modifiers | Purpose |
|----------|-----------|---------|
| **Confidence** | `confidence` (0-1) | How reliable is this edge? |
| **Provenance** | `source`, `author`, `timestamp` | Where did this come from? |
| **Location** | `path`, `symbol`, `subsystem` | Where is the implementation? |
| **Content** | `description`, `text`, `lesson` | Human-readable explanation |
| **Strength** | `strength` (0-1) | How strong is the causal link? |
| **Certainty** | `certainty` (0-1) | Agent's belief in objective truth |

---

## 2. The Completeness Test

Before ingesting an edge, check:

```
□ Does it have at least one meta semantic field?     (Layer 1)
    → If no: it's an empty shell. Add one or don't ingest.

□ Does the meta field value actually convey meaning?
    → Bad:  action="related"  (says nothing)
    → Good: action="triggers_when_watermark_breached"

□ Is the description accurate to the source material?
    → If from code: does it match what the function actually does?
    → If from text: does it match what the document actually says?
    → If unsure: don't ingest. No edge > wrong edge.

□ Is the source node specific enough?
    → Bad:  [Memory_Management]  (too broad)
    → Good: [Page_Reclaim_Via_Kswapd]

□ Is the target node specific and DIFFERENT from other edges?
    → If all edges point to the same target: low-quality batch.
```

---

## 3. Ingest Patterns by Knowledge Source

### 3.1 Source Code (functions, structs, modules)

**Primary meta fields:** `action`, `role`, `is_a`, `phase`
**Primary attributes:** `path`, `symbol`, `subsystem`, `description`

Decision tree for choosing meta field:

```
Function does X to Y?
  → action="X"  (e.g., action="reclaims", action="evaluates", action="dispatches")

Function IS a kind of X?
  → is_a="X"  (e.g., is_a="sysfs_callback", is_a="interrupt_handler")

Function SERVES as X in subsystem Y?
  → role="X"  (e.g., role="entry_point", role="fallback", role="validator")

Function runs during lifecycle phase X?
  → phase="X"  (e.g., phase="initialization", phase="shutdown", phase="error_recovery")

Function exposes interface at /sys or /proc?
  → role="sysfs_interface", source="/sys/..."

Function's state is notable?
  → status="X"  (e.g., status="deprecated", status="config_dependent")
```

**Example edges:**

```stl
[OOM_Killer_Entry] -> [Victim_Process_Termination] ::mod(
  action="selects_and_kills",
  rule="causal",
  confidence=0.99,
  strength=0.95,
  cause="all reclaim attempts exhausted",
  effect="highest-scoring process terminated via SIGKILL",
  path="mm/oom_kill.c",
  symbol="out_of_memory",
  subsystem="mm",
  description="Main OOM entry that evaluates memory state, selects victim via oom_badness, invokes kill"
)

[BDI_Min_Ratio_Fine] -> [Dirty_Page_Quota] ::mod(
  role="sysfs_interface",
  is_a="store_callback",
  confidence=0.98,
  path="mm/backing-dev.c",
  symbol="min_ratio_fine_store",
  subsystem="mm",
  source="/sys/class/bdi/<dev>/min_ratio_fine",
  description="Sets fine-grained minimum dirty page ratio for a backing device without BDI_RATIO_SCALE"
)

[Can_Age_Anon_Pages] -> [Reclaim_Strategy_Decision] ::mod(
  action="evaluates_feasibility",
  rule="logical",
  confidence=0.95,
  path="mm/vmscan.c",
  symbol="can_age_anon_pages",
  subsystem="mm",
  description="Checks swap availability and NUMA demotion feasibility to decide if aging anonymous pages is worthwhile"
)

[MGLRU_Bloom_Filter] -> [Hot_Page_Tracking] ::mod(
  is_a="probabilistic_data_structure",
  rule="empirical",
  confidence=0.95,
  path="mm/vmscan.c",
  symbol="lru_gen_test_recent",
  subsystem="mm",
  lesson="Bloom filter trades false positives for O(1) lookup; avoids scanning cold pages entirely",
  description="Tests recent page access via per-generation bloom filter to guide LRU aging"
)

[OOM_Init] -> [OOM_Subsystem] ::mod(
  phase="initialization",
  role="subsystem_initializer",
  confidence=0.98,
  path="mm/oom_kill.c",
  symbol="oom_init",
  subsystem="mm",
  description="Registers OOM killer subsystem and initializes global reaper structures at boot"
)
```

### 3.2 Documentation (prose, specifications, RFCs)

**Primary meta fields:** `is_a`, `relation`, `action`
**Primary attributes:** `text` (verbatim), `source`, `section`, `description`

```stl
[Doc_CFS_Section3_RBTree] -> [CFS_Scheduler] ::mod(
  is_a="design_documentation",
  rule="definitional",
  confidence=0.99,
  section="3. THE RBTREE",
  source="Documentation/scheduler/sched-design-CFS.rst",
  text="CFS uses a time-ordered rbtree to build a timeline of future task execution..."
)
```

### 3.3 Design Narratives (cross-document conceptual chains)

**Primary meta fields:** `action` (causal chains), `is_a` (classification)
**Primary attributes:** `cause`, `effect`, `strength`, `description`

```stl
[Virtual_Runtime_Necessity] -> [Leftmost_Selection_Rule] ::mod(
  action="necessitates",
  rule="causal",
  confidence=0.98,
  strength=0.95,
  cause="vruntime normalizes CPU time to ideal fair share",
  effect="task with smallest vruntime should run next",
  description="The core CFS selection rule derives directly from the vruntime definition"
)
```

### 3.4 Lessons and Experience

**Primary meta fields:** `action`, `status`
**Primary attributes:** `lesson`, `timestamp`, `description`

```stl
[AppArmor_UserNS_Restriction] -> [Thumbnail_Generation_Failure] ::mod(
  action="blocks",
  rule="empirical",
  confidence=0.98,
  lesson="Ubuntu 24.04 default apparmor_restrict_unprivileged_userns=1 prevents bwrap sandbox, breaking GNOME thumbnailer",
  timestamp="2026-04-15"
)
```

### 3.5 Node Intrinsic Properties (Self-Loop Pattern)

**Primary meta field:** `action="intrinsic_properties"` (reserved value)
**Form:** `[Node] -> [Node]` (self-loop — surface syntax only, not stored as an edge)
**Primary attributes:** any free-form attribute keys (`appid`, `release_year`, `price_usd`, ...)

When a node has multiple identity-level attributes that would otherwise be **repeated on every outgoing edge**, write them as a single self-loop intrinsic-property statement. The engine materializes the modifiers into the node's attribute storage; **no graph edge is created**.

```stl
[Elden_Ring] -> [Elden_Ring] ::mod(
  action="intrinsic_properties",
  appid="1245620",
  release_year="2022",
  price_usd="59.99",
  reviews_total="850000",
  confidence=0.99,
  rule="definitional"
)
```

**What ingest does** (see STL Operational Protocol §9.4):
1. Detects self-loop + `action="intrinsic_properties"` pattern
2. Strips carrier keys (`action`, `edge_class`)
3. Calls `add_node(**remaining_modifiers)` — attrs go to node-level storage
4. **Does not create an edge** — `_edges` / `_edges_lookup` / graph topology / SQLite `edges` table are untouched

**Use when:**
- A node will emit ≥ 5 outgoing edges that would otherwise duplicate the same attributes
- Attributes are intrinsic to the node identity (id, registration codes, fixed dimensional facts)

**Don't use when:**
- The attribute is itself a relationship → make it a normal edge with the appropriate `action`
- Only 1–2 attributes — boilerplate cost on outgoing edges is acceptable

**Confidence/rule calibration:** authors typically write `confidence=0.99, rule="definitional"` for STL syntactic completeness, but these are edge-level fields and engines drop them during materialization (no edge to attach them to). They are not retained in the node's attribute store.

**Retrieval:** node attributes are queryable via the engine's node-attribute query path (e.g. `JSON_EXTRACT(metadata_json, '$.appid')` in STG's SQLite backend). UIs render attributes as a `Properties:` section in node detail views.

---

## 4. Anti-Patterns (What NOT to Do)

### 4.1 Empty Shell Edge
```stl
# ❌ No meta semantic field — what IS the relationship?
[A] -> [B] ::mod(confidence=0.9, path="file.c")
```

### 4.2 Generic Meta Value
```stl
# ❌ action="related" says nothing
[A] -> [B] ::mod(action="related", confidence=0.9)

# ✅ Specific
[A] -> [B] ::mod(action="triggers_on_threshold_breach", confidence=0.9)
```

### 4.3 Uniform Target Syndrome
```stl
# ❌ All edges point to [Memory_Management] — no discrimination
[Func_A] -> [Memory_Management] ::mod(...)
[Func_B] -> [Memory_Management] ::mod(...)
[Func_C] -> [Memory_Management] ::mod(...)

# ✅ Each target reflects the specific concept
[Func_A] -> [Page_Reclaim_Decision] ::mod(...)
[Func_B] -> [OOM_Victim_Selection] ::mod(...)
[Func_C] -> [Dirty_Page_Writeback] ::mod(...)
```

### 4.4 Description Restates Function Name
```stl
# ❌ "Selects a bad process" just restates select_bad_process
[Select_Bad_Process] -> [MM] ::mod(description="Selects a bad process")

# ✅ Explains the concept
[OOM_Victim_Selection] -> [Process_Scoring] ::mod(
  action="ranks_by_oom_badness",
  description="Scans task list using oom_badness scores considering RSS, swap, and oom_score_adj to find the process whose death frees the most memory"
)
```

### 4.5 Hallucinated Description
```stl
# ❌ LLM guessed "read-ahead" from function name — actually does dirty page ratio
[Min_Ratio_Adjustment] -> [Ratio_Configuration] ::mod(
  description="Adjusts fine-grained minimum ratio parameter for read-ahead algorithm"
)
```

**Prevention:** Always feed function source context (comments + body) to LLM. Never generate description from function name alone.

### 4.6 Intrinsic Attributes Repeated on Outgoing Edges

```stl
# ❌ Each outgoing edge re-declares the same node-identity attributes
[Elden_Ring] -> [Souls_Like]   ::mod(action="has_tag", appid="1245620", year="2022", confidence=0.95)
[Elden_Ring] -> [Action_RPG]   ::mod(action="has_tag", appid="1245620", year="2022", confidence=0.95)
[Elden_Ring] -> [Open_World]   ::mod(action="has_tag", appid="1245620", year="2022", confidence=0.95)
# ... 35 more rows, all carrying appid + year again ...

# ✅ Put intrinsics on a single self-loop carrier; outgoing edges stay clean
[Elden_Ring] -> [Elden_Ring] ::mod(action="intrinsic_properties", appid="1245620", year="2022", confidence=0.99, rule="definitional")
[Elden_Ring] -> [Souls_Like] ::mod(action="has_tag", confidence=0.95)
[Elden_Ring] -> [Action_RPG] ::mod(action="has_tag", confidence=0.95)
[Elden_Ring] -> [Open_World] ::mod(action="has_tag", confidence=0.95)
```

See §3.5 for the pattern and STL Operational Protocol §9.4 for the runtime contract.

---

## 5. Quality Tiers

| Tier | Meta Field | Rule | Description | Source Context | Review |
|------|-----------|------|-------------|---------------|--------|
| **Gold** | ✅ specific | ✅ correct | ✅ concept-level, accurate | ✅ full context fed | ✅ human/Claude reviewed |
| **Silver** | ✅ present | ✅ present | ⚠ adequate but shallow | ✅ context fed | ❌ not reviewed |
| **Bronze** | ✅ present | ⚠ default | ⚠ may restate name | ❌ name-only | ❌ not reviewed |
| **Reject** | ❌ missing | — | ❌ hallucination | ❌ | — |

**For public knowledge bases: Gold or Silver only.** Bronze is acceptable for personal/draft STG. Reject must never be ingested.

---

## 6. Epistemic Classification (TruthHallucination Standard Integration)

Every edge carries an implicit epistemic claim. Before ingesting, classify it using the [TruthHallucination Standard v1.2](../../TruthHallucination-Standard-v1.2.md):

### 6.1 Four Trace Types

| Trace Type | What it means | confidence | certainty | Ingest? |
|-----------|---------------|-----------|-----------|---------|
| **EarthTrace** | Verifiable fact: peer-reviewed, reproducible, documented | 0.60-0.98 | ≈ confidence | ✅ Yes |
| **CosmicTrace** | Structurally coherent but beyond current paradigm | 0.50-0.75 | < confidence | ✅ Yes, with markers |
| **UserClaimed** | Subjective claim from a source | 0.40-0.95 | 0.10-0.60 | ✅ Yes, labeled |
| **Hallucination** | Self-contradictory, no structure, fabricated | — | — | ❌ **Never ingest** |

### 6.2 When to Use Each

**EarthTrace** — the default for most ingest:
- Source code (code IS the fact)
- Official documentation
- Peer-reviewed papers
- Reproducible experiments
- Only `confidence` needed; `certainty` is implicit (same as confidence)

```stl
[kswapd] -> [Page_Reclaim] ::mod(
  action="performs",
  confidence=0.99,       # EarthTrace: code proves it
  path="mm/vmscan.c", symbol="kswapd"
)
```

**CosmicTrace** — structurally coherent but unverified:
- Theoretical predictions not yet tested
- Design rationale inferred (not documented)
- Cross-system analogies

```stl
[EEVDF_Lag_Bound] -> [Latency_Guarantee] ::mod(
  action="provides",
  confidence=0.70,
  certainty=0.55,        # CosmicTrace: theory, not measured
  trace_type="CosmicTrace",
  description="EEVDF theoretically bounds scheduling latency but empirical measurements vary"
)
```

**UserClaimed** — source says it, agent isn't sure:
- User bug reports ("it crashed when I did X")
- Anecdotal performance claims
- Third-party blog posts without evidence

```stl
[User_Report] -> [Performance_Improvement] ::mod(
  action="claims",
  confidence=0.90,       # User definitely said this
  certainty=0.40,        # But agent doubts the claim
  trace_type="UserClaimed",
  description="User reports 30% throughput increase after switching scheduler"
)
```

**Hallucination** — never ingest:
- LLM fabricated a description that doesn't match source code
- Self-contradictory statements
- Claims with no structural basis

### 6.3 The confidence-certainty Split

Most edges only need `confidence`. Add `certainty` ONLY when they diverge:

```
confidence = "How reliable is the SOURCE of this edge?"
certainty  = "How likely is the CONTENT to be objectively true?"

Same:     Scientific fact     → confidence=0.95, certainty not needed
Split:    User anecdote       → confidence=0.90 (they said it), certainty=0.30 (doubtful)
Split:    LLM-generated desc  → confidence=0.85 (format OK), certainty=0.60 (might be wrong)
```

**For LLM-generated code descriptions (our pipeline):**
When Stage 1 (local LLM) generates a description without review, consider:
- `confidence` = structural reliability (syntax valid, fields present) → 0.85-0.95
- `certainty` = semantic accuracy (does description match code reality?) → 0.60-0.80

After Stage 2 review confirms accuracy, `certainty` can be removed (it converges with confidence).

### 6.4 The Hallucination Gate

The TH Standard's most important rule for ingest: **Hallucination = not manifestable = never ingest.**

In practice for LLM pipelines:

| LLM Output Problem | TH Classification | Action |
|--------------------|--------------------|--------|
| Description matches source code | EarthTrace | ✅ Ingest |
| Description is vague but not wrong | EarthTrace (low confidence) | ✅ Ingest at 0.70 |
| Description contradicts source code | **Hallucination** | ❌ Delete |
| Description invents features that don't exist | **Hallucination** | ❌ Delete |
| Description is plausible but unverifiable | CosmicTrace | ⚠ Ingest with certainty < confidence |

**This is why Stage 2 review exists** — Stage 1 (local LLM) cannot distinguish its own hallucinations from accurate descriptions. Only a reviewer with access to the actual source code can make this judgment.

---

## 7. Two-Stage Pipeline for LLM Ingest

```
Stage 1: Generation (local LLM, fast, cheap)
  Source context → LLM → STL edges with meta semantic fields
  → stl_parser.validate_llm_output() for format validation
  → Post-validate: meta field present? target diverse? no self-loops?
  → Write .md files

Stage 2: Review (large LLM or human, thorough)
  Read .md + original source → verify each edge:
    □ Meta semantic field appropriate?
    □ Description matches source code reality?
    □ No hallucination?
  → Mark: ✅ keep / ⚠ fix description / ❌ delete
  → Write reviewed .md → stg ingest-file
```

**Stage 1 catches format issues. Stage 2 catches semantic issues.** Neither alone is sufficient.

---

## 8. Confidence Calibration (v1.2 canonical levels)

Pick from the six canonical levels rather than inventing intermediate
values. See Operational Protocol §5.2 for the full discussion.

| Confidence | Canonical Name | Use When (kernel/code ingest examples) |
|-----------:|---------------|----------------------------------------|
| **1.0** *(omit)* | **Assertive** | Analytic truth — function signature *defines* the relationship; struct field *is* the attribute. Type-level facts that hold by definition. |
| **0.95** | **Confident** | Strong evidence — code comments + body clearly support the claim; well-documented historical fact; direct quote from authoritative source. |
| **0.8** | **Likely** | Moderate evidence — inferred from code patterns, not explicitly documented; correlation observed across multiple call sites. |
| **0.5** | **Unknown** | Genuine 50-50 — two competing interpretations with no decisive code evidence; ambiguous comment. |
| **0.2** | **Doubtful** | Evidence against — leaning false but recording for completeness; competing implementations elsewhere refute the local code. |
| **0.01** | **Disbelieved** | Recorded but rejected — user-claimed but agent doubts; apocryphal documentation. |

**Confidence < 0.5 ingest policy:** still legal, but pair with `certainty`
when source-reliability and content-truth diverge. Don't silently drop
edges — record them with the right level so the asymmetry stays visible.

---

## Appendix A: Meta Semantic Field Quick Reference

```
is_a     → "X is a kind of Y"          (taxonomy, classification)
action   → "X does something to/for Y" (behavior, causation, operation)
role     → "X serves as R in Y"        (functional purpose)
status   → "X is in state S re: Y"     (lifecycle, deprecation)
phase    → "X occurs during phase P"   (temporal, initialization, cleanup)
relation → "X relates to Y as R"       (general — use only as last resort)
```

## Appendix B: Retired Fields

| Old Field | Replacement | Reason |
|-----------|------------|--------|
| `type` | `is_a` | Redundant — both mean classification |
| `kind` | `is_a` | Same as type |
| `predicate` | `action` or `role` | Overly formal; action/role are clearer |

---

**End of STL Ingest Methodology v1.2**
**Established:** 2026-04-16 (v1.0)
**Updated:** 2026-05-13 (v1.2 — align with Operational Protocol v1.2)
**Authors:** wuko + Syn-claude

---

## Changelog

**v1.2.0 (2026-05-13)** — Align with STL Operational Protocol v1.2:
- §1.2 Computational Modifiers: `confidence` default changes `0.5` → **`1.0`**
  (assertive — analytic truths only). Strong empirical claims use canonical
  `0.95`. Calibration table rewritten as 6 canonical discrete levels.
- §1.2 introduced the analytic/synthetic distinction with examples.
- §1.3 Informational Modifiers: `rule` may be omitted; parsers infer from
  meta-semantic field (cross-reference to Operational Protocol §4.2.2).
- §1.3 "How the three categories work together": example pair shows v1.2
  default-omitted form alongside the legacy explicit form.
- §8 Confidence Calibration: continuous ranges replaced with six canonical
  levels; ingest policy clarified for `confidence < 0.5` (don't drop —
  pair with `certainty`).
- Header gained a "What's new in v1.2" callout.

Backward compatible. Existing edges with explicit `confidence=0.5` /
`0.85` / `0.99` / etc. continue to parse identically; canonical levels are
SHOULD for new authoring, not MUST for parsing.

**v1.0.0 (2026-04-16)** — Initial methodology document.
