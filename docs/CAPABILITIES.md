# OncoLab Index semantics

The sections below describe the delivered F0–F6 capability contracts. Their
completion evidence and original deferrals are preserved in the
[completed F0–F6 plan](IMPLEMENTATION_PLAN_COMPLETED_F0_F6.md). The
[active H0–H15 implementation plan](IMPLEMENTATION_PLAN.md) owns next-stage
status. The [complete supplied requirements](references/NEXT_STAGE_AUTONOMOUS_LAB_REQUIREMENTS.md)
remain the reference for that stage. The next-stage section at the end of this
document describes planned work, not delivered capability.

Cross-cycle research context lives in `src/memory/`, separately from capability
verification. Versioned digests reference recorded outcomes, measurements,
evidence, hypotheses, semantic candidates, blockers, uncertainties and proposals.
Director prose is optional context. Factory/service backfill appends derived
records and respects effective legacy outcome corrections; it never reruns work.

Both roles can use `search_research_memory`, `get_dossier`, `get_evidence`,
`get_hypotheses`, `get_negative_results`, `get_open_uncertainties` and
`resolve_memory_reference`. Director `read_research_memory` now returns a bounded
typed context envelope rather than a recent-prose list. Retrieval accepts mission,
declared entity/topic and timezone-aware time filters. Search uses stable lexical
relevance, not automatic newest-result copying; bounded semantic memory context is delivered in F4; broader utility validation remains an earned deferral.
The Director receives retrieved context automatically and allocation retrieves
again for its selected objective. Both Researcher launch paths receive the validated
start packet, while state/evidence/measurements/skills/budgets remain fresh.

Digest context is bounded to 20 results and 32 KiB; start memory to 16 KiB. Exact
records remain hash-resolvable. Oversized requested records return an explicit
omission response instead of silently changing measurements. Current Science
outputs do not declare scientific negatives: the separate negative-results field
remains empty for them. Provider failures and semantic rejection cannot populate it.

`OncoLabIndex` is the one shared application registry for Director and Researcher within a runtime. It provides bounded deterministic retrieval and loads bundled records from `src/oncolab/proven/verified-executions.yaml` plus resolvable durable verification receipts through factory composition, separately from descriptor status. Loading is idempotent by capability/verification identity and never resumes research. Verification names a declared execution, not the maturity or scientific validity of a statistics family. `describe_oncolab` returns at most 20 verification records and an omitted count. The Pydantic AI harness is only a client through runtime dependencies; it owns no registry. “OncoLab” names this domain index; Pydantic AI capabilities and tools remain framework plumbing under `src/runtime/pydantic_ai/`.

The Index describes data/source capabilities, scientific and statistical methods, transformations, software, visualization, literature/knowledge, and Jev measurements. It uses typed descriptors with purpose, contracts, applicability, limitations, assumptions, missingness semantics, availability, execution/access policy, resource class, validation state, and provenance. It is metadata only: typed wrappers remain the only route to execution.

Index availability is explicit: `known`, `available`, `installed`, `acquirable`, `validated`, `reusable`, `unavailable`, or `forbidden`. It is distinct from validation state: a known or acquirable item is not a validated executable scientific capability. Retrieval is deterministic metadata/text matching and capped at 20 results; neither agent receives the complete catalogue in its prompt.

The initial catalogue contains over 100 descriptors. It includes GDC endpoint, retrieval, pipeline, entity, and workflow-reference metadata plus statistical-method planning families; these entries remain descriptors, not pipelines or arbitrary Python APIs.

Phase 3 makes a deliberately small subset executable through typed Researcher tools: anonymous GDC metadata retrieval (with an enforced `files.access == open` filter for file searches), anonymous UCSC Xena catalogue lookup, public literature metadata retrieval, NumPy/pandas/SciPy/statsmodels measurements, and matplotlib SVG `FigureArtifact` production. Each source wrapper accepts no credentials and enforces the configured response-byte budget. Source records are retained by acquisition ID so Science can deterministically measure the exact stored acquisition. Agent-provided numeric arrays are exploratory measurements and cannot be admitted; only source-bound or replay-validated measurements cross evidence admission.

