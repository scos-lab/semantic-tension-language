# Agent-to-Agent Communication Profiles (DRAFT)

Two community profiles that govern the STL autonomous agents write to each other, so
the vocabulary stays bounded and consumers route by field rather than by substring.

| Profile | Namespace | Covers |
|---|---|---|
| `software-agentcoord` | `Coord` | work ownership, the human loop, sequencing, lane run-reports |
| `software-review` | `Review` | gates, QA, independence, merges, patches, findings/evidence |

Grounded in a field report of live multi-agent STL traffic (scos-lab
[discussion #8](https://github.com/scos-lab/semantic-tension-language/discussions/8)):
agents converged on a shared operational envelope but sprawled everywhere the schema left
open (108 `kind` verbs, `status` doing three jobs, no `outcome`, confidence pinned at 1.0).

## The governed envelope (both profiles)

**Required on every edge:** `action` (closed enum), `priority` (int 0–3, scheduling),
`confidence` (float), `provenance` (`verified|reported|claimed|inferred`), `source`
(URL / path / `git://…@sha` / `kumidai://…` / `sha256:` — never `"memory"`), `author`,
`timestamp` (ISO-8601 UTC).

**Optional, governed:** `outcome` (`pass|fail|warn|skip|blocked|pending|no_change` — the one
machine-decision axis), `status` (free-text detail, never authoritative), `severity`
(risk, findings only), `about_phase` (see below), `certainty`, `obligation`
(`must|should|may`), `owner`/`notify`/`verifier`/`claimant` (identities), `run_id`,
`work_item`, `command`/`result`, `note`/`detail`.

## Design decisions (from the review + the maintainer's answers on #8)

- **Verb de-fused from outcome.** The speech-act is `action`; pass/fail is `outcome`.
  Never `action="gate_pass"` — write `action="gate", outcome="pass"`. This is what
  collapses the 108-verb sprawl and removes the substring hazard.
- **`kind` → `action` / `is_a`.** Per the maintainer: event verbs are `action`,
  categories are `is_a`; no bespoke `kind` field.
- **Confidence calibration.** Continuous `float(0.0,1.0)`; the six canonical levels
  (`1.0`/`0.95`/`0.8`/`0.5`/`0.2`/`0.01`) are the authoring target. `1.0` is analytic-only;
  any empirical / `reported` / `claimed` / `inferred` claim caps at `0.95`; never default a
  missing value to `1.0`. (The cap is DEFERRED to the engine branch; documented here now.)
- **`about_phase`, not `phase`.** An agent edge may carry lifecycle *as a claim*
  (`provenance="reported"`), never as a state transition — the authoritative lifecycle is
  system-owned (Board-as-Spec two planes). The field is named `about_phase` so an agent can
  never appear to move an item.
- **`validate` vs `verify`.** Two verbs: `validate` = self-check, `verify` = independent.
  Independence is made checkable by recording `verifier` and `claimant`; a validator can test
  `verifier != claimant` (Eval-Verdict V1/V3).
- **Identity registry is external.** `author`/`owner`/`verifier`/`claimant` values resolve
  against a deployment-local registry at validation time (a resolver hook), never a hardcoded
  list inside the profile — so the profile stays upstreamable.
- **Namespaced nodes.** `Coord:` / `Review:` namespaces keep node types from colliding with
  the `software-*` family in composite validation.
- **Two urgency axes.** `priority` = scheduling (who acts first); `severity` = risk (how bad
  if unhandled). Both governed, distinct.

## Cross-references (do not duplicate)

- `claim` / `release` / `handoff` / `owner` / `notify` / `obligation` mirror
  **Board-as-Spec** §6 cross-board semantics (relay-with-authorization, help requests,
  parent propagation) and the **Intent Contract** notification tier — reference, don't restate.
- `outcome` / `provenance` / `confidence` / `certainty` come from the **Eval-Verdict
  Vocabulary**; the six-level confidence scale is defined there and in STL Operational
  Protocol §5.2.

## Enforcement status

Enforced today (stl-parser 1.10.2): closed `action`/`outcome`/`provenance`/`severity`/
`obligation`/`about_phase` enums, anchor namespace + name-prefix patterns, `source` shape,
statement counts.

Deferred to the STL-TOOLS engine branch (resolver hook + cross-statement requirement rule):
1. **action-keyed edge rules** (which `action` is legal between which node types);
2. **role binding / gate satisfiability** — a `merge` gate requiring an independent
   registry-resolved `verify` fails validation, naming the missing binding, when unsatisfiable
   (this is the structural fix for the SPECIALIST_QA deadlock);
3. **confidence cap** (`1.0` analytic-only / empirical ≤ `0.95`);
4. closed modifier sets (reject unknown keys) with a warn-then-enforce sunset.

See the STL-TOOLS branch `feature/agent-comms-engine` for the resolver contract.

**These profiles are drafts** for review on discussion #8 — not yet a released standard.
