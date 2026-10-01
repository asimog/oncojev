# Implementation plan

This is OncoJev’s only implementation-phase and status tracker.

## Mission and planning principle

OncoJev is an autonomous computational oncology research system designed to search extremely large biological information spaces.

Its central question is whether high-throughput typed semantic measurement from Jev, dynamically constructed deterministic science, and selective deep reasoning can improve useful discovery per research allocation while preserving candidate recall.

Semantic search and measurement are the core mechanism to deliver and evaluate. The research loop retrieves plausible candidates deterministically, projects bounded structured context, measures semantic properties with Jev, preserves distributions and uncertainty through deterministic frontier policy, and lets the Researcher choose investigation inside its allocation. Science measures and admits reproducible evidence; Reasoner supplies possibilities; durable memory informs the Director's next allocation. This is an adaptive research loop, not a prescribed source-to-analysis sequence.

GDC, Xena, literature and future sources are interchangeable capability adapters selected for a research need. Their integration tests verify adapters; they do not define the system's mission or require every investigation to use the same source, modality or statistical method. Source-specific repairs must not become prerequisites for the provider-independent semantic core.

The original phases below record delivered scaffolding. Their historical **DONE** labels do not certify the stronger completeness, scientific utility, or live-path claims challenged by the engineering audit. Section 10 is authoritative: F0–F6 are DONE for their bounded implementation scope; section 10.4 retains deferred extensions and verification limits.

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

**Status:** DONE for the bounded F0–F6 implementation scope. Deferred extensions and verification limits remain in section 10.4.

**Historical audit baseline:** commit `1f2e999a3e23e88da4ece1defce1f09429005120`; checkout was clean before this documentation change. Input: the supplied “OncoJev — Engineering Audit” and four-block findings. Verification used current application paths, configuration, relevant tests, reference documents, installed dependency source, the committed snapshot generator/view, and read-only local SQLite records. No `.upstream/` repositories were searched or executed. No new live/provider calls were made.

**Specification order:** the mission above and the user's explicit semantic-core direction govern this plan. Preserve the epistemic rules and Director/Researcher ownership in `AGENTS.md`, `docs/ARCHITECTURE.md`, and `docs/EPISTEMIC_CONSTITUTION.md`. Where current documentation restricts semantic use more narrowly than the mission requires, plan an explicit, bounded architecture update with the implementation rather than indefinitely deferring the core concept. Keep corrective engineering, semantic search mechanisms, and individual scientific methods distinguishable.

### 10.1 Historical verified four-block run

The final four cycles in local `var/oncojev.sqlite3` match the user's report. The database has eight cycles and six research-memory records in total; four memory records belong to this run. These records are local evidence, not committed portable verification artifacts.

| Run block | Durable observations | Verdict |
| --- | --- | --- |
| 1: `24bae85d-6169-4679-b2d5-b2c606230972` | Jev Noul `p_true=0.84`; Choice `DEFER=0.73`; frontier `defer`; `ResearcherRunCompleted`. Source-bound LUAD/LUSC project counts 585/504 appear in the recorded result. | Jev use and deferred mutation candidate confirmed. This does not establish mutation prevalence. |
| 2: `464e26ac-52c6-47a2-9860-3d827df0ba91` | `statistical-method-selection` receipt; no Jev output; completed Researcher. Objective references block 1 and its unreachable mutation path. | Prior memory influenced direction; decedent-only summaries are not a censoring-aware survival result. |
| 3: `ad726765-d4db-457b-b8e1-d11420d89ea8` | `reproducible-external-method` receipt; Jev `p_true=0.80`, Choice `DEFER=0.78`, frontier `defer`; completed Researcher. Objective references block 1 and counts 585/504. | Reported skill, Jev use, and completeness cross-check confirmed. Exposure contrasts remain non-computable. |
| 4: `19b7478a-ee24-48c0-9c5f-32e1cf1a7d8a` | Starts at ledger-record seq 1062 and 1209; `UsageLimitExceeded` failures at 1208 and 1210; no `ResearcherRunCompleted`. Block revision 1212 says `complete`/`researcher_returned`; cycle 1216 says `complete`. One source-bound measurement, one evidence record, and a dossier exist. | **Confirmed P0 false completion.** Neither a dossier nor an admitted partial measurement establishes completed survival analysis. |

Research memory is persisted Director prose, truncated to 2000 characters per record. The observed later objectives and summaries reference prior results, so “no memory” or “no influence beyond a single cycle” would be false. Structured, reference-resolving result memory is still missing. `search_oncolab`/`describe_oncolab` return metadata without lookup receipts; Director prose cannot independently prove each Researcher's Index search. Skill receipts prove loading, not execution of an external method.

### 10.2 Finding dispositions and unfinished-work reconciliation

The original audit used baseline `1f2e999a3e23e88da4ece1defce1f09429005120`. Section 10.1 and F0–F3 delivery/verification below are historical evidence, not results rerun for this rewrite. Current verified HEAD is `c15164a65a272715fe158a2521a53f9a59023fc7`; initial `git status --short` was empty. F0/F1 shipped in `dc0b74a6781ae9c62c3b59baf78c09226f585e06`, F2 in `7f77d69b20ebc256b4b1cb6492557502b3cd6f91`, F3 at current HEAD. No local database was inspected or changed in this rewrite.

**Current trace:** `run_cycle` checks completion/failure receipts on nested and fallback paths; `AutonomousService.run_once` recovers before composition. Factory/BlockManager enforce defaults, bounds, zero budgets and distinct role/aggregate limits. Repository/reconstruction retain exact parsed inputs, sandbox requests/candidates, typed verification, Index/Jev receipts and candidate history. `ResearchMemory` derives append-only digests, resolves hashed references and supplies objective-relevant bounded start packets. The service retains one Director; `agents.py` constructs fresh Researchers with fresh state, skills and budgets. Existing service/Code Mode/reopen, lifecycle, budget and SDK tests protect these boundaries. This confirms delivered contracts, not live scientific utility or remote Linux isolation.

Each still-open item has one primary disposition; dependencies are cross-references, not duplicated ownership. Completed remedies remain in F0–F3 history. New gaps do not retract historical delivery.

