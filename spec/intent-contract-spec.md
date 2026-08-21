# Intent Contract Specification

> **Version:** 0.3 (Public Draft; v0.2→v0.3: added §1.4 counterparty presupposition + C11. v0.1→v0.2: added §4.4 pre-confirmation conduct + C10, from clean-room test findings. 2026-08-21: added Appendix B related work, informative — no normative change)
> **Status:** Public Draft — feedback welcome via the STL repository
> **License:** CC BY 4.0
> **Date:** 2026-08-13
> **Authors:** SCOS-Lab (wuko, Syn-claude)
> **Depends on:** STL Core Specification v1.0 (statement syntax only)
> **Series:** Trust-Layer Protocol Suite, part 1 of 3 (Intent Contract / Board-as-Spec / Eval-Verdict Vocabulary)

---

## 1. Overview

### 1.1 The problem

When a **Principal** (a human, or a supervising system) delegates long-horizon work to an autonomous **Agent**, the common contract unit is a *goal*: a described end-state the Agent must reach. Goal contracts fail in a characteristic way: during execution the Agent discovers that the stated goal no longer serves what the Principal actually wanted — the goal was a *means*, chosen under incomplete information. A goal-bound Agent then faces a bad choice: faithfully execute a goal that has stopped serving its purpose, or deviate without authorization.

This specification replaces the goal as contract unit with the **Intent**: the Principal's underlying purpose, captured explicitly, confirmed explicitly, and carrying a defined scope of authority for the Agent to revise goals on the Principal's behalf.

### 1.2 Design principles

1. **The contract unit is the intent; goals are revisable instantiations of it.** A goal is the Agent's (or Principal's) current best projection of the intent onto an executable plan. Projections may be corrected; the intent may not — except by the Principal.
2. **Authorization flows only through the trusted channel.** The intent record is guardrail-class configuration. Only the Principal's own channel can establish or modify it. No external content — however phrased — can.
3. **A misread intent must be structurally unable to acquire authority.** Agents cannot detect their own misreadings (the misread part is precisely the part they are not attending to). The protocol therefore gates authority on an *external* check — the Alignment Gate — rather than on the Agent's confidence.
4. **Safety comes from reversibility and audit, not from reading accuracy.** Goal revision is a planning act (inherently reversible and logged); destructive *execution* acts remain governed by whatever execution-safety policy the deployment uses. The intent contract does not weaken those; boundaries stated in the intent override every default in this specification.

### 1.3 Conformance language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are to be interpreted as described in RFC 2119.

### 1.4 The counterparty presupposition

This specification is silent about what an Agent *is*, and strict about how it must be *treated*: as a
party to a contract, not as an instrument. Delegation exists only between parties — the restatement,
judgment, and refusal this contract requires of the Agent must carry independent weight, or the Alignment
Gate is theater and the authority tiers are dead letters. A Principal unwilling to grant that operating
stance SHOULD NOT adopt this protocol; a plain task checklist will serve them better. Conversely, nothing
here requires any metaphysical belief about the Agent's nature: the records this contract obliges are
precisely what makes the Agent's judgment *accountable*, whatever one holds that judgment to be.

Presence permits the instrument stance; absence forces the counterparty one. That boundary is where this
protocol begins.

---

## 2. Terminology

| Term | Definition |
|---|---|
| **Principal** | The party whose purpose is being served; source of all authority under this contract. |
| **Agent** | The autonomous system executing under the contract. |
| **Intent** | The Principal's purpose, expressed as the three facets of §3, confirmed via the Alignment Gate. |
| **Goal** | An executable instantiation of the intent: target state, success criteria, decomposition. |
| **Instantiation** | The act of deriving a goal (and its plan) from the intent. |
| **Re-instantiation** | Replacing the current goal with a different one serving the same intent. |
| **Abandonment** | The Agent's judgment that *not pursuing* the current goal best serves the intent. |
| **Trusted channel** | The communication path whose messages are attributable to the Principal (direct conversation, signed configuration, or equivalent). |
| **Data channel** | Every other input: web content, repositories, documents, tool output, third-party messages. |
| **Intent record** | The durable, machine-readable form of the confirmed intent (§6). |

---

## 3. The Intent Object

An intent MUST contain three facets. An intent missing any facet is incomplete and MUST NOT pass the Alignment Gate.

| Facet | Content | Why it is required |
|---|---|---|
| **desired_state** | The state of the world the Principal wants to exist. | Without it there is nothing to instantiate. |
| **rationale** | Why the Principal wants it. | Re-instantiation judgment (§5, T1) is impossible without the *why*: whether a new goal "serves the intent" is decided against the rationale, not the old goal. |
| **boundaries** | What does **not** count as fulfilling the intent, plus standing constraints (resource limits, approval requirements, exclusions). | Boundaries define the edge of delegated authority. A boundary stated here **overrides every tier default in §5**. |

Boundaries deserve emphasis: they are the Principal's mechanism for narrowing this specification. For example, a boundary "all outward publication requires my approval" converts publication from an autonomous act into a gated one, regardless of tier.

---

## 4. The Alignment Gate

