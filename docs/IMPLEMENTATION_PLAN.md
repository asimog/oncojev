# Implementation Plan

## Task 1 — Bound installed Science and account for resources

Goal: Enforce resource limits on installed scientific computations and report their
actual consumption through the service and BlockDelta.

Scope: Installed Science, parsing and figures currently run through detached thread
work under a heavy-work lease, without a process-family quota. Put expensive work
behind enforceable CPU, memory, process, disk and cancellation controls while keeping
state, charging and persistence with the service owner. Populate observed workspace,
peak workspace and CPU accounting from measurements; retain unknowns where unavailable.
Reuse the existing governor, service-wide budgets and external-execution controls.

Owning code: `src/runtime/pydantic_ai/contracts.py`,
`src/runtime/pydantic_ai/scientific_tools.py`, `src/runtime/resources.py`,
`src/runtime/process.py`, `src/science/execution.py`, `src/dossier/delta.py`,
`src/config/models.py`, `config/runtime.yaml`;
`tests/invariants/test_persistence.py`, `tests/invariants/test_live_mode.py`.

Done when: Real installed computations obey their declared limits; success, failure,
cancellation and shutdown drain work before releasing ownership. Composed receipts
and Delta resolve measured usage, preserve consumed allowances across blocks and
show that busy Director scratch cannot interrupt healthy scientific work.

## Task 2 — Qualify local execution on WSL2

Goal: Produce one complete, current-basis local execution qualification record that
governance can consume.

Scope: Exercise both Coder roles, external scientific preparation/install/test/
execution/replay and installed Science directly on native WSL2 storage. Assemble
`local-verification-v1` from actual observations of filesystem, credential, network,
descendant, resource, download, lease and cancellation controls. Installed Science
must first have enforceable resource limits. Keep exact application, code/worktree,
configuration and environment identities; setup-helper caches are not qualification.
Extend receipt production and consumption together: the current gate checks the
application content identity and declared WSL2/control fields, but does not compare
an exact current environment identity. Bind and check the measured interpreter,
dependencies and effective control configuration so environment drift invalidates proof.

Isolated-testing native assessment: explicitly exercise the frozen testing root,
both role workspaces and local-venv experiment/command-family paths on WSL2 native
storage, including linked-path denial and retention scope. Keep testing receipts
non-qualifying; qualification is produced only for the ordinary `ONCOJEV_TESTING=0`
application identity. Windows local profile contracts are already verified and
do not block code iteration while these kernel observations remain outstanding.

Owning code: `src/runtime/verification.py`, `src/runtime/process.py`,
`src/science/local.py`, `scripts/verify_coder_container.py`,
`scripts/verify_coder_resources.py`, `scripts/verify_local_science.py`,
`scripts/verify_science_resources.py`, `scripts/verify_native.py`,
`src/persistence/records.py`; `tests/invariants/test_persistence.py`.

Done when: A production writer retains one complete record and supporting native
observations on the same basis. Missing controls, stale identity, expansion/disk
failure and unconfirmed cleanup fail honestly; partial or historical records cannot
satisfy the gate, including a changed environment with unchanged application content.
Windows fixtures and provider connectivity are reported separately.

## Task 3 — Extend the neutral evaluation substrate and independent corpus

Goal: Provide reusable, independent measurement of scientific validity and research
decisions beyond the existing generated contract cases.

Scope: Extend the corpus and fresh-condition harness with independently reviewed
labels/reference outputs for representation and method fit, relation distinctions,
failed/inconclusive memory retrieval, duplicate-work avoidance, new-evidence
reopening, literature rediscovery/new-context/contrary reports, acquisition fidelity,
invalid designs, planted signals/nulls and challenge outcomes. Compare deterministic,
Reasoner-assisted, Jev-assisted and full-system conditions on matched inputs and
budgets. Withhold answer-bearing labels/documents; separate tuning and held-out
cases, repeat stochastic measurements and disclose leakage and unavailable costs.
Add source-bound validity, false-positive, alternative-recall, uncertainty-resolution
and verified replication metrics; replication IDs alone are not corroboration.
Produce candidate/scope-bound `utility_evaluation` records for measured reusable
candidates, without admitting benchmark labels as scientific evidence. Own the shared
corpus, labels, held-out splits, condition adapters, comparison harness, metrics and
resource accounting, independently of Jev, Reasoner, memory or search policy.
Generalize the existing fresh-condition harness rather than build another harness;
its current three conditions omit a Jev-only comparison and multi-block memory/search
ablations. Task 11 consumes this substrate for whole-lab evaluation; it does not
recreate corpus, labels, harness, utility records or accounting. Capability-specific
evaluations retain their own scientific scope and completion proof. Reuse suitable cases/results while keeping
ability-level acceptance distinct from complete-lab utility.
Run selection-recall baselines at the configured search/candidate limits through
the actual consumer. Report larger-budget diagnostic runs separately; the existing
200-candidate evaluation override must not stand in for the configured 80-candidate
baseline. Retain the current fixed-query lexical-mismatch case and budget identity
for Task 11's bounded retrieval repair, without claiming scientific utility.

