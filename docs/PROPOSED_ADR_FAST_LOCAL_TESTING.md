# ADR: Isolated fast local testing through existing owners

Date: 2026-10-02.
Owners: [Architecture](ARCHITECTURE.md), [implementation plan](IMPLEMENTATION_PLAN.md),
`src/config/loader.py`, `src/runtime/paths.py` and `src/autonomous.py`.

## Context

Assessment basis: HEAD `2302b4bcc0ede6b94da466f5b3d6342548271b6c` on 2026-10-02.
The worktree is already dirty, including this untracked proposal, the plan,
AGENTS, ADR guidance and architecture-checker changes. Those unrelated edits and
archive deletions are preserved; this assessment does not adopt or implement the ADR.
Existing runtime configuration defaults to live mode, 900-second blocks with a
300-second minimum and 90-second handoff reserve. The loader validates one typed
RuntimeConfig; factory composition feeds its values into BlockManager, role/cycle
budgets, sources, Jev, sandbox and service resource controls. Those owners already
support smaller values; there is no need for a second lifecycle or runtime mode.

Service storage normally uses `ONCOJEV_DATA_ROOT` or application `var/`, with an
optional database override. Researcher/sandbox workspaces use the path owner, but
the default Director workspace is `/work/director`. The environment factory currently
chooses the database before the constructor loads `.env.local`. An environment-only
switch must be resolved before database selection and recovery, not after opening
normal research history.

The proposed bounded testing mode addresses a real missing entry point. Smaller
verification scope means choosing appropriate existing local tests, not skipping
scientific validation/replay, reducing qualification requirements or changing errors
to successes. Runtime mode and provider selection must remain unchanged.

## Decision

### Environment and editable configuration

Put `ONCOJEV_TESTING=1` in ignored repository `.env.local`; no repeated shell export
or machine-wide setting is needed. Load it through `src/config/environment.py`
before selecting paths. Existing process values retain precedence: an explicit
process `ONCOJEV_TESTING=0` overrides local `1`. Parse the switch once when the
process settings are established: unset or literal `0` means normal, literal `1`
means testing. Empty, `true`, `2` and other unsupported values fail explicitly
before database creation, opening or recovery. Do not pass the switch or secrets
into agent context or credential-free execution children.

Keep editable profile parameters in a small typed `testing` section of the existing
`config/runtime.yaml`, owned by `src/config/models.py` and `src/config/loader.py`.
The following is a proposed configuration shape, not installed configuration:

```yaml
testing:
  observation_target_seconds: 120
  block:
    default_seconds: 90
    min_seconds: 60
    max_seconds: 90
    handoff_reserve_seconds: 15
  public_data:
    max_response_bytes: 10000000
    max_block_download_bytes: 20000000
    max_service_download_bytes: 50000000
```

The byte values are proposed editable starting ceilings, not measured adequacy or
a guaranteed useful cohort size. They leave the current 10 MB per-response/file
ceiling intact while reducing public-data totals. They apply to GDC and Xena data
and data metadata; literature and external software/catalogue metadata retain their
ordinary limits. Future data clients must declare their acquisition category at
composition rather than inherit a software limit accidentally. No additional
environment variables, alternate RuntimeConfig, provider profile or test dispatcher
are needed. A future `.env.example` comment should point to this section. Do not
edit the developer's actual `.env.local` during proposal assessment.

### What centralized downward caps mean

The loader first validates ordinary configuration, computes the allowed testing
changes on its dumped values, then calls `RuntimeConfig.model_validate` again.
This preserves the same configuration owner and all its field/cross-field checks;
unchecked `model_copy(update=...)` is insufficient. Unset/`0` returns ordinary
effective settings. `observation_target_seconds` is reporting metadata for a small
scenario, not an execution allowance or a cancellation deadline. The testing block
section has ordinary consistent allocation bounds.

For timing, let `c` be validated ordinary block settings and `t` the testing
profile. Require positive profile durations, `t.min_seconds <= t.max_seconds`,
`t.min_seconds <= t.default_seconds <= t.max_seconds` and a reserve shorter than
its minimum. Compute:

```text
max_seconds     = min(c.max_seconds, t.max_seconds)
min_seconds     = min(c.min_seconds, t.min_seconds, max_seconds)
default_seconds = min(c.default_seconds, t.default_seconds, max_seconds)
reserve         = min(c.handoff_reserve_seconds, t.handoff_reserve_seconds,
                      min_seconds - 1)
```

