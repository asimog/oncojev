# Next-stage autonomous laboratory implementation plan

**Stage status: PLANNED.** Planning and documentation reconciliation performed on 2026-10-01; no next-stage runtime implementation, deployment, promotion or publication is claimed by this document. This is OncoJev's sole active implementation-phase/status tracker.

The completed plan is archived as [IMPLEMENTATION_PLAN_COMPLETED_F0_F6.md](IMPLEMENTATION_PLAN_COMPLETED_F0_F6.md), marked **DONE for its bounded F0–F6 scope**. Its original text, delivery evidence, limitations and deferred history are preserved unchanged below an archival header. Historical instructions and statuses there are recording-time facts, not current work orders.

The complete supplied target is preserved byte-for-byte in [NEXT_STAGE_AUTONOMOUS_LAB_REQUIREMENTS.md](references/NEXT_STAGE_AUTONOMOUS_LAB_REQUIREMENTS.md). It remains the reference for every requirement, example, prohibition, acceptance criterion and final-report field; this plan expands and sequences it without replacing or deleting any point. Its SHA-256 is `101fb984c7d15d03d3220d9e8c43bcf241edb7d84c9934e708e3e455dcca2b65`. The G0–G73 coverage table below maps all 74 sections to implementation owners. [ARCHITECTURE.md](ARCHITECTURE.md) is the single canonical architecture document and distinguishes delivered behavior from the next-stage target.

D1–D8 are integrated implementation batches inside H4, H6, H7, H9, H10 and H14, with H13 supplying their comparative evaluations. Their original triggers are preserved as execution and acceptance gates within those phases. There is no separate deferred-work section or backlog: each owning phase implements its baseline, runs its gate, delivers the justified extension and records the actual outcome. A gate that is not met produces a reference-linked limitation or not-eligible decision in that phase; it cannot be silently postponed or reported as implemented.

## 1. Goal and authority

Build a continuously running computational oncology laboratory with **one Python/Railway service, one persistent Director, at most one active fresh Researcher per JevBlock, one authoritative durable database, one revisioned OncoLab, one scientific-execution abstraction and one separate generated `asimog/oncojevlab` repository**. Both agents retain their bounded Coder and CodeMode/Monty capabilities. Researcher strategy remains adaptive; no fixed source/modality pipeline is introduced.

The thesis remains: high-throughput semantic judgment can guide search and comparison without becoming scientific evidence or execution authority. Director decides global allocation, supervision and program pause; Researcher decides investigation inside one block; Jev measures bounded semantic properties; Reasoner proposes possibilities; deterministic Science alone validates and admits measurements. Python owns lifecycle, deadlines, budgets, provenance, frontier composition, registry governance and persistence. Persistence stores admitted records; it cannot admit evidence itself.

Global scope contains Director Control, Research Memory and OncoLab, including typed global portfolios and semantic analyses. Block-local scope contains Researcher, immutable ResearchState, source acquisition, Science, Jev use, Reasoner, workspace, measurements, evidence and dossier. A global Jev **operation** is a typed measurement facility, never a global Jev agent or autonomous authority. Director cannot mutate active ResearchState, extend its deadline, execute scientific acquisition/analysis/admission, or use scratch code to edit production source, policy, questions, prompts, registry state or deployment configuration.

No swarms, additional concurrent Researchers, Engineer agent, global Science agent, unnecessary microservices, Celery/Redis/Kafka/Temporal, generic workflow engine, extra database, speculative vector infrastructure, uncontrolled mass harvesting or unjustified broad ontology ingestion. H7's integrated D6 batch must measure need before any bounded catalogue/index/vocabulary expansion. No cBioPortal/Hugging Face expansion without later explicit approval. Public visibility, metadata listing, successful execution, suitability, validation and reusability remain separate facts. Unknown access/licence/price/coverage stays unknown. Operational failure, missing input and semantic rejection never become scientific negatives.

## 2. Verified starting point and reusable foundations

Planning started on clean `main` at **`c9712e67050548354d32fcd6bb5b910569449431`**, matching the supplied baseline. Recheck HEAD and status at H0 and before each implementation batch; do not overwrite unrelated changes or assume this stays current. This planning pass inspected the supplied target, current documents, configuration and the relevant runtime/source paths; it did not rerun historical live research, inspect/change the historical database, install dependencies or inspect `.upstream/`.

| Area | Delivered baseline to retain | Next-stage difference |
| --- | --- | --- |
| Service/Director | `src/autonomous.py:AutonomousService.run_once` retains one Director Agent; `build_system` rebinds it to each new runtime. Prior transcripts are not retained. | Keep service-lifetime Agent and durable structured continuity; add service-owned asynchronous run/event context, not an ever-growing transcript. |
| Launch/cycle | `register_director_tools.launch_researcher` awaits `researcher.run`; `src/runtime/cycle.py:run_cycle` requires one new block and can launch fallback synchronously. | Start returns run identity immediately; Python owns task/terminal handling. Explicit pause permits zero allocations while allocating turns still allow only one. |
| Harness | Linux Director Coder already uses `/work/director`; fresh block Coder and Monty CodeMode exist; `workspace.py`/`landlock_exec.py` fail closed. | Preserve these capabilities; prove actual deployed confinement and prevent new DB/registry/export credentials from entering scratch authority. |
| Memory/semantics | F3 typed digests/start packets and F4 bounded memory, suitability, representations, hypotheses and dossier support already work. | Extend global portfolios, contradiction/relation context and program reviews; preserve deterministic retrieval and separate policies. |
| OncoLab | `initial_oncolab_index`, `OncoLabIndex`, cards, snapshot-bound `search_page`, routes and durable verification loading. | Add durable immutable institutional revisions, history/proposals/gaps and block pins; snapshots alone are not that revision model. |
| GDC/artifacts | `GdcPublicSource.search` already supports `/files`, offset/size/sort and coverage, currently adds open-access filtering; `acquire_file`/ScientificArtifact retain exact bytes and hashes. | Expand metadata/data-asset discovery and truthful access visibility; reuse acquisition/coverage/ownership bridge, keep anonymous acquisition open-only. |
| External execution | `DockerScientificSandbox`, independent replay, retained inputs/outputs and Science admission exist; dependencies are disclosed as unlocked. `sandbox.provider` is Docker; Dockerfile supplies no daemon. | Backend-neutral contract and confined per-experiment local Python venv backend; pinned dependency/environment identity for reusable methods. |
| Operations | Append-only SQLite recovery/atomic terminal dossiers; F6 archive-before-cleanup; read-only API/UI with truthful failure/synthetic provenance. | Durable Railway path/status, sequential runs without restart, event/program/revision/export views and generated downstream lab history. |
| Policy | `FrontierPolicy.interpret` serves multidimensional semantics; `decide` remains a production caller in `evaluate_candidate`. | Audit and migrate or separately version/evaluate that real caller; do not assume `decide` is dead. |

Preserve the completed contracts: F0 truthful lifecycle/recovery; F1 allocation, budgets and authority; F2 replayable provenance, receipts and telemetry; F3 typed memory and validated start packets; F4 semantic search/Jev slices; F5 undefined statistics, missing/invalid denominators, coverage, source-resolved pairing, stable admission identity and exact artifacts; F6 retention and truthful live/synthetic/offline and failed/incomplete presentation. Historical missing bytes remain missing unless verifiably recovered. New features do not retroactively validate old records.

## 3. Delivery rules and shared contracts

Each phase is split into small coherent batches below. Extend the existing owner rather than creating a parallel canonical implementation. Names of proposed models/tools are conceptual until H0 reconciles existing equivalents; Pydantic AI construction/dependencies/tool registration remain exclusively under `src/runtime/pydantic_ai/`, with `factory.py` the deterministic/live composition point. Domain contracts and policies belong in their owning `src/` packages. No code, config, tests or UI are being changed as part of this planning delivery.

Before a new regression, state its observable contract, credible failure, why existing coverage misses it and its primary owner. Prefer real service/tool/persistence boundaries and shared/table-driven fixtures. Do not add source-string, copied-fixture, descriptor-existence or mock-ordering tests as proof of capability. A bug regression must fail before the fix for its intended reason. Fixtures establish correctness; bounded live smokes establish connectivity/execution; labelled evaluations address utility; actual target verification establishes deployment confinement. None substitutes for the others.

After every implementation batch run its focused tests, `uv run python scripts/check_architecture.py` and `git diff --check`; inspect the diff and update this tracker with exact results, versions, limitations and actual completion evidence. Commit coherent implementation batches as specified by G71. At final integration run the full suite. A phase is DONE only when its delivered path, failure semantics and required proof pass; a type, descriptor, fixture or document is insufficient. Record external setup/deployment blockers without blocking independent local work.

For each integrated D batch, retain the trigger inputs, benchmark/labelled cases, decision basis, resource allowance, delivered path or unmet prerequisite, and acceptance result in its owning H phase. H13 results return to H4/H6/H7/H9/H10/H14 before final acceptance; evaluation is part of delivery, not a reason to move these commitments into a later plan. A completed qualification/no-change decision does not close an unmet scientific or capability gap. Unsupported automatic self-promotion, production self-modification and uncontrolled ingestion remain authority prohibitions, not scheduled features.

Target contract additions or smallest equivalent extensions:

| Contract | Owner and authority | Required identity/limits |
| --- | --- | --- |
| `ActiveResearchContext` / run handle | Service lifecycle in `src/autonomous.py`/`src/runtime/cycle.py`; adapters in runtime integration | Mission/cycle/block/run IDs; application version; registry pin; start sequence; independent budgets/usage; task state. Never share mutable ResearchState with Director. |
| Program outcome / event | `src/director/models.py`, block/cycle models and persistence | ALLOCATE or truthful PAUSE with reason such as NO_MATERIAL_NEXT_BLOCK/NEEDS_HUMAN_DIRECTION; event identity/deduplication; distinct run, program and objective-attainment status. |
| `BlockDelta` | Deterministic dossier/memory derivation from stored references | Start/end sequence and origin; new evidence/measurement/hypothesis/negative/uncertainty/continuation/blocker/demand/gap/relation references, explicit resolutions and resource delta; omission limits. No inferred negatives/resolutions. |
| Global frontier / relations / review | Director domain with deterministic policy and memory references | Candidate identity; basis digest IDs/high-water sequence/active block+revision/OncoLab revision/app version; projection/question/policy versions; Jev receipts/distributions; statuses/limitations. |
| OncoLab revision/history/proposal | `src/oncolab/` plus append-only persistence | Parent revision, content hash, accepted transition and governance version, descriptor/route/verification histories. Blocks pin immutable revision; no agent CRUD. |
| External capability / data asset | `src/oncolab/` discovery vs `src/sources/` asset contracts | Source/query/filter/cursor/retrieval time/candidate IDs/hash/omissions/failure. Preserve mutable-source truth; GDC files never become capabilities. |
| Scientific execution/environment | `src/science/` | Backend-specific runtime identity, repo/commit/package, dependencies/install/test/execute commands, exact inputs/parameters/outputs, first/replay identity, validator and limitations. Local identity never fabricates Docker digest. |
| Export/publication receipt | Deterministic downstream application/exporter | DB high-water/revision, renderer version, generated paths/content hashes, event boundary, commit/publication outcome. No input route from notebook Markdown to scientific state. |

## 4. Phase tracker and dependency order

The supplied H0–H15 sequence is retained. A later number is not a reason to bypass a prerequisite: **H9 accepted executable promotion requires H10's environment/replay proof and H11's deployment verification**. H9 proposal/governance scaffolding can precede H10; acceptance is gated until those dependencies are satisfied. H13 evaluation cases/receipts start alongside each semantic/discovery phase rather than being postponed to the end. H14 audits callers at H0 and performs final cleanup/calibration after evaluation. H11 persistence prerequisites must be prepared before any production cutover.

Integrated batches use two passes where necessary: build the concrete mechanism and evaluation cases in the owning phase, then return with H13 evidence to complete its qualified extension. D1 belongs to H9; D2 to H6; D3 and D4 to H4, with D3's shared-contract decision completed in H14; D5 to H14; D6 to H7; D7 and D8 to H10, using H6's source/input gates. H15 checks these phase results directly rather than reconciling a separate deferred list.

| Phase | Priority/class | Build prerequisites / completion evidence | Status |
| --- | --- | --- | --- |
| H0 — baseline audit/reconciliation | P0, audit | Current checkout | PARTIAL: planning baseline recorded; full G0 implementation audit and executable baseline pending |
| H1 — Director harness/role/tools | P0, authority preservation | H0 | PLANNED |
| H2 — non-blocking single-Researcher lifecycle | P0, lifecycle correctness | H1 | PLANNED |
| H3 — events, delta, pause and stale basis | P0, lifecycle/provenance | H2, existing F3/F6 | PLANNED |
| H4 — global semantics, generators and hypothesis refinement (D3/D4) | P1, semantic method | Build: H3. Return-pass proof: H6/H7 generators and H13/H14 contract comparison. | PLANNED |
| H5 — revisioned institutional OncoLab | P1, durable contracts | H3, existing catalogue/F2 | PLANNED |
| H6 — GDC files/assets, deeper representation/schema search (D2) | P1, source correctness + scoped method | Build: H5, existing F4c/F5. Return-pass proof: incremental H13 misses. Supplies D7 input gates. | PLANNED |
| H7 — bio.tools, EDAM and measured search expansion (D6) | P1, capability retrieval | Build: H5 and H4 baseline policy primitives. Return-pass proof: H13 scale/coverage evidence. | PLANNED |
| H8 — ecosystem enrichment | P2, scoped adapters | H7 | PLANNED |
| H9 — governed capability promotion/review (D1) | P1, governance | Build: H5/H7/H8 as applicable. Acceptance: measured H13 utility and H10/H11 execution/deployment proof. | PLANNED |
| H10 — execution backend, scientific operations and dependency locking (D7/D8) | P0 for Railway execution, scientific correctness | Build: H2 and existing F5 admission; H6 inputs for selected science. Return-pass proof: scoped H13 evaluation; deployment in H11. | PLANNED |
| H11 — durable Railway deployment/confinement | P0 for deployment, operations | H2/H3/H5/H10 | PLANNED |
| H12 — oncojevlab export/publication | P2, observability | H3/H4/H5/H9/H11 records | PLANNED |
| H13 — semantic/scientific evaluation corpus | P1, evaluation | Build alongside H4/H6–H10 baselines; return scoped proof to owners. Full-system conditions after H11/H12. | PLANNED |
| H14 — frontier audit, generator contract and bounded calibration/Autoresearch (D3/D5) | P1, policy correctness and measured semantic research | Build: H0 caller inventory and H4/H6/H7 baselines. Acceptance: H13 comparisons/instability evidence. | PLANNED |
| H15 — final documentation/full verification | Integration | H1–H14 acceptance or explicitly recorded external blockers | PARTIAL: target documentation aligned; final implemented-state reconciliation pending |

### H0 — Audit actual HEAD and reconcile the target

**Owner:** README/AGENTS/canonical docs, `config/runtime.yaml`, `config/models.yaml`, `src/autonomous.py`, `src/runtime/`, domain packages, Dockerfile/railway.toml, owning invariants and scripts. **Requirement:** G0, G54, G57, G71.

1. Record HEAD/branch/status, compare current `main` with supplied `c9712e6` and archived F0–F6 delivery; preserve unrelated work. Read AGENTS/README, architecture/constitution/plan/Jev/capabilities/frontend, then configuration and smallest relevant packages in the required order. Do not recursively inspect `.upstream/`; a concrete upstream question uses INDEX then manifest then one minimal path.
2. Trace Director/Researcher construction, Coder/CodeMode/Monty, both workspace backends, both Researcher launches/fallback, cycle lifecycle/recovery, usage ownership and service shutdown. Inventory synchronous source/Jev/scientific/SQLite work that would stall an async event loop and determine thread/transaction ownership before scheduling.
3. Trace semantic memory, OncoLab `search_page`/snapshots/verifications/execution routes, delivered suitability/representation/alignment/memory semantics, both FrontierPolicy callers, Science admission/artifacts/replay, retention, eval harness and Railway storage/authentication separation.
4. Record a gap/equivalence matrix here: already delivered, extension required, superseded control invariant, verification unavailable. Capture baseline focused tests and architecture check without claiming semantic utility or target Linux proof. Leave historical unreplayable records explicitly limited.

**Exit proof:** every G0 path has a production caller and owner; no duplicate F4–F6 work is proposed; starting commands/results and actual deployment limitations are recorded. Baseline correctness: `uv run pytest tests/invariants/test_boundaries.py tests/invariants/test_persistence.py tests/invariants/test_live_mode.py tests/invariants/test_evaluation.py`; architecture/diff checks. This implementation baseline has not been run by this planning pass.

### H1 — Preserve Director Coder/CodeMode and establish its global role

**Owner:** `src/director/agent.py`, `src/director/models.py`, `src/runtime/pydantic_ai/{agents,contracts,controls,factory,workspace}.py`, `landlock_exec.py`, strict runtime configuration. **Requirements:** G1/G2/G46/G47/G61/G62/G63.

1. Preserve the existing persistent Director, POSIX Coder, Monty CodeMode and writable `/work/director`; preserve fresh Researcher Coder. Reuse existing typed memory/index/control tools. Expand instructions from allocate/wait/summarize to memory synthesis, hypotheses/uncertainties, duplication/contradictions, diversification/dependencies, capability demand/failure analysis, resources/failure triage, supervision/continuations, engineering proposals and legitimate program pause.
2. Add only usable typed Director tools as their owners ship: memory resolve/dossier/evidence/hypothesis/negative/uncertainty reads; semantic frontier/relations/contradiction/candidate comparison/program review; OncoLab suitability/history/gaps/external search/promotion/review/reverification proposals; allocate/start/inspect/read completed/pause. Preserve adapted names rather than duplicate APIs. No generic unrestricted Jev escape hatch or evidence-admission tool.
3. Keep scientific source/method/representation/analysis/strategy selection, candidate generation, local frontier, Jev/Reasoner use, acquisition/prototyping, scope escalation proposals and local completion with Researcher. Director allocates a question, never a prescribed pipeline.
4. Bound independent Director turns separately from Researcher elapsed time and aggregate service/cycle allowances. Retain separate model/provider-tool/CodeMode/tool, Jev call/question, Reasoner, source, scientific execution and byte counters. Expose configured monetary bound and known/unknown reported cost; do not invent pricing. Check newly introduced persistence/credential paths remain outside Coder access.

**Exit proof:** real harness can write its own scratch while denied application/config/policy/question/prompt/deployment writes, peer workspace and credential/process-environment reads; child commands remain scrubbed/confined. Scratch scripts/prototypes are non-evidence and cannot mutate authoritative OncoLab/lifecycle. Primary owners: `test_live_mode.py` and existing Linux `scripts/verify_coder_container.py`; budget ownership in `test_boundaries.py`. Run owning tests; Linux verifier here proves its tested environment only, actual Railway proof remains H11.

