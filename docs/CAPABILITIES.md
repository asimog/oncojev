# OncoLab Index semantics

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
