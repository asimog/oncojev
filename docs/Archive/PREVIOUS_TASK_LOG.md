# Previous Task Log

Completed task evidence only; this is not a roadmap or status authority.

Each entry records the completed scope, result, implementation identity,
verification, retained proof and known limitations.

## 2026-10-02 — Align the five active documents

Task: Align README, AGENTS, Architecture, Implementation Plan and this log with
current code and the user's planning clarifications.

Result: Replaced repeated architecture prose with component and lifecycle diagrams;
corrected state/admission/composition ownership; supplied current run/navigation
entry points. Bounded tool selection, complete-lab evaluation and exact-environment
qualification work are explicit in existing plan tasks. Capability-specific
evaluations and the composed-trajectory task retain their separate purposes.

Basis: HEAD `d74577221b43d7385e7d10a96424fa01472aef74` plus the existing worktree.
Only the five named documents were edited by this task; runtime, configuration,
scientific records and governance tooling were preserved.

Verification:

- `.venv/Scripts/python.exe -B -` with an inline documentation validator — passed
  local link/heading targets, referenced paths, balanced fences, two Mermaid blocks,
  16 feature specs and absence of historical task identifiers/archive navigation.
- In-memory comparison against the pre-edit documents — all 16 task numbers/titles
  preserved; only task bodies 2, 3, 8, 14 and 16 changed; 11 bodies, including 15,
  identical. SHA-256 comparison preserved all ten protected-file snapshots.
- `git diff --check` — passed; existing LF-to-CRLF notices only.

Evidence: [Architecture](../ARCHITECTURE.md), [plan](../IMPLEMENTATION_PLAN.md),
[README](../../README.md) and [agent guidance](../../AGENTS.md). Claims were traced to
runtime composition, typed tool registration, Science admission, state/persistence
owners, configuration, CLI/UI entry points and owning test source.

Limitations: Documentation and source inspection only. No runtime, integration,
native, scientific or provider tests were run; diagrams were checked structurally,
not rendered. Subsystem documents, the recorded ADR and the architecture projection
were outside the edit scope. This entry does not certify scientific utility,
execution qualification or completion of the broader documentation task.

## 2026-10-02 — Align subsystem docs and establish minimal drift checks

Task: Completed the remaining documentation/projection scope and its bounded
governance feature spec; removed finished task 16 from the active plan.

Result: Corrected subsystem links and obsolete planning references, aligned the
accepted ADR's log destination, shortened agent rules, and reviewed the architecture
projection against current composition and state ownership. Production Reasoner
composition uses the runtime integration; standalone construction remains possible.
Qualification consumption checks declared controls rather than independently proving
the exact current environment. Removed the duplicate governance specification;
its history remains in Git.

Extended the existing architecture checker with canonical-source hashes, owner and
evidence references, Python symbols, active Markdown navigation and detectable
planning structures. Reused the declaration index; direct import guards now inspect
AST imports instead of prose. Removed the duplicate frontend token scan and upstream
manifest requirement; existing frontend tests retain their own coverage. Catalogue
identity/portable-byte checks remain. Documentation-only checking imports no
application code. Native setup copies its required governance inputs and excludes
historical/source-input trees; its reusable cache is developer setup only.

Basis: HEAD `d74577221b43d7385e7d10a96424fa01472aef74` plus the existing aligned
worktree and this documentation/development-tooling patch. Application code,
configuration, persistence and scientific records were unchanged.

Verification:

- `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider -o addopts='' tests/invariants/test_architecture_checks.py tests/invariants/test_repo_index.py tests/invariants/test_native_setup.py -q`
  — 40 passed in 13.08s. Fixture checkout mutations exercise rejected drift,
  permitted prose/examples, read-only nonexecution, static imports and developer
  setup invalidation; no WSL/native execution probes run.
- `.venv/Scripts/python.exe -B scripts/check_architecture.py` — passed, including
  existing catalogue integrity. `--docs-only` — passed projection and active links.
  Before projection review, the new check rejected the stale canonical hash that
  the old checker had accepted.
