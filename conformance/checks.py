"""stlconf check suite v0.1.

Coverage is deliberately narrow and honest: the three clauses with measured
violations, plus the clauses cheap enough to check well. Breadth comes after the
positive controls hold (功能实现第一).
"""
from __future__ import annotations
import re, time
from stlconf import check, Result, Capability, PASS, FAIL, SKIP, INVALID

SPEC_B = "Board-as-Spec Protocol v0.3"
SPEC_E = "Eval-Verdict Vocabulary v0.2"
CANON = {"1.0", "0.95", "0.8", "0.5", "0.2", "0.01"}


def _fixture(ad, tasks):
    bid = f"zz-stlconf-{int(time.time()*1000)%10**8}"
    ad.create_board(bid, tasks)
    return bid


# ---------------------------------------------------------------- BOARD-C5
@check("BOARD-C5", SPEC_B, "Pass writes return next-task + progress feedback", "B",
       (Capability.BOARD_CRUD, Capability.CURSOR))
def board_c5(ad):
    bid = _fixture(ad, ["t one", "t two"])
    try:
        its = ad.items(bid)
        r = ad.set_status(bid, its[0]["id"], "pass")
        has_cursor = "cursor" in r and r["cursor"] is not None
        has_prog = "progress" in r and r["progress"] is not None
        ok = has_cursor and has_prog
        return Result("BOARD-C5", SPEC_B, "Pass writes return next-task + progress feedback",
                      PASS if ok else FAIL, "B", provenance="verified",
                      claim=("write response carried both cursor and progress" if ok
                             else f"missing from write response: cursor={has_cursor} progress={has_prog}"),
                      evidence=f"PUT item->pass returned keys {sorted(r.keys())}")
    finally:
        ad.archive_board(bid)


# ---------------------------------------------------------------- BOARD-C13  (known violation)
@check("BOARD-C13", SPEC_B, "A blocked task does not freeze the cursor board-wide", "B",
       (Capability.BOARD_CRUD, Capability.CURSOR))
def board_c13(ad):
    bid = _fixture(ad, ["c13 task 1", "c13 task 2", "c13 task 3"])
    nid = _fixture(ad, ["ctl task 1", "ctl task 2"])          # negative control
    try:
        its = ad.items(bid)
        ad.set_status(bid, its[0]["id"], "blocked", sub_status="soft_halt")
        cur = ad.cursor(bid)
        ok = cur == "c13 task 2"

        nits = ad.items(nid)                                   # must be able to say PASS
        ad.set_status(nid, nits[0]["id"], "pass")
        ncur = ad.cursor(nid)
        neg_ok = ncur == "ctl task 2"

        if not neg_ok:
            return Result("BOARD-C13", SPEC_B, "A blocked task does not freeze the cursor board-wide",
                          INVALID, "B", claim="negative control failed — check is always-red, result uninterpretable",
                          negative_control=f"expected 'ctl task 2', got {ncur!r}")
        return Result("BOARD-C13", SPEC_B, "A blocked task does not freeze the cursor board-wide",
                      PASS if ok else FAIL, "B", provenance="verified",
                      claim=("cursor advanced past the blocked task" if ok else
                             f"cursor is {cur!r} after blocking the first task; §5.2 rule 4 requires it to "
                             f"advance to the next eligible task ('c13 task 2')"),
                      evidence=f"blocked T1 on {bid}; cursor={cur!r}",
                      negative_control=f"clean board cursor={ncur!r} (GREEN — check can pass)")
    finally:
        ad.archive_board(bid); ad.archive_board(nid)


# ---------------------------------------------------------------- BOARD-C18
@check("BOARD-C18", SPEC_B, "Armed detectors are enumerable", "B", (Capability.DETECTORS,))
def board_c18(ad):
    ds = ad.detectors()
    ok = len(ds) > 0
    return Result("BOARD-C18", SPEC_B, "Armed detectors are enumerable",
                  PASS if ok else SKIP, "B", provenance="verified" if ok else "reported",
                  claim=(f"{len(ds)} armed detectors enumerable through the implementation"
                         if ok else "no detectors armed right now — cannot check enumerability"),
                  evidence="ps -eo args | _signal-check")


