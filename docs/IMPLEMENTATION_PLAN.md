# Implementation plan

This is OncoJev’s only implementation-phase and status tracker.

## 1. Architecture, upstream, and tracking

**Status:** DONE

**Goal:** Lock the two-scope architecture, add progressive upstream navigation, and establish this single tracker.

**Scope:** Architecture and capability documentation; `.upstream/INDEX.md`; limited GDC API/model/pipeline navigation; manifest reconciliation for locally cloned procedural and public-source references; and a procedural statistical-method guide. No scientific runtime expansion.

**Acceptance criteria:** The Director/Researcher scope boundary is canonical; upstream navigation is progressive; the manifest remains the pin source; no additional tracker is created; existing executable behavior remains unchanged.

**Dependencies:** Existing repository documentation and local upstream inventory.

**Completion evidence:** `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/CAPABILITIES.md`, `skills/statistical-methods/README.md`, `.upstream/INDEX.md`, and `.upstream/manifest.yaml` updated; focused test suite and architecture check pass.

## 2. OncoLab Index and wrapper contracts

**Status:** DONE

**Goal:** Define a large, bounded-retrieval OncoLab Index and wrapper contracts.

**Scope:** One typed metadata index, bounded deterministic retrieval, initial descriptors, and Director/Researcher index-access tools. No scientific execution wrappers.

**Acceptance criteria:** Indexed existence remains distinct from executable, validated, and reusable capability state; both roles can search/describe the same bounded OncoLab catalogue without receiving it wholesale.

**Dependencies:** Phase 1.

**Completion evidence:** `OncoLabDescriptor`, `OncoLabIndex`, and 100+ initial descriptors implemented; Director and Researcher Code Mode integration exercised with `FunctionModel`; `pytest`, the synthetic slice, and architecture checks pass.

## 3. Initial executable scientific capabilities

**Status:** DONE

**Goal:** Add initial statistics, GDC/Xena, literature, and visualization capabilities.

**Scope:** Typed public GDC/Xena/literature wrappers, a small deterministic NumPy/pandas/SciPy/statsmodels surface, matplotlib SVG artifacts, and their bounded Researcher Code Mode tools. No fixed scientific workflow, controlled-data support, sandbox filesystem/shell access, database/API, or UI.

**Acceptance criteria:** A Researcher can discover and invoke independent source, literature, statistics, and visualization methods through the bounded OncoLab Index; sources cannot receive credentials; acquisition is not evidence; deterministic measurements require explicit evidence admission; all tool activity is recorded in the block ledger.

**Dependencies:** Phase 2.

**Completion evidence:** `tests/invariants/test_boundaries.py` exercises the typed tool surface through Code Mode with transport-safe source responses. A live OpenRouter Researcher run on 2026-09-30 selected public GDC, literature, SciPy correlation, and matplotlib independently through the Index, explicitly admitted its measured result, completed its block, and emitted the ledger-backed log. The UCSC Xena wrapper also retrieved two public TCGA-matching dataset records through its documented Hub query interface. `pytest`, `uv lock --check`, and `scripts/check_architecture.py` pass.

## 4. JevBlock deterministic state and Researcher loop

**Status:** DONE

**Goal:** Implement deterministic ResearchState, Jev projections, and the local Researcher loop.

**Scope:** Immutable provider-agnostic ResearchState, deterministic Jev projections, and block-local Researcher orchestration only.

**Acceptance criteria:** Local decisions respect lifecycle, budgets, frontier policy, and scope escalation.

**Dependencies:** Phases 2–3.

**Completion evidence:** `src/researcher/state.py` (immutable `ResearchState`, content-derived `JevProjection`) and `src/runtime/pydantic_ai/contracts.py` (bounded, budgeted Researcher tools) are exercised by `tests/invariants/test_boundaries.py`; `pytest` and `scripts/check_architecture.py` pass.

## 5. Skills and scientific sandbox

**Status:** DONE

**Goal:** Add progressive skills, a scientific sandbox, and GitHub method acquisition.