- In-memory SHA-256 comparison — remaining task text 1–15 preserved by governance
  completion (final trailing newline normalized); task 16 alone removed. Three
  pre-existing source archives preserve Git blob identity. The completed-plan
  archive changes only its relocation link; the rejected ADR retains its proposal
  body with recorded rejection metadata. Contents were checked for preservation,
  not used as current authority.
- `git diff --check` — passed.

Evidence: [checker](../../scripts/check_architecture.py),
[focused tests](../../tests/invariants/test_architecture_checks.py),
[projection](../../architecture.yaml), [Architecture](../ARCHITECTURE.md) and
[agent rules](../../AGENTS.md). The implementation plan is the sole future-work owner.

Limitations: Static integrity does not establish semantic consistency, prose
completeness, dynamic-import behavior, scientific utility or current qualification.
Planning detection covers explicit task/backlog headings, open checkboxes and
active log fields on the named active surface; prose still requires review. Owner
and data-flow semantics, framework exclusivity, shallow state freezing, native
command controls and declared qualification consumption remain REVIEWED. Existing
TESTED labels cite scoped behavioral tests, not fresh native/runtime certification.
No application runtime, provider, integration, scientific or native tests were run.

## 2026-10-02 — Reconcile the ADR-handling workflow and template

Task: Verify the supplied workflow against existing governance and implement its
bounded documentation clarification.

Result: Created a reconciled proposal directly, without an untouched supplied copy.
Extended AGENTS and the explicitly requested archived template to distinguish
repository facts, justified changes, decision status, implementation and proof.
Reused existing owners and checks; the projection changed only the reviewed AGENTS
hash. No application code, tests, configuration or architecture semantics changed.
Decision adoption is not inferred from document creation or passing checks.

Basis: HEAD `f8165fd43e108f26863754380b486b40f27c1063`, initially clean worktree,
plus this documentation patch. The template and ADR convention were read explicitly
for this request; other archive/source-input content was excluded.

Verification:

- `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider -o addopts='' tests/invariants/test_architecture_checks.py tests/invariants/test_repo_index.py -q`
  — 32 passed in 15.92s before edits; checker/index/test code remains unchanged.
- `.venv/Scripts/python.exe -B scripts/check_architecture.py` and the same command
  with `--docs-only` — passed before and after documentation implementation.
- Explicit inline ADR/template review — required sections and local link targets
  checked outside the routine archive-excluding scan. Preservation hashes retain
  the implementation plan, Architecture, checker, index, tests and configuration;
  YAML semantic comparison retains all other projection facts/classifications.
- `git diff --check` — passed.

Evidence: [reconciled proposal](ADR/PROPOSED_ADR_REPOSITORY_VERIFIED_DECISIONS.md),
[working rules](../../AGENTS.md), [projection](../../architecture.yaml) and the existing
[checker](../../scripts/check_architecture.py). The archived template was updated only
under this task's explicit authorization.

Limitations: Documentation implementation is complete; ADR decision status is recorded
in the proposal rather than inferred from this log. No application decision was
supplied. Semantic ADR review/acceptance remains explicit and is not checker-enforced;
static integrity provides no native/scientific qualification. No new prose tests,
application/runtime, native/WSL, provider, scientific or integration tests were run.

## 2026-10-02 — Investigate the fast local testing proposal

Result: Traced environment/config/path, download/resource, lifecycle, admission and
qualification owners. Appended the investigation and reconciled Task 17. No runtime
or actual local environment settings changed; decision remained PROPOSED.

Basis: HEAD `2302b4bcc0ede6b94da466f5b3d6342548271b6c` plus the existing worktree.
Proof: [current testing ADR](PROPOSED_ADR_FAST_LOCAL_TESTING.md).
Checks: explicit active document/ADR link, whitespace and earlier-plan preservation
checks passed (exit 0); `git diff --check` passed (exit 0). Documentation-only
architecture checking failed (exit 1) on the pre-existing stale AGENTS projection hash.
Limits: Source/document assessment only; no behavior, provider or native qualification.

