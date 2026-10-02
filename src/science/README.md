# Scientific execution

`ScienceExecutor` executes typed deterministic analyses; `admit_scientific_evidence`
is the admission boundary. External execution defaults to the fail-closed Linux x86_64 local-venv backend.
The historical Docker backend and its receipts remain compatible. Both retain immutable
public GitHub commits, exact inputs, command/output identities and replay receipts;
typed candidates require explicit validation before admission. Local experiments
use fresh Python package environments referencing the exact base interpreter
read-only, offline retained wheels, Landlock read-only inputs,
scrubbed environments and seccomp single-process execution with no networking.
The application interpreter applies confinement before executing any fresh
environment entry point, including one replaced during installation.
Archive/bootstrap/install/test/replay use the shared cgroup/tmpfs governor and
retain per-phase resource/cleanup receipts. Retained scratch reduces disk allowance;
installation has a bounded temporary directory. Inputs/repository stay read-only.
Public body chunks are charged before rejection without response decompression or
environment proxies. New phases use the remaining wall allowance; in-flight reads
retain a bounded socket timeout. Failed usage survives reservation/budget rejection.
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

`source-followup-v1` freezes a same-method GDC case-paired follow-up, its meaningful
effect bound, explicit multiplicity family, exact query, expected discrimination
and alternative explanations. The runtime retains the declaration before accessing
new confirmation inputs and checks earlier case-level value exposure across queries.
Canonical case UUIDs and complete retained queries distinguish observed disjointness
from overlap or unknown identity/coverage. Designs and population/variable compatibility
remain declared; hidden linkage, confounding and external leakage are not ruled out.

Comparisons retain both effect intervals. Recovery of the directional minimum effect
is model-conditional replication; a confidently reversed effect is contradictory.
An interval wholly within the declared negligible-effect bounds is not replicated;
wide intervals remain inconclusive, including non-significance. Same-participant
changes yield consistent or sensitivity-dependent results, never independent
replication. Invalid/operational outcomes stay distinct, and comparisons cannot
change original measurements or admit evidence. This supports case-paired Pearson
and simple OLS contracts, not biological corroboration or other operation families.
`run_source_analysis` returns the retained comparison alongside the measurement
when a follow-up is requested, so the Researcher can use its outcome immediately.

Exact scientific bytes remain in append-only ScientificArtifact records.
`representation.py` parses explicitly identified GDC augmented STAR Counts TSVs
into source-bound selected-gene records. Counts and normalized expression retain
separate units; exact gene versions and missing genes survive. This is a single-file
gene summary, with no inferred sample/case linkage, cohort matrix or biological
validation. Its parse receipt is distinct from a measurement or evidence admission.
External sandbox requests retain copies and validate their identities; execution
mounts are read-only and network-disabled. The local backend accepts declared
retained wheel hashes; exploratory Docker installation is not complete reusable
dependency qualification.
`verify_scientific_artifacts.py` proves only Linux input/root mount immutability.

Presentation keeps explicit descriptive/associative/exploratory labels; undeclared
legacy or sandbox interpretation is unclassified. GDC source-paired analyses
require top-level endpoint entity IDs and compatible units. File/project rows
cannot be relabelled as patient denominators; joins require a separate contract.

Backend portability, scientific expansion and reusable dependency qualification belong to the [active plan](../../docs/IMPLEMENTATION_PLAN.md).