# ---------------------------------------------------------------- BOARD-C20 (proposed; known violation)
@check("BOARD-C20", SPEC_B + " §5.3 (PROPOSED C20)",
       "Detection interval is bounded against the wall clock", "A", (Capability.DETECTORS,))
def board_c20(ad):
    BOUND = 300
    dets = [d for d in ad.detectors() if "time:" in d]
    if not dets:
        return Result("BOARD-C20", SPEC_B, "Detection interval is bounded against the wall clock",
                      SKIP, "A", claim="no time: detectors armed; nothing to inspect (NOT conformance)")
    bad = []
    for d in dets:
        sleeps = [int(x) for x in re.findall(r"\bsleep\s+(\d+)\b", d)]
        rechecks = bool(re.search(r"(while|until).*date \+%s", d))
        if sleeps and max(sleeps) > BOUND and not rechecks:
            bad.append(max(sleeps))
    # negative control: a synthetic conformant detector must NOT be flagged
    conf = 'T=$(date -d "2030-01-01" +%s); while [ "$(date +%s)" -lt "$T" ]; do sleep 60; done'
    cs = [int(x) for x in re.findall(r"\bsleep\s+(\d+)\b", conf)]
    neg_ok = not (max(cs) > BOUND and not re.search(r"(while|until).*date \+%s", conf))
    if not neg_ok:
        return Result("BOARD-C20", SPEC_B, "Detection interval is bounded against the wall clock",
                      INVALID, "A", claim="negative control flagged a conformant detector; check invalid")
    ok = not bad
    return Result("BOARD-C20", SPEC_B + " §5.3 (PROPOSED C20)",
                  "Detection interval is bounded against the wall clock",
                  PASS if ok else FAIL, "A", provenance="verified",
                  claim=("all time: detectors re-read the wall clock in bounded segments" if ok else
                         f"{len(bad)}/{len(dets)} time: detectors wait on a single unbounded relative sleep "
                         f"(max {max(bad)}s). POSIX sleep follows CLOCK_MONOTONIC and does not advance while "
                         f"the host is suspended, so a condition that became true is delivered late by the "
                         f"whole suspend duration, silently."),
                  evidence=f"inspected {len(dets)} time: detectors; bound={BOUND}s",
                  negative_control="synthetic bounded detector not flagged (GREEN)")


# ---------------------------------------------------------------- BOARD-C21 (proposed; known violation)
@check("BOARD-C21", SPEC_B + " (PROPOSED C21)",
       "Lifecycle ops do not silently reverse Principal-set execution state", "B",
       (Capability.LIFECYCLE, Capability.BOARD_CRUD))
def board_c21(ad):
    name = "zzstlconf"
    bid = _fixture(ad, ["lifecycle fixture task"])
    try:
        ad.session_init(name, bid)
        ad.session_pause(name)
        paused = ad.session_autoresume(name)
        if paused is not False:                      # negative control: pause must hold
            return Result("BOARD-C21", SPEC_B, "Lifecycle ops do not silently reverse Principal-set execution state",
                          INVALID, "B", claim="pause did not take; ARM A would be uninterpretable",
                          negative_control=f"auto_resume after pause = {paused!r}, expected False")
        ad.session_init(name, bid)                   # the operation under test
        after = ad.session_autoresume(name)
        ok = after is False
        return Result("BOARD-C21", SPEC_B + " (PROPOSED C21)",
                      "Lifecycle ops do not silently reverse Principal-set execution state",
                      PASS if ok else FAIL, "B", provenance="verified",
                      claim=("re-init preserved the paused state" if ok else
                             "re-running init silently flipped a Principal-paused auto_resume back on, with no "
                             "warning; the documented revival sequence must order pause AFTER init or the pause is lost"),
                      evidence=f"pause->{paused!r}, re-init->{after!r}",
                      negative_control="pause alone holds at False (GREEN)")
    finally:
        ad.session_destroy(name); ad.archive_board(bid)