Owning code: `src/evals/`, `evals/`, `scripts/evaluate_selection.py`,
`scripts/evaluate_representation.py`, `src/persistence/records.py`;
`tests/invariants/test_evaluation.py`.

Actual blockers: Current selection labels are embedded contract examples, the
representation corpus lacks broader independent scientific labels, and the
fresh-condition harness has three fixed semantic conditions and mostly operational
counts. It does not yet provide matched multi-block experience/search comparisons
or the candidate-bound utility producer required by reusable governance.
The current 109-item catalogue misses labelled `stat.scipy` for
`co movement linear association` at candidate budget 80; the evaluation override
of 200 retrieves it by exhausting the catalogue and hides the configured-budget miss.

Done when: A bounded, versioned scientific corpus runs through the actual consumers
and fresh conditions, with per-case results, independent label basis, native model/
policy identity, resource accounting, failures and uncertainty. Reports distinguish
contract correctness, scientific utility and connectivity; scoped utility records
resolve their measured candidate and retained comparison. No improvement is a valid
measured result, not a reason to manufacture a winner.
Configured-budget recall failures and separate larger-budget diagnostics are visible
with their query, snapshot, labels and effective limits; passing exhaustive retrieval
does not close a bounded retrieval failure.

## Task 4 — Extend formal investigation search and outcome-linked continuity

Goal: Let formal search compare new mission-grounded proposals with retained work,
and make the effect of scientific outcomes on later selection reference-resolvable.

Scope: Extend the observable portfolio with source-linked blocked, newly testable,
deferred and scientifically resolved transitions. Generate or regenerate candidates
from retained relations, capability changes, new representations, underexplored
mission areas and previously deferred work. Preserve stable identities and both
sides of contradictions, distinguishing population/design differences from actual
conflicts and identifying a test that could discriminate them. Scientific resolution
requires supporting admitted results; allocation completion and semantic agreement
are insufficient. Existing frontier preparation, mission continuity and revalidation
remain the foundation. Free-form Director allocation already accepts new questions;
do not add a second generator/runtime or require a new Director Reasoner. Extend
the existing frontier to accept bounded Director-authored proposals grounded in the
retained mission and inspected capability/source context, even with no prior hypothesis.
Preserve proposal provenance separately from scientific support, stable identities,
scope, omissions, alternatives, budget limits and stale-basis revalidation. Do not
encode a growing list of biological search rules.

Connect retained attempt/follow-up outcomes and unresolved prerequisites to actual
next choices through existing memory retrieval receipts, frontier records and
allocation/review records. Extend those records only where the current lineage is
insufficient; retain which experience informed a choice and which relevant change
made a deferred question actionable. Existing outcome-to-candidate generation and
block-start memory already work; no parallel memory, learned ranker or automatic
scientific resolution is needed. Repair zero-overlap retrieval only against labelled
misses using a bounded alternative in ResearchMemory, measured with Task 3 cases.

Owning code: `src/director/frontier.py`, `src/director/review.py`,
`src/runtime/pydantic_ai/global_tools.py`, `src/memory/models.py`,
`src/memory/service.py`, `src/jev/questions.py`, `src/persistence/records.py`,
`src/runtime/pydantic_ai/contracts.py`, `src/runtime/pydantic_ai/search_tools.py`;
`tests/invariants/test_persistence.py`, `tests/invariants/test_boundaries.py`.

Actual blockers: The formal generator consumes only retrieved digest items, and
ResearchMemory excludes zero-lexical-overlap items before Jev can compare them.
Free-form allocation need not name a frontier; retained retrieval and follow-up
lineage alone does not establish that an autonomous next choice used it.

