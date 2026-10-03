# ADR: Rewrite Simple Implementation Plan

Status: **ACCEPTED with the changes below**. Date: 2026-10-02.
Owning document: [Implementation plan](../../IMPLEMENTATION_PLAN.md).

## Context

The active plan combines completed batches, recording-time test results, cancelled
deployment work and remaining scientific acceptance under broad phase labels.
Later delivery notes contradict earlier work orders, and shared qualification
gates recur across phases. Reading it requires familiarity with the H/D/R taxonomy.

Important: OncoLab registry pins and qualification guards
exist, while the reusable execution route required by governance has no dispatcher.
Missing qualification is different from missing implementation. The
[reconciliation](../PLAN_RECONCILIATION.md) helps recover those distinctions, but its
obligation mappings should not become permanent planning machinery. The
[previous proposal](PLAN_STATUS.md) was rejected for preserving that structure.

## Decision

Replace the contents of `docs/IMPLEMENTATION_PLAN.md` with simple, self-contained
future tasks. It remains the only future-work and planning/status authority. A fresh coding agent
must understand its task without learning the old H/D/R structure.

- Remove completed delivery narratives and historical H/D/R identifiers from the
  active plan. Git, archived documents, retained execution evidence and the permitted
  task verification log preserve history.
- Discard the phase dependency lifecycle and its build/return loops. Tasks stand
  alone or follow a straightforward sequence. Put a genuinely absent blocking
  prerequisite inside the affected task; unfinished umbrella phases are not blockers.
- At the start of work, give that task a brief feature spec: intended goal, scope,
  owning code and completion proof. Keep it within the planned task, without
  creating a separate tracker.
- New requirements become new tasks. Reopen completed work only when evidence
  disproves its original completion claim. Expansion, broader validation or a new
  utility question does not undo a correctly delivered mechanism.
- Permit one separate, non-authoritative task verification log at
  `docs/TASK_LOG.md`. It records completed task outcomes and supporting
  proof only: task, result, implementation/HEAD identity where relevant, verification
  performed, retained evidence or receipts, and known limitations and what was not
  proven. It must contain no future work, task ordering, dependencies, active planning
  status, roadmap decisions or replacement acceptance criteria.
- When a task completes, remove it from the active implementation plan and record
  its result in the verification log. Completion is judged against the task's
  acceptance criteria in the plan; the log records the outcome and proof without
  redefining those criteria. Any remaining or new work belongs in the implementation
  plan, not in the log.
- Use reconciliation only during migration. Apart from this verification-only log,
  create no permanent obligation/evidence ledger, `plan.yaml`, backlog database or
  parallel planning/status authority.
- Introduce no replacement taxonomy of letter-coded status or evidence categories.
  Describe the remaining work directly.
- Separate mechanism implementation, coding verification, scientific utility,
  admission and OncoLab qualification into bounded tasks where work remains.
  Remove contradictory instructions, circular gates, copied cross-task restrictions
  and broad approval dependencies. Each task contains its own scope and required proof.
- Rewrite `docs/ARCHITECTURE.md` as a concise description of current structure and
  ownership, and keep README focused on orientation and running the system.
  Avoid repeated explanations between them or roadmap content in either.
- AGENTS.md points agents to their assigned implementation-plan task, not the whole
  roadmap or historical reports. Exclude `docs/Archive/` and `.upstream/` from normal
  agent reading and ripgrep searches.

## Alternatives

Keep the current phase document: least editing, but retains contradictory work
orders and historical prerequisites. Refine H/D/R status records or add a tracker:
more precise accounting, but preserves the complexity that prompted rejection.

## Consequences

Less historical context and fewer interdependent pending items should save agent
time and speed development. A task can close on its own stated result instead of
waiting for broad scientific or phase approval. Scientific admission and reusable
qualification remain checks at their owning code boundaries; their unfinished work
gets explicit tasks rather than reopening unrelated mechanisms.
The verification log preserves execution history without allowing historical proof
to bloat the active plan or become a second planning authority.
`architecture.yaml` remains a current-state projection, not another roadmap.

## Migration boundary

Acceptance establishes the migration policy, not a claim that migration is done.
This edit records the decision and applies agent/search exclusions; it does not
rewrite the plan, README or architecture yet.

During the rewrite, verify remaining capabilities against code and use reconciliation
once to prevent silent loss of valid unfinished work. Simplify each carried-forward
requirement into its own task scope; retain conditional scientific work as a task
with its concrete trigger. Remove historical identifiers, contradictory instructions,
cross-task boundary repetition and dependency loops. Preserve history through
Git/archive, retained evidence and the permitted verification log, then retire
reconciliation from active use.
No runtime, database or scientific evidence changes are authorized by this migration.