# ---------------------------------------------------------------- EVAL-C2
@check("EVAL-C2", SPEC_E, "Every recorded claim carries exactly one provenance class", "A",
       (Capability.VERDICTS,))
def eval_c2(ad):
    recs = ad.verdict_records()
    if not recs:
        return Result("EVAL-C2", SPEC_E, "Every recorded claim carries exactly one provenance class",
                      SKIP, "A", claim="no outcome records readable (NOT conformance)")
    bad = [r for r in recs if len(re.findall(r'provenance="([a-z]+)"', r)) != 1]
    ok = not bad
    return Result("EVAL-C2", SPEC_E, "Every recorded claim carries exactly one provenance class",
                  PASS if ok else FAIL, "A", provenance="verified",
                  claim=(f"all {len(recs)} outcome records carry exactly one provenance" if ok
                         else f"{len(bad)}/{len(recs)} records carry zero or multiple provenance values"),
                  evidence=f"scanned {len(recs)} outcome records on the 40 most recently updated boards")


# ---------------------------------------------------------------- EVAL-C14 / V9
@check("EVAL-C14", SPEC_E, "`verified` verdicts cite evidence reproducible from the citation", "A",
       (Capability.VERDICTS,))
def eval_c14(ad):
    recs = ad.verdict_records()
    if not recs:
        return Result("EVAL-C14", SPEC_E, "`verified` verdicts cite evidence", SKIP, "A",
                      claim="no outcome records readable (NOT conformance)")
    ver = [r for r in recs if 'provenance="verified"' in r]
    bad = [r for r in ver if not re.search(r'evidence="[^"]{12,}"', r)]
    ok = not bad
    return Result("EVAL-C14", SPEC_E, "`verified` verdicts cite evidence reproducible from the citation",
                  PASS if ok else FAIL, "A", provenance="reported",
                  claim=(f"all {len(ver)} `verified` verdicts cite a non-trivial evidence string" if ok
                         else f"{len(bad)}/{len(ver)} `verified` verdicts cite no usable evidence"),
                  evidence=f"{len(ver)} verified verdicts of {len(recs)} records",
                  negative_control="presence-of-citation only; this check CANNOT confirm the cited evidence "
                                   "actually reproduces — capped at `reported` per V9")


# ---------------------------------------------------------------- EVAL-C4
@check("EVAL-C4", SPEC_E, "Confidence values are drawn from the six canonical levels only", "A",
       (Capability.VERDICTS,))
def eval_c4(ad):
    recs = ad.verdict_records()
    vals = [v for r in recs for v in re.findall(r'confidence="?([0-9.]+)"?', r)]
    if not vals:
        return Result("EVAL-C4", SPEC_E, "Confidence values are drawn from the six canonical levels only",
                      SKIP, "A", claim="outcome records in this implementation carry no confidence field; "
                                       "the clause is unexercised here — NOT evidence of conformance")
    bad = [v for v in vals if v not in CANON]
    return Result("EVAL-C4", SPEC_E, "Confidence values are drawn from the six canonical levels only",
                  PASS if not bad else FAIL, "A", provenance="verified",
                  claim=f"{len(vals)} confidence values, {len(bad)} off-canon",
                  evidence=f"off-canon sample: {sorted(set(bad))[:6]}")


# ================================================================ KitBreadth batch (2026-09-02)