### H2 — Python-owned non-blocking execution with one active Researcher

**Owner:** `src/autonomous.py`, `src/__main__.py`, `src/runtime/cycle.py`, `src/runtime/pydantic_ai/{contracts,agents,factory,controls}.py`, `src/block/{models,manager}.py`, persistence terminal/cycle records. **Requirements:** G3/G5/G43/G47/G63/G69.

1. Introduce the smallest service-owned active context/run handle. Create fresh block state, skills, budgets, Researcher agent and workspace; pin mission/cycle/block/run and starting record sequence. Allocation/start guards atomically permit at most one active Researcher and one launch per block. Persistence records start before externally visible work begins.
2. Adapt the existing launch tool to schedule the Researcher and return its active-run identity promptly. Replace the synchronous fallback with the same owned start path; remove competing lifecycle implementations. Keep CLI one-cycle behavior as an awaitable compatibility boundary that waits in Python, not inside the Director model tool. Adapt `src/__main__.py` and other result consumers for H3 zero-block PAUSE: the current `result.block_ids[0]` printer must not crash or invent a block.
3. Use one service-lifetime event loop/task owner or an equally minimal owned design. Offload blocking Jev/source/subprocess work so a task wrapper actually permits independent Director work. Do not share SQLite connections/mutable budget/state objects across unsafe threads; persist/charge through one authoritative owner with explicit ordering and bounded operations. Keep Pydantic integration confined to its adapter package.
4. Persist completion/failure once; combine terminal dossier, outcome and run receipts atomically/idempotently. `complete_block` remains handoff, not successful return. Preserve failure precedence, failed partial results and recovery corrections. Director turn truncation must not silently cancel a healthy active Researcher; define service aggregate-stop and graceful shutdown explicitly. Respect reserve windows; do not discard in-flight work. On restart close interrupted work honestly, never silently resume/relaunch it.

**Exit proof:** through the real service/tool path, launch returns before a deliberately pending Researcher finishes, Director can do bounded independent work, second starts fail without effects, and completion/failure races/reopen/shutdown retain one honest outcome. Include a representative blocking operation to detect event-loop starvation; fixtures must not fabricate owner persistence. Primary owner `test_persistence.py`, distinct nested-tool failure/usage boundary `test_live_mode.py`/`test_boundaries.py`. Run those focused files and architecture/diff checks.

### H3 — Event-driven turns, BlockDelta, pause and stale-plan revalidation

**Owner:** service/cycle/block lifecycle, `src/director/models.py`, `src/dossier/{models,builder}.py`, `src/memory/`, persistence records/reconstruction, application/API read models. **Requirements:** G4/G6/G9/G14/G47/G53/G58/G63/G69.

1. Deliver bounded Director turns for Researcher started, explicitly useful material persisted events, completion/failure and configured scheduled program review. Use a bounded in-process event mechanism with durable identities/deduplication and reconstructable terminal events. Yield when useful work is exhausted; Python waits for events. Do not call a model merely to poll run state.
2. Derive reference-linked BlockDelta from start/end sequences and recorded changes: evidence/measurements/hypotheses/scientific negatives/uncertainties/resolutions/continuations/blockers/capability demand/gaps/contradiction and relation candidates/resource delta. Missing negatives or explicit resolutions remain absent. Feed delta and typed memory prominently into the post-block turn without duplicating full payloads.
3. Add explicit program ALLOCATE/PAUSE outcomes with NO_MATERIAL_NEXT_BLOCK/NEEDS_HUMAN_DIRECTION or typed equivalent reasons. Pause when meaningful uncertainty is exhausted, inputs/capabilities unavailable, candidates duplicate, outcomes add no material distinction or mission needs human choice. Permit a zero-block **explicit pause**, not accidental allocation failure. Persist decision/basis/limitations; do not imply scientific success or create a dummy block. Await changed direction/input/capability or scheduled review instead of immediate model retries.
4. Persist prepared-frontier basis: digest IDs, DB high-water sequence, active block/revision, OncoLab revision and application version. At completion/failure or material revision, revalidate before allocation, invalidate/recompute changed dependencies and preserve superseded plans. Active ResearchState and deadline remain inaccessible to global mutation. H5 adds exact registry pins to this basis once available.

**Exit proof:** terminal events drive one post-block turn, idle runs do not busy-poll, deltas resolve their actual source records, failures remain operational, explicit pause creates no block, and new evidence/revision invalidates stale planning. Primary owner `test_persistence.py`; truthful read-model outcomes in its existing coverage. Retention still excludes active/unresolved contexts. Run focused file plus existing boundary tests and architecture/diff checks.

### H4 — Global Director semantic frontier, candidate generation and hypothesis refinement

**Owner:** `src/director/`, `src/memory/{models,service}.py`, `src/jev/{models,questions,frontier}.py`, `src/runtime/pydantic_ai/{semantic,contracts,search_tools}.py`, dossier/persistence relations, incremental eval cases. **Requirements:** G7/G8/G10–G16/G34/G61/G64.

1. Extend F3/F4e retrieval first using entity/topic/capability/hypothesis identity/shared references/time/terms/block lineage. Normalize exact duplicates before bounded Jev comparison. Preserve relevance, duplication, contradiction, recurring/newly actionable uncertainty, repeated hypotheses/blockers/capability need and cross-block relation dimensions. Never perform whole-database all-pairs semantic search.
2. Create a bounded global hypothesis portfolio with stable identities and distinctions: duplicate, paraphrase, related-but-distinct, independent replication, contradicted, blocked, newly testable, deferred and resolved. Preserve local F4d alignment/duplicates; no hypothesis relation or rejection becomes evidence/negative result.
3. Persist cross-block relation candidates with source refs, relation type, call IDs/native distributions, basis sequence/memory revision, limitations and candidate-for-testing/possible-duplicate/contradiction/independent/uncertain status. Contradiction questions distinguish actual conflict from population/design/method/phrasing differences and whether a bounded block could resolve it. Preserve both original records; later scientific resolution requires admitted measurements, not Jev agreement.
4. Generate future investigations from continuations, hypotheses, uncertainties, contradictions, relation candidates, capability gaps, replication needs and underexplored mission areas. Measure atomic mission relevance, uncertainty linkage, duplication, contradiction resolution, continuation coherence, dependency readiness, block fit, capability availability, hypothesis distinction and material global-state change. Python composes a small beam; Director selects one. No single "best" or universal quality/reward score.
5. Separate global/local candidates, authority, scope, stop conditions, policy identity and threshold interpretation while reusing projections/receipts/distribution decoding. Preserve useful alternatives and deterministic fallback on Jev failure. Program review describes concentration/modality imbalance, rediscovered/rejected/deferred ideas, unresolved contradictions, recurring provider/capability failures and expensive blocks without actionable change.
6. Produce reference-linked EngineeringProposal records for retrieval misses, ambiguity, descriptor mismatch, deployment gaps or policy pathologies; scratch Coder may calculate/prototype. No Engineer agent, live source modification, auto-question rewrite or self-reward loop. Bind proposals to actual records and review state.

**Exit proof:** real bounded retrieval→projection→receipt→policy→Director path; independent replication retained, both sides of conflict intact, alternative recall/failure fallback and global/local separation protected. Primary owners `test_boundaries.py` for semantics and `test_persistence.py` for durable relations/reopen. Start H13 labelled cases in the same slices; connectivity smoke is separate from utility evidence. Run focused tests, selection eval commands appropriate to the delivered cases, architecture/diff checks.

#### H4a — Integrated D3: universal candidate generation through proven domain contracts

**Trigger:** Multiple domain generators demonstrate useful shared contracts and improved recall.

1. Implement and inventory concrete generators for global continuations/uncertainties/contradictions here, retrievable representations in H6, and method candidates in H7. Record each generator's real inputs, scope, identity, reference provenance, prerequisites, omissions, bounded output and existing policy consumer. Preserve distinct global/local types and decision authority.
2. Add H13 paired multi-domain cases comparing the current generators with proposed shared retrieval/composition mechanics. Measure useful-candidate recall, missed alternatives, deterministic duplicates, context size, latency and resource use. A shared interface must handle multiple real domains and improve recall; a common-looking model alone does not meet the trigger.
3. On a passing comparison, complete H14's extraction of the smallest production-used generator contract/dispatcher. Keep domain-specific scientific meaning, eligibility and stop policies in the existing owners; avoid a generic strategy/workflow engine or a single candidate type that erases scope. If comparison fails, retain the working domain generators and record the failed abstraction/recall evidence here and in H14.

**Acceptance:** actual domain consumers execute through the demonstrated contract where adopted; deterministic recall/identity/provenance and scope guards survive abstraction. `test_boundaries.py` owns the consumer-visible behavior, H13 owns the multi-domain recall comparison. Both passing and rejected extraction decisions require recorded evidence; D3 is no longer an unassigned deferred item.

#### H4b — Integrated D4: deeper hypothesis-frontier refinement

**Trigger:** Labelled cases expose duplication or alignment failures beyond the delivered mechanism.

