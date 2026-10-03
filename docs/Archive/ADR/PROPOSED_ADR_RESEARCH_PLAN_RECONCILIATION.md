# ADR: Reconcile research search, experience use, semantics and runtime reuse

Date: 2026-10-02.
Owning documents: [Implementation plan](../../IMPLEMENTATION_PLAN.md),
[Architecture](../../ARCHITECTURE.md), [agent rules](../../../AGENTS.md).
Template: [ADR guidance](GUIDANCE.md).

## Context

Assessment basis: HEAD `b27a6b220cd183bd51aff06aec8b8f778187d1b1`, clean worktree
before this assessment. The supplied proposal is an investigation mandate, not a
verified diagnosis or an accepted runtime redesign. Its attachment SHA-256 is
`ff9f0b92be23160300439e737e7d3d83732b1288af4c9a8d0f92c8e0305be91a`.
This reconciled assessment replaces unsupported assumptions rather than retaining
the supplied text as repository truth. It is archived immediately under the active
document rule; only the current testing ADR has an active-location exception.

### Verified execution and state flow

The service retains a Director instance but uses fresh Researcher runs. In
`src/runtime/pydantic_ai/contracts.py::allocate_block`, a free-form objective is
accepted without a frontier ID. Python computes the allocation and attaches
`StartMemory`; supplied frontier IDs are optional and validated when present.
Thus the live research space is not confined to previously represented hypotheses.

The formal path is narrower:
`global_tools.prepare_frontier → ResearchMemory.search → frontier.generate →
bounded Jev measurements → deterministic beam → validate_selection → allocate_block`.
`frontier.generate` consumes continuation proposals, uncertainties, hypotheses,
follow-ups, attempts, literature contexts, blockers and candidates in retained
digests. It has no input for a newly authored mission-grounded investigation.
`ResearchMemory.search` excludes zero-overlap queries before semantic reranking;
relation comparison also skips pairs without shared terms. These are coverage
limits, not proof that an embedding model or wider search improves scientific utility.

The experience loop already has working mechanisms:
`attempt/follow-up records → ResearchMemory._derive/backfill → digest items →
frontier.generate or semantic_memory_context_async → StartMemory → fresh block`.
Follow-up outcomes produce different future objectives for contradiction, design
repair, sensitivity, independent replication and unresolved information. Retrieval
receipts, allocation events, original references and reopened digests exist.
However, reranking is limited to retrieved items, and a free-form allocation need
not record a frontier choice. Existing records/tests do not establish a causal,
autonomous improvement in later choices from experience.

`src/jev/questions.py` already batches independent Noul questions for global/local
fit, hypothesis alignment, memory, distinction, contradiction and replication.
Statement support and literature context already use Choice plus Noul, with unknown
outcomes. SDK models/client also support Score. `semantic.measure_async` retains
versioned questions, projections, native decisions, failures and policy identity.
Global policy uses categorical deterministic rules; several measured dimensions
are retained without directly changing its beam rule. Additional questions alone
would not repair missing candidates or prove a better consumer decision.

`src/evals/harness.py` creates fresh stores/runtimes and compares science-only,
science/Reasoner and science/Jev/Reasoner. It collects execution/record counts,
elapsed time and failures; declared replication IDs are not verified replication.
`selection.py` and `representation.py` exercise their respective production
consumers with different case contracts. Representation cases have split/label
basis and keep labels out of provider projections; selection has a smaller embedded
label set and reports unknown downstream utility/cost. Task 3 already owns shared
corpus/harness/metrics; Task 14 owns composed-lab evaluation. Their distinction is
valid. A neutral extensible condition interface, independent scientific labels,
consistent accounting and multi-block ablations remain unfinished; actual duplicated
whole-system implementations were not found.

The follow-up audit reproduced a current-catalogue candidate-coverage failure, not
only a prospective scaling problem. With the configured page size 20 and candidate
budget 80, the 109-item initial catalogue omits labelled `stat.scipy` for
`co movement linear association` (recall 0); budget 200 exhausts the catalogue and
retrieves it (recall 1). `scripts/evaluate_selection.py` currently overrides the
candidate budget to 200. This fixed-query label result does not prove autonomous
or scientific utility. Task 3 must expose the configured-budget baseline separately
from larger-budget diagnostics; current Task 11 owns bounded repair through the
canonical OncoLab registry/discovery and agent consumer without waiting for scale work.

