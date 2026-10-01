# Implementation plan

This is OncoJev’s only implementation-phase and status tracker.

## Mission and planning principle

OncoJev is an autonomous computational oncology research system designed to search extremely large biological information spaces.

Its central question is whether high-throughput typed semantic measurement from Jev, dynamically constructed deterministic science, and selective deep reasoning can improve useful discovery per research allocation while preserving candidate recall.

Semantic search and measurement are the core mechanism to deliver and evaluate. The research loop retrieves plausible candidates deterministically, projects bounded structured context, measures semantic properties with Jev, preserves distributions and uncertainty through deterministic frontier policy, and lets the Researcher choose investigation inside its allocation. Science measures and admits reproducible evidence; Reasoner supplies possibilities; durable memory informs the Director's next allocation. This is an adaptive research loop, not a prescribed source-to-analysis sequence.

GDC, Xena, literature and future sources are interchangeable capability adapters selected for a research need. Their integration tests verify adapters; they do not define the system's mission or require every investigation to use the same source, modality or statistical method. Source-specific repairs must not become prerequisites for the provider-independent semantic core.

The original phases below record delivered scaffolding. Their historical **DONE** labels do not certify the stronger completeness, scientific utility, or live-path claims challenged by the engineering audit. The verified follow-up plan in section 10 is authoritative for outstanding work. F0–F3 are implemented; F4–F6 remain planned.

## 1. Architecture, upstream, and tracking

**Status:** DONE

**Goal:** Lock the two-scope architecture, add progressive upstream navigation, and establish this single tracker.

**Scope:** Architecture and capability documentation; `.upstream/INDEX.md`; limited GDC API/model/pipeline navigation; manifest reconciliation for locally cloned procedural and public-source references; and a procedural statistical-method guide. No scientific runtime expansion.

**Acceptance criteria:** The Director/Researcher scope boundary is canonical; upstream navigation is progressive; the manifest remains the pin source; no additional tracker is created; existing executable behavior remains unchanged.

**Dependencies:** Existing repository documentation and local upstream inventory.

**Completion evidence:** `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/CAPABILITIES.md`, `skills/statistical-methods/README.md`, `.upstream/INDEX.md`, and `.upstream/manifest.yaml` updated; focused test suite and architecture check pass.

## 2. OncoLab Index and wrapper contracts

**Status:** DONE

**Goal:** Define a large, bounded-retrieval OncoLab Index and wrapper contracts.

**Scope:** One typed metadata index, bounded deterministic retrieval, initial descriptors, and Director/Researcher index-access tools. No scientific execution wrappers.

**Acceptance criteria:** Indexed existence remains distinct from executable, validated, and reusable capability state; both roles can search/describe the same bounded OncoLab catalogue without receiving it wholesale.

**Dependencies:** Phase 1.

**Completion evidence:** `OncoLabDescriptor`, `OncoLabIndex`, and 100+ initial descriptors implemented; Director and Researcher Code Mode integration exercised with `FunctionModel`; `pytest`, the synthetic slice, and architecture checks pass.

## 3. Initial executable scientific capabilities

**Status:** DONE

**Goal:** Add initial statistics, GDC/Xena, literature, and visualization capabilities.

**Scope:** Typed public GDC/Xena/literature wrappers, a small deterministic NumPy/pandas/SciPy/statsmodels surface, matplotlib SVG artifacts, and their bounded Researcher Code Mode tools. No fixed scientific workflow, controlled-data support, sandbox filesystem/shell access, database/API, or UI.

**Acceptance criteria:** A Researcher can discover and invoke independent source, literature, statistics, and visualization methods through the bounded OncoLab Index; sources cannot receive credentials; acquisition is not evidence; deterministic measurements require explicit evidence admission; all tool activity is recorded in the block ledger.

**Dependencies:** Phase 2.

**Completion evidence:** `tests/invariants/test_boundaries.py` exercises the typed tool surface through Code Mode with transport-safe source responses. A live OpenRouter Researcher run on 2026-09-30 selected public GDC, literature, SciPy correlation, and matplotlib independently through the Index, explicitly admitted its measured result, completed its block, and emitted the ledger-backed log. The UCSC Xena wrapper also retrieved two public TCGA-matching dataset records through its documented Hub query interface. `pytest`, `uv lock --check`, and `scripts/check_architecture.py` pass.

## 4. JevBlock deterministic state and Researcher loop

**Status:** DONE

**Goal:** Implement deterministic ResearchState, Jev projections, and the local Researcher loop.

**Scope:** Immutable provider-agnostic ResearchState, deterministic Jev projections, and block-local Researcher orchestration only.

**Acceptance criteria:** Local decisions respect per-block budgets, soft handoff windows, frontier policy, and scope escalation. No hard cancellation discards in-flight work.

**Dependencies:** Phases 2–3.

**Completion evidence:** `src/researcher/state.py` (immutable `ResearchState`, content-derived `JevProjection`) and `src/runtime/pydantic_ai/contracts.py` (bounded, budgeted Researcher tools) are exercised by `tests/invariants/test_boundaries.py`; `pytest` and `scripts/check_architecture.py` pass.

## 5. Skills and scientific sandbox

**Status:** DONE

**Goal:** Add progressive skills, a scientific sandbox, and GitHub method acquisition.

**Scope:** Controlled procedural use and external software acquisition. Local labskills under `src/oncolab/labskills/` adapt relevant procedural guidance from the pinned K-Dense Scientific Agent Skills and ClawBio repositories without vendoring their code or automatically trusting their skills. Both agent roles use the Pydantic AI Coder harness in the non-root Railway/Linux container; external scientific execution remains Docker-only because WSL alone is not a sufficient isolation boundary.

**Acceptance criteria:** Public GitHub code can run only in an isolated sandbox; `.upstream` is never executable runtime software; sandbox processes receive no provider, SSH, or browser credentials; repository URL, resolved commit, environment, commands, input/output hashes, and exit status are captured; raw output cannot become evidence; and successful execution does not promote a new method to reusable capability.

**Dependencies:** Phases 2–4.

**Completion evidence:** `tests/invariants/test_boundaries.py` covers the credential-free Docker sandbox, receipt fields, replay validation, and non-promotion. The original Linux repository-root Director workspace is superseded by F1's `/work/director` scratch workspace and read-only application access. Each block receives a fresh writable Researcher workspace under `var/workspaces/<block-id>`; provider credentials are omitted from child-command environments.

## 6. Live agent and Jev execution

**Status:** DONE

**Goal:** Enable live Director, Researcher, Reasoner, and TypeSafe execution.

**Scope:** Provider configuration and live integration validation.

**Acceptance criteria:** Credentials, budgets, fallbacks, and live failure semantics are verified.

**Dependencies:** Phases 2–5.

**Completion evidence:** `src/runtime/pydantic_ai/factory.py` constructs a fail-closed autonomous live system from strict configuration; the Reasoner remains independent; TypeSafe failures remain operational; model and scientific-data authentication remain disjoint. Python requires exactly one new block per cycle, launches a Researcher if the Director did not, and produces a deterministic terminal handoff. Live verification uses `.env.local` without logging secrets.

## 7. Persistence and application API

**Status:** DONE

**Goal:** Add durable persistence and the application API.

**Scope:** State, artifacts, and typed backend exposure.

**Acceptance criteria:** Ledger immutability and dossier/evidence boundaries persist across restarts.

**Dependencies:** Phases 4 and 6.

