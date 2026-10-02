# Minimal repository governance substrate

Status: bounded tooling specification; no roadmap or authority change.

The [code-first truth report](REPOSITORY_TRUTH_REPORT.md) was completed before
reading the current plan and its [reconciliation](PLAN_RECONCILIATION.md).
Those reports identify inaccurate status aggregation and a framework-boundary
exception. Neither is repaired by an inventory. Valid unfinished science,
qualification and evaluation work stays in the unchanged implementation plan.

## Architecture projection

`architecture.yaml` is a manually reviewed, machine-readable projection of
`docs/ARCHITECTURE.md` and `AGENTS.md`. Those documents retain authority. The
projection records current owners, authority/data-flow directions, prohibitions
and consequential invariants, with evidence scope and known exceptions. Directions
are not an import DAG. Canonical-source hashes identify its review basis; a source
change requires review, not automatic policy adoption.

Classification means ENFORCED by the named executable guard, TESTED at the named
behavior boundary, or REVIEWED by source inspection. Classification is scoped:
it does not establish live connectivity, scientific utility or current native
confinement. The projection adds no policy, acceptance gate, future capability or
phase status. It is not read by runtime, and no ADR is needed to retain existing
authority. Making it canonical would require a separate proposed ADR and decision.

## Python declaration index

`scripts/repo_index.py` is justified as a repeatable machine query surface where
text search cannot reliably distinguish declaration kinds, scopes or imports.
It uses only the Python standard library and AST; it never imports indexed code.

- Default scope: Python files in `src/`, `scripts/`, `tests/`, including current
  untracked files. Exclude vendor/cache directories, `.upstream/` and links/junctions.
- JSON on stdout: stable schema, relative paths, source hashes, qualified names,
  locations and static declaration metadata. No timestamps or absolute paths.
- Query by kind, name substring, module prefix and path prefix; filters combine.
  Models include statically traceable Pydantic subclasses and dataclasses. Enums
  include statically traceable standard-library Enum subclasses.
- Return modules, classes/models/enums, functions (including methods/nested/async),
  declared annotated class fields, enum assignments and scoped imports. Preserve
  annotations, defaults, bases, decorators and relative-import levels as syntax.
- Inherited fields remain queryable on their declaring class. Dynamic factories,
  metaclasses, wildcard imports and runtime type evaluation are not resolved;
  model/enum classification is positive static recognition, not exhaustive proof.
  Import-alias recognition uses module-level syntax; conditional rebinding and
  wildcard imports are not runtime name resolution.
- Invalid syntax/read errors fail with nonzero exit and no partial JSON. Inventory
  is read-only; no cache, generated reference document, DB access or network access.

No registry, schema database, frontend parser, document generator, new architecture
enforcer or runtime dependency is introduced. Consumers can query this substrate;
semantic compliance still requires the existing checks and review.

Examples (run with the existing environment):

```powershell
.venv/Scripts/python.exe -B scripts/repo_index.py --kind model --name ResearchState
.venv/Scripts/python.exe -B scripts/repo_index.py --kind field --name ResearchState
.venv/Scripts/python.exe -B scripts/repo_index.py --kind import --module src.reasoner
```

## Verification contract

New tests belong at the CLI boundary. They protect correct declarations and filters,
nonexecution of indexed code, exclusion of vendor input, root-independent byte
determinism, and honest syntax-error failure. Credible regressions are missed alias
inheritance, accidental import execution, walking excluded trees, unstable path
ordering and silently returning incomplete results. Existing runtime tests exercise
none of this new CLI. Tests require no test-only production seams or copied repo
inventory. Run these focused tests, current-repo queries,
`scripts/check_architecture.py`, projection evidence checks and `git diff --check`.

## Delivery verification (2026-10-02)

- `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider -o addopts='' tests/invariants/test_repo_index.py -q`
  — **6 passed in 1.06s**, including actual symbolic-link exclusion on this host.
- `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider -o addopts='' tests/invariants/test_live_mode.py -k handoff_preserves_in_flight_source_result_and_blocks_next_request -q`
  — **1 passed, 30 deselected in 5.80s**; one existing dependency event-loop warning.
  Other fresh runtime/UI proof and limits are recorded in the truth report.
- Current-repo full index returned byte-identical JSON twice. Model, enum,
  function, declared-field and scoped-import queries returned expected matches.
  Output stayed on stdout; no generated reference document was written.
- YAML parsed successfully; canonical-source hashes, owner paths, direction
  endpoints, classifications and every file/symbol/test evidence reference checked.
  This validates projection integrity, not semantic completeness or policy enforcement.
- `.venv/Scripts/python.exe -B scripts/check_architecture.py` passed.
  Markdown links and tracked/new-file whitespace checks passed.
- Implementation plan SHA-256 remains
  `8e8ea32423d572265ba6407b061418ed1234962e01f80e1db04ab20b7f07e92b`.
  Existing worktree changes, reconciliation and proposed planning ADR are preserved.
  No canonical architecture/status authority, runtime behavior or qualification
  gate changed; no new authority ADR is proposed by this tooling delivery.
