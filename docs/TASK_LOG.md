# Task Log

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

Evidence: [Architecture](ARCHITECTURE.md), [plan](IMPLEMENTATION_PLAN.md),
[README](../README.md) and [agent guidance](../AGENTS.md). Claims were traced to
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

Evidence: [checker](../scripts/check_architecture.py),
[focused tests](../tests/invariants/test_architecture_checks.py),
[projection](../architecture.yaml), [Architecture](ARCHITECTURE.md) and
[agent rules](../AGENTS.md). The implementation plan is the sole future-work owner.

Limitations: Static integrity does not establish semantic consistency, prose
completeness, dynamic-import behavior, scientific utility or current qualification.
Planning detection covers explicit task/backlog headings, open checkboxes and
active log fields on the named active surface; prose still requires review. Owner
and data-flow semantics, framework exclusivity, shallow state freezing, native
command controls and declared qualification consumption remain REVIEWED. Existing
TESTED labels cite scoped behavioral tests, not fresh native/runtime certification.
No application runtime, provider, integration, scientific or native tests were run.