**Completion evidence:** block, ledger, state, measurement, evidence, Jev, artifact, and dossier records are written through during execution to an append-only SQLite file. Restart recovery closes interrupted blocks explicitly. `python -m src serve` runs the autonomous worker and read-only API with a Railway health check.

## 8. Next.js observability UI

**Status:** DONE

**Goal:** Build the observability-only frontend.

**Scope:** Missions, blocks, evidence, dossiers, frontiers, registries, and resource usage.

**Acceptance criteria:** UI consumes typed backend state and is not a scientific authority.

**Dependencies:** Phase 7.

**Completion evidence:** `web/` server components fetch live read models from `ONCOJEV_API_URL` with `no-store`; the generated snapshot is only an offline fallback. The standalone production build preserves epistemic categories and contains no orchestration or evidence-admission logic.

## 9. Autonomous research evaluation

**Status:** DONE

**Goal:** Run and evaluate real autonomous research work.

**Scope:** Reproducible research-evaluation corpus and outcomes.

**Acceptance criteria:** Scientific utility, recall, uncertainty, cost, and safety are evaluated reproducibly.

**Dependencies:** Phases 3–8.

**Completion evidence:** `src/evals/` runs fresh autonomous conditions and reports source-bound evidence, Jev failures, completed blocks, dossiers, hypotheses, resource outcomes, and elapsed time without a hard-coded winner. Deterministic `FunctionModel` tests protect orchestration contracts; live evaluation uses the configured agents and services.

## 10. Verified engineering-audit follow-up — 2026-10-01

**Status:** IN PROGRESS; F0–F3 implemented, F4–F6 remain planned.

**Baseline:** commit `1f2e999a3e23e88da4ece1defce1f09429005120`; checkout was clean before this documentation change. Input: the supplied “OncoJev — Engineering Audit” and four-block findings. Verification used current application paths, configuration, relevant tests, reference documents, installed dependency source, the committed snapshot generator/view, and read-only local SQLite records. No `.upstream/` repositories were searched or executed. No new live/provider calls were made.

**Specification order:** the mission above and the user's explicit semantic-core direction govern this plan. Preserve the epistemic rules and Director/Researcher ownership in `AGENTS.md`, `docs/ARCHITECTURE.md`, and `docs/EPISTEMIC_CONSTITUTION.md`. Where current documentation restricts semantic use more narrowly than the mission requires, plan an explicit, bounded architecture update with the implementation rather than indefinitely deferring the core concept. Keep corrective engineering, semantic search mechanisms, and individual scientific methods distinguishable.

### 10.1 Verified four-block run

The final four cycles in local `var/oncojev.sqlite3` match the user's report. The database has eight cycles and six research-memory records in total; four memory records belong to this run. These records are local evidence, not committed portable verification artifacts.

| Run block | Durable observations | Verdict |
| --- | --- | --- |
| 1: `24bae85d-6169-4679-b2d5-b2c606230972` | Jev Noul `p_true=0.84`; Choice `DEFER=0.73`; frontier `defer`; `ResearcherRunCompleted`. Source-bound LUAD/LUSC project counts 585/504 appear in the recorded result. | Jev use and deferred mutation candidate confirmed. This does not establish mutation prevalence. |
| 2: `464e26ac-52c6-47a2-9860-3d827df0ba91` | `statistical-method-selection` receipt; no Jev output; completed Researcher. Objective references block 1 and its unreachable mutation path. | Prior memory influenced direction; decedent-only summaries are not a censoring-aware survival result. |
| 3: `ad726765-d4db-457b-b8e1-d11420d89ea8` | `reproducible-external-method` receipt; Jev `p_true=0.80`, Choice `DEFER=0.78`, frontier `defer`; completed Researcher. Objective references block 1 and counts 585/504. | Reported skill, Jev use, and completeness cross-check confirmed. Exposure contrasts remain non-computable. |
| 4: `19b7478a-ee24-48c0-9c5f-32e1cf1a7d8a` | Starts at ledger-record seq 1062 and 1209; `UsageLimitExceeded` failures at 1208 and 1210; no `ResearcherRunCompleted`. Block revision 1212 says `complete`/`researcher_returned`; cycle 1216 says `complete`. One source-bound measurement, one evidence record, and a dossier exist. | **Confirmed P0 false completion.** Neither a dossier nor an admitted partial measurement establishes completed survival analysis. |

Research memory is persisted Director prose, truncated to 2000 characters per record. The observed later objectives and summaries reference prior results, so “no memory” or “no influence beyond a single cycle” would be false. Structured, reference-resolving result memory is still missing. `search_oncolab`/`describe_oncolab` return metadata without lookup receipts; Director prose cannot independently prove each Researcher's Index search. Skill receipts prove loading, not execution of an external method.

### 10.2 Finding dispositions and corrected remedies

**Legend:** confirmed = current code supports the defect; partial = narrower defect or overstated impact; design = target feature or policy decision rather than an established regression. Audit IDs retain traceability.

