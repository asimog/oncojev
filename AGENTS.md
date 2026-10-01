# OncoJev agent map

OncoJev is an autonomous computational oncology research system.
Use this file as a navigation map; read only the context needed for the task.

## Read in this order

1. This file and [README.md](README.md).
2. The owning document below, then relevant `config/` and the smallest `src/` package.
3. Relevant registry, skill and behavior-level test files.
4. `web/` only for UI work.

## Documentation ownership

| Document | Owns |
| --- | --- |
| [README](README.md) | Orientation, running and development |
| [Architecture](docs/ARCHITECTURE.md) | System structure and component ownership || [Active implementation plan](docs/IMPLEMENTATION_PLAN.md) | Sole roadmap, phase status, implementation detail and acceptance |
| [Jev](docs/JEV.md) | Current semantic-measurement contract |
| [Capabilities](docs/CAPABILITIES.md) | Current capability and verification semantics |
| [Frontend](docs/FRONTEND.md) | Current UI/read-model contract |
| `src/*/README.md` | Current local implementation |
| `docs/references/` | Ignore unless asked. Preserved source inputs; read only for a concrete provenance question |

One document owns each kind of truth; other documents link to it.
The completed F0-F6 archive is historical evidence, not normal implementation context.
Do not rewrite archives/reference inputs or confuse target architecture with delivery.
Completed phases retain compact evidence in the active plan; Git preserves the detail.


## Repository map

- `src/oncolab/`: shared Index, descriptors, contracts and verification records.
- `src/oncolab/proven/`: durable verification; no automatic reusable promotion.
- `src/oncolab/labskills/`: block-selected procedural guidance, not executable capabilities.
- `src/runtime/pydantic_ai/`: exclusive framework integration; `factory.py` is the composition point.
- `src/block/`, `src/runtime/`, `src/autonomous.py`: deterministic lifecycle and service ownership.
- `src/science/`: controlled execution, validation and evidence admission.
- `src/sources/`: source acquisition and exact input identity.
- `src/memory/`: typed, reference-linked derived context.
- `src/persistence/`, `src/application/`, `src/api/`: append-only records and read-only views; no admission.
- `src/evals/`: outcome evaluation, never mission-success authority.
- `web/`: observability only; no orchestration or admission.
- `skills/`: instructions and domain knowledge; they do not execute work.

## Upstream rule

Never begin by recursively reading, searching, indexing, testing or summarizing `.upstream/`.
Do not import it from application code or install it as application dependencies.
For a concrete upstream question only: read `.upstream/INDEX.md`, then
`.upstream/manifest.yaml`, select one repository and the smallest relevant path, inspect it, then stop.

## Implementation discipline

Follow the active plan's phase dependencies,
Update the owning documentation only when behavior changes; do not copy roadmap detail into local READMEs.
A planned behavior is described in detail only in IMPLEMENTATION_PLAN.md. Other documents may state the durable architectural boundary and link to the plan, but must not duplicate phase-specific implementation detail.
Update only the authoritative document for the changed fact and any current-state document made factually wrong by the implementation. Do not propagate the same explanation across multiple doc

## Verification and done

Use `rg`/`rg --files`; preserve unrelated changes and checkout boundaries.
Add behavior-level tests only for credible regressions, at the owning boundary.
Run focused checks, `scripts/check_architecture.py` and `git diff --check`.
For documentation-only work, validate links, scope, preservation and plan traceability.
Report exact results and distinguish local proof, live connectivity, utility and deployed confinement.
