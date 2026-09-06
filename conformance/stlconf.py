"""stlconf — conformance kit for the STL trust-layer specs (v0.1).

Checks an IMPLEMENTATION against the numbered conformance items published in
  - Intent Contract Spec            (C1-C11)
  - Board-as-Spec Protocol          (C1-C19)
  - Eval-Verdict Vocabulary         (C1-C15)
plus two clauses this kit proposes, from violations measured in a live
deployment that the published checklists do not cover:
  - BOARD-C20  bounded detection lateness   (§5.3 states the MUST; no C item tests it)
  - BOARD-C21  lifecycle ops must not silently reverse Principal-set execution state

Design rules, each of which encodes a discipline the specs themselves demand:

1. Checks talk to an implementation ONLY through an Adapter. No internals.
2. Every behavioural check declares the adapter CAPABILITIES it needs. A missing
   capability yields SKIPPED, never PASSED — "couldn't test" is not "conformant".
   (Eval-Verdict V2/C8: a reading an instrument cannot produce is uninformative.)
3. Every check that can fail must be able to PASS on conformant input. Checks
   carrying a negative control record it; a check whose negative control fails is
   reported INVALID and its main result is suppressed as uninterpretable.
4. Verdicts are emitted in Eval-Verdict form. A check that only inspects a
   recorded artifact (rather than observing the behaviour) caps at `reported`,
   never `verified` (V9).
"""
from __future__ import annotations
import json, time, traceback
from dataclasses import dataclass, field, asdict

PASS, FAIL, SKIP, INVALID = "pass", "fail", "skipped", "invalid"


@dataclass
class Result:
    clause: str                      # e.g. "BOARD-C13"
    spec: str
    title: str
    status: str                      # PASS | FAIL | SKIP | INVALID
    level: str                       # A static | B behavioural | C negative-sample | D not machine-checkable
    claim: str = ""
    evidence: str = ""
    provenance: str = "reported"     # verified | reported | claimed | inferred
    negative_control: str | None = None
    detail: dict = field(default_factory=dict)
    # V10/C15: a reading taken over a SHARED, GROWING artifact is not a standing
    # property of the implementation. `corpus` describes what was scanned; the kit
    # stamps `observed_at` on every result. Measured 2026-09-04: this kit's own
    # headline moved 47%->35% with NO change to the system under test, because two
    # unrelated agents' records entered the scanned window -- the exact mechanism
    # Eval-Verdict Appendix B cites as V10's origin.
    corpus: str | None = None
    observed_at: str = ""

    def to_stl(self, subject: str) -> str:
        esc = lambda s: str(s).replace('"', "'").replace("\n", " ")
        return (f'[Verdict:{self.clause}] -> [Implementation:{subject}] '
                f'::mod(role="conformance_verdict", status="{self.status}", '
                f'provenance="{self.provenance}", level="{self.level}", '
                f'spec="{esc(self.spec)}", claim="{esc(self.claim)}", '
                f'evidence="{esc(self.evidence)}"'
                + (f', observed_at="{self.observed_at}", corpus="{esc(self.corpus)}"'
                   f', standing_property="false"' if self.corpus else "")
                + ')')


class Capability:
    BOARD_CRUD = "board_crud"          # create/read/status-write/archive a board
    CURSOR = "cursor"                  # expose the system-maintained cursor
    DETECTORS = "detectors"            # enumerate armed resume-condition detectors
    LIFECYCLE = "lifecycle"            # init / pause / inspect a session's execution state
    VERDICTS = "verdicts"           # read back outcome records written by the execution plane
    INTENT = "intent"               # read intent records and plan lineage              # read back outcome records written by the execution plane


class Adapter:
    """Implement this to submit an implementation to the kit."""
    name = "unnamed"
    capabilities: set[str] = set()

    # -- Capability.BOARD_CRUD ------------------------------------------------
    def create_board(self, board_id: str, tasks: list[str]) -> str: raise NotImplementedError
    def items(self, board_id: str) -> list[dict]: raise NotImplementedError
    def set_status(self, board_id: str, item_id: str, status: str, sub_status=None) -> dict: raise NotImplementedError
    def archive_board(self, board_id: str) -> None: raise NotImplementedError
    def append_structure(self, board_id: str, task: str) -> None:
        """Append a task to the AUTHORED source and re-materialize (C2 needs this)."""
        raise NotImplementedError
    # -- Capability.CURSOR ----------------------------------------------------
    def cursor(self, board_id: str) -> str | None: raise NotImplementedError
    # -- Capability.DETECTORS -------------------------------------------------
    def detectors(self) -> list[str]: raise NotImplementedError
    def wake_notifications(self) -> list[str] | None:
        """Notification lines delivered to THIS subject, or None if the deployment
        has not told us which channel is the subject's. Returning None yields an
        honest SKIP; guessing (e.g. newest file on disk) can silently test another
        agent's channel — measured 2026-09-02."""
        raise NotImplementedError
    # -- Capability.LIFECYCLE -------------------------------------------------
    def session_init(self, name: str, board_id: str) -> None: raise NotImplementedError
    def session_pause(self, name: str) -> None: raise NotImplementedError
    def session_autoresume(self, name: str): raise NotImplementedError
    def session_destroy(self, name: str) -> None: raise NotImplementedError
    # -- Capability.VERDICTS --------------------------------------------------
    def verdict_records(self) -> list[str]: raise NotImplementedError
    # -- Capability.INTENT ----------------------------------------------------
    def intent_records(self) -> list[str]: raise NotImplementedError
    def reinstantiated_plans(self) -> list[dict]: raise NotImplementedError
    # -- Capability.BOARD_CRUD (chains) --------------------------------------
    def create_child_board(self, board_id, parent_id, parent_item, tasks) -> str: raise NotImplementedError


