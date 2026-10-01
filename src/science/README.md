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

An optional retained-hypothesis test plan adds an exploratory directional effect
bound, explicit multiplicity family and Bonferroni simultaneous uncertainty. Pearson
uses the [SciPy Fisher interval](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html);
OLS uses its [slope t interval](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.conf_int.html).
Support/contradiction compares the entire directional interval with the declared
effect bound; overlapping uncertainty stays inconclusive. These are conditional
association-model outcomes. Designs/independence are declared, and adaptive
exploration is not preregistered confirmation. Non-significance never establishes
absence. Historical unplanned v1 outputs and analysis identities are preserved.

ScientificAttempt records retain analysis/hypothesis/input basis before execution
and a separate measurement-backed or invalid/operational terminal state. Resource
and interruption failures remain attempts. The test protocol is source-paired-test-v1;
replay does not establish independent biological replication.

Exact scientific bytes remain in append-only ScientificArtifact records.
External sandbox requests retain copies and validate their identities; execution
mounts are read-only and network-disabled. The local backend accepts declared
retained wheel hashes; exploratory Docker installation is not complete reusable
dependency qualification.
`verify_scientific_artifacts.py` proves only Linux input/root mount immutability.

Presentation keeps explicit descriptive/associative/exploratory labels; undeclared
legacy or sandbox interpretation is unclassified. GDC source-paired analyses
require top-level endpoint entity IDs and compatible units. File/project rows
cannot be relabelled as patient denominators; joins require a separate contract.

Backend portability, scientific expansion and reusable dependency qualification belong to the [active plan](../../docs/IMPLEMENTATION_PLAN.md) (H10/H11).