**Scope:** Controlled procedural use and external software acquisition. Local labskills under `src/oncolab/labskills/` adapt relevant procedural guidance from the pinned K-Dense Scientific Agent Skills and ClawBio repositories without vendoring their code or automatically trusting their skills. Both agent roles use the Pydantic AI Coder harness in the non-root Railway/Linux container; external scientific execution remains Docker-only because WSL alone is not a sufficient isolation boundary.

**Acceptance criteria:** Public GitHub code can run only in an isolated sandbox; `.upstream` is never executable runtime software; sandbox processes receive no provider, SSH, or browser credentials; repository URL, resolved commit, environment, commands, input/output hashes, and exit status are captured; raw output cannot become evidence; and successful execution does not promote a new method to reusable capability.

**Dependencies:** Phases 2–4.

**Completion evidence:** `tests/invariants/test_boundaries.py` covers the credential-free Docker sandbox, receipt fields, replay validation, and non-promotion; `scripts/verify_coder_container.py` ran the Director→Researcher Coder harness inside the hardened non-root image (read-only rootfs, writable tmpfs, no capability set) and printed `{"director": "director complete", "researcher": "researcher complete"}` with exit status 0.

## 6. Live agent and Jev execution

**Status:** DONE

**Goal:** Enable live Director, Researcher, Reasoner, and TypeSafe execution.

**Scope:** Provider configuration and live integration validation.

**Acceptance criteria:** Credentials, budgets, fallbacks, and live failure semantics are verified.

**Dependencies:** Phases 2–5.

**Completion evidence:** `src/runtime/pydantic_ai/factory.py` centralizes deterministic/live selection from `config/models.yaml` and `config/runtime.yaml`; the Reasoner is an independent Pydantic AI sub-agent (`src/reasoner/agent.py`); TypeSafe failures raise `JevOperationalFailure` and are recorded operationally, never as judgments; model-provider and scientific-data authentication are disjoint (`src/config/authentication.py`). `tests/invariants/test_live_mode.py` verifies all of this without any external service, and `scripts/run_live_cycle.py` runs a complete live cycle when credentials are configured.

## 7. Persistence and application API

**Status:** DONE

**Goal:** Add durable persistence and the application API.

**Scope:** State, artifacts, and typed backend exposure.

**Acceptance criteria:** Ledger immutability and dossier/evidence boundaries persist across restarts.

**Dependencies:** Phases 4 and 6.

**Completion evidence:** `src/persistence/` stores typed records in an append-only SQLite store with database triggers rejecting updates/deletes; `src/application/service.py` exposes read models; `src/api/server.py` is a read-only stdlib HTTP API. `tests/invariants/test_persistence.py` verifies append-only enforcement, reconstruction, read-only routes, and that persistence/API cannot bypass evidence admission.

## 8. Next.js observability UI

**Status:** DONE

**Goal:** Build the observability-only frontend.

**Scope:** Missions, blocks, evidence, dossiers, frontiers, registries, and resource usage.

**Acceptance criteria:** UI consumes typed backend state and is not a scientific authority.

**Dependencies:** Phase 7.

**Completion evidence:** `web/` is a Next.js App Router app that renders a generated snapshot (`scripts/export_snapshot.py`) and visually separates observation, measurement, evidence, Jev judgment, hypothesis, and agent action. `npm run build` succeeds and `tests/invariants/test_frontend.py` proves the frontend contains no orchestration or scientific-admission logic.

## 9. Autonomous research evaluation

**Status:** DONE

**Goal:** Run and evaluate real autonomous research work.

**Scope:** Reproducible research-evaluation corpus and outcomes.

**Acceptance criteria:** Scientific utility, recall, uncertainty, cost, and safety are evaluated reproducibly.

**Dependencies:** Phases 3–8.

**Completion evidence:** `src/evals/` runs the same broad directions under science-only, science+Reasoner, and science+Jev+Reasoner conditions with capability gating and a report that carries no `best`/`winner` field. `tests/invariants/test_evaluation.py` verifies the conditions differ only in semantic capabilities, all admitted evidence stays deterministic, the path is assembled dynamically, and provider/method changes need no architecture change.
