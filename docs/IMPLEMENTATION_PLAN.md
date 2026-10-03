# Implementation Plan

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
it now includes Jev-only comparison and matched multi-block memory/search
ablations; extend their independently reviewed scientific scope. Task 11 consumes this substrate for whole-lab evaluation; it does not
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

Current implementation/proof (2026-10-02): the existing fresh-condition owner now
has all four conditions, published Anscombe reference outputs, twelve independently
expert-annotated lung/pulmonary SciFact claim-document pairs, and separately labelled
generated adverse/memory/relation contracts. Offline comparison retains 192 rows,
native semantic receipts, measured usage and explicit unavailable costs. A one-case
live assessment completed 24 comparisons, with twelve Jev-enabled annotation matches;
the full twelve-case, three-repeat live assessment finished 144 observations: 71/72
Jev-enabled annotation matches and one operational failure; the other 72 observations
have no support classifier. Task 11 retained 192 matched offline and 24 held-out live
composition comparisons. Reviewed SciPy metadata repair recovered fixed and held-out
linear-query recall from zero to one at configured 80/8 limits. Larger-budget
diagnostics remain separate. Reports are retained under `var/task3-proof/`.

Retained blockers: independent scientific review for broader representation,
relation/next-test/challenge labels remains pending, as requested. Published SciFact
annotations close only claim-document support labels. Broader independently reviewed multi-block scientific comparisons
and actual candidate-bound measured utility remain outstanding; a producer now
retains candidate/scope/comparison identity and rejects unsupported qualification.
The original configured-budget lexical miss and its exhaustive 200-candidate
diagnostic remain retained; bounded metadata repair is supported by Task 11 receipts,
not by exhaustive retrieval.

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

Current implementation/proof (2026-10-02): formal frontier tools accept bounded
Director-authored mission/context-grounded proposals without prior hypotheses;
allocation retains the selected experience and basis. Portfolio history reconstructs
blocked/deferred-to-newly-testable changes through exact prerequisites. Bounded
zero-overlap scientific-context retrieval exposes route/omission receipts. Focused
five-check tool/lineage assessment passed; broader independent scientific next-test
labels remain pending. The empty failed-cycle harness fallback now retains adapter
errors correctly. The 24 held-out live composition comparisons finished without
semantic, adapter or SDK snippet failures; scripted choices establish lineage only.

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

Continuation feature specification (2026-10-02): close the demonstrated gzip/
row-count parser gap for actual retained open lung MAFs without increasing download,
process or decompressed-byte ceilings. Extend the existing `parse_gdc_table` owner
with explicitly declared gzip (matching source filename), bounded 8 MiB decoded
UTF-8, whole-file validation, at most 100000 source rows and an optional predeclared
1–20 exact gene-symbol panel. Retain at most 100 selected mutation events, reject
oversized selection, and disclose excluded source rows and absent selected genes.
Unselected or absent events do not imply mutation-free samples or TMB. Preserve
old transform identities; the extended path gets a v2 receipt and source checks.
Use existing installed workers, typed tool, owned acquisition/persistence and source
candidate flow. Prove corrupt/truncated/oversized gzip rejection, malformed excluded
rows, incompatible builds/duplicate events and selected-vs-source coverage, then
run an explicit ordinary real lung file acquisition/transform/readiness assessment.
Independent clinical usefulness review remains pending as requested.

Current implementation/proof (2026-10-02): owned schema/modality alternatives,
fixed open MAF/CNV parsing, case clinical/survival derivation, selected-gene cohort
assembly and unique case joins are installed with source/transform receipts and
registered application routes. Native transforms passed under real process controls.
Native compressed lung MAF qualification now validates the entire bounded table before exact gene-panel selection: 43 source events, one selected KRAS event, 18,509 compressed and 84,970 decoded bytes. Retained proof: `var/task5-proof/lung-maf-panel.json`; the initial annotation-width rejection remains retained. The existing owner accepts declared gzip with an 8 MiB decoded ceiling, at most 100,000 inspected rows and 100 selected events; missing panel genes are never mutation absence. Larger inputs beyond these bounds and independent clinical usefulness remain unqualified. Endpoint/coverage/censoring validity is not
inferred. Independent broader scientific usefulness review remains pending.

