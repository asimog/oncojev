# OncoJev

OncoJev is an autonomous computational oncology research system designed to search extremely large biological information spaces.

Its central question is whether high-throughput typed semantic measurement from Jev, dynamically constructed deterministic science, and selective deep reasoning can improve useful discovery per research allocation while preserving candidate recall.

OncoJev is not a fixed GDC or cancer-modality pipeline. A human provides a broad direction; the system determines where to search, what representation and capability are sufficient, what analysis to run, and what deserves further investigation.

## Core architecture

```text
Director
  -> BlockManager
  -> Researcher / JevBlock
     -> Science | Jev | Reasoner | capability registries
  -> Evidence + Ledger + Dossier
  -> Director
```

## Intelligence boundaries

```text
Science measures reality.
Jev measures bounded semantic properties.
Reasoner generates possibilities.
Researcher chooses local investigation.
Director allocates global research scope.
Python controls lifecycle, evidence admission, and frontier policy.
```

Only reproducible deterministic measurements admitted by Science become `ScientificEvidence`. Jev, Reasoner, generated code, and Dossiers never directly create evidence.

## Repository map

| Location | Purpose |
| --- | --- |
| `src/oncojev/` | Python application and runtime implementation |
| `registries/capabilities/` | Deterministic executable scientific capabilities |
| `registries/jev/` | Evaluated reusable semantic measurements |
| `skills/` | Progressive procedural and domain knowledge |
| `evals/` | Evaluation corpora and regressions |
| `web/` | Future TypeScript/Next.js observability UI |
| `.upstream/` | Pinned external reference material; never runtime code |

## First executable slice

The initial slice executes a credential-free synthetic run through independent Director and Researcher agents, deterministic block deadlines, parallel Jev questions, deterministic frontier policy, Science-only evidence admission, Reasoner hypotheses, and a typed Dossier handoff. It intentionally does not yet provide a database, API, GDC client, or frontend.

## Development

```bash
uv sync --all-groups
uv run pytest
uv run python scripts/check_architecture.py
```

Read [AGENTS.md](AGENTS.md) first. The canonical design is in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md); epistemic rules are in [docs/EPISTEMIC_CONSTITUTION.md](docs/EPISTEMIC_CONSTITUTION.md).
