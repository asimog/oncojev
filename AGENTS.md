# OncoJev agent map

## What this is

OncoJev is an autonomous computational oncology research system, not a fixed analysis pipeline. Its canonical architecture is [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md); its non-negotiable epistemic rules are [docs/EPISTEMIC_CONSTITUTION.md](docs/EPISTEMIC_CONSTITUTION.md).

The bounded F0–F6 implementation is DONE and preserved in [docs/IMPLEMENTATION_PLAN_COMPLETED_F0_F6.md](docs/IMPLEMENTATION_PLAN_COMPLETED_F0_F6.md). [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) is the sole active H0–H15 phase/status tracker. The complete next-stage target is preserved in [docs/references/NEXT_STAGE_AUTONOMOUS_LAB_REQUIREMENTS.md](docs/references/NEXT_STAGE_AUTONOMOUS_LAB_REQUIREMENTS.md). Target architecture and planned status are not proof of implemented behavior; do not recreate delivered F4–F6 slices or rewrite their historical evidence.

## Read in this order

1. This file and `README.md`.
2. The task-relevant document in `docs/`.
3. `config/` and the smallest relevant package in `src/`.
4. Relevant registry, skill, and test files.
5. `web/` only for UI work.

## Durable boundaries

- Science deterministically measures and is the only evidence-admission authority.
- Jev measures bounded semantic properties; it is not an agent, evidence source, or action authority.
- Reasoner generates possibilities, never evidence.
- Director allocates global scope; Researcher investigates inside one block.
- `BlockManager` is deterministic and owns all deadlines. A Researcher cannot extend one.
- Ledger history is append-only. Dossiers are summaries, not evidence.
- Preserve uncertainty: missing is not zero, source failure is not absence, and Jev failure is not a negative judgment.
- Both Director and Researcher retain bounded Coder and CodeMode. Director scratch is `/work/director`; production source/configuration/policy, peer workspaces, authoritative records and credentials remain inaccessible to modification. Scratch output is not Science, evidence, registry governance or runtime policy.
- Next-stage global Jev tools measure typed semantic properties; they are not a global Jev agent or allocation authority. Global and local candidates, policy versions, scope and stop conditions stay distinct.
- Python owns at most one active fresh Researcher, task/event lifecycle and governed OncoLab transitions. Director cannot mutate active ResearchState or extend its deadline. An explicit program pause creates no fake block and does not establish mission success.
- Database records are authoritative. Research Memory is typed derived context; OncoLab revisions describe institutional capability knowledge; `oncojevlab` is a downstream human-readable projection with no scientific write-back authority.

## Taxonomy

- `src/oncolab/`: the single shared OncoLab Index, its typed contracts, and bundled verification records.
- `src/oncolab/proven/`: durable verification records; they do not automatically promote local work into reusable capability.
- `src/oncolab/labskills/`: block-selected procedural guidance; it is not executable capability code or standing agent context.
- `src/runtime/pydantic_ai/`: the only place Pydantic AI is integrated; `factory.py` is the single deterministic/live composition point.
- `src/persistence/`, `src/application/`, `src/api/`: append-only typed records, application read models, and the read-only API. None may admit evidence.
- `src/evals/`: research-evaluation harness; it reports outcomes and never declares a winning condition.
- `web/`: observability UI only; it renders records and contains no orchestration or admission logic.
- `skills/`: instructions and domain knowledge; they do not execute work.
- A local `JevQuestionSpec` or local capability is not automatically reusable or promoted.
- Planned external capability discovery lives with OncoLab contracts/adapters; GDC files remain source data assets, never individual capability entries. External metadata, semantic suitability, executable routes, validated scopes and reusable promotion are distinct.
- Planned scientific backends live in `src/science/` and share the existing Science validation/admission contract. A per-experiment venv isolates dependencies, not security authority; actual confinement and replay identity must be verified. Never install research dependencies into the application `.venv`.

## `.upstream/` rule

Never begin by recursively reading, searching, indexing, testing, or summarizing `.upstream/`. Do not import it from application code. For a concrete upstream question only: read `.upstream/INDEX.md`, then `.upstream/manifest.yaml`, select one repository and the smallest relevant path, inspect it, then stop.

`docs/IMPLEMENTATION_PLAN.md` is the sole phase/status tracker. Director has global scope; Researcher operates only inside one JevBlock.

## Next-stage implementation discipline

Follow H0–H15 and all G0–G73 requirements in the active plan/reference. Keep one Python/Railway service, one persistent Director, one active fresh Researcher, one durable database, one revisioned OncoLab and one scientific-execution abstraction. No swarms, distributed queues, generic workflow engine, bulk uncontrolled ingestion or speculative vector infrastructure. No cBioPortal/Hugging Face expansion without later explicit approval.

Preserve deterministic high-recall retrieval before bounded Jev comparison, complete native distributions, retained alternatives and deterministic failure fallback. BlockDelta, global hypothesis/contradiction/relation portfolios and program reviews are reference-linked context, never new evidence. Prepared global plans must pin their basis and be revalidated after block completion or material revision.

OncoLab starts from the existing curated catalogue. New immutable institutional revisions must preserve historical context and be pinned by block; accepted updates refresh between blocks without restart. Agents may propose promotion/review/reverification, never unrestricted registry CRUD. Declarative reusable promotion requires explicit versioned governance, scoped validation, measured utility and reproducible dependencies/replay; code-requiring changes become engineering proposals, not live self-modification.

Implement D1–D8 inside their owning H-phase batches, not a separate deferred backlog. Their original triggers are execution/acceptance gates: H4 owns multi-domain generator qualification and hypothesis refinement; H6 deeper representation/schema search; H7 staged retrieval/index/vocabulary expansion; H9 governed promotion; H10 operation-specific science and dependency locking; H14 shared-generator extraction and bounded calibration/Autoresearch. H13 supplies evidence and returns results to those phases before H15. A failed gate records an unmet prerequisite or measured no-change decision there, without claiming the gap is closed. No automatic Jev/self-promotion, speculative universal ladder/generator, uncontrolled ingestion or production self-modification. Scientific operations retain input/design/denominator and execution proof.

Railway deployment must verify durable `ONCOJEV_DB_PATH` storage and actual Coder/scientific confinement. Unavailable target verification is an explicit deployment blocker, never a passing claim or reason to weaken controls. Publication failures in the planned generated `asimog/oncojevlab` repository must not roll back scientific state or block finalization; publisher credentials stay outside Coder/scientific environments.

## Boundaries and done

Backend code belongs in `src/`; UI code belongs in `web/` and is observability only. Keep Pydantic AI integration behind `src/runtime/pydantic_ai/`. Model-provider authentication and scientific-data authentication are separate domains (`src/config/authentication.py`).

For a change to be done: update the nearest durable documentation/configuration if needed, preserve the boundaries above, add a behavior-level test only when it protects a credible regression, run the focused tests and `scripts/check_architecture.py`, and report exact results.
