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

## 2026-10-02 — Make implementation-plan numbering consecutive

Result: Renumbered former active Tasks 14 and 15 as Tasks 11 and 12. Updated all
references throughout the plan, including the catalogue-extension reference;
clarified the historical-to-current mapping in the reconciled assessment ADR.
The three conditional feature specs and all capability scope/proof text are retained.

Basis: HEAD `b27a6b220cd183bd51aff06aec8b8f778187d1b1` plus the existing documentation
worktree. Earlier assessment, testing acceptance and unrelated edits are preserved.
Proof: [implementation plan](IMPLEMENTATION_PLAN.md) and
`docs/Archive/ADR/PROPOSED_ADR_RESEARCH_PLAN_RECONCILIATION.md`.
Checks: Inline Python numbering/preservation review passed (exit 0): headings exactly
1 through 12, no old 14/15 references, all singular task references resolve, plural
catalogue reference updated, and three conditional specs retained. Documentation-only
architecture check passed (exit 0); `git -c core.safecrlf=false diff --check` passed
(exit 0). Log rotation preserves the displaced entry intact.
Limits: Documentation/reference integrity only; no runtime or test changes.

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


## 2026-10-02 — Establish native WSL setup and assess execution gaps

Result: Confirmed Linux-home checkout on ext4, WSL2 kernel
`6.6.114.1-microsoft-standard-WSL2`, nonroot ownership and running systemd user
manager. Installed locked Linux Python 3.12.13 environment with `uv sync --frozen`
(133 packages), and web dependencies with `npm ci --prefix web` (29 packages).
Corrected the native Coder verifier's other-block target to use the actual relocated
peer workspace in both profiles. README now documents setup and a user-owned local
data root. Configured local Git whitespace handling to accept existing CRLF while
retaining trailing-space checks; no worktree-wide line-ending rewrite.

Basis: HEAD `2d10d1d2fe7875690d48f8eecaa929679753d877` plus the existing CRLF worktree.
Changed source: `scripts/verify_coder_container.py` only; retained environment,
interpreter/config/lockfile/verifier hashes and results are in
`var/wsl-verification-20261002/environment-and-checks.json`. Detailed Coder,
isolated Science and focused-check logs are retained beside it. Existing scientific
records preserved; the failed live run remains in its own testing database.

Checks: `ONCOJEV_TESTING=0`, telemetry disabled, with explicit user-owned data root
for ordinary fixtures: profile selection across live-mode/boundary/persistence
owners passed 25, deselected 156, in 13.32 s. Initial run had 23 passed/2 failed
in 17.71 s because `/work/director` was unwritable; explicit data root resolved it.
Native-setup and architecture-owner tests: 45 passed in 6.19 s. Web typecheck passed.
Direct `verify_coder_container` passed for both roles in ordinary and testing
profiles (21 controls each). Ordinary `verify_coder_resources` passed 11 executions;
`verify_local_science` passed five controlled phases, fresh replay and modified
interpreter denial; `verify_science_resources` passed nine resource/accounting
checks. Isolated Science also passed five phases/replay inside a native testing root.
Fixture transport/scripted agents prove exercised controls, not research utility.
Full architecture checker and `git diff --check` passed (exit 0).

Live assessment: configured providers acquired public data and retained one
measurement/evidence, Jev records, handoff, dossier and Delta. `run_once` then raised
`UnexpectedModelBehavior` after 196.54 s following repeated unsupported external
source calls and exhausted `run_code` retries; post-block review was not reached.
Failure logs and exact database path remain in `live-record-summary.json` and
`live.log`. This failed check provides no complete live qualification. API and UI
subsequently returned HTTP 200 at ports 8080 and 3000; user systemd units
`oncojev-api`/`oncojev-web` remain running. API maintenance mode pauses automatic
research and opens a fresh isolated history, not the failed-run database. Stop with
`systemctl --user stop oncojev-api oncojev-web`.

Limits: Tasks 1, 2 and 12 remain unfinished: installed Science quotas, complete
current-environment-bound qualification record, successful composed live trajectory,
consecutive-cycle/review proof and data-limit usefulness. Two minutes remains an
observation target. Testing qualification/import boundaries are unchanged. Dependency
installation reported one high and one critical web advisory; no dependency upgrade
or reusable-method promotion performed. Rotated predecessor preserved intact in
Previous Task Log; the immediately preceding completed task remains below.

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


## 2026-10-02 — Task 1: Govern installed Science and retain resource accounting

Result: Fixed typed installed operations execute under the shared native governor,
with CPU/memory/process/time/workspace limits, private filesystem/network authority
and trusted confinement before scientific imports. State, usage and persistence
remain with the service owner. Cancellation and aggregate shutdown drain work before
releasing the heavy lease; unconfirmed cleanup quarantines it. Durable receipts feed
shared consumption and Delta CPU/workspace counters; sampled disk peaks are lower
bounds and unavailable counters remain unknown.