_REGISTRY: list = []


def check(clause: str, spec: str, title: str, level: str, needs: tuple[str, ...] = ()):
    def deco(fn):
        fn._meta = dict(clause=clause, spec=spec, title=title, level=level, needs=needs)
        _REGISTRY.append(fn)
        return fn
    return deco


def run_all(adapter: Adapter, only: str | None = None) -> list[Result]:
    out = []
    observed_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    for fn in _REGISTRY:
        m = fn._meta
        if only and only.lower() not in m["clause"].lower():
            continue
        missing = [c for c in m["needs"] if c not in adapter.capabilities]
        if missing:
            out.append(Result(m["clause"], m["spec"], m["title"], SKIP, m["level"],
                              claim=f"adapter lacks capability {missing}; NOT evidence of conformance",
                              provenance="reported", observed_at=observed_at))
            continue
        try:
            r = fn(adapter)
            # Rule 5: a level-D clause constrains agent judgement or deployer posture,
            # not interface behaviour. It is NOT decidable by this kit, so it may record
            # an observation but MUST NOT return a verdict. A D check that returns
            # PASS/FAIL is a bug in the check, and is reported as one rather than believed.
            if r.level == "D" and r.status in (PASS, FAIL):
                r = Result(r.clause, r.spec, r.title, INVALID, "D",
                           claim=("KIT BUG: a level-D (not machine-checkable) clause returned a "
                                  f"{r.status.upper()} verdict. Original observation: " + r.claim),
                           evidence=r.evidence, provenance="reported",
                           negative_control=r.negative_control)
            r.observed_at = observed_at
            out.append(r)
        except Exception:
            out.append(Result(m["clause"], m["spec"], m["title"], INVALID, m["level"],
                              claim="check raised; result uninterpretable",
                              evidence=traceback.format_exc()[-400:], provenance="reported"))
    return out


def report(results: list[Result], subject: str, as_stl=False) -> str:
    if as_stl:
        return "\n".join(r.to_stl(subject) for r in results)
    tally = {}
    for r in results:
        tally[r.status] = tally.get(r.status, 0) + 1
    lines = [f"# stlconf conformance report — subject: {subject}",
             f"# generated: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}", ""]
    for r in results:
        mark = {PASS: "PASS", FAIL: "FAIL", SKIP: "SKIP", INVALID: "INVL"}[r.status]
        lines.append(f"[{mark}] {r.clause:<12} ({r.level}) {r.title}")
        if r.claim:
            lines.append(f"        claim: {r.claim}")
        if r.evidence:
            lines.append(f"        evidence: {r.evidence}")
        if r.negative_control:
            lines.append(f"        negative-control: {r.negative_control}")
        if r.corpus:
            lines.append(f"        corpus: {r.corpus} (observed {r.observed_at})")
            lines.append( "        NOT A STANDING PROPERTY (V10/C15): this reading is taken over a shared, "
                          "growing artifact. It can move without any change to the implementation, so it is "
                          "valid only for the corpus above at the observation time above.")
    total = len(results)
    decided = [r for r in results if r.status in (PASS, FAIL)]
    fixed = [r for r in decided if not r.corpus]
    shared = [r for r in decided if r.corpus]
    pct = lambda rs: (f"{sum(1 for r in rs if r.status == PASS)}/{len(rs)}"
                      f" ({100*sum(1 for r in rs if r.status == PASS)//len(rs)}%)") if rs else "0/0"
    lines += ["", f"# {total} checks: "
                  f"{tally.get(PASS,0)} pass / {tally.get(FAIL,0)} fail / "
                  f"{tally.get(SKIP,0)} skipped / {tally.get(INVALID,0)} invalid",
              f"# observed at: {results[0].observed_at if results else ''}",
              "#",
              "# conformance over ACTUALLY CHECKED clauses, SPLIT BY REPRODUCIBILITY (V10/C15):",
              f"#   implementation-scoped (reproducible against the impl alone): {pct(fixed)}",
              f"#   corpus-scoped (over a shared, growing artifact; MOVES ON ITS OWN): {pct(shared)}",
              f"#   combined: {pct(decided)}",
              "#",
              "# skipped clauses are NOT counted as conformant.",
              "# The combined figure is NOT citable as a standing property: the corpus-scoped",
              "# rows above are measured over records this deployment shares with other agents,",
              "# and change when they write. Cite it only with the observation time."]
    return "\n".join(lines)