These formulas keep shorter valid user bounds and reserves; revalidation confirms
`min <= default <= max` and `0 <= reserve < min`. With current normal settings the
effective testing allocation is **90 seconds**, minimum 60, reserve 15; work handoff
begins at 75 seconds. A user's 20/30/40-second min/default/max with a 5-second reserve
stays 20/30/40/5. The **120-second observation target** covers a small scenario's
observed wall time; the **60–90-second allocation** bounds govern new block work.
They now have separate names and purposes. Exceeding the observation target is
reported, not converted to a scientific failure and not used to cancel required
in-flight work. A smaller existing valid allocation remains smaller.

Only timing and public-data byte allowances change. For each data ceiling use the
minimum of its ordinary allowance and editable testing ceiling, retaining the
ordinary cumulative service/block, workspace, durable-storage and free-disk guards.
Data reservations and failed-transfer charging stay with `ServiceResources`; extend
that existing owner with data-category accounting beneath its shared aggregate
limits. Do not reduce the shared aggregate limits, which also account for software.
Software acquisition must use an ordinary software reservation from that owner,
instead of borrowing a newly capped GDC reservation. Lowering
`block.max_download_bytes` globally would also shrink literature and repositories
and therefore does not implement this decision.

Do **not** add testing caps to role/model/tool/source-call/Jev/Reasoner/sandbox-call/
Code Mode/search budgets, costs, model output tokens or request timeouts. Keep
Director event/review settings, sandbox time/CPU/memory/process limits, retention,
workspace/storage guards, required confinement and scientific contracts unchanged.
Repositories and declared dependencies may still download through ordinary typed
acquisition under their existing limits. Existing controls can honestly reject work;
testing adds no blanket prohibition on tool selection, analysis or exploratory use.

### Paths, continuity and retained data

Choose `<configured-data-root>/testing/<run-id>/`, falling back to
`<application>/var/testing/<run-id>/`. Reuse `src/runtime/paths.py` to create a
random UUID run ID once per testing process, rather than per block/cycle or using
a PID alone. The configured root respects deployment/native-storage placement;
the `var/` fallback is already ignored. Both separate test records from normal
history without adding a storage setting or granting agents path authority.

```text
testing/<run-id>/oncojev.sqlite3
testing/<run-id>/director/
testing/<run-id>/workspaces/<block-id>/
testing/<run-id>/workspaces/<block-id>/experiments/<experiment-id>/
```

Database, Director, Researcher and both sandbox backend workspaces use this root.
Docker temporary experiment directories must receive an owned parent; they currently
use the system temporary directory. Owned-command supervisor metadata already lives
beside its workspace and must remain inside the same testing namespace. Preserve
existing backend scratch cleanup and retention; do not add whole-run deletion.

Resolve and validate `ONCOJEV_DB_PATH` and explicit `AutonomousService` constructor
database paths against this root before even making directories, calling
`SqliteResearchStore`, initializing institutions or recovering/backfilling records.
Reject escapes, including linked parents/symlinks/junctions that resolve outside it.
An old normal database override must produce an explicit error, never be silently
opened or ignored. Low-level stores used for fixtures and analysis are not service
constructors and do not acquire a global testing prohibition on reading other files.

Load repository `.env.local`, parse process settings and choose the run root before
service composition. Pass the frozen selection through config, agents, sandbox,
retention and institution owners; they must not reread mutable environment variables
for each cycle. Subsequent cycles reuse the service's loaded policy and paths.
The process shares one testing namespace; a new process creates a fresh one. Fixed
settings mean configuration edits take effect on restart, not that Director or
Researcher decisions are fixed.

Report the resolved testing flag, effective timing/data ceilings and storage paths
through existing service logs/events so an assessment can identify its actual
settings. Exclude credentials and unrelated environment contents. Profile parameters
are editable in YAML; path/run-ID isolation and qualification boundaries are fixed
semantics of enabling the switch, not configurable safety bypasses.

Director global work, post-block review, next allocation, Researcher tool choices,
proposals and memory-based continuation remain available. One service process can
run many cycles with the same isolated history, while each block still has a fresh
Researcher. Use `serve` for that trajectory; separate invocations of `cycle` start
separate histories. The switch makes no claim that those decisions improve: that
requires measured evaluation. The unchanged 300-second scheduled Director review
interval may outlast a short block; material events and terminal review remain
available, so a fast run alone does not prove the scheduled-review path.

