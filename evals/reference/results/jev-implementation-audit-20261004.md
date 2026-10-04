# Jev source fixes and implementation bug audit

Date: 2026-10-04. Starting HEAD: `5f3f4175fb346d8214782439aeae557067a71666`.
The worktree already contained the preceding semantic-search assessment, source
representation/relation corrections, evaluation changes, tests and documentation.
Those changes and original scientific artifacts were preserved. This pass applies
source fixes and reviews their real runtime callers; it does not claim whole-repository
feature completion or independent scientific usefulness.

## Existing fixes applied in source

The retained v3 relation question is in `src/jev/questions.py`; supported discovered
modalities remain alternatives in `src/sources/representation.py`. The existing
reference consumer counts actual generation/durable receipts rather than supplied
IDs. Earlier committed source already retains direct/generated hypotheses before
semantic failure, exact local duplicate lineage and historical scope comparisons,
append-only hypothesis transitions, method alternatives and representation omissions.
These were verified rather than reimplemented. No evaluation label became evidence.

## Reproduced bugs and corrections

| Finding | Observable failure | Owning correction | Regression proof |
| --- | --- | --- | --- |
| P2: malformed semantic batches can reach policy | The general candidate route advances an empty response. Typed routes check count/IDs but accept another projection/version or primitive; copied nonfinite values bypass normal model construction. | `HarnessRuntime.evaluate_jev` calls shared `src/jev/client.py:validate_jev_batch` before any consumer. Require complete unique IDs, primitive, projection/version binding, finite values, normalized distributions and declared choice/score support. Preserve valid partial answers as failed history, never advancement. | Both production tool routes exercise empty, partial, duplicate, wrong projection/version/primitive and nonfinite batches. Choice/Score cases cover invalid support, distributions and selected values. Before-fix failures are retained in `batch-regression.log`. |
| P2: byte-bound failure loses method alternatives | A valid bounded need with ten owned acquisitions generates real index candidates, then raises because remaining input context exceeds 32 KiB. The full candidate receipt is absent. | `generate_method_candidates` persists its full existing `METHOD_CANDIDATES` receipt before bounded-view trimming or failure. The oversized agent view still rejects and grants no execution. | Real production generation reproduces missing receipt, then verifies full candidates equal the actual index receipt IDs after failure. `retention-regression.log` retains the original failure. |
| P2: global relation context is missing/misassigned | Investigation payloads contain only the last two relation IDs/statuses. They omit measured results and can refer to unrelated candidate pairs when earlier pairs are already seen. | `prepare_frontier` supplies only relations between the current candidate and its at-most-two selected neighbours, including exact call IDs, native decisions and explicit unavailable status. | A four-candidate production frontier checks every delivered pair against the current candidate/comparison and exact durable measured results. `relation-context-regression.log` retains the original failure. |
| P2: error metadata can mask the original failure | A malformed candidate batch with partial usage metadata lacking `model_resolved` raises KeyError while constructing its failed receipt. | Candidate failure handling derives resolved models from valid partial decisions and conditionally includes an actually reported model name. Missing metadata remains unavailable. | A regression verifies failed receipts, original operational failure and absence of policy/evidence in both routes. `metadata-regression.log` retains the original KeyError. |

These are measurement binding, context composition and existing receipt-order
corrections. Director/Researcher authority, deterministic eligibility/admission,
canonical state, native execution ownership, budgets and institutional qualification
requirements remain unchanged. No new primitive, agent, harness, registry or planner
was added. No new architectural decision is introduced.

## Post-implementation review

Traced every source caller of `runtime.evaluate_jev`: typed `measure_async` and the
general candidate tool both use the new shared boundary. Reviewed native decoding,
failure/partial-answer receipts, candidate policy consumption, owned-input method
generation, global neighbour pairing, memory fallback and persisted provenance.
Full discovery survives byte failures; invalid batches retain proposals and valid
partial native history without a frontier decision, Jev output admission or scientific
evidence. Global relation measurements remain semantic context, not findings.

The final inspected patch preserves original LF/CRLF conventions. Architecture
projection hashes were refreshed only after reviewing the unchanged authority flow.
No further confirmed bug was found within these inspected surfaces. This is a scoped
implementation review, not an exhaustive security or whole-repository audit.

## Verification

Final owning command:

```bash
ONCOJEV_TESTING=0 .venv/bin/python -B -m pytest -q -o addopts='' \
  tests/invariants/test_semantic_retention.py \
  tests/invariants/test_live_mode.py \
  tests/invariants/test_representations.py \
  tests/invariants/test_evaluation.py \
  tests/invariants/test_persistence.py
```

Result: **231 passed in 83.45 seconds**, with one serializer warning from deliberately
malformed Score support. The ordinary subprocess profile is explicit; no project
settings were changed. Initial focused run: 93 passed and one existing profile/
explicit-environment mismatch. A mistaken `ONCOJEV_TESTING=false` retry was rejected
because the setting requires literal `0`/`1`; final verification uses `0`. These
failed attempts remain retained instead of being hidden.

`scripts/check_architecture.py` and `git diff --check` passed. Regression, correction
and final test logs remain in `var/jev-fixes-20261004/`. Earlier assessment corpora,
compressed provider/trajectory records and reports remain unchanged. Rolling task-log
rotation appends the displaced entry intact. Code/test patch identity is retained in
`jev-implementation-audit-20261004.json`.

No new live/provider trajectory or native whole-environment qualification was run.
Offline behavioral tests do not establish scientific usefulness. Independently reviewed
representation/method/next-test labels, meaningful source-bound challenge/replication,
hypothesis discrimination/evolution, ordinary-budget final-basis qualification and
accepted reusable-method utility remain in the existing plan. Feature completeness
cannot be established by fabricating that missing proof or lowering admission gates.