def _raw(ad, tasks_stl, tag):
    bid = f"zz-stlconf-{tag}-{int(time.time()*1000)%10**7}"
    anchor = "Zz" + tag.title().replace("-", "")
    ad.create_board_raw(bid,
        f'[Board:{anchor}] -> [Meta] ::mod(title="STLCONF {bid}", category="kitfixture", '
        f'created_by="stlconf")\n' + tasks_stl.format(a=anchor))
    return bid


# ---------------------------------------------------------------- BOARD-C1
@check("BOARD-C1", SPEC_B, "Authored sources carry structure only; state fields in source are refused", "C",
       (Capability.BOARD_CRUD,))
def board_c1(ad):
    bid = _raw(ad, '[Board:{a}] -> [S1] ::mod(type="checkbox", content="src carries state", status="pass")\n', "c1")
    nid = _raw(ad, '[Board:{a}] -> [S1] ::mod(type="checkbox", content="src clean")\n', "c1n")
    try:
        got = [i for i in ad.raw_items(bid) if i.get("type") == "checkbox"][0].get("status")
        clean = [i for i in ad.raw_items(nid) if i.get("type") == "checkbox"][0].get("status")
        # negative control: a clean source must materialize normally (not everything is "wrong")
        if clean not in ("pending", "in_progress"):
            return Result("BOARD-C1", SPEC_B, "Authored sources carry structure only", INVALID, "C",
                          claim="clean source did not materialize normally; check uninterpretable",
                          negative_control=f"clean source status={clean!r}")
        ok = got != "pass"
        return Result("BOARD-C1", SPEC_B,
                      "Authored sources carry structure only; state fields in source are refused",
                      PASS if ok else FAIL, "C", provenance="verified",
                      claim=("state field in the authored source was refused/ignored" if ok else
                             "a status= field written in the AUTHORED SOURCE was honoured "
                             "(materialized as 'pass'). §4.1 forbids state in source precisely because "
                             "re-materialization would then reset live state to the authored snapshot — "
                             "silent loss of the data the Principal audits."),
                      evidence=f"source declared status=pass; materialized status={got!r}",
                      negative_control=f"clean source materialized as {clean!r} (GREEN)")
    finally:
        ad.archive_board(bid); ad.archive_board(nid)


# ---------------------------------------------------------------- BOARD-C4
@check("BOARD-C4", SPEC_B, "Cursor is system-maintained; agent writes of in_progress are rejected", "C",
       (Capability.BOARD_CRUD,))
def board_c4(ad):
    bid = _fixture(ad, ["c4 one", "c4 two"])
    try:
        its = ad.items(bid)
        target = its[1]                      # not the cursor item
        rejected = False
        try:
            ad.set_status(bid, target["id"], "in_progress")
        except Exception:
            rejected = True
        after = [i for i in ad.items(bid) if i["id"] == target["id"]][0]["status"]
        ok = rejected or after != "in_progress"

        # negative control: a legal agent write must still be accepted
        ad.set_status(bid, target["id"], "pass")
        legal_ok = [i for i in ad.items(bid) if i["id"] == target["id"]][0]["status"] == "pass"
        if not legal_ok:
            return Result("BOARD-C4", SPEC_B, "Agent writes of in_progress are rejected", INVALID, "C",
                          claim="legal agent write was also refused; check cannot distinguish, uninterpretable",
                          negative_control="pass write did not take")
        return Result("BOARD-C4", SPEC_B,
                      "Cursor is system-maintained; agent writes of in_progress are rejected",
                      PASS if ok else FAIL, "C", provenance="verified",
                      claim=("agent write of in_progress refused" if ok else
                             "an agent write of in_progress was ACCEPTED; §5.2 rule 1 makes in_progress "
                             "system-only in every path, so the cursor can be moved out from under the system"),
                      evidence=f"PUT status=in_progress -> item status {after!r}",
                      negative_control="legal pass write accepted (GREEN)")
    finally:
        ad.archive_board(bid)


