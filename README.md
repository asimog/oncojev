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
| [Task log](docs/TASK_LOG.md) | Two most recent completed tasks; older proof is archived |
| [Current testing ADR](docs/PROPOSED_ADR_FAST_LOCAL_TESTING.md) | Accepted isolated testing decision, reconciliation and scoped proof |
| [Agent guidance](AGENTS.md) | Working rules and task navigation |

## Run

Use an existing Python environment with the project dependencies installed. Live
mode reads [model configuration](config/models.yaml) and
[runtime configuration](config/runtime.yaml), and requires `OPENROUTER_API_KEY`
and `TYPESAFE_API_KEY` in the process environment or ignored `.env.local`.
Linux command execution requires native Linux storage and the controls described
in [Architecture](docs/ARCHITECTURE.md#composition-and-execution).

From the repository root on native Linux/WSL2 storage, install the locked Linux
Python dependencies (including focused-test tools) and the web dependencies:

```sh
uv sync --frozen
npm ci --prefix web
```

Use an explicit user-owned data root for local runs. Without one, ordinary Linux
Coder defaults to the container path `/work/director`, which may be unwritable:

```sh
ONCOJEV_DATA_ROOT="$PWD/var" .venv/bin/python -B -m src serve --direction "Investigate a public oncology signal"
ONCOJEV_DATA_ROOT="$PWD/var" .venv/bin/python -B -m src cycle --direction "Investigate a public oncology signal"
```

The requested assessment currently enables `unbounded_work: true` in runtime YAML.
This ignores application call/retry/cost budgets while
retaining usage records. Set it to `false` for ordinary bounded investigations.
Blocks target 3-5 minutes: 240 s default, 180-300 s bounds and 30 s handoff reserve.
Data-download ceilings and scientific process/isolation/validity controls remain.

`serve` runs research continuously and exposes the read-only API; `cycle` runs
one cycle. The service defaults to SQLite at `var/oncojev.sqlite3`. The active ordinary
history is the WSL assessment store. Original Windows records are preserved separately
in the read-only `var/archive/original-windows-history-20261002.sqlite3` archive;
no automatic history merge is performed. An absolute
`ONCOJEV_DATA_ROOT` changes the data root; `ONCOJEV_DB_PATH` overrides the database
file. `HOST` and `PORT` configure the API bind address and port (default 8080).

Set `ONCOJEV_TESTING=1` in ignored `.env.local` for isolated application runs.
Edit the `testing` section in runtime YAML: defaults are 240/180/300 s allocation,
30 s reserve, 10 MB data response, 20 MB data per block and 50 MB data per service.
Lower ordinary ceilings win. Each process retains a new `testing/<uuid>/` history
and owned workspaces; `serve` preserves continuity across cycles. A normal database
override fails explicitly in testing. Process `ONCOJEV_TESTING=0` overrides local `1`.
Providers and scientific execution stay unchanged. The 120 s observation target
reports elapsed `run_once` time, excludes post-block review, and is not a timeout.

The web UI reads that API, falling back to a labelled committed snapshot when it
is unavailable. Run it from `web/` with `npm run dev`; `ONCOJEV_API_URL` overrides
its default API address, `http://127.0.0.1:8080`.

## Focused checks

For routine Windows development, choose the test file that owns the change:

```powershell
$env:ONCOJEV_TESTING='0' # Normal fixture defaults; testing contracts enable their own profile.
$env:LOGFIRE_SEND_TO_LOGFIRE='false'
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider -o addopts='' <owning-test-file>
.venv/Scripts/python.exe -B scripts/check_architecture.py
git diff --check
```

For the short isolated-profile check, use the same environment and:

```powershell
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider -o addopts='' tests/invariants/test_live_mode.py tests/invariants/test_boundaries.py tests/invariants/test_persistence.py -k testing -q --durations=5
```

These checks use scripted models, mock transport and clocks, with no WSL/provider
launch. Run native/live or long scientific trajectories explicitly for their task;
record outstanding proof without turning every implementation iteration into one.

For the same short offline profile check on Linux/WSL2, explicitly give ordinary
fixtures a writable data root:

```sh
ONCOJEV_TESTING=0 ONCOJEV_DATA_ROOT="$PWD/var/contract-checks" LOGFIRE_SEND_TO_LOGFIRE=false .venv/bin/python -B -m pytest -p no:cacheprovider -o addopts='' tests/invariants/test_live_mode.py tests/invariants/test_boundaries.py tests/invariants/test_persistence.py -k testing -q --durations=5
```

Native probes are separate from local contract tests. The explicit WSL2 setup
helper is [scripts/verify_native.py](scripts/verify_native.py); its cache is
developer setup, not qualification evidence. Run only the checks needed for the
task. For documentation-only changes, run
`scripts/check_architecture.py --docs-only`, review scope/preservation and run
`git diff --check`.
