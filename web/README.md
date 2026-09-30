# OncoJev observability UI

Presentation-only Next.js App Router app. It renders a generated snapshot of application read models and contains no orchestration, scientific, or evidence-admission logic.

```bash
npm install
npm run build
npm run dev
```

Regenerate the snapshot from the repository root:

```bash
uv run python scripts/export_snapshot.py
```

The snapshot is written to `web/data/snapshot.json`. See [../docs/FRONTEND.md](../docs/FRONTEND.md).
