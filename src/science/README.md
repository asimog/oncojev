# Scientific execution

Delivered F0–F6 execution evidence remains in the
[completed plan](../../docs/IMPLEMENTATION_PLAN_COMPLETED_F0_F6.md). The
[active H0–H15 plan](../../docs/IMPLEMENTATION_PLAN.md) tracks the next-stage
target; the final section below is planned work.

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

## Next-stage target: a portable scientific-execution contract

**Planned in H10 and deployment verification in H11.** The current external
scientific executor is `DockerScientificSandbox`, with dependencies explicitly
unlocked. Preserve its retained-input, replay, validation and admission contracts
while introducing one backend abstraction. Railway uses a local per-experiment
Python venv executor without Docker-in-Docker; the Docker backend may remain
for local verification against the same canonical measurement-candidate contract.
Historical Docker receipts preserve their original backend and limitations.

Each experiment owns a repository, venv, inputs and outputs under its block
workspace. Dependencies never install into the application `.venv` or leak into a
fresh Researcher. A venv is dependency isolation, not a security boundary. The
executor must independently verify confinement for public read-only application
code/policy, peer workspaces, credentials and read-only inputs, scrub descendant
environments, enforce resource/deadline budgets and verify denied network access
for tests/replay/execution. Installation/acquisition access is bounded separately.
If the target runtime cannot enforce required isolation, execution is explicitly
blocked rather than silently weakened. Linux Coder confinement and external
scientific execution each require their own deployment proof.

Retain repository URL and resolved commit, package/version, application/runtime
version, backend, Python/OS/base environment, dependency-resolution identity,
install/test/execute commands, owned inputs and hashes, parameters, output hashes,
validator version, first run and replay run plus limitations. A fixed commit alone
does not establish reproducibility. H10 activates D8 for reusable external
methods: prefer repository lockfiles, pinned requirements or a reproducibly
resolved dependency set; retain freeze/hash for audit. A freeze alone does not
prove repeatable installation, and irreproducible dependencies block unsupported
reusable promotion. H9 governance can accept only declarations the actual verified
executor supports, with applicable H11 deployment confinement verified;
code-requiring reuse produces an engineering proposal.

Initial external execution supports compatible Python repositories. R, Conda,
CUDA, Docker-required methods and system daemons remain unsupported unless
separately implemented and verified. Discovery metadata about those ecosystems
cannot change that boundary. GDC representation discovery in H6 does not itself
implement new scientific analyses. H10's integrated D7 batch qualifies actual
needs, inputs, designs and denominators for MAF/VCF/expression, static GDC joins,
TMB, survival and approved source families, then implements and proves selected
operations through execution/replay/Science admission. Unmet prerequisites stay
explicit in H10; file discovery alone cannot complete an operation.

The evidence path remains a declared experiment with exact software/input
identity, controlled execution, replay/validation, a typed candidate, Science
validation and explicit admission. Coder/shell output, model prose, semantic
judgments, plots and notebook files remain exploratory. Retention extends F6
archive-before-cleanup to experiment scratch while preserving required inputs,
artifacts, evidence, receipt/dependency identity and ledger history. Missing
historical bytes remain unreplayable unless exactly and verifiably recovered.

The [complete supplied requirements](../../docs/references/NEXT_STAGE_AUTONOMOUS_LAB_REQUIREMENTS.md)
preserve G38–G42, G55–G58 and G68 requirements; these targets are not claims that
the Railway backend or stronger dependency locking is already delivered.
