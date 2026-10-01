# Research memory

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