Done when: Real tools compare a new mission-grounded question with no prior hypothesis
and retain its provenance without admitting it as evidence. They recover a
deferred/blocked investigation after a relevant basis change, retain distinct tests
and independent replication, and reconstruct
lifecycle/relation lineage after reopen. Independent cases assess resolvable conflict,
useful next-test selection and missed alternatives; unknown resolution stays unknown.
Source-bound failed, inconclusive and contrary outcomes lead to observable later
choices after reopen, with no experience fabricated from execution errors. Task 11
measures marginal benefit using matched memory/search conditions; this task proves
the mechanism and lineage, without claiming learned scientific utility.

## Task 5 — Generate usable representation alternatives

Goal: Generate source-backed input alternatives beyond the existing owned-input gate
and single-file STAR gene parser.

Scope: For concrete scientific needs, discover bounded alternatives across available
mutation, CNV, expression, clinical and survival assets. Describe actual schemas,
entity units, identifiers/builds, normalization, sample/case relationships, coverage
and missingness. Add only needed parsers, sample/cohort matrices, joins or transforms
with validated keys/cardinality and explicit information loss. Mark alternatives as
directly available, derivable by a supported operation, inaccessible or unmeasured.
When labelled cases expose available-but-missed inputs, repair the responsible
retrieval/grouping/schema mapping and measure recovery, including low lexical overlap.

Owning code: `src/sources/representation.py`, `src/sources/public.py`,
`src/science/representation.py`, `src/runtime/pydantic_ai/search_tools.py`,
`src/runtime/pydantic_ai/scientific_tools.py`, `src/oncolab/methods.py`,
`src/evals/representation.py`; `tests/invariants/test_boundaries.py`,
`tests/invariants/test_persistence.py`.

Done when: The Researcher generates actual owned/retrievable alternatives for the
selected needs, with exact source and transform lineage. Independent comparisons
show useful retention and honest omissions; incompatible units, incomplete pairing,
unsupported derivation and metadata masquerading as assay data cannot pass readiness.

## Task 6 — Bind scientific operations to canonical references

Goal: Turn discovered software into a scoped operation with independently established
behavior and scientific applicability.

Scope: Inspect the smallest relevant pinned implementation, callable/CLI, documentation
and canonical examples for a concrete capability gap. Inspect targeted Galaxy,
nf-core or Bioconda invocation/fixture material when relevant. Retain exact inputs,
preprocessing, parameters/defaults, units, assumptions, licence/source binding and
expected outputs. Build the missing reference-validation producer: compare controlled
execution with independently obtained upstream results on canonical, changed-input/
parameter and invalid-input cases, using predeclared tolerances and scope diagnostics.
Unavailable runnable references leave qualification unsupported.

Owning code: `src/oncolab/enrichment.py`, `src/oncolab/discovery.py`,
`src/science/local.py`, `src/science/sandbox.py`, `src/science/models.py`,
`src/runtime/pydantic_ai/scientific_tools.py`, `src/persistence/records.py`;
`tests/invariants/test_boundaries.py`, `tests/invariants/test_persistence.py`.

Done when: A real candidate has a durable, candidate/scope-bound `reference_validation`
record resolving its reference material and comparisons, with adverse-case failures
retained. Wrapper-derived expectations, ignored parameters and faithfully reproduced
but scientifically unsuitable behavior cannot qualify. Replay alone is insufficient.

## Task 7 — Qualify recoverable dependency environments

Goal: Establish recoverable fresh installation and independent replay for reusable
scientific operations.

Scope: Trigger this work when a method is selected for reusable promotion or measured
repeatability/dependency drift requires it. Retain a supported lockfile or resolved
transitive package set, exact recoverable bytes/hashes, platform/Python constraints
and installer/runtime identity. Use existing packaging tools and isolated experiment
environments. Build the environment-qualification producer and exercise drift,
conflicting pins, unavailable packages and corruption; a freeze hash alone is not a lock.

Owning code: `src/science/local.py`, `src/science/sandbox.py`,
`src/science/models.py`, `src/oncolab/governance.py`, `src/persistence/records.py`;
`tests/invariants/test_boundaries.py`, `tests/invariants/test_persistence.py`.

Done when: A triggered candidate reinstalls independently and replays exact owned
inputs/parameters with matching declared environment/output identity. Durable
`environment_qualification` records bind candidate and scope to the actual proof.
Failed recovery blocks reusable status while retaining truthful exploratory results.