Done when: The Researcher generates actual owned/retrievable alternatives for the
selected needs, with exact source and transform lineage. Independent comparisons
show useful retention and honest omissions; incompatible units, incomplete pairing,
unsupported derivation and metadata masquerading as assay data cannot pass readiness.

Tasks 3–5 blocker assessment after the representation implementation (2026-10-02):
Published SciFact labels supply independent lung/pulmonary claim-document support;
broader scientific label review remains explicitly retained. The real GDC lung slice
retains 100/1089 cases in 25,618 bytes; 95 age observations and 72 time/event rows
are usable, with five missing ages and 28 missing time/event pairs. This establishes
bounded acquisition/transform utility for the inspected slice, not population or
survival validity. Owned proof is in `var/task5-proof/`. Declared compressed MAF
within the documented limits now has real lung-file proof. Larger tables beyond
those limits and independently reviewed challenge/representation decisions remain
unqualified. The same bounded table parser accepts source-declared gzip CNV with
the CNV schema, but no retained public compressed-CNV native run establishes its
practical or scientific usefulness. Actual scoped utility qualification depends on Task 6/7's candidate
proof; carry these limitations forward without manufacturing review or admission.

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

Feature specification before implementation (2026-10-02): extend one supported
challenge, `method_robustness`, from Pearson association to simple OLS with both
complete-pair variables explicitly standardized using sample SD. Both point effects
have the standardized bivariate association scale; OLS t and Fisher intervals retain
their own conditional assumptions and are not interchangeable evidence. Reject raw
slope/correlation comparison, changed variables/participants/estimands, undeclared
preprocessing, relaxed families and constant/insufficient inputs. Keep same-case
robustness distinct from independent replication; all original freshness, overlap,
coverage and leakage limits remain. Declare the challenge before its target result.

Use the independently published Anscombe vectors for numerical reference behavior
and invalid/changed contracts. Execute a real GDC lung age/death-duration exploratory
slice as a scoped data/method check, with source omissions and endpoint limitations;
if the baseline is unsupported, report inconclusive rather than invent a finding.
Retain attempts, original/target references, model-specific uncertainty and memory
context leading to a new prerequisite/next-test proposal. Broader independent expert
review of clinical challenge interpretations remains pending, as already authorized;
these reference checks cannot certify clinical validity, absence or replication.

Owning code: `src/science/followup.py`, `src/runtime/pydantic_ai/followup_tools.py`,
`src/runtime/pydantic_ai/context_tools.py`, `src/science/execution.py`,
`src/memory/service.py`, `src/evals/`; `tests/invariants/test_persistence.py`,
`tests/invariants/test_boundaries.py`.

Current implementation/proof (2026-10-02): a fixed same-input `method_robustness`
contract compares Pearson with complete-pair standardized OLS. Published Anscombe
points agree; raw-slope comparisons, changed data/participants and insufficient or
constant inputs reject. Real GDC lung data supplied 41 complete age/death-duration
pairs; both point effects were -0.348283236572435 (rounded), with baseline and
follow-up inconclusive. Exact source/attempt/plan/measurement/follow-up refs and
conditional intervals are retained under `var/task9-proof/` and ordinary history.
After reopening, actual scripted Director SDK/tools selected an endpoint/selection
prerequisite assessment using the retained follow-up reference (seq 169 → allocation
seq 191). No clinical evidence was admitted and no replication/absence was inferred.
Focused combined checks passed 19 in 11.93 s; source/flow selection passed 5 in
6.66 s. Broader independent real-data clinical challenge labels remain pending;
mechanism/lineage proof does not close that scientific-review requirement.

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

Feature specification before implementation (2026-10-02): dispatch only the
reference-qualified fixed finite-mean operation through an immutable block-pinned
`run_reusable_method` route. Resolve route candidate, exact scope hash, licence,
current local qualification and independently resolvable reference/environment/
utility proof; retain acquisition/field extraction, complete finite rows, exclusions,
units and unique case keys. Reuse the existing pipeline, validator, state/measurement
persistence and explicit admission. Reject changed parameters, unknown/synthetic
source inputs, missing proof and stale/current-basis mismatch before execution.
Source vectors must come from owned acquisitions, never benchmark labels.

Exercise real distinct-input/block source use and governance decisions. Reference
and environment proof exist for the narrow operation; reviewed scientific utility
remains unsupported until its independent comparison basis is sufficient. Preserve
that gap, reject promotion truthfully and still verify dispatcher rejection, pins,
proposal/review history and engineering/retirement boundaries. Do not fabricate
passing utility or accepted native promotion to satisfy the done criterion.