1. Deliver the global hypothesis/cross-block/contradiction portfolio above on top of F4d. Extend H13 labels with paraphrases, genuinely distinct hypotheses, alternative tests, population/design differences, independent replication and blocked/newly testable hypotheses.
2. Replay labelled duplication/alignment failures through the actual proposal→identity→retrieval→Jev→frontier path. Repair the smallest responsible normalization, candidate-generation, test-alignment or retention contract and version the changed projection/question/policy. Do not treat related claims as duplicates merely to reduce the frontier.
3. Demonstrate before/after retention and alignment on held-out cases with explicit unknowns/resource use. If initial mechanisms already pass the cases, record that result and the covered limits inside H4 rather than retaining a separate refinement backlog.

**Acceptance:** useful alternative tests and independent replication remain retained; exact/semantic duplicates are distinguished; hypotheses, semantic rejection and relation candidates never become evidence or scientific negatives. Behavioral regressions belong to `test_boundaries.py`; durable portfolio identity/reopen belongs to `test_persistence.py`; utility/alignment labels belong to H13.

### H5 — Dynamic, immutable OncoLab institutional knowledge

**Owner:** `src/oncolab/{models,registry,catalogue,execution}.py`, `src/persistence/{records,repository,reconstruct,store}.py`, allocation/start models, factory/search tools. **Requirements:** G17/G18/G19/G34/G37/G43/G55/G65.

1. Retain the curated catalogue/routes/schema/governance as seed knowledge with existing hashes/cards/continuations/verifications. Add typed durable usage/successful scope/failure/limitation/demand/suitability/gap/promotion/review/reverification histories. Descriptor presence never implies installed, executable, appropriate, validated or reusable.
2. Append immutable revisions with parent/hash/governance/application identity and enough content/reference closure to reconstruct any historical registry. Make initial seed identity explicit. Migrate/backfill conservatively without inventing historical pins; label legacy registry context unknown where not provable.
3. Pin exact OncoLab revision and application/runtime version at block allocation/start. Resolve that snapshot throughout local execution; invalidate search continuations crossing revisions. Refresh accepted state between blocks without worker restart; active blocks retain their pinned contracts/routes. Couple append/acceptance/visibility atomically.
4. Keep three layers: curated reusable capability state; on-demand external capability candidates; data-asset discovery. Persist actual-record-linked capability gaps and minimal proposal/review/update/reverification/retirement transitions, using H4 semantic grouping where useful. No unrestricted add/edit/delete agent tools. Python governance owns state transitions.

**Exit proof:** static catalogue still works, reopen reconstructs immutable past/current revisions, block pins survive updates, histories resolve, stale continuations fail honestly and the next sequential block observes an accepted revision without restart. Primary owner `test_persistence.py`; search transport/continuation contracts in `test_boundaries.py`. Promotion proof remains H9/H10/H11. Run focused files and architecture/diff checks.

### H6 — Truthful GDC files and deeper representation/schema search

**Owner:** `src/sources/{models,public,coverage}.py`, existing scientific artifact models/execution, OncoLab source descriptors, `scientific_tools.py`/`search_tools.py`, F4c semantic integration. **Requirements:** G20–G23/G56/G57/G58/G66.

1. Reuse existing `/files` pagination and acquisition. Verify current field/mapping contracts for selected needs at implementation time. Extend bounded asset cards with file ID/name/access/state/category/type/format/strategy/platform/workflow, size/MD5, case/project refs, release/version when available, filters/requested fields/sort/offset/page/total/query identity/retrieval time and omissions. Preserve coverage/overlap/endpoint-unit contracts. Missing metadata stays unknown.
2. Separate discovery's truthful open/controlled/unknown visibility from anonymous open-only acquisition. Enforce scientific-data authentication domain independently from model-provider credentials; unsupported controlled access is explicit, never attempted silently. No individual UUID enters the capability catalogue; only search/describe/acquire/manifest methods can be capability entries.
3. For selected open files use existing exact-byte `/data`→ScientificArtifact path; validate supplied MD5/size, internal SHA-256, request/source UUID/access and block ownership before inputs are exposed. Bound downloads/time/resources; manifest acquisition is optional for a concrete bounded need, never a bulk default. Extend no new analysis family just because bytes are available.
4. Group available assets by data type/format/entity unit/strategy/coverage/transformation. Deterministically establish retrievability/input/design requirements before Jev measures sufficiency/assumption fit. Feed retained actual representations into existing F4c frontier and execute the D2 expansion batch below; do not invent an unavailable universal representation ladder.

**Exit proof:** deterministic transport fixtures protect query/pagination/order/total/metadata/access, exact byte/hash/size/owner rejection and representation grouping; preserve existing F5 regressions. Primary owner `test_boundaries.py`; artifact reopen/mount ownership in `test_persistence.py`. Bounded selected-file live smoke verifies current route/access only, with exact queries/results/limits recorded; no family-wide science/licence claim. Run focused files, artifact verification script where relevant and architecture/diff checks.

#### H6a — Integrated D2: deeper representation and schema search

**Trigger:** Evaluations show useful representations being missed despite available inputs.

1. Build H13 cases where the same scientific need has multiple actually available formats, entity units, schema mappings, coverage levels or transformations, including useful low-lexical-overlap alternatives. Retain access/input identity and a labelled useful-representation set before semantic filtering.
2. Diagnose misses as retrieval, schema-field/entity mapping, representation grouping or semantic sufficiency failures. Add only the executable/retrievable rungs and bounded schema mappings needed to recover those cases. Use the current source field/mapping contract, retained artifacts and deterministic availability checks; do not invent data or treat metadata as usable inputs.
3. Re-evaluate retained useful-representation recall and assumption fit, with versions, omitted candidates and resource changes. The phase records either the implemented recovery plus proof or an explicit no-miss/unavailable-input result, instead of sending D2 to another plan.

**Acceptance:** demonstrated available useful representations survive retrieval and frontier policy; wrong entity unit/access/schema/prerequisite remains rejected deterministically. `test_boundaries.py` protects those source-to-frontier behaviors; H13 measures missed/recovered alternatives. This batch supplies available-schema/input contracts to H10's D7 scientific operation batches without declaring those operations delivered.

### H7 — bio.tools, EDAM and measured catalogue/search expansion

**Owner:** one external discovery contract/adapter family in `src/oncolab/`, typed persistence/search receipts, `src/runtime/pydantic_ai/search_tools.py` and semantic adapter. **Requirements:** G24–G26/G31/G32/G33/G56/G67.

1. Define one bounded `search(source, need, filters, continuation)`/`describe(source, external_id)` interface or smallest existing equivalent; GDC assets remain separate. Verify current bio.tools API/filter/pagination semantics before implementing. Support applicable free text/tool ID/name/domain/topic/operation/input-output data type/format filters without asserting unsupported filters work.
2. Retain ExternalCapabilityCandidate cards: source/ID/name/description/homepage/tool types/EDAM inputs-outputs-topics-operations-formats/publication and download/package/repo links/licence/version where returned. Keep IDs/terms as controlled normalization; do not ingest the ontology. Store query/filter/page/cursor/IDs/time/response-content hash or retained payload identity/omissions/failure. Mutable lookup is not an immutable snapshot unless retained.
3. Search current OncoLab→cards→contract expansion→deterministic route/input/access/runtime checks→Jev suitability→retained frontier first. When still inadequate, use external discovery/enrichment and the same staged bounded checks; Jev assesses estimand/operation/input/output/limitation fit, never grants missing execution authority. Director uses metadata for planning; Researcher chooses acquisition/prototype. Do not prefer external software automatically or restore an installed lexical veto.
4. Benchmark catalogue size/recall/latency/continuations/context before changing search infrastructure. Keep scan retrieval where adequate; earned expansion order is FTS5/equivalent, controlled vocabulary, then embeddings only if measured added recall. No vector DB or uncontrolled bulk import.

**Exit proof:** fixtures protect filters/query/cursors/cards, mutable-source receipts, metadata-only execution denial, missing-route denial despite favorable Jev, validation requirement and outage as operational failure. Primary owner `test_boundaries.py`; persistence receipt/reopen owner `test_persistence.py`. Bounded live smoke independent of permanent unit availability; H13 recall cases compare retained useful candidates. Run focused tests and architecture/diff checks.

#### H7a — Integrated D6: harvesting, SQLite/FTS, vocabulary/ontology and embeddings

**Trigger:** Growing curated catalogues demonstrate recall, latency or coverage problems.

1. Establish a versioned scan-retrieval benchmark with growing curated snapshots and H7/H8 on-demand external candidates. Measure useful recall, coverage gaps, latency, candidate/context size and continuation correctness under identical query/input limits. H5 durable registry revisions alone do not meet a search-index migration requirement.
2. When measured scale exceeds the baseline contract, add the smallest deterministic SQLite FTS5/equivalent index over the existing authoritative revisioned records. Keep it rebuildable and non-authoritative, bind query/algorithm/snapshot identities in receipts, preserve stable ties and continuation scope, and compare recall/latency against scanning before adoption.
3. Diagnose residual vocabulary/coverage misses. Add bounded EDAM term expansion, a versioned approved vocabulary snapshot or a bounded ontology resolver only for those misses. Returned IDs/terms remain the default. Any larger curated import must have selected sources, query/family purpose, retained licence/access/retrieval/hash identity, explicit record/byte/time limits and deduplication; do not mass-import a registry or ontology without demonstrated need.
4. Compare embedding-assisted retrieval only when FTS/vocabulary still misses labelled useful candidates. Retain deterministic high-recall candidate retrieval and versioned embedding/index identity; adopt only a measured recall improvement within resource limits. No vector database or uncontrolled bulk harvesting is a prerequisite. Reject or retain a measured no-change decision when the stage adds no useful value.