## Task 8 — Add justified oncology operations

Goal: Add a bounded set of scientific tools that answer demonstrated research needs
with defensible inputs and comparisons.

Scope: Trigger selection from a recorded uncertainty/capability gap and accessible
eligible representations. Before implementation, freeze a finite list of named tools
and supported operations in this feature spec, with the originating need, exact
inputs, expected outputs, upstream implementation and build/no-build reason for each.
Only those tool contracts and their required parsers/transforms are in scope; do not
assess or implement whole oncology operation families. Candidate operations may cover
mutation/annotation/burden/TMB, expression/signature/pathway, CNV association,
co-mutation/subtype/clinical, survival, aligned cross-cohort/multi-omic or prioritization
needs. Freeze estimand, design, participants, denominators, transformations,
covariates, missingness, multiplicity, diagnostics and interpretation before inspecting
results. TMB needs callable territory; survival needs time/event/censoring definitions;
aligned assays need audited joins; multi-omic tools need comparison with a simpler
aligned analysis. Select supported implementations and independent canonical baselines;
evaluate need and scientific benefit before adding a wrapper. Carry each tool's
outcomes into existing attempt, memory and literature-context
consumers where applicable.

Owning code: `src/science/`, `src/sources/`, `src/oncolab/catalogue.py`,
`src/oncolab/execution.py`, `src/runtime/pydantic_ai/scientific_tools.py`,
`src/runtime/pydantic_ai/context_tools.py`, `src/memory/`, `src/evals/`;
`tests/invariants/test_boundaries.py`, `tests/invariants/test_persistence.py`.

Done when: Every named tool in the frozen selection has its scoped build/no-build
result. Each built tool has a declared route/input/output contract, controlled
execution, replay, validator/admission and independently reviewed valid/invalid/null/
changed-input proof. A no-build result identifies the unavailable prerequisite or
adequate existing tool. Completion covers only the frozen selection and demonstrated
scientific scope; it does not establish whole-family validity.

## Task 9 — Extend scientific challenges and follow-up

Goal: Challenge findings using independent cohorts, alternative methods/representations
and discriminating controls beyond same-method paired follow-ups.

Scope: For a selected source-bound finding, declare the follow-up before observing
confirmation results, including expected discrimination, effect/uncertainty comparison,
multiplicity and failure criteria. Extend the supported challenge operations only as
needed. Audit cohort/participant overlap, endpoint compatibility and preprocessing/
training leakage; same-participant robustness is distinct from independent replication.
Retain failed, contradictory, sensitivity-dependent and inconclusive outcomes with
originals, alternative explanations and unresolved prerequisites in memory and context.

Owning code: `src/science/followup.py`, `src/runtime/pydantic_ai/followup_tools.py`,
`src/runtime/pydantic_ai/context_tools.py`, `src/science/execution.py`,
`src/memory/service.py`, `src/evals/`; `tests/invariants/test_persistence.py`,
`tests/invariants/test_boundaries.py`.

Done when: Independently reviewed real-data challenge cases execute through the
selected operation and affect the next investigation using retained source references.
Overlap, reversed/confounded effects, low information and unavailable prerequisites
receive defensible interpretations; replay and non-significance cannot certify
replication or absence. New challenge operations have their own validated contracts.

## Task 10 — Deliver qualified reusable methods

Goal: Execute an accepted scoped reusable method in a subsequent fresh Researcher
block through the governed registry path.

Scope: Implement the missing `run_reusable_method` dispatcher over supported declarative
operations, resolving pinned route, candidate, software, owned inputs and qualified
scope. Exercise proposal/review/acceptance with actual repeated admitted use across
distinct inputs and blocks, independent reference/scientific validation, recoverable
fresh-environment replay, measured utility, licence binding and complete current local
qualification. Those proof producers and a supported operation are genuine prerequisites;
hand-authored passing booleans cannot replace them. Connect demand/use to promotion
and qualify changed-scope updates, reverification and retirement. Code-requiring
changes continue through reviewed engineering proposals.

Owning code: `src/oncolab/governance.py`, `src/oncolab/execution.py`,
`src/oncolab/institution.py`, `src/runtime/pydantic_ai/contracts.py`,
`src/runtime/pydantic_ai/factory.py`, `src/runtime/pydantic_ai/discovery_tools.py`,
`src/science/admission.py`; `tests/invariants/test_persistence.py`.

