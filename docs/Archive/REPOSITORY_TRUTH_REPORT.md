# Verified repository truth

Audit date: 2026-10-02. This is a human-reviewed current-state report, not a
generated code-reference document, roadmap or new architecture authority.
The pasted reports were treated as claims to verify. This report was completed
before reading the implementation plan for this task.

## Basis and scope

- Branch `main`; HEAD `f1376d6035c78da4f3a52f5e58f246e6daef77aa`.
- The checkout is **not clean**. Existing modifications: `README.md`,
  `docs/CAPABILITIES.md`, `docs/FRONTEND.md`. Existing untracked files:
  `docs/PLAN_RECONCILIATION.md`, `docs/PROPOSED_ADR_PLAN_STATUS.md`,
  `scripts/verify_native.py`, `tests/invariants/test_native_setup.py`.
  All are preserved. Findings concern this worktree, not only committed HEAD.
- All public Python files under `src/`, `scripts/`, `tests/` were syntax-parsed
  without executing their modules. Baseline: 104 source files, 15 scripts, seven
  test files. Source AST contains 170 classes, 381 synchronous and 94 asynchronous
  function definitions, including methods and nested functions. These are syntax
  counts, not counts of capabilities or validated science.
- Current owning docs, configuration, entrypoints, production callers and focused
  regressions were inspected. Frontend source/data flow and rendered behavior were
  checked. No `.upstream/` tree was traversed or read, no dependencies installed,
  and no service, provider, remote publisher, Docker or WSL probe was started.

## Current ownership and executable flow

