# Jev in OncoJev

This document separates the delivered F0–F6 measurement contract from the planned
H0–H15 extension. [The active implementation plan](IMPLEMENTATION_PLAN.md) owns
next-stage status; [the completed plan](IMPLEMENTATION_PLAN_COMPLETED_F0_F6.md)
retains historical delivery evidence. The full supplied requirements remain in
[the reference document](references/NEXT_STAGE_AUTONOMOUS_LAB_REQUIREMENTS.md).

## Delivered measurement contract

Jev is TypeSafe System One: typed semantic measurement, not an autonomous agent or an evidence source. Use it after deterministic retrieval/candidate generation and before deterministic frontier management. Prefer atomic Noul, Choice, and Score questions with structured criteria, explicit exclusions, and failure semantics. Preserve full distributions when they influence search.

`jev.client.TypeSafeJevClient` adapts current `typesafe-sdk` Noul, Choice, and Score calls to project-owned types; its deterministic counterpart drives tests. Full native probabilities and Choice/Score confidence are retained. A TypeSafe execution failure raises `jev.failure.JevOperationalFailure` (timeout, rate limit, transport, validation, or service) and is recorded operationally: it never becomes a Noul value, a Choice, or a Score. The supplied deep reference is [references/TYPESAFE_JEV_DOSSIER.md](references/TYPESAFE_JEV_DOSSIER.md).

Every candidate evaluation has a unique call ID and append-only started/prepared/
terminal receipts. They retain the bounded projection and its specification/hash,
versioned question definitions/exclusions and hashes, primitive types, requested and
reported resolved models, elapsed attempt time, native decisions and operational
failures. SDK construction and decoding are inside the failure boundary. Valid
partial answers survive a failed batch for inspection; no failed batch reaches
frontier policy. Duplicate question IDs are rejected before dictionary conversion.
Question count and request bytes are bounded independently of allocation counters.