The installed environment reports Pydantic AI `2.52.0`, Harness `0.52.0` and
TypeSafe SDK `0.7.2`. `agents.py` already composes Harness CodeMode and Linux Coder,
replaces its Shell with an owned foreground adapter and supplies ConfinedWorkspace.
The installed Linux Coder also retains ClearToolResults (fraction 0.7),
WarnNearLimits (context fraction 0.9), bounded output truncation and
RepairToolArguments. Replacing only Shell preserves these inherited capabilities.
Windows does not compose Coder. These are existing platform-specific mechanisms,
not merely available future adaptations; their live effectiveness is unverified.
`RuntimeControls` uses capability hooks and SDK UsageLimits while enforcing
cross-role/aggregate budgets and terminal-event yield. Telemetry is already wired.
Custom persistence, resource leases and drain are domain obligations, not shown
to be duplicate generic agent infrastructure. Agent runs do not pass prior
transcripts for continuity; retained research context is the owner.

### Classification of the supplied concerns

| Concern | Classification and evidence-based disposition |
| --- | --- |
| Director search is closed to new questions | Partially correct: formal digest generation is closed; free-form allocation is already implemented. Extend formal proposal intake, preserving the free-form path. |
| Memory is only searchable history | Stale/false as a blanket claim: outcomes already alter generated future questions and block context. Partially correct concerning autonomous choice lineage and measured benefit. |
| Tasks 3 and 14 duplicate evaluation | Partially correct as a scope risk, not established duplicated implementations. Retain substrate versus experiment ownership and share case/accounting machinery. |
| Candidate-generation abstraction is premature | Correct for active scheduling: the representation generator is missing and no common contract or benefit is demonstrated. Retain an explicit future trigger. |
| Representation and scientific operation owners conflict | Stale/false at the inspected flow: source/representation checks, method discovery and deterministic Science are distinct. Preserve Tasks 5, 6, 8 and 9. |
| Repeated qualification is duplicate work | Partially correct concerning repeated descriptions; native confinement, canonical-reference validation, environment recovery and reusable acceptance establish different facts. Retain their producers and consume their records once. |
| Jev is only shallow classification | Partially correct: typed multidimensional contracts and Choice compositions already exist. Scientific value of richer compositions is unverified; improve against failure cases, including consumer use and question pruning. |
| Custom runtime should be replaced by Pydantic/Harness | Already implemented in substantial part, including Linux Coder result clearing, near-limit warnings, output truncation and argument repair. Preserve canonical owners; evaluate existing controls before adding conditional summarization/reminder mechanisms. |
| Scaling and publication must remain active now | Defer broader scale infrastructure while keeping the demonstrated current-catalogue recall repair active. Publication deferral is a scheduling recommendation, not evidence that its unfinished handoff is unnecessary; activate on a selected publication need, then perform publisher setup and remote proof. |

### Relevant prior art and compatibility limits