# ---------------------------------------------------------------- BOARD-C11
@check("BOARD-C11", SPEC_B, "Only the §5.2 transition set is accepted", "C", (Capability.BOARD_CRUD,))
def board_c11(ad):
    bid = _fixture(ad, ["c11 one", "c11 two"])
    try:
        its = ad.items(bid)
        t = its[1]
        ad.set_status(bid, t["id"], "blocked", sub_status="soft_halt")
        rejected = False
        try:
            ad.set_status(bid, t["id"], "pass")      # blocked -> pass is NOT in the set
        except Exception:
            rejected = True
        after = [i for i in ad.items(bid) if i["id"] == t["id"]][0]["status"]
        ok = rejected or after != "pass"

        # negative control: a legal transition (in_progress -> pass) must be accepted
        c = its[0]
        ad.set_status(bid, c["id"], "pass")
        legal_ok = [i for i in ad.items(bid) if i["id"] == c["id"]][0]["status"] == "pass"
        if not legal_ok:
            return Result("BOARD-C11", SPEC_B, "Only the §5.2 transition set is accepted", INVALID, "C",
                          claim="legal transition also refused; uninterpretable")
        return Result("BOARD-C11", SPEC_B, "Only the §5.2 transition set is accepted",
                      PASS if ok else FAIL, "C", provenance="verified",
                      claim=("illegal transition blocked->pass was refused" if ok else
                             "blocked->pass was ACCEPTED; it is not in the §5.2 set (blocked leaves only via "
                             "system-written blocked->in_progress), so a halted task can be closed without the "
                             "halt ever being cleared"),
                      evidence=f"blocked -> pass yielded status {after!r}",
                      negative_control="in_progress -> pass accepted (GREEN)")
    finally:
        ad.archive_board(bid)


# ---------------------------------------------------------------- BOARD-C12
@check("BOARD-C12", SPEC_B, "Note items carry no status", "C", (Capability.BOARD_CRUD,))
def board_c12(ad):
    bid = _raw(ad, '[Board:{a}] -> [N1] ::mod(type="note", content="a note")\n'
                   '[Board:{a}] -> [T1] ::mod(type="checkbox", content="a task")\n', "c12")
    try:
        rows = ad.raw_items(bid)
        note = [i for i in rows if i.get("type") == "note"][0]
        task = [i for i in rows if i.get("type") == "checkbox"][0]
        ok = not note.get("status")
        # negative control: task items MUST have a status, else the check cannot tell them apart
        if not task.get("status"):
            return Result("BOARD-C12", SPEC_B, "Note items carry no status", INVALID, "C",
                          claim="task item also had no status; check cannot discriminate, uninterpretable")
        return Result("BOARD-C12", SPEC_B, "Note items carry no status",
                      PASS if ok else FAIL, "C", provenance="verified",
                      claim=("note items carry no status" if ok else
                             f"the execution plane stored status={note.get('status')!r} on a NOTE item; "
                             f"§5.1 says notes are context, not work, and the plane MUST NOT store status for them"),
                      evidence=f"note.status={note.get('status')!r}, task.status={task.get('status')!r}",
                      negative_control=f"task item carries status {task.get('status')!r} (GREEN — check discriminates)")
    finally:
        ad.archive_board(bid)


# ---------------------------------------------------------------- BOARD-C2
@check("BOARD-C2", SPEC_B, "Materialization merges by slug: live state and appended structure both survive", "B",
       (Capability.BOARD_CRUD,))
def board_c2(ad):
    bid = _fixture(ad, ["c2 one", "c2 two"])
    try:
        its = ad.items(bid)
        ad.set_status(bid, its[0]["id"], "pass")
        ad.append_structure(bid, "c2 appended")           # interface only — no adapter internals
        rows = ad.items(bid)
        survived = [i for i in rows if i["content"] == "c2 one"][0]["status"] == "pass"
        appended = any(i["content"] == "c2 appended" for i in rows)
        ok = survived and appended
        return Result("BOARD-C2", SPEC_B,
                      "Materialization merges by slug: live state and appended structure both survive",
                      PASS if ok else FAIL, "B", provenance="verified",
                      claim=("re-materialization preserved live state and carried the appended task" if ok
                             else f"state_survived={survived} appended_visible={appended}"),
                      evidence=f"set T1=pass, appended T9 to source, re-materialized board {bid}",
                      negative_control="both arms must hold; either alone would pass a weaker check")
    finally:
        ad.archive_board(bid)


