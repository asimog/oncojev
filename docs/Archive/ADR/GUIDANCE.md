# ADR guidance and template

Read this document only for explicit ADR work or a consequential architecture,
ownership, state, persistence or execution decision. Routine tasks use their
assigned plan feature spec and current architecture instead.

ADRs record proposals, decisions and rationale. Reconcile claims against current
code before implementation. Acceptance is explicit and is separate from delivered
scope and qualification. Update affected current owners; keep future work in
IMPLEMENTATION_PLAN and completed verification in the two-entry rolling TASK_LOG.
Append displaced older entries intact to `docs/Archive/PREVIOUS_TASK_LOG.md`.
The checker verifies
static integrity; it does not accept ADRs or prove their semantic correctness.

Historical ADRs remain in `docs/Archive/ADR/` and are excluded from routine reading
and scans. Read them only when their history is explicitly relevant. This guide
and template are archived too; AGENTS permits a scoped exception for explicit ADR
work, consequential decisions and historical proof. No repeated user approval is
needed for that exception, and archived material is not current architecture.

## Template

```markdown
# ADR: <decision title>

Date: YYYY-MM-DD.
Owning document(s): <link to existing current authorities>.

<Start from HEAD/worktree and verify the affected owner, configuration/input flow
and tests before saving the reconciled proposal. Rewrite unsupported claims in the
proposal itself; do not first save an untouched supplied version. Use this template explicitly for ADR work; it is not another
current-state or planning authority.>

## Context

<Verified HEAD/worktree basis. Existing behavior and owner; real remaining problem.
Identify correct, partial, stale/false assumptions, already implemented behavior
and reusable mechanisms. Trace the affected flow; flag ownership conflicts.>

## Decision

<Smallest justified change and reason, distinguished from existing behavior. Extend
the current owner. If no code change is needed, say so. Do not describe planned
behavior as implemented. An ADR does not become configuration or a roadmap.>

## Alternatives

<Relevant options, including retaining/extending the existing mechanism or no change,
and why they were rejected. Do not redesign because the supplied proposal suggested it.>

## Consequences

<Concrete benefits, costs, coupling/drift risks and limits. Keep unfinished execution
scope in IMPLEMENTATION_PLAN and completed proof in TASK_LOG; link instead of copying
their task/status/evidence history.>

## Invariants/boundaries affected

<Owners, authority/state/persistence/execution boundaries preserved or changed.
Name the current documents, code/config and behavioral tests that own those facts.
For adopted changes, align affected owners and review architecture.yaml before
refreshing canonical hashes. Preserve ENFORCED/TESTED/REVIEWED scope; static integrity
does not prove semantics or scientific/native qualification.>

## Verification

<Actual commands/results, implementation basis and retained evidence links; state
what was not verified. Test changed behavior/invariants, not prose/source strings.
Use the repository environment, focused owning tests where applicable,
scripts/check_architecture.py and git diff --check. Documentation-only changes can
use --docs-only plus explicit ADR/template link and scope review. Run expensive
WSL/native/provider/integration checks only when the decision depends on them.>

## Status

<Choose PROPOSED / ACCEPTED / REJECTED / SUPERSEDED; record the actual decision and
its basis/date, linking a superseding ADR if applicable. Separately state delivered
implementation scope and supported/unproven evidence. Writing or passing checks
does not imply acceptance; acceptance does not imply implementation completion.
An unresolved proposal is PROPOSED; rejected proposals authorize no work.>
```
