# Board-as-Spec Protocol

> **Version:** 0.2 (Public Draft; v0.1→v0.2: added §5.1 note-status rule, §5.2 transition set + C11/C12, from clean-room test findings. 2026-08-21: added §9 related work, informative — no normative change)
> **Status:** Public Draft — feedback welcome via the STL repository
> **License:** CC BY 4.0
> **Date:** 2026-08-13
> **Authors:** SCOS-Lab (wuko, Syn-claude)
> **Depends on:** STL Core Specification v1.0 (statement syntax); Intent Contract Specification v0.2 (§3 goal declaration)
> **Series:** Trust-Layer Protocol Suite, part 2 of 3 (Intent Contract / **Board-as-Spec** / Eval-Verdict Vocabulary)

---

## 1. Overview

### 1.1 The problem

An autonomous Agent executing long-horizon work needs a plan representation that survives what the Agent's working memory cannot: session death, context decay, interruption, hand-off to another agent, and audit by an absent Principal. Prose plans fail at this — they cannot be queried, their progress cannot be measured, and their state cannot be trusted after the writer's context is gone.

This specification defines the **Board**: a durable goal tree whose structure is authored declaratively and whose execution state is maintained by the system. The Board is simultaneously the Agent's specification ("spec as the executable artifact"), its progress tracker, its externalized attention, and the Principal's audit surface.

### 1.2 Design principles

1. **Two write planes, never mixed.** Structure (what the work is) is authored on the *authoring plane*; state (how it is going) lives on the *execution plane*. The authoring source MUST NOT carry state — a re-materialization of the source would silently overwrite live state (§4).
2. **Bookkeeping belongs to the system; attention belongs to the Agent.** The Agent reports outcomes (pass / halt); every derived fact — the current focus, progress, cross-board completion — is computed and written by the system (§5, §6).
3. **Identity is semantic and stable.** Every item is addressed by a meaning-bearing stable identifier, never by position. Positions drift; identity must not (§3.3).
4. **The tree grows; it is not pre-planned.** Tasks that turn out to be goals expand into child boards at discovery time. Depth is emergent (§3.4).
5. **The Board outranks the Agent's memory.** On any conflict between the Agent's working context and the Board, the Board wins (§7.2).

### 1.3 Conformance language

**MUST / MUST NOT / SHOULD / SHOULD NOT / MAY** per RFC 2119.

---

## 2. Terminology

| Term | Definition |
|---|---|
| **Board** | A durable goal tree: one goal declaration plus an ordered set of items. |
| **Item** | A node on a board: either a **note** (context, non-actionable) or a **task** (actionable, verifiable). |
| **Slug** | An item's stable semantic identifier, unique within its board. |
| **Cursor** | The system-maintained pointer to the single task currently in focus. |
| **Child board** | A board that instantiates one non-atomic task of a parent board. |
| **Materialization** | Deriving the live board from its authored source. |
| **Dormancy** | The state of a fully-completed board that remains live for future tasks (§7.3). |
| **Agent / Principal** | As in the Intent Contract Specification. |

---

## 3. Structure Model

### 3.1 Authoring form

A board is authored as STL statements: one **board anchor** connected to a metadata item, a goal item, and task items.

```stl
[Board:MigrateArchive] -> [Meta] ::mod(title="Archive migration", created_by="agent-a")

[Board:MigrateArchive] -> [Goal]        ::mod(type="note", content="=== Goal === Migrate the legacy archive to the new store.\nintent: <confirmed intent line per Intent Contract Spec §6.1>")
[Board:MigrateArchive] -> [Inventory]   ::mod(type="checkbox", content="Inventory all legacy records; pass = counted manifest exists")
[Board:MigrateArchive] -> [BulkCopy]    ::mod(type="checkbox", content="Copy records to new store; pass = counts match manifest")
[Board:MigrateArchive] -> [VerifySpot]  ::mod(type="checkbox", content="Spot-verify N random records byte-identical")
```

### 3.2 Goal declaration

The goal note SHOULD carry the confirmed `intent:` line (Intent Contract Spec §6.1) when the board operates under an intent contract. A board created by re-instantiation (Tier T1) MUST carry a lineage reference to its predecessor in its metadata (`intent_of=` / `supersedes=`).

### 3.3 Identity rules

