# OncoJev working rules

OncoJev is an autonomous computational oncology research system.

- Start from current HEAD/worktree. Treat prose as claims; verify relevant code,
  configuration, runtime composition, state/persistence ownership and owning tests.
- Read only the assigned task and feature spec in
  [IMPLEMENTATION_PLAN](docs/IMPLEMENTATION_PLAN.md), the sole future-work and
  planning/status authority. Use [Architecture](docs/ARCHITECTURE.md) for current
  boundaries and [README](README.md) for entry points. Find the existing owner and
  trace the real flow before changing it.
- Prefer the smallest correct change. Preserve unrelated edits and scientific
  records. New capability work needs a short feature spec in the plan: goal,
  scope, owning code, actual blockers and completion proof. Use an ADR for
  consequential architecture, ownership, state, persistence or execution changes.
- Test observable behavior and invariants, not prose/source strings. Keep fast
  checks separate from explicit WSL/native/integration verification. Run focused
  checks, `scripts/check_architecture.py` and `git diff --check`; documentation-only
  edits use `scripts/check_architecture.py --docs-only`, scope/preservation review
  and `git diff --check`. Honor narrower task-specific limits.
- Update the owning current document when a fact changes. Review the
  `architecture.yaml` projection against Architecture/AGENTS before refreshing its
  hashes; reference checks do not prove semantic boundaries or native qualification.
- On completion, remove the finished task from the plan and record outcome,
  implementation identity, verification, retained proof and limitations in
  [TASK_LOG](docs/TASK_LOG.md). The log contains completed verification only;
  keep future work and active completion criteria in the plan. Add no parallel tracker.
- Use `rg`/`rg --files` within relevant paths. Exclude `docs/Archive/` and
  `.upstream/` from normal reading, searching and indexing unless explicitly needed.
  When overriding ignore rules, retain `-g '!docs/Archive/**' -g '!.upstream/**'`.
  Historical reports are not current authority. Do not import `.upstream/` into
  runtime code or install it as application dependencies.

Report exact check results and the scope actually demonstrated.