Requested policy: explicit `unbounded_work` disables application model/tool/retry/cost
gates while retaining measurement, data ceilings, scientific controls and terminal/
handoff behavior. Blocks remain 180–300 s (240 s default, 30 s reserve). Default
mission is lung cancer. Ordinary bounded behavior is available with the flag disabled.

Verification: current owner suite passed 214 in 75.03 s. Expanded installed native
probe passed 13 process families plus aggregate-shutdown draining, including source
statistics, parser, figure, clinical/survival, MAF/CNV, expression cohort and case join;
retained `var/task1-proof/installed-expanded.log`. Task 2 ordinary and isolated writer
also reran it successfully. Architecture and whitespace checks passed exit 0.

Implementation: existing runtime/Science/resources/Delta/config owners plus fixed
`src/science/installed.py` transport/worker and explicit native verifier; accepted
architecture decision retained in `Archive/ADR/ADR_INSTALLED_SCIENCE_PROCESS.md`.
No scientific records rewritten. Provider/trajectory time and scientific utility are
separate proof; required draining can exceed the testing observation target.


## 2026-10-02 — Task 2: Qualify native WSL2 execution

Result: Implemented production qualification and consumer together. Six direct
observations resolve both Coder roles, external Science preparation/install/test/
execution/replay, installed Science, resources/downloads/leases/cancellation, linked
paths and retention. Current-basis checks include interpreter, installed package and
stdlib bytes, control binaries/shared libraries, kernel, policy, worktree and actual
owned-path filesystems. Drift/missing/tampered observations reject qualification.

Basis: HEAD `2d10d1d2fe7875690d48f8eecaa929679753d877` plus the preserved worktree;
exact basis and raw logs retained under `var/task2-proof/ordinary-current/` and
`testing-current/`. Ordinary writer passed all six probes and atomically retained
six operational records plus qualification `a68ae217715748e596ffa7338beace86`, seq 7,
in `var/oncojev.sqlite3`. Testing writer passed all six probes with `qualifying:false`;
no importer or normal-history transfer. Earlier run correctly refused changing code.

Verification: final owner suite (evaluation, representations, live mode, persistence,
boundaries) passed 214 in 75.03 s; architecture and whitespace checks passed exit 0.
Tests and raw native probes demonstrate different scopes. Fixture source transport
and exact command controls do not prove biological validity or complete live research.
Later source/projection changes intentionally invalidate the historical ordinary
receipt; promotion must run the writer again against its final current basis.


## 2026-10-02 — Task 6: Bind a pinned descriptive operation to canonical references

Result: Retained MIT-licensed `TheAlgorithms/Python` operation at immutable commit
`84b73d08f8bfa4e6bfae0243369c24f5a7539745`. Science extracts upstream-authored
canonical, changed-vector and empty-input expectations before comparisons. Real
controlled candidate outputs resolve separate direct upstream invocations, exact
inputs/software/scope and native resource records. Unsupported weights/parameters,
missing output references, modified proof and unsuitable population inference reject.
No benchmark label or qualification result becomes scientific evidence.

Proof: ordinary native candidate `a8271658-0944-46e5-bc8a-f6cbcdf29c46`; reference
validation `337b1e1ff2774e4f8177d70834e6af50`, seq 68, in `var/oncojev.sqlite3`.
Three upstream numerical cases matched and empty input rejected. Eight real pipelines
retained 67,582,192 acquired software bytes; data ceilings were not relaxed. Separate
native undeclared-weights case rejected with cleanup/control receipts. Exact material,
licence, comparisons and adverse logs remain under `var/task6-proof/`.

Verification: 50 focused qualification/representation/boundary tests passed in
10.40 s; external-owner regression selection passed 7 in 4.31 s; evaluation owner
passed 13 in 12.97 s. Architecture and whitespace checks passed exit 0. Initial
collector incorrectly read the ledger envelope; its failed record remains intact.
A subsequent proof resolves nested actual resource records and independent candidate
IDs from immutable executions, without changing expectations or fabricating reruns.

Implementation: `src/science/qualification.py` producer, fixed independent upstream
probe and Researcher declaration/validation tools. Existing external pipeline body
is shared through `HarnessRuntime.execute_external`; reservation, charging, lease,
receipts and persistence remain with the service. Accepted decision is in
`Archive/ADR/ADR_SCOPED_OPERATION_QUALIFICATION.md`. Scope is only finite arithmetic
mean of a retained same-unit numeric vector; the installed summary remains adequate.
No new oncology inference, clinical benefit or arbitrary package qualification claimed.

## 2026-10-02 — Task 7: Qualify a recoverable stdlib-only environment

Result: The selected pinned mean now has an exact owned archive, explicit empty
third-party dependency set, commands/inputs/output identity and Python/stdlib/
platform/installer constraints. A separate fresh venv restored 8,447,774 retained
bytes, ran all five governed phases and replayed exactly with zero network acquisition.
There is no network fallback from missing retained packages. Actual resource, fresh
candidate, source-lock and failure references remain independently resolvable.