Retain databases, source bytes, measurements, evidence, proposals, failures, usage
receipts and logs for assessment. No automatic deletion or database merge is added.
Useful inputs/results can be selected for later normal-context ingestion only
through explicit provenance-preserving validation and ordinary admission, retaining
original test identities and limitations. Do not relabel testing qualification or
copy accepted registry state as normal authority. There is no generic cross-store
scientific ingestion path today; this ADR does not pretend an export is an importer.
Assess/export the retained records, then define any concrete missing ingestion
operation in the plan before building it. Analysis and later justified use are
allowed; automated cross-store ingestion is not delivered by this switch.

### Scientific and qualification authority

Extend the existing institutional application identity with an unambiguous testing
profile discriminator and effective-profile/configuration binding; retain it in
registry revisions, block pins and existing receipts. Keep the normal identity
algorithm otherwise intact. Do not put the random storage run ID into application
content identity. `application_identity()` currently hashes source/configuration
files, not a testing setting; this distinction is proposed, not already enforced.

Extend the existing `local_verification_passed` consumer to reject qualification
for the frozen testing profile, even for a complete receipt matching a testing
identity. Normal consumption also cannot accept a testing application's receipt.
Through existing governance this denies reusable promotion/update authority without
denying acquisition, sandbox execution, measurement, admission, memory, analysis or
proposal/rejected-review retention. No new qualification writer or registry is added.
Actual source-bound measurements may still pass ordinary admission in the testing
database. Testing status is neither a scientific negative nor a scientific-quality
verdict. Selected material may later support normal work after ordinary checks;
testing receipts themselves do not supply normal-application qualification.

Verification routing stays in AGENTS and the assigned task. The switch does not
disable governance checks, choose tests automatically, switch to deterministic
providers or shorten required scientific procedures.

## Alternatives

Manually copy/edit runtime configuration and paths for every task: possible but
error-prone and easy to leak into normal history. A second complete configuration,
lifecycle or fixture runtime: duplicates owners and tests a different system. A
small typed profile inside the existing YAML only describes its allowed changes.
Always use `var/` despite a configured data root: ignores the native-storage/deployment
owner. A per-block root: loses the continuity under assessment. Reuse a fixed testing
database across processes: carries unselected old history into a fresh experiment.
Automatically omit replay/admission/native checks: changes contracts and can
misrepresent proof. Explicit deterministic test fixtures remain useful but are
not what this switch implements.

## Consequences

Testing runs use shorter allocations and smaller public-data totals. Ordinary
allowances may honestly exhaust, handoff early, reject large inputs or fail to
install/run expensive software; the profile does not add smaller software budgets.
Live mode still requires credentials and can incur provider cost. Isolated data
remains on disk for inspection; no historical test receipt qualifies a normal run.
The mode is process configuration, not a knob changed during active work. A soft
allocation is not a whole-cycle stopwatch: model latency, already-running scientific
work, draining and Director review may exceed 90 or 120 seconds. Required scientific
procedures retain their original timeout/replay requirements.

## Invariants/boundaries affected

Config retains limit authority, paths/service retain storage/lifecycle ownership,
Director retains global allocation and Researcher retains block-local investigation.
Science admission, provenance, replay/validation and append-only persistence remain
unchanged. Test-scoped application identity and local-verification rejection extend
the existing qualification boundary without relaxing it. YAML remains a reviewed
projection; the plan and log retain their distinct future-work/completed-proof roles.

## Verification

