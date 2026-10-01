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

The application runs autonomously in live mode. It requires `OPENROUTER_API_KEY` (Director, Researcher, Reasoner) and `TYPESAFE_API_KEY` (Jev) and fails closed when either is missing. Deterministic clients remain explicit test fixtures; they are not an autonomous fallback. Model-provider credentials are omitted from Coder child-command environments and the scientific sandbox.

```bash
uv run python -m src cycle               # one durable autonomous Director -> Researcher cycle
uv run python -m src serve               # autonomous worker plus read-only API
uv run python scripts/run_live_cycle.py  # one live cycle persisted under var/
uv run python scripts/export_snapshot.py # regenerate the offline UI fallback
```

## Autonomous runtime

Python owns the autonomous cycle, requires exactly one new block, persists records as work occurs, and always produces a terminal dossier or a recorded failure. Deadlines are soft handoff boundaries: new expensive work stops in the reserve window while in-flight work and dossier construction finish. In Railway's Linux container, the Director has a writable repository-root Coder workspace and unrestricted shell; every JevBlock receives a fresh writable Researcher workspace under `var/workspaces/`. Code Mode exposes the typed OncoLab tools alongside those coding capabilities.

Only source-bound acquisition measurements or replay-validated sandbox measurements can be admitted as evidence. Agent-provided arrays and generated code may support exploration but cannot cross the Science admission boundary.

## Development

```bash
uv sync --all-groups
uv run pytest
uv run python scripts/check_architecture.py
```

Web UI: see [docs/FRONTEND.md](docs/FRONTEND.md).

Read [AGENTS.md](AGENTS.md) first. The canonical design is in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md); epistemic rules are in [docs/EPISTEMIC_CONSTITUTION.md](docs/EPISTEMIC_CONSTITUTION.md).
