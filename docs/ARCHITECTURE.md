# OncoJev architecture

## Purpose

OncoJev searches large biological information spaces under bounded research allocations. It is a research system, not a predefined GDC workflow or a specialist-agent swarm.

## Two architectural scopes

```mermaid
flowchart TD
  H[Human direction] --> D[Director]
  D --> C[Control]
  D --> CI[OncoLab Index]
  D --> RM[Research Memory]
  C --> B[BlockManager]
  B --> JB[JevBlock]
  JB --> R[Researcher]
  R --> CI
  R --> A[Acquisition and deterministic Science]
  R --> RS[Deterministic ResearchState]
  R --> J[Jev projections and Jev]
  R --> F[Local FrontierPolicy]
  R --> X[Reasoner]
  R --> SS[Optional sandbox and visualization]
  R --> DOS[Block dossier and next-block proposals]
  A --> E[ScientificEvidence]
  E --> RM
  DOS --> RM
```

The global scope contains only Director Control, the OncoLab Index, and Research Memory. Control includes global allocation and deterministic block lifecycle. Director and Researcher are separate Pydantic AI agents. `BlockManager` is plain deterministic Python, owns hard deadlines and budgets, and is the only lifecycle authority.

Each JevBlock is the Researcher’s local scope. It contains capability discovery/use, acquisition, deterministic science, deterministic ResearchState, Jev projections/measurement, local deterministic frontier policy, Reasoner, optional sandboxed software, visualization, and dossier construction. There are no separate global Science, source, Jev, visualization, or sandbox planes.

## Agent harness

In the Railway/Linux deployment, both agents compose Pydantic AI Harness `Coder` with `CodeMode`. Coder supplies repository tools in the non-root container workspace with a scrubbed child-command environment; Code Mode runs typed role-specific contract orchestration in Monty. Coder tools are not a path around typed acquisition, Science, evidence admission, or the credential-free scientific sandbox. Windows local development retains Monty Code Mode because Pydantic AI's `LocalWorkspace` backend is POSIX-only; validate Coder behavior through the Docker image. The Director allocates, inspects, and launches bounded JevBlocks. The Researcher operates block-local facilities. There is no deadline-extension tool.

Every block begins with a fresh immutable `ResearchState`. Public-provider records are reduced into typed summaries before state update. Jev receives only a deterministic JSON projection of that state, identified by a content-derived projection ID; it never receives provider JSON, dataframes, or shell output. Proven executions are bundled under `src/oncolab/proven/` and loaded by the shared OncoLab Index; this does not promote a broad OncoLab descriptor into a reusable capability.

Researcher procedural skills are selected locally and afresh per JevBlock. They are short guidance, not executable capabilities or standing prompt context. When a missing method requires public GitHub software, the repository is resolved to a commit and run only in a credential-free Docker sandbox. The sandbox captures command, environment, input/output hashes, and exit status; raw stdout and files cannot become evidence.

## Boundaries

| Concept | Responsibility | Never does |
| --- | --- | --- |
| Science | Deterministic block-local source, cohort, transformation, statistics, validation | Semantic judgment or global allocation |
| Jev | Block-local typed semantic measurements after retrieval and before frontier policy | Evidence admission or agent control |
| Reasoner | Block-local hypotheses, interpretations, possible tests | Evidence admission |
| Researcher | Local investigation and facilities inside one JevBlock | Extend its block or allocate new global scope |
| Director | Global Control, OncoLab Index search, and Research Memory use | Direct science, source, Jev, visualization, or sandbox operation |
| Python policy | Lifecycle, provenance, admission, composition, frontier | Treat uncertainty as a negative result |

## Search policy

Inside a JevBlock, the canonical pattern is deterministic candidate generation, bounded Jev questions, complete distributions, deterministic local frontier policy, then Researcher action or a proposal to Director. A Choice winner is not suitability proof; preserve a beam when ambiguity has material recall risk. Jev failures remain operational failures.

## Evolution

Scientific and Jev capabilities begin local. Only repeat use, validation, provenance, and evaluation justify a reusable registry entry. Skills explain when and how to approach work; registries contain contracts for executable or evaluated artifacts.

## Deferred until a vertical slice needs them

Persistence/API, GDC, scientific sandboxing, capability catalogues, evaluation corpora, and the Next.js observability UI are intentionally deferred. The TypeSafe adapter is present behind `jev.client`; the synthetic vertical slice uses its deterministic test implementation so no credential is required. See [UPSTREAM.md](UPSTREAM.md) and [JEV.md](JEV.md).
