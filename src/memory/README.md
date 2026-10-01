# Research memory

The sections below first describe the delivered F3/F4 behavior, then the planned
next-stage extensions. [The active implementation plan](../../docs/IMPLEMENTATION_PLAN.md)
owns H0–H15 status; [the completed F0–F6 plan](../../docs/IMPLEMENTATION_PLAN_COMPLETED_F0_F6.md)
preserves the prior delivery record. Full requirements are retained in
[the reference document](../../docs/references/NEXT_STAGE_AUTONOMOUS_LAB_REQUIREMENTS.md).

## Delivered typed continuity

`ResearchMemory` derives versioned cycle digests from append-only records. Each
reference pins record kind, sequence, identity, owner and SHA-256. Missing source
or dossier references remain explicit uncertainty. Digests include corrected
lifecycle/run outcomes, admitted-evidence and measurement references, limitations,
hypotheses, candidate history, blockers, uncertainties, proposals and recorded use.
Director prose is optional context and never supplies canonical outcomes or search
relevance. Legacy prose remains labelled, including records without a linked cycle.

Backfill runs through autonomous/factory composition and after terminal cycle
recording. It appends derived snapshots without altering original records. A new
correction or state revision produces a new digest; retrieval selects the latest
snapshot of each cycle. API reads do not backfill or execute research.

Search uses deterministic token overlap and stable identity ties, with explicit
mission/entity/topic/time filters. Entity/topic tags are declared at allocation,
not guessed from model prose. Returned context is bounded to 20 results and 32 KiB,
with omitted-item and text-truncation markers. Start memory is bounded to 16 KiB;
the new Researcher receives references and summaries, never prior transcripts,
inherited evidence IDs, measurements, skills or budgets.

`get_negative_results` reads the distinct scientific-negative field. Existing
Science outputs do not declare scientific-null/negative interpretations, so this
field remains empty for those outputs. Memory never manufactures negatives from
zero values, missing evidence, semantic rejection or provider failures. Hypotheses
and semantic history retain their original epistemic status.

The service owns one Director Agent per process through the factory. It passes no
previous message history (retention bound: zero); persisted structured memory
remains authoritative after restart. Each cycle has a new runtime, and each block
has a fresh Researcher, state, skill selections and usage budgets.

Semantic annotations follow deterministic retrieval of selected digests. Separate global retrieval budgets bound calls, questions, bytes and elapsed time. Failures return F3 ordering with operational receipts. Native answers remain in Jev receipts; no whole-memory context or evidence authority is introduced.

## Planned next stage: global memory and BlockDelta (H3–H4)

The database remains authoritative typed scientific and operational state.
Research Memory is a versioned, reference-resolved view for Director decisions;
it cannot admit evidence or overwrite original records. Planned OncoLab
institutional memory records capabilities, revisions, verification, failure,
demand and governance history. The separate `asimog/oncojevlab` repository is a
deterministically generated human-readable projection of persisted records.
Director primarily consumes typed Research Memory, Python owns durable state,
and humans inspect the projection. Markdown is never read back as scientific
truth or used to repair authoritative state.

`BlockDelta` (or the smallest equivalent typed extension) is planned to answer
what changed because of a terminal block. It derives reference-linked changes
from durable records rather than interpreting dossier prose. Its contract covers
new evidence/measurement references, hypotheses, explicitly recorded scientific
negative findings, new or explicitly resolved uncertainties, continuation
proposals, operational blockers, capability demand/gaps, candidate contradictions,
cross-block relation candidates and resource-use deltas. Prefer references over
duplicated payloads. Missing references, legacy unreplayable inputs and unknown
outcomes remain visible; no delta field invents a negative result, resolved
uncertainty or unsupported scientific inference.

H4 extends the delivered retrieval-first pattern: deterministic high-recall
search and exact duplicates, bounded typed comparison candidates, Jev semantic
dimensions, then a deterministic retained memory frontier. Candidate generation
uses declared entity/topic tags, capability IDs, stable hypothesis identities,
shared references, time bounds, retrieval terms and block lineage. It must not
compare the whole database all-pairs. Separate budgets bound semantic calls,
questions, projections, bytes and elapsed time; failures preserve deterministic
ordering, explicit uncertainty and operational receipts.

Planned semantic context includes relevance, duplication, contradiction,
recurring/newly actionable uncertainty, repeated hypotheses/blockers, recurring
capability need and cross-block relationships. Global hypothesis records preserve
duplicate, paraphrase, related-but-distinct, independent-replication,
contradicted, blocked, newly-testable, deferred and explicitly resolved
distinctions. Cross-block relation candidates retain source references, relation
type, call IDs, native distributions, limitations, basis sequence/memory revision
and status. Apparent contradictions preserve both originals and may require a
bounded test of population, design or method differences. These records guide
search; hypotheses and semantic relations retain their non-evidence status.

Program review is planned to derive typed descriptive context about recurring
research, uncertainty, failures, capability gaps, modality concentration and
resource use. It supplies future allocation context without a universal quality
score or self-reward loop. The global deterministic frontier has a distinct
policy identity from the Researcher's block-local frontier; memory relevance or
Jev output grants no action, admission or lifecycle authority.

## Planned basis revalidation and readable export (H3, H5, H12)

Director may prepare bounded global context while the single Researcher runs.
Prepared frontiers must pin memory digest IDs, the database high-water sequence,
active block ID/revision, OncoLab revision and application version. On Researcher
completion, consume the new `BlockDelta` and revalidate the basis before making
a future allocation; stale plans cannot execute automatically. Active block
state, workspace, skills and budgets remain isolated. An immutable OncoLab
revision pinned by a block cannot change beneath it; accepted institutional
updates become visible between blocks without altering historical memory.

H12 plans deterministic Markdown/JSON export from typed database records at
material boundaries such as terminal blocks, frontier changes, contradictions,
accepted capability revisions, program reviews and mission changes. Generated
output must link references and label evidence, measurements, hypotheses,
semantic judgments, Director decisions and operational failures separately.
Export/publication status is operational data. GitHub failure retains scientific
state and terminal records and must not roll back evidence or block closure.
Publisher credentials remain outside Coder environments; absent setup is an
explicit external requirement. This documentation update creates no exporter,
publisher or global-memory runtime implementation.