| Owner | Current behavior and authority | Verified limits |
| --- | --- | --- |
| Entry/service: `src/__main__.py`, `src/autonomous.py` | `serve` runs one autonomous loop plus read-only API thread; `cycle` awaits one actual cycle. Service retains Director, event-loop runner and service resources; exact human direction supplies a durable mission spanning cycles/reopen | Service catches operational cycle failures; pre-allocation/no-active failures may use configured retry sleep. No prior Director transcript is retained |
| Composition/adapters: `src/runtime/pydantic_ai/` | `factory.build_system` requires live mode/credentials, composes fresh runtime and Researcher factory, accepts retained Director/resources, selects backend, binds durable records | Integration is concentrated here, but **not exclusive**: `src/reasoner/agent.py` imports and constructs Pydantic AI Agent outside this package |
| Lifecycle: `src/block/`, `src/runtime/cycle.py`, runtime contracts/lifecycle | BlockManager owns bounds/deadlines/handoff; runtime owns one async Researcher, one launch per block, owner-thread persistence, event wakeups and terminal finalization. Director chooses allocation; Researcher investigates locally | Single-worker discipline is in service/tool path, not a universal guarantee for arbitrary BlockManager calls. Blocking detached operations drain before ownership is released |
| Operational resources: `src/runtime/resources.py`, process/confinement owners | Role/cycle attempt/request budgets; service-lifetime download totals and reservations; one heavy lease; owned Linux cgroup/namespace/tmpfs execution with cleanup confirmation | Native controls are code-reviewed here, not freshly qualified. Installed in-process Science runs offloaded in a thread with no kernel process-family quota. Unknown cost/counters remain unknown |
| Director: `src/director/` and global adapter tools | Bounded history-derived candidates, normalized exact duplicates, native global relations, categorical beam, stale-basis checks, portfolio/reviews and non-authoritative engineering proposals | Selection through prepared frontier is optional. Portfolio scientific resolution remains unknown. Lexical memory search can miss zero-overlap items; no global scientific execution/admission tool |
| Researcher state: `src/researcher/` | Fresh block state, candidates, inputs, measurements and evidence IDs; bounded semantic projections; each retained state revision is append-only | Pydantic `frozen=True` prevents attribute reassignment, **not deep mutation of nested dictionaries**. Persistence serializes immutable record snapshots; shallow frozen objects are not a universal deep-immutability mechanism |
| Acquisition: `src/sources/` | Anonymous GDC endpoint metadata/open bytes, Xena catalogue, literature metadata/abstracts; exact source/query/content/coverage/artifact identities; ordered page composition and input assessment | Controlled scientific authentication is unsupported. Metadata does not become assay inputs. Unknown coverage/normalization/build stays unknown; no automatic matrices or joins |
| Science: `src/science/` | Deterministic descriptive/provided-array statistics; owned-source complete-row Pearson/simple OLS; selected-gene STAR parsing; exploratory effect-bound/multiplicity plans; same-method GDC case-paired follow-up comparisons | Provided/synthetic statistics are ineligible for admission. Source design/independence is declared, not empirically established. No general survival/TMB/DE/multi-omic execution inferred from catalogue entries |
| External science backend | Factory defaults to local-venv. Fresh per-experiment package environments, retained commit/archive/wheels, trusted app launcher before experiment entrypoint, offline install, first/replay/fresh replay and hash/command validation | Linux x86_64 required; unsupported source builds, threads/subprocess methods/filesystem output fail closed. Historical Docker backend remains code-compatible, not active default or newly qualified |
| Evidence: `src/science/admission.py`, `src/evidence/models.py` | Researcher admission tool calls deterministic gate, then persists typed evidence; stable scope/analysis/replication identity | Gate checks deterministic flag, source/sandbox origin, provenance/source refs and top-level finite numerics. It does not independently prove scientific assumptions, biological truth or existence of every referenced record; owning runtime validates inputs/replay |
| Jev: `src/jev/` | Typed Noul/Choice/Score/native distributions, explicit operational failures, versioned candidate and multidimensional policies; global/literature policies remain distinct | Semantics cannot admit evidence, grant a missing route, extend deadlines or resolve biological contradictions. Thresholds are software policy, not calibrated scientific confidence |
| Reasoner: `src/reasoner/` plus budget adapter | Independent typed hypothesis/interpretation sub-agent; live usage charged to Researcher, deterministic fixture alternative | No admission/allocation authority. Agent construction outside adapter package is a documented boundary mismatch |
| OncoLab: `src/oncolab/` | Shared bounded Index, catalogue/cards/contracts/routes, verification records, immutable registry revisions and separate institutional observations; blocks/searches pin revision/history/application basis | Seed has 109 descriptors. Most descriptor presence is metadata; no automatic reusable promotion. Accepted review fixture proves revision/pin mechanics, not qualified promotion |
| External capability discovery/enrichment | bio.tools search/describe with bounded EDAM metadata and mutable-source receipts; targeted GitHub commit/root refs, Bioconda builds, Bioconductor page facts | Root links/recipe URLs are not inspected canonical operations. Conda/R execution unsupported; listings grant no execution or scientific authority |
| Governance: `src/oncolab/governance.py` | Deterministic source-linked proposals/review; explicit reference/environment/utility/local/licence/repeated-use checks; accepted state revision branch and code-required EngineeringProposal | `run_reusable_method` is required by policy but has no tool/dispatcher implementation. Proof record kinds have consumers, but no production producers found for reference validation, environment qualification, utility evaluation or complete local verification |
| Labskills/`skills/` | Researcher selects fresh bounded procedural guidance through block skill store | Instructions do not execute science or constitute reusable capabilities |
| Persistence: `src/persistence/`, ledger/provenance owners | Direct SQLite, immutable envelopes and sequence/hash-linked refs, append-only UPDATE/DELETE triggers, atomic terminal bundles, coherent serialized reads, recovery corrections, source bytes and archival | Store accepts typed records; it is not an admission-policy service. Check-then-append workflows rely on owner discipline beyond explicit transactions. No PostgreSQL selector/migration path found in active source |
| Dossier/Delta: `src/dossier/` | Deterministic terminal handoff and bounded block-owned change references with explicit omissions; duration/download/execution/lease metrics | CPU/workspace/peak fields remain `None`; stale Delta prose says exact pins “follow H5” although block pins exist. Missing negatives/resolutions are not manufactured |
| Memory: `src/memory/` | Reference-validated memory-v4 derivation, bounded retrieval/start packets, source attempts/follow-ups/tentative context, independent global semantic allowances | Derived context has no admission authority. Missing/failed/inconclusive records stay distinct. API reads do not backfill; lexical overlap and summary omissions limit recall |
| Presentation/API: `src/application/service.py`, `src/api/` | Health/overview/blocks/memory/reconstruction read models; POST/PUT/PATCH/DELETE rejected; failure precedence and missing-input labels | Connectivity/run completion does not certify objective attainment or utility |
| Export/publisher: `src/application/export.py`, `publication.py`, CLI | Renderer-v3 reads a pinned prefix, carries IDs/hashes/native calls, excludes private bytes/credentials; separate publisher guards approved remote/dirty edits, retry cap, pushed SHA and failure receipts | Service hooks retain export identities; only separate CLI invokes publication. No automatic event-to-publisher dispatcher or current remote publication proof established |
| Evaluation: `src/evals/`, evaluation CLIs/artifacts | Fresh science-only, science+Reasoner, science+Jev+Reasoner conditions; generated selection/representation comparisons, versions/distributions/failures/recall | Labels remain outside admission. Small generated corpora are contract proof. Declared replication metric counts IDs, not proven independent biological replication; utility/cost frequently null |
| Visualization: `src/visualization/` | Bounded provided-series line figure→SVG artifact | Plot is exploratory, never evidence/admission |
| Frontend: `web/` | Next.js 14/React 18 observability UI with uncached server-side read-only API, five-second fetch timeout and synthetic offline snapshot fallback | Presentation categories/read models grant no orchestration/admission. Rendered controlled-transport tests passed; no live browser/build/deployment proof performed |
| Developer/verification scripts | Existing architecture checker, live/eval/export entrypoints, scoped native verifiers; untracked native helper caches public tree/developer setup while rerunning requested probes | No `.github/` directory observed. Native setup cache is not qualification. Docker/Railway artifacts still exist but do not select runtime storage/backend |

## Dependency directions and enforcement reality

The current authority flow is service→composition→Director allocation→owned
Researcher→source/Science→validated measurement→admission→persistence, with
persisted records→memory/read models/export and API→web. Jev and Reasoner feed
bounded decisions/proposals; they have no evidence-admission edge. Governed
review→registry revision affects later pinned blocks.