Done when: A qualified candidate is accepted into a reconstructible revision and
actually discovered/executed by the next fresh block without restart. Active and
historical pins remain reproducible. Missing/stale/changed-scope proof rejects;
rejection and reverification remain history-only; governed updates and retirement
change only their scoped contracts. The real admission path remains authoritative.

## Task 11 — Evaluate whole-lab search, experience use and semantic composition

Goal: Evaluate the complete lab's investigation selection, scientific continuation
and semantic decisions, adopting refinements only where measured failures justify them.

Scope: Consume Task 3's neutral corpus, held-out methodology, condition adapters,
metrics, utility-record producer and accounting. Own multi-block experiments and
their scientific interpretation, not another evaluation substrate. Compare the
current composed lab with matched memory-present/withheld, retained-only/open-proposal
search and suitable capability/representation/method/tool conditions; account for
unavailable paths instead of simulating scientific success. Trace whether prior
experience, OncoLab, representations, methods, scientific tools, Jev and search
alternatives actually affect useful choices and source-bound outcomes.
Compare bounded offline reflection,
proximity/diversity and branch/analysis/debug-budget variants on matched needs, inputs
and budgets. Follow actual Director allocation/review, Researcher tool choices,
retained measurements, memory and subsequent selections across blocks. Evaluate
scientific coverage/concentration and whether review leads to a useful next test or
an actionable capability/engineering proposal. The current program review counts
declared entity/topic tags and leaves scientific value unknown; those observations
alone are not measured scientific coverage or decision utility.

Replay independently labelled paraphrase, alternative-test, population/design,
replication and blocked-to-actionable cases through actual consumers. Repair
normalization/alignment/retention failures only when demonstrated, including retrieval
that drops useful zero-overlap memory before semantic comparison. Measure repeated
fixed-input semantic instability before spending an explicit extra allowance on
calibration, self-consistency or a bounded Autoresearch-style variant loop. Preserve
native distributions, alternatives, failure fallback and separate local/global
policies; adoption uses reviewed engineering. Use capability-specific results as
scoped inputs, without treating their separate successes as complete-lab benefit.

Keep current-catalogue retrieval repair active independently of scale infrastructure.
Use Task 3's configured-budget baseline to repair demonstrated OncoLab misses in
the canonical registry/discovery path and its agent consumer. Start with the retained
lexical-mismatch case; compare the smallest bounded deterministic retrieval or
query-expansion change before broader mechanisms. Measure useful recall and resource
cost at unchanged budgets, preserving stable query/snapshot identity and continuation
correctness. Additional queries, semantic calls and returned candidates consume the
existing allowances. Broader held-out cases must expose regressions and limits;
this repair establishes candidate coverage, not complete-lab scientific benefit.

Keep Jev semantic design separate from the evaluation machinery. For demonstrated
failures, compare existing batched Noul dimensions with a scoped Choice relation or
alignment classification (including unknown) and, where ordered graded relevance is
useful, descriptive Score levels plus independent Noul checks. Include meaningful
distinction, contradiction versus scope difference, replication, alternative
explanations, uncertainty linkage, coherence and representation/method fit only as
needed by actual consumers. Retain native distributions and versioned Python
interpretation; prune unused questions rather than increasing calls by default.

Before a measured context/output/runtime failure leads to custom generic machinery,
compare the installed Pydantic AI/Harness capability and owner-preserving adapter.
Coder, Code Mode, capability hooks, SDK usage limits and telemetry already exist.
Linux Coder already retains ClearToolResults, WarnNearLimits, output truncation and
RepairToolArguments because the owned adapter replaces only Shell; Windows uses
Code Mode without this Coder composition. Record the platform-specific baseline and
evaluate those existing controls before changing them. Additional summarizing
compaction or reminder mechanisms require retained problematic trajectories and a
measured benefit, charging costs and preserving resolvable scientific context.
Do not replace ResearchMemory, BlockSkillStore, OncoLab, admission, cross-role budgets,
terminal drain or native confinement with framework memory, Skills or safety defaults.
No standalone runtime-migration task is justified without a demonstrated blocker.

