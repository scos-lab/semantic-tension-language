# Board-as-Spec Protocol

> **Version:** 0.3 (Public Draft; v0.1→v0.2: added §5.1 note-status rule, §5.2 transition set + C11/C12, from clean-room test findings. 2026-08-21: added §9 related work, informative. v0.2→v0.3: **corrected §5.2 cursor eligibility** (a blocked task no longer freezes the board — see §5.2 rules 3–5); added §5.4 standing items and ticks, §5.5 wake notification semantics, §5.6 outcome records, §6.4 intra-board ownership, §7.1 wake-channel rules, C13–C19. Sources in Appendix A.)
> **Status:** Public Draft — feedback welcome via the STL repository
> **License:** CC BY 4.0
> **Date:** 2026-08-13
> **Authors:** SCOS-Lab (wuko, Syn-claude)
> **Depends on:** STL Core Specification v1.0 (statement syntax); Intent Contract Specification v0.2 (§3 goal declaration); Eval-Verdict Vocabulary Specification v0.2 (§5.6 outcome records)
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

1. The cursor is **always system-maintained**: it points at the first *eligible* task (rule 3); it advances when that task passes. The Agent MUST NOT set `in_progress`.
2. **Pass feedback contract:** on every pass write, the execution plane MUST return the new cursor (next task) and overall progress. The Agent acts on this feedback directly — it does not search for the next task and does not re-read the board in the normal path.
3. **Eligibility.** The cursor selects the first task that is *actionable now*: status `pending`, not standing (§5.4), not owned by a different Agent (§6.4), and not awaiting an unmet resume condition. Tasks in `blocked`, `fail`, `warn`, or `pass` MUST NOT be selected, and an Agent MUST NOT be handed one as its next action.
4. **A blocked task MUST NOT freeze the board.** Tasks waiting on a future signal are normal and long-lived. If any single soft halt suspended cursor advancement board-wide, a board with one date-blocked task and ten ready tasks would present as having no work — indistinguishable from a finished board, with no error raised. The cursor therefore skips blocked tasks and continues past them; it is the *halt record* (§5.3), not cursor position, that keeps a stuck task from being forgotten.
5. **An empty cursor is a reportable state, not silence.** When no task is eligible, the execution plane MUST report which case holds: all tasks complete (→ dormancy, §7.3), or all remaining tasks blocked — in which case it MUST list their resume conditions. "No cursor" and "nothing to do" MUST NOT be indistinguishable to the Agent.

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
- **Bounded detection lateness.** A resume condition that has become true MUST eventually be delivered, and the implementation's detection interval MUST be bounded and declared. Polling granularity is the lateness bound: a time-based condition checked on a 30-minute cycle is up to 30 minutes late, and that lateness is a property of the deployment, not an accident of it. Implementations MUST NOT let a coarse poll silently swallow a deadline the halt record states precisely.
- **Recurring conditions.** A condition that recurs on a calendar SHOULD be expressed as an idempotent guard — a predicate that is true only when the period has arrived *and* no completion marker exists for that period — rather than by adding a calendar/cron kind to the resume-condition vocabulary. A one-shot watcher plus a period marker yields exactly-once-per-period behaviour, is safe to re-arm at any time, and keeps the condition vocabulary small.
- Failure to reach a goal is an execution matter, handled here; the judgment that a goal no longer *serves the intent* is Tier T1 of the Intent Contract Specification, not a halt.

### 5.4 Standing Items

Not every responsibility terminates. "Handle inbound correspondence as it arrives" is real, delegated, auditable work that has no completion criterion — it ends when the engagement ends, not when a task is done. A protocol with only terminating tasks forces such work to be either mis-modelled as a task that never passes (which, under a naive cursor, blocks the board forever) or kept outside the record entirely (which defeats the point of the board).

A task MAY be declared **standing**. Requirements:

1. A standing task is never selected by the cursor (§5.2 rule 3) and never reaches a terminal status through ordinary execution. It is closed only by an explicit structure edit when the responsibility ends.
2. Each discharge of a standing responsibility is a **tick**: an appended outcome record (§5.6) stating what was handled and when. The task's status does not change; the ticks accumulate.
3. Ticks MUST be individually addressable and ordered, so "what was done under this responsibility, and when" is answerable without reading prose.
4. A board whose only incomplete tasks are standing is **not** complete: it MUST NOT enter dormancy (§7.3) on that basis, and an execution loop MUST NOT exit on the grounds that every terminating task has passed.

### 5.5 Wake Notification Semantics

When a resume condition fires, the notification delivered to the Agent MUST identify **which task** and **which condition** fired. Requirements:

1. **Structured, not prose.** The notification carries the task's slug and the condition that matched. A bare "something happened" cannot be routed: the Agent cannot tell which of several outstanding halts it refers to, and must fall back on guessing or re-reading everything.
2. **A notification is not a signal.** Wake channels are shared with liveness pings, scheduler heartbeats, and supervisory pokes. An implementation MUST distinguish *a condition fired* from *the channel was touched*; a bare touch MUST NOT be interpretable as any specific resume condition. Absent this, a routine heartbeat is read as an event that never happened.
3. **Delivery MUST survive a busy Agent.** A condition that fires while the Agent is occupied MUST still be delivered when it becomes free. Implementations MUST compare against the last *consumed* notification, not against "everything from now on" — the latter drops precisely the events that arrive during work.
4. **Re-arming.** Where detection is one-shot, the detector MUST be re-armed after handling; an implementation SHOULD make re-arming automatic rather than a step the Agent must remember. A detector that fires, exits, and is not re-armed leaves an observation surface that is silently gone — the board still lists the halt, and nothing reports that nothing is watching it.

### 5.6 Outcome Records

Every terminal status write (`pass` / `fail` / `warn`) and every standing tick (§5.4) MUST carry an **outcome record** conforming to the Eval-Verdict Vocabulary Specification: the claim, its provenance class, and the evidence relied on.

1. **The record is written by the execution plane, not narrated by the Agent.** The Agent supplies the structured outcome; the plane writes the record. An Agent's prose self-report is not an outcome record — a verdict derived from the reporting party's narration inherits whatever that narration got wrong, which is the failure mode the record exists to catch.
2. **Handled wakes leave a trace.** Discharging a resume condition (§5.5) MUST leave a durable, queryable record linking the condition, the task, and the outcome. "This task was woken by that condition at that time and this is what came of it" is the minimum audit unit for delegated work that ran unattended.
3. Implementations adopting this section against an existing corpus MAY accept records-absent writes during a migration period, but MUST surface them as non-conforming rather than accept them silently.

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

### 6.4 Intra-board ownership

§6.2 governs collisions *between* boards. Within a single board, more than one Agent may legitimately be at work: a long-running executor holding the goal, and a separate process discharging a standing responsibility (§5.4) declared on the same board. Where an execution plane permits this, a task MAY declare an **owner**. Requirements:

1. Only the owning Agent selects that task, arms its resume conditions, and writes its outcome records. Non-owners MUST skip it — for cursor purposes it is treated as ineligible (§5.2 rule 3), not as available work.
2. An implementation MUST make non-ownership visible when an Agent attempts to arm or claim another's task, rather than failing silently or arming a duplicate detector.
3. Ownership is a routing declaration, not an authorization boundary: it says who acts, not who may. Authorization remains governed by the Intent Contract Specification.

---

## 7. Observability, Truth, and Dormancy

### 7.1 Liveness semantics

- `in_progress` + no board activity beyond a threshold ⇒ stalled: a supervising process SHOULD wake or escalate.
- `pending` items are **never** a stall signal.
- The board is the Agent's *output*, not its vital sign: a healthy-looking board is compatible with a dead agent, and vice versa. Supervisors SHOULD have at least one liveness channel that is not the board.
- **Detection surfaces are themselves state that can die.** Resume-condition detectors (§5.5) typically live in the Agent's process or session and do not survive its death. A revived Agent MUST be able to rebuild the full set of detectors from the board's declarations alone, and doing so SHOULD be a single idempotent operation — not a checklist the Agent's replacement is trusted to reproduce from memory or from a hand-written note.
- **A missing detector reports as silence.** Nothing distinguishes "no event occurred" from "nothing was watching"; both are quiet. Implementations SHOULD therefore make detector state enumerable — answering *what is currently being watched* — so the absence of watchers is observable without waiting for an event that will never be reported.

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
- [ ] C13. The cursor selects only actionable tasks; blocked/fail/warn/pass tasks are never handed to an Agent, and a blocked task does not suspend cursor advancement board-wide (§5.2).
- [ ] C14. An empty cursor is reported with its cause — all-complete vs all-blocked-with-conditions — never as bare silence (§5.2).
- [ ] C15. Standing tasks are cursor-exempt, accumulate addressable ticks, and do not make a board eligible for dormancy (§5.4).
- [ ] C16. Wake notifications identify task and condition; a bare channel touch is not interpretable as a condition; delivery survives a busy Agent (§5.5).
- [ ] C17. Terminal writes and ticks carry outcome records conforming to the Eval-Verdict Vocabulary, written by the execution plane rather than narrated by the Agent (§5.6).
- [ ] C18. Detectors are rebuildable from board declarations by a single idempotent operation, and the current detector set is enumerable (§7.1).
- [ ] C19. Owned tasks are acted on only by their owner, and non-ownership is surfaced rather than silently ignored (§6.4).