- **Board identity** is a stable id fixed at creation (RECOMMENDED: derived from the authored source's name, so identity exists before first materialization).
- **Item identity** is the slug: unique within the board, semantically descriptive of the task (not a copy of its display text), and **stable across content edits**. Display text MAY change freely; the slug MUST NOT.
- **Ordinals are display-only.** Any numbering shown to humans MUST NOT be used for addressing: insertion and reordering make ordinals drift. All programmatic addressing uses slugs.

### 3.4 Atomicity and expansion

For every task, apply the test: *can this be directly executed and pass/fail-verified within one working session?*

- **Yes** → it is a leaf; keep it as a task.
- **No** (it is itself a goal) → expand it into a **child board** that declares, in its metadata, which parent task it instantiates:

```stl
[Board:CopyPhase] -> [Meta] ::mod(title="Bulk copy", parent_board="migrate-archive", parent_item="BulkCopy")
```

Expansion recurses: a child's task may itself expand. Task *count* is not a signal of atomicity — three non-atomic tasks warrant three child boards; twenty-five atomic tasks warrant none. Implementations SHOULD NOT pre-build depth speculatively.

Each task SHOULD state its own pass criterion in its display text, so that "done" is decidable without consulting the author.

---

## 4. The Two Write Planes

### 4.1 The iron rule

**The authored source MUST NOT contain execution state.** State fields (status, sub-status, progress) are written exclusively through the execution plane (the state API). 

*Rationale:* boards re-materialize from source whenever structure changes. If the source carried state, every re-materialization would reset live state to the authored snapshot — silent loss of exactly the data the Principal audits. The two planes exist so that structure edits and state changes can never race each other.

### 4.2 Materialization requirements

- Materialization MUST merge by slug: structure updates from the source; state carries over from the execution plane.
- Structure appended after a board is live MUST survive subsequent state writes (an implementation MUST NOT let a state write cause later structure reads to be skipped).
- Deletion of boards or items MUST be recoverable (archive, not destroy) — plan artifacts are audit records.

---

## 5. Status, Cursor, and Halts

### 5.1 Status vocabulary

| Status | Written by | Meaning |
|---|---|---|
| `pending` | system (default) | Not yet in focus. **Not** a stall signal. |
| `in_progress` | **system only** | The cursor: the single task currently in focus. |
| `pass` | agent | Done, criterion met. |
| `fail` | agent | Attempted, criterion not met (terminal for this task). |
| `warn` | agent | Done with caveats recorded in notes. |
| `blocked` | agent (via halt) | Halted; see §5.3. |

**Status applies to task items only.** Note items are context, not work: they carry no status, and an execution plane MUST NOT store status for them.

### 5.2 Cursor rules

1. The cursor is **always system-maintained**: it points at the first incomplete task; it advances when that task passes. The Agent MUST NOT set `in_progress`.
2. **Pass feedback contract:** on every pass write, the execution plane MUST return the new cursor (next task) and overall progress. The Agent acts on this feedback directly — it does not search for the next task and does not re-read the board in the normal path.
3. The cursor does **not** advance past a blocked task: focus stays where the work is stuck.

*Rationale for 1–2:* every derived fact the Agent must otherwise hold in working memory ("which task is next", "how far along am I") is a fact it can drop or corrupt. Moving bookkeeping into the system converts plan-following from a memory burden into a feedback loop — this is load-bearing precisely when the Agent's attention is narrow.

**Transition set.** The execution plane MUST enforce the following as the complete set of legal status transitions; anything else is rejected:

| Transition | Written by | Condition |
|---|---|---|
| `pending → in_progress` | system | cursor arrival |
| `in_progress → pass / fail / warn / blocked` | agent | outcome report |
| `blocked → in_progress` | system | halt cleared / resume condition met |
| `pending → pass / fail / warn` | agent | **off-cursor completion** — permitted, but the execution plane MUST record it as off-cursor, so audit distinguishes focused work from opportunistic completion |
| `pass / fail → pending` | Principal (or structure edit) | explicit reopen only |

`in_progress` remains system-only in every path (rule 1). Terminal states are never silently reversible.

### 5.3 Halt semantics

- **Soft halt** (`blocked` + awaited-signal record): the task waits on an external event. The halt record MUST state a machine-checkable resume condition (file appears, log line matches, time reached, job exits). Before arming a watcher on a condition, the Agent MUST check whether the condition already holds — a watcher armed after the event fires waits forever.
- **Hard halt** (`blocked` + exhaustion record): the Agent has exhausted at least three *distinct* approaches (fix in place / different method / redefine the sub-goal) and requires the Principal. The record MUST enumerate the approaches tried and the root cause hypothesis. Retrying one approach N times is one approach.
- Failure to reach a goal is an execution matter, handled here; the judgment that a goal no longer *serves the intent* is Tier T1 of the Intent Contract Specification, not a halt.

---

## 6. Cross-Board Semantics

### 6.1 Vertical: parent propagation

When every task on a child board has passed, **the system** — not the Agent — marks the parent's linked task as passed and advances the parent's cursor, recursing upward with a cycle guard. The completion feedback MUST tell the Agent which parent board is now in focus, so the Agent switches boards without pausing. The Agent MUST NOT manually mark parent tasks: cross-board bookkeeping is system work (principle 1.2 #2).

A top-level board (no parent) whose tasks are all complete enters **dormancy** (§7.3).

### 6.2 Horizontal: relay chains

Sibling boards forming a work queue are linked by a **relay directive**: a trailing note on each board naming the next board. Requirements:

1. **The directive is itself work authorization.** On completing a board (including any hand-off conditions the directive states), the Agent claims and starts the next board directly. It MUST NOT stop to ask permission at the boundary — the chain exists to eliminate that wait.
2. **Collision clause.** In multi-agent settings the directive MUST state claim semantics: before starting, write a claim marker; if the next board is already claimed by another agent, skip along the chain or halt per the directive.
3. **Tail closure.** The final board's directive MUST NOT dangle: it states where the queue ends and where the decision gate for further work lives.

### 6.3 Help requests

An Agent needing outside help (a decision, a resource, a shared credential) records a **request note** on its own board — problem, what was tried, what is needed — and halts the affected task per §5.3. Requests for *stuck* problems do not exempt the exhaustion discipline of §5.3; requests for decisions or resources may be raised directly. A supervising process routes the request; the requesting Agent does not block other tasks meanwhile.

---

## 7. Observability, Truth, and Dormancy

### 7.1 Liveness semantics

- `in_progress` + no board activity beyond a threshold ⇒ stalled: a supervising process SHOULD wake or escalate.
- `pending` items are **never** a stall signal.
- The board is the Agent's *output*, not its vital sign: a healthy-looking board is compatible with a dead agent, and vice versa. Supervisors SHOULD have at least one liveness channel that is not the board.

### 7.2 The board outranks working memory

The board is the source of truth. The Agent's working context degrades — long sessions blur, interruptions corrupt, reasoning chains hallucinate state. Whenever the Agent is unsure of a task's status, finds feedback inconsistent with its beliefs, or resumes after sleep/revival, it MUST re-read the board and recalibrate. Re-reading is an exceptional calibration act, not the normal path (§5.2 #2).

### 7.3 Dormancy vs retirement

- **Completed ≠ retired.** A fully-passed board enters **dormancy**: it stays live, and new tasks appended later re-activate the cursor and wake the Agent. Dormancy preserves the delegation relationship across work batches.
- **Retirement** (archival) is a distinct, explicit Principal decision. An Agent MUST NOT retire its own board.

---

## 8. Conformance Checklist

- [ ] C1. Authored sources carry structure only; state writes go through the execution plane; a source containing state fields is rejected or the fields ignored (§4.1).
- [ ] C2. Materialization merges by slug and preserves live state and appended structure (§4.2).
- [ ] C3. All programmatic addressing is by slug; ordinals are display-only (§3.3).
- [ ] C4. The cursor is system-maintained; agent writes of `in_progress` are rejected (§5.2).
- [ ] C5. Pass writes return next-task + progress feedback (§5.2).
- [ ] C6. Soft halts carry machine-checkable resume conditions, with the pre-armed-condition check (§5.3).
- [ ] C7. Hard halts enumerate ≥3 distinct exhausted approaches (§5.3).
- [ ] C8. Child-board completion auto-propagates to the parent, recursively, system-written (§6.1).
- [ ] C9. Relay directives carry authorization, collision, and tail-closure semantics (§6.2).
- [ ] C10. Deletion is recoverable; completed boards go dormant rather than auto-retire (§4.2, §7.3).
- [ ] C11. The execution plane enforces the §5.2 transition set; off-cursor completions are recorded as such.
- [ ] C12. Note items carry no status (§5.1).

---

## 9. Related Work (informative)

- Mishra & Sharad, *Observability for Delegated Execution in Agentic AI Systems* (arXiv:2606.09692, 2026) show that delegation-scoped execution is not recoverable from audit logs and execution traces alone, and propose an observability substrate whose information model separates an *authority graph* from an *execution graph*. This protocol's two write planes (§4) make the same separation at the plan-record level: structure (what was delegated) and state (what was done) are written through different paths and merged by slug. The two are complementary — their substrate binds delegation context at execution time; this protocol defines the plan record that context would point to. Neither attempts intent inference; intent is established separately, on the trusted channel, by the Intent Contract Specification.

---

*Part of the Trust-Layer Protocol Suite. License: CC BY 4.0. Feedback via the STL repository.*