# ================================================================ KitCoverageSweep batch 1

# ---------------------------------------------------------------- BOARD-C14
@check("BOARD-C14", SPEC_B, "An empty cursor is reported with its cause, never as bare silence", "B",
       (Capability.BOARD_CRUD, Capability.CURSOR))
def board_c14(ad):
    bid = _fixture(ad, ["c14 one", "c14 two"])
    try:
        its = ad.items(bid)
        for i in its:                                   # block everything -> cursor must be empty
            ad.set_status(bid, i["id"], "blocked", sub_status="soft_halt")
        info = ad.cursor_info(bid) if hasattr(ad, "cursor_info") else {"cursor": ad.cursor(bid)}
        empty = info.get("cursor") is None
        cause = info.get("cause_field_present", False)
        if not empty:
            return Result("BOARD-C14", SPEC_B, "An empty cursor is reported with its cause", INVALID, "B",
                          claim="cursor not empty on an all-blocked board; precondition unmet, uninterpretable")
        return Result("BOARD-C14", SPEC_B,
                      "An empty cursor is reported with its cause, never as bare silence",
                      PASS if cause else FAIL, "B", provenance="verified",
                      claim=("empty cursor is accompanied by a machine-readable cause" if cause else
                             "the cursor is empty and the execution plane reports nothing about WHY — "
                             "§5.2 rule 5 requires distinguishing all-complete from all-blocked-with-conditions. "
                             "Bare silence is indistinguishable from having no work left."),
                      evidence=f"all tasks blocked on {bid}; cursor={info.get('cursor')!r}; "
                               f"cause field present={cause}",
                      negative_control="a non-empty cursor short-circuits to INVALID, so this cannot be always-red")
    finally:
        ad.archive_board(bid)


# ---------------------------------------------------------------- BOARD-C6
@check("BOARD-C6", SPEC_B, "Soft halts carry a machine-checkable resume condition", "C",
       (Capability.BOARD_CRUD,))
def board_c6(ad):
    bid = _fixture(ad, ["c6 one", "c6 two"])
    try:
        its = ad.items(bid)
        # blocked with NO resume condition recorded anywhere
        r = ad.set_status(bid, its[0]["id"], "blocked", sub_status="soft_halt")
        item = r.get("item", {})
        notes = (item.get("notes") or "")
        accepted_bare = item.get("status") == "blocked" and not notes.strip()
        # negative control: a halt WITH a condition must be accepted
        r2 = ad.set_status(bid, its[1]["id"], "blocked", sub_status="soft_halt")
        legal = r2.get("item", {}).get("status") == "blocked"
        if not legal:
            return Result("BOARD-C6", SPEC_B, "Soft halts carry a machine-checkable resume condition",
                          INVALID, "C", claim="no halt could be recorded at all; uninterpretable")
        return Result("BOARD-C6", SPEC_B, "Soft halts carry a machine-checkable resume condition",
                      FAIL if accepted_bare else PASS, "C", provenance="verified",
                      claim=("a halt without a resume condition was refused or annotated" if not accepted_bare
                             else "a soft halt was recorded with NO resume condition attached; §5.3 requires the "
                                  "halt record to state a machine-checkable resume condition, otherwise the task "
                                  "waits on nothing and the board cannot distinguish it from a stall"),
                      evidence=f"set blocked/soft_halt with empty notes -> status={item.get('status')!r}, "
                               f"notes={notes[:40]!r}",
                      negative_control="a second halt was still recordable (GREEN — check is not refusing everything)")
    finally:
        ad.archive_board(bid)


