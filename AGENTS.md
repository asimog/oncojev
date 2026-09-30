# OncoJev agent map

## What this is

OncoJev is an autonomous computational oncology research system, not a fixed analysis pipeline. Its canonical architecture is [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md); its non-negotiable epistemic rules are [docs/EPISTEMIC_CONSTITUTION.md](docs/EPISTEMIC_CONSTITUTION.md).

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

## Taxonomy

- `src/oncolab/`: the single shared OncoLab Index, its typed contracts, and bundled verification records.
- `src/oncolab/proven/`: durable verification records; they do not automatically promote local work into reusable capability.
- `src/oncolab/labskills/`: block-selected procedural guidance; it is not executable capability code or standing agent context.
- `skills/`: instructions and domain knowledge; they do not execute work.
- A local `JevQuestionSpec` or local capability is not automatically reusable or promoted.

## `.upstream/` rule

Never begin by recursively reading, searching, indexing, testing, or summarizing `.upstream/`. Do not import it from application code. For a concrete upstream question only: read `.upstream/INDEX.md`, then `.upstream/manifest.yaml`, select one repository and the smallest relevant path, inspect it, then stop.

`docs/IMPLEMENTATION_PLAN.md` is the sole phase/status tracker. Director has global scope; Researcher operates only inside one JevBlock.

## Boundaries and done

Backend code belongs in `src/`; future UI code belongs in `web/` and is observability only. Keep Pydantic AI integration behind `src/runtime/pydantic_ai/`.

For a change to be done: update the nearest durable documentation/configuration if needed, preserve the boundaries above, add a behavior-level test only when it protects a credible regression, run the focused tests and `scripts/check_architecture.py`, and report exact results.