**Acceptance:** H13 records the staged scan→FTS→vocabulary/ontology→embedding decisions and gains/limits; only justified stages are implemented. Continuation/query/revision determinism and rebuild/reopen belong to existing boundary/persistence test owners. Bounded curated ingestion yields candidates, not installation, validation or automatic promotion. Every D6 component has a phase-owned decision and execution/proof path; no separate deferred scale/ontology backlog remains.

### H8 — GitHub, Bioconda and Bioconductor enrichment

**Owner:** H7 external-discovery adapters/models and current public GitHub method request validation in `src/science/sandbox.py`; typed role tools. **Requirements:** G27–G31/G56/G67.

1. GitHub: preserve public compatible repository acquisition and pin resolved commit. Bounded metadata may include repo/default branch/release-tag/language/declared licence/README-docs/requirements-lockfiles/tests/package identity. Director reads metadata; scientific execution/admission stays Researcher/Science. Public does not establish permitted use.
2. Bioconda: add optional targeted metadata enrichment for discovered/gap candidates with package/version/source/checksum/dependencies/build-runtime constraints/tests/licence/platforms. No automatic Conda install; a concrete method requiring Conda needs a later separately evaluated backend decision.
3. Bioconductor: bounded need-driven package/purpose/BiocViews/version-release/dependencies/docs-vignettes/source/licence/build-status candidates remain metadata-only until a supported verified R environment exists. Do not advertise R execution from a listing.
4. Keep extension seams for PyPI/BioContainers/other approved curated registries/data resources, without implementing them all. Add only a minimal measured-value source. Record partial/missing metadata and transport limits. No cBioPortal/Hugging Face addition under this stage.

**Exit proof:** distinct source fixtures prove candidate identity/filter/pagination/enrichment and truthful unsupported-runtime/access/licence status; source-specific failures do not create negatives or promote records. Reuse H7 test owner rather than duplicating interface assertions for every provider. Run owning `test_boundaries.py` cases and architecture/diff checks; bounded smokes only for adapters actually delivered.

### H9 — Governed promotion, review and engineering proposals

**Owner:** `src/oncolab/` governance/execution/registry models, persistence transitions, Director proposal tools, H10 execution identities. **Requirements:** G16/G34–G37/G41/G55/G56/G65.

1. Persist proposals from repeated concrete needs and controlled validated use, with actual reference links. Include source/repo-commit/package-version/purpose/typed inputs-outputs/execution/dependency identity/replay/scopes/failures/limits/access/licence knowledge/measured utility/overlap. No execution count alone certifies validity or generalization; one successful run does not promote.
2. Implement explicit versioned deterministic ACCEPT/REJECT governance with scope/generalization/contract/replay/utility checks. Failed/rejected proposals leave registry unchanged and retain reasons. Unknown reproducibility or licence/access information must remain explicit and cannot justify unsupported REUSABLE claims.
3. Declarative methods usable through the already supported generic executor may create a new immutable revision without source changes. Code requiring a parser/wrapper/algorithm/route/source adapter/admission change produces EngineeringProposal and awaits ordinary reviewed development; Director Coder never patches live code. Minimal review/update/reverification/retirement proposals use governed append-only transitions, not unrestricted CRUD.
4. Stage proposals/policy in supplied order; do not accept new executable reusable capabilities until H10's exact environment/dependency/replay proof and H11's applicable actual deployment confinement pass. On acceptance refresh between blocks without restart; preserve old pins and receipts. Unsupported automatic Jev/local-question/self-promotion cannot pass this governance path.

**Exit proof:** one external execution does not promote; rejected/incomplete proposal causes no revision; accepted supported declarative method creates reconstructable revision and is actually usable in the next block without restart; code-requiring method yields proposal only; Jev cannot override governance. Primary owner `test_persistence.py` exercising proposal→policy→registry→factory→execution; independent admission guard in `test_boundaries.py`. Run those focused files and architecture/diff checks.

#### H9a — Integrated D1: automatic capability promotion under explicit governance

**Trigger:** Repeated validated use, measured utility and explicit governance. Execution receipts alone are insufficient.

1. Connect H5 demand/usage/failure history and H13 measured utility to repeatable promotion proposals. Resolve exact scientific contracts, validated/generalized scopes, failures/limitations, access/licence knowledge, software/dependency identity and existing-capability overlap; reject missing, unsupported or stale prerequisites explicitly.
2. Implement the deterministic versioned acceptance/rejection pipeline so a supported declarative reusable method can transition automatically only after all declared governance checks pass. H10 fresh reinstall/replay and H11 applicable deployment proof are required before executable acceptance. Neither a successful receipt nor an arbitrary minimum execution count proves scientific validity.
3. Verify an accepted revision is actually discoverable and usable by a subsequent fresh Researcher without process restart, while active/historical blocks retain their pins. Retain reject/reverification/update/retirement history and prevent registry changes from rejected proposals. Code-requiring reuse becomes an EngineeringProposal; unsupported automatic Jev/local-question/self-promotion cannot grant reusable status or alter live questions/policy.

**Acceptance:** evidence-linked repeated use/utility and governed accept/reject behavior are exercised end-to-end, including missing reproducibility, changed scope, failure history, overlap and absent deployment proof. A rejection/not-eligible outcome is recorded in H9 with the failed prerequisites; it is not a separate deferred item or a claim of reusable delivery. Existing persistence and admission boundaries remain the primary test owners.

### H10 — Scientific execution, dependency locking and additional scientific operations

**Owner:** `src/science/{sandbox,models,execution,admission}.py`, artifact references, runtime factory/scientific tools, `src/config/{models,authentication}.py`, `config/runtime.yaml`, Dockerfile and retention. **Requirements:** G38–G42/G47/G56–G58/G68.

1. Replace Docker-specific canonical ownership with one ScientificExecutionBackend contract; retain Docker implementation for local proof if useful. Generalize existing receipts/replay/measurement validators with typed backend-specific environment identity and compatibility for historical Docker receipts. Configure Railway's local venv implementation without requiring a Docker daemon; do not create parallel admission paths.
2. Each experiment owns `experiments/<experiment-id>/{repository,venv,inputs,outputs}` inside its block workspace. Never install into application `.venv` or inherit previous block dependencies. Initially support Python-compatible methods only; R/Conda/CUDA/Docker-required methods/daemons remain unsupported unless separately implemented and verified.
3. A venv isolates dependencies, not filesystem/process authority. Reuse or strengthen actual POSIX confinement for scientific subprocesses/descendants, read-only exact inputs/application, own output writes, peer/DB/credential denial, scrubbed auth domains, bounded runtime/CPU/memory/downloads and appropriate controlled acquisition versus execution network behavior. Fail closed if the backend cannot enforce its declared contract; H11 verifies target behavior. Avoid relaxing current sandbox security to make Railway execution appear successful.
4. Persist repo URL/commit/package-version/app version/backend/Python/OS-base runtime/dependency resolution and lock identity/install-test-execute commands/input refs-hashes/parameters/output hashes/validator/first run/replay/limits. Prefer repo lockfile, then pinned requirements, reproducibly resolved set, then freeze+hash with declared reproducibility limitations. Reinstall/replay in a fresh environment and compare exact retained output identity. Freeze alone is not proof of recoverable dependencies; prevent unsupported reusable promotion.
5. Preserve declared experiment→exact software/input→controlled deterministic execution→replay/validation→typed measurement→Science validation→explicit admission. Generic Coder/shell/prose/hypothesis/Jev/plot/notebook output cannot cross admission. Extend F6 archival to clones/venvs/scratch removal only after required artifacts, environment/dependency identities, receipts, revisions, memory and ledger are durable. `/work/director` remains outside block retention.

**Exit proof:** representative compatible repo completes first run/fresh-environment replay through canonical Science path on local backend without Docker; app env unchanged; dependency/input/output identity corruption and wrong ownership reject; Coder output remains ineligible; retained Docker backend passes the shared contract. Primary owner `test_boundaries.py` for actual backend execution/admission and `test_persistence.py` for retained/reopened identity. Run focused tests, `scripts/verify_scientific_artifacts.py` as applicable, architecture/diff checks; actual confinement/platform proof remains separately recorded at H11.

#### H10a — Integrated D8: stronger external dependency locking

**Trigger:** Repeatable reinstall is required, or dependency drift breaks replay.

1. For each selected/reusable external method, retain the preferred repo lockfile, pinned requirements or reproducibly resolved package set, including transitive versions, hashes/available package identity, supported platform/Python constraints and installer/runtime version. Retain install commands and post-install freeze/hash as audit information, with explicit limits when packages cannot be recovered exactly.
2. Reinstall independently into a fresh experiment environment and replay against exact owned inputs/parameters. Compare dependency/environment and output identity; exercise drift, unavailable packages, conflicting pins and corruption. A repo commit, image identity or freeze hash alone cannot establish repeatability.
3. Route reusable-status acceptance through H9 only after these checks pass. Record unreproducible dependency state and the failed reinstall/replay gate here; block unsupported REUSABLE claims while preserving allowed exploratory results and honest execution receipts.

**Acceptance:** real fresh reinstall/replay protects the selected method's dependency contract; app `.venv` and other block environments remain unchanged. Backend execution/admission tests own credible reinstall/drift failures, persistence owns exact retained identity/reopen, and H9 consumes their proof. D8 is a required execution batch, not a later packaging task.

#### H10b — Integrated D7: operation-specific science and source expansion

**Trigger:** A concrete research need, available inputs, scientific contracts and operation-specific execution proof. This includes broader MAF/VCF/expression work, static GDC extraction/joins, TMB and survival.