Owning code: `src/autonomous.py`, `src/director/frontier.py`,
`src/director/review.py`, `src/jev/frontier.py`, `src/jev/questions.py`,
`src/runtime/pydantic_ai/global_tools.py`, `src/runtime/pydantic_ai/semantic.py`,
`src/runtime/pydantic_ai/search_tools.py`, `src/runtime/pydantic_ai/agents.py`,
`src/runtime/pydantic_ai/controls.py`, `src/runtime/pydantic_ai/workspace.py`,
`src/memory/service.py`, `src/oncolab/registry.py`, `src/oncolab/discovery.py`,
`src/oncolab/enrichment.py`, `src/evals/`;
`tests/invariants/test_persistence.py`, `tests/invariants/test_boundaries.py`,
`tests/invariants/test_evaluation.py`.

Actual blockers: Current program review leaves scientific value unknown and
reports declared tag concentration. Existing fixtures do not measure autonomous
experience-to-choice benefit. Task 3 supplies independent held-out cases and
comparison adapters; Task 4 supplies the formal open-proposal path and choice
lineage for those comparisons. No semantic or framework refinement is required
until its failure/benefit trigger is measured.
Current-catalogue candidate coverage already has a labelled configured-budget miss;
its bounded repair must not wait for a growing-scale failure or a larger-budget pass.

Done when: Repeated matched-budget held-out comparisons through the composed lab
support scoped versioned changes or measured no-change, with false merges, useful
recall, next-test alignment, coverage/concentration, instability, scientific outcomes
and resources reported. Retain the case basis and actual review-to-next-selection
lineage; report unavailable capabilities and unmeasured utility explicitly.
Extra variants run only when their measured trigger and allowance hold. Conditional
dispositions state covered limits; no automatic live question/policy rewrite or
semantic termination of the research program is introduced.
The current labelled OncoLab miss is recovered at configured limits through the
actual consumer, with held-out recall, continuation and resource regressions checked
and retained. A measured remaining limit stays explicit rather than being hidden by
increasing the evaluation budget.

## Task 12 — Verify a composed oncology research trajectory

Goal: Establish one exact-basis scientific and operational trajectory through the
real service rather than infer composition from separate slice checks.

Scope: Use an eligible computational-cancer question and exact retained source,
software, registry/history and application identities. Trace need, representation
alternatives, method choice, controlled validated analysis, challenge or explicit
unavailable prerequisite, literature context, memory-driven next selection and
export. Include a misleading/invalid alternative and contradiction or inconclusive
outcome. Exercise bounded independent Director work/event wait, early completion,
post-block revalidation, another allocation, shutdown and reconstruction. Include
qualified reuse once its missing path is available. Add isolated publication only
when its conditional-extension trigger is met; report publication as unavailable
otherwise, without blocking the core trajectory or claiming remote delivery.
If required original history is unavailable locally, first establish the exact
missing record/input identity and provenance through read-only inspection; recovery
must preserve original stores without assuming remote completeness or merging data.

Isolated-profile live assessment: retain provider-backed elapsed `run_once` and
post-block-review phases separately, a consecutive-cycle `serve` trajectory and
unchanged scientific preparation/install/test/execution/replay. Report the 120 s
target as observation only, including overruns and exhausted data ceilings. Use an
explicit longer scenario for the unchanged 300 s scheduled Director review. Scripted
Windows profile checks establish contracts, not live timing or scientific benefit;
these trajectories remain separate from routine implementation checks.

Owning code: `src/autonomous.py`, `src/runtime/cycle.py`,
`src/runtime/pydantic_ai/`, `src/persistence/`, `src/dossier/delta.py`,
`src/memory/`, `src/application/`; `tests/invariants/test_persistence.py`,
`tests/invariants/test_live_mode.py`.

Done when: A retained execution resolves the entire trajectory and demonstrates
that scientific outcomes/limitations determine continuation on the pinned basis.
Exactly-once closure, honest interruption, unchanged future defaults after one fast
block and refreshed next-block pins compose correctly. Local contracts, live source/
model connectivity, scientific utility, WSL2 qualification and remote publication
have separate supported conclusions; absent required external proof stays explicit.
Correct the stale Delta pin limitation only where composed behavior establishes it.

## Conditional extensions

These retained feature specs become active only when their stated trigger is met.
They are not prerequisites for the core research-loop work. Active tasks are numbered
consecutively; the reconciled ADR retains the original numbering for traceability.

### Automatic isolated notebook publication