| Audit ID | Verdict and current evidence | Planned treatment |
| --- | --- | --- |
| 1.1 | Confirmed: `oncolab/registry.py` retains new verifications only in memory; `autonomous.py` rebuilds each runtime. Bundled `science.scipy.pearsonr` is orphaned. Partial: phase-3 JSON is present locally but untracked, rather than absent everywhere. Unchanged descriptor maturity is intentional non-promotion. | F2: durable verification receipts, typed reference resolution, tracked redacted artifact. Do not auto-promote after execution. |
| 1.2 | Confirmed structured-memory gap: `cycle.py`, `repository.py`, and Director tools store/read prose; no historical dossier/evidence retrieval; start fields empty; failures not digested. Agent rebuilt per cycle. Partial: durable prose has demonstrably shaped objectives. | F3: typed outcome digests, bounded retrieval, populated start packets; service-owned Director continuity with fresh Researchers. |
| 1.3.1 + block-4 bug | Confirmed: exception recovery catches arbitrary Director exceptions; normal Director return bypasses failure checks and checks only `ResearcherRunStarted`. Default cycle status is complete. Partial: an allocation-only truncation can subsequently launch Python's fallback Researcher, so “no Researcher ran” is not universal. | F0: explicit terminal outcome, completion receipt requirement, failed-run precedence, shared finalization. |
| 1.3.2 | Confirmed startup-only recovery; recovery marks interrupted blocks COMPLETE; reconstruction treats terminal dossier as success. | F0: honest interrupted/failed outcome and idempotent recovery before each service cycle; no scientific-success inference from closure. |
| 1.3.3 | Confirmed: `evals/harness.py` propagates runner errors before reporting metrics; custom runners may write no cycle receipt. | F0: record failed condition and continue remaining conditions; close stores. |
| 1.3.4 | Confirmed POSIX authority exposure at audit: both roles had Coder shell, `/app` was writable, Director workspace was repo root. Researcher LocalWorkspace alone was not OS isolation. | F1 user override: preserve Director Coder in `/work/director` scratch engineering, read-only application access for both roles, and kernel isolation from peers and credentials. Update docs and Linux verifier together. |
| 1.4.1 | Confirmed: positive model duration has no configured maximum; default_seconds is not used by allocation. | F1: configured default/min/max and reserve validation in deterministic allocation. |
| 1.4.2 | Confirmed exceptions on claimed work after handoff/budget exhaustion. Retry/reserve wastage is a plausible risk, not measured for every block. Some cheap tools remain callable. | F1: structured non-retryable stop signals, preserve inspection/finalization and in-flight completion. |
| 1.4.3 | Confirmed nested `usage=ctx.usage`; no explicit nested Researcher limits. Fallback run omits explicit limits entirely. | F1: bounded independent role budgets plus aggregate allocation accounting; test both launch paths. |
| 1.4.4 | Partial: candidate fragments already survive in persisted STATE_REVISIONs; decisions/distributions survive in ledger/JEV_OUTPUT. They are not silently lost from all history. No typed retained-candidate retrieval/resurface path exists. | F2–F3: retained candidate record/read model with linked probe and rejection rationale. Semantic rejection is not a biological negative result. |
| 1.4.5 | Confirmed: ESCALATE has no frontier branch; explicit scope proposals already work. | F4: define bounded escalation semantics; proposal never allocates scope. |
| 1.5.1 | Confirmed lack of source-backed inferential statistics and incomplete AnalysisSpec. Partial: `run_statistics` is intentionally useful exploratory computation; rejecting provided arrays is correct. | F4: keep exploratory path explicit; add resolved acquisition-based analysis with scientific contracts, not an origin relabel. |
| 1.5.2 | Confirmed full sandbox candidate/request not persisted, so replay provenance is incomplete. Persisting only receipt+values still would not allow independent replay after temporary inputs disappear. | F2: persist immutable request/input and execution receipt, output digest/values, environment identity, and validation linkage. |
| 1.5.3 | Confirmed UUID admissions permit duplicate counting; count-only slice evidence can be overstated. Input hash alone is not safe dedup: different fields/methods may share it. Hash currently includes acquisition UUID, so identical newly acquired content can hash differently. Counts can be valid descriptive evidence. | F2/F4: content/analysis identity and descriptive/completeness labels; separate independent replication from duplicate admission. |
| 1.5.4 / J-3 | Confirmed projection omits origin/source_refs/provenance, acquisition summaries, and evidence links. | F2: bounded typed scientific context in versioned content-addressed projection. |
| 1.5.5 | Confirmed numeric acquisition summaries silently drop absent/non-numeric/nonfinite values without counts; sample SD of one observation becomes 0. Exploratory descriptive_summary rejects nonfinite inputs before counting missingness, so its missing count is always zero on accepted inputs. | F4: explicit missing/invalid denominators and undefined statistics; no missing-to-zero substitution. |
| 1.6.1 | Confirmed CAPABILITY_INVOCATION adapter has no caller, although ledger invocation events exist. | F2: use ledger as canonical receipt and derive reconstruction view; avoid duplicate record streams unless a consumer requires them. |
| 1.6.2 | Partial: live dossiers count source invocations correctly (100/12/100/45 in this run). Synthetic snapshot injects an acquisition without invocation, so zero there is correct for attempts. Successful acquisition count and attempt count are different metrics. | F2: separate attempts, successes, failures and bytes; do not replace attempted-call counts with state length. |
| 1.6.3–1.6.4 | Confirmed hardcoded GDC/Xena admission attribution and visualization verification from provided floats. Literature is contextual metadata, not automatically evidence. | F2: explicit wrapper/method identity; remove unsupported figure verification or bind figure to durable measurement. |
| 1.6.5–1.6.6 | Confirmed empty unloaded sources.yaml, budget naming ambiguity, uneven tool claims. Additional defect: factory `or` fallbacks turn configured zero source/Jev/Reasoner/sandbox budgets into nonzero limits. | F1/F5: honor zero, separate Code Mode and allocation budgets; remove empty config or implement it only for a real consumer. |
| 1.6.7–1.6.9 | Confirmed no workspace retention policy; state revisions are available to reconstruction but not runtime resume; StartPacket alias unused. | F5: safe retention after durable export; document close-without-resume policy; remove alias if still unused. |
| 1.7.1 | Overstated: `test_build_system_is_live_fail_closed_and_roles_stay_independent` exists in test_live_mode.py. Actual `AutonomousService.run_once -> build_system -> run_cycle` completion/failure integration remains uncovered. | F0–F3: service-path verification with controlled transports/model responses and a separate redacted live smoke. |
| 1.7.2 | Confirmed no two-consecutive-service-cycle result/memory contract test. | F3: fresh runtime/restart receives prior typed outcomes; evidence remains references, not injected conclusions. |
| 1.7.3 | Confirmed snapshot generator scripts synthetic acquisition/agents; page shows mode but has no explicit synthetic provenance marker. | F5: separate live/synthetic/offline provenance and persistent presentation label. |
| 1.7.4 | Confirmed no tracked live artifact. Local `var/phase3-live/stdout-2.json` has started/completed, source, measurement, admission and figure receipts; presence does not validate every historical claim against current admission policy. | F2: redacted export with hashes and honest result categories, correct bundled references. |
| 1.8–1.9 / 4.1 | Existing tests support key admission, append-only, failure, deadline and isolation boundaries. “20/20” does not establish OS isolation, complete lifecycle truthfulness, or scientific validity of outputs. | Preserve those guards and correct claims as each affected phase lands. |
| J-1/J-2 | Confirmed no call-level timing/retry/primitive/frontier link or downstream utility measurements. | F2 telemetry; F6 outcome evaluation. Unknown retries/cost stay unknown, not invented zero. |
| J-4/J-5/J-6/J-7 | Confirmed vague Choice labels, empty exclusions, one invocation charging two questions, and Score unused in current production tool. Invocation count itself is valid if named honestly. | F2: definitions/exclusions, distinct batch/question counters; Score remains deferred until a meaningful bounded purpose exists. |
| Part 3 / 4.2–4.4 | Candidate triage exists; the five broader semantic uses and reusable JevCapability workflow are absent. Audit percentages/effort estimates are not independently measured coverage or engineering estimates. | F6 is P1 mission-critical delivery after minimum foundations. Plan bounded memory-frontier semantics and the necessary architecture clarification; no standalone global execution plane or semantic evidence authority. |

Additional verified adapter defect: `GdcPublicSource.search` accepts no page offset and discards response pagination/total metadata. A request is capped at 100 hits. Repeating it cannot prove cohort completeness or pagination, regardless of model prose. This limits that adapter, not OncoJev's research scope. Separately, acquisitions are only in memory; persisted source_refs cannot resolve exact input records after restart. F2 fixes this provider-independent provenance gap; F4 contains the optional GDC adapter repair.

### 10.3 Dependency-ordered implementation batches

Each batch starts PLANNED. Mark DONE here only after its acceptance proof passes. Keep implementation batches small; F0 is the first patch. Phase IDs remain stable for audit traceability; execution priority is **F0 → F1 → F2 minimum semantic foundations → F3 → F6 semantic core**, followed by capability-specific F4 work and F5 operational cleanup. Portable historical exports, complete source integrations and UI cleanup do not block semantic-core development.

| Priority | Deliverable | Why it serves the mission |
| --- | --- | --- |
| P0: F0–F1 | Honest outcomes, bounded allocations and deterministic authority | Search utility cannot be measured honestly if failures appear successful or budgets are unbounded. |
| P1: F2 minimum + F3 | Bounded projections, native distributions, question/call accounting, retained frontiers and typed research memory | Supplies the semantic search substrate across independent blocks. |
| P1: F6 | Capability/method and representation search, candidate triage, hypothesis/test alignment, dossier support and memory-frontier semantics | Makes Jev a repeated decision-relevant measurement mechanism rather than a decorative candidate check. |
| P1: F6 evaluation | Scientific utility, recall and cost under equal allocations across different information spaces | Tests the central research question, not success on one GDC question. |
| P2: F4–F5 and remaining F2 | Specific executable scientific capabilities, adapter repairs, historical artifact packaging and operations | Extends and maintains the research system as needs arise. |

