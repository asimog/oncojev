# Jev in OncoJev

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
