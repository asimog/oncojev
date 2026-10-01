# OncoJev observability UI

Presentation-only Next.js App Router app. It renders live read models from `ONCOJEV_API_URL`, falls back to the generated snapshot when the API is unavailable, and contains no orchestration, scientific, or evidence-admission logic.

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