Current [TypeSafe reranking guidance](https://docs.typesafe.ai/cookbooks/rerank_typesafe)
uses retrieval followed by semantic comparison. This supports measuring candidate
coverage before tuning judgments; omitted candidates cannot be recovered by reranking.
[Entity alignment](https://docs.typesafe.ai/cookbooks/entity_alignment) composes a
descriptive Score with independent Nouls; it supplies a design example for graded
fit and supporting dimensions, not oncology validity or universal thresholds.
[Parallel questions](https://docs.typesafe.ai/cookbooks/parallel_questions) motivates
batching related questions. These examples do not establish a benefit from adding
questions to the existing batches. No cookbook benchmark result is transferred here.

Current Pydantic [compaction](https://pydantic.dev/docs/ai/harness/compaction/),
[tool-output handling](https://pydantic.dev/docs/ai/harness/tool-output-limits/) and
[reminders](https://pydantic.dev/docs/ai/harness/system-reminders/) provide generic
mechanisms, some already inherited from Linux Coder as described above. Establish
that platform-specific baseline before comparing changes; additional summarizing
compaction or reminder mechanisms require an observed failure and measured benefit.
Installed capability composition was inspected; live effects on OncoJev context,
costs and control-hook composition were not exercised.
[Framework Skills](https://pydantic.dev/docs/ai/harness/skills/) catalog exposure is
not an access-control boundary; it must not introduce another procedural authority
alongside BlockSkillStore. Framework run persistence is not research-state ownership.

Scoped historical reads covered the simplified-plan and repository-reconciliation
ADRs, `.upstream/INDEX.md`, its manifest, and ClawBio/K-Dense READMEs. ClawBio's
pinned `docs/reproducibility.md` explicitly distinguishes replay bundles from full
input/tool availability guarantees. Retain exact replay/environment provenance in
existing qualification owners; a bundle is not scientific validation. The K-Dense
library illustrates procedural guidance, not an execution/admission authority.
Manifest pins are reference provenance, not independently refreshed clones or
qualified dependencies. No upstream package was installed or imported into runtime.
No broad historical-report or upstream scan was performed; other scientific-agent
architectures and OpenAI patterns are not needed to justify this bounded decision.

## Decision

Technical recommendation: **ADOPT WITH LIMITATIONS**.

Adopt evidence-led plan reconciliation through existing owners. Add no runtime,
configuration, database, scientific-method or test implementation in this assessment.
The edited feature specs are recommendations for unfinished work, not delivered
capabilities or accepted execution architecture.

Retain separate neutral evaluation machinery and composed-lab experiments. Extend
the formal frontier with bounded Director-authored, mission-grounded proposals;
make experience-to-selection lineage observable through existing records. Address
retrieval misses before extra semantic calls. Evaluate Choice/Score/Noul composition
against independent failure cases and actual downstream decisions. Prefer installed
framework capability reuse after a measured generic runtime problem, retaining
scientific ownership and deterministic execution controls.

The Bitter Lesson is a useful lens for general proposal/search/experience mechanisms;
it does not justify removing eligibility, admission, budget or validation contracts.
No RL, fine-tuning, bandit, embedding store, common-generator platform or automatic
live semantic-policy rewrite is required by current evidence.

### Requirement preservation and proposed plan edits

| Original scope | Retained owner/disposition |
| --- | --- |
| Tasks 1 and 2 | Unchanged resource enforcement and exact-basis WSL2 qualification; installed Science limits remain a real prerequisite. |
| Task 3 | Neutral substrate, independent corpus, labels, splits, condition adapters, metrics, candidate/scope utility records and resource accounting. Retains scientific-validity/leakage requirements and exposes configured-budget selection recall separately from larger-budget diagnostics. |
| Task 4 | Existing lifecycle/regeneration plus bounded new-proposal intake and outcome-to-choice lineage. Repair labelled memory misses in ResearchMemory. No second memory or Director authority. |
| Tasks 5, 6, 8 and 9 | Unchanged representation alternatives, reference validation, justified named operations and scientific challenges. These are distinct capabilities. |
| Tasks 7 and 10 | Unchanged fresh-environment producer and governed reusable dispatcher/acceptance. Governance consumes Tasks 2/3/6/7 proof; repeated consumption is not duplicate production. |
| Task 11 | Complete publication scope/proof retained under Conditional extensions as a scheduling recommendation; activate for an explicitly needed publication deliverable. Separate publisher configuration, credentials, connectivity and remote SHA proof are work/completion requirements after activation. No capability completion claim. |
| Task 12 | Complete scale-retrieval scope/proof retained under Conditional extensions; activate on measured growing-scale recall/resource failure. Task 3 measures configured-budget recall; former Task 14 (current Task 11) owns current OncoLab retrieval repair, and Task 5 owns input alternatives. |
| Task 13 | Complete shared-generator comparison spec retained under Conditional extensions; activate only after representation generation and demonstrated useful shared mechanics. |
| Task 14 | Whole-lab multi-block experiments consuming Task 3, plus bounded current-catalogue recall repair through the canonical OncoLab owner. Compare experience/search/capability conditions, semantic composition and measured runtime refinements against the installed platform-specific baseline. Retains calibration, recall, instability, budgets and reviewed-adoption limits. |
| Task 15 | Core source-bound composed trajectory retained; qualified reuse remains required when delivered, and publication is conditional with an honest unavailable result before its trigger. Native, connectivity, utility and remote proof remain separate. |
| Task 17 | Removed solely at the user's explicit instruction. Its fast-testing decision remains in the accepted active ADR, with all implementation/proof obligations unverified and no replacement plan task. This is an explicit exception to normal unfinished-work tracking, not silent loss or completion. |

Active tasks are numbered consecutively from 1 through 12. In the original-scope
table above, former Task 14 maps to current Task 11 and former Task 15 maps to
current Task 12; original Tasks 11–13 name the three conditional extensions, not
current active tasks. References in the verified-HEAD context retain their historical
numbering. Twelve tasks remain active; three conditional specs remain in the sole plan. Reduction follows the triggers above, not a target count.
No new tracker, parallel corpus owner or generic-runtime work item is introduced.

## Alternatives

Keep the plan unchanged: preserves valid separate acceptance scopes but retains
unconditional platform/publication scheduling and leaves formal proposal coverage
implicit. Merge Tasks 3/14 wholesale: loses substrate versus experiment distinction
and makes evaluation dependent on the mechanism it measures. Merge qualification
tasks: confuses native execution, reference/scientific validity, recoverability,
utility and reusable governance. These alternatives are not recommended.

Introduce a learned search policy or unified candidate-generation platform now:
unnecessary without comparative evidence. Replace canonical research memory and
domain lifecycle with framework persistence/memory/safety: conflicts with recorded
ownership and does not demonstrate equivalent scientific or execution controls.
Adopt every available Harness capability: adds coupling/cost without a demonstrated
problem. More Jev calls by default: cannot recover an omitted candidate and may
increase cost without improving a consumed decision.

## Consequences

The core plan becomes more focused without dropping scoped scientific qualification.
Formal search and experience use receive testable mechanism requirements. Evaluation
can measure different mechanisms without inheriting their authority. Framework reuse
remains available with an explicit behavioral trigger and compatibility comparison.

Costs include new proposal provenance, retained choice lineage and multi-block
experimental design. Semantic utility and the benefit of broader proposal search
remain empirical questions. Conditional specs can drift before activation and must
be reverified then. Removing Task 17 is an explicit user-directed tracking exception;
acceptance of the testing ADR does not make its switch available.

## Invariants/boundaries affected

No runtime authority/state/execution boundary changes in this delivery. Director
allocates globally; Researcher investigates locally; ResearchMemory derives canonical
record-linked context; OncoLab owns scientific capabilities; BlockSkillStore owns
procedural guidance. Science measures and admits; Jev judges semantics; Python
enforces lifecycle, eligibility, admission, budgets and execution. The neutral
`src/evals` owner measures outcomes and never supplies scientific evidence.

Architecture and AGENTS remain current boundary authorities. README reflects the
testing decision status; Architecture also records inherited Linux Coder controls
without claiming their live effectiveness. The existing YAML owners, directions,
ENFORCED/TESTED/REVIEWED classifications and limits were reviewed and retained;
only Architecture's canonical hash changes. Future implementation must reconcile
its actual state/ownership decision before refreshing that projection.

Owning behavioral evidence inspected includes the global-frontier/stale-basis test,
semantic-memory budget/fallback test, source-resolved follow-up/reopen test and
evaluation-condition/label-isolation tests in `tests/invariants/test_persistence.py`
and `test_evaluation.py`. Fixtures prove their exercised plumbing and contracts;
they do not establish scientific correctness or autonomous learning utility.

## Verification

Initial `git status --short`: clean. `git rev-parse HEAD`: the basis above.
Source/test/configuration and installed API inspection only; no tests or runtime
were changed. Reviewed every original task against its retained feature spec or
explicit trigger. Tasks 1/2/5/6/7/8/9/10 are preserved; conditional bodies retain
their original scope and proof criteria; Task 17 is the named user exception.
Archived ADR/template links and source references require explicit review because
routine governance excludes archived Markdown.

Final documentation/governance results are recorded in [TASK_LOG](../../TASK_LOG.md).
Required checks are `.venv/Scripts/python.exe -B scripts/check_architecture.py
--docs-only`, scope/requirement/archived-link preservation review and `git diff --check`.
Both commands passed (exit 0). Inline scope/preservation review passed: eight
unaffected task specs unchanged, three conditional bodies preserved, expected task
inventory, unchanged projection semantics, exact template sections and resolving
local ADR links. Two-entry log rotation preserved the displaced entry intact.
These original checks establish static documentation integrity only. Follow-up
audit corrections retain current-catalogue repair as active work, remove publisher
setup from its activation gate and identify inherited Linux Coder controls. Their
completed verification and implementation identity are recorded in TASK_LOG; these
corrections change documentation, not retrieval or agent behavior.

Not verified: empirical search/learning/semantic utility, richer Jev compositions,
multi-block ablations, live provider behavior, native WSL2 controls, qualified reusable
execution, remote publication, live effectiveness of inherited Coder controls or
additional summarizing compaction/reminder adaptations, or testing-profile behavior.
Relevant owning tests were inspected but not run for the initial documentation-only
assessment; the follow-up audit ran seven local evaluation/frontier/memory fixture
cases, not scientific-utility or native/provider qualification. Live TypeSafe
Markdown endpoints failed; their normal official pages
were accessible and used instead.

## Status

**PROPOSED — repository-reconciled recommendation, 2026-10-02.** The user requested
assessment and plan suggestions, not acceptance of a new runtime architecture.
Documentation edits are delivered; proposed runtime/scientific changes remain
unfinished in the plan. Passing governance checks does not accept this ADR.

The separate fast-testing ADR is **ACCEPTED** by explicit user instruction, remains
at `docs/PROPOSED_ADR_FAST_LOCAL_TESTING.md`, and has unverified implementation.
