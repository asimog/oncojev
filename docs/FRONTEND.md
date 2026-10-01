# Frontend

`web/` is a Vercel-deployable TypeScript/Next.js observability interface. It reads the live read-only API in server components, is not a scientific authority, and contains no orchestration or evidence-admission logic.

This document describes delivered F6 presentation and the planned next-stage
read-model additions separately. [The active implementation plan](IMPLEMENTATION_PLAN.md)
owns H0–H15 status; [the completed F0–F6 plan](IMPLEMENTATION_PLAN_COMPLETED_F0_F6.md)
retains historical verification. Full next-stage requirements are preserved in
[the reference document](references/NEXT_STAGE_AUTONOMOUS_LAB_REQUIREMENTS.md).

## Screens

- `/` mission overview: block count, evidence, dossiers, cycles, records; block list; research memory; epistemic legend.
- `/blocks/[blockId]`: objective, lifecycle, and the block reconstruction ordered by epistemic category.

## Epistemic separation

The interface visually distinguishes six categories, each with its own colour and badge: observation, measurement, scientific evidence, Jev judgment, hypothesis, and agent action. The mapping in `web/lib/categories.ts` is presentation-only — it labels what the backend already recorded and never decides what counts as evidence.

## Data

The UI reads `ONCOJEV_API_URL` (default `http://127.0.0.1:8080`) with uncached server-side requests. The generated `web/data/snapshot.json` remains an offline/build fallback, not the primary runtime data source.

## Development

```bash
cd web
npm install
npm run build
```

Regenerate the snapshot after backend changes:

```bash
uv run python scripts/export_snapshot.py
```

F6 separates transport (`live_api` or `offline_snapshot`), data provenance and
recorded execution mode. Live API pages do not inherit fixture evaluation
conditions. Offline fallback displays its synthetic/no-live-research limitation;
synthetic measurements have no evidence-admission authority. Lifecycle and run
outcomes, unknown objective attainment, operational failures, source counters,
statement support, interpretation and scientific limits are shown explicitly.
Historical completion corrections come from effective backend read models.

The frontend regression renders the real async pages against controlled API
responses and fallback using the installed TypeScript/React environment. Web
build and browser checks are separate from Python source-bound execution tests.

Read models omit retained artifact byte payloads while preserving identities and an explicit omission flag; durable scientific input bytes remain unchanged.

## Planned next-stage observability

The H0–H15 target adds durable records before presentation. Until their backend
contracts and read models are implemented, they are planned behavior and must
not be shown as delivered features or successful live research. `web/` continues
to render recorded state only; it gains no Director, Researcher, Jev, capability
governance, scientific execution or evidence-admission authority.

| Planned backend state | Presentation contract |
| --- | --- |
| Event-driven single-Researcher lifecycle (H2–H3) | Distinguish active Researcher work, bounded concurrent Director planning, terminal block outcome and recovery; one active block does not imply allocation or scientific success |
| Director program outcomes (H3) | Show `ALLOCATE`, `PAUSE`, `NO_MATERIAL_NEXT_BLOCK` or `NEEDS_HUMAN_DIRECTION` with recorded rationale; a pause creates no dummy block and does not establish mission attainment |
| BlockDelta and prepared-frontier basis (H3) | Render reference-linked recorded changes, missing references and revalidation status; expose stale basis rather than display a prepared plan as an authorized next block |
| Global frontier, hypotheses, cross-block relations, contradictions and program review (H4) | Label semantic context, hypotheses and Director decisions separately from admitted evidence; preserve both conflicting originals, uncertainty, independent replication and operational failures |
| Dynamic OncoLab institutional state (H5/H9) | Render immutable revision identity, the block's pinned revision, verification/failure/demand history and proposal/governance status; discovery or a receipt is not promotion |
| External capability and GDC data-asset discovery (H6–H8) | Keep data assets separate from executable capabilities and retain access/licence, coverage, provenance and failure limitations; public metadata does not imply downloadable controlled data |
| Execution and Railway verification (H10–H11) | Show recorded backend/environment identity and verified or blocked confinement status; elapsed execution, retained artifacts and deployment availability do not certify scientific validity |
| `oncojevlab` export/publication (H12) | Distinguish generated export, publication success, publication failure and missing external setup; link the readable projection while the database remains authoritative |

The separate `asimog/oncojevlab` repository is downstream observability produced
by a deterministic exporter from typed persisted records. Publication failure
must remain an operational status and cannot erase evidence, reverse terminal
block closure or replace database truth. Offline snapshots continue to display
their transport, execution mode, provenance and limitations explicitly. Unknown
or absent new fields remain unknown; frontend defaults must not invent outcomes,
revision acceptance, semantic judgments or evidence.

Any later UI change should verify the rendered lifecycle, epistemic categories,
live/offline separation and export-failure state against controlled backend read
models, with the web build and browser checks recorded separately. This planning
update changes no UI code, routes or API behavior.