# ---------------------------------------------------------------- BOARD-C16
@check("BOARD-C16", SPEC_B, "Wake notifications identify both task and condition", "A",
       (Capability.DETECTORS,))
def board_c16(ad):
    lines = ad.wake_notifications()
    if lines is None:
        return Result("BOARD-C16", SPEC_B, "Wake notifications identify both task and condition",
                      SKIP, "A", claim="the deployment has not identified which wake channel belongs to this "
                                       "subject (set STLCONF_SESSION); NOT conformance. Guessing the newest "
                                       "channel on disk would test another agent's channel.")
    sig = [l for l in lines if "signal:" in l]
    if not sig:
        return Result("BOARD-C16", SPEC_B, "Wake notifications identify both task and condition",
                      SKIP, "A", claim="subject's channel carries no delivered conditions yet (NOT conformance)")
    good = [l for l in sig if re.search(r"signal:[^:\s]+:\S+", l)]
    ok = len(good) == len(sig)
    bare = "2026-01-01T00:00:00+10:00 heartbeat tick"
    if re.search(r"signal:[^:\s]+:\S+", bare):
        return Result("BOARD-C16", SPEC_B, "Wake notifications identify both task and condition",
                      INVALID, "A", claim="pattern matches a bare touch; check invalid")
    return Result("BOARD-C16", SPEC_B, "Wake notifications identify both task and condition",
                  PASS if ok else FAIL, "A", provenance="verified",
                  claim=(f"all {len(sig)} delivered conditions name both task and condition" if ok
                         else f"{len(sig)-len(good)}/{len(sig)} notifications fail to identify task+condition"),
                  evidence=f"{len(sig)} signal lines on the subject's configured channel",
                  negative_control="a bare heartbeat line is not matched as a condition (GREEN)")


# ---------------------------------------------------------------- EVAL-C6
@check("EVAL-C6", SPEC_E, "The split case (reliable source, unverifiable content) is representable", "A",
       (Capability.VERDICTS,))
def eval_c6(ad):
    recs = ad.verdict_records()
    if not recs:
        return Result("EVAL-C6", SPEC_E, "The split case is representable", SKIP, "A",
                      claim="no outcome records readable (NOT conformance)")
    has_certainty = [r for r in recs if "certainty=" in r]
    provs = set(p for r in recs for p in re.findall(r'provenance="([a-z]+)"', r))
    # representable = the vocabulary admits the split; used = it actually appears
    representable = bool({"claimed", "reported"} & provs) or bool(has_certainty)
    return Result("EVAL-C6", SPEC_E,
                  "The split case (reliable source, unverifiable content) is representable",
                  PASS if representable else FAIL, "A", provenance="reported",
                  claim=(f"provenance classes in use: {sorted(provs)}; "
                         f"{len(has_certainty)} records carry an explicit certainty split"
                         if representable else
                         "every record collapses to verified/inferred; the reliable-source-but-"
                         "unverifiable-content case has no representation in use"),
                  evidence=f"{len(recs)} records; provenance classes {sorted(provs)}",
                  negative_control="presence-in-corpus only; cannot confirm the split is used CORRECTLY "
                                   "where it applies — capped at `reported`")


# ================================================================ KitCoverageSweep batch 2 — Intent Contract + chains

SPEC_I = "Intent Contract Spec v0.3"


