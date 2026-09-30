# Jev in OncoJev

Jev is TypeSafe System One: typed semantic measurement, not an autonomous agent or an evidence source. Use it after deterministic retrieval/candidate generation and before deterministic frontier management. Prefer atomic Noul, Choice, and Score questions with structured criteria, explicit exclusions, and failure semantics. Preserve full distributions when they influence search.

`jev.client.TypeSafeJevClient` adapts current `typesafe-sdk` Noul, Choice, and Score calls to project-owned types; its deterministic counterpart drives tests. Full native probabilities and Choice/Score confidence are retained. A TypeSafe execution failure raises `jev.failure.JevOperationalFailure` (timeout, rate limit, transport, validation, or service) and is recorded operationally: it never becomes a Noul value, a Choice, or a Score. The supplied deep reference is [references/TYPESAFE_JEV_DOSSIER.md](references/TYPESAFE_JEV_DOSSIER.md).
