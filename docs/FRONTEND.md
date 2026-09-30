# Frontend

`web/` is a Vercel-deployable TypeScript/Next.js observability interface. It is not a scientific authority, does not store scientific state, and contains no orchestration or evidence-admission logic.

## Screens

- `/` mission overview: block count, evidence, dossiers, cycles, records; block list; research memory; epistemic legend.
- `/blocks/[blockId]`: objective, lifecycle, and the block reconstruction ordered by epistemic category.

## Epistemic separation

The interface visually distinguishes six categories, each with its own colour and badge: observation, measurement, scientific evidence, Jev judgment, hypothesis, and agent action. The mapping in `web/lib/categories.ts` is presentation-only — it labels what the backend already recorded and never decides what counts as evidence.

## Data

The UI renders a generated snapshot at `web/data/snapshot.json`, produced offline by `scripts/export_snapshot.py` from a deterministic scripted cycle. It reads domain read models through `web/lib/snapshot.ts`; it never imports backend modules.

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