Proof: environment qualification `d48dcd3b8df54f5cb32595f0eb4093bc`, seq 89, in
`var/oncojev.sqlite3`; exact lock and new candidate refs retained under
`var/task7-proof/`. Conflicting dependency declarations, Python drift, altered lock
reference, unavailable retained archive and real corrupted-archive preparation all
rejected. Failed qualifications/adverse observations remain retained; successful
recovery does not erase them. Corruption probe confirmed governed cleanup and zero
network bytes. Source bytes were copied into the existing store, not imported from
testing research history.

Verification: focused external/qualification/resource owner checks passed 20,
deselected 139, in 5.43 s (one framework event-loop deprecation warning). Four
integrity/recovery contracts passed in 0.12 s. Architecture and whitespace checks
passed exit 0. Native observations establish the selected recovery path, while
synthetic tests establish rejection/identity logic.

Implementation: existing local backend accepts only explicit retained recovery
inputs; runtime owns the shared execution/reservation/charging path. Science lock/
qualification producers and the Researcher recovery tool use actual owned artifacts
and receipts. Decision remains in `Archive/ADR/ADR_SCOPED_OPERATION_QUALIFICATION.md`.
Scope is the pinned stdlib-only method on the exact declared host Python constraints;
arbitrary dependency-bearing, R/Conda or whole-host recovery remains unsupported.

## 2026-10-02 — Task 8: Assess the frozen lung oncology selection

Result: Three named scoped needs received no-build decisions: the existing source
summary adequately supplies retained age-slice mean/count/missingness; survival
inference lacks qualified time-origin/endpoint/censoring/design prerequisites; TMB
lacks source-bound callable territory and audited variant/sample denominators.
The existing governed transforms expose availability without manufacturing endpoints,
assays, missing values or burden. No new inferential wrapper was justified.

Proof: ordinary GDC assessment retains 100/1089 case rows, 95 observed ages/five
missing, 72 available time/event pairs/28 missing, and five MAF metadata records.
Case and file queries, exact inputs, baseline measurement, transform and decisions
resolve in `var/oncojev.sqlite3`; outcome `69f8c2a3381a4a14ba54cbb806f6e3af`, seq 134.
Corrected file-project filter assessment acquired 31,564 data bytes. The initial
empty wrong-field file query and its outcome remain history; the corrected bounded
query uses `cases.project.project_id`. Exact final report/raw log is in
`var/task8-proof/`. Two installed native operations ran under shared controls.

Verification: actual source assessment and existing governed baseline/transform
completed; architecture and whitespace checks passed exit 0. The finite selection
was frozen in the plan before assessment and is retained with its declaration in
ordinary history. Broader independent scientific review remains pending. No clinical
survival estimate, TMB value, population coverage or new scientific benefit claimed.
Implementation is the explicit `scripts/assess_oncology_selection.py` through existing
source/Science/persistence owners; this completes only the selected no-build scope.

## 2026-10-02 — Task 2: Refresh final WSL native qualification

Result: Current source, including compressed-assay transforms, composed-verification preparation and the corrected GDC metadata/SDK contract, has
current ordinary local qualification. All six ordinary probes and six isolated
testing probes passed: Director/Researcher confinement, aggregate command resources,
five-phase external science/replay, scientific adverse controls, installed worker
families/shutdown/drain and profile-path/retention isolation. Ordinary record
`50a94491032440978961416cbf1e69f3`, seq 1158, resolves in `var/oncojev.sqlite3` against
the exact current application/worktree, interpreter/package/stdlib, policy, kernel,
control binaries and native Linux filesystems. Testing remains nonqualifying.

Verification: current full invariant suite exited 0: 291 passed and one frontend check skipped after the Linux Node executable disappeared. Restoring the same official-SHA256-verified v22.22.2 release passed that check separately (1 passed in 0.47 s), verifying all 292 collected invariants across the two runs. Focused SDK/migration/qualification checks passed 12. Ordinary profile and owned Linux data paths were used. Architecture and whitespace checks passed exit 0.
Raw proof: `var/task2-proof/ordinary-gdc-final/`,
`var/task2-proof/testing-gdc-final/`, and their adjacent final raw logs. The API
restarted with final source; API/web user services remain active and return HTTP 200
on ports 8080/3000. Repository, `.venv` and data are on WSL2 ext4 `/dev/sdf`, outside
`/mnt/c`. API testing maintenance mode keeps automatic research paused.

Scope: native execution/control proof, not independently reviewed scientific utility,
accepted reusable promotion, Docker/Railway qualification or a complete clinical
trajectory. Re-review of actual Task 10 source-use history now rejects only unsupported
utility. Tasks with remaining scientific-review/qualification criteria stay in the
plan. The dated whole-lab assessment and raw comparisons live under
`evals/reference/results/` and `var/task11-proof/`; original failed observations remain.

Implementation identity: uncommitted worktree at HEAD
`2d10d1d2fe7875690d48f8eecaa929679753d877`; exact application/environment hashes are
retained in seq 1158 and the machine-readable assessment. Existing scientific history,
unrelated worktree edits and ignored credentials were preserved.