Trigger: Activate only when automatic external publication is explicitly needed
for a selected research deliverable. Approved remote/credential setup, connectivity
and remote SHA verification are work and completion requirements after activation,
not prerequisites for activating the spec. Retained exports remain usable beforehand.
This is a scheduling decision; the missing event-to-publisher handoff remains an
unfinished capability, not a completed or disproven requirement.

Goal: Connect retained export events to the existing separate publisher and establish
actual publication to `asimog/oncojevlab`.

Scope: Add an event-consumption/handoff path in a separate credential-owning process
for completed blocks, material frontier/contradiction changes, mission changes,
capability proposals/reviews/revisions, program reviews and engineering proposals.
Publish the pinned export identity, deduplicate/no-op unchanged content and reuse the
existing bounded retries and dirty-checkout safeguards. Service event hooks currently
retain identities only. Configure the approved remote/credentials outside agent and
scientific environments; missing connectivity is an explicit publication blocker.

Owning code: `src/application/export.py`, `src/application/publication.py`,
`scripts/export_notebook.py`, `src/autonomous.py`,
`src/runtime/pydantic_ai/contracts.py`, `src/persistence/records.py`;
`tests/invariants/test_persistence.py`.

Done when: Defined events reach the isolated publisher, survive restart/deduplication
and produce a remotely verified commit SHA for the exact generated snapshot. Failed
publication and exhausted retries retain durable outcomes without changing scientific
closure/evidence or overwriting external edits. Local Git simulations and live remote
proof remain distinguishable.

### Catalogue scaling

Trigger: Activate only on measured growing-catalogue recall, latency, context or
continuation failures. Task 3 owns configured-budget measurement and Task 11 owns
current-catalogue OncoLab retrieval repair; Task 5 owns representation/input misses.
A scale platform is not their prerequisite. Task 3/11 measurements can activate
this extension; the benchmark below is not the only way to establish its trigger.

Goal: Resolve measured catalogue-scale or vocabulary recall problems with the smallest
compatible retrieval change.

Scope: Benchmark growing curated snapshots and on-demand external candidates for
useful recall, coverage, latency, context size and continuation correctness. Trigger
implementation only on demonstrated misses or unacceptable resource use. Compare a
deterministic retrieval alternative first, then bounded vocabulary/EDAM expansion,
then embeddings only for residual useful-candidate misses. Retain selected-source,
licence, snapshot and algorithm identity and bounded ingestion. Migration-based FTS,
additional databases and uncontrolled harvesting are outside the existing storage scope.

Owning code: `src/oncolab/registry.py`, `src/oncolab/discovery.py`,
`src/oncolab/enrichment.py`, `src/evals/selection.py`,
`scripts/evaluate_selection.py`; `tests/invariants/test_evaluation.py`,
`tests/invariants/test_boundaries.py`.

Done when: Growing-scale comparisons establish the applicable staged decisions,
including compatibility limits or measured no-change. Any adopted extension improves
the declared recall/latency objective while preserving query/snapshot identity,
stable ordering, bounded resources and continuations. Small-catalogue success alone
cannot close the growing-scale assessment.

### Shared candidate-generation mechanics

Trigger: Activate only after the representation generator exists and multiple
production generators demonstrate the same useful mechanical contract or costly
duplication. No common abstraction is required to deliver Tasks 4 or 5.

Goal: Determine whether common retrieval/composition mechanics improve multiple real
domain generators without erasing their scientific meaning.

Scope: Compare delivered global and method generators with a real representation
alternative generator once that missing domain path exists. Specify each generator's
inputs, identity, source references, prerequisites, omissions and consumer; measure
multi-domain useful recall, duplicates, context, latency and resources. Extract the
smallest production-used interface/dispatcher only when the comparison demonstrates
a useful shared contract and improved recall. Preserve global/local authority,
scientific eligibility and domain-specific policies.

Owning code: `src/director/frontier.py`, `src/oncolab/methods.py`,
`src/runtime/pydantic_ai/global_tools.py`, `src/runtime/pydantic_ai/search_tools.py`,
`src/evals/`; `tests/invariants/test_boundaries.py`,
`tests/invariants/test_evaluation.py`.

Done when: The paired multi-domain comparison supports adoption or a measured
rejection. An adopted contract is used by actual domain consumers with retained
identity/provenance and useful-alternative recall. Similar-looking models or the
existing representation assessor/parser alone do not establish the trigger.