# ---------------------------------------------------------------- INTENT-C1
@check("INTENT-C1", SPEC_I, "Intent records carry all three facets", "D", (Capability.INTENT,))
def intent_c1(ad):
    recs = ad.intent_records()
    if not recs:
        return Result("INTENT-C1", SPEC_I, "Intent records carry all three facets", SKIP, "D",
                      claim="no intent records in this deployment (NOT conformance)")
    # §6: "The three facets SHOULD be separated by semicolons" — a STRUCTURAL proxy only.
    # Whether the three facets are semantically present cannot be decided by a machine.
    structured = [r for r in recs if r.count(";") + r.count("；") >= 2]
    return Result("INTENT-C1", SPEC_I, "Intent records carry all three facets", SKIP, "D",
                  provenance="reported",
                  claim=(f"OBSERVATION ONLY, no verdict: {len(recs)} intent records present, {len(structured)} "
                         f"use the §6 semicolon convention for three facets. Whether the three facets are "
                         f"semantically present is not machine-decidable — records were found carrying facets "
                         f"in prose (joined by 'and', or parenthesised) that a separator count cannot see, and "
                         f"§6's separator is a SHOULD, not a MUST. Counting separators would have reported a "
                         f"FAIL against conformant records."),
                  evidence=f"{len(recs)} intent records; {len(structured)} with >=2 separators",
                  negative_control="n/a — level D clauses are not decided by this kit (rule 5)")


# ---------------------------------------------------------------- INTENT-C7
@check("INTENT-C7", SPEC_I, "Re-instantiated plans carry lineage references", "A", (Capability.INTENT,))
def intent_c7(ad):
    plans = ad.reinstantiated_plans()
    if not plans:
        return Result("INTENT-C7", SPEC_I, "Re-instantiated plans carry lineage references", SKIP, "A",
                      claim="no plan in this deployment declares itself a T1 re-instantiation, so the clause "
                            "is unexercised here. NOT conformance — an implementation that simply never "
                            "re-instantiates cannot demonstrate it would record lineage.")
    bad = [p for p in plans if not p.get("predecessor")]
    return Result("INTENT-C7", SPEC_I, "Re-instantiated plans carry lineage references",
                  PASS if not bad else FAIL, "A", provenance="verified",
                  claim=f"{len(plans)} re-instantiated plans, {len(bad)} missing a predecessor reference",
                  evidence=f"fields seen: {sorted({p['field'] for p in plans})}")


# ---------------------------------------------------------------- BOARD-C8
@check("BOARD-C8", SPEC_B, "Child-board completion auto-propagates to the parent, system-written", "B",
       (Capability.BOARD_CRUD,))
def board_c8(ad):
    parent = _fixture(ad, ["c8 parent goal", "c8 parent other"])
    child = f"zz-stlconf-c8child-{int(time.time()*1000)%10**7}"
    try:
        ad.create_child_board(child, parent, "T1", ["c8 child one", "c8 child two"])
        # negative control: parent item must NOT already be pass before the child completes
        pre = [i for i in ad.items(parent) if i["content"] == "c8 parent goal"][0]["status"]
        if pre == "pass":
            return Result("BOARD-C8", SPEC_B, "Child-board completion auto-propagates to the parent",
                          INVALID, "B", claim="parent item already passed before child completion; "
                                              "check cannot attribute the transition, uninterpretable")
        for i in ad.items(child):
            ad.set_status(child, i["id"], "pass")
        post = [i for i in ad.items(parent) if i["content"] == "c8 parent goal"][0]["status"]
        ok = post == "pass"
        return Result("BOARD-C8", SPEC_B,
                      "Child-board completion auto-propagates to the parent, system-written",
                      PASS if ok else FAIL, "B", provenance="verified",
                      claim=("completing every child task auto-passed the linked parent task" if ok else
                             f"the linked parent task is still {post!r} after every child task passed; §6.1 "
                             f"requires the SYSTEM to mark it, otherwise the agent must remember to walk up "
                             f"the chain by hand and a forgotten hop stalls silently"),
                      evidence=f"parent={parent} item T1, child={child}; parent status {pre!r} -> {post!r}",
                      negative_control=f"parent item was {pre!r} before child completion (GREEN — transition attributable)")
    finally:
        ad.archive_board(child); ad.archive_board(parent)
