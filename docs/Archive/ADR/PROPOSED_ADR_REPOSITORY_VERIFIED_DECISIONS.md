# ADR: Reconcile architectural proposals against repository truth

Date: 2026-10-02.
Owners: [Agent rules](../../../AGENTS.md), [current architecture](../../ARCHITECTURE.md),
[implementation plan](../../IMPLEMENTATION_PLAN.md) and [completed verification](../PREVIOUS_TASK_LOG.md).

## Context

Basis: HEAD `f8165fd43e108f26863754380b486b40f27c1063`, clean worktree before edits.
The supplied proposal describes an ADR-handling workflow, not a specific application
change. No application abstraction, configuration or persistence change is justified.

Existing behavior: AGENTS already requires code-first verification, existing owners,
small changes, feature specs, consequential-change ADRs and scoped tests. Architecture
owns current boundaries; the plan owns unfinished work; TASK_LOG owns completed proof.
The accepted simplified-planning decision already separates decision acceptance from
implementation completion. At the inspected HEAD, the archived template had
status/context/decision/consequences but no explicit alternatives, affected invariants
or verification scope.

The real mechanical path is `architecture.yaml` plus the named current documents
into `scripts/check_architecture.py`: canonical hashes and owner/evidence references,
then active-document links/planning structures, then (unless `--docs-only`) static
runtime imports and bundled catalogue integrity. The checker reuses AST declarations;
it does not adopt ADRs, interpret their decisions or decide scientific validity.
Archive documents are excluded from this routine scan. The template was inspected
only because this request explicitly names it.

| Supplied assumption | Repository assessment |
| --- | --- |
| Verify claims and trace the existing owner before implementing | Correct; already required by AGENTS. |
| Reconcile the supplied proposal rather than preserve it untouched first | Sound clarification; the prior template did not express this workflow. |
| Implement the surviving decision and test changed behavior | Correct when behavior changes; this workflow needs documentation edits and existing checks, not invented application code or prose tests. |
| Status must distinguish writing from acceptance and implementation evidence | Correct; the existing planning ADR already separates acceptance from completion. |
| Use focused verification rather than automatic expensive execution | Correct; current checks protect static integrity. ADR/template links need explicit review because they are outside the routine scan. |

No concrete application proposal or stale application claim was supplied. The necessary
reconciliation is to express the workflow through existing governance owners and state
its static/manual limits, rather than introduce a new architectural subsystem.

## Decision

Extend AGENTS and consolidate guidance/template in [docs/ADR.md](GUIDANCE.md), outside
the excluded archive. Read it only for explicit ADR work or consequential decisions;
historical ADRs remain excluded. Retain
the current checker and tests; add no ADR parser, approval service, tracker or runtime
policy reader.

1. Inspect HEAD/worktree and the smallest relevant owner/configuration/flow/test set.
   Treat proposal claims as unverified, including claims of missing implementation.
2. Rewrite the proposal itself after verification. State existing behavior, the real
   remaining problem and the smallest justified decision; record rejected assumptions
   and alternatives. Do not save an untouched supplied version first.
3. Implement only that reconciled decision through the existing owner. Use behavioral
   tests for changed contracts; when no code change is justified, do not invent one.
4. Record decision status separately from delivered scope and proof. Acceptance records
   an adopted decision; it does not imply that implementation, utility or qualification
   is complete. Writing or passing checks does not automatically accept a proposal.
5. For an adopted change, update only affected current owners: AGENTS for working rules,
   Architecture for structure/boundaries, code/configuration and owning behavioral tests
   for behavior. Review the YAML projection and refresh changed canonical hashes only
   after that review. Preserve ENFORCED/TESTED/REVIEWED proof scope.
6. Put executable unfinished scope in the implementation plan. On completion, remove
   that scope and record actual verification in TASK_LOG. The ADR retains rationale,
   decision status and scoped evidence links, not an active task list or duplicate proof
   history. Read relevant ADRs/templates explicitly; do not scan archived records as
   ordinary task context.

## Alternatives

Keep the old template: smaller edit, but leaves reconciliation and evidence distinctions
implicit. Copy supplied proposals unchanged before review: preserves unsupported claims
as apparent repository truth. Add automatic ADR acceptance/schema/status enforcement:
duplicates decision authority and cannot establish semantic correctness. These alternatives
are unnecessary for the demonstrated documentation gap.

## Consequences

Proposals can resolve to a smaller change, no code change or rejection. Accepted decisions
reach existing owners without creating a second roadmap. Maintenance is limited to a short
working rule and reusable template; semantic review remains a human/agent responsibility.

## Invariants/boundaries affected

No application ownership, state, persistence, execution or scientific boundary changes.
The plan remains the sole future-work authority and TASK_LOG remains completed proof only.
Architecture remains current-state authority; YAML remains a projection. An ADR records why
a decision was made and never supplies runtime configuration or scientific evidence.
Static checks do not upgrade REVIEWED claims or certify current native qualification.

## Verification

Implemented scope: the AGENTS clarification and combined current ADR guidance/template
are present. The current guide participates in document integrity checks while archive
exclusion remains. This location correction does not add ADR acceptance automation.
Completed verification and its implementation basis are linked below.

The existing governance/declaration tests passed: 32 tests in 15.92s before edits;
their code is unchanged. Post-edit full and documentation-only architecture checks
passed for the original workflow delivery. Exact commands and proof limits are recorded
in [TASK_LOG](../PREVIOUS_TASK_LOG.md). Individual proposal contents still require explicit review;
the current guide's links are included in document checks.
No new behavior test is warranted for a documentation-only rule; existing fixture-mutation
tests protect the reused checker. No application/runtime, WSL/native, live-provider,
scientific or integration verification is required by this decision.

## Status

**PROPOSED — repository-reconciled.** The documentation implementation and its
verification are recorded separately; adoption is not inferred from writing this ADR
or passing checks. This status authorizes no additional application change.
