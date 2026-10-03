# OncoJev working rules

OncoJev is an autonomous computational oncology research system.

- Start from current HEAD/worktree. Treat prose as claims; verify relevant code,
  configuration, runtime composition, state/persistence ownership and owning tests.
- Read only the assigned task and feature spec in
  [IMPLEMENTATION_PLAN](docs/IMPLEMENTATION_PLAN.md), the sole future-work and
  planning/status authority. Use [Architecture](docs/ARCHITECTURE.md) for current
  boundaries and [README](README.md) for entry points. Find the existing owner and
  trace the real flow before changing it.
- Within `docs/`, keep only the plan, Architecture, rolling task log and
  [current testing ADR](docs/PROPOSED_ADR_FAST_LOCAL_TESTING.md) active. Move other
  Markdown in `docs/`, including completed/retired ADRs, into `docs/Archive/`,
  preserving content and provenance. This archive rule does not apply to root,
  source, skill, evaluation or web READMEs. Add no parallel tracker.
- Prefer the smallest correct change. Preserve unrelated edits and scientific
  records. New capability work needs a short feature spec in the plan: goal,
  scope, owning code, actual blockers and completion proof. Use an ADR for
  consequential architecture, ownership, state, persistence or execution changes.
  Only for those decisions or explicit ADR tasks, exercise the archive exception to
  read [ADR guidance/template](docs/Archive/ADR/GUIDANCE.md).
- Treat supplied ADRs as proposals. Verify the owning flow and reconcile the
  proposal itself before implementing the smallest justified decision. Record
  decision status separately from implementation and proof; passing checks does
  not accept an ADR. Reflect adopted changes in the existing document owners and
  reviewed projection; keep unfinished work in the plan.
- Test observable behavior and invariants, not prose/source strings. Keep fast
  checks separate from explicit WSL/native/integration verification. Run focused
  checks, `scripts/check_architecture.py` and `git diff --check`; documentation-only
  edits use `scripts/check_architecture.py --docs-only`, scope/preservation review
  and `git diff --check`. Honor narrower task-specific limits.
- Keep routine implementation moving with focused offline checks. Do not launch
  WSL/native/provider/full-trajectory checks implicitly during a code iteration;
  schedule them explicitly for their owning qualification task and record missing
  proof in the plan. A long scientific procedure still retains its required phases
  and limits; the testing observation target is reporting, not cancellation.
- Update the owning current document when a fact changes. Review the
  `architecture.yaml` projection against Architecture/AGENTS before refreshing its
  hashes; reference checks do not prove semantic boundaries or native qualification.
- On completion, remove the finished task from the plan and record outcome,
  implementation identity, verification, retained proof and limitations in
  [TASK_LOG](docs/TASK_LOG.md). Keep only the most recent completed task and its
  immediate predecessor, newest first, with one concise level-two entry per task.
  Before adding a third entry, append the displaced entry intact to
  [Previous Task Log](docs/Archive/PREVIOUS_TASK_LOG.md); never discard completed proof.
  The rolling log contains completed verification only; avoid copied investigation
  reports, repeated history or active completion criteria. Keep future work in the
  plan. The architecture checker enforces the active layout and two-entry limit.
- Use `rg`/`rg --files` within relevant paths. Exclude `docs/Archive/` and
  `.upstream/` from normal reading, searching and indexing. Exercise a scoped exception
  without asking permission when the assigned task needs historical evidence, ADR
  guidance or log rotation; name the reason and read only the needed files. History
  is not current authority, and rotating the log does not require a history-wide scan.
  When overriding ignore rules, retain `-g '!docs/Archive/**' -g '!.upstream/**'`.
  Historical reports are not current authority. Do not import `.upstream/` into
  runtime code or install it as application dependencies.

Report exact check results and the scope actually demonstrated.
