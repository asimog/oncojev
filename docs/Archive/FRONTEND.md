# Frontend

`web/` is a Vercel-deployable TypeScript/Next.js observability interface. It reads the live read-only API in server components, is not a scientific authority, and contains no orchestration or evidence-admission logic.

## Screens

- `/` mission overview: block count, evidence, dossiers, cycles, records; block list; research memory; epistemic legend.
- `/blocks/[blockId]`: objective, lifecycle, and the block reconstruction ordered by epistemic category.

## Epistemic separation

The interface visually distinguishes six categories, each with its own colour and badge: observation, measurement, scientific evidence, Jev judgment, hypothesis, and agent action. The mapping in `web/lib/categories.ts` is presentation-only — it labels what the backend already recorded and never decides what counts as evidence.

## Data

The UI reads `ONCOJEV_API_URL` (default `http://127.0.0.1:8080`) with uncached server-side requests. The generated `web/data/snapshot.json` remains an offline/build fallback, not the primary runtime data source.

The UI separates transport (`live_api` or `offline_snapshot`), data provenance and
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

Unfinished work is tracked only in the [active plan](../IMPLEMENTATION_PLAN.md).