Required local evidence is owned by [the assigned feature spec](IMPLEMENTATION_PLAN.md#task-17--add-isolated-fast-local-testing-limits):
normal defaults and invalid switch rejection; preservation of shorter/custom and
all unchanged budgets; isolated actual stores and role/sandbox workspace paths;
shorter real allocation/handoff; data-only rejection/charging and unaffected software
acquisition; cross-cycle history, analysis access and unchanged admission. Independently
verify test-profile identity and qualification rejection. Use focused owning tests,
the existing architecture checker and Git whitespace checks; retain exact results
in [TASK_LOG](TASK_LOG.md). Native confinement, provider connectivity and scientific
utility are not established by these local contracts.

## Status

**PROPOSED — repository-reconciled; implementation not yet verified.** Adoption
is distinct from implementation/proof. No application change beyond this bounded
decision is authorized by the supplied proposal itself.

## Investigation report appended 2026-10-02

This report records current code and read-only test inspection on the HEAD/worktree
basis above. Proposed configuration and guards in Decision are not runtime facts.

### Environment and entry-point findings

| Owner / entry point | Current behavior and implication |
| --- | --- |
| `src/config/environment.py::load_local_environment` | Loads `<root or cwd>/.env.local` using `os.environ.setdefault`. Local settings can enable a switch without shell repetition; process values win. No switch parser or frozen settings object exists. `.gitignore` ignores `.env.*`; `.env.example` currently lists provider/telemetry settings. |
| `src/autonomous.py::service_from_environment`, `AutonomousService.__init__` | Factory selects `ONCOJEV_DB_PATH` / `data_root` before constructor loads local env. Constructor makes the parent and opens SQLite before config validation, recovery and memory backfill. Both factory and explicit construction need validation before those side effects. |
| `src/runtime/paths.py`, agent/factory callers | Data root is absolute `ONCOJEV_DATA_ROOT` or application `var/`. Workspace is `<data-root>/workspaces`; Director is `<data-root>/director` only with an override, otherwise `/work/director`. Helpers reread environment; factory and agents derive application root from source location. Frozen path selection must reach all callers rather than just the service database. |
| `src/__main__.py`, `src/autonomous.py::_serve_cycles` | `serve`/`cycle` use the environment factory. CLI direction is read before service loading; HOST/PORT/interval are read afterwards. `ONCOJEV_MAINTENANCE=1` waits without autonomous cycles; interval is a failure retry delay, not block timing. Keep these settings distinct from the testing switch. |
| `scripts/run_live_cycle.py` | Loads local env/config but opens `var/oncojev.sqlite3` directly and performs recovery. A testing-aware loader alone would allow this script to touch normal history. Route its storage/composition through the same owners before claiming testing coverage. |
| `scripts/run_live_phase3.py` | Loads policy but constructs a manual HarnessRuntime with deterministic Jev/Reasoner, an unconfigured BlockManager and an allocation whose reserve defaults to zero. This is an explicit mixed-provider demonstration, not the composed live service or evidence that the switch changes providers. Keep its label and reconcile its path/timing use if supported in testing. |
| `scripts/worker_entrypoint.py`, `scripts/verify_native.py` | Worker prepares/chowns the configured root before dropping privileges and exec. Do not mint a different testing root in the pre-exec bootstrap; prepare the base and resolve settings in the final service process. Native helper selects its own run/cache root; setup-cache success is not qualification. |
| `src/runtime/pydantic_ai/agents.py::create_configured_agents` | Loads local env again using cwd on each construction. Service composition needs its already loaded snapshot, preserving standalone callers without allowing a later reload to change a service profile. |

### Budget and resource inventory

Numbers below are the current committed YAML or typed default where omitted by YAML.
All values remain unchanged by testing except the explicitly proposed timing and
public-data sublimits. Input/schema guardrails remain in their owners.

| Configuration / constraint | Current application sites and limits |
| --- | --- |
| `block.default_seconds`, `min_seconds`, `max_seconds`, `handoff_reserve_seconds` | YAML 900/300/3600/90. `BlockConfig` validates ordering/reserve; `ResourceAllocation` validates reserve; `BlockManager.create/allocate/status/require_work_window` computes deadline and blocks new work in handoff. Director `allocate_block` uses those bounds. This is the only testing timing overlay. |
| Block domain allowances | YAML tool 500, source 100, Jev calls 100/questions 200, Reasoner calls 10/model requests 10, sandbox 5. `HarnessRuntime.claim/check_work/resources`, Researcher tools, `scientific_tools`, `discovery_tools`, `semantic.py` and hypothesis generation enforce the respective allowances before work. Preserve zeros and custom limits, including existing handoff on exhaustion. |
| Role/aggregate framework allowances | Block model requests 200, provider tools 500, Code Mode executions/inner calls 100/100; Director 50/100/30/100; cycle requests/tools 300/700. Costs are null by default. Factory feeds `HarnessRuntime`, agent capabilities and `RuntimeControls`; preflight/response accounting and `UsageLimits` enforce role, combined Researcher/Reasoner and aggregate budgets. Costs depend on reported provider usage; unknown costs stay unknown. No testing reduction. |
| Director global work / memory | YAML retrieval 20, event turns 8, program review interval 300 seconds. Typed omitted defaults: memory Jev calls/questions/bytes/seconds 4/20/131072/20. `lifecycle.wait_for_research`, `contracts.claim_memory_measurement`, `search_tools.semantic_memory_context_async`, memory service and Director tools consume them. `discovery_tools` separately limits Director external lookups to 10. Keep all unchanged. |
| OncoLab retrieval | YAML search/candidate 20/80, typed ceilings 20/200. `search_tools` counts paged candidates; contracts/global frontier/discovery use bounded results and continuations. Memory searches cap at 20; global frontier/review cap at 20; method generation limits at 8 with at most 10 acquisition IDs. These are ordinary retrieval/schema guards, not testing caps. |
| Jev request/projection | YAML questions per call 100, payload 131072 bytes, projection items 20/payload 65536 bytes. Factory, `TypeSafeJevClient`, semantic measurement and frontier projections consume these plus block question/call allowances. Question identity and registered measurement schema checks remain. |
| Models/providers | `config/models.yaml` owns model/fallback/output/reasoning/timeout choices; outputs Director/Researcher/Reasoner 12000/16000/12000, timeout 120 seconds each. `providers.model_settings/configured_model`, authentication and factory use them; TypeSafe model/HTTP2 is separate. Preserve credentials, provider modes, fallbacks and all these settings. Testing must not make a missing live credential succeed. |
| Public response/file bytes | `block.max_download_bytes` is 10,000,000, with typed and source-wrapper upper ceiling 10,000,000. Factory passes it to GDC, Xena and literature. `bounded_response` checks advertised size and streamed decoded bytes; GDC raw files also require explicitly open access, exact size and checksum. Metadata and failed chunks are charged. Proposed data-only ceilings must be passed selectively to GDC/Xena, leaving literature ordinary. |
| Source and parser shape bounds | GDC search size 1..100, offset 0..1000000 and one declared stable sort; Xena results 1..50; literature results 1..20. Combined pages are limited to 20 with continuity/overlap checks. STAR parsing in `science/representation.py` requires exact source workflow/units, an artifact at most 8 MiB, 1..20 unique selected Ensembl IDs, at most 100000 gene rows, bounded cells and validated numeric values. These independent ordinary constraints can reject an input even if download fits; testing does not truncate a scientific procedure or silently change representation/sample sufficiency. |
| Shared download/disk authority | `ServiceResources`: file 10 MB, block 50 MB, service 500 MB; workspace 100 MB, durable artifacts 1 GB, free-disk floor 10 MB. Factory/service configure it; source meters, discovery meters and local software transfer charge it. `reserve_download` also subtracts held capacity, used workspace/artifacts, retention archive allowance and fourfold disk headroom. Service owns this object across fresh runtimes. Public-data sublimits must share that lifetime without shrinking software reservations or discarding failed bytes. |
| Local software acquisition | `contracts.acquire_github_scientific_method` currently uses `runtime.gdc.reserve(owner, None)`, setting backend download limit from the shared reservation. `LocalVenvScientificBackend` downloads immutable repo tarball/ref metadata and declared wheels, with total pipeline timeout 300 seconds and network fetch timeout at most 20. Metadata parsing cap 262144 bytes; declared wheels max 30. Software bytes are retained/charged on failure too. Decouple this reservation from the data category, preserving ordinary limits. |
| Sandbox and archive controls | YAML backend local_venv, CPU 2, memory 4096 MB, timeout 300 seconds. Local prepare/install/test/execute/replay uses process-family controls and a total wall allowance; extraction caps at 20000 members and half the workspace bytes, forbidding unsafe paths/links. Docker uses per-command timeout, CPU/memory, PID 128, tmpfs 256 MB and credential-free mounts/network phases; its Git/image/install transfers do not currently share the local byte governor. Preserve backend semantics; do not claim universal transfer accounting. |
| Coder/service execution controls | YAML Coder processes/memory/CPU/seconds 16/512 MB/2/60; Science processes 16. `ConfinedBackend` caps requested Coder timeout at service limit and holds heavy lease. `run_owned_command` requires Linux x86_64, nonroot owned storage, cgroup/namespaces/quota and disk headroom, limits output to 1 MB and confirms descendant cleanup. Confinement/credential/network controls in `confinement.py` and trusted launchers fail closed. No testing bypass or native claim. |
| Installed Science | `ScienceExecutor` calls run through `heavy_operation/offload` and drain detached thread work; they do not yet have installed-computation CPU/memory/process-family quotas. A fast profile cannot fill that existing qualification gap. Source design/unit/sample sufficiency, follow-up lineage and explicit admission remain with science/runtime owners. |
| Retention | YAML enabled, minimum age 604800 seconds, archive max 100 MB, workspaces 20 per pass. Service invokes `cleanup_workspaces`; only resolved terminal workspaces are archived, verified and removed; active/unresolved/linked paths fail closed. It preserves ledger/scientific records. Limit its traversal to frozen testing workspace root, with no changed retention values or run-root purge. |

### Preservation, assessment and qualification sites

| Boundary | Owning flow and consequence |
| --- | --- |
| Immutable records and recovery | `SqliteResearchStore` opens/schema-initializes at construction and enforces append-only records. `recover_interrupted_blocks` can append correction/terminal records; `ResearchMemory.backfill` appends derived digests. Namespace checks must precede all three. No test record UPDATE/DELETE or normal-store recovery is authorized. |
| Continuity and decision assessment | `AutonomousService._run_once` retains its Director/resources/store, creates fresh runtimes and Researcher blocks, reviews terminal Delta and allocates again. `ResearchMemory`, frontier/program review and persisted scientific attempts/follow-ups supply next-selection context. Retain this flow and inspect multiple cycles for decision changes rather than infer improvement from isolation. |
| Storage/log visibility | `ResearchApplication` and the API expose read-only reconstructed records, dossiers, state, Delta and ledger/service receipts; telemetry remains under existing Logfire settings, and console failures remain available. No new logging registry or forced telemetry change. `ResearcherRunStarted` currently records a hardcoded `var/workspaces/<block-id>` label: update it to the actual frozen path in implementation. |
| Offline analysis/export | `scripts/export_notebook.py --database ... --out ...` can render a selected store prefix without publication; it opens the schema-initializing store, so it is not a strictly read-only file opener. For immutable inspection use SQLite read-only access or a verified copy. `export_snapshot.py` generates an explicit synthetic fixture, not a retained-database importer. Notebook edits are never ingested into science. No existing generic cross-database importer was found in persistence/application/API owners. |
| Scientific admission | `science.admission.admit_scientific_evidence` requires deterministic source/sandbox origin, provenance, source refs and finite numeric values. `validate_sandbox_candidate` checks retained request/input/software/environment, successful command receipts and replay; runtime tools check block ownership before validation/admission. Provided arrays, fixtures and model prose do not gain authority from testing. Ordinary qualifying measurements can still be admitted and assessed in the separate store. |
| Profile and block pins | `institution.application_identity` hashes `src/*.py` recursively, config YAML and pyproject; `HarnessRuntime.initialize_institution`, institution revisions/pins, `BlockManager.registry_pin_provider`, block start and index receipts carry the result. Identity currently has no environment/profile discriminator. Extend this owner once and propagate its frozen testing basis, preserving active block pins. |
| Local qualification / reusable acceptance | `runtime.verification.local_verification_passed` checks contract version, exact application, local_venv, WSL2/platform/interpreter declarations and boolean control groups. It currently has no testing rejection or exact current environment-identity comparison. `governance.review` requires candidate/scope-bound reference/environment/utility/local records, admitted repeated distinct use, licence and supported routes for promotion/update. Reject test-profile qualification here while retaining observations/proposals/rejected reviews; do not disable science or normal governance. No new qualification producer is part of this decision. |

### Existing behavior-test owners inspected

These tests were read, not executed in this documentation assessment. They establish
where to extend coverage, not that the proposed switch works. Follow the test-audit
authoring gate: extend owner-boundary cases rather than assert YAML/source strings.

| Existing owner | Behavior exercised and missing testing-specific proof |
| --- | --- |
| `test_boundaries.py::test_local_credentials_are_loaded_without_overriding_host_environment` | Local credential loading/precedence. Extend to switch parsing and service startup ordering without reading real credentials. |
| `test_live_mode.py::test_allocation_configuration_rejects_inconsistent_bounds`, `test_handoff_preserves_in_flight_source_result_and_blocks_next_request` | Invalid bounds and observable handoff/new-work denial with in-flight preservation. Add effective timing/shorter-user cases at the loader/allocation boundary. |
| `test_boundaries.py::test_public_sources_stop_unknown_length_stream_at_the_byte_ceiling`, `test_download_service_consumption_survives_fresh_runtime_allocations`, `test_failed_local_transfer_retains_billing_receipts_when_budget_is_exceeded` | Streaming ceilings, retained service consumption and actual typed-tool failed software billing. Add data-category isolation and software success unaffected by data-only exhaustion, not fabricated passing execution receipts. |
| `test_persistence.py::test_service_completion_reviews_delta_and_allocates_again_without_deadline_sleep`, `test_service_delivers_relevant_failed_history_to_fresh_researcher` | Director continuity, Delta/next allocation and history to fresh Researcher with scripted agents. Add actual namespace/path/store checks, environment/constructor escape rejection before writes, fixed settings and distinct-process roots. These fixtures do not measure live decision improvement. |
| `test_persistence.py::test_workspace_retention_exports_before_cleanup_and_preserves_active_or_unresolved`, `test_exact_public_artifact_retention_ownership_and_sandbox_replay` | Archive/preservation and owned source/sandbox lineage. Exercise relocated workspace/backend parents without weakening replay/admission. Native execution remains a separate explicit check. |
| `test_persistence.py::test_governance_rejects_unqualified_use_without_revision_or_evidence_mutation` | Missing/invalid local proof and other independent reusable gates; its valid proof is a policy fixture. Add a testing receipt that otherwise satisfies the local consumer and prove that testing-specific rejection occurs, while ordinary admitted evidence remains retained. Existing rejection for missing reference/environment/utility proof alone cannot demonstrate this guard. |

### Continued assessment

The proposed switch is useful for service composition, acquisition, tool selection,
handoff, failure retention and within-process learning/continuation assessment.
The original blanket-budget overlay is unsuitable: it would shrink the behaviors
being assessed and, through shared reservation, restrict repository acquisition.
The smallest justified decision is editable timing plus public-data sublimits,
frozen owned paths and testing-specific qualification consumption, extending the
existing owners. Separate data accounting is necessary for the requested software
exception; a loader-only scalar rewrite is insufficient.

Use a 90-second block allocation and a separate 120-second scenario observation
target. Required sandbox replay/control procedures retain their ordinary limits.
Useful analysis remains possible without reusable qualification; live improvement
and later normal ingestion need
their own actual evidence/selected inputs. These concerns are separated below:
scenario timing is an observation, acquisition/execution still obey ordinary
procedures, exploratory testing does not require reusable qualification, and a
generic importer is not a prerequisite of the switch. The plan retains only the
actual implementation changes needed for the isolated profile.

Documentation assessment checks on this worktree:

- `.venv/Scripts/python.exe -B scripts/check_architecture.py --docs-only`: exit 1,
  `stale architecture projection: AGENTS.md`, reproduced before and after edits.
  This proposal does not refresh unrelated canonical hashes.
- Direct invocation of the existing `check_documents(ROOT)` plus an explicit
  relative-link/heading check for this proposed ADR: exit 0. The main checker stops
  at projection validation before reaching document validation; this narrower check
  does not establish projection correctness or semantic/runtime behavior.
- `git diff --check`: exit 0. Separate whitespace inspection includes the untracked
  ADR, which ordinary Git diff omits.
- Scope review: only this proposal and assigned plan feature spec changed during
  assessment; other initially modified/untracked files retained identical hashes,
  archive deletions retained, and earlier plan sections retained unchanged.

No live provider, native, scientific qualification or implementation behavior test
was run. Decision status remains PROPOSED; this report does not complete the
implementation task, so its completion/log transfer has not occurred.

## Suggested testing application sites and limits

Recommendation updated 2026-10-02 after the documentation cleanup. These are proposed
profile settings, not changes to `config/runtime.yaml` or implemented behavior.
Byte units below are decimal MB, except where MiB is stated. Lower existing user
ceilings win; all unlisted ordinary controls retain their current values.

| Application site | Current configuration / behavior | Suggested testing configuration / behavior |
| --- | --- | --- |
| Enable/profile selection | No `ONCOJEV_TESTING` parser | `ONCOJEV_TESTING=1` in ignored `.env.local`; parameters in existing typed runtime YAML; invalid values fail before storage side effects |
| `BlockManager` allocation | Default/min/max 900/300/3600 s | Default/min/max 90/60/90 s, preserving shorter valid settings |
| Block handoff | Reserve 90 s; default handoff at 810 s | Reserve 15 s; default handoff at 75 s; in-flight work drains |
| Scenario observation | No separate target | 120 s reporting target for a small scenario; not a timeout, reserve, qualification condition or hard pass/fail gate |
| GDC/Xena response and file acquisition | Shared source per-response ceiling 10 MB | Public-data per-response ceiling up to 10 MB; leave sufficient capacity for one ordinary small file |
| GDC/Xena cumulative data | Charged to ordinary block/service totals 50/500 MB shared with other transfers | Additional data-only block/service ceilings 20/50 MB, within the unchanged shared totals; metadata and failed chunks count |
| Software repository/dependency acquisition | Local software reservation currently borrowed from GDC; ordinary file/block/service 10/50/500 MB | Ordinary software reservation separated from data sublimits; retain 10/50/500 MB and all existing disk/extraction/network guards. Data-only exhaustion does not stop a software reservation that otherwise fits ordinary remaining capacity |
| Literature / external catalogue metadata | Literature per response 10 MB; external metadata per response 2 MB; ordinary lookup/result bounds | Unchanged; do not apply the GDC/Xena data-only ceilings here |
| Role and cycle model/provider tools | Researcher 200 model requests/500 provider tools; Director 50/100; cycle 300/700 | Unchanged, including stricter user budgets, Code Mode allowances and reported-cost caps |
| Domain calls | Tool/source/Jev/Reasoner/sandbox 500/100/100/10/5; Jev questions 200; Reasoner model requests 10 | Unchanged; real selection and failure behavior remain observable |
| Retrieval/Jev projections | Search/candidates 20/80; Jev questions per call 100, payload 131072 bytes, projected items/payload 20/65536 | Unchanged, including memory semantics and native Jev responses |
| Director review | 8 event turns; scheduled interval 300 s; material-event and post-block review | Unchanged. Evaluate material/terminal review and multiple cycles in short scenarios; explicitly schedule a longer scenario when assessing the 300 s scheduled-review path |
| Full local execution | YAML already selects local_venv; Linux command-family controls; optional Docker backend | Prefer WSL2/Linux native storage and local_venv. No Docker service is needed for this chosen path, and the switch does not override an explicit backend choice |
| Sandbox pipeline | CPU 2, memory 4096 MiB, wall allowance 300 s, Science processes 16; prepare/install/test/execute/replay | Unchanged; do not shorten or omit scientific phases to hit the observation target |
| Coder/resources/retention | Coder 16 processes/512 MiB/2 CPU/60 s; workspace 100 MB, durable artifacts 1 GB, free-disk floor 10 MB; retention 7 days/100 MB/20 workspaces | Unchanged; retention traverses only the testing workspace root and preserves archived records |
| Durable paths | Normal database/root; default Director `/work/director`; block workspaces | One frozen process root `<data-root or var>/testing/<uuid>/` for database, Director, Researcher and experiments; consecutive cycles share it |
| Measurement and qualification | Ordinary measurement/admission; reusable promotion requires separate complete proof | Ordinary testing measurements can be admitted and inspected. Testing qualification cannot authorize reusable acceptance or normal-application qualification; no execution/analysis ban or new proof writer |

### Selected execution method and timing resolution

Use **WSL2 with local_venv for full application testing**, retaining Windows for
fast configuration, API, lifecycle/Code Mode contract checks and UI work. Inspection
of `agents.py`, `workspace.py`, `runtime/process.py` and `science/local.py` shows why:
Windows omits the POSIX Coder capabilities; controlled external scientific execution
requires Linux x86_64, nonroot ownership, native filesystem storage and kernel
controls. Windows cannot currently exercise that same execution path. Making it do
so requires a separate confinement/resource implementation, which is outside this
profile. Windows checks remain useful and can exercise Director/Researcher tools
that do not require the Linux external-execution boundary.

WSL2 is the recommended platform, not a newly measured speed claim or sufficient
confinement proof. Keep the checkout, environment and configured data root on the
Linux filesystem for Linux runs; Microsoft recommends this placement for performance
in [its filesystem guidance](https://learn.microsoft.com/en-us/windows/wsl/filesystems).
The existing command governor uses systemd; verify the actual user service manager
and required controls rather than assume they work because WSL2 supports
[systemd](https://learn.microsoft.com/en-us/windows/wsl/systemd/).
The local `wsl --list --verbose` inventory showed Ubuntu on WSL version 2; no native
scientific/control probes or platform timings were run during this assessment.

Docker is optional and is not a prerequisite of this testing task. Preserve its
existing normal backend and owned-parent path handling when explicitly selected;
do not require a separate Docker qualification to finish the selected local_venv
testing-profile implementation. Do not silently fall back to unconfined Windows or
change live providers when a Linux control is unavailable.

The timing conflict is resolved by separating **allocation** from **observation**:
90 seconds default block allowance, a 15-second handoff reserve, and a 120-second
reported scenario target. Model requests, already-running sandbox procedures,
draining and Director review retain ordinary limits and may exceed that target.
Report elapsed time and which phases it covers. The switch does not promise a
full scientific trajectory in two minutes or stop necessary procedures to manufacture
one. Choose the scenario scope in AGENTS/the assigned task, not through the switch.

Profile implementation covers environment/path startup ordering, the direct live
script's storage bypass, data-versus-software reservation, frozen identity/pins and
qualification consumption. Analysis uses retained records now; selected later use
retains provenance and ordinary admission. A universal cross-store importer and
scientific improvement measurement are separate work, not blockers for enabling
useful isolated testing. Decision remains PROPOSED and implementation unverified.
