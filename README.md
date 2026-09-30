# OncoJev

OncoJev is an autonomous computational oncology research system designed to search extremely large biological information spaces.

Its central question is whether high-throughput typed semantic measurement from Jev, dynamically constructed deterministic science, and selective deep reasoning can improve useful discovery per research allocation while preserving candidate recall.

OncoJev is not a fixed GDC or cancer-modality pipeline. A human provides a broad direction; the system determines where to search, what representation and capability are sufficient, what analysis to run, and what deserves further investigation.

## Core architecture

```text
Director
  -> BlockManager
  -> Researcher / JevBlock
     -> Science | Jev | Reasoner | OncoLab Index
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
| `src/` | Python application and runtime implementation |
| `src/oncolab/` | Shared OncoLab Index, typed contracts, and bundled verification records |
| `src/persistence/`, `src/application/`, `src/api/` | Append-only typed records, read models, and the read-only application API |
| `src/evals/` | Deterministic research-evaluation harness and corpus |
| `skills/` | Progressive procedural and domain knowledge |
| `web/` | TypeScript/Next.js observability UI (presentation only) |
| `.upstream/` | Pinned external reference material; never runtime code |

## Running

Deterministic mode needs no credentials. Live mode requires `OPENROUTER_API_KEY` (Director, Researcher, Reasoner) and `TYPESAFE_API_KEY` (Jev); a live request without them degrades to deterministic rather than producing a partial live run. Model-provider credentials are separate from any scientific-data authentication and are never shared with the scientific sandbox.

```bash
uv run python -m src                     # credential-free synthetic vertical slice
uv run python scripts/run_live_cycle.py  # complete live Director -> Researcher cycle (needs keys)
uv run python scripts/export_snapshot.py # regenerate the observability snapshot
```

## First executable slice

The initial slice executes a credential-free synthetic run through deterministic block deadlines, parallel Jev questions, deterministic frontier policy, Science-only evidence admission, Reasoner hypotheses, and a typed Dossier handoff. In Railway's Linux container, both Director and Researcher use Pydantic AI Harness `Coder` plus `CodeMode`: Coder supplies bounded repository tools and a scrubbed command environment, while Code Mode runs typed OncoLab orchestration in Monty. Public GitHub methods execute separately in the credential-free Docker scientific sandbox.

## Development

```bash
uv sync --all-groups
uv run pytest
uv run python scripts/check_architecture.py
```

Web UI: see [docs/FRONTEND.md](docs/FRONTEND.md).

Read [AGENTS.md](AGENTS.md) first. The canonical design is in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md); epistemic rules are in [docs/EPISTEMIC_CONSTITUTION.md](docs/EPISTEMIC_CONSTITUTION.md).
