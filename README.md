# OncoJev

OncoJev is an autonomous computational oncology research system designed to search extremely large biological information spaces.

Its central question is whether high-throughput typed semantic measurement from Jev, dynamically constructed deterministic science, and selective deep reasoning can improve useful discovery per research allocation while preserving candidate recall.

OncoJev is not a fixed GDC or cancer-modality pipeline. A human provides a broad direction; the system determines where to search, what representation and capability are sufficient, what analysis to run, and what deserves further investigation.

The bounded F0–F6 stage is **DONE**; its full historical plan and verification limits are preserved in [the completed plan](docs/IMPLEMENTATION_PLAN_COMPLETED_F0_F6.md). The [active next-stage plan](docs/IMPLEMENTATION_PLAN.md) expands the [complete supplied requirements](docs/references/NEXT_STAGE_AUTONOMOUS_LAB_REQUIREMENTS.md) into H0–H15. Next-stage behavior below is a target, not a claim of delivery.

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

## Delivered autonomous runtime

Python owns the autonomous cycle, requires exactly one new block, and persists records as work occurs. Successful closure requires a recorded Researcher return; `complete_block` requests handoff rather than declaring success. Failed allocated work retains a partial dossier and failed cycle receipt before the error propagates. A Director budget/token truncation produces an incomplete cycle with a separate Director outcome. Run completion never establishes scientific objective attainment, which remains unknown unless independently established. Recovery runs before every service cycle, closes interrupted work without resuming it, and appends corrections for contradictory legacy completion records while preserving their originals.

Deadlines are soft handoff boundaries: new expensive work stops in the reserve window while in-flight work and dossier construction finish. Allocation uses the configured 900-second default, 300–3600-second bounds and 90-second reserve. Zero resource budgets disable work; attempted operations, including failures, consume their own counters. Director and Researcher have separate model/tool budgets, with Reasoner requests charged to the Researcher's allocation and all roles subject to cycle limits. Reported cost is tracked; missing provider cost remains unknown.

Both roles retain Coder and Code Mode in Linux. The Director uses `/work/director` for scratch engineering; each JevBlock has its own `var/workspaces/<block-id>`. Application source and policy are read-only from both coding contexts. Linux Landlock confines native file tools, shell commands and descendants to public application reads and their own writable workspace; peer workspaces, credential files and process environments are inaccessible. Commands receive a scrubbed environment. This path fails closed without Landlock ABI 3 or newer; run `scripts/verify_coder_container.py` in the target Linux image. Scratch results never become scientific evidence without deterministic Science validation and admission.

H1 expands the Director's instructions to global memory synthesis, uncertainty,
duplication/contradiction review, diversification/dependencies, capability gaps,
failure/resource triage and non-authoritative engineering proposals. Its
`inspect_director_resources` tool reads independent Director, aggregate cycle and
memory-semantic allowances before allocation or during a block, including
configured cost bounds and reported-cost completeness. Researcher retains local
scientific choices. Non-blocking supervision, durable global portfolios, governed
proposals and a zero-block program pause await their owning H phases.

Only source-bound acquisition measurements or replay-validated sandbox measurements can be admitted as evidence. Agent-provided arrays and generated code may support exploration but cannot cross the Science admission boundary.

Public acquisitions, literature context and sandbox replay requests/outputs are
durable before use. Reconstruction resolves block-owned inputs and reports missing
legacy references. Index and Jev receipts retain provenance, bounded projections,
native semantic distributions and operational failures. Verification records have
typed, hashed execution references and declared scope; exploratory plots and
provided-array statistics remain exploratory. See [capability records](docs/CAPABILITIES.md)
and [Jev receipts](docs/JEV.md) for the replay and uncertainty contracts.

Typed cross-cycle memory retrieves relevant recorded outcomes and supplies bounded
start packets with references, failures, uncertainties and candidate directions.
The service retains one Director Agent and no prior message history; Researcher
instances, state, skills and budgets remain fresh. See [research memory](src/memory/README.md).

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

Workspace retention runs between service cycles under `retention` in
`config/runtime.yaml`. It archives exact closed-block scratch bytes to durable
SQLite before cleanup; active/unknown/unresolved blocks and failed exports are
excluded. Defaults: seven days, 20 workspaces, 100 MB each. Director scratch is
excluded. The ledger, source inputs and replay records survive cleanup.

OncoLab progressive retrieval uses `oncolab.candidate_k` separately from the
per-response `search_k`. Director memory semantics has separate call/question/
byte/time limits. Unused `jev.search_k`, `jev.candidate_k`,
`director.semantic_frontier_k`, empty sources configuration and unused aliases
were removed; configuration remains strict.

The web fallback is explicitly an offline synthetic fixture with zero admitted
evidence. API availability does not certify scientific validity or completion.
See the phase delivery records in [the completed F0–F6 plan](docs/IMPLEMENTATION_PLAN_COMPLETED_F0_F6.md) for scoped checks
and unresolved scientific/semantic utility and dependency-lock limitations.

## Next-stage target

The target remains one Python/Railway service with a persistent Director and at most one active fresh Researcher. Python will own a non-blocking Researcher task while the Director receives bounded event-driven turns for global memory, hypotheses, contradictions, capability gaps and program review. Both roles retain Coder and CodeMode; Director scratch remains bounded to `/work/director`. The Director will choose a future block from a retained global semantic frontier or truthfully pause, without changing active local state or deadlines.

OncoLab will preserve its curated seed and add immutable institutional revisions, block pins and governed between-block updates. Capability discovery will expand on demand through bio.tools and bounded GitHub/Bioconda/Bioconductor metadata; GDC file results remain data assets. Actual retrievable representations extend the existing frontier. Suitability never grants execution authority, and a successful method run alone never earns reusable promotion.

Scientific execution will share one validation/replay contract across an optional Docker backend and a Railway-compatible confined local Python backend with per-experiment dependencies. Reusable external methods require exact environment/dependency identity and fresh replay. Durable database storage and actual deployed confinement remain acceptance gates; a venv is not a security boundary.

The separate generated `asimog/oncojevlab` repository will present deterministic, reference-linked laboratory history. Database records remain authoritative, typed Research Memory informs the Director, and publication failure cannot damage scientific state. D1–D8 are integrated directly into the active H phases as implementation/evaluation batches, with their original triggers, concrete proof and phase-owned gate outcomes. The canonical [architecture](docs/ARCHITECTURE.md) distinguishes these planned changes from the delivered runtime.