#### F0 — P0: truthful cycle outcomes and recovery

**Status:** DONE (2026-10-01). **Dependencies:** none. **Class:** orchestration correctness.

**Owners:** `src/runtime/cycle.py`, `src/runtime/pydantic_ai/contracts.py`, `src/block/{models,manager}.py`, `src/autonomous.py`, `src/dossier/{models,builder}.py`, `src/persistence/{records,repository,reconstruct}.py`, `src/application/service.py`, `src/evals/{models,harness}.py`.

1. Define typed run/terminal outcomes separating lifecycle closure, successful Researcher return, Director truncation, and scientific objective attainment. A completed run can honestly conclude that an estimand is unreachable; it does not become a successful scientific estimate. Add failed/interrupted terminal representation and an incomplete cycle outcome; update every status consumer.
2. Require a recorded `ResearcherRunCompleted` before successful block/cycle finalization. Under the present no-retry contract, any `ResearcherRunFailed` makes that cycle failed/incomplete even if the Director returns normal text. Reject repeated launches for the same block. Do not mark COMPLETE from `complete_block` before the run completion receipt: record a handoff request and let deterministic finalization close it.
3. Unify nested launch and Python fallback outcome handling. Inspect ledger outcomes after normal Director return as well as exceptions. Recoverable Director truncation must be explicitly classified using installed Pydantic AI exception types; authentication, transport, tool crash, or unknown errors must not masquerade as success. Avoid an arbitrary `UnexpectedModelBehavior` success blanket.
4. Finalize partial dossiers and durable failed cycle receipts for allocated blocks before propagating hard failure. If no block exists, persist a failed cycle without inventing a block/dossier. Invalid multiple allocation finalizes all created blocks as failed. Record explicit Director failure/truncation details separately from scientific findings.
5. Use idempotent, crash-recoverable terminal writes; a partial append sequence must not allow a dossier alone to suppress needed recovery. Run recovery before each service cycle, closing interrupted blocks honestly without resuming research. Do not use stale block-write time as the recovery-event time.
6. Evaluation catches a failed condition, records failure metrics and retains partial results, then runs remaining conditions. Account for custom-runner failures without duplicating cycle receipts. Reconstruction/API/completed_blocks use honest run outcomes, including legacy contradictions.
7. For existing block 4 and any matching history, plan an append-only correction receipt linked to original seqs; effective read models show failed/incomplete. Preserve original cycles, dossiers, measurements and evidence; never UPDATE/DELETE or relabel historical evidence as a completed survival estimate.

**Acceptance:** a normal-returning Director after two swallowed nested UsageLimitExceeded errors cannot yield success; failure after a handoff request is still failed; valid completed runs succeed; post-completion Director truncation is represented separately; fallback failure, pre-allocation failure, invalid block count and interrupted writes remain honest. Recovery is idempotent. No failed/interrupted run counts as successful evaluation completion.

**Primary regression owner:** extend `tests/invariants/test_persistence.py` at `run_cycle`/service and reconstruction boundaries, using real Code Mode nested failures where possible; extend test_evaluation.py for failed-condition continuation. These tests must fail before F0 for the intended outcome error, not because mocks fabricate ledger order. Existing successful-cycle tests miss this exact path.

**Checks:** `.venv/Scripts/python.exe -m pytest tests/invariants/test_persistence.py tests/invariants/test_evaluation.py`; `.venv/Scripts/python.exe scripts/check_architecture.py`. Update README and ARCHITECTURE lifecycle claims with the implementation.

**Delivery:** Typed lifecycle/run/Director/cycle outcomes and unknown-by-default scientific objective attainment; one Researcher launch per block; handoff requests defer closure until the run-completion receipt. Nested and fallback runs share receipt handling. Normal Director returns are checked against ledger failures; only installed budget/token truncation exceptions are recoverable, with incomplete cycle status. Hard failures and invalid allocations preserve partial dossiers and failed receipts. Terminal block/dossier writes are atomic and idempotent, cycle starts are durable, and every service cycle recovers pending work without resuming it. Effective API/reconstruction and evaluation completion use run receipts. Evaluation retains failed-condition results and continues, including custom-runner and setup failures.

**Historical correction rollout:** Recovery appends a correction for each legacy completion contradicted by failure receipts or lacking a completion receipt, linking original outcome-bearing sequence numbers. Read models already apply this precedence before corrections are appended. Original records and scientific evidence remain immutable. Existing `var/oncojev.sqlite3` is not modified during implementation; corrections activate at the next service recovery. F5 snapshot regeneration and UI labels remain separate.

**Regression evidence:** Before the fix, the real Code Mode nested-failure regression failed because `run_cycle` returned normally after two swallowed Researcher usage-limit errors. It now rejects the repeated launch, closes the block as failed, retains a partial dossier and records the original failure type. Additional cases cover handoff-then-failure, fallback failure, pre-allocation failure, multiple/zero allocations, authentication/transport/tool/unknown Director failures, post-completion truncation, SQLite terminal-bundle rollback, database reopen, idempotent recovery and legacy correction precedence. Distinct cycle identities preserve separate receipts for repeated cycles within one mission. F1 budget propagation and Linux coding confinement remain planned; no live provider utility claim is made by these deterministic regressions.

**Verification (2026-10-01):**