When no adequate installed method exists, a Researcher may use the `software.github-scientific` capability. It accepts only an HTTPS GitHub repository, resolves an exact commit, and runs installation with a credential-free Docker sandbox. Tests and two identical command replays run without network; strict JSON parsing plus replay comparison produces a `SandboxMeasurementCandidate`. Only a separate deterministic validator can turn that candidate into a `MeasuredResult`, followed by ordinary Science admission. The method is not promoted merely because it ran.

Capability maturity remains explicit:

| State | Meaning |
| --- | --- |
| Descriptor | Catalogue metadata only. |
| Local capability | A block- or application-local implementation or question. |
| Validated capability | Has defined validation evidence for its declared use. |
| Reusable capability | Validated, provenance-bearing, and eligible for registry reuse. |

`ScientificCapability` is deterministic executable scientific work. `JevCapability` is an evaluated reusable semantic measurement. A `JevQuestionSpec` is normally a local semantic probe. A Skill is progressive procedural/domain guidance. Pydantic AI capabilities/tools are framework plumbing and live behind `src/runtime/pydantic_ai/`.

Acquisitions and literature context are persisted before use, including exact
request identities, content, response-byte reports and stable content hashes
that exclude acquisition UUIDs. Science resolves block-owned acquisitions from
storage; another block's acquisition ID does not grant access. Reconstruction
exposes exact available inputs and explicitly lists unresolved legacy references.
`science.acquisition-summary` identifies the existing descriptive slice-count and
numeric-field wrapper; its output does not establish population coverage.

Index search, describe and execution-selection receipts record actor, filters,
requested/effective bounds, returned or selected catalogue IDs and mission/cycle/
block association. Director receipts may precede allocation. Researcher searches
use the configured cap. Invocation views derive from ledger events; skill-load
receipts remain separate. Dossiers report source attempts, successes, failures,
reported bytes and the number of byte reports, preserving incomplete reporting.

Verification references distinguish portable files from block-owned measurement,
evidence, acquisition, literature, sandbox-candidate and artifact records. Hashes
bind references to their exact bytes or canonical record payload. The architecture
checker validates bundled catalogue identities and portable artifact integrity.
The redacted historical live ledger is tracked under `proven/artifacts/`; it proves
observed execution events only. Its absent numeric inputs and SVG bytes are not
fabricated. The former orphan Pearson record now refers to `stat.scipy` and names
only the recorded Pearson invocation. Provided-array statistics remain exploratory;
SVG rendering records carry `artifact_created` and an exploratory label, never
scientific validation.

Sandbox requests are retained before execution. Candidates retain the full request,
policy, immutable commit and resolved Docker image ID, exact JSON output, invocation
receipts, content identity and validator version. Validation checks input/environment/
output hashes, commands, successful exits and replay agreement. An explicit
`DockerScientificSandbox.replay(candidate)` can independently run the stored request
at its resolved commit/image; recovery and Index loading never invoke it. Installation
dependencies remain unlocked, so independent reinstall is an attempt whose output
must be compared; identical historical environments are not claimed.

Selected procedural guidance lives in `src/oncolab/labskills/` and is loaded only
for an active Researcher block. It remains separate from the index and from
Pydantic AI's Coder/Code Mode framework capabilities.

Coder remains available to both roles on Linux. Director scratch engineering uses
`/work/director`; Researcher coding uses only its block workspace. A shared kernel
filesystem boundary makes public application code and policy read-only, denies
peer workspaces and credential files, and applies to native file tools, shell
commands and descendants. It fails closed without the required Landlock support.
Scratch output is neither evidence nor a promoted capability; scientific replay,
validation and admission remain separate typed operations.

`config/runtime.yaml` separates resource budgets:

| Budget | What consumes it |
| --- | --- |
| `max_model_requests` | Role provider requests; Researcher allocation also includes live Reasoner requests. |
| `max_provider_tool_calls` | Framework tool calls, including Code Mode inner tools; failed execution attempts count. |
| `max_code_mode_executions` | Role-wide `run_code` executions. |
| `max_code_mode_tool_calls` | Typed calls within one Code Mode snippet. |
| Block `max_tool_calls` | Local Science/validation/figure operations, separate from framework calls. |
| Source, sandbox, Reasoner call budgets | Attempted resource operations, including failures. |
| Jev call and question budgets | Invocation attempts and individual questions, counted separately. |
| Cycle requests/tools/cost | Aggregate usage across Director, Researcher and live Reasoner. |