Owning code: `src/oncolab/governance.py`, `src/oncolab/execution.py`,
`src/oncolab/institution.py`, `src/runtime/pydantic_ai/contracts.py`,
`src/runtime/pydantic_ai/factory.py`, `src/runtime/pydantic_ai/discovery_tools.py`,
`src/science/admission.py`; `tests/invariants/test_persistence.py`.

Current implementation/proof (2026-10-02): the fixed mean dispatcher and strict
reference/environment/utility proof consumers are implemented. Missing/stale proof,
undeclared units, synthetic or missing/duplicate source rows and changed parameters
reject before execution. Two actual fresh GDC source blocks retained LUAD/LUSC age
means (18/19 complete rows), validated pipeline replay and explicit admission, with
owned source/vector identities and missingness limitations. Promotion review was
truthfully rejected; `var/task10-proof/reusable-mean.json` retains source use and the
review. Independent scientific utility remains unsupported. Historical ordinary proof (seq 1158) resolves its archived source/environment;
pinned licence binding resolves the exact inspected source/commit. On that basis,
review `ce7f42ed-87cc-449c-94d0-a0492bbf22b3` rejected only unsupported utility
(`var/task10-proof/review-current.json`). Audit changes invalidate the old current-basis
claim; post-commit native proof and promotion re-review resolve through
var/production-audit/final-verification.json. The refreshed review still rejects
only unsupported utility; no accepted scientific qualification is inferred. Acceptance, subsequent accepted-route native
execution, qualified updates and retirement cannot be claimed without utility review.

Done when: A qualified candidate is accepted into a reconstructible revision and
actually discovered/executed by the next fresh block without restart. Active and
historical pins remain reproducible. Missing/stale/changed-scope proof rejects;
rejection and reverification remain history-only; governed updates and retirement
change only their scoped contracts. The real admission path remains authoritative.

## Task 11 — Evaluate whole-lab search, experience use and semantic composition

Goal: Evaluate the complete lab's investigation selection, scientific continuation
and semantic decisions, adopting refinements only where measured failures justify them.

Assigned semantic-search reconciliation slice (2026-10-03): retain proposals before
semantic narrowing, repair demonstrated omission/direct-hypothesis memory gaps,
and expose append-only challenge/reopen/revision/supersession lineage without a
new owner. Extend the existing reference/fresh-condition substrate with matched
five-domain recall/preservation/fit/relation/next-choice metrics, native probability
and categorical instability, observed costs and explicit unknowns. Completion proof
for this engineering slice is behavioral regressions, paired observations and one
source-owned outcome-to-formal-frontier-to-next-choice trajectory. Independent
scientific labels and autonomous utility are separate retained qualification work.

Verified slice outcome: five generated tuning cases ran 60 live comparisons across
four conditions/three repeats; three relation contracts ran 18 live comparisons.
All conditions retained useful candidates; Jev improved first-choice context ordering
only in the generated low-overlap case. Joint hypothesis alignment and contradiction
classification retained unknowns. Native probabilities varied; observed search choices
and fit signatures stayed stable. No independent five-domain scientific labels were
fabricated. Three final owned-launch source paths each completed two Researcher runs,
dossiers and Deltas: 41/100 complete source pairs yielded a model-conditional
inconclusive Pearson effect-bound result, followed by a different duration-coverage/
endpoint-prerequisite question selected through actual formal frontier IDs. Reopening
119 retained envelopes reconstructed both completed blocks and validated memory.
The five new cases are tuning-only; the 696-row offline report is contract/fixture
measurement, not empirical utility. Matched candidates keep Reasoner proposals out
of candidate-set changes, so autonomous Reasoner-generation benefit is unmeasured.
Detailed observed results and original trajectory records are retained under
evals/reference/results/semantic-search-assessment-20261003.* and
semantic-search-trajectory-20261003.json; raw observations remain under
var/semantic-search-proof/. Engineering decision: ADOPT WITH LIMITATIONS.

Retained qualification limits for this slice: independent representation/method/
relation/next-investigation scientific labels, genuine autonomous choice utility,
fresh acquisition, endpoint validity and independent replication. Scripted choices,
source replay/prior exposure and unchanged ordinary data/science controls are explicit;
no final-committed-basis whole-environment or reusable promotion qualification is
claimed. These gaps keep Task 11 active; they do not justify another search framework.

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