| Command / inspection | Result |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest tests/invariants/test_persistence.py tests/invariants/test_evaluation.py` | **32 passed, 1 warning in 42.01s**. |
| `.venv/Scripts/python.exe -m pytest` | **59 passed, 1 warning in 54.66s**. Existing pydantic_graph event-loop deprecation; no new warning. |
| `.venv/Scripts/python.exe scripts/check_architecture.py` | **architecture checks passed**. |
| `git diff --check` | **passed**, exit 0; Git emitted Windows line-ending conversion notices. |
| Read-only SQLite `mode=ro`, with records copied to an in-memory store for effective reconstruction | Eight historical cycles; two contradictory completions. Latest raw cycle remains `complete`; effective cycle is `failed`. No local database writes. |

**Scope preserved:** Existing telemetry/configuration/lockfile edits were retained. No `.upstream` inspection, dependency installation, live provider calls, historical database writes, UI changes, commit or push. README and ARCHITECTURE now document the lifecycle and correction contracts. F1–F6 remain planned.

#### F1 — P0/P1: deterministic allocation, budgets and authority

**Status:** DONE (2026-10-01), with the explicit Director Coder override below. **Dependencies:** F0. **Class:** governance and lifecycle correctness.

**Owners:** `config/runtime.yaml`, `src/config/models.py`, `src/block/manager.py`, `src/runtime/pydantic_ai/{factory,agents,contracts}.py`, role instructions, Dockerfile and `scripts/verify_coder_container.py`.

1. Wire default/min/max block seconds and reserve consistently through factory and manager. Start with current 900s default/90s reserve; choose documented min/max policy (300/3600s is an initial proposal), validating default and reserve relationships. Omitted duration uses configuration; excessive duration is rejected deterministically.
2. Remove `or` defaults for zero-enabled budgets. Name provider request/tool limits, Code Mode execution limits, local resource counters, and batch/question counts separately. Apply explicit limits to nested and fallback Researcher launches, with independent role headroom and aggregate allocation/cost accounting; no unlimited fallback.
3. Preflight new expensive work before side effects, returning a structured non-retryable handoff/exhaustion directive. Keep read-only inspection and deterministic dossier/finalization available. Existing in-flight operations finish; reserve is not a hard cancellation timeout. Charge attempted work including failures and expose remaining counters.
4. **User override:** preserve Director Coder and shell capability for scratch engineering in a separate writable `/work/director` workspace. Make the application tree read-only to Director coding; prevent peer-workspace and credential access. The original removal of Director Coder is excluded. Control/Index/memory/allocation authority remains bounded; semantic-memory retrieval remains F6 work.
5. Protect policy source from the Researcher's unrestricted shell too: runtime policy must be read-only from the coding execution context, with block workspace access and approved scientific sandbox only. A workspace path and `unrestricted_filesystem=False` restrict file tools, not unrestricted shell. Do not treat them as an OS sandbox. Keep provider secrets out of the filesystem mounts and command environment.

**Acceptance/tests:** in boundary/live-mode tests, prove zero permits no calls, oversized allocation is denied, budget consumption is role-bounded in both launch paths, handoff stops new work without cancelling already started work, and completion remains available. Linux container verifier exercises real shell with fake secret sentinels, checks only presence booleans, and proves Researcher cannot write policy or another block workspace while its own workspace remains writable. No real secrets printed. This is platform proof distinct from Windows tests.

**Checks:** focused test_boundaries.py/test_live_mode.py/test_persistence.py plus architecture checker; run revised container verifier in Linux. Update ARCHITECTURE, CAPABILITIES, README and role instructions.

**Delivery:** Factory-enforced 900-second default, 300–3600-second allocation range and 90-second reserve; explicit independent Director/Researcher usage limits in nested and fallback launches, live Reasoner allocation accounting and cycle aggregate guards. Configured zero budgets remain zero. Code Mode executions, per-snippet calls, framework tool attempts, local Science calls, Jev invocations/questions and source/sandbox/Reasoner attempts have distinct limits. New work preflights before effects, emits non-retryable directives and retains attempts on failure; inspection and Python finalization remain available. ModelUsage records retain reported cost even when its response exceeds the aggregate cap, and flag unknown provider cost.

Director Coder is preserved with `/work/director` scratch writes. A command-only workspace backend routes native file tools, shell and descendants through Linux Landlock, failing closed below ABI 3. Both roles read public application files, write only their own workspace, and cannot access peer workspaces, application credential files or process environments. The Docker application is root-owned and the runtime user unprivileged. Scratch coding is separate from scientific replay/admission. Local Linux verification does not certify a remote Railway kernel.

**Verification:**

- `.venv/Scripts/python.exe -m pytest tests/invariants/test_agent_telemetry.py tests/invariants/test_boundaries.py tests/invariants/test_live_mode.py tests/invariants/test_persistence.py` — 60 passed at the focused checkpoint.
- `.venv/Scripts/python.exe -m pytest` — 78 passed, one existing `pydantic_graph` event-loop deprecation warning (69.79s), after the final cost-reporting and zero per-snippet changes.
- `.venv/Scripts/python.exe scripts/check_architecture.py` — passed.
- `docker run --rm --mount 'type=bind,source=C:\dev\oncojev\src,target=/app/src,readonly' --mount 'type=bind,source=C:\dev\oncojev\scripts,target=/app/scripts,readonly' --mount 'type=bind,source=C:\dev\oncojev\config,target=/app/config,readonly' oncojev-f1:local python scripts/verify_coder_container.py` — passed on local Linux x86_64 / WSL2 kernel 6.6.114.1; all 12 shell checks true for each role, plus native Coder own writes, public application reads and denied peer writes. No extra container privileges; fake secret presence only.
- `docker run --rm oncojev-f1:final python scripts/verify_coder_container.py` — passed with the same checks, packaged final runtime source and no bind mounts. The initial Dockerfile dependency image built successfully; an additional full rebuild stalled at export and its client was stopped. Root-owned source overlays (`src`, `scripts`, `config`, then final `agents.py`/`controls.py`) built successfully as `oncojev-f1:verified` and `oncojev-f1:final`, retaining the unprivileged runtime user.
- `git diff --check` — passed (line-ending notices only).

The zero-source regression was separately reproduced against the HEAD factory: configured zero became 20. Current real Code Mode tests deny all six zero local-resource cases before effects. Nested/fallback request limits, framework execution zeros, live Reasoner allocation charging, failed Jev invocation/question charging, in-flight completion and mixed known/unknown response cost are exercised through actual agent/tool boundaries. The SDK requires a positive per-snippet limit internally; configured zero instead disables `run_code` at runtime preflight, with a non-retryable directive and no source effects. Prior F0 and unrelated telemetry edits are preserved. No live provider calls, historical database writes, `.upstream` inspection, UI changes, commit or push. The Docker build installs frozen dependencies inside the image; no local dependency changes were made for F1.

#### F2 — P1: replayable provenance, registry receipts and telemetry

**Status:** DONE (2026-10-01). **Dependencies:** F0–F1. **Class:** persistence/observability; no new scientific method.

**Minimum milestone for F3/F6:** bounded provenance-bearing projections, resolvable references for available research context, native decisions and question definitions/exclusions, call/question budgets, failure/frontier receipts, and retained candidate identities. Historical artifact packaging and full external-software replay enhancements continue as separate F2 batches; they do not delay semantic search over already valid inputs.

**Owners:** `src/sources/models.py`, `src/science/{models,sandbox}.py`, `src/persistence/`, `src/oncolab/{registry,models,proven}/`, `src/researcher/state.py`, `src/runtime/pydantic_ai/{contracts,factory}.py`, `src/jev/{models,client,failure}.py`, `src/dossier/builder.py`, `scripts/check_architecture.py`.

1. Persist immutable public acquisitions and literature-context records before use. Science resolves exact block-owned inputs; reconstruction resolves source_refs to content and request identities after restart. Hash stable scientific content separately from acquisition/run UUIDs.
2. Persist full sandbox request/input, immutable commit, candidate/receipt, output identity and validator version; pin or record resolved environment image identity. Reconstruct enough input to independently replay with the same isolated executor; no automatic research resumption or capability promotion.
3. Persist verification receipts and seed the Index from bundled plus durable records through factory composition. Use explicit reference types for file paths, measurement/evidence IDs and artifact IDs. Validate catalogue IDs and resolvability; never assume every execution_reference is a filesystem path. Deduplicate loading by verification identity. Verification is scoped to a declared execution, not maturity of an entire statistics family.
4. Correct the orphan record using its actual catalogue identity and verified execution scope. Export a redacted, integrity-hashed portable local live record under a tracked verification-artifact path and repoint bundled records. Redaction changes bytes: hash the redacted artifact and record provenance accordingly. Never commit `.env.local` or fabricate missing run details.
5. Add Index search/describe receipts with actor, query/filters, bounds, returned IDs, selected ID when chosen, and block/mission association. Researcher searches obey configured cap. Director receipts can precede block allocation. Preserve skill-load receipts separately. Derive canonical invocation views from ledger rather than keeping an unused parallel adapter.
6. Add Jev call IDs, projection/question specifications and hashes, requested/resolved model, primitive types, duration, reported retry metadata, outcomes and frontier linkage. Preflight SDK-spec validation and record construction/decoding failures operationally too. Do not invent SDK retry counts or token costs. Bound payload bytes/questions and reject duplicate question IDs before dict conversion.
7. Add structured acquisition summaries, origin/provenance/source/evidence references and result limitations to Jev projections; enforce count/byte bounds as state grows. Version projections, question templates and policy; replace vague Choice definitions and populate exclusions. Actually deliver exclusions to the SDK, since `_spec_for` currently forwards only instructions/criteria. Distinguish invocation and question counters; attempts/failures count toward configured budgets.
8. Fix wrapper/method verification attribution; bind figures to measured input or stop calling exploratory pictures verified science. Count source attempts, successes, failures and bytes separately; retain ledger as attempted-call authority.
9. Persist retained/rejected candidate identities, summaries, distributions, projection and policy rationale. Preserve unknown/ambiguous candidates. These are semantic search history; a scientific negative finding requires its own admitted measurement.

**Acceptance/tests:** persistence restart reconstructs exact source input and sandbox replay request; verifier detects orphan/unresolved typed refs; new Index search has a durable receipt; duplicate loads do not duplicate verification; provided values stay provided in a bounded projection; SDK-construction failure has an operational receipt and no frontier judgment; two-question batch consumes two questions and one call. Extend persistence/boundary/live-mode tests at owning boundaries.

**Checks:** focused persistence/boundary/live-mode tests and architecture checker including new verification integrity checks. Update CAPABILITIES/JEV/proven record semantics.

**Delivery:** Exact acquisition and literature records are stored before use; Science resolves block-owned acquisitions, and reconstruction exposes retained inputs plus unresolved legacy references. Stable content identity excludes acquisition/run UUIDs. Sandbox requests, inputs, outputs, commands, validator version and immutable commit/image identity survive restart, with explicit independent replay and no automatic resumption. Factory composition loads validated bundled and durable scoped verification receipts idempotently. The orphan Pearson record now identifies `stat.scipy` and its specific historical invocation; bundled records resolve the tracked redacted ledger artifact by SHA-256 and disclose unavailable historical inputs. Exploratory figures and supplied-array statistics do not establish verified science or capability promotion.

Index search/describe/selection receipts include actor, limits, catalogue identities and mission/cycle/block scope; Researcher searches obey configuration. Invocation reconstruction derives from the canonical ledger. Source attempts, successes, failures and reported bytes remain separate. Version-2 Jev projections retain origins, acquisition summaries, measurement/evidence references and limitations under item/byte bounds. Version-2 questions deliver full definitions and exclusions to the native SDK. Calls retain IDs, specifications, hashes, requested/resolved models, timing, native distributions and reported usage; construction/decoding failures remain operational. Duplicate IDs are rejected before dispatch. Candidate history retains summaries, distributions and `candidate-frontier-v1` rationale without scientific-negative inference.

**Verification:** `.\.venv\Scripts\python.exe -m pytest tests/invariants/test_persistence.py tests/invariants/test_boundaries.py tests/invariants/test_live_mode.py` passed 70 tests. `.\.venv\Scripts\python.exe -m pytest` passed 83 tests. Both reported one existing `pydantic_graph` event-loop deprecation warning. `.\.venv\Scripts\python.exe scripts/check_architecture.py` and `git diff --check` passed. Against the pushed baseline, the restart regression failed because exact acquired inputs were absent; duplicate question IDs collapsed into one provider specification while producing two decisions. Current regressions exercise actual Code Mode, SQLite reopen and native SDK construction/decoding boundaries, including failed attempts and unknown retry metadata. Publication checks compare staged and working artifact SHA-256 values; the exporter emits UTF-8 LF bytes and `.gitattributes` preserves LF on checkout. After this portability correction, the capability-index integrity regression passed (1 test), and architecture/staged diff checks passed again.

**Scope and limits:** F0/F1 plus preserved telemetry were committed and pushed first as `dc0b74a6781ae9c62c3b59baf78c09226f585e06`; remote `main` was verified at that SHA. F2 implementation and verification are recorded in the subsequent provenance/telemetry delivery commit. Director Coder and `/work/director` scratch authority are preserved. No new scientific methods, live provider calls, historical database writes, local dependency changes, UI work or `.upstream` inspection. Sandbox command/replay routing is tested with controlled CLI responses; this is not a new live external-software utility claim. Installation dependencies are not independently locked: their uncertainty is recorded, and independent replay rejects changed output. Missing historical acquisition/measurement/SVG bytes remain missing. Research memory retrieval and downstream semantic utility remain F3/F6 work.

#### F3 — P1: typed cross-cycle memory and start packets

**Status:** DONE (2026-10-01). **Dependencies:** F0 and F2 minimum milestone. **Class:** continuity and retrieval, not scientific admission.

**Owners:** new typed memory domain/read service, `src/director/models.py`, `src/block/manager.py`, `src/autonomous.py`, `src/runtime/{cycle,pydantic_ai/contracts,pydantic_ai/factory}.py`, `src/persistence/`, `src/application/service.py`.

1. Append a versioned typed digest for every cycle outcome: mission/block/objective, lifecycle/run status, termination/failure reason, evidence/dossier/measurement refs, descriptive result limitations, hypotheses, scientific negative findings, semantic retained/rejected candidates, operational blockers, unresolved uncertainty, continuation proposals and measured resource use. Director prose is an optional note, never the canonical digest. Validate references without admitting evidence.
2. Backfill only from resolvable historical records using appended derived records. Mark legacy prose context and inferred/contradictory outcomes explicitly; do not reinterpret unsupported narrative claims as facts. F0 correction precedence applies to block 4.
3. Implement bounded deterministic memory search and get_dossier/get_evidence/get_hypotheses/get_negative_results/get_open_uncertainties with mission/entity/topic/time filters and stable ties. Separate scientific null/negative results from semantic rejection and source/provider failure. Read historical blocks from persistence, not the new runtime's manager.
4. Supply a bounded retrieved digest context to the Director and deterministically populate selected start references, prior failures, uncertainty, candidate directions and constraints for the current objective. Retrieve by relevance, not “always copy the newest digest.” Deliver that validated start context to the fresh Researcher; no prior Researcher transcript or whole-memory dump.
5. Own the Director instance at service lifetime through the single factory composition boundary. Durable structured memory remains authoritative across process restart; bound any retained Director messages. Preserve fresh Researcher/state/skills/budgets per block. Evidence and measurements are reference-resolved context, not inherited admission authority.

**Acceptance/tests:** two consecutive `AutonomousService.run_once` cycles with fresh block runtimes consume the first cycle's typed outcome through the actual tools/start packet; repeat across database reopen. Include failed cycle, no evidence, unrelated newest result and legacy memory. Verify Director receives limitations and failure reason without automatically repeating the failed path; test input availability, not stochastic objective wording. Extend existing persistence fixtures before adding a new test module.

**Checks:** focused persistence/live-mode tests and architecture checker. Update ARCHITECTURE/CAPABILITIES memory and Director-lifetime documentation.

**Delivery:** `src/memory/` derives append-only `research-memory-v1` cycle digests from persisted records, including failed/pre-allocation cycles, interrupted terminal blocks and labelled legacy prose. References pin kind/sequence/identity/owner/hash; unresolved historical inputs stay explicit. Corrections and later source records append new snapshots, and retrieval selects the latest per cycle. Digests retain lifecycle/run status, termination/failure reason, dossier/evidence/measurement references, limitations, hypotheses, candidate history, blockers, uncertainty, proposals and recorded resource/model use. Director prose is an optional note, excluded from canonical relevance and start context. Scientific-negative results remain a separate typed collection; current Science outputs do not declare those interpretations, so they remain empty rather than inferred.

Deterministic token-overlap search has stable identity ties and mission, declared entity/topic and timezone-aware time filters. Historical getters resolve persistence rather than a fresh manager. Both roles receive bounded search and reference-resolution tools. Director input automatically includes relevant structured memory; allocation retrieves for its actual objective and persists a validated start packet. Nested and Python fallback launches deliver that packet without prior Researcher messages, inherited evidence/measurements, skills or budgets. Retrieved digest context is limited to 32 KiB and start memory to 16 KiB, with item omissions/text truncation recorded. API reads stay read-only and retain derived summary/provenance fields for existing observability consumers. Service lifetime owns one Director through factory composition; previous Director message retention is zero.

**Verification:** `.\.venv\Scripts\python.exe -m pytest tests/invariants/test_persistence.py tests/invariants/test_live_mode.py` passed 59 tests; `.\.venv\Scripts\python.exe -m pytest` passed 87 tests, each with one existing `pydantic_graph` event-loop deprecation warning. `.\.venv\Scripts\python.exe scripts/check_architecture.py` passed, now also preventing memory from bypassing admission. The service/factory/Code Mode regression covers consecutive cycles, database reopen, nested/fallback launch, prior source and Researcher failures, no evidence, unrelated newer history, legacy prose, entity/topic/time filters and reference resolution. The legacy fixture checks correction precedence, immutable originals, changed-reference denial and large Unicode context bounds. Against the pushed F2 baseline, the service regression failed at the intended assertion: the next Director lacked the prior `UsageLimitExceeded` outcome; only baseline tool-signature arguments were adapted for that reproduction.

**Scope:** F3 implementation and verification are recorded in the typed-memory/start-packet delivery commit. No live provider calls, historical database writes, new scientific methods, `.upstream` inspection or UI implementation. Director Coder and `/work/director` scratch authority remain preserved. These checks prove deterministic continuity and input availability, not stochastic wording or downstream semantic utility; semantic memory ranking and utility evaluation remain F6.

#### F6 — P1: semantic search and measurement core

**Status:** PLANNED. **Dependencies:** F0–F1 and F2 minimum milestone; memory-frontier and cross-block hypothesis work additionally require F3. **Class:** core research mechanism and thesis evaluation. No dependency on GDC pagination, a specific modality, completion of F4, or F5 UI cleanup.

**Owners:** `src/jev/`, `src/oncolab/`, `src/researcher/state.py`, `src/director/`, `src/dossier/`, `src/evals/`, and orchestration integration under `src/runtime/pydantic_ai/`; update `docs/ARCHITECTURE.md`, `docs/JEV.md`, `docs/CAPABILITIES.md` and this tracker with each delivered contract.

Deliver semantic search as a repeated, inspectable part of the autonomous loop: deterministic high-recall retrieval → bounded structured projections → batched atomic semantic measurements → full distributions → deterministic multidimensional frontier policy → autonomous investigation or next-allocation proposal. The decisions span capabilities/methods, representations, candidates, hypotheses/tests, dossier interpretations and research-memory relevance. These are decision contexts within Director Control and Researcher blocks, not six new global services. Each probe stays local until validation and utility evidence justify reuse; no audit threshold is adopted as a universal scientific rule.

**Delivery order:** F6a capability/method selection and dossier support over available contracts; F6b representation sufficiency and candidate-frontier management; F6c hypothesis/test alignment and memory-frontier semantics using F3. Evaluation starts with F6a and accompanies every batch. These paths consume provider-independent state and can be verified before adding any new source adapter.

1. Add deterministic dossier reference checks and epistemic labels from F2. The current builder unions evidence IDs; it does not resolve them. Bounded Jev support checks annotate interpretations, never rewrite admitted measurements or prevent a terminal dossier during provider failure. Use per-statement linkage: five questions for a whole dossier cannot validate each claim independently. Record unavailable semantic validation explicitly and preserve the terminal dossier.
2. Deliver Researcher-local capability/method semantic search after deterministic contract retrieval. Measure requested estimand fit, required-variable availability, design/assumption compatibility, active limitations and missingness semantics against bounded typed contracts. Installed status is not scientific suitability; semantic output cannot prove executable availability or scientific validity. Replace the broad lexical installed-method veto with deterministic applicability checks, multidimensional semantic measurements, recall-preserving retention and an explicit inadequacy rationale for acquiring or constructing a method. A Researcher can choose among executable capabilities or dynamically construct deterministic Science under admission controls.
3. Add representation sufficiency and candidate triage only over proven available summaries and executable retrieval rungs. Introduce deterministic candidate identities/generation where a specific domain capability supports it, while preserving model-proposed exploratory candidates. Unsupported modality/missingness is unknown, not false cross-modal support. Preserve beams and retained history under ambiguous distributions; no unsupported aggregation of unequal dimensions.
4. Add hypothesis/test alignment after memory retrieval, with stable identities, exact normalized duplicate detection first, then semantic similarity. String hashing does not detect paraphrase. A semantic REJECT_RETAIN label is never a scientific NEGATIVE_RESULT. Hypotheses remain possibilities, not evidence; test proposals stay within current allocation or go to Director.
5. Deliver bounded semantic measurement over deterministically retrieved Research Memory to inform the Director's allocation frontier. Measure relevance, duplication, contradiction, recurring capability gaps and newly actionable uncertainty; retain material contradictions and uncertain alternatives. Update ARCHITECTURE as part of this batch to describe semantic retrieval as a bounded Control/Research Memory operation, without introducing a standalone global Jev execution plane. Director still allocates, Python composes the frontier and owns budgets, and Jev supplies semantic properties only. Define a separate global retrieval budget and a transparent deterministic fallback on Jev failure; never dump full memory into a model. This is planned core work, not indefinitely deferred architecture scope.
6. Extend evaluation with independent feature flags and comparable allocation budgets, failure/incomplete rates, unique nontrivial source-bound outcomes, retained-candidate recall on a corpus with reference labels, attempted/successful acquisition cost, elapsed time, duplication suppression, provenance support and resolved model/question/policy versions. Include at least two distinct information spaces or capability families and a task that does not use GDC, so improvements cannot be explained solely by repairing one adapter. Null/unknown denominators are not zero scores. Report descriptive evidence separately; no hardcoded winning condition. Measure actual provider usage/cost only when available.

**Acceptance/checks:** a Researcher searches capabilities, evaluates a sufficient representation and manages a candidate frontier using bounded Jev measurements without a prescribed source sequence; differing needs can choose different methods or propose construction. A subsequent Director receives a reference-linked semantic memory frontier that affects the context for allocation without treating semantic scores as evidence. Each delivered decision context has a Science-only/Reasoner/semantic ablation with controlled data and equal limits; preserve recall and log policy decisions/failures. Extend live-mode/evaluation/boundary contracts at their owning boundaries, run architecture checker, then a bounded real-provider smoke with redacted receipts. Deterministic fixtures verify routing, not semantic utility. Use Noul/Choice/Score where their native semantics fit an actual bounded decision; do not add Score merely to satisfy primitive coverage.

#### F4 — P2: dynamically selected scientific capabilities and adapter correctness

**Status:** PLANNED. **Dependencies:** F1 and relevant F2 provenance contracts; F6 selects needs without requiring this entire phase. **Class:** scientific-method changes selected by research need.

**Owners:** `src/science/{models,execution,admission}.py`, `src/sources/{models,public}.py`, `src/researcher/state.py`, `src/runtime/pydantic_ai/contracts.py`, dossier contracts, OncoLab descriptors.

1. Define provider-independent acquisition coverage/completeness contracts for the representation an investigation needs. Repair GDC offset/pagination as one adapter-specific batch when selected work requires it: preserve query/ordering identity, totals and pages; detect overlap. Equivalent adapters implement their own documented coverage semantics. A response slice count is not a population total; unknown coverage remains unknown. GDC pagination is not a prerequisite for F6 or a mandatory step in any research block.
2. Expand AnalysisSpec with actual population/design/estimand, resolved fields, transformations, covariates, missingness policy, diagnostics and declared outputs. Add source-resolved analysis for currently supported methods; deterministic Science constructs inputs and provenance from stored acquisitions, never caller-supplied origin/source_refs. Keep exploratory supplied-array computation explicitly ineligible for admission.
3. Preserve row pairing for correlation/regression, document method assumptions and small-sample/constant-input behavior, and report missing/invalid/nonfinite counts plus valid denominators. A one-observation sample SD is undefined, not zero; model that limitation without nonfinite evidence values. Do not silently compute survival from uncensored death-only rows.
4. Make admission idempotent for the same resolved analysis identity: content+field selection+population+transformations+method/parameters+versions, excluding incidental UUID/analysis labels. Distinct analyses sharing one input remain distinct. Retain execution/replication receipts and record dependency rather than counting duplicate evidence as independent discovery. Science owns equivalence/admission policy, persistence only stores its decisions.
5. Mark count-only and exploratory results, cohort completeness and attainable estimand explicitly in dossiers/read models. Counts may remain admitted descriptive evidence; do not present them as inferential effects. Define Frontier ESCALATE as a bounded local recommendation or Director proposal, never permission to extend a deadline or allocate scope.

**Acceptance/tests:** independent numerical fixtures/known results at Science boundary; incomplete pages cannot claim full cohort, repeated pages do not increase coverage, paired missing data keeps pair identities, missing/nonfinite values remain distinguishable, single-observation uncertainty is explicit, repeated identical admission does not inflate evidence utility, and two different analyses on one acquisition remain available. Current provided/synthetic rejection guards continue passing.

**Checks:** boundary/persistence/evaluation tests and architecture checker; separately review method contracts and diagnostics. Update executable descriptor limitations and scientific documentation. Deliver each method through the shared capability contract only when the Researcher identifies an unmet need; dynamically written deterministic analyses must undergo the same input, replay, diagnostics and admission checks. Kaplan–Meier/RMST/log-rank, bootstrap inference and mutation downloads are possible capabilities, not mandatory roadmap milestones or a predetermined oncology workflow.

#### F5 — P2: retention, cleanup and truthful observability

**Status:** PLANNED. **Dependencies:** affected F0–F3 contracts; specific F4/F6 outputs only where rendered. **Class:** operations/documentation/UI presentation.

**Owners:** `config/`, `src/autonomous.py`, `src/director/models.py`, `scripts/export_snapshot.py`, `web/lib/`, `web/app/`, `docs/`.

1. Remove empty unused source configuration and unused alias/adapters only after checking callers; state revisions remain supported reconstruction history, with interrupted research closed rather than resumed.
2. Add bounded workspace retention after durable provenance/artifact export. Resolve and validate absolute paths under the workspace root, exclude active blocks and unresolved persistence failure, then delete expired block workspaces. Durable evidence/replay data must survive cleanup.
3. Label synthetic fixture, live data and offline fallback separately in snapshot/API types and the UI. Regenerate fixture only after contracts settle. Render effective failed/interrupted outcomes, descriptive slice counts, scientific limitations and corrected legacy cycles; UI only renders backend records.
4. Revise historical completion claims to link portable verification evidence and its exact scope. Do not claim all 100+ descriptors execute or that passing Windows tests validates Linux Coder confinement.

**Acceptance/checks:** focused persistence/frontend tests and architecture checker; exercise retention with sibling/active paths and a reopened store. Validate synthetic/offline banner and failed block detail in browser if UI is changed, plus web build. Avoid source-grep tests for banner rendering when an actual rendered behavior check is available.

### 10.4 Deferred work and stop conditions

- Automatic capability-family promotion, reusable JevCapability discovery, full ten-rung representation ladder, universal candidate generator, semantic self-consistency and full hypothesis frontier refinement remain deferred. Promotion requires a capability-focused block, generalization, declared validation and deterministic governance; accumulating execution receipts is insufficient.
- New survival/mutation/exposure analysis implementations require their own scientific input and diagnostics contracts plus verified source access. Do not infer these methods from the four blocks' partial measurements or build a fixed GDC workflow into the architecture.
- Deterministic metadata retrieval is the first stage of semantic search, not its replacement. Vector retrieval, full reusable-capability promotion and deeper schema-semantic search can follow validated core delivery; capability, candidate, representation and memory semantic measurements are P1 work.
- F0 truthfulness, F1 deterministic controls and the F2 minimum semantic milestone precede live semantic-core delivery. Remaining adapter repairs, historical exports, new scientific methods and UI cleanup do not block it. A Linux test that cannot run is an explicit platform blocker for the affected coding path, not a passing result or a reason to defer all semantic research.

### 10.5 Verification performed for this plan

| Command / inspection | Result |
| --- | --- |
| `git rev-parse HEAD`; `git status --short` before planning edit | Baseline SHA above; clean checkout. |
| Read-only SQLite connection (`mode=ro`) to `var/oncojev.sqlite3` | Eight cycles, six memory records; final four confirmed as in section 10.1. No Index lookup event receipts. |
| In-memory `run_cycle` reproduction: Director allocates, records two started/failed attempts, returns normally | Incorrectly returns cycle `complete`, no error type, dossier reason `researcher_returned`. Confirms owner logic defect independently of the historical ledger; not a committed regression test or model-transport proof. |
| `uv run pytest` / `uv run python scripts/check_architecture.py` | `uv` is not on this shell's PATH. Used existing virtualenv/system Python; no dependency installation needed. |
| `python -m pytest` | System Python lacks pydantic_ai: four collection errors. Environment failure, not product test failure. |
| `.venv/Scripts/python.exe -m pytest` | **36 passed, 1 warning in 22.13s**. Warning: pydantic_graph event-loop deprecation in sandbox tool test. Passing suite does not detect false completion. |
| `python scripts/check_architecture.py` | **architecture checks passed**. Existing checker does not check proven-record integrity or OS shell confinement. |
| Local phase-3 artifact and `git ls-files var` | JSON exists with completed Researcher/source/measurement/admission/figure events; no tracked var files. SHA-256 `d4c3d64375efc97e3171ff9c9416428faef92ddc982bee5b5eae2454ae050934`. |
| Installed Pydantic AI LocalWorkspace/Coder source | LocalWorkspace documents no host isolation and environment allowlist; Coder file confinement does not confine unrestricted commands. Credential omission is source-supported; end-to-end Linux shell/environment proof remains required. |

For every implementation batch: require a credible regression and one primary behavior-level test owner; reuse existing fixtures where possible, add no test-only production seam. Run focused tests and `scripts/check_architecture.py`, then `git diff --check`. At integration completion run the full Python suite and any affected web/Linux checks; record exact commands, results, unresolved blockers and documentary changes here. Only this plan file changed during planning; no source, tests, configuration, ledger or evidence were modified.