| Origin / commitment | Current evidence or proposal assessment | Primary disposition |
| --- | --- | --- |
| 1.1; 1.7.4: durable verification, orphan Pearson, portable artifact | F2 factory loading and typed/hash resolution delivered; `stat.scipy` names the observed Pearson invocation. Historical absent inputs/SVG remain absent. | Completed F2; remaining claim presentation is F6b. |
| 1.2; 1.7.2: memory/start fields/failures/Director continuity | F3 service/factory/tools and restart regression delivered; prose optional, not authoritative. | Completed F3; semantic ranking separately F4e. |
| 1.3.1–1.3.4, block-4: outcomes/recovery/eval continuation/authority | F0 receipt precedence/corrections and F1 scratch confinement delivered. Historical SQLite not freshly revalidated. | Completed F0/F1; remote kernel proof is a deployment verification requirement. |
| 1.4.1–1.4.3; zero budgets in 1.6.5–1.6.6 | 900/300–3600/90-second policy, stop signals and role/aggregate usage implemented. | Completed F1. |
| 1.4.4: retained candidate history/retrieval | F2 reconstructs identities/distributions/rationale; F3 retrieves reference-linked candidates. | Completed F2/F3; generalized policy separately F4c. |
| 1.4.5: ESCALATE | Enum exists, no frontier branch; scope proposal tool already exists. | F4c. |
| 1.5.1: source-resolved inference/AnalysisSpec | `execute` uses provided arrays, correctly ineligible for admission; source measurement remains descriptive acquisition summary. | F5d. |
| 1.5.2: retained sandbox request/candidate/replay | F2 persists exact request/JSON output, commit/image/validator identity; explicit independent replay. | Completed F2; file bridge separately F5c; dependency locking D8. |
| 1.5.3: duplicate admission/identity/count interpretation | F2 structured hash excludes acquisition UUID; repeated admission still produces new evidence UUIDs; slice limits now explicit. | F5d identity/idempotence; coverage owned by F5b. |
| 1.5.4 / J-3: scientific Jev context | Version-2 projections retain origin, source/evidence refs and limitations. | Completed F2; context-specific extensions in F4, no replacement system. |
| 1.5.5: missingness/undefined statistics | Summary drops absent/non-numeric values without counts; n=1 sample SD is 0. Nonfinite content can fail canonical hashing; exploratory arrays reject it. | F5a, P1 admission-relevant repair. |
| 1.6.1–1.6.4: invocation/metrics/attribution/figures | Ledger-derived views and distinct attempts/successes/failures/bytes delivered; supplied-array figures remain exploratory. | Completed F2; future output presentation F6b. |
| 1.6.5–1.6.9: config/alias/retention/resume | Empty/unloaded sources.yaml and StartPacket alias remain; state revisions are reconstruction, not resume. | F6a; zero handling completed F1. |
| 1.7.1: service-path proof | F3 regression exercises service → factory → cycle, both launches and reopen. No new live service smoke. | Completed deterministic F3; provider smoke accompanies F4a, separate from utility. |
| 1.7.3: synthetic snapshot labels | Live/synthetic/offline provenance and failed-state presentation remain. | F6b. |
| 1.8–1.9 / 4.1: preserve guards/correct overstated claims | Tests protect admission/append-only/lifecycle/budgets; Windows tests do not establish Linux isolation/scientific validity. | F6b remaining historical claim reconciliation; preserve guards throughout. |
| J-1/J-2: telemetry/utility | F2 timing/spec/model/failure/frontier linkage delivered; unknown retries/cost remain unknown. | F4a evaluation, continued with each later context. |
| J-4–J-7: definitions/exclusions/charging/Score | F2 forwards exclusions, separates question accounting and supports Score; candidate tool uses Noul/Choice. | Completed F2; Score only for a justified F4 dimension. |
| Part 3 / 4.2–4.4; old F6 capability selection | Broader semantics absent; installed lexical veto verified in contracts.py. Report effort/coverage percentages unmeasured. | F4a; reusable promotion D1; percentages rejected as planning evidence. |
| Old F6 dossier support | Builder unions evidence IDs; no per-statement resolution/support. | F4b. |
| Old F6 representations/generalized frontier | Narrow candidate heuristic exists; factual availability must be deterministic. | F4c. |
| Old F6 hypothesis/test alignment | Reasoner proposals exist; exact duplicate and semantic alignment mechanisms absent. | F4d. |
| Old F6 semantic memory/allocation; F3 utility limit | F3 deterministic retrieval delivered; relevance/duplication/contradiction/gaps/actionability semantics absent. | F4e. |
| Old F4 coverage/total/pagination/overlap | GDC caps size at 100, accepts no offset, discards pagination. | F5b. |
| Old F4 design/estimand/fields/transforms/covariates/pairing/diagnostics | Small AnalysisSpec/equal-array-length checks do not establish source-resolved entity pairing/inference. | F5d; current summary bug owned only by F5a. |
| Report exact-byte artifact bridge | Parsed retention is not raw HTTP bytes; sandbox currently mounts JSON only. | F5c; no F4a dependency. |
| Report static entity/key/relationship contracts | Narrow pins support static inspection; graph is not API projection/scientific sufficiency. | F5b when a selected source/join needs it. |
| Report MAF/VCF/count/expression/public inputs | Curated candidates, not executed capabilities/mandatory milestones; broad claims unverified here. | F5e, operation-level feasibility gate. |
| Old F5 operations/observability | Replay artifacts must survive cleanup; UI only renders records. | F6a retention/config; distinct presentation contract F6b. |
| Old 10.4 and F2/F3 limits not resolved above | Full promotion/ladders/generators/self-consistency/deeper frontiers/schema search/methods/scale/replay need measured justification. | Deferred D1–D8 in 10.4; nothing discarded. |

### 10.3 Active roadmap and dependency-ordered batches

| Phase | Status | Meaning |
| --- | --- | --- |
| F0 | DONE | Truthful lifecycle and recovery |
| F1 | DONE | Deterministic allocation, budgets and authority |
| F2 | DONE | Replayable provenance, registry receipts and telemetry |
| F3 | DONE | Typed cross-cycle memory and validated start packets |
| F4 | DONE, P1 | Semantic search and Jev measurement core |
| F5 | DONE, P1 correctness / P2 expansion | Scientific execution depth and curated capability expansion |
| F6 | DONE, P2 | Retention, cleanup and truthful observability |

**Mapping:** old F6 → new F4; old F4 → new F5; old F5 → new F6. Historical identifiers in F0–F3 and original verification remain unchanged; apply this mapping to their forward references. Other docs' old F6 semantic-memory references require follow-up with the relevant implementation; this rewrite does not edit them.

**Order:** F4a shipped first with evaluation in the same slice. F4b/F4c then ship independently; F4d uses F4c; F4e uses F3 + F4a/F4c. F5a/F5b and F6a/F6b are independent corrective branches over delivered foundations. F5c precedes file-based F5e operations; F5d uses F5a/F5b, F5c only for files. F5e selects one need after F4a rather than waiting for all F4. Numbering does not serialize every branch.