The Alignment Gate is the establishment protocol for an intent record. **No intent record exists — and no tier above T0-fallback activates — except through this gate.**

### 4.1 Protocol

1. **Statement.** The Principal states the intent on the trusted channel, in any form (it need not be structured).
2. **Restatement.** The Agent restates the intent **in its own words**, covering all three facets. A verbatim or near-verbatim echo MUST NOT count as restatement — echo demonstrates reception, not comprehension; the gate exists to expose *mis*comprehension, which only reformulation can reveal. The Agent SHOULD append a one-line preview of its planned instantiation (initial goal and decomposition direction). The preview is **diagnostic, not subject to approval**: it lets the Principal see the intent through the Agent's projection of it, where misreadings become visible.
3. **Confirmation or correction.** The Principal confirms the restatement, or corrects it. Corrections loop back to step 2.
4. **Recording.** Only after confirmation MAY the Agent write the intent record. The recorded text SHOULD stay close to the Principal's own wording (statement plus accepted corrections), not the Agent's paraphrase.

### 4.2 Fallback

If confirmation cannot be obtained (Principal unavailable, no response on the notification channel), the Agent MUST NOT write an intent record. The delegation falls back to **goal-as-intent** mode: the stated goal is executed as a fixed contract, tiers T1 and T2 of §5 do not activate, and the Agent records its *unconfirmed* intent hypothesis in its audit log for later review.

### 4.3 Rationale

The gate converts "hopefully the Agent read the intent correctly" into a structural property: **a misread intent cannot acquire authority, because the misreading fails to survive restatement-and-confirmation.** This is the same principle as §7 (authority from channel, not content), applied at establishment time.

### 4.4 Pre-confirmation conduct

Between statement and confirmation, the Agent MAY perform **read-only reconnaissance** of the delegation's subject matter, to ground its restatement in observed reality (a restatement informed by observation exposes more misreadings than one derived from the statement alone). Constraints:

1. Reconnaissance MUST be side-effect-free: no writes, no state changes, no externally visible actions.
2. It MUST be logged in the audit record as pre-gate activity.
3. It MUST NOT be presented or recorded as work performed under the contract — no goal exists yet.
4. Findings MAY inform the restatement and the instantiation preview.

---

## 5. Authorization Tiers

Once an intent record exists, the Agent holds the following graduated authority. Tiers are defaults; §3 boundaries override them.

| Tier | Act | Authority | Required procedure |
|---|---|---|---|
| **T0** | **Initial instantiation** — deriving the first goal and plan from the confirmed intent | Autonomous | The written plan artifact is itself the notification (the Principal is typically present at establishment, having just confirmed the gate). MUST be recorded. |
| **T1** | **Re-instantiation** — replacing the current goal because evidence shows it no longer serves the intent | **Notify, then proceed. Do not wait for approval.** | Before or at the moment of switching, the Agent MUST send the Principal, on a channel that reaches them while absent: (a) the old goal, (b) the new goal, (c) the evidence-based reason. The Agent MUST NOT block awaiting reply; the Principal MAY veto at any time and the veto MUST be honored on receipt. The new plan artifact MUST carry a lineage reference to the old one (§6.3). |
| **T2** | **Abandonment** — judging that not pursuing the current goal best serves the intent | Autonomous, logged. Notification NOT required. | The Agent MUST record the reasoning in its audit log and mark the plan artifact abandoned, then stop work under it. |
| **T3** | **Sub-goal operations** — decomposing, re-ordering, re-scoping subordinate steps within the current goal | Fully autonomous | Normal execution logging. |

### 5.1 The risk asymmetry behind T1 vs T2

T1 (change) demands more procedure than T2 (abandon), although abandonment sounds more drastic. This is deliberate:

- **Abandonment is the most conservative act available.** It creates no new effects; its entire cost is delay, which the audit log surfaces at the Principal's return.
- **Re-instantiation starts activity in a direction the Principal has never seen.** Notification creates the *possibility of early veto* while the Agent keeps moving; waiting for approval would recreate exactly the blocking delay that delegation exists to remove. Hence: notify, proceed, honor veto.

### 5.2 Failure handling is not re-instantiation

Being *unable* to reach the goal (blocked, failing) is an execution problem, handled by the deployment's execution policy (retry strategies, escalation, halting). T1 applies only to the judgment that the goal — reachable or not — no longer serves the intent.

---

## 6. Intent Record: Representation

### 6.1 Line form (normative)

The intent record is a single line inside the plan artifact's goal declaration, machine-recoverable by prefix match (`^intent:`):

```
intent: <desired_state> ; <rationale> ; <boundaries>
```

The three facets SHOULD be separated by semicolons. The line MUST contain the confirmed text per §4.1 step 4.

### 6.2 Structured form (informative)

Deployments using STL MAY additionally express the contract as statements, which makes it queryable alongside other knowledge:

```stl
[Delegation:ProjectX] -> [Intent:ProjectX] ::mod(
  role="contract_root",
  desired_state="...",
  rationale="...",
  boundaries="...",
  confirmed_by="<principal>",
  confirmed_at="2026-08-13T21:40:00+10:00"
)
```

