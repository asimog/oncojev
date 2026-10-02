# OncoJev

OncoJev is an autonomous computational oncology research system. A human supplies
a broad direction; Director allocates bounded questions, and a fresh Researcher
chooses how to investigate each one. The research thesis is whether typed semantic
measurement, deterministic science and selective reasoning improve useful discovery
while preserving candidate recall.

## Navigation

| Document | Owner |
| --- | --- |
| [Architecture](docs/ARCHITECTURE.md) | Current structure, ownership and invariants |
| [Implementation plan](docs/IMPLEMENTATION_PLAN.md) | Unfinished work and completion criteria |
| [Task log](docs/TASK_LOG.md) | Completed-task verification and proof limits |
| [Agent guidance](AGENTS.md) | Working rules and task navigation |

## Run

Use an existing Python environment with the project dependencies installed. Live
mode reads [model configuration](config/models.yaml) and
[runtime configuration](config/runtime.yaml), and requires `OPENROUTER_API_KEY`
and `TYPESAFE_API_KEY` in the process environment or ignored `.env.local`.
Linux command execution requires native Linux storage and the controls described
in [Architecture](docs/ARCHITECTURE.md#composition-and-execution).

From the repository root in Linux/WSL2:

```sh
.venv/bin/python -B -m src serve --direction "Investigate a public oncology signal"
.venv/bin/python -B -m src cycle --direction "Investigate a public oncology signal"
```

`serve` runs research continuously and exposes the read-only API; `cycle` runs
one cycle. The service defaults to SQLite at `var/oncojev.sqlite3`. An absolute
`ONCOJEV_DATA_ROOT` changes the data root; `ONCOJEV_DB_PATH` overrides the database
file. `HOST` and `PORT` configure the API bind address and port (default 8080).

The web UI reads that API, falling back to a labelled committed snapshot when it
is unavailable. Run it from `web/` with `npm run dev`; `ONCOJEV_API_URL` overrides
its default API address, `http://127.0.0.1:8080`.

## Focused checks

For routine Windows development, choose the test file that owns the change:

```powershell
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider -o addopts='' <owning-test-file>
.venv/Scripts/python.exe -B scripts/check_architecture.py
git diff --check
```

Native probes are separate from local contract tests. The explicit WSL2 setup
helper is [scripts/verify_native.py](scripts/verify_native.py); its cache is
developer setup, not qualification evidence. Run only the checks needed for the
task. For documentation-only changes, run
`scripts/check_architecture.py --docs-only`, review scope/preservation and run
`git diff --check`.
