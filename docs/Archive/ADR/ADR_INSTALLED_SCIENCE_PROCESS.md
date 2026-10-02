# ADR: Govern installed scientific operations as owned Linux command families

Date: 2026-10-02.
Owning documents: [Architecture](../../ARCHITECTURE.md), [implementation plan](../../IMPLEMENTATION_PLAN.md).

## Context

HEAD `2d10d1d2fe7875690d48f8eecaa929679753d877` with the existing migrated
worktree used `HarnessRuntime.heavy_operation` to offload installed statistics,
source summaries, parsing and figures into threads. The heavy lease drained them
on cancellation, but did not enforce memory, CPU, descendants or aggregate disk.
Coder and external scientific execution already use `run_owned_command`, whose
systemd user cgroup, private network/mount namespaces and tmpfs quota provide the
required process-family governor. The service owns state and append-only records.

## Decision

Use that existing governor for live installed computations. Serialize only a fixed
allowlist of installed scientific operations and typed JSON input values; a trusted
worker imports installed packages after filesystem/process confinement. It receives
no credentials, store or runtime handles. Reconstruct results on the service loop,
retain actual process receipts on success and failure, and derive Delta resource
usage from those receipts. Remaining block workspace capacity is consumed across
operations rather than reset. The shared heavy lease stays held through cancellation
and descendant cleanup; unconfirmed cleanup quarantines ownership and locks further
heavy execution. Explicit deterministic fixtures keep offline execution and cannot
qualify a native implementation.

## Alternatives

Retaining threads cannot enforce family CPU/memory limits. A second process pool
would duplicate resource and cleanup ownership. Serializing arbitrary callables or
pickle values would widen authority and obscure the operation/input contract.

## Consequences

Installed operations incur a fresh process and scientific-import cost. The worker
allows read-only scientific packages and application source, bounded writable
operation scratch and no network/host-process authority. It preserves scientific
input validation, measurement origin and explicit evidence admission. Sampled
allocated-disk peaks are lower bounds; missing CPU counters remain unknown. This
execution change does not produce reusable-method or current-environment local
qualification; Task 2 owns that separate writer/consumer proof.

## Invariants/boundaries affected

Science computes detached values; the service owns leases, state and persistence.
`src/science/installed.py`, `installed_exec.py`, runtime contracts/factory/resources,
`src/runtime/process_exec.py` and `src/dossier/delta.py` own the changed flow.
Existing sandbox and service-resource configuration remain the limits owner.
Architecture and its reviewed projection describe the adopted execution boundary.

## Verification

Explicit native `scripts.verify_installed_science` passed in ordinary and testing
profiles: real installed summary, source-paired analysis, parser, figure, invalid
input, actual memory cgroup kill/cleanup, cancellation drain, Director exclusion,
retained disk allowance and measured Delta. Inputs are fixtures, not source evidence
or scientific-utility qualification. Offline service-transport tests passed 3 cases;
aggregate Runner shutdown also passed in both profiles. Owning regressions passed
185 cases in 68.67 s before the final revised 3-5-minute timing settings; final
timing proof and retained records are in TASK_LOG on completion.

## Status

ACCEPTED on 2026-10-02 as the implementation decision for the user's Task 1 request.
Implementation and native probes are present; completion remains governed by the
plan's required final owner regressions and resource/shutdown proof. Passing probes did
not itself accept the decision or complete Tasks 2-5.