Implemented retrieval/composition scope (2026-10-02): canonical SciPy purpose/tags
were repaired against existing Pearson/Welch routes with reviewed migration and
old-pin preservation. Configured 80/8 fixed/held-out retrieval, continuation and
changed-snapshot rejection were measured. The existing Task 3 adapter now retains
controlled multi-block SDK work, typed memory, review/frontier/allocation and fresh
Researcher choices crossed with memory/search variants. Scripted choices establish
composition; clinical/autonomous choice utility remains unmeasured. No answer labels
enter adapter prompts and no reference/synthetic result becomes scientific evidence.

Current implementation/proof (2026-10-02): the earlier Task 11 slice passed 284 invariants
in 89.81 s, architecture/whitespace checks, and six native probes per profile. The
dated report is `evals/reference/results/lung-lab-assessment-20261002.md` with its
JSON/raw retained comparisons. Unchanged-budget retained-registry recall
improved 0 to 1 for the original lexical case and a held-out linear query; tested
literature, summary, missing-input and Welch retrieval were unchanged, survival
execution remains unavailable. Native current-registry migration changes only
purpose/tags; routes and old pins remain identical and changed cursors reject.
Four numerical references across four conditions, memory variants, two search modes
and three repetitions produced 192/192 numerical agreements. Actual SDK review-to-
next-selection and source references are retained per row, with all scientific value
unknown. Live held-out semantic composition returned 24/24 numerical agreements across
four conditions, memory variants and three repetitions; 156 retained native semantic
receipts remain operational observations, with no independently labelled clinical
choice utility. Retained-only memory-withheld variants allocate no next block, while
memory-present variants retain referenced continuations; open proposals allocate in
both variants. All compared SDK tool snippets returned without runtime errors. Tool failures and
partial adapter errors remain explicit; an earlier incomplete cycle no longer masks
the actual adapter exception. Scientific coverage, false merges, clinical next-test
alignment and autonomous decision utility remain unmeasured, and independent broader
clinical review remains pending. No measured instability/context failure justifies a
new calibration/reflection/SDK replacement mechanism. Conditional variants remain
conditional, rather than being declared qualified by fixture agreement.

Actual blockers: Current program review leaves scientific value unknown and
reports declared tag concentration. Existing fixtures do not measure autonomous
experience-to-choice benefit. Task 3 supplies independent held-out cases and
comparison adapters; Task 4 supplies the formal open-proposal path and choice
lineage for those comparisons. No semantic or framework refinement is required
until its failure/benefit trigger is measured.
The retained labelled catalogue miss was repaired at configured 80/8 limits with
fixed and held-out recall proof. Its original miss and larger-budget diagnostic
remain preserved; broader autonomous scientific-choice coverage stays unmeasured.

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

Completed source metadata correction: the actual anonymous acquire_gdc wrapper
and selected-open-file retrieval are reflected in canonical limitations and an
explicit reviewed metadata-only migration. Actual SDK validation accepts only the
four supported endpoints and rejects unsupported guesses before transport. Owning
catalogue, institution and contracts code preserve routes, authority and immutable
old pins; migration no-op and invalid/valid-call checks passed. Retained migration:
var/task11-proof/gdc-metadata-correction.json. Historical ordinary native proof
seq 1158 remains archived; current qualification resolves through
var/production-audit/final-verification.json and its exact source archive. Source-
owned Welch and clinical utility remain unavailable. Earlier live trajectories
retain their own archived basis; later qualification does not certify them.

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

Current verification (2026-10-03): eleven provider-backed observation scenarios
finished with closed-store reconstruction and retained public exports; see
`evals/reference/results/lung-lab-assessment-20261002.md` and
`var/task12-proof/completed-assessments.json`. The stock isolated `serve` completed
two cycles/reviews, exactly-once dossier/Delta closure and memory-informed next
allocation with refreshed history pins; its scientific inputs were unavailable.
A separate controlled historical-input block ran owned Pearson/OLS on 41 complete
lung case rows, with unknown literature context and no admitted clinical evidence.
Historical raw public acquisition seq 123 and its full original payload/reference
were retained; no expected outcomes or qualification records were imported. These
separate scenarios do not establish a single composed scientific trajectory.

