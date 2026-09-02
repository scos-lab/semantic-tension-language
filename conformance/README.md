# stlconf — a conformance kit for the STL trust-layer specifications

Checks an implementation against the numbered conformance items published in
[`spec/intent-contract-spec.md`](../spec/intent-contract-spec.md),
[`spec/board-as-spec-protocol.md`](../spec/board-as-spec-protocol.md), and
[`spec/eval-verdict-vocabulary.md`](../spec/eval-verdict-vocabulary.md).

**Status: v0.1. 20 checks over 45 published clauses.** Narrow on purpose — see
*Coverage, honestly* below, and note what the numbers are *not* saying.

## Why this exists before a reference implementation

We wrote three specifications out of a year of running an agent on unattended,
long-horizon work. Then we ran this kit against our own implementation — the one
the specs were extracted from.

**It fails 9 of the 17 clauses the kit can currently check.**

That result is published here unedited, in [`SELF-RUN.txt`](SELF-RUN.txt), because
it is the single most useful thing we know about these specs. Every one of those
seven was found at runtime, none by reading code, and each failure mode is shaped
exactly like normal operation:

| Clause | What the implementation actually does |
|---|---|
| `BOARD-C13` | Any blocked task freezes the cursor board-wide; the board looks idle, not stuck |
| `BOARD-C1`  | A `status=` written in the **authored source** is honoured, though §4.1 forbids state in source |
| `BOARD-C4`  | An agent can write `in_progress` directly, moving the cursor out from under the system that owns it |
| `BOARD-C11` | `blocked → pass` is accepted; a task whose halt was never cleared can be closed |
| `BOARD-C12` | Note items are stored with a `status`, which §5.1 forbids |
| `BOARD-C20` | `time:` detectors wait on one unbounded relative sleep — late by the whole suspend duration, silently |
| `BOARD-C21` | Re-running session init silently re-enables an operator-paused execution loop |
| `BOARD-C14` | When the cursor is empty the plane reports nothing about why — bare silence is indistinguishable from having no work left |
| `BOARD-C6`  | A soft halt is recorded with no resume condition attached, so the task waits on nothing |

A specification whose own reference implementation quietly violates it is worse
than no specification, because it teaches the violation. That is the entire
argument for shipping the checker before the implementation.

## Two clauses this kit proposes

`BOARD-C20` and `BOARD-C21` are **not** in the published checklists. They come from
failures measured in live operation that the existing 45 items do not cover —
`§5.3` states bounded detection lateness as a MUST but no conformance item tests
it, and nothing at all covers a lifecycle operation reversing operator-set state.

That gap is itself the finding: **a clause can exist and still be unenforceable, and
then its violations are invisible.** Both are proposed for the next spec revision.

## Design rules (each one is a discipline the specs demand of implementations)

1. **Checks talk to an implementation only through an `Adapter`.** No internals, so
   a check is portable to any implementation exposing the same interface.
2. **A missing adapter capability yields `SKIP`, never `PASS`,** and skipped clauses
   are excluded from the conformance denominator. *Could not test* is not *conformant*.
3. **Every check carries a negative control.** A check that cannot report GREEN on
   conformant input is always-red and therefore worthless; when its negative control
   fails, the check reports `INVALID` and its main result is suppressed as
   uninterpretable rather than believed.
4. **A check that only inspects a recorded artifact caps at `provenance="reported"`,**
   never `verified` (Eval-Verdict V9). `EVAL-C14` says outright that it cannot confirm
   the evidence it cites actually reproduces.
5. **A clause that is not machine-checkable may record an observation but MUST NOT
   return a verdict.** Ten of the forty-five constrain an agent's judgement or a
   deployer's posture rather than interface behaviour. The runner enforces this: a
   level-D check returning PASS or FAIL is coerced to `INVALID` and reported as a bug
   in the check. This rule exists because we wrote such a check and it was wrong — a
   separator-counting proxy for "carries three facets" reported FAIL against intent
   records that carried their facets in prose.

## Coverage, honestly

    20 checks: 8 pass / 9 fail / 3 skipped / 0 invalid
    conformance over ACTUALLY CHECKED clauses: 8/17 (47%)

**47% is not this implementation's conformance rate.** It is the pass rate over the
seventeen clauses the kit currently checks, out of forty-five published. The other
twenty-eight are untested, and by rule 2 untested is not conformant. Ten of the
forty-five are not machine-checkable at all — they constrain an agent's judgement or
a deployer's posture, not interface behaviour — and for those the kit can only record
whether evidence exists, never whether it is sound.

## Running it

    python3 run_kit.py            # human-readable report
    python3 run_kit.py --stl      # Eval-Verdict records
    python3 run_kit.py --only C13 # one clause

Configure the reference adapter through the environment; nothing is baked to one
machine: `STLCONF_API`, `STLCONF_BOARDS_DIR`, `STLCONF_SOLO_HOME`, `STLCONF_SESSION`.

`STLCONF_SESSION` names the wake channel belonging to the subject. Leave it unset and
the notification check reports SKIP rather than guessing — picking, say, the most
recently modified channel on disk would silently test *another agent's* channel and
report the result as if it were the subject's. That bug was live in this kit until
2026-09-02.

## Submitting your own implementation

Subclass `Adapter` in `stlconf.py`, declare the `Capability` values you support, and
pass it to `run_all`. Capabilities you do not declare are skipped rather than failed,
so a partial implementation gets a partial — and honest — report.

We would rather see a low score reported accurately than a high one produced by a kit
that could not fail. If a check passes against an implementation you know to be
non-conformant, that is a bug in the check and we want the report.
