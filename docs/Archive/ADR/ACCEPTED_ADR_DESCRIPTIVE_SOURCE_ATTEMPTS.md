# Descriptive source attempts and explicit array-path eligibility

Date: 2026-10-02. Owner: existing Science execution and runtime persistence owners.

## Context

A completed controlled lung source trajectory reached review and a distinct next
allocation, but its descriptive route supplied no ScientificAttempt records, so
literature context rejected its otherwise valid owned measurement. A real SDK
before-fix check confirmed that rejection. The second block also reported 100
absent diagnosis ages using a dotted path through arrays, although the retained
source contains those requested fields in 96 diagnosis arrays. Unsupported
traversal is not missing data and cannot qualify that scientific conclusion.

## Decision

Retain the existing ScientificAttempt lifecycle around measure_acquisition, binding
the exact owned acquisition, deterministic descriptive contract and exact result.
Completed summaries have unknown scientific outcome. InvalidAnalysis, operational
failure and interruption retain distinct terminal stages; no failed result becomes
a measurement. Measurement and completed-attempt records form one SQLite bundle.
Keep the existing literature consumer's owned/source identity checks and tentative
classification authority unchanged. Empty or title-only material remains unknown;
synthetic and foreign inputs remain ineligible. Do not backfill old attempts.

Reject numeric dotted paths crossing arrays unless an explicit supported
representation or aggregation resolves them. Preserve dictionary-field missing,
null and invalid leaf types; do not choose an arbitrary diagnosis or flatten rows
implicitly. Existing execution limits and required scientific procedures remain.

## Alternatives and consequences

Accepting raw measurement IDs without attempt lineage would weaken the context
owner's contract. Invented historical attempts would change scientific provenance.
Implicit array selection or aggregation would invent a design and could change
cardinality. Explicit rejection exposes missing representation prerequisites while
preserving existing supported summaries. Existing faulty records remain immutable
and their assessment records the limitation; this change cannot qualify them.

## Verification

Before correction, four attempt/context regressions failed; three array-traversal
regressions failed while the dictionary/leaf-type control passed. Current real SDK,
owned-input, lifecycle, context and allocation checks passed 18 tests in 7.70 s.
The full suite passed 314 invariants in 91.08 s. Final native qualification is
separately recorded in TASK_LOG,
the current plan and the dated assessment. Raw before/after logs resolve under
var/production-audit/. Provider-backed corrected scientific composition is separate.

## Status

Decision: ACCEPTED. Implementation: existing attempt records and source numeric
extractor; no new state owner, schema, execution backend or admission authority.
Proof: named behavioral contracts. Earlier runtime continuity is retained against
its archived basis; its diagnosis-absence conclusion is unqualified. Independent
scientific review and broader usefulness remain withheld.
