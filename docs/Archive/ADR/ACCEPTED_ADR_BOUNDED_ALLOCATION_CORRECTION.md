# Bounded correction for a missing cycle allocation

Date: 2026-10-02. Owner: Director output validation and Python cycle lifecycle.

## Context

At HEAD 68b5eda, a controlled provider-backed historical-source assessment retained
one valid source-slice age summary and review, then the persistent Director returned
without allocating its next block. Python correctly recorded InvalidBlockCount.
The model claimed allocation tools were absent. Repeated real SDK catalog inspection
advertises run_code, allocation and frontier functions on both runs; the model's claim
is not proof of missing application tools or of the provider's internal presentation.

## Decision

Offer one output-validation correction when a supervised allocating cycle returns
without any block for its cycle ID. Persist an operational service event containing
cycle/mission identity, reason and output hash, then request the Director to use its
existing functions. The Director chooses scope and performs the actual allocation.
A second empty return is accepted as a model return and rejected by the existing
Python InvalidBlockCount check. Existing launch fallback, usage controls, scientific
admission and source procedures remain authoritative.

## Alternatives

Leaving every recoverable empty return terminal impedes scientific continuation.
A Python-generated question/block would replace the Director's selection authority.
Unlimited output retries could consume unbounded work; a per-cycle counter allows
only one correction, including when the testing runtime is otherwise unbounded.

## Consequences and boundaries

A correction consumes normal model request/cost allowance and can still fail when
limits or the model prevent allocation. It does not retry rejected scratch commands,
shorten science or timers, manufacture results, or qualify scientific usefulness.
Standalone, event and post-block review turns have no allocation requirement. The
same mutable-state/persistence owner remains; no schema migration or new agent.

## Verification

Recovery and permanent-refusal tests failed before correction. Focused current
allocation, serve/event and request-limit owners passed 22 checks in 11.36 s. Tests
exercise real SDK allocation and cycle closure, ordinary/unbounded runtime modes,
permanent refusal and exhausted Director request allowance. Raw before/after logs
are retained under var/production-audit/allocation-correction-*.log. The final full suite passed 314 invariants in 91.08 s. Native and
composed qualification remain separate evidence recorded in the current plan/report.

## Status

Decision: ACCEPTED for operational allocation protocol recovery under the existing
owner. Implementation: one Director output validator and operational receipt.
Proof: the named local contracts. A later controlled run completed two cycles and actual continuation without invoking
the correction, so it establishes no causal recovery claim. Its scientific array-path
and literature limitations remain in the report; independent utility is unproven.