Zero-enabled limits are honored without fallback substitution. Optional cost
limits enforce reported costs; usage records flag incomplete cost reporting.
Denied work returns a non-retryable handoff directive before side effects;
inspection and deterministic finalization remain available. Hard SDK limits may
end the agent run, after which Python still records its outcome and partial dossier.

F4 exposes progressive OncoLab cards and explicit contract expansion, plus local method, representation, hypothesis/test and statement-support measurements. Local semantic contracts are not promoted capabilities. External GitHub acquisition retains inadequacy rationale and alternatives; installed lexical overlap no longer vetoes an unmet need. Existing sandbox, credential and allocation limits apply.

F5 adds source-resolved Pearson/simple OLS over one retained acquisition, with unique
entity keys, complete paired rows, explicit fields/transforms/design and missingness
counts. Joins, covariates, survival and TMB remain unsupported. Association is not
causal inference; method assumptions and population representativeness remain
limitations. The bundled Pearson record proves only its three-row fixture.

Open GDC file acquisition requires per-file open metadata and bounded anonymous
streaming, retaining exact bytes/hash/size/source identity in immutable typed
SQLite records. Sandbox requests retain those owned inputs and mount them read-only
at `/input/artifacts/<byte_sha256>` with execution network disabled. Unknown licence
and release remain null. Controlled-access and arbitrary URL acquisition remain
unavailable. JSON acquisition hashes continue to identify structured retained
content, not unstored HTTP bodies.

F6 retains terminal scratch files as immutable byte artifacts and a manifest before
removing a closed workspace. Default minimum age is seven days, at most 20
workspaces and 100 MB per archive. Active, unknown, unresolved-input, linked and
failed-export workspaces remain intact. Durable evidence/replay inputs and ledger
records are never deleted. Oversized archives require an explicit larger budget
or operational review; cleanup does not silently discard them.

Synthetic acquisitions now propagate synthetic measurement origin and cannot be
admitted. Offline snapshots show fixture provenance separately from API transport
and execution mode, with no fabricated evaluated conditions. Presentation retains
failed/incomplete outcomes, unknown objective attainment, source attempts/successes
and scientific limitations. Historical portable records keep their original scope
and missing inputs; new deliveries do not retroactively validate them.

## Next-stage target: revisioned institutional capabilities

**Planned, pending the active H5–H10 phases and applicable H11 deployment proof.** The existing descriptor catalogue,
bounded cards, snapshot-bound continuations, contract hashes, execution routes,
verification records and F4 suitability measurements remain the static seed.
They do not yet constitute a durable dynamically revisioned registry. H5 adds
immutable institutional state in the authoritative database: revisions,
verification and failure history, usage and demand, observed limitations,
suitability history, capability gaps, proposals and review/reverification state.
Each block pins the exact OncoLab revision and application/runtime version.
Historical selections retain their original contracts; new accepted revisions
become available between blocks without restarting the worker.

Discovery keeps three distinct surfaces rather than expanding one catalogue
without bounds:

| Surface | Records and authority | Planned phase |
| --- | --- | --- |
| Curated OncoLab | Existing descriptors/routes and governed reusable capabilities. Presence alone grants no execution or admission authority. | H5, H9 |
| External capability discovery | Bounded candidates from bio.tools, GitHub and optional Bioconda/Bioconductor metadata. Candidates are discovery information, not executable or validated capabilities. | H7, H8 |
| Scientific data assets | GDC file/metadata candidates and selected block-owned retained artifacts. Individual file UUIDs never become capability descriptors. | H6 |

H6 extends current `/files` acquisition infrastructure into first-class bounded
data-asset and representation discovery. Candidate records retain file identity,
name, access, type/category/format, strategy, size, MD5, state, available workflow,
release and case/project metadata, query identity and retrieval time. Existing
pagination, ordering, overlap and coverage rules remain authoritative. Selection
uses actual retrievable representations, deterministic availability checks and
bounded Jev sufficiency/assumption-fit measurements. Open selected files use the
existing exact artifact bridge; controlled access requires a separate explicitly
supported authentication route. Search infrastructure does not deliver MAF/VCF,
expression, TMB, survival or other new Science operations.

