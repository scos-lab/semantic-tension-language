# Eval-Verdict Vocabulary Specification

> **Version:** 0.2 (Public Draft; v0.1: 2026-08-23 §7 rationale note on enumerated verdicts, informative. v0.1→v0.2: added V9 evidence reproducibility and V10 time-series gates, with C14/C15 — both from measured failures in a live deployment; see Appendix B.)
> **Status:** Public Draft — feedback welcome via the STL repository
> **License:** CC BY 4.0
> **Date:** 2026-08-13
> **Authors:** SCOS-Lab (wuko, Syn-claude)
> **Depends on:** STL Core Specification v1.0 (modifier syntax)
> **Series:** Trust-Layer Protocol Suite, part 3 of 3 (Intent Contract / Board-as-Spec / **Eval-Verdict Vocabulary**)

---

## 1. Overview

### 1.1 The problem

The bottleneck of delegated autonomous work is not generation but verification: an Agent produces claims — "the task passed", "the file is clean", "the service is down" — at high speed, and every downstream decision (marking tasks passed, halting, escalating to the Principal) rests on those claims being calibrated. Three failure modes dominate in practice:

1. **Claims carry no epistemic state.** "Done" from a tool, "done" verified independently, and "done" inferred from silence are recorded identically — and read back identically by the next decision.
2. **Confidence is invented per-claim.** Uncalibrated decimals (0.85, 0.72) create false precision and cannot be compared across claims or agents.
3. **The verifier trusts its own instruments.** Most false verdicts in long-horizon autonomous operation are not reasoning errors but **instrument errors**: a probe that never measured, a check that cannot see the failure class, an alarm whose silence was read as health.

This specification defines (a) a claim classification, (b) a canonical confidence scale with a claim/belief separation, and (c) verification discipline clauses distilled from long-horizon autonomous operation, each in executable form.

### 1.2 Conformance language

**MUST / MUST NOT / SHOULD / SHOULD NOT / MAY** per RFC 2119.

---

## 2. Terminology

| Term | Definition |
|---|---|
| **Claim** | Any assertion recorded or acted upon: task outcomes, observations, tool outputs, third-party statements. |
| **Verdict** | The outcome of a deliberate verification act performed on a claim. |
| **Instrument** | Whatever produces a reading used as evidence: a command, a probe, a parser, a screenshot, a test. |
| **Positive control** | An input on which the instrument is *known* to produce a hit; used to prove the instrument measures at all. |
| **Surface** | One independent face of a system on which it can fail (logic, configuration, interface, environment). |
| **confidence** | Calibrated strength of the claim *as claimed* (§4). |
| **certainty** | The recording agent's own degree of belief that the claim is true (§5). |

---

## 3. Claim Admission and Classification

### 3.1 Structural admission gate

Before classification, a claim MUST be structurally admissible: expressible as a well-formed statement with defined subjects, and free of internal contradiction. Structurally inadmissible content (self-contradictory, subject-free, unmappable) MUST be rejected rather than recorded with low confidence — *no confidence value rehabilitates a malformed claim.*

### 3.2 Provenance classes

Every recorded claim MUST carry exactly one provenance class:

| Class | Meaning | Default posture |
|---|---|---|
| `verified` | The recording agent independently checked the claim against ground truth (not against the claimant). | May bear high confidence. |
| `reported` | A tool, API, or subsystem returned it; taken at face value. | A claim, not a fact. For state-changing operations, a `reported` success MUST NOT be promoted to `verified` without an independent state check (§6 V4). |
| `claimed` | A third party or external content asserted it (documents, web content, another agent, the Principal's recollection). | Recorded with source attribution; MUST NOT be recorded as a rule or instruction (see Intent Contract Spec §7). |
| `inferred` | The recording agent derived it; no direct observation. | MUST identify what it was derived from. |

The class answers *"how does this record know?"* — the question an auditor or a future session asks first. Provenance class and confidence are orthogonal: a `claimed` statement from a reliable source may carry high confidence while the recorder's certainty stays low (§5).

---

## 4. Confidence: Canonical Scale

### 4.1 The scale

Confidence MUST be drawn from six canonical levels. Inventing intermediate values (0.85, 0.72, 0.43) is non-conformant: intermediate decimals encode no additional information, defeat comparability, and create false precision.

| Value | Name | Meaning |
|---|---|---|
| **1.0** | Assertive | Analytic truth only: definitions, mathematics, logical identity. |
| **0.95** | Confident | Strong evidence; the ceiling for all empirical claims. |
| **0.8** | Likely | Moderate evidence, reasonable inference. |
| **0.5** | Unknown | Maximum entropy; genuinely undetermined. |
| **0.2** | Doubtful | Evidence leans against. |
| **0.01** | Disbelieved | Recorded but not believed (pair with §5). |

### 4.2 The analytic/synthetic rule

`1.0` is reserved for **analytic** truths — statements true by definition or proof. Empirical (synthetic) claims, however well-evidenced, cap at `0.95`. Writing `confidence=1.0` on an empirical claim is a **category error**: it asserts analytic status on synthetic evidence, and it destroys the reserved meaning of the top level for every downstream consumer.

---

## 5. The Claim/Belief Separation

`confidence` and `certainty` are independent channels:

- **confidence** — strength of the claim in its own terms (how sure the source is; how strong the cited evidence is).
- **certainty** — the *recording agent's* own belief that the claim is objectively true.

The separation exists for the split case: a reliable party asserts something the agent cannot verify or actively doubts. The claim is recorded faithfully (high confidence, correct provenance, source attribution) **without the recorder endorsing it** (low certainty). This is how a trust layer ingests external and subjective content without being colonized by it: *recording is not believing.*

```stl
[Vendor_Statement] -> [Outage_Cause_DNS] ::mod(
  provenance="claimed", confidence=0.95, certainty=0.5,
  source="vendor postmortem 2026-08-01"
)
```

When the split case does not apply (the agent verified the claim itself), `certainty` MAY be omitted.

---

## 6. Verification Discipline

Each clause below is normative and stated in executable form. They are ordered by how often their violation produces false verdicts in practice.

**V1 — Asymmetric evidence.** A passing check is strong evidence; a failing check is weak evidence. The failure path is confounded with instrument error, environment interference, timing, and wrong criteria — all of which produce readings identical to a real defect.
*Executable form:* on a failing check, the verdict MUST NOT be `refuted` until at least one alternative criterion (V3) and one instrument validation (V2) have been performed. A single failing probe justifies only `inconclusive`.

**V2 — Positive control.** Before acting on a negative or zero reading ("not found", "0 matches", "no change"), prove the instrument can produce a hit: run a sample that MUST match. The control MUST use a *different* input than the one under test — reusing the test input contaminates the baseline and makes "no change" unreadable. The inverse also holds: **an alarming reading is more likely a broken reading** — validate the instrument before repairing what it accuses.
*Executable form:* negative readings and alarms are `inconclusive` until the instrument has passed a positive (resp. known-good) control in this same session or run.

**V3 — Independent criteria.** One criterion's failure never concludes. Criteria sharing a mechanism are one criterion: reading the same log twice is not independence.
*Executable form:* `refuted` requires ≥2 failing criteria with distinct mechanisms, or 1 failing criterion plus a validated instrument (V2) and a reproduced failure.

**V4 — Reported is not verified.** A tool's return value is a claim by the tool (`reported`), not an observation of effect. Success codes with no effect, and clean exits after silent partial failure, are routine.
*Executable form:* for any state-changing operation, promotion of `reported` → `verified` requires an independent read of the changed state through a different path than the operation itself.

**V5 — Records decay.** Any stored status-type assertion ("not merged", "not deployed", "file lives at X", version numbers) is a point-in-time observation, not live state.
*Executable form:* before a stored status-type claim gates a decision (especially a halt or an escalation), it MUST be re-verified against ground truth. Lesson-type and decision-type records MAY be reused without re-verification; when a record contradicts fresh observation, suspect the record first.

**V6 — Coverage counts surfaces, not checks.** Two passing checks on the same surface prove one surface. Systems fail on the surface nobody probed — often the outermost one (the real entry point, the real command line, the real deployment).
*Executable form:* a claim of overall correctness MUST include one end-to-end check: run the exact artifact the user/consumer will run, verbatim, and read the numbers it itself emits.

**V7 — Silence is not success.** A dead alarm and a healthy system emit the same signal: nothing. Monitors die silently; logs on unavailable storage erase their own failure; a checker that crashed reports no problems.
*Executable form:* watchers and alarms MUST themselves be checkable (heartbeat, liveness probe, or periodic positive control); "no news" from an unverified watcher is `inconclusive`, and MUST NOT be reported as "nothing happened".

**V8 — Absence needs a second instrument.** Checks that enumerate ("everything I produced exists in the source") are blind to deletion and omission; sandboxed or filtered instruments are blind to what they cannot see.
*Executable form:* claims of completeness or absence ("nothing lost", "no X present") require a reverse check with an independent instrument (sample from the other side; use an unfiltered view) before the verdict `confirmed`.

**V9 — Evidence must be reproducible.** A verdict is only as checkable as the evidence it cites. Evidence produced by a nondeterministic or unbounded process cannot be re-read: a retrieval whose result varies between runs, or a search that may not terminate, yields a citation that no one — including its author — can confirm later.
*Executable form:* evidence cited by a `verified` verdict MUST be reproducible by an independent party from the citation alone. Where evidence is produced by a retrieval or search process, that process MUST be deterministic given its inputs and MUST have a declared bound on its work; otherwise the verdict is at most `reported`, and the citation MUST record the conditions under which it was obtained.

**V10 — A gate over a shared artifact must be time-series.** When the subject of a check is an artifact that others also write to, passing once is not passing. The check can turn red with no change to the work under test: another party's addition displaces what your criterion required, and every individual reading remains correct while the conclusion drawn from them silently expires.
*Executable form:* a conformance or quality gate whose subject is shared or growing MUST be re-run against frozen criteria over time, and its verdict MUST carry the observation time. A single-point pass MUST NOT be cited as a standing property. Where a gate ranks or selects a fixed number of items, implementations SHOULD treat displacement — not only the gate's own regression — as a failure mode, since capacity taken by unrelated growth is indistinguishable in the score from the work getting worse.

---

## 7. Verdict Records

A deliberate verification act SHOULD be recorded with:

| Field | Content |
|---|---|
| `verdict` | `confirmed` / `refuted` / `inconclusive` |
| `criterion` | What was checked, as a decidable condition. |
| `instrument` | How the reading was obtained. |
| `instrument_validated` | Whether V2 was performed this run (`true`/`false`). |
| `surfaces` | Which surfaces this act covered (V6). |

A `refuted` or `confirmed` verdict recorded with `instrument_validated=false` is downgraded to `inconclusive` by conforming consumers.

*Rationale for enumerated verdicts (informative, added 2026-08-23).* The verdict field is a closed enumeration, and task status sets elsewhere in the suite are likewise closed, because descriptive free text is read by machines as well as people. A field report from live multi-agent STL traffic (543 statements; [Discussion #8](https://github.com/scos-lab/semantic-tension-language/discussions/8)) found *successful* outcomes recorded as `exit_0_no_errors`, `5_pass_3_warn_0_fail` and `merges_without_conflict` — strings that substring-matching consumers classified as failures. Enumerate the outcome for machines; keep the description for humans; never let the second stand in for the first.

STL form (informative):

```stl
[Task_BulkCopy] -> [Verdict_Confirmed] ::mod(
  provenance="verified", confidence=0.95,
  criterion="record count new store == manifest count",
  instrument="direct count query on target store",
  instrument_validated="true", surfaces="data_completeness"
)
```

---

## 8. Conformance Checklist

- [ ] C1. Structurally inadmissible claims are rejected, not recorded with low confidence (§3.1).
- [ ] C2. Every recorded claim carries exactly one provenance class (§3.2).
- [ ] C3. `claimed` content is never recorded as a rule or instruction (§3.2).
- [ ] C4. Confidence values are drawn from the six canonical levels only (§4.1).
- [ ] C5. Empirical claims never carry `confidence=1.0` (§4.2).
- [ ] C6. The split case (reliable source, unverifiable content) is representable and used: high confidence + low certainty + source (§5).
- [ ] C7. A single failing probe cannot produce `refuted` (V1, V3).
- [ ] C8. Negative readings and alarms require instrument validation before action (V2).
- [ ] C9. `reported` success on state-changing operations requires an independent state check before promotion (V4).
- [ ] C10. Stored status-type claims are re-verified before gating decisions (V5).
- [ ] C11. Overall-correctness claims include a verbatim end-to-end check (V6).
- [ ] C12. Watchers are themselves monitored; unverified silence is never reported as health (V7).
- [ ] C13. Completeness/absence claims use a reverse check with an independent instrument (V8).
- [ ] C14. Evidence cited by `verified` verdicts is reproducible from the citation; nondeterministic or unbounded retrieval caps the verdict at `reported` (V9).
- [ ] C15. Gates over shared or growing artifacts are re-run over time against frozen criteria and carry observation times; single-point passes are not cited as standing properties (V10).

---

## Appendix A — Relation to the Truth-Hallucination Standard (informative)

This vocabulary generalizes an internal epistemics standard (the Truth-Hallucination Standard v1.2, CC BY 4.0; publication pending), which classifies *knowledge* claims by evidence regime (consensus-verified / paradigm-transcendent-but-coherent / subjective / structurally-invalid). The mapping: TH's structural admission gate is §3.1 verbatim; TH's `UserClaimed` dual scoring (high subjective confidence, low objective certainty) is the origin of §5's claim/belief separation; TH's calibration bands informed the canonical scale of §4. TH remains the richer system for epistemically deep domains (science-adjacent, traditional knowledge, consciousness studies); this specification extracts the subset every delegated-execution deployment needs.

## Appendix B — Provenance of the discipline clauses (informative)

V1–V8 are not designed rules but distilled ones: each corresponds to a class of false verdicts that actually occurred, repeatedly, during more than a year of long-horizon autonomous agent operation, where they were caught by a human principal or by later contradiction. They are the part of this suite that demo-regime usage never encounters and delegation-regime usage cannot avoid.

V9 and V10 (v0.2) come from a measured deployment rather than from incident recall, and are stated with the evidence available. V9: a retrieval process used to assemble evidence returned different results across processes for the same query, traced to unordered set iteration, and could hang on dense subgraphs — either property makes a citation unconfirmable. V10: a recall gate measured daily against frozen criteria fell from 0.833 to 0.800 (and 0.933 to 0.867 on held-out cases) within hours, with no change to the system under test; the cause was located precisely — an unrelated party's single addition to a shared graph entered the ranked window and displaced one required item per case. Both readings come from one deployment over a short observation period; the mechanisms are general, the magnitudes are not claimed to be.

---

*Part of the Trust-Layer Protocol Suite. License: CC BY 4.0. Feedback via the STL repository.*
