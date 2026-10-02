# Task Log

Completed verification only. Keep the most recent completed task and its immediate
predecessor, newest first; append displaced entries intact to
[Previous Task Log](Archive/PREVIOUS_TASK_LOG.md). The architecture checker rejects
a third level-two entry. Future work belongs only in IMPLEMENTATION_PLAN.

## 2026-10-02 — Implement reconciled isolated fast local testing

Result: Adopted the accepted ADR through existing config, paths, service, resource,
identity and qualification owners. Installed typed timing/data caps, frozen startup
policy/paths/content identity, process UUID isolation, linked-store denial, data-only
accounting with ordinary local software reservations, owned Docker scratch paths and
safe elapsed/profile logs. Routed the direct live script through the service; the
phase-3 demo retains explicit mixed providers. Enabled `ONCOJEV_TESTING=1` in ignored
`.env.local` without changing other contents; `.env.example` defaults to `0`.
Short offline checks and explicit long/native/live qualification now have separate
working guidance. Completed implementation slice removed; outstanding native/live
assessment remains scoped to existing Tasks 2 and 12.

Basis: clean HEAD `d791ee8a204706bbda3c5d19f95607588eb8fb68`; this task's commit
contains the implementation and retained proof. Runtime/config/scripts diff SHA256:
`55a65c63e575874d3b263b73cb41a33b1aeb2091f5593cd5364df972ffff58b5`.
Proof: [testing ADR reconciliation](PROPOSED_ADR_FAST_LOCAL_TESTING.md#implementation-reconciliation-report--2026-10-02),
[Architecture](ARCHITECTURE.md), current test owners and reviewed projection.
The displaced previous entry is appended intact to the archive; the immediate
predecessor below is preserved. No scientific records were edited.

Checks: with process `ONCOJEV_TESTING=0` and `LOGFIRE_SEND_TO_LOGFIRE=false`:

- `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider -o addopts='' tests/invariants/test_live_mode.py tests/invariants/test_boundaries.py tests/invariants/test_persistence.py tests/invariants/test_native_setup.py tests/invariants/test_architecture_checks.py -q --durations=8`: 226 passed, one dependency event-loop deprecation warning, 150.98 s. Before the final refinement restricting metadata reservations to testing only.
- Final `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider -o addopts='' tests/invariants/test_live_mode.py tests/invariants/test_boundaries.py tests/invariants/test_persistence.py -k testing -q --durations=5`: 25 passed, 156 deselected, 14.35 s.
- Final `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider -o addopts='' tests/invariants/test_live_mode.py tests/invariants/test_boundaries.py -q --durations=5`: 81 passed, one dependency warning, 38.64 s.
- `.venv/Scripts/python.exe -B scripts/check_architecture.py` and `git -c core.safecrlf=false diff --check`: passed, exit 0. AST syntax review: 20 changed Python files passed. Plan preservation review: original tasks/conditional specs unchanged except two explicit outstanding-proof additions. `.env.local` remains ignored and other contents were hash-checked unchanged.

Scope: real service/factory/pins/store cycles with scripted model responses; config
and fake-clock handoff; GDC/Xena mock streams with failed-byte charging; software
reservation after data exhaustion; process UUID continuity/freshness; Windows
junction/store denial; otherwise complete testing qualification rejected while
admitted evidence remains retained; Docker owned-parent/replay/cleanup contracts.
Limits: no live provider calls, WSL2/kernel probes, native scientific execution,
measured research utility, complete two-minute live trajectory or reusable method
qualification. No importer, authority transfer or run-root deletion. Docker's
existing transfer accounting is retained, not newly qualified. Required scientific
procedures and the 300 s scheduled-review path keep their ordinary limits.

## 2026-10-02 — Correct research-plan reconciliation after adversarial audit

Result: Kept configured-budget OncoLab recall measurement in Task 3 and bounded
canonical retrieval repair in Task 11. Publication now activates on a selected
deliverable; isolated publisher setup, connectivity and remote SHA proof remain
work/completion requirements. Corrected the research ADR and Architecture to identify
Linux Coder's inherited result clearing, warnings, output truncation and argument
repair. Research ADR remains PROPOSED; fast-testing ADR remains ACCEPTED in docs
with Task 17 absent. No runtime capability was implemented.

Basis: HEAD `b27a6b220cd183bd51aff06aec8b8f778187d1b1` plus the prior documentation
worktree; this task's commit contains the assessment, numbering and audit corrections.
Proof: [implementation plan](IMPLEMENTATION_PLAN.md),
[Architecture](ARCHITECTURE.md) and
`docs/Archive/ADR/PROPOSED_ADR_RESEARCH_PLAN_RECONCILIATION.md`.
The displaced assessment entry is preserved intact in the previous log.

Checks: `.venv/Scripts/python.exe -B scripts/check_architecture.py --docs-only`
and `git -c core.safecrlf=false diff --check` passed (exit 0). Inline
scope/preservation/link review passed: Tasks 1/2/4/5/6/7/8/9/10 unchanged from the
pre-correction worktree, active numbering 1–12, three conditional specs retained,
ADR template/local links valid, log rotation intact, and projection semantics
unchanged with only the reviewed Architecture hash refreshed. Fixed-query catalogue
reproduction at page size 20: 109 candidates; budget 80 retrieves 80, labelled
`stat.scipy` recall 0; budget 200 retrieves 109, recall 1.

Limits: Documentation integrity and local fixed-query candidate coverage only.
Runtime, configuration and tests unchanged. No live providers, scientific utility,
native controls, actual retrieval repair or remote notebook publication verified.
