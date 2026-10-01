# Frontend

`web/` is a Vercel-deployable TypeScript/Next.js observability interface. It reads the live read-only API in server components, is not a scientific authority, and contains no orchestration or evidence-admission logic.

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