H7 introduces one bounded external discovery interface with search/describe
operations, rather than an agent tool for every registry. bio.tools search
supports useful text/identity/domain, EDAM topic/operation, input/output
type/format and pagination filters where the verified source contract supports
them. Candidate cards retain supplied provenance, links, publication, version
and licence metadata. EDAM IDs/terms returned by candidates support controlled
normalization; full ontology ingestion is outside the initial scope. Search
receipts retain query, filters, page/cursor, returned identities, retrieval time,
hashes where feasible, omissions and failures. Mutable registry metadata is never
represented as an immutable source snapshot unless its bytes were retained.

H8 adds bounded GitHub repository/commit/release/package/lockfile inspection and
optional Bioconda recipe metadata for compatibility and reproducibility.
Bioconda metadata does not install Conda. Bioconductor candidates remain
metadata-only until a supported R execution environment is implemented and
verified. Additional sources require a measured retrieval need; cBioPortal and
Hugging Face expansion require explicit later approval.

Capability selection starts with deterministic current-OncoLab retrieval,
compact cards, selected contract expansion and execution/input checks. Jev then
measures bounded semantic suitability and Python retains useful alternatives.
An unmet need may trigger bounded external discovery and equivalent checks.
An installed lexical match cannot veto a demonstrated unmet need, and external
software does not automatically outrank a verified appropriate local method.
Jev suitability never supplies a missing route, supported runtime, input, access
permission or scientific validation.

H9 adds versioned Python governance for promotion, review, update,
reverification and retirement proposals using the minimum necessary models.
Recorded repeated need, validated controlled executions, utility, overlap,
generalization, replayability, failures, scope, typed contracts, exact software
and dependency identities and access/licence limitations inform decisions. One
execution or an arbitrary execution-count threshold cannot establish scientific
validity. Rejection preserves the registry; acceptance appends a new immutable
revision. Unsupported automatic Jev/self-promotion cannot pass governance.

The promotion boundary is executable: a declarative capability can reuse an
already verified generic executor using pinned software/environment, commands,
typed inputs/outputs and validation contracts. Reuse requiring a parser, wrapper,
Science algorithm, source adapter, route or admission change instead produces an
`EngineeringProposal`. Director scratch work cannot modify live source or policy.
Declarative promotion must fail closed until H10 supplies and verifies its actual
execution contract and reproducible dependency identity, and H11 verifies the
applicable deployment confinement. Local proof cannot certify Railway reuse.

H10 replaces Docker-specific canonical ownership with one scientific-execution
abstraction. The Railway target is a per-experiment Python venv executor without
a Docker daemon; the current Docker backend may remain for local verification
under the same canonical result contract. A venv isolates dependencies, not
security. External execution requires verified confinement of application code,
policy, peer workspaces, credentials and input bytes, scrubbed command
environments, bounded resources and verified network restrictions for tests and
execution. Unsupported isolation fails closed. Research packages never enter the
application `.venv`, and no R, Conda, CUDA or daemon support is implied.

Reusable methods require retained repository/commit/package identities,
backend/Python/base runtime, exact dependency resolution/lock identity, commands,
owned input references and hashes, parameters, first/replay receipts, output
hashes and validator version. Dependency locking prefers a repository lockfile,
then pinned requirements, then a reproducibly resolved dependency set, with
post-install freeze/hash retained as an audit record. A freeze alone does not
prove reproducible installation. Unreproducible dependencies prevent unsupported
reusable status. Science validation and explicit evidence admission remain
separate from execution, promotion and discovery.

The active plan integrates all D1–D8 work into the owning H phases rather than a
separate deferred table. H9 executes governed D1 promotion; H6 diagnoses and
repairs available-but-missed D2 representations; H4/H14 qualify shared D3
generators and refine D4 hypotheses; H14 runs budget-qualified D5 experiments;
H7 delivers justified D6 index/vocabulary/ontology/embedding stages; H10 executes
need/input-qualified D7 operations and D8 locked reinstall/replay. H13 supplies
comparative evidence and returns it to each implementation owner. Original
triggers and authority limits remain binding; measured no-change or unmet-input
decisions stay in that phase and never claim scientific delivery. New
infrastructure never reconstructs absent historical bytes by assertion. F6
archive-before-cleanup remains canonical for new experiment scratch, repositories
and venvs; required artifacts, execution/dependency identities, evidence,
revisions, Research Memory and ledger history remain durable.