1. Derive candidate operations from actual Director/Researcher uncertainties, capability gaps and H6 input/representation contracts. Assess MAF/VCF, expression/count processing, static GDC extraction/joins, exposure/paired analyses, TMB, survival and other approved source families explicitly. Record need, supported access, available exact inputs and remaining prerequisites for each relevant family; catalogue growth alone is not a scientific need.
2. Specify a selected operation before execution: input/schema/entity identity, population/design/estimand, denominators, transformations, missing/invalid accounting, diagnostics, output interpretation and validator. MAF/VCF requires reference/sample/somatic/filter semantics; expression requires gene/count/length/unit/normalization contracts; static joins require documented keys/cardinality/pairing and exclusions; TMB requires callable/capture denominator and variant eligibility; survival requires time origin, event/censoring, population and design/diagnostics. Missing prerequisites remain unknown, never invented zeros.
3. Implement the smallest selected `src/science/` or approved `src/sources/` operation/adapter with a narrow OncoLab contract. Execute it on approved retained inputs through H10's backend/locking and existing Science validation/admission; prove first/replay and actual result interpretation. Any new parser/wrapper/algorithm/source/admission code follows ordinary engineering, not dynamic declarative promotion or application imports from `.upstream/`.
4. Add H13 operation-specific outcomes/resources and held-out valid/invalid/prerequisite cases. Report the exact operation and input scope delivered, not an entire capability family. When a family's concrete need or available inputs are absent, record that gate outcome and source-bound limitation in this phase; GDC file access alone does not complete an analysis or require every family to execute. cBioPortal/Hugging Face still require later explicit approval.

**Acceptance:** each selected operation has real execution/replay/admission proof and protected design/denominator/missingness behavior; each assessed but ineligible family has explicit current-phase prerequisites. `test_boundaries.py` owns actual operation behavior, persistence covers novel retained/reference contracts, H13 reports source-bound outcomes without claiming clinical utility. H6/H10/H13 jointly deliver this work; no independent additional-science backlog remains.

### H11 — One durable Railway worker and truthful confinement status

**Owner:** Dockerfile, railway.toml, service/env/config, read-only operational application/API, existing Coder verifier plus scientific backend proof. **Requirements:** G43–G47/G56/G58/G63/G69.

1. Keep API and autonomous loop in one service with one Director and one active Researcher; redeploy only for application/software changes. Sequential blocks/dossiers/evidence/hypotheses/memory/verifications/registry revisions/promotions/reviews/exports must not restart normal research.
2. Require/document `ONCOJEV_DB_PATH` on durable mounted storage for production; SQLite plus one worker/volume is the initial design. Verify writable ownership, mount/reconstruction and restart behavior. Expose DB location and configured/verified/unknown persistent-storage state without credentials; a path string alone does not prove persistence. No speculative Postgres migration.
3. Run `scripts/verify_coder_container.py` in the actual deployed environment where possible; capture image/runtime/app identity, Landlock ABI≥3, both own workspace writes, app read-only, peer and credential denial, environment scrubbing and descendant confinement. Verify H10 scientific executor's actual isolation/resource contracts too. Linux image/local Docker proof is not Railway kernel proof.
4. Preserve failed-closed deployment on unavailable/failed confinement; record the exact external blocker without silently removing Coder or weakening controls. Reconstruct durable memory/revisions/program state on service restart; interrupted Researcher closes honestly without resumption. Test graceful shutdown and read API visibility while active.

**Exit proof:** several sequential real service blocks and a dynamic revision transition without restart, durable reopen after process/service reconstruction, honest interruption and credential-free logs/exports. Primary owner `test_persistence.py`; Linux/deployed verifier is a separate mandatory operational gate. Run owning tests and architecture/diff checks; record exact Railway smoke/volume/kernel findings or unresolved external setup. No deployment is performed by this documentation task.

### H12 — Deterministic oncojevlab exporter and isolated publisher

**Owner:** deterministic application/export module and `scripts/` entrypoint, persistence export/publication records, service event hooks; external repo `asimog/oncojevlab`. **Requirements:** G48–G53/G56/G70.

1. Read only authoritative persisted records at a pinned high-water/revision and render compact populated Markdown/JSON. Director never edits notebook files. Suggested structure: README; program/current-direction, frontier, open-uncertainties, contradictions; blocks/<id>/summary + dossier JSON; hypotheses/current; capabilities/current, gaps, revisions, proposals; program-reviews; engineering/proposals. Generate useful populated paths only.
2. Render BlockDelta, relation/contradiction context, capability gaps/revisions/proposals, program reviews and engineering proposals with authoritative IDs, basis/version/limitations. Label evidence, measurement, hypothesis, semantic judgment, Director decision and operational failure distinctly; keep objective attainment unknown where unestablished. Stable ordering/formatting and record-derived timestamps make identical DB snapshots produce identical bytes.
3. Publication is a downstream operation using separate configured Git credentials outside all Coder/scientific environments. Commit at block completion, material global-frontier update/new contradiction, accepted revision/capability proposal/program review/engineering proposal/mission change, with templated messages; skip no-op content, never commit every model turn. Persist deterministic export and publication identities independently of scientific finalization.
4. GitHub/setup/credential failure records a publication failure, retains export/DB state and cannot roll back evidence or fail block closure. Absent setup is an external requirement: finish/review exporter and report it. Notebook edits are never ingested as scientific truth. Bound retry attempts and deduplicate by exported state/event boundary.

**Exit proof:** same persisted snapshot yields identical bytes, all claims trace to typed IDs, secrets absent, external edits cannot change scientific records, failed publish leaves closure/evidence unchanged and defined boundaries deduplicate commits. Primary owner `test_persistence.py` at exporter/publication service boundary; add a distinct owning export test file only if needed for that new public contract. Run focused tests, local exporter dry-run, architecture/diff checks; external publication proof separately recorded when configured.

### H13 — Labelled semantic/scientific utility evaluations

**Owner:** `src/evals/{models,corpus,selection,harness}.py`, `scripts/evaluate_selection.py`, existing `evals/jev/` guidance and eval receipts. **Requirements:** G33/G59/G60/G64/G67.

1. Start cases as each phase ships: static OncoLab and bio.tools selection, semantic mismatch, representation sufficiency/GDC assets, hypothesis duplicates vs independent replication/test alignment, contradiction vs population differences, cross-block relations, memory relevance/actionable uncertainty and capability-gap grouping. Labels are evaluation data and never runtime evidence.
2. Retain dataset/case identity, retrieval/projection/question/policy versions, requested/resolved models, native distributions, deterministic inputs/retained frontier, failures and resource use. Compare deterministic retrieval/policy; deterministic+Reasoner where appropriate; deterministic+Jev; current full Director/Researcher system with comparable input/allowance accounting and explicit resource differences.
3. Report retrieval/external discovery/representation recall, suitability retention, duplicate suppression, replication preservation, hypothesis alignment, relationship recovery, contradiction detection, memory relevance, important-alternative retention, global diversity/duplicate-block suppression, explicitly recorded uncertainty resolution, unique source-bound outcomes, operational failures, elapsed/resource use and Jev failure fallback. No universal research-quality score or unsupported winner from one tiny live run.
4. Benchmark search scale before FTS/ontology/embeddings; measure semantic instability before calibration/self-consistency/Autoresearch. Distinguish labelled semantic metrics from scientific validity and clinical effectiveness. Record cases missed before/after, retained alternatives and limits, not just aggregate means. Continue other conditions after failure with partial results and honest receipts.

5. Supply and record gate evidence for every integrated batch: multi-domain generator contracts/recall (H4a/H14), hypothesis duplication/alignment failures (H4b), available-but-missed representations/schema mappings (H6a), scan/FTS/vocabulary/embedding scale/coverage comparisons (H7a), repeated validated promotion utility (H9a), locked reinstall/replay and operation-specific outcomes (H10a/H10b), and repeated fixed-input semantic instability with budgeted calibration comparisons (H14a). Return results to those phases for their implementation/acceptance decisions before H15; an evaluation report alone does not deliver the dependent mechanism.

**Exit proof:** labelled cases reproducibly execute real retrieval→projection→policy and end-to-end fresh conditions, report versioned/resources/failure-aware outcomes and never contaminate admission. Primary owner `test_evaluation.py`; exact live/fixture evaluation outputs retained as evaluation artifacts. Run owning tests and `uv run python scripts/evaluate_selection.py` with documented available cases/arguments; full-system evaluation entrypoint follows actual harness, not an invented command. Utility conclusions require adequate data and limitations, not test pass counts.

### H14 — Frontier policy audit, shared generator contract and bounded calibration

**Owner:** `src/jev/frontier.py` and every production caller in runtime semantic/contracts; versioned policy config/receipts and H13 cases. **Requirements:** G8/G54/G55/G64.

1. Reconcile H0 inventory for both `interpret()` and `decide()`. Current `evaluate_candidate` calls `decide`, so verify its public behavior before deciding migration/removal. Migrate legacy callers to the correct multidimensional owner, or retain a necessary context under its own explicit policy version and evaluation. Do not leave two unintentionally canonical local policies or collapse local/global policies.
2. Treat historical .2/.25/.4–.6/.5 cutoffs as context-specific software policy, not scientific constants. Retain distribution/uncertainty/alternatives/failure fallback and historical receipt versions. Remove dead competing paths only after real callers are migrated and independent regression/eval proof passes.
3. Complete H4a's D3 multi-domain generator comparison after H6/H7 real generators and H13 cases exist. When its shared-contract/recall trigger passes, extract and use the smallest tested production generator interface; otherwise retain the domain contracts and record the measured rejection. Global/local scientific scope, authority, policy and stop semantics remain distinct.
4. Execute the D5 experiment batch below using H13 instability/recall/resource evidence. Preserve scientific-method experiments separately from cleanup commits; no automatic live question/policy rewrites or autonomous self-promotion.

