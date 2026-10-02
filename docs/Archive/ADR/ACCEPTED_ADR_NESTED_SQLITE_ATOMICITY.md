# Nested SQLite bundle atomicity

Date: 2026-10-02. Owner: persistence store.

## Context

The existing store nests bundle writes inside terminal and qualification transactions.
Depth-only rollback allows an outer caller to catch an inner SQLite insert failure and
commit the earlier part of that failed bundle. Trigger fault/reopen regressions reproduced
both the committed-outer and aborted-outer paths before the correction.

## Decision

Begin an explicit outer transaction and use a depth-named SQLite savepoint for each
nested transaction. Release successful nested writes; roll back and release the nested
savepoint on failure, including when the outer caller catches that failure. Commit only
at the outer boundary. Keep the existing reentrant lock, single connection, append-only
schema and runtime-owned write ordering. No database migration or history rewrite.

## Alternatives

Marking the entire outer transaction rollback-only would discard unrelated successful
outer writes after a handled bundle failure. Retaining depth-only rollback violates
bundle atomicity. Separate stores or connections introduce unnecessary ownership changes.

## Consequences and invariants

Nested writes remain invisible to other connections until outer commit. Caught inner
failures preserve prior outer writes while discarding the complete failed inner bundle.
Outer failure discards all writes. Savepoint names derive only from owned depth. This
storage decision does not qualify scientific meaning or authorize cross-history import.

## Verification

Two SQLite-trigger regressions failed before the fix and passed afterward, including
close/reopen inspection. Focused persistence/governance checks: 28 passed, 88 deselected,
8.62 s. Raw before/after logs: `var/audit-nested-rollback-before.log` and
`var/audit-nested-rollback-after.log`. Final broader verification is retained in the dated
lung assessment and the rolling completed task log.

## Status

Decision: ACCEPTED for the existing persistence owner. Implementation: explicit BEGIN
and nested savepoints in `src/persistence/store.py`. Proof: the named local fault/reopen
contracts; native execution controls and scientific qualification remain separate scopes.
