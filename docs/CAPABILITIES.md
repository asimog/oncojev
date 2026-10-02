# OncoLab Index semantics

Current capability and verification contracts. [Architecture](ARCHITECTURE.md) owns component boundaries.

`OncoLabIndex` is the one shared application registry for Director and Researcher within a runtime. It provides bounded deterministic retrieval and loads bundled records from `src/oncolab/proven/verified-executions.yaml` plus resolvable durable verification receipts through factory composition, separately from descriptor status. Loading is idempotent by capability/verification identity and never resumes research. Verification names a declared execution, not the maturity or scientific validity of a statistics family. `describe_oncolab` returns at most 20 verification records and an omitted count. The Pydantic AI harness is only a client through runtime dependencies; it owns no registry. “OncoLab” names this domain index; Pydantic AI capabilities and tools remain framework plumbing under `src/runtime/pydantic_ai/`.

The Index describes data/source capabilities, scientific and statistical methods, transformations, software, visualization, literature/knowledge, and Jev measurements. It uses typed descriptors with purpose, contracts, applicability, limitations, assumptions, missingness semantics, availability, execution/access policy, resource class, validation state, and provenance. It is metadata only: typed wrappers remain the only route to execution.

Index availability is explicit: `known`, `available`, `installed`, `acquirable`, `validated`, `reusable`, `unavailable`, or `forbidden`. It is distinct from validation state: a known or acquirable item is not a validated executable scientific capability. Retrieval is deterministic metadata/text matching and capped at 20 results; neither agent receives the complete catalogue in its prompt.

The initial catalogue contains over 100 descriptors. It includes GDC endpoint, retrieval, pipeline, entity, and workflow-reference metadata plus statistical-method planning families; these entries remain descriptors, not pipelines or arbitrary Python APIs.

Phase 3 makes a deliberately small subset executable through typed Researcher tools: anonymous GDC metadata retrieval (with truthful access metadata in file discovery and explicitly open-only byte acquisition), anonymous UCSC Xena catalogue lookup, public literature metadata retrieval, NumPy/pandas/SciPy/statsmodels measurements, and matplotlib SVG `FigureArtifact` production. Each source wrapper accepts no credentials and enforces the configured response-byte budget. Source records are retained by acquisition ID so Science can deterministically measure the exact stored acquisition. Agent-provided numeric arrays are exploratory measurements and cannot be admitted; only source-bound or replay-validated measurements cross evidence admission.

When no adequate installed method exists, a Researcher may use the `software.github-scientific` capability. It accepts only an HTTPS GitHub repository, resolves an exact commit, and runs installation with the configured credential-free scientific backend; the default is confined Linux x86_64 local-venv execution. Tests and two identical command replays run without network; strict JSON parsing plus replay comparison produces a `SandboxMeasurementCandidate`. Only a separate deterministic validator can turn that candidate into a `MeasuredResult`, followed by ordinary Science admission. The method is not promoted merely because it ran.

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
policy, immutable commit and backend-specific environment identity, exact JSON output, invocation
receipts, content identity and validator version. Validation checks input/environment/
output hashes, commands, successful exits and replay agreement. An explicit backend `replay(candidate)` can independently run the stored request
at its resolved commit/environment; recovery and Index loading never invoke it. Historical Docker installation dependencies remain unlocked. Local execution retains
exact archive and declared wheel bytes/hashes; fresh reusable qualification remains
separate, and identical historical environments are not claimed.

Selected procedural guidance lives in `src/oncolab/labskills/` and is loaded only
for an active Researcher block. It remains separate from the index and from
Pydantic AI's Coder/Code Mode framework capabilities.

Runtime budget and Coder confinement contracts are owned by [architecture](ARCHITECTURE.md#agent-harness) and the strict [runtime configuration](../config/runtime.yaml). Scratch does not promote capabilities or admit evidence.

F4 exposes progressive OncoLab cards and explicit contract expansion, plus local method, representation, hypothesis/test and statement-support measurements. Local semantic contracts are not promoted capabilities. External GitHub acquisition retains inadequacy rationale and alternatives; installed lexical overlap no longer vetoes an unmet need. Existing sandbox, credential and allocation limits apply.

Current source/analysis, replay and retention behavior is described in
[Science](../src/science/README.md), [acquisition](../src/sources/README.md) and
[architecture](ARCHITECTURE.md#persistence-and-application-api).
The bundled Pearson verification proves only its declared three-row fixture;
provided-array statistics and SVG figures remain exploratory.

OncoLab registry revisions retain accepted descriptors and routes separately from
append-only institutional usage, failure, suitability and verification history.
Blocks pin their registry revision, history boundary and application identity;
subsequent observations or accepted changes do not rewrite their contracts.
New allocations see the current accepted basis. Legacy unpinned context remains
unknown. External discovery and reusable qualification acceptance remain in the
[active plan](IMPLEMENTATION_PLAN.md).


External bio.tools search and describe retain public method metadata and bounded
EDAM terms separately from the executable registry. Role tools expose compact
cards; exact responses remain resolvable in persistence. Mutable-source pages
carry query-bound continuations and explicit snapshot limitations. Discovery,
installation, execution, scientific validation and reusable qualification remain
distinct.


Targeted external describe also supports public GitHub repositories and Bioconda
and Bioconductor packages. Repository commits and package build/reference
metadata remain source-bound candidates. Conda and R execution are unsupported;
source listings do not claim otherwise.

Reusable promotion requires one current-application `local-verification-v1` receipt
under `scoped-governance-v2-local`, retaining the direct WSL2 environment identity
and complete Coder, scientific execution and resource-control checks. Missing,
partial, changed-application or unsupported-version proof cannot qualify.
Historical deployment receipts remain readable/exportable but cannot satisfy this
local gate. Scientific scope/reference validation, fresh locked reinstall/replay,
measured utility, repeated admitted use and licence checks remain separate requirements.
