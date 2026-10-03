# Jev in OncoJev

## Current measurement contract

Jev is TypeSafe System One: typed semantic measurement, not an autonomous agent or an evidence source. Use it after deterministic retrieval/candidate generation and before deterministic frontier management. Prefer atomic Noul, Choice, and Score questions with structured criteria, explicit exclusions, and failure semantics. Preserve full distributions when they influence search.

`jev.client.TypeSafeJevClient` adapts current `typesafe-sdk` Noul, Choice, and Score calls to project-owned types; its deterministic counterpart drives tests. Full native probabilities and Choice/Score confidence are retained. A TypeSafe execution failure raises `jev.failure.JevOperationalFailure` (timeout, rate limit, transport, validation, or service) and is recorded operationally: it never becomes a Noul value, a Choice, or a Score.

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
`candidate-frontier-v1`, owned by `CandidateFrontierPolicy.decide` for the
Researcher `evaluate_candidate` relevance/action tool. Every frontier receipt retains candidate identity/summary,
call/projection linkage, full distributions, policy version and rationale.
KEEP_ALIVE and REJECT_RETAIN are semantic search history, never a scientific
negative finding, evidence admission or authority to extend scope/deadlines.

Local, versioned contracts live in `src/jev/questions.py`: method fit, available
representation sufficiency, hypothesis/test alignment, individual statement
support/overstatement, and selected memory relevance/duplication/contradiction/
gaps/uncertainty. Independent questions share bounded state in one native batch.
`FrontierPolicy.interpret` owns the separate `semantic-frontier-v2` contract used
by `runtime/pydantic_ai/semantic.measure_async` for method, representation,
hypothesis, memory and statement measurements; it retains ambiguous alternatives
and expresses ESCALATE only as a bounded recommendation. Actual route, access and
input checks remain Python decisions. Failed batches never supply a negative
judgment. Exact normalized hypothesis/test duplicates precede semantic comparison.

Statement references resolve before measurement; semantic failure cannot stop
terminal dossier creation. Global memory semantics runs after deterministic retrieval under
separate call/question/byte/time limits and falls back to deterministic ordering.
Native distributions and operational receipts remain durable even when context
contains only bounded receipt references. No new Director acquisition tools exist.

The candidate policy uses its Choice distribution, relevance probability and
reported Score confidence. The multidimensional policy keeps fit dimensions
separate and excludes duplication, contradiction, capability-gap, actionability
and overstatement from fit aggregation. Their thresholds are versioned software
policy, not scientific constants or calibrated confidence. Historical receipts
retain their original versions; neither policy is an evidence-admission gate.

`literature-context-v1` measures a native categorical context judgment alongside
independent claim-support and comparison-scope dimensions. Its annotation policy
always keeps the underlying finding alive and grants no execution or admission
authority. Uncertain distributions or scope remain unknown; required material and
potential-novelty coverage checks are deterministic. The distribution thresholds
are uncalibrated annotation policy, not scientific confidence or proof of novelty.

Unfinished work is tracked only in the [active plan](../IMPLEMENTATION_PLAN.md).

Global investigation and relation contracts use `global-contracts-v1` and a separate `global-frontier-policy-v1`. They reuse native projection/receipt decoding under Director semantic allowances, preserve alternatives on failure, and cannot admit evidence or resolve scientific contradictions. Original relation sides and native distributions remain reference-resolvable.
