# OncoJev observability UI

Presentation-only Next.js App Router app. It renders live read models from `ONCOJEV_API_URL`, falls back to the generated snapshot when the API is unavailable, and contains no orchestration, scientific, or evidence-admission logic.

```bash
npm ci
npm run build
npm run start
```

Regenerate the snapshot from the repository root:

```bash
uv run python scripts/export_snapshot.py
```

The snapshot is written to `web/data/snapshot.json`. See [Architecture](../docs/ARCHITECTURE.md).

Use `npm run dev` for development. Production builds use pinned Next.js 15.5.24,
React 19.3.0 and patched PostCSS 8.5.28; dynamic routes await their route parameters.
The Linux Node environment is separate from Python. `ONCOJEV_API_URL` points the
server at the read-only Python API; UI startup does not start research.