The **Python import graph is not a clean layer DAG**. Syntax inspection finds
bidirectional package references including runtime/science, runtime/oncolab,
persistence/dossier, persistence/memory and science/evidence. Many are model,
reference or late imports. Import reachability is not authority; package cycles
alone do not establish a runtime circular-import failure. A machine manifest must
not invent a stricter allowed-import DAG than the existing canonical boundary.

`scripts/check_architecture.py` currently checks selected admission bypass tokens,
Director admission import, frontend backend tokens, `.upstream` import syntax,
required architecture records and bundled verification/catalogue integrity. It
does **not** enforce all dependency directions, all Pydantic AI imports, deep state
immutability, complete confinement, or documentation accuracy. Its upstream check
matches literal `.upstream` names; arbitrary aliases/dynamic loading are not
comprehensively denied. Its pass is scoped static/integrity evidence.

Classification for any machine projection must state its scope:
`ENFORCED` = a named existing runtime/mechanical guard; `TESTED` = a named owning
regression for a bounded behavior; `REVIEWED` = code/doc trace without mechanical
proof of the whole statement. A guard may exist while current native qualification
is unproven. None of these labels means scientific utility.

## Exact identity and retained proof inventory

Computed current application identity:
`application-v1:3fbbab17078dbf9c0db588ac904faf70c80a783742bc35c8ea1ac01394c548de`.
`application_identity()` hashes source Python, direct config YAML and
`pyproject.toml`; not Git HEAD, scripts, docs or the exact installed environment.
Backend environment hash includes observed execution/environment details and
experiment path; it is a different identity.

Read-only SQLite URI connections (`mode=ro`, `query_only=ON`) independently found:

| Local file | Integrity / records / high-water | Local verification / environment qualification / reference validation / utility evaluation |
| --- | --- | --- |
| `var/oncojev.sqlite3` | `ok` / 1,216 / 1,216 | 0 / 0 / 0 / 0 |
| `var/h6-star-parse.sqlite3` | `ok` / 3 / 3 | 0 / 0 / 0 / 0 |
| `var/local-notebook-proof.sqlite3` | `ok` / 1 / 1 | 0 / 0 / 0 / 0 |

`local_verification_passed` requires one complete application-matched receipt,
local-venv, Linux/x86_64/WSL2 and exact boolean control groups. It checks nonempty
Python/executable strings; **it does not compare current Git HEAD or current
environment identity**. No current composed qualification is established by these
three databases. Remote history completeness and other external stores remain
unknown. Historical session-log/probe claims in the paste were not substituted for
current evidence or reread; native enforcement/connectivity/utility is unproven here.

## Independently confirmed drift

- The pasted clean-worktree assertion is false for this checkout; its application
  identity and the three specified local proof-count assertions match fresh checks.
- Exclusive framework-integration guidance conflicts with live Reasoner Agent
  construction in `src/reasoner/agent.py`. Existing architecture checks do not catch it.
- `verify_coder_container.py` actually requires `railway.toml` as a denial-control
  target. Its filename does not mean it invokes Docker. `verify_scientific_artifacts.py`
  actually invokes Docker; it is not a current no-Docker local gate.
- Complete local qualification/reusable dispatch is absent, despite policy/schema
  consumers. Separate native scripts print scoped reports, not the canonical receipt.
- Frozen models, admission checks and static boundary checks must not be described
  as stronger guarantees than they implement. No architecture cleanup is made here.

## Verification completed before plan review

- Focused boundary/persistence/live/evaluation command, selecting admission,
  append-only/API, fail-closed credentials, governance, launch/event continuity,
  registry pins and evaluation isolation: **37 passed, 130 deselected in 39.67s**.
  Command: `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider -o addopts='' tests/invariants/test_boundaries.py tests/invariants/test_persistence.py tests/invariants/test_live_mode.py tests/invariants/test_evaluation.py -k 'non_science_outputs or synthetic_measurement or repeat_admission or store_is_append_only or terminal_bundle or persistence_and_api or api_is_read_only or deterministic_fixture or build_system_is_live or governance_rejects or owned_launch or service_completion or block_registry or representation_evaluation or conditions_differ' -q`.
- `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider -o addopts='' tests/invariants/test_frontend.py tests/invariants/test_agent_telemetry.py -q`
  — **5 passed in 15.23s**, including rendered live/fallback views and telemetry
  content exclusion against the installed local environment.
- `.venv/Scripts/python.exe -B scripts/check_architecture.py` — passed.
- `git diff --check` — passed, with existing LF→CRLF notices.
- Whole selected Python syntax parse and local read-only integrity/proof counts
  passed. These checks prove their local contracts only, not a whole-system
  certification, current native confinement, live connectivity or scientific utility.

Architecture authority remains [ARCHITECTURE.md](../ARCHITECTURE.md), with ownership
defined by [AGENTS.md](../../AGENTS.md). The plan/status authority is separate and is
read only after this code-first report; report drift does not change either owner.