## 2026-10-02 — Archive surplus docs and enforce a two-task log

Result: Archived nine docs, including the retired ADRs/guide and all previous log
content. Restored all ten READMEs outside `docs/` and removed their empty archive
directories after scope correction. Root navigation and one subsystem link were
then updated. Package metadata and native-copy inputs remain unchanged.
AGENTS and the existing checker enforce docs-only archiving, scoped historical
exceptions and at most two completed log entries. The testing ADR now compares
current/proposed limits and separates a 90 s block allowance from a 120 s observation
target; recommends WSL2/local_venv for full execution and Windows for fast contracts.

Basis: HEAD `2302b4bcc0ede6b94da466f5b3d6342548271b6c` plus the existing worktree.
Completed Task 18 removed from the plan. Runtime/scientific records are unchanged.
Proof: [previous log](Archive/PREVIOUS_TASK_LOG.md), [ADR](PROPOSED_ADR_FAST_LOCAL_TESTING.md),
checker/tests; local relocation snapshot at
`var/document-cleanup-02e3557814c741599a5cf71894a98c47/baseline.json` (ignored).

Checks: `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider -o addopts='' tests/invariants/test_architecture_checks.py tests/invariants/test_repo_index.py tests/invariants/test_native_setup.py -q`
— 51 passed in 14.75 s. The third-entry case first failed because the old checker
accepted it; the revised checker rejects it and preserves external READMEs.
Full and `--docs-only` architecture checks passed; projection semantics retained,
only reviewed canonical hashes refreshed. Relocation/body/hash preservation and
`git diff --check` passed.
Limits: Local governance/fixture proof only; no native/provider execution or platform
speed measurement. Testing-profile implementation remains proposed in Task 17.

## 2026-10-02 — Assess research-plan reconciliation and accept the testing ADR

Result: Assessed the supplied research-plan ADR with the archived template and
traced frontier, memory, semantic, evaluation, runtime and qualification owners.
Recorded ADOPT WITH LIMITATIONS as a proposed technical recommendation in
`docs/Archive/ADR/PROPOSED_ADR_RESEARCH_PLAN_RECONCILIATION.md`; reconciled plan specs
for neutral evaluation, formal open proposals, experience lineage and whole-lab
semantic/runtime experiments. Retained publication/scaling/shared-generation specs
under explicit triggers. Accepted the fast-testing ADR at the user's instruction,
kept its active path and removed Task 17 without claiming implementation completion.

Basis: HEAD `b27a6b220cd183bd51aff06aec8b8f778187d1b1`, initially clean; this
documentation worktree is the implementation identity. No source, configuration,
tests, dependencies or scientific records changed. README/Architecture now reflect
the testing decision; reviewed YAML semantics are unchanged, with only its canonical
Architecture hash refreshed.
Proof: reconciled ADR and [implementation plan](IMPLEMENTATION_PLAN.md),
[accepted testing decision](PROPOSED_ADR_FAST_LOCAL_TESTING.md); displaced predecessor
preserved intact in [previous log](Archive/PREVIOUS_TASK_LOG.md).

Checks: `.venv/Scripts/python.exe -B scripts/check_architecture.py --docs-only`
passed (exit 0); `git diff --check` passed (exit 0). Inline Python scope/preservation
review passed (exit 0): eight unaffected task specs unchanged; all three conditional
spec bodies preserved; Task 17 explicitly removed; expected task inventory; unchanged
projection semantics; exact ADR template sections and resolving archived links.
Limits: Source/test/API/document assessment and static integrity only. No behavioral
tests, provider/native runs, empirical scientific/search/learning/semantic utility,
framework adaptation or testing-profile implementation were verified. New research
ADR remains proposed; testing ADR acceptance is separate from implementation proof.