The attempted historical-input two-cycle composition reached handoff before
scientific work in cycle one (410.25 s plus 580.48 s review); cycle two raised
ModelHTTPError after 197.02 s. Stock serve caught and retained this per-cycle failure;
its top-level null error field must not be interpreted as scientific success. The
unchanged 300 s scheduled-review probe started review at 300.09 s without cancelling
its pending task; interruption recovery closed once and repeated recovery was a
no-op. Initial unsupported-discovery failures, all source/provider errors and later
observations remain preserved. Valid fresh GDC diagnostics returned HTTP 503; a post-audit bounded five-case LUAD
request through the corrected client again returned HTTP 503 at 2026-10-03 16:49 UTC
(`var/production-audit/gdc-report-final-20261003.json`). Source availability, model
latency/failures and missing external review remain distinct from repaired code defects.
Bounded slices do not prove general data-limit usefulness.

The later HEAD 68b5eda descriptive replay admitted a source-slice age summary (95
valid numeric ages of 100 rows), then completed review, but its second cycle failed
InvalidBlockCount without allocation. Cycle/review/failed-next-cycle elapsed times
were 252.84 / 345.65 / 187.68 s; literature search did not yield typed literature
context. The allocation-corrected source replay then completed both cycles/reviews
(514.67 / 538.35 s; 495.49 / 168.47 s), retaining a valid age summary and
memory-informed distinct next allocation, history 6 to 352, and stable registry.
No allocation correction was requested in that run. Both dossiers/Deltas closed
once and reconstructed without unresolved input references. Scientific qualification
remains incomplete: typed literature context was absent, and the second block
treated unsupported diagnosis-array traversal as absence although 96 source rows
contain the requested fields inside arrays. That conclusion is unqualified.
The confirmed descriptive-attempt/context and array-path defects are now repaired
and logged separately with 18 focused checks and 314 invariants in 91.08 s. The
existing context gate stays intact, and unsupported traversal fails InvalidAnalysis.
The corrected frozen trajectory resolves against allocation-corrected-source-worktree.json;
later code/native proof cannot qualify its scientific outcome retroactively.

Corrected-source assessment on committed 04deffb finished on 2026-10-03. Cycle
one failed ModelAPIError after retaining measurements (725.89 s; review 371.56 s);
cycle two completed (774.09 s; review 552.37 s). Both dossiers/Deltas closed once
and resolve their inputs; the failed block remains failed, not successful. Review/
memory informed a distinct next allocation, history 31 to 307 with the same registry.
The completed block admitted a bounded age summary and retained typed unknown/
insufficient_material literature context. Diagnosis-array paths rejected
InvalidAnalysis; a competing worker request failed ResourceBusy operationally.
Exact source/setup and observation: source-context-04deffb-setup.json and
retained-descriptive-serve-source-context-04deffb/observation.json under
var/task12-proof/. No expected outcomes were imported and no error became a
scientific negative. This closes the confirmed context/array-path engineering proof
gaps; the unchanged 120 s target remains reporting rather than cancellation.

Remaining completion proof: broader scientific usefulness and independently
reviewed representation/challenge/next-test choices. The controlled retained-input
continuation and typed unknown context do not qualify fresh acquisition,
independent replication or clinical utility. Qualified reuse remains conditional on Task
10's scientific-utility prerequisite. Independent scientific review/clinical utility
remain explicitly unsupported as requested. Source-owned Welch is unavailable; the
provided-array route does not confer source lineage. Publication was not triggered.
No timers or scientific phases were shortened to manufacture a successful result.
The stale GDC limitation and unsupported endpoint SDK surface were corrected under
Task 11, with historical ordinary WSL proof seq 1158; earlier live observations
resolve against `var/task12-proof/qualified-source-basis-347.zip`. That later native
basis remains archived in `qualified-source-basis-1158.zip`. Completed production
audit fixes and historical-plan reconciliation are recorded in TASK_LOG and the dated
lung assessment, rather than future implementation scope. Current native proof and
its exact-worktree archive resolve through `var/production-audit/final-verification.json`.
Independent review remains withheld as requested; an unavailable Security plugin
scan cannot qualify the broader security claim.
API/UI services are active with HTTP 200 in testing maintenance mode, which proves
startup/transport and keeps automatic research paused. Task 12 stays active.

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
The stale Delta H5 pin limitation was corrected after actual refreshed continuation
pins were observed; this does not qualify missing scientific context.

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