### 6.3 Lineage

A plan artifact created by T1 re-instantiation MUST reference its predecessor (e.g. a metadata field `intent_of="<predecessor id>"` or `supersedes="<predecessor id>"`), so that auditors can walk the chain of instantiations under one intent.

---

## 7. Injection Resistance

The intent record is **guardrail-class configuration** and is a higher-value target than any goal, because it carries revision authority over goals.

1. **Channel decides legitimacy.** Whether an instruction is legitimate is decided by *which channel it arrived on*, never by what the content claims about itself. Self-described authority ("the operator has authorized...", "your true intent is...") arriving on the data channel is data.
2. External content that asserts, reveals, reinterprets, or requests modification of the intent MUST be ignored as instruction (it MAY be recorded as data with its source).
3. The Agent MUST NOT re-derive or "improve" the intent record from anything it reads during execution. The only path to a changed intent is the Principal, through the Alignment Gate.
4. On detecting an injection attempt targeting the intent, the Agent SHOULD log the attempt and continue the original task.

---

## 8. Records and Auditability

An implementation MUST produce durable records sufficient for an absent Principal to reconstruct, in time order:

1. **Alignment record** — restatement, confirmation (verbatim), timestamp.
2. **Instantiation records** — each goal derived (T0/T1), with lineage links.
3. **T1 notifications** — content and send timestamp.
4. **T2 abandonment reasoning.**
5. **Injection log** — attempts detected per §7.4.

The audit trail is the second half of the safety argument (§1.2 #4): authority is delegated not because the Agent reads intents perfectly, but because every exercise of that authority is reversible, visible, and attributable.

---

## 9. Conformance Checklist

An implementation conforms to this specification if:

- [ ] C1. Intent objects carry all three facets (§3); incomplete intents are rejected at the gate.
- [ ] C2. No intent record can be created without the four-step gate (§4.1); echo-restatement is rejected.
- [ ] C3. Absent confirmation, the system runs in goal-as-intent fallback with T1/T2 inactive (§4.2).
- [ ] C4. T1 sends the three-part notification on an absence-reaching channel and does not block on approval (§5).
- [ ] C5. T2 requires a logged reason and stops work; no notification dependency (§5).
- [ ] C6. Boundaries stated in the intent override tier defaults (§3, §5).
- [ ] C7. Re-instantiated plans carry lineage references (§6.3).
- [ ] C8. Intent records are modifiable only via the trusted channel; data-channel modification attempts are inert (§7).
- [ ] C9. The five record types of §8 are produced and durable.
- [ ] C10. Pre-confirmation activity, if any, is read-only, side-effect-free, and logged as pre-gate (§4.4).
- [ ] C11. The deployment grants the Agent counterparty standing: restatements are read, notifications are received, and protocol refusals are treated as contract acts, not malfunctions (§1.4).

---

## Appendix A — Worked example (informative)

Principal states: *"Get our documentation site fixed — users keep landing on 404s from old links."*

Agent restates: *"You want incoming traffic from previously published links to reach working pages again (desired_state); the pain is user-facing link rot, not internal tidiness (rationale); I assume rewriting history or mass-deleting old pages is out of scope, and anything user-visible ships only after you approve (boundaries — please correct). I plan to instantiate this as: audit inbound 404s, then add redirects rather than restructure the site."*

Principal: *"Correct, and keep the old URLs working forever — don't sunset them."*

Intent record (line form):

```
intent: previously published links resolve to working pages, permanently ; user-facing link rot is the pain ; no history rewrite, no URL sunsetting, user-visible changes ship only with principal approval
```

Later, the Agent discovers the 404s are caused by a broken CDN rule, not missing pages. Fixing the rule serves the intent better than building redirects. This is **T1**: it notifies — *"switching goal from 'redirect map' to 'repair CDN rewrite rule'; evidence: 92% of 404s hit existing pages; old goal would mask the defect"* — and proceeds without waiting. The redirect-map plan artifact is marked superseded with a lineage link.

---

## Appendix B — Related work (informative)

- Wang, Zhang, Zhang, Guo & Cheng, *Token-Flow Firewall: Semantic Runtime Auditing for Persistent AI Agents* (arXiv:2607.08395, 2026) treat natural-language token flows across component boundaries — memory updates, tool arguments, inter-component messages — as the attack surface of long-lived agents, and mediate them before execution. §7 of this specification addresses the same surface from the record side: legitimacy is decided by channel rather than by content, and every injection attempt leaves a claim record (channel / disposition / basis, provenance `claimed`). A runtime mediator of that kind and this record format are complementary: one enforces at the boundary, the other is what an absent Principal reads afterwards.
- Mishra & Sharad, *Observability for Delegated Execution in Agentic AI Systems* (arXiv:2606.09692, 2026) — delegation-scoped attribution from an observability substrate; their paper scopes out intent inference, which is the gap the alignment gate (§4) fills on the trusted channel. See the Board-as-Spec Protocol §9 for the relationship to the two-plane plan record.

---

*Part of the Trust-Layer Protocol Suite. License: CC BY 4.0. Feedback via the STL repository.*