**Exit proof:** exact caller ownership documented, old receipt interpretation remains reconstructable, relevant local/global behaviors survive migration and labelled retention/fallback/calibration results support policy changes. Primary owner existing `test_boundaries.py` semantic cases, evaluation owner `test_evaluation.py`; do not add source-inventory tests. Run focused files/evals and architecture/diff checks.

#### H14a — Integrated D5: semantic calibration, self-consistency and Autoresearch

**Trigger:** Measured instability justifies the additional budget.

1. H13 repeats fixed-input, versioned semantic cases and measures distribution/retention disagreement, calibration on labelled outcomes, useful-alternative loss and elapsed/token/question/cost use. Separate operational provider failures from semantic variation, keep unknown reported cost unknown, and define the extra experiment allowance explicitly before running it.
2. Where instability meets that documented gate, run bounded offline calibration or self-consistency comparisons against the deterministic/single-measurement baseline. Preserve native distributions and fallback; measure whether the change reduces instability or useful-candidate loss within its allowance rather than averaging uncertainty away or selecting a winner from one tiny run.
3. Under the same measured-instability and explicit resource-allowance gate as step 2, implement a bounded Autoresearch-style evaluation loop only for approved experiment variants such as projection/question/policy candidates on the labelled corpus. Persist variant/version/model/receipt/resource/result identity and produce an EngineeringProposal for any adopted production change. No self-reward score, automatic production-source/question/policy rewrite, evidence admission or Jev self-promotion is permitted.
4. Adopt only a versioned, behavior-tested, evaluation-supported change through ordinary reviewed engineering. If instability is absent or extra calls do not justify their cost, record the measured no-change decision here with the covered cases and limits. The experiment/gate result is required in H14, not a separate future Autoresearch program.

**Acceptance:** repeated-case evaluation and budget accounting are reproducible; candidate recall, alternatives, operational fallback and global/local policy boundaries remain protected. `test_evaluation.py` owns experiment/resource/failure reporting; existing boundary tests own any adopted policy behavior. No test pass or calibration score establishes scientific or clinical effectiveness.

### H15 — Reconcile implemented documentation and verify the full system

**Owner:** existing AGENTS/README/architecture/constitution/Jev/capability/frontend and module READMEs, this tracker; full integration paths. **Requirements:** G0/G55/G57/G58/G71–G73 and all acceptance/final-report sections.

1. As implementation lands, replace target labels only where runtime proof exists. Reconcile instructions/roles/tool names/config/backends/deployment with real behavior, preserve the complete supplied reference and untouched historical F0–F6 evidence. No duplicate architecture or second live status tracker. Verify each integrated D1–D8 batch's phase-owned implementation and gate outcome; change completion only on actual evidence, never restore a standalone deferred-work list.
2. Run full `uv run pytest`, architecture checker and `git diff --check` after focused batches. For any UI changes run its existing type/build/tests and real read-only browser flow; render program pause/run outcome/revision/export/confinement honestly without moving orchestration/admission into `web/`.
3. Exercise continuous service→allocate/start→independent bounded Director→terminal/delta/memory→basis revalidation→next block/pause; registry update→next pinned revision; GDC selected bytes→experiment→replay→Science admission; export→publication success/failure; shutdown/reconstruction→honest interruption. Capture live smokes/evaluations/deployed checks separately and flag unavailable external proof.
4. Produce all 24 final-report fields from the supplied reference: starting/ending HEAD, commits/batches/files, preserved F contracts, Director before/after and harness/async behavior, global Jev/memory/relations, complete OncoLab layer/revision/discovery/promotion account, D1–D8 changes, execution/backend/environment identity, Railway persistence/confinement/blockers, exporter/publication failure semantics, exact tests/smokes/evals/results/utility limits, remaining science/capability/deployment gaps, deferrals and prompt-vs-current discrepancies. Never claim completion from document/type/fixture existence.

**Exit proof:** each acceptance row below links delivered path and validation evidence; external blockers are explicit and not reported as passing. Final stage stays incomplete when required deployment proof is missing. Planning-document delivery is complete when preservation/links/coverage/diff/architecture checks pass; it does not complete H1–H14.

## 5. Complete supplied-requirement traceability

Every point in each G section remains in the preserved reference. This table identifies the primary phase and dependent proof rather than replacing the section's detailed requirements. Cross-cutting prohibitions/thesis/baseline, supplied H order, final acceptance and final report also apply to all phases.

| Requirement | Primary owner | Implementation/proof disposition |
| --- | --- | --- |
| G0 — Audit current main | H0 | Recorded HEAD; complete specified caller/config/test/deployment trace before coding. |
| G1 — Retain Director Coder + CodeMode | H1 | Preserve both roles and bounded Director scratch; H11 actual target proof. |
| G2 — Global research manager | H1/H4 | Full global responsibilities; local strategy stays Researcher. |
| G3 — Non-blocking Researcher lifecycle | H2 | Python-owned single task; immediate run handle, no distributed queue. |
| G4 — Event-driven Director | H3 | Bounded meaningful turns/yield; no model polling. |
| G5 — Isolate active run state | H2 | Typed IDs/pins/budgets/task/start sequence; safe persistence ownership. |
| G6 — BlockDelta | H3 | Reference-linked deterministic changes, no unsupported inference. |
| G7 — Global Director Jev frontier | H4 | Atomic measurements→deterministic beam→one Director choice. |
| G8 — Distinct global/local frontiers | H4/H14 | Separate candidate/scope/authority/stop/policy interpretation. |
| G9 — Legitimate pause/stop | H3 | Explicit zero-block program pause, no mission-success claim. |
| G10 — Global semantic Research Memory | H4 | High-recall retrieval/exact duplicate first, bounded dimensions. |
| G11 — Global hypotheses | H4 | Stable identity/status distinctions and independent replication. |
| G12 — Cross-block discovery | H4 | Typed relation candidates with refs/distributions/basis/limits. |
| G13 — Contradiction frontier | H4 | Conflict/population/design/method/phrasing distinction; preserve originals. |
| G14 — Stale parallel planning | H3/H5 | Basis pins and terminal/revision revalidation before allocation. |
| G15 — Program review | H4 | Descriptive concentration/failure/uncertainty review, no reward score. |
| G16 — Engineering intelligence | H4/H9 | Record-backed EngineeringProposal, scratch only, no Engineer agent. |
| G17 — Institutional OncoLab | H5 | Static seed plus dynamic verification/use/failure/demand/proposal history. |
| G18 — Version OncoLab | H5 | Immutable reconstructable revisions/block pins/hot refresh. |
| G19 — Three discovery layers | H5 | Curated capabilities vs external candidates vs data assets. |
| G20 — Files are not capabilities | H6 | Typed ScientificDataAssetCandidate/equivalent; methods alone indexed. |
| G21 — GDC file discovery | H6 | Field contracts, complete metadata/query/order/page/coverage identity. |
| G22 — GDC file acquisition | H6 | Existing exact bytes/MD5/SHA/size/ownership/access bridge. |
| G23 — GDC representations | H6 | Actual assets→availability→Jev sufficiency→retained frontier. |
| G24 — bio.tools adapter | H7 | Bounded current filters/pagination/cards; metadata not proof. |
| G25 — EDAM semantics | H7/H13 | Returned IDs/terms first; H7a measures and delivers justified vocabulary/resolver/snapshot expansion. |
| G26 — bio.tools to Jev selection | H7 | Deterministic runtime/input checks before bounded semantic fit. |
| G27 — GitHub discovery | H8 | Public bounded metadata; pinned compatible Researcher execution. |
| G28 — Bioconda enrichment | H8 | Compatibility/reproducibility metadata; no mandatory Conda. |
| G29 — Bioconductor discovery | H8 | Metadata-only until separately verified R support. |
| G30 — Optional sources | H8 | Extension seam, no automatic adapter suite or cBioPortal/HF. |
| G31 — External discovery interface | H7/H8 | One bounded interface/receipts; GDC resource model separate. |
| G32 — Multi-stage capability search | H7 | Preserve local staged F4 selection then unmet-need external path. |
| G33 — Search scale / D6 | H7/H13 | H7a executes staged scan→FTS→vocabulary/ontology→embedding gates and qualified extensions. |
| G34 — Capability gaps | H5/H4 | Actual reference-linked demand/failure, semantic grouping not capability. |
| G35 — Governed promotion | H9 | Explicit versioned checks/ACCEPT-REJECT; no count-only validity. |
| G36 — Declarative vs code-requiring | H9/H10 | Generic executor declarations vs EngineeringProposal; no live patch. |
| G37 — Review/reverification | H9/H5 | Minimal typed proposals; Python transitions, no unrestricted CRUD. |
| G38 — Remove Docker-in-Docker dependency | H10 | Shared scientific backend result; Railway local venv, optional Docker. |
| G39 — Scientific environment | H10 | Per-experiment dependencies; application env unchanged; honest runtime support. |
| G40 — Exact experiment identity | H10 | Software/runtime/dependencies/commands/input-output/first-replay/validator. |
| G41 — D8 locking | H10/H9 | Prefer reproducible locks/pins; retain result; block unsupported reuse. |
| G42 — Evidence discipline | H10/all | Science-only deterministic validation/admission; Coder output ineligible. |
| G43 — One Railway worker | H11/H2 | One service/Director/active Researcher; normal state changes no restart. |
| G44 — Durable persistence | H11 | Durable ONCOJEV_DB_PATH volume and truthful operational status. |
| G45 — Railway Coder verification | H11 | Actual target ABI/paths/secrets/descendants; explicit blocker if unavailable. |
| G46 — Director Coder authority | H1/H11 | Scratch cannot modify evidence/registry/policy/production/peer state. |
| G47 — Cost/budgets | H1/H2/H3 | Independent counters/parallel allowance/aggregate limits; cost unknown retained. |
| G48 — oncojevlab | H12 | Separate readable repository; database authoritative. |
| G49 — Notebook structure | H12 | Compact useful populated program/block/hypothesis/capability/review/engineering paths. |
| G50 — Deterministic exporter | H12 | Persisted typed state→renderer→Markdown/JSON→Git; explicit claim labels. |
| G51 — Publication failure | H12 | Durable failure, no scientific rollback; absent setup reported. |
| G52 — Commit boundaries | H12 | Defined material events, templated messages, no per-turn commit. |
| G53 — Three memory surfaces | H3/H12 | DB authority, typed Director memory, human projection distinct. |
| G54 — Frontier audit | H0/H14 | Both real callers traced; migrate or separately version/evaluate. |
| G55 — D1–D8 integrated delivery | H4/H6/H7/H9/H10/H13/H14/H15 | All original triggers preserved inside owning implementation batches; evaluated gate outcomes and actual proof required. |
| G56 — Access/licence truth | H6/H7/H8/H9/H10 | Known/unknown/controlled/public/unverified explicitly separate. |
| G57 — Historical inputs | H0/H15 | Missing exact bytes stay unreplayable without verified recovery. |
| G58 — Retention | H3/H10/H11 | F6 archival extends experiments; durable identities/history preserved. |
| G59 — Evaluate thesis | H13 | Correctness distinct from utility; meaningful conditions and resources. |
| G60 — Evaluation corpus | H13 | All 13 supplied case families, versions/models/native distributions. |
| G61 — Director tools | H1/H4/H9 | Full typed MEMORY/SEMANTIC/ONCOLAB/CONTROL/CODER surface as owners ship. |
| G62 — Researcher ownership | H1/H10 | All local scientific decisions/prototyping/escalation/completion retained. |
| G63 — Director tests | H1/H2/H3/H11 | Harness denial/async single run/events/state-deadline/staleness/pause proof. |
| G64 — Global Jev tests | H4/H14 | Retrieval/bounds/duplicates/replication/non-evidence/fallback/beam/distinct policies. |
| G65 — OncoLab tests | H5/H9 | Seed/reopen/immutability/pins/history/governance/non-promotion/hot usability. |
| G66 — GDC tests | H6 | Full metadata/pagination/access/bytes/hashes/ownership/grouping, preserved F5. |
| G67 — External search tests | H7/H8/H13 | Real filters/cursors/cards/receipts/non-authority/route/access/outage; fixtures + smoke. |
| G68 — Scientific execution tests | H10 | No daemon, isolated env/pins/replay/output/admission and optional Docker parity. |
| G69 — Railway/persistence tests | H2/H11 | Sequential runs/hot revisions/lifetime Director/reopen/interruption/durable status/secrets. |
| G70 — oncojevlab tests | H12 | Authoritative deterministic export/no reverse input/secrets/failure/event commits/refs. |
| G71 — Implementation order | H0–H15 | Supplied phases retained with dependency gates, focused checks and batch commits. |
| G72 — KISS | All | Single service/database/Director/Researcher/registry/executor/notebook. |
| G73 — Documentation | H15 | Existing docs updated when proven; historical F evidence/reference preserved. |

