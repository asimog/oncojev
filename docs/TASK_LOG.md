# Task Log

Completed verification only. Keep the most recent completed task and its immediate
predecessor, newest first; append displaced entries intact to
[Previous Task Log](Archive/PREVIOUS_TASK_LOG.md). The architecture checker rejects
a third level-two entry. Future work belongs only in IMPLEMENTATION_PLAN.

## 2026-10-04 — Production Task 4: canonical operational runtime

Result: both compatibility live launchers delegate cycle/direction arguments to the
ordinary module CLI, removing phase3's independent Researcher lifecycle and the
live-cycle launcher's prescribed scientific procedure. CLI cycle/serve and container
bootstrap reach the same AutonomousService composition and Python scheduler. Existing
sync wrappers delegate to the async cycle owner. Allocation/frontier validation,
fresh Researcher creation, state writes, deterministic admission, terminal atomicity,
recovery, memory and qualification retain their current owners; no new coordinator.

Implementation: `src/__main__.py`, `scripts/run_live_cycle.py`,
`scripts/run_live_phase3.py` and owning entrypoint tests on HEAD
`5f3f4175fb346d8214782439aeae557067a71666` plus preserved source/package fixes.
No current caller of the two old scripts was found outside the new compatibility
checks. Component/qualification/evaluation/export probes still invoke existing owners
in explicit scopes; comprehensive script retirement remains Task 9.

Verification: 134 entrypoint and persistence/lifecycle tests passed in 47.23 s,
covering supplied direction, module/serve/worker delegation, one active Researcher,
persistent Director, fresh local agents, terminal atomicity, recovery and shutdown
drain. Both old launcher regressions were reproduced before replacement. Architecture
and `git diff --check` passed. Exact caller/owner/hash inventory:
`evals/results/production-runtime-convergence-20261004.json`; scoped raw proof in
`var/production-convergence/runtime-owner-tests.log` and saved pre-cutover scripts.
Prior completed bootstrap proof was archived intact.

Limits: offline scripted lifecycle/caller contracts, not scientific utility,
black-box autonomy or deployed confinement. Final native/live/deployment/scientific
qualification remains Tasks 12/13. No scientific store or evidence was changed.

## 2026-10-04 — Production Task 3: production/evaluation package separation

Result: utility proof retention/resolution and its condition vocabulary moved to
`src/oncolab/utility.py`; governance and reusable execution share that owner without
evaluation imports. Evaluation implementation/callers moved to `evals/`; the generated
1,178,174-byte selection report moved outside installed source with bytes/hash intact.
The existing architecture checker rejects direct evaluation/test imports, known
literal dynamic imports (including imported aliases), and unresolved names in those
known dynamic-import calls. Arbitrary loader indirection is outside its static scope.

Implementation basis: HEAD `5f3f4175fb346d8214782439aeae557067a71666` plus prior fixes
and owner-preserving package migration. AST comparison with the preserved pre-migration
source proves both utility functions unchanged except the source of their exact
condition vocabulary. Candidate/scope/application hashes, actual repetitions, failure
checks and independent reviewer resolution remain mandatory; no proof was promoted.

Verification: 80 owning evaluation/qualification/retention/isolation tests passed in
21.96 s (one intentional invalid-score warning); 50 architecture/import tests passed
in 7.65 s. Expanded isolation tests passed 13 cases in 4.89 s. Fresh source-only and
extracted built-wheel consumers constructed a new service/factory and exercised the
unsupported utility producer/resolver with evaluation/history absent. The 116-file
wheel contains neither evaluation/test packages nor the generated selection report.
Architecture/projection and `git diff --check` passed. Exact migration/artifact/wheel
proof: `evals/results/production-package-separation-20261004.json` and
`var/production-convergence/package-*`. Previous completed proof was archived intact.

Limits: constructor/qualification contracts and package boundaries, not whole-lab
provider/native autonomy, scientific utility or deployment qualification. Historical
verification archive relocation remains Task 10; final-basis qualification remains
Tasks 12/13. Application identity changes with the package cutover; older qualification
is not silently accepted for the new basis.
