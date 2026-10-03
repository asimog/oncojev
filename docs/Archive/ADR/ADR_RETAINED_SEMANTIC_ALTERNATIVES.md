# ADR: Retain semantic-search alternatives in existing owners

Decision: **Accepted for the bounded retention and proposal-lineage implementation,
2026-10-03**. This engineering decision follows the requested architecture and verified
owner/failure audit; it is not acceptance of scientific utility or a consequence of
passing tests. Implementation and proof are recorded separately below.

Context: on baseline 83b9def, direct hypothesis state was written after Jev success;
Reasoner alternatives were measured sequentially before reaching candidate state.
Memory omitted direct hypothesis fragments and compacted away test/scope. Method byte
trimming removed full alternatives before durable recording. The existing state,
append-only SQLite, memory, frontier, role task and evaluation owners already exist.

Decision: retain the entire Reasoner proposal batch and direct hypotheses before
semantic measurement; preserve exact-duplicate lineage and failed/disabled unknowns.
Keep scientific test lineage in existing state snapshots. Historical equal wording stays
in semantic comparison because its original source/population/replication scope cannot
be inferred from text equality; only exact local duplicates skip reassessment. Append explicit challenged,
reopened, revised and superseded proposal annotations to block-local candidate state,
requiring retained identities and distinct replacements for revision/supersession.
These annotations never mutate the original hypothesis or resolve scientific status.
Derive both proposals and transitions into existing memory with compact test/link
fields; keep transition IDs/status/links in existing global candidate scopes.
Preserve full method receipts before view trimming. Representation omission receipts
retain candidate/source identity; byte-limited views refer to durable records.

Alternatives: leaving proposals only in returned model prose loses direct failures and
scientific test lineage. A separate hypothesis table/search framework/lifecycle owner
would duplicate existing append-only state. Semantic destructive merging would conflate
scope, replication and epistemic status without independent evidence. None is adopted.

Consequences: extra proposal/state records and a new typed proposal-annotation status
are visible through existing reconstruction/memory. Old scientific records stay intact;
the memory derivation version advances and appends refreshed digests. Models remain
shallow-frozen. Annotation status is proposal history, never a scientific finding,
execution permission, admission or automatic allocation decision.

Implementation: src/runtime/pydantic_ai/search_tools.py and contracts.py;
src/memory/models.py and service.py; src/director/frontier.py;
src/sources/representation.py and existing scientific generation tools.
The existing reference/fresh-condition owner records matched search metrics, native
probability variability, unknowns and an owned-launch controlled source trajectory.

Proof: owning behavioral regressions, bounded omission/lifecycle tests, actual live
matched comparisons and controlled retained-source repetitions. Results and exact
identity are retained in evals/reference/results/semantic-search-assessment-20261003.*
and TASK_LOG. Independent scientific utility, autonomous-choice benefit, fresh source
availability and final-basis native/reusable qualification are not accepted by this ADR.