Known exclusions are delivered in structured SDK instructions, consistent with
[TypeSafe's structured question contract](https://docs.typesafe.ai/sdk/python/api/types/questions).
The adapter retains only reported token usage; the installed response contract
does not report retry counts, so retry metadata remains null and no monetary cost
is invented. [TypeSafe response contract](https://docs.typesafe.ai/sdk/python/api/types/responses).

Projection version 2 includes acquisition summaries, source/evidence references,
provenance, measured values, explicit origin and limitations. Provided values stay
provided; missing values stay null. Raw acquisitions and shell output are excluded.
Count/byte bounds omit whole entries with explicit omitted counts rather than alter
measurements. `config/runtime.yaml` controls projection and SDK request bounds.

Candidate question templates are version 2; frontier policy remains
`candidate-frontier-v1`. Every frontier receipt retains candidate identity/summary,
call/projection linkage, full distributions, policy version and rationale.
KEEP_ALIVE and REJECT_RETAIN are semantic search history, never a scientific
negative finding, evidence admission or authority to extend scope/deadlines.

F4 adds local, versioned contracts in `src/jev/questions.py`: method fit, available
representation sufficiency, hypothesis/test alignment, individual statement
support/overstatement, and selected memory relevance/duplication/contradiction/
gaps/uncertainty. Independent questions share bounded state in one native batch.
`semantic-frontier-v2` extends the existing policy; it retains ambiguous alternatives
and expresses ESCALATE only as a bounded recommendation. Actual route, access and
input checks remain Python decisions. Failed batches never supply a negative
judgment. Exact normalized hypothesis/test duplicates precede semantic comparison.

Statement references resolve before measurement; semantic failure cannot stop
terminal dossier creation. Global memory semantics runs after F3 retrieval under
separate call/question/byte/time limits and falls back to deterministic ordering.
Native distributions and operational receipts remain durable even when context
contains only bounded receipt references. No new Director acquisition tools exist.

The TypeSafe skill-suggestion, rerank and citation-check cookbooks informed compact
shortlist expansion, recall-before-reranking and per-statement checks. Cookbook
thresholds were not adopted as scientific validation. The scoped provider report
is `src/evals/results/f4-selection.json`; equal useful-candidate recall in these
five tasks is not evidence of downstream scientific advantage.

## Planned next stage: global semantic research control (H3–H4)

The delivered F3/F4 memory retrieval and semantic annotations remain the base.
The next stage adds bounded Director operations for global comparison; it does
not add a global Jev agent or give the Director scientific acquisition or
evidence-admission tools. Conceptual operations are memory-frontier analysis,
hypothesis-relation analysis, cross-block relation analysis, contradiction
analysis, future-block comparison and research-program review. Implementation
must extend the current typed tools where possible rather than provide an
unrestricted Jev escape hatch.

The planned global flow is deterministic high-recall retrieval, deterministic
candidate generation and exact duplicate checks, bounded typed projections,
atomic Jev dimensions, deterministic global frontier composition, a small
retained beam, and the Director's choice of one future block or a truthful
program pause. Retrieval gates comparisons by entity, topic, capability,
hypothesis identity, shared references, time and block lineage. Whole-database
all-pairs semantic comparison is excluded. Question, call, byte, elapsed-time
and role/cycle resource budgets bound the work; maximum semantic value does not
mean maximum call volume.

| Planned comparison | Separate semantic dimensions and retained distinctions |
| --- | --- |
| Research Memory | Relevance, duplication, contradiction, recurring/newly actionable uncertainty, repeated hypothesis/blocker, recurring capability need and cross-block relationship |
| Global hypothesis portfolio | Stable identity and exact normalized duplicates first; duplicate, paraphrase, related but distinct, independent replication, contradicted, blocked, newly testable, deferred and resolved remain distinguishable |
| Cross-block relation candidates | Possible subgroup overlap, testable explanation, defined-population relevance, conflict and independent versus repeated descriptions; all remain context for testing |
| Contradiction frontier | Population, design, measurement method and epistemic phrasing can explain apparent conflict; retain both original results and the limits of any proposed resolution |
| Future block candidates | Mission relevance, recorded uncertainty, duplication, contradiction resolution, continuation coherence, dependency readiness, bounded-block fit, capability availability, hypothesis discrimination and material state change |
| Program review | Repeated exploration, rediscovered hypotheses, unresolved contradictions, recurring failures/gaps, modality concentration, measurements without uncertainty reduction, costly low-change blocks and recurring deferred ideas |

These are independent dimensions, not one universal research-quality score or a
self-reward mechanism. A `CrossBlockRelationCandidate` must retain its source
references, relation type, Jev call IDs and native distributions, limitations,
basis sequence/memory revision and explicit status. Candidate-for-testing,
possible-duplicate, contradiction, independent-relation and uncertain statuses
must never imply new `ScientificEvidence`. Hypothesis rejection remains semantic
history, not a scientific negative. Independent replications must survive
duplicate handling.

## Planned policy and basis boundaries

Global and local frontiers may reuse primitives, projection infrastructure,
receipts and distribution decoding. They need distinct candidate types,
authority, scope, stop conditions, deterministic policy identities/versions and
threshold interpretations. The Researcher's existing local frontier asks what
to pursue within its block; the planned Director frontier asks what to allocate
next. Existing local policy thresholds are not automatically valid for global
allocation. H14 audits actual `FrontierPolicy.interpret` and `decide` callers
before consolidation or calibration; historical receipts retain their original
policy identities.

Every planned global result must retain projection/question versions and hashes,
source and basis references, call IDs, complete native distributions, operational
failure information and deterministic policy rationale. Jev failure returns the
deterministic retrieval/frontier fallback with explicit unknown semantic fields;
it cannot become a rejection or negative finding. Ambiguity preserves useful
alternatives. Science alone admits evidence, Python composes policy and controls
lifecycle, and the Director chooses allocation.

A frontier prepared while a Researcher is active must pin memory digest IDs,
database high-water sequence, active block/revision, OncoLab revision and
application version. Block completion invalidates or triggers explicit
revalidation of this basis before allocation. `BlockDelta` supplies recorded
changes and references; it does not supply inferred scientific conclusions.
Semantic tools cannot mutate active ResearchState, extend deadlines, allocate
blocks themselves or mutate OncoLab. A pause is a typed research-program outcome,
never proof of mission attainment or a fabricated completed block.

H13 evaluates useful-candidate recall, diversity, duplication and contradiction
handling, uncertainty preservation and resource use separately from deterministic
correctness. Calibration, self-consistency and Autoresearch remain D5 work gated
by measured instability; this documentation change implements none of them.

Global investigation and relation contracts use `global-contracts-v1` and a separate `global-frontier-policy-v1`. They reuse native projection/receipt decoding under Director semantic allowances, preserve alternatives on failure, and cannot admit evidence or resolve scientific contradictions. Original relation sides and native distributions remain reference-resolvable.