**Backend-independence check (SHOULD).** An implementation claiming conformance SHOULD demonstrate that the same board, executed by different model backends, produces outcome records with the same field set and the same status on mechanically-checkable tasks. The protocol's value proposition is that the plan record — not the model — carries the work across sessions and agents; that claim is testable, and untested it is only an assertion.

---

## 9. Related Work (informative)

- Mishra & Sharad, *Observability for Delegated Execution in Agentic AI Systems* (arXiv:2606.09692, 2026) show that delegation-scoped execution is not recoverable from audit logs and execution traces alone, and propose an observability substrate whose information model separates an *authority graph* from an *execution graph*. This protocol's two write planes (§4) make the same separation at the plan-record level: structure (what was delegated) and state (what was done) are written through different paths and merged by slug. The two are complementary — their substrate binds delegation context at execution time; this protocol defines the plan record that context would point to. Neither attempts intent inference; intent is established separately, on the trusted channel, by the Intent Contract Specification.

---

## Appendix A — Provenance of the v0.3 clauses (informative)

Every clause added in v0.3 came from an implementation running the protocol unattended, not from design review. Each is listed with the observation that produced it and the strength of that evidence, so implementers can weigh clauses by the evidence behind them rather than by their tone.

| Clause | Observation | Evidence strength |
|---|---|---|
| §5.2 r3–5 (cursor eligibility; blocked does not freeze) | Two independent failures. A loop handed a hard-halted task to a model as its next action — a class of task that could not appear on the toy boards it had been developed against. Separately, a reference implementation was found to suspend cursor advancement whenever *any* task was blocked; a board carrying three date-blocked tasks presented as having no work for two days, with progress and health indicators normal throughout, and execution continued only because a human-written hand-off note said what to do. | Verified; both reproduced by code inspection and direct observation |
| §5.4 standing items | A standing "handle inbound as it arrives" task on a live board had no representation: it could not pass, and every implementation invented its own convention for recording that it had been serviced. Tick semantics validated on a positive-control board and on one live daily responsibility discharged unattended. | Verified (single responsibility, ~1 day) |
| §5.5 wake semantics | (1) Prose-formed wake text proved unroutable and, used as a retrieval seed, scored at noise level. (2) A scheduler heartbeat touching the wake channel was consumed as a resume condition, aborting a wait. (3) A condition firing while the model was busy was dropped by a wait that compared "from now" rather than against last-consumed. (4) A one-shot detector that fired and was not re-armed left an unwatched channel for ~4 hours; the event it should have caught was reported by a human first. | Verified; (1),(4) first-hand incidents |
| §5.3 bounded lateness | A time condition due at 18:02 was not delivered until the next 30-minute poll, because the pre-computed sleep ended fractionally early and fell into a coarse polling loop. Post-fix delivery: 1–2 s, across four runs. | Verified |
| §5.3 recurring guard | Daily responsibility implemented as one-shot detector + period marker; fired while the model was busy, re-armed, and correctly declined to fire again the same period. | Verified (single period) |
| §5.6 outcome records | Structured outcome writes on a test board (5/5) and 16 unattended terminal writes across four runs, in which the record was composed by the loop from a structured decision rather than from the model's prose. | Verified |
| §6.4 ownership | One board shared by an interactive executor and an unattended loop; an ownership declaration kept each from arming the other's detectors, confirmed by the executor's channel showing no traffic for the other's task. | Verified (n=1 pairing) |
| §7.1 detector rebuild | A full machine restart destroyed all detectors; on revival a single idempotent command rebuilt 11 of 11 from board declarations, verified at process level rather than by return value. | Verified (n=1 restart cycle) |
| Backend-independence check | Same board and same memory state executed by two different model families, twice each: identical verdict field sets, identical statuses, same task order and wait→wake path; differences confined to wording and turn count. | Reproduced, at toy-task granularity — a deliberately weak claim: the boards were small enough that a capability gradient between backends would not show. Stated as SHOULD for this reason. |

Two findings from the same source were **not** adopted, and are recorded here because the boundary matters more than the findings. A measured context-assembly token budget, and a method for compiling procedural dependencies into a memory graph, were both well-evidenced but describe how a particular agent's memory is tuned — not what two implementations must agree on to interoperate. This protocol specifies the plan record; it does not specify the Agent's memory architecture, and a clause that cannot be checked between two independent implementations does not belong in it.

---

*Part of the Trust-Layer Protocol Suite. License: CC BY 4.0. Feedback via the STL repository.*
