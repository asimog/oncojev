# Scientific execution

`ScienceExecutor` executes typed deterministic analyses; `admit_scientific_evidence`
is the admission boundary. External execution supports Docker and a fail-closed
Linux x86_64 local-venv backend selected by configuration. Both retain immutable
public GitHub commits, exact inputs, command/output identities and replay receipts;
typed candidates require explicit validation before admission. Local experiments
use fresh Python environments, offline retained wheels, Landlock read-only inputs,
scrubbed environments and seccomp single-process execution with no networking.
Tests/execution write only bounded inherited stdout/stderr. Source builds,
subprocesses, threads and filesystem output are unsupported on this backend.
Fresh qualification and scientific fidelity remain separate governance gates.

Science alone admits evidence. Stored-source summaries count valid, absent, null,
invalid-type and nonfinite classifications; undefined means/SD stay null with a
reason. Nonfinite structured content cannot obtain a canonical acquisition hash.
A record count is a response-row count, never a patient denominator.

Source-paired-v1 supports Pearson and simple OLS for complete unique-entity rows
from one owned acquisition. Fields, entity unit, population, design, estimand,
transformations and exclusions are retained. Unsupported joins/covariates and
constant/undersized data fail explicitly. Results are associative and carry
assumption/coverage limits, not causal claims. Stable analysis identity excludes
run/acquisition UUIDs; explicit replication ID distinguishes declared reruns from
duplicate admission. Declared replication is not proof of independence.

Exact scientific bytes remain in immutable SQLite ScientificArtifact records.
External sandbox requests retain copies and validate their identities; execution
mounts are read-only and network-disabled. Installation dependencies remain
unlocked: an immutable image is not a deterministic dependency-install guarantee.
`verify_scientific_artifacts.py` proves only Linux input/root mount immutability.

Presentation keeps explicit descriptive/associative/exploratory labels; undeclared
legacy or sandbox interpretation is unclassified. GDC source-paired analyses
require top-level endpoint entity IDs and compatible units. File/project rows
cannot be relabelled as patient denominators; joins require a separate contract.

Backend portability, scientific expansion and reusable dependency qualification belong to the [active plan](../../docs/IMPLEMENTATION_PLAN.md) (H10/H11).
