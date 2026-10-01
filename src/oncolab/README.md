# OncoLab Index

This document describes the delivered index. F0–F6 delivery records remain in the
[completed plan](../../docs/IMPLEMENTATION_PLAN_COMPLETED_F0_F6.md); next-stage
status belongs to the [active H0–H15 plan](../../docs/IMPLEMENTATION_PLAN.md).

`OncoLabIndex` is the only OncoJev domain index used by Director and Researcher.
It holds bounded, typed planning descriptors and loads durable verified-execution
records from `proven/verified-executions.yaml`. The agents receive one bounded
descriptor plus its verification summary through `describe_oncolab`; they do
not read YAML files directly. A descriptor is not execution authority, and a
proven record does not automatically promote local work to reusable capability.

OncoLab is deliberately separate from Pydantic AI's framework capabilities and
tools. Framework integration remains under `src/runtime/pydantic_ai/`.

`labskills/` contains selected procedural guidance for Researcher blocks. Skills
can guide use of the index and typed wrappers, but never execute work or create
evidence.

Jev descriptors remain distinct from local `JevQuestionSpec`s. A reusable Jev
capability requires reproducible evaluation evidence.

Verification records use typed, integrity-bound execution references and a declared
scope/outcome. Bundled artifacts must live under `proven/artifacts/`; durable record
references also identify their owning block. Factory composition loads resolvable
durable receipts alongside bundles and deduplicates verification identities.
Historical artifacts explicitly disclose missing inputs. Execution observation,
validated measurement and exploratory artifact creation do not promote a family
or a local method into reusable capability.

Progressive search returns compact cards with a contract hash and explicit
snapshot-bound continuation. The response cap is separate from the configured
candidate budget. Zero lexical overlap stays reachable on later pages; lexical
ranking is not a suitability judgment. Describe selected IDs to obtain contracts
and declared routes. Execution checks distinguish metadata-only, access, missing
inputs and callable operation prerequisites. Library installation is not authority.

## Next-stage target: institutional state and governed revisions

**Planned in H5–H9, with execution readiness gated by H10 and applicable H11 deployment proof.** Preserve the static
catalogue and current F4 retrieval/verification mechanisms as the seed. Add durable
immutable OncoLab revisions, observed execution scopes and limitations, failure,
usage, demand and suitability history, capability gaps and governed proposals.
Each block pins its revision plus application/runtime version. Old revisions
remain reconstructable; normal accepted changes refresh between blocks without
worker restart.

Keep curated capabilities, external capability candidates and scientific data
assets as distinct discovery surfaces. bio.tools/GitHub/Bioconda/Bioconductor
metadata is non-authoritative. EDAM IDs/terms support bounded normalization;
bulk registry/ontology ingestion is not the initial design. GDC file results
belong to source/data-asset models; a file UUID cannot become an OncoLab capability.
Source outages remain operational failures, never scientific negatives.

Selection retains deterministic retrieval, compact cards, contract expansion and
route/input/runtime/access checks before bounded Jev suitability. Jev cannot
grant execution authority. On-demand external discovery follows an unmet need;
it must retain receipt/query/filter/continuation/time/content identity and
omission/failure context without claiming immutable external snapshots.

Python governance owns accepted promotion/review/reverification/retirement
transitions and appends a revision. One execution cannot auto-promote. A reusable
declarative method needs repeated demonstrated need, measured utility, validated
scope, failure/limitation history, exact executable contracts and reproducible
software/dependencies. If reuse needs application code, a parser, source adapter,
runtime route or admission change, produce an engineering proposal instead.
Accepted executable reuse requires H10's environment/replay identity and H11's
applicable actual deployment confinement; local proof does not certify Railway.
Preserve unknown licence/access facts and refuse unsupported reusable status.
Unsupported automatic Jev/self-promotion cannot pass governance. D1 promotion
and D6 measured search expansion are integrated batches in H9/H7; H4/H14 qualify
shared candidate-generation contracts. H13 evidence returns to those owners,
with unmet gates recorded there rather than in a separate deferred backlog.

See [capability contracts and next-stage boundaries](../../docs/CAPABILITIES.md)
and [the complete supplied requirements](../../docs/references/NEXT_STAGE_AUTONOMOUS_LAB_REQUIREMENTS.md)
for G17–G37, G55–G58 and acceptance details. Dynamic revisions, external adapters
and promotion are targets; their presence in documentation is not execution proof.