**Authority throughout:** OncoLab (`src/oncolab/`) and Research Memory (`src/memory/`) remain shared application components, not Director-owned. Director allocates global scope; Researcher chooses inside one JevBlock; Science alone measures deterministically and admits evidence; Jev measures bounded semantics; Reasoner generates possibilities; BlockManager owns allocations/deadlines. Python enforces budgets/admission/reproducible frontier rules. Frontier is decision context, not research strategy. Preserve Director Coder, read-only application access, writable `/work/director`, isolation/credentials, service-lifetime Director/durable-memory authority and fresh Researchers/state/skills/budgets. No global Science/Jev plane, swarm, new agent framework or direct Director acquisition tools.

**Batch discipline:** Each remaining batch states primary behavior owners/checks. Credible bug regressions require before-fix evidence; extend existing service/tool/execution fixtures without test-only production seams or duplicate ownership. Focused tests + architecture checker + diff check required; full suite at integration, Linux/browser checks only for affected paths. Documentation targets below accompany implementation. The later user request authorizes implementation and a commit between completed phases; the earlier rewrite-only restriction is historical.

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

#### F4 — DONE: semantic search and Jev measurement core

**Contract basis:** Reuse `JevQuestionSpec`, `JevProjection`/`ProjectionSpec`, TypeSafe clients/decisions, `JevCallReceipt`, Index receipts, candidate history and `FrontierPolicy`. Centralize/version question definitions and context-specific policy; keep local contracts local. Noul, Choice and Score are primitives; semantic capabilities are versioned measurement contracts composed from appropriate questions over bounded typed context. No parallel semantic framework or second frontier subsystem.

