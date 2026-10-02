# PROPOSED ADR: capability-level planning status and evidence

Status: **PROPOSED — not adopted**. Date: 2026-10-02.
Basis: [reconciliation at f1376d6](PLAN_RECONCILIATION.md).

## Context

`docs/IMPLEMENTATION_PLAN.md` is the sole roadmap and status authority under
AGENTS.md. It currently combines historical implementation orders, current
mechanisms, conditional extensions, qualification and scientific utility into
whole-phase labels. Later delivery notes close tasks still described as open in
earlier paragraphs. Broad PARTIAL phases obscure absent code versus missing proof,
and whole-phase dependencies can turn intended build/return passes into closure
loops. The report also identifies a missing reusable dispatcher and proof writers
that a generic “acceptance remains” label does not adequately express.

## Proposed decision

Keep the existing implementation plan as the **one authoritative planning/status
document**, with unchanged phase ownership, scope and scientific requirements.
If this ADR is accepted, record status at the smallest existing capability or
acceptance obligation, using stable identities derived from H/D/R references.
Phase labels summarize those records; they do not substitute for them.

For each obligation record:

- its exact supported capability/scope, production owner and retained requirement;
- implementation state separately from local contract proof, live connectivity,
  scientific qualification/utility and current local confinement proof;
- evidence identity, code/application/input/environment basis and demonstrated
  limitations; proof at an older basis stays historical until equivalence or fresh
  proof is established;
- concrete build dependencies separately from evidence/return dependencies;
- conditional trigger and measured adopted/no-change/not-eligible result, or an
  explicit unresolved prerequisite; cancellation needs a source/scope disposition.

Each shared gate has one owning evidence record. Other phases reference it rather
than copying an experiment/checklist. DONE mechanism work reopens only for a
demonstrated defect or explicitly accepted requirement change. Missing utility
does not reopen correct scheduling code. A rejected conditional extension can
close its assessment, but cannot silently cancel an unrelated baseline capability.

Historical completed/cancelled material stays clearly non-operative and retains
recording-time evidence/Git provenance. No automatic promotion, new database,
migration, workflow engine, status service or second manually maintained tracker
is introduced. This draft does not propose new scientific work or reorder phases.

## Alternatives

1. Retain phase labels plus accumulating delivery paragraphs. This preserves
   format but retains ambiguous closure, stale work orders and repeated gates.
2. Create a separate authoritative backlog/status database. This adds a second
   truth owner and synchronization burden, conflicting with current ownership.
3. Use item-level implementation/evidence distinctions within the existing plan
   (proposed). This clarifies closure without changing roadmap authority.

## Consequences and adoption conditions

Item-level records add a small amount of maintenance but allow a reader to tell
what exists, what must be built and what merely needs qualifying. Historical
probes and generated fixtures cannot silently become current certification.

Any later conversion must account for every existing H step, D1–D8, R1–R12,
conditional gate and cancellation; preserve valid unfinished capabilities;
validate links and dependencies; and keep the plan as sole authority. The present
reconciliation is a review snapshot, not another live tracker. No conversion,
plan replacement or ownership change is authorized or performed by this ADR draft.