## 6. Final acceptance and remaining external proof

Use the complete acceptance lists and 24-field final-report contract in the preserved reference; none is waived by this summary. Attach actual executable path, test/eval/smoke/deployment record and remaining limit to each row before stage completion.

| Acceptance area | Required delivered behavior | Primary proof phases |
| --- | --- | --- |
| Director | Persistent global manager with bounded Coder/CodeMode/scratch, event-driven independent work, semantic memory/hypotheses/contradictions/gaps/reviews, truthful pause and stale-plan revalidation; no source/policy/active-block mutation. | H1–H4/H11/H14 |
| Researcher | Fresh per block, both harness facilities, local strategy, installed Python/public compatible repos with isolated dependencies, no admission bypass. | H1/H2/H10/H11 |
| Jev | Bounded distribution-bearing semantic search across memory/capabilities/representations/hypotheses/contradictions/future blocks; no lifecycle/evidence/capability authority. | H4/H6/H7/H13/H14 |
| OncoLab | Static seed plus immutable dynamic institutional state/pins/history/gaps; GDC assets and bio.tools/GitHub/Bioconda/Bioconductor discovery; governed hot declarative promotion; no file UUID capabilities/bulk import. | H5–H9/H10/H11 |
| Science | Truthful GDC discovery/open-file exact artifact bridge/explicit controlled status; compatible scientific repos without Docker-in-Docker; reproducible auditable identity; Coder remains non-evidence. | H6/H10/H11 |
| Railway | One worker, sequential blocks without normal restart, durable DB, actual Coder/scientific confinement verified or explicitly blocked. Unavailable proof cannot be marked passing. | H11 |
| oncojevlab | Separate deterministic reference-linked readable non-authoritative history; publication failure harmless to scientific state. | H12 |
| Evaluation | Correctness, semantic utility, retrieval expansion and cross-block behavior measured separately with resource reporting; all integrated D batches receive recorded gate evidence and phase decisions; no unsupported discovery-improvement claim. | H4/H6/H7/H9/H10/H13/H14 |

External setup to verify during implementation: actual Railway access/volume mount/Landlock/runtime constraints; supported scientific package/network resources; current bio.tools/GDC/metadata API behavior and selected access/licence facts; `asimog/oncojevlab` repository and separate publisher credentials; live model/data connectivity and sufficient labelled evaluation cases. These are verification gates or scoped setup requirements, not assumptions or reasons to stop independent documentation/local implementation.

### Planning-delivery verification — 2026-10-01

This subsection records this documentation delivery and checks against the unchanged runtime only. Next-stage regressions, provider smokes, deployments, scientific experiments and utility evaluations for H1–H14 remain future work. Starting and ending HEAD are both `c9712e67050548354d32fcd6bb5b910569449431`; no commit or publication was performed.

| Check performed | Exact result and scope |
| --- | --- |
| Reference byte comparison and SHA-256 against supplied attachment | Identical bytes; `101fb984c7d15d03d3220d9e8c43bcf241edb7d84c9934e708e3e455dcca2b65`. Every supplied point remains available. |
| Archived plan body compared with `git show HEAD:docs/IMPLEMENTATION_PLAN.md` | Entire original text unchanged after normalizing Git LF/worktree CRLF; only the archival DONE/header is added. |
| G/H/D traceability validation | Original planning check: all 74 G0–G73 rows mapped exactly once, all 16 H0–H15 phases and eight D1–D8 rows present. The subsequent integration revision moves all eight items into phase-owned batches, preserving their triggers; there is no standalone deferred table. |
| Markdown/scope validation | 15 changed/new Markdown files only; 53 local links resolve; code fences balanced. No runtime/config/test/UI changes. |
| `.venv\Scripts\python.exe -B scripts/check_architecture.py` | Exit 0: `architecture checks passed`. |
| `.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/invariants/test_live_mode.py -q` | Exit 0: all 25 existing runtime/auth/budget/Jev boundary cases pass; one existing `pydantic_graph` event-loop deprecation warning. Count confirmed by collect-only, not a second test run. |
| `git diff --check` | Exit 0; Git reports LF→CRLF worktree warnings, no whitespace errors. |
| Independent read-only review | Confirmed target coverage and baseline source facts; incorporated zero-block CLI consumer handling and consistent H10/H11 promotion gates. |
| Subsequent D1–D8 integration revision | Removed the separate carry-forward table and integrated eight named implementation/evaluation batches into H4/H6/H7/H9/H10/H14. All eight original triggers, their scope and proof requirements remain; H13 evidence returns to the owning phases. |
| Integration coverage/preservation/link checks | Eight integrated batches each contain an original trigger, numbered implementation tasks and acceptance criteria; all 74 G mappings and 16 H phases retained; complete source/archive unchanged; 53 local links resolve and fences balance. |
| `.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -o addopts='' tests/invariants/test_evaluation.py -q` | Exit 0: 10 passed, one existing `pydantic_graph` event-loop deprecation warning, 30.03 s. This checks the unchanged evaluation runtime, not delivery of planned features. |
| Main-checkout integration scope | Updated the active plan and nearest AGENTS/README/architecture/capability/module guidance in `C:\dev\oncojev` only. The separate `.kilo/worktrees/rustic-faucet` checkout remains clean and unchanged, as requested. Architecture and diff checks pass; HEAD unchanged. |

Only AGENTS/README, existing architecture/constitution/capability/Jev/frontend/upstream documentation, four module READMEs, the active plan, completed archive and preserved reference changed. No historical database writes, `.upstream/` inspection, dependency installation, live provider call, deployment, new scientific method or external publication occurred. Planning/documentation is delivered; the new runtime stage remains PLANNED.
