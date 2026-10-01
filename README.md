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

Python owns the autonomous cycle, requires exactly one new block, and persists records as work occurs. Successful closure requires a recorded Researcher return; `complete_block` requests handoff rather than declaring success. Failed allocated work retains a partial dossier and failed cycle receipt before the error propagates. A Director budget/token truncation produces an incomplete cycle with a separate Director outcome. Run completion never establishes scientific objective attainment, which remains unknown unless independently established. Recovery runs before every service cycle, closes interrupted work without resuming it, and appends corrections for contradictory legacy completion records while preserving their originals.

Deadlines are soft handoff boundaries: new expensive work stops in the reserve window while in-flight work and dossier construction finish. Allocation uses the configured 900-second default, 300–3600-second bounds and 90-second reserve. Zero resource budgets disable work; attempted operations, including failures, consume their own counters. Director and Researcher have separate model/tool budgets, with Reasoner requests charged to the Researcher's allocation and all roles subject to cycle limits. Reported cost is tracked; missing provider cost remains unknown.

Both roles retain Coder and Code Mode in Linux. The Director uses `/work/director` for scratch engineering; each JevBlock has its own `var/workspaces/<block-id>`. Application source and policy are read-only from both coding contexts. Linux Landlock confines native file tools, shell commands and descendants to public application reads and their own writable workspace; peer workspaces, credential files and process environments are inaccessible. Commands receive a scrubbed environment. This path fails closed without Landlock ABI 3 or newer; run `scripts/verify_coder_container.py` in the target Linux image. Scratch results never become scientific evidence without deterministic Science validation and admission.

Only source-bound acquisition measurements or replay-validated sandbox measurements can be admitted as evidence. Agent-provided arrays and generated code may support exploration but cannot cross the Science admission boundary.

Public acquisitions, literature context and sandbox replay requests/outputs are
durable before use. Reconstruction resolves block-owned inputs and reports missing
legacy references. Index and Jev receipts retain provenance, bounded projections,
native semantic distributions and operational failures. Verification records have
typed, hashed execution references and declared scope; exploratory plots and
provided-array statistics remain exploratory. See [capability records](docs/CAPABILITIES.md)
and [Jev receipts](docs/JEV.md) for the replay and uncertainty contracts.

## Development

Configured Director, fresh Researcher, and Reasoner agents send Logfire agent,
tool, and model spans as `oncojev-agents`. Setup runs once per worker process,
before live agents are constructed. Prompt, response, tool argument/result, and
binary content capture are disabled; telemetry is diagnostic data, never evidence.
The integration follows [Pydantic AI's Logfire integration](https://pydantic.dev/docs/ai/integrations/logfire/).

Local runs use the ignored `.logfire/` project credential. This checkout is
connected to [asimog/oncojev (US)](https://logfire-us.pydantic.dev/asimog/oncojev).
Start a cycle or worker with the commands above to generate traces. Deployments
should inject their own project write token as `LOGFIRE_TOKEN` and set
`LOGFIRE_ENVIRONMENT` to the deployment environment. Without a token, export is
optional. Set `LOGFIRE_SEND_TO_LOGFIRE=false` for tests or to disable export.

```bash
uv sync --all-groups
uv run pytest
uv run python scripts/check_architecture.py
```

Web UI: see [docs/FRONTEND.md](docs/FRONTEND.md).

Read [AGENTS.md](AGENTS.md) first. The canonical design is in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md); epistemic rules are in [docs/EPISTEMIC_CONSTITUTION.md](docs/EPISTEMIC_CONSTITUTION.md).