Official [primitives](https://docs.typesafe.ai/primitives), [API](https://docs.typesafe.ai/api), [state](https://docs.typesafe.ai/concepts/state), [batching](https://docs.typesafe.ai/patterns/fan-out) and [Python client](https://docs.typesafe.ai/sdk/python/api/clients/sync) were consulted on 2026-10-01 using the available TypeSafe skill. Installed `typesafe-sdk==0.7.2` supports `system_one(state, questions)`, JSON instructions/criteria and all three primitives; official [changelog](https://docs.typesafe.ai/sdk/python/changelog) currently lists 0.7.2. At rewrite time project `JevQuestionSpec.instructions` was a string; adapter already wraps it/exclusions/failure semantics into structured instructions. Broader JSON instructions are a minimal validated extension only if needed; no SDK upgrade required. Recheck version-dependent behavior before implementation rather than assuming newer docs imply installed support.

Use deterministic checks for routes/access/fields/input presence. Jev cannot certify execution authority or actual input availability. Batch independent questions sharing bounded state; dependent stages construct new context. Retain native distributions, ambiguity and operational failures. Do not collapse unequal dimensions into a universal scalar or add primitives for coverage.

##### F4a — DONE / P1: Researcher capability and method suitability

**Dependencies:** delivered F1–F3. No verified blocker. **Problem → behavior:** Full descriptors and lexical matches obscure unmet needs; deliver research need → deterministic high-recall OncoLab retrieval → compact cards → describe selected IDs → full typed contracts → deterministic execution/input/access checks → atomic Jev suitability → native distributions → existing frontier-policy extension → bounded alternatives for Researcher choice.

**Owners:** `src/oncolab/{models,registry}.py`; `src/jev/{models,client,frontier}.py` plus centralized local questions; `src/researcher/state.py`; `src/runtime/pydantic_ai/{contracts,factory}.py`; `src/evals/{corpus,models,harness}.py`; receipt persistence/reconstruction only as needed.

**Implementation scope:**

1. Search depends on the OncoLab interface, never `catalogue.py` storage. Both search callers need IDs/names/kinds/purpose and concise applicability/input/limitation and declared availability/execution/access signals to select descriptions. Derive bounded cards from these existing descriptor fields; full assumptions/contracts/provenance/verification stay behind describe-by-ID. No speculative Resource/Capability/ExecutionProfile hierarchy. Cards do not supply execution authority. Define the smallest route/input-check binding against actual registered tools/method arguments; availability enums and implementation-reference strings alone are not callable routes. Keep this behind OncoLab/runtime interfaces, not catalogue storage.
2. Preserve separate resource existence, semantics, declared route, actual access/input availability, observed execution, suitability and validation/reuse state. Planning cards may contain metadata-only resources; execution-selection candidates require an actual typed route and deterministic access/input checks. Inaccessible/input-missing candidates remain visible with reasons outside the executable frontier; Jev cannot convert unknown prerequisites to availability.
3. The 20-result cap is per response, not catalogue capacity. Add stable continuation over reproducible snapshot/order and a bounded wider retrieval budget (or equivalent bounded hierarchical coverage); no blanket cap increase or whole-contract context load. Evaluate recall before reranking, including synonym/lexical mismatch cases. Deterministic query expansion/controlled vocabulary needs explicit retrieval version and labelled coverage evidence.
4. Extend bounded projection/specs with scientific need, selected contract identity/version/hash and deterministic check results. Independently measure estimand fit, design/assumption compatibility, required-variable semantic fit and limitations/missingness compatibility where relevant. Actual variable presence is Python's check. Reuse client batching/decoding/receipts; parameterize hard-coded two-question accounting by actual count. Preserve distributions, dimensional policy rationale, ambiguity and useful alternatives.
5. Replace installed lexical veto in `acquire_github_scientific_method` with deterministic eligibility/applicability, bounded suitability context, considered alternatives and explicit inadequacy rationale. Installed lexical match cannot forbid unmet need. Jev failure retains deterministic alternatives/uncertainty, not proof acquisition is needed. Researcher can justify controlled acquisition/construction under existing GitHub URL/budget/sandbox/admission guards. Jev never grants permission. No reusable registration for every scratch repo; preserve Coder.
6. Extend Index/Jev/frontier receipts with retrieval algorithm/snapshot/query/continuation identity, card and expanded contract IDs/versions/hashes, check results, context and policy linkage. Reconstruct retrieval → description → projection/questions → answers/failure → frontier/Researcher choice, separate from actual execution. Bound returned context; record omissions.

**Behavior acceptance:** Actual Researcher Code Mode retrieves a curated set of fitting, inadequate installed, inaccessible, metadata-only and input-missing alternatives. Selected IDs expand explicitly; only deterministically eligible routes enter executable alternatives. Independent semantic measurements preserve distributions/uncertain candidates. Inadequate installed lexical match permits justified bounded external acquisition while arbitrary URL/credential/budget denials remain intact. Receipts survive reopen with complete lineage; failed batch produces no fabricated negative/frontier judgment. Continuation surfaces a useful candidate beyond page one with stable ties/snapshot and explicit exhaustion. Researcher remains action authority.

**Primary tests/checks:** `tests/invariants/test_boundaries.py` owns search/describe/selection and installed-veto before-fix regression through Code Mode; `test_live_mode.py` owns native SDK construction/decoding/failure and actual question charging; `test_persistence.py` owns receipt lineage after reopen; `test_evaluation.py` owns condition/report integrity. Reuse owners, not tests per helper. Run these focused modules and architecture checker. Separate bounded provider smoke (redacted questions/models/receipts, failures retained) from empirical evaluation; fixture routing is not semantic utility.

**Evaluation with F4a:** Label capability-selection tasks with useful candidate sets, ambiguity and plausible lexical mismatches, including non-GDC information space (existing literature/statistical contracts suffice). Measure retrieval coverage before Jev and retained useful-candidate recall after policy. Record candidate identities, uncertainty/native distributions, retrieval/snapshot/projection/question/model/policy versions, operational failures, source attempts/successes, elapsed time and allocation consumption. Compare deterministic, Reasoner-assisted and Jev-assisted conditions under comparable limits where meaningful; declare unequal resource use. Downstream source-bound outcomes only where existing execution supports them, with descriptive scope explicit. Unknown costs/recall denominators/scientific outcomes stay unknown. No winner, SDK-success utility inference or inherited cookbook thresholds.

**Documentation updates:** OncoLab README, JEV, CAPABILITIES, architecture search boundary, eval protocol, tracker. **Non-goals/limits:** no mass harvesting, GDC pipeline/new adapter, general artifact bridge, UI, all semantic contexts or promotion system. Lexical recall is an empirical risk to measure before trusting reranking.

##### F4b — DONE / P1: statement-specific dossier support

**Dependencies:** F2 references + F4a measurement extension; independent of F4c/F5. **Problem → behavior:** Builder unions IDs; resolve deterministic support before semantic annotation per statement.

**Owners/scope:** `src/dossier/{models,builder}.py`, persistence reference resolver, `src/jev/` questions/projections, runtime finalization. Preserve statement epistemic type, actual support and source limitations. No dossier-level judgment standing in for all claims. Missing/wrong-owner/changed references explicit; Jev failure marks unavailable support validation, never blocks terminal construction or rewrites evidence.

**Acceptance/primary tests:** `test_persistence.py` owns terminal build/reopen with valid/unresolved refs, hypothesis versus evidence, overstatement and failed Jev; originals immutable and terminal dossier persists. Focused module + architecture checker. **Docs:** JEV, architecture/dossier contracts, tracker. **Non-goals/limits:** no admission, prose-to-evidence conversion or semantic certainty guarantee.

##### F4c — DONE / P1: available representations and generalized frontier

**Dependencies:** F4a; existing valid inputs, not broad F5 acquisition. **Problem → behavior:** Narrow relevance/action heuristic becomes context-specific multidimensional frontier over available representations/candidates.

**Owners/scope:** `src/jev/{frontier,models}.py`, `src/researcher/state.py`, typed runtime tools, selected OncoLab contract. Check input/rung availability before sufficiency measurement; unknown modality/missingness is unknown support. Generalize existing policy with stable identities, bounded beams/history and explicit question meanings. ESCALATE is bounded local review/Reasoner request or Director proposal under existing budgets; no deadline extension/scope allocation. Add deterministic generation only for a selected domain; model-proposed candidates stay exploratory.

**Acceptance/primary tests:** `test_boundaries.py` owns actual tool outcomes for ambiguous/no-fit/unavailable representations, alternatives and escalation at handoff; `test_live_mode.py` retains operational failure contract. Focused modules + architecture checker. **Docs:** JEV, CAPABILITIES, search/authority architecture, tracker. **Non-goals/limits:** no universal generator/full ladder, automatic experiment choice or universal scalar; evaluate context-specific thresholds.

##### F4d — DONE / P1: hypothesis/test alignment and duplication

**Dependencies:** F4c + F3 historical retrieval. **Problem → behavior:** Repeated/misaligned Reasoner proposals become identified, inspectable alternatives.

**Owners/scope:** `src/researcher/state.py`, `src/memory/` retrieval, `src/jev/` similarity/alignment questions, runtime Reasoner integration. Stable identity and exact normalized duplicates before bounded semantic similarity, then hypothesis/test/estimand alignment. Distinguish paraphrase, independent replication and contradiction; string hashes cannot eliminate scientifically distinct alternatives. In-scope tests or scope proposals remain Researcher choice.

**Acceptance/primary tests:** `test_boundaries.py` owns Reasoner-output → exact duplicate → alignment/frontier cases including paraphrase, different tests and failed semantics; `test_evaluation.py` owns utility/recall report. Focused modules + architecture checker. **Docs:** JEV, memory contracts, tracker. **Non-goals/limits:** hypotheses never become evidence/scientific negatives; full frontier refinement D4.

##### F4e — DONE / P1: semantic Research Memory for Director Control

**Dependencies:** F3 retrieval + F4a measurement/receipts + F4c policy. F4d may enrich labels later without blocking first memory relevance slice. **Problem → behavior:** Deterministic memory gains reference-linked relevance, duplication, contradiction, recurring capability gaps and actionable uncertainty.

**Owners/scope:** `src/memory/{models,service}.py`, `src/jev/` bounded measurement, `src/director/` input contract, `src/runtime/pydantic_ai/{contracts,factory}.py`. F3 retrieval/filtering first; resolve selected references and project small typed context, never whole memory. Separate global retrieval call/question/byte/time budgets with deterministic fallback and failure/omission receipts through existing factory. Generalize existing block-specific Jev call/projection receipt ownership for mission/cycle Control context without inventing a block or parallel receipt stream. Retain contradictions/ambiguity; no retrieval score becomes evidence. Allocation context may use semantics; feasibility needing acquisition/computation belongs in Researcher block. Preserve Director lifetime/start packet behavior.

**Acceptance/primary tests:** Extend `test_persistence.py` service/factory/Code Mode/reopen owner with relevant older/unrelated newer, contradiction/gap/actionability, budget exhaustion and failed Jev returning F3 context; fresh Researcher inherits no authority. `test_evaluation.py` owns memory utility/recall comparisons. Focused modules + architecture checker. **Docs:** ARCHITECTURE bounded Control clarification, memory README, JEV/CAPABILITIES old F6 references, tracker. **Non-goals/limits:** no global Jev plane/director scientific tools/unlimited budget or guaranteed novelty.

**F4 delivery (2026-10-01):** Implemented the bounded first slices of F4a-e through the existing Index, Code Mode, native client, receipts and frontier. Cards/continuation pin snapshot/contract identity; callable routes and owned input checks keep metadata out of executable frontiers. Atomic independent dimensions remain native distributions. External acquisition retains alternatives and inadequacy rationale without the installed lexical veto. Dossier support is per statement with resolved references and terminal failure fallback. Available-representation and hypothesis/test tools retain ambiguity; exact normalized duplicates precede semantics. Selected F3 memory receives bounded semantic annotations under separate global budgets with deterministic fallback and durable retrieval receipts. No framework, global Science, promotion or Director acquisition plane was added.

**F4 verification:** Full `python -B -m pytest -p no:cacheprovider`: 94 passed, one existing event-loop warning, 91.21 s. Architecture checker and `git diff --check` passed. The lexical-veto regression failed on detached c15164 baseline (1 failed, 16 deselected), then passed through the real sandbox/Code Mode path. Native provider evaluation: `python -B scripts/evaluate_selection.py --live --output src/evals/results/f4-selection.json` completed five labelled tasks in deterministic and Jev conditions, no operational failures; four positive-labelled tasks had retrieval/retained recall 1 in both conditions, the unimplemented-survival denominator stayed unknown. Full receipts retain models/distributions/versions/resources; costs and downstream scientific utility remain unknown. This is a small scoped selection evaluation, not proof of semantic benefit. Reasoner-query comparison is supported with explicitly differing resource use but was not run here. Broader empirical calibration, memory/hypothesis utility and domain-specific representation generation remain D2/D4/D5 earned extensions; no provider-response success promotes a contract.

**Transition review:** F4 found an explicit paired-association need represented by the lexical-mismatch selection case. F5 should first repair current summary/admission correctness, retain coverage/entity identity, then add source-resolved paired analysis and exact-byte inputs. A curated per-operation association wrapper can close that need without harvesting GDC or requiring its full caller pipelines. Bulk harvesting, embedding/storage migration and automatic promotion triggers remain unmet. Dependency-lock uncertainty remains D8 and must be visible in file replay.

#### F5 — DONE: scientific execution depth and curated expansion

F4a does not require this phase. Correctness over existing admission paths is P1; new families are selected P2 expansion. F2 already retains parsed acquisitions and sandbox requests/candidates.

##### F5a — DONE / P1: truthful existing source summaries

**Dependencies:** F2; independent of broader F4/F5. **Problem → behavior:** Admissible source summaries report SD=0 for n=1 and omit invalid/missing denominators; represent undefined statistics/diagnostics explicitly.

**Owners/scope:** `src/science/{execution,models,admission}.py`, runtime summary tool, descriptor limitations and affected typed consumers. Preserve total rows, valid numeric, absent/null, invalid-type and nonfinite counts/denominators with declared classification. Never fake zero for undefined SD. Nonfinite canonical content currently fails hashing; distinguish invalid-acquisition failure from analyzable missingness without weakening immutable identity. Exploratory nonfinite rejection is not successful missingness accounting.

**Acceptance/primary tests:** Before-fix Science/tool regression reproduces n=1 with missing/invalid rows. `test_boundaries.py` owns independently calculated summary/admission cases n=0/1/2, null/invalid/nonfinite and constant/small samples; undefined outputs carry reason, not certainty. Persistence checks only if new typed compatibility introduces a distinct reopen risk. Focused modules + architecture checker. **Docs:** Science/descriptor missingness contracts, CAPABILITIES, tracker. **Non-goals/limits:** no new methods/source family; never silently revise historical measurements.

##### F5b — DONE / P1: coverage, population and structural input contracts

**Dependencies:** F2; independent of F4a/F5c. **Problem → behavior:** Response counts lack completeness proof; source contracts make coverage/entity units explicit.

**Owners/scope:** `src/sources/{models,public}.py`, Science input validation, selected OncoLab descriptors, runtime acquisition tools. Preserve query/ordering/release identity when known, offsets/pages/totals, bounds/truncation, duplicates/overlap. GDC pagination repair for selected needs; repeated pages cannot prove completeness. Qualify unknown totals/count-only slices. Derive required fields, join keys, population and multiplicity from declarations. Distinguish unrequested fields from missing analysis requirements and joined rows from unique patients.

Static GDC extraction is a small optional branch for a specific join/field need: static declarations, pin/hash/regeneration, no ORM/admin imports. Internal graph/public API mapping requires actual response verification. Structural validity is not estimand sufficiency. No mandated artifact filenames/global ontology extraction.

**Acceptance/primary tests:** `test_boundaries.py` owns acquisition via controlled transport → Science validation for incomplete/repeated/overlapping pages, missing totals, projected fields and one-to-many joins; joined rows cannot inflate patients. Independent declared fixtures, not extractor-generated expectations. Focused module + architecture checker; named live field/access probes before new source-route claims. **Docs:** source/Science/capability contracts, tracker. **Non-goals/limits:** no fixed GDC workflow/all-example access claims.

##### F5c — DONE / P2: exact scientific file/artifact bridge

**Dependencies:** F2 + relevant F5b request/access contract. **Problem → behavior:** Parsed records/JSON mounts do not support broad file-based Science. Deliver bounded public acquisition → exact retained bytes → immutable typed artifact/content identity → block-owned read-only input → isolated deterministic execution → replay/validation → Science admission.

**Owners/scope:** `src/sources/`, `src/provenance.py`, `src/persistence/{records,references,repository,reconstruct}.py`, `src/science/{models,sandbox}.py`, runtime tools. Derive fields from existing contracts: source/operation/request identity, byte hash/size/format, durable reference/ownership. Release/licence/access conditions only when known. Separate byte/content, logical acquisition and analysis identity. F2 `content_sha256` hashes retained structured source/request/records/public/provenance, not unstored raw HTTP body. Preserve retained inputs across cleanup; resolve owner/hash before read-only mount. Controlled installation network is separate from credential-free network-disabled execution/replay.

**Acceptance/primary tests:** `test_persistence.py` owns byte retention/reopen/hash/wrong-owner/cleanup survival at acquisition-to-execution boundary; existing sandbox transport owner checks mount/replay mismatch. Target Linux verifier separately proves filesystem isolation. Admission rejects unresolved/mutated inputs. Focused modules + architecture checker + affected Linux check. **Docs:** source/provenance/sandbox/CAPABILITIES, tracker. **Non-goals/limits:** no arbitrary URL execution/promotion; immutable image alone does not freeze dependency installation (D8).

##### F5d — DONE / P1: source-resolved analysis and admission identity

**Dependencies:** F5a/F5b; F5c only for files. **Problem → behavior:** Scientifically explicit source-resolved analyses and idempotent admission prevent misleading/inflated utility.

**Owners/scope:** `src/science/{models,execution,admission}.py`, `src/evidence/models.py`, runtime tools, persistence lookup, selected descriptors/dossier contracts. Expand AnalysisSpec with actual population/design/estimand, resolved fields/entity units, transformations/covariates, missingness policy, assumptions/diagnostics/declared outputs. Deterministically construct inputs from block-owned acquisitions, not caller origin labels. Preserve paired row identities, not just array lengths. Account for missing/invalid/nonfinite denominators, constant/undersized/undefined statistics. Stable analysis identity includes input content, selections/fields/transforms/parameters/method/version/design; byte hash or caller ID alone insufficient. Duplicate admission returns existing identity; explicitly identified independent replication stays distinct. Descriptive/inferential/coverage limits survive projections/dossiers.

**Acceptance/primary tests:** `test_boundaries.py` owns source-to-Science/tool/admission with independent known numerical results, adversarial pairing, assumptions and exploratory-array rejection; duplicate bug requires before-fix evidence. `test_persistence.py` owns repeat admission/reopen without inflated evidence and distinct analyses on one input. `test_evaluation.py` counts unique outcomes/replication correctly. Focused modules + architecture checker; scientific review of estimand/diagnostics. **Docs:** Science/evidence/capability/identity contracts, tracker. **Non-goals/limits:** no relabelled arrays, inference from counts or mandatory survival/TMB.

##### F5e — DONE / P2: one curated capability selected by research need

**Dependencies:** F4a identifies need/inadequacy; relevant F5b/F5d, F5c for files. Standalone fixture transform need not wait for full caller pipeline. **Problem → behavior:** Useful upstream ideas become truthful per-operation capabilities with actual prerequisites/scoped verification.

**Owners/scope:** selected `src/science/` or `src/sources/` wrapper, OncoLab contracts/proven records, runtime tool; no upstream runtime imports. Candidate menu: MAF schemas/inheritance/masking/vocabularies; validation/read/write/sort/overlap; scientifically explicit caller merge/filter/metrics; selected VCF transforms; STAR/junction/count merging and FPKM/FPKM-UQ with gene/count/length checks; public mutation/expression/copy-number/clinical inputs; static contracts via F5b. Narrow gdc-tosvc/GATK/Sanger postprocessing may be useful independently. NormalDepth absent cutoff and filter-annotation counts require verified semantics, never assumed zero filtering/prevalence. TMB needs somatic-count/capture denominator/reference contracts; survival needs censoring/time/design/diagnostics. These are candidates, not workflow milestones.

**Operation gate:** INDEX → manifest → actual clone pin → smallest implementation/tests, then stop. Record missing wrapper, missing input, unsupported environment, credentials, unknown licence/access or explicit prohibition separately. GitHub visibility is not licence certainty; no unsupported non-redistributability claims for BAM/reference/PON/images/capture inputs. Verify selected current anonymous route/artifact constraints before declaring executable sources. Correct impossible-work blocker descriptions here. No execution receipt for reference inspection; fixtures prove scoped execution, not live utility; one receipt never promotes family.

**Acceptance/primary tests:** `test_boundaries.py` owns actual wrapper on independently verified valid/invalid inputs/prerequisite failures; persistence only for novel behavior beyond F2/F5c. Focused modules + architecture checker; scoped live acquisition/execution only when claiming it. **Docs:** descriptor/prerequisites/provenance/scoped record, tracker. **Non-goals/limits:** no whole-repository certification/all-GDC audit/harvesting targets/ORM/admin exposure/mandatory TMB/survival; additional families D7.

**F5 delivery (2026-10-01):** All five bounded batches shipped. Source summaries preserve classification counts/undefined SD rather than fabricate zero. GDC offsets/order/totals/unique IDs survive retention; ordered page composition rejects overlap/gaps/mixed queries/changing totals and discloses absent snapshot guarantees. Source-resolved Pearson/simple OLS constructs complete pairs from unique entity rows, retaining fields, design, estimand, transformations, exclusions and associative limits. Unsupported covariates/joins fail explicitly. Stable scoped admission reuses evidence; declared replication stays separately identified without claiming independence. The first curated operation closes F4's paired-association need; a portable three-row fixture verifies that operation only. Optional GDC static extraction and other candidate families remain selected-need branches D7, not mandatory broad delivery.

ScientificArtifact retains exact bytes with owner/source/request/hash/size/format in immutable persistence; controlled open GDC acquisition validates access, bounds, size and source MD5 when available. Science sandbox requests retain owned bytes and mount `/input/artifacts/<hash>` read-only, with network-disabled execution/replay. Resolution and validation reject corrupted/wrong-owner inputs. No general arbitrary-URL execution or promotion exists. Structured acquisition hashes remain distinct from raw byte hashes; dependency installation remains unlocked (D8).

**Newly verified F2 gap:** Execution and later validation of the same measurement originally reused one immutable verification ID, causing an identity-rebind failure. F5 now includes record kind and outcome in new verification IDs. Historical receipts were not altered. The paired Code Mode regression exercises both transitions and duplicate admission.

**F5 verification:** `python -B -m pytest -p no:cacheprovider`: 99 passed, one existing warning, 91.72 s. Summary/admission regression tests on detached `0b8d4fa` failed on SD=0 and distinct repeat UUIDs (2 failed, 18 deselected); current tests pass. Real Code Mode covers retained source pairs and file acquisition → retained owner/hash resolution → controlled sandbox/replay → Science validation/admission, plus SQLite reopen. `python -B scripts/verify_scientific_artifacts.py` passed real Linux read-only input/root mounts on image `sha256:1c6bfc53933fc364bee31525905264a63967566add58cba2077be8743f50a5da`; this is fixture mount proof, not external-software utility. Anonymous acquisition of documented GDC UUID `353efa55-06d3-43a8-adf5-50f3219e9f14` succeeded: 51,100 bytes, SHA-256 `8c8fe077f4e6d3b02301c4df5d6d72b66b37c02271a479087d330e3f90030b69`, metadata open, source size/MD5 matched; licence/release unknown. This scoped probe was temporary, with no live scientific admission or claim of retained historical replay. Architecture/diff checks passed; no dependency installation or upstream runtime imports.

**Transition review:** Retained scientific inputs now live outside scratch workspaces, enabling F6 archive-before-cleanup. Preserve active/unresolved blocks and persistence failures. F4 evaluation does not justify bulk harvesting, embeddings, registry migration, ontology prerequisites or promotion. Additional methods/static GDC joins, stronger dependency locks and expanded scientific/semantic utility evaluations remain earned deferrals. F6 should also repair the snapshot's synthetic rows being presented as source-bound evidence and live UI inheriting offline evaluation-condition labels.

#### F6 — DONE: retention, cleanup and truthful observability

##### F6a — DONE / P2: safe retention and dead configuration

**Dependencies:** delivered F0–F3; F5c retention contract when introduced, not all F4/F5. **Problem → behavior:** Bound workspace growth/unused config without losing evidence inputs.

**Owners/scope:** `config/`, `src/autonomous.py`, `src/director/models.py`, persistence retention references. Remove empty sources config/unused aliases/adapters after caller verification. Retention only after durable artifact export; validate resolved absolute path under workspace root; exclude active blocks/peer paths/unresolved persistence failures. Preserve evidence/replay data/state history; close interrupted work without resume.

**Acceptance/primary tests:** `test_persistence.py` owns retention/reopen, active/sibling/escape paths, failed export/unresolved persistence and surviving inputs using temporary roots. Focused module + architecture checker. **Docs:** retention/runtime config, README/CAPABILITIES, tracker. **Non-goals/limits:** no ledger deletion/evidence rewrite/cleanup before durable export.

##### F6b — DONE / P2: truthful presentation and historical claims

**Dependencies:** delivered lifecycle/provenance/memory; later outputs only where rendered. **Problem → behavior:** Explicit live/synthetic/offline and failed/incomplete/limited outcomes replace overstated presentation.

**Owners/scope:** application read models, `scripts/export_snapshot.py`, `web/lib/`, `web/app/`, nearest docs. Render backend epistemic categories/effective corrections, failures/incomplete outcomes, attempts versus successes, descriptive slice limits. Separate synthetic fixture provenance from live data and offline transport. Reconcile historical phase claims with portable verification's scope/missing artifacts; Linux proof remains platform-scoped. Regenerate snapshot after relevant contracts settle.

**Acceptance/primary tests:** `test_frontend.py` owns rendered provenance/outcome behavior with browser checks/web build when changed; persistence retains effective read-model authority. Focused affected checks + architecture checker. **Docs:** FRONTEND/README/historical verification explanations, tracker. **Non-goals/limits:** observability only; no orchestration/admission/backfill on reads or all-descriptors-execute claims.

**F6 delivery (2026-10-01):** Archive-before-cleanup retains exact scratch bytes and an immutable manifest before bounded terminal-workspace removal. It excludes active/unknown/unresolved blocks, peers, symlinks/junctions, changed files and failed exports. Defaults are seven days, 20 workspaces, 100 MB each; oversized archives are skipped. Durable scientific inputs, evidence, replay records and ledger history survive reopen. Cleanup/deletion/receipt failures remain explicit and do not grant agent authority or resume research. Director scratch is excluded. Removed verified unused sources configuration, StartPacket/Dossier aliases and unused Jev search/Director frontier configuration; actual Index candidate budget remains separate from response cap.

Synthetic acquisition origin now propagates through deterministic measurements and cannot be admitted. Snapshot generation retains synthetic rows/measurements with zero scientific evidence and no claimed evaluation conditions. UI separates transport, provenance and mode, shows failed/incomplete outcomes, objective uncertainty, source counters, statement support and scientific interpretation/limits. API read views omit binary payloads with an explicit flag while canonical retained bytes remain intact. Source counters cover recorded invocation identities, not inferred historical unrecorded activity. Historical F0–F3 evidence and portable verification scopes remain unchanged.

**Additional verified F5 corrections:** GDC endpoint/entity-unit mismatch could label file rows as patient units; top-level entity IDs must now match endpoint units and joined analyses require a separate contract. Provided-array statistics now explicitly label exploratory interpretation; undeclared legacy/sandbox interpretation remains unclassified, rather than silently descriptive. Both regressions failed on detached `7f6c744` for their intended assertions (one unit mismatch and one exploratory-label failure), then passed. These are separate newly verified gaps, not changes to historical delivery evidence.

**F6 verification:** Final integration `python -B -m pytest -p no:cacheprovider`: 101 passed, one existing event-loop warning, 92.77 s. The later artifact-view narrowing was checked with the actual persistence/Code Mode bridge regression (1 passed, 40 deselected). Retention regression proves reopen, active/unresolved exclusions, failed export/byte-bound refusal and an actual Windows junction to a sibling; archive survives deletion. Snapshot regression failed on detached `7f6c744` because synthetic rows produced one admitted evidence item (1 failed, 3 deselected). Four frontend tests passed, including actual async React page rendering against controlled live/failing API transport. `npm run typecheck` and `npm run build` passed using installed web dependencies. Chrome checked built overview/block pages: offline/synthetic labels, zero evidence, synthetic measurement origins, unknown objective attainment and limits visible. Architecture checker and final diff checks passed. Temporary baseline worktrees and the verification server were removed/stopped; no historical database writes, dependency installs or push.

**Limits:** Retention preserves data by archival, not ledger deletion or backup rotation; oversized/unsafe/unresolved workspaces require operational review. Byte retention uses current typed SQLite records; no storage migration was justified. New local method/semantic contracts are not promoted. Expanded semantic/scientific utility, domain-specific representation generation, additional curated methods/static GDC joins and locked dependency environments remain D1–D8 below. Fixture execution, anonymous file access and mount isolation do not establish an end-to-end oncology capability family.

### 10.4 Deferred work and earned triggers

| ID | Primary deferred commitment | Trigger |
| --- | --- | --- |
| D1 | Automatic scientific/Jev promotion, full reusable JevCapability workflow | Repeated scoped use plus declared validation/generalization/measured utility and deterministic governance. Receipts alone insufficient. |
| D2 | Full representation ladder, deeper schema-semantic search | F4c evaluation shows missed useful representations despite available inputs; add executable/retrievable rungs only. |
| D3 | Universal candidate generator | Repeated domain generators demonstrate shared contract/recall benefit; no generic strategy now. |
| D4 | Full hypothesis-frontier refinement | F4d labels show duplication/alignment failures beyond initial mechanism. |
| D5 | Semantic self-consistency/calibration research/Autoresearch features | F4 evaluation shows instability worth additional measured budget; no automatic promotion. |
| D6 | Bulk harvesting, registry storage migration/SQLite-FTS, embeddings, broad ontology/EDAM/bio.tools | Measured recall/latency/coverage failure on growing curated snapshots. Preserve data-driven catalogues, progressive disclosure, reproducible snapshots and algorithm/snapshot receipt identity now; no tens-of-thousands prerequisite. |
| D7 | Additional survival/mutation/exposure/TMB/other source/method families | Need, approved available inputs, denominator/design/diagnostic contracts and scoped execution proof. F5e owns first selected operation, not every family. Science beyond GDC preserved; no cBioPortal/Hugging Face additions here. |
| D8 | Stronger dependency locking/reproducible external packaging | Selected method needs repeatable reinstall or drift prevents replay. F2 discloses unlocked dependencies/rejects changed output; necessary per-method locking cannot be waived by image hash. |

F2 missing historical bytes remain missing unless recovered from a verifiable source. F3 continuity proves context availability, not semantic usefulness or scientific negatives. Unavailable target Linux verification blocks that deployment path only. SDK smoke/reference/fixture inspection never establishes scientific utility.

**Report decisions:** Accept semantic-first retrieval, retained alternatives, static contracts, curated GDC candidates, artifact bridge and truthful operations. Modify F4a to exclude dossier work (F4b), separate actual availability from semantic fit and allow independent correctness/cleanup branches. Reject Director-owned OncoLab/global Science/Jev, speculative hierarchy mandates, installed veto, arbitrary URL execution, swarms/new framework, fixed GDC milestones, forced Score coverage, automatic promotion and unsupported legal assertions. Stale acquisition/request/memory/receipt gaps are completed F2/F3. Counts such as “57 descriptors” and “358 modules”, family-wide executability, exact filter/merge/normalization behavior, licences and selected anonymous artifacts remain unverified pending operation checks.

**Narrow upstream verification:** INDEX/manifest read first. `maf-lib` HEAD `a4e1f9d23a4e68dca4fc7a8b1c1eabd89248fea7` is absent from manifest; do not assume coverage. `gdc-1.0.0-public.json` extends protected, requires six normal fields null and filters seven annotations; protected extends base. Base Mutation_Status description includes more than Somatic/Germline/LOH shorthand; column_types.py defines YesNoOrUnknown separately and preserves Unknown. No reader/filter execution/schema-count claim verified. `gdcdatamodel2` HEAD matches manifest `9c6a046b96c130ea131d2ce2c9160381edd2fcc1`; `case.py` declares required submitter_id/disease_type/primary_site and secondary key (project_id, submitter_id). `samplederivedfromcase.py` declares source Sample/destination Case and associations; multiplicity requires governing declarations, not filename/edge names alone. ORM imports support static inspection. Broader diagnosis/multiplicity/exclusive-rule counts unverified; no upstream execution/import/install.

Official [GDC download documentation](https://docs.gdc.cancer.gov/API/Users_Guide/Downloading_Files/) describes `/data/{file_id}` and controlled-access tokens. This is a documented route, not anonymous availability/licence/release proof for every mutation/expression/CNV/clinical artifact. F5 still requires selected current metadata/access and bounded byte-acquisition verification.

### 10.5 Historical verification of the original audit plan (unchanged evidence)

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


### 10.6 Historical verification of the rewrite — 2026-10-01

| Check | Current result |
| --- | --- |
| `git rev-parse HEAD`; initial `git status --short` | `c15164a65a272715fe158a2521a53f9a59023fc7`; clean working tree. |
| `$env:PYTHONDONTWRITEBYTECODE='1'; .\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/invariants/test_persistence.py tests/invariants/test_live_mode.py tests/invariants/test_boundaries.py tests/invariants/test_evaluation.py` | **83 passed, 1 warning in 78.72s**. Existing pydantic_graph event-loop deprecation. Deterministic/controlled transports, not new live utility evidence. |
| `.\.venv\Scripts\python.exe -B scripts/check_architecture.py` | **architecture checks passed**. |
| `git diff --check` | **passed**, Windows line-ending notice only. |
| Read-only, in-memory Science/admission probes | One valid numeric row plus null/invalid rows produces n=1, SD=0.0 with no missing counts; two admissions of same measurement yield distinct UUIDs. An initial nonfinite probe failed canonical JSON hashing before result construction; this qualifies the older silent-drop claim. No persisted artifacts. |
| Comparison with `git show HEAD:docs/IMPLEMENTATION_PLAN.md` | F0–F3 historical blocks and original verification table/closing instructions preserved verbatim after newline normalization. |
| Final changed-path check | Only `docs/IMPLEMENTATION_PLAN.md`; no pre-existing edits to preserve. |

No F4a blocker was verified. Semantic utility/provider behavior, selected current GDC file access/licences/releases and per-operation upstream feasibility remain future verification, not passing claims. Local historical SQLite, target Linux kernel/isolation and new provider/scientific executions were not rerun. No dependencies installed; no source/tests/config/other docs/upstream/database/snapshot/runtime artifacts edited; no implementation, commit or push. Stop here: next implementation is F4a.


### 10.7 Current implementation completion

The user subsequently authorized implementation of F4–F6 and phase commits; this supersedes the historical rewrite-only stopping instruction in 10.6. Implementation began at `c15164a65a272715fe158a2521a53f9a59023fc7` with only the rewritten plan modified. F4 committed as `0b8d4fa0b4338dc29953d5f16a19826e1bfc674b`; F5 as `7f6c744` (full identity in Git); F6 as `c6b8dbe8fbc331aeb79fea8976fe5fee129e4944`. On the user's subsequent request, all three phase commits were pushed to GitHub `origin/main`; remote HEAD was verified at the F6 commit. The delivery paragraphs preserve their verification-time scope, including that no push occurred during those checks.

All active bounded batches F4a-e, F5a-e and F6a-b are delivered. The baseline finding table retains its verified-at-rewrite facts and primary phase ownership; delivery paragraphs above supersede “absent/remaining” observations. Optional static extraction and unselected MAF/VCF/count/expression/TMB/survival branches remain D7, with F5b/e dependencies. No unfinished commitment was silently removed. The earned triggers in 10.4 remain unmet for bulk harvesting, embeddings/storage migration, general ontology prerequisites and automatic promotion. No blocker remains for the delivered scope; broader empirical utility and dependency locking remain explicit verification limits.
