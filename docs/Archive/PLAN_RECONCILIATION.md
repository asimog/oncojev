# Implementation-plan reconciliation

2026-10-02. **Review artifact only; not a roadmap or status authority.** The entire
802-line [current plan](../IMPLEMENTATION_PLAN.md) was read. No plan, runtime, config,
test, database or historical archive was changed by this review.

Basis: HEAD `f1376d6035c78da4f3a52f5e58f246e6daef77aa`, plus the existing worktree.
Pre-existing changes: `README.md`, `docs/CAPABILITIES.md`, `docs/FRONTEND.md`,
`scripts/verify_native.py`, `tests/invariants/test_native_setup.py`. These are
preserved; the untracked native setup helper is developer tooling, not qualification.
Plan SHA-256: `8e8ea32423d572265ba6407b061418ed1234962e01f80e1db04ab20b7f07e92b`.

## Findings that change the reconciliation

1. **Substantial implementation is complete within PARTIAL phases.** Async
   scheduling, terminal transactions, event turns, persistent mission identity,
   frontier revalidation, registry/history pins, GDC acquisition, one STAR parser,
   need-bound methods, scoped follow-ups, literature context and deterministic
   export have executable paths and passing local regressions. Keep those as
   completed slices; broader scientific acceptance does not reopen them.
2. **H9 has missing implementation, beyond missing proof.** Governance requires
   `run_reusable_method`, but repository-wide searches of `src`, `scripts` and
   `tests` find that name only in governance and its rejection fixture. There is
   no registered tool/dispatcher. Reference-validation, environment-qualification,
   utility-evaluation and complete local-verification record kinds have consumers
   but no production producers in those paths. Accepted reusable delivery needs
   these paths built, then qualified and exercised in a fresh block.
3. **Aggregate Coder and external-science controls are landed.** The old H2/H10
   return notes and final open question 5 are stale about clone/bootstrap/install
   enforcement. Current external science is `local-venv-v4`, with five governed
   phases; Coder uses the same owned command family. Remaining work is installed
   in-process Science quotas, composed accounting and complete current-basis local
   proof. Windows tests cannot requalify WSL2 controls.
4. **Qualification and utility are the largest remaining acceptance surface.**
   Generated selection/input cases and scripted semantic answers prove plumbing,
   routing and deterministic guards. They do not prove biological replication,
   method suitability, literature classification, useful discovery or marginal
   Jev benefit. No current whole-system utility conclusion is supported.
5. **H11 is cancelled, not blocked.** PostgreSQL/migration/target work must remain
   historical. Local SQLite, confinement and recovery obligations remain active.

## Classification and evidence

`P` = implemented and proven for the explicitly stated local contract;
`U` = implemented but unproven for the claimed scope;
`N` = not implemented; `C` = obsolete/cancelled;
`D` = duplicated obligation whose original owner must remain;
`F` = still valid future work, including a required measured gate/disposition.
Codes can coexist: implementation and qualification are different facts. `P`
never means clinical/scientific utility or current native confinement certification.
Numbered step references below refer to the numbered work orders inside each H
section, rather than similarly named historical delivery batches.

| Evidence | Code/config inspected | Primary behavior proof inspected and run |
| --- | --- | --- |
| E1 lifecycle | [service](../../src/autonomous.py), [cycle](../../src/runtime/cycle.py), [runtime](../../src/runtime/pydantic_ai/contracts.py), [event waits](../../src/runtime/pydantic_ai/lifecycle.py), [factory](../../src/runtime/pydantic_ai/factory.py) | `test_persistence.py`: owned launch, terminal bundle/rollback, shutdown, pending-Director handoff, continuous review/next allocation, bounded event turns, mission/history across fresh/reopened nested/fallback runs |
| E2 resources | [resources](../../src/runtime/resources.py), [process family](../../src/runtime/process.py), [local backend](../../src/science/local.py), [workspace](../../src/runtime/pydantic_ai/workspace.py), [runtime config](../../config/runtime.yaml) | Boundary failed-transfer/preflight tests; persistence heavy-work drain tests; live role/aggregate limits. Native verifier source inspected; earlier native results in the plan are historical and were not rerun |
| E3 global semantics | [frontier](../../src/director/frontier.py), [reviews](../../src/director/review.py), [global tools](../../src/runtime/pydantic_ai/global_tools.py), [memory](../../src/memory/service.py) | Persistence real Director/CodeMode normal/failure frontier, duplicate/replication/population preservation, stale basis, reviews, mission isolation, reopen/export |
| E4 institutional basis | [institution](../../src/oncolab/institution.py), [registry](../../src/oncolab/registry.py), factory/runtime pin resolution | `test_block_registry_search_remains_pinned_after_governed_change`: old/new contracts, history-only observations, stale cursor, execution denial, reopen. Accepted review is supplied by the fixture; it does not prove H9 qualification |
| E5 source/representation | [public sources](../../src/sources/public.py), [input assessment](../../src/sources/representation.py), [STAR parser](../../src/science/representation.py), [science tools](../../src/runtime/pydantic_ai/scientific_tools.py) | Boundary access/filter/query errors, byte ceilings, reservations and parser exact IDs/units/zeros/missingness/row bounds; persistence artifact ownership/replay/reopen |
| E6 methods/discovery | [method contracts](../../src/oncolab/methods.py), [search tools](../../src/runtime/pydantic_ai/search_tools.py), [external discovery](../../src/oncolab/discovery.py), [enrichment](../../src/oncolab/enrichment.py) | Boundary need-bound method/representation CodeMode cases and distinct enrichment fixtures; persistence retained external lookups, cursor identity/outages/no execution authority |
| E7 qualification | [governance](../../src/oncolab/governance.py), [local proof contract](../../src/runtime/verification.py), [routes](../../src/oncolab/execution.py) | Persistence unqualified-use rejection and local receipt adverse cases. No accepted-promotion end-to-end test or production proof writers found |
| E8 scientific history | [science](../../src/science/execution.py), [follow-ups](../../src/science/followup.py), [context tools](../../src/runtime/pydantic_ai/context_tools.py), memory | Persistence paired source/repeated admission, directional attempt history, predeclared follow-up/adverse/overlap/exposure cases and literature unknown/failure/reopen cases |
| E9 projection/publication | [export](../../src/application/export.py), [publisher](../../src/application/publication.py), [CLI](../../scripts/export_notebook.py) | Persistence pinned deterministic bytes, global native calls, private-data exclusion, local Git with simulated push/remote failure/success, retry cap and dirty-checkout preservation |
| E10 evaluation/policy | [selection](../../src/evals/selection.py), [representation](../../src/evals/representation.py), [harness](../../src/evals/harness.py), [policy](../../src/jev/frontier.py), [retained artifacts](../../evals) | All `test_evaluation.py` cases; boundary conservative Choice/multidimensional policy tests. Generated artifacts explicitly leave utility/cost unknown |

## Item disposition: current implementation versus retained work

This covers every H work-order step, all integrated D batches and R additions.
Exit-proof paragraphs inherit their owning row's proof limits; no phase-wide
DONE label is inferred from the local suite.

| Plan items | Exists now / disposition | Future plan must retain |
| --- | --- | --- |
| H0 | Historical completed audit, not a runtime feature. Current caller split differs from its recording-time inventory (E10) | Preserve audit provenance; do not execute historical setup or turn old test totals into current certification |
| H1 | P: persistent Director composition, bounded role/resource inspection, Linux Coder + Monty composition (E1/E2); U: fresh current-environment native qualification | Keep H1 delivered. Current resource/native acceptance belongs to H2/H10, not reopened H1 |
| H2 steps 1–2 | P: run/context identity, fresh Researcher/state, one active start, prompt handle, common nested/fallback start and CLI await; pins belong to block start (E1/E4) | Preserve mechanisms and independent regression ownership; only composed acceptance remains |
| H2 steps 3–4 | P: loop-owned mutation, detached offload, atomic terminal outcome/dossier, failure precedence, drain/recovery (E1). U: universal nonblocking/coherent behavior outside covered operations | Retain bounded synchronous JSON/hash/DB/retention concerns and composed responsiveness; do not promise universal transaction atomicity |
| H2 step 5 | P: configured role/cycle counts, persistent service-lifetime download usage/reservations, native-governor implementation. N/F: installed in-process Science kernel quotas; U/F: complete accounting/current native qualification (E2) | Keep actual limit scopes and unknown cost/metrics. New blocks do not reset service download totals; proof must cover composed use |
| H2 step 6 | P: one heavy lease, busy rejection and cancellation draining; Coder/external-science aggregate integration exists (E2). U: fresh native enforcement proof in this review | Retain integrated lease/telemetry proof; close stale demands to introduce already landed aggregate controls |
| H3 steps 1, 3, 5 | P: material/scheduled bounded turns, event wait, terminal handoff, exactly-once local review, rapid next cycle, unchanged allocation defaults (E1). U: combined scientific refresh/next-selection trajectory | Keep composed acceptance and honest incomplete/failed cycles; no repeated implementation of scheduling |
| H3 step 2 | P: source-linked bounded Delta categories/omissions and wall/download/count metrics (E1/E8). N/F: CPU/workspace aggregation into Delta (E2) | Native receipts exist, but Delta still returns `None` for CPU/workspace/peak and reviews consume those unknowns. Retain telemetry integration |
| H3 step 4 | P: material-basis revalidation and registry/history/application pins (E3/E4); U: full post-review composition | Retain current material dependencies, historical selections and next-block refresh proof; do not require every read-only record to invalidate a frontier |
| H4 step 1 | P: bounded typed retrieval/filtering, exact duplicate normalization, bounded neighbour comparisons (E3); U: low-overlap/relation recall | Keep measured misses/recall acceptance; lexical memory search still excludes zero-overlap digests |
| H4 steps 2–3 | P: referenced portfolio observations and native relation receipts. N/F: full scientific blocked/newly-testable/deferred/resolved lifecycle and resolvability handling; U: paraphrase/conflicting-design accuracy (E3) | `portfolio()` reports scientific resolution as unknown; relation measurements alone do not implement a scientific resolution state machine |
| H4 step 4 | P: candidates from continuations/uncertainties/hypotheses/attempts/context/follow-ups/blockers, distinct follow-up purposes, categorical beam (E3/E8). N/F: broader representation/external/newly-testable and retained-relation/deferred regeneration | Preserve every listed origin and weak-continuation requirement. Optional frontier-bound selection is guarded; arbitrary allocation is not forced through that beam |
| H4 steps 5–6 | P: global/local policy separation, native failure fallback, bounded observed resource/concentration reviews, reference-linked EngineeringProposal with no mutation authority (E3) | U/F: scientific concentration/actionable-change utility and complete review metrics; proposals remain proposals |
| H4a steps 1–3 / D3 | P: actual global and method domains; N/F: representation generator and shared production dispatcher; U/F: multi-domain comparison. D: extraction obligation repeated in H14 step 3 | Retain inventory, paired recall/resource gate and conditional extraction or measured rejection. Assessing/parsing a representation is not generating alternatives |
| H4b steps 1–3 / D4 | P: exact duplicate, independent replication/population retention. N/F + U/F: remaining lifecycle distinctions, labelled failures, minimal repairs where exposed, held-out retention/alignment comparison (E3/E10) | Preserve paraphrase, different test/design/population, blocked-to-actionable and new-evidence cases; no unconditional refinement rewrite |
| H5 steps 1–3 | P: curated seed, immutable governed revisions, separate append-only observations, frozen block/search basis, rejection of stale cursors, next-block visibility (E4) | U/F: composed exact-basis return acceptance; legacy missing pins stay unknown, no backfill/migration |
| H5 step 4 | P: distinct catalogue/external/data layers, proposals/reviews and history (E4/E6/E7); U: fully qualified accepted update/retirement/reuse | D: execute the qualified transition in H9, not another H5 promotion engine |
| H6 steps 1–3 | P: bounded `/files` metadata/cards, controlled/unknown visibility, open-only exact-byte acquisition, hash/size/owner checks, free-space/reservations/failure metering (E5) | U/F: fresh current endpoint/selected-asset connectivity if needed, and selected analysis prerequisites. Release/assay/participant facts remain unknown when absent |
| H6 step 4, H6a steps 1–3 / D2 | P: deterministic owned-input schema/unit/entity gate and one selected-gene STAR parser; generated comparison cases (E5/E10). N/F: broader executable schemas/matrices/joins/transforms and alternatives; U/F: independent useful-representation recall | Preserve available-but-missed cases, low lexical overlap, actual transform prerequisites, conditional recovery/no-miss decisions; never equate a file card with a cohort matrix |
| H7 steps 1–3 | P: common bounded search/describe, bio.tools/EDAM fields, retained mutable-source receipts, local route checks and need-bound local methods (E6). U: scientific design applicability/external suitability | Retain competing methods, covariate/prerequisite gaps, missing-route denial and method-suitability evaluation; vocabulary metadata is not ontology reasoning |
| H7 step 4; H7a steps 1–4 / D6 | P: scan retrieval and small fixed-catalogue selection benchmark. N/F: growing-snapshot/coverage benchmark and conditional vocabulary/embedding experiments. C: migration-based FTS/new database adoption. D: staged gate reporting in H13 | Preserve scale measurement and all staged decisions, including explicit FTS scope incompatibility. Current small scan result is not a growing-catalogue no-change conclusion |
| H8 steps 1–3 | P: targeted pinned GitHub/root references, Bioconda builds, Bioconductor page facts (E6); N: supported R/Conda execution, intentionally outside stage | Retain canonical operation/example inspection and exact source bindings; metadata/public access/constructed recipe URLs cannot qualify software |
| H8 step 4 | P: modular adapter seam; C/out of scope: cBioPortal/Hugging Face; F: optional additional approved source only after measured need | Preserve optionality; no obligation to implement every registry, runtime or source |
| H9 steps 1–2 | P: source-linked proposals and versioned deterministic reject checks/dedup, history-only rejection (E7); U: accepted governance path/adverse cases | Retain scoped scientific/reference/repeated-use/licence/utility/local qualification; mere receipt booleans are not independent proof production |
| H9 steps 3–4; H9a steps 1–3 / D1 | P: EngineeringProposal for code-required changes; acceptance/revision branch exists. N/F: `run_reusable_method` dispatcher and proof-production path; U/F: accepted proposal→review→revision→fresh Researcher execution (E7) | Retain accepted reuse, active/historical pin isolation and update/reverification/retirement behavior. A rejection disposition cannot close missing accepted-delivery capability |
| H10 steps 1–3 | P: configured local backend/default, isolated per-experiment inputs/env, trusted launcher, shared aggregate governor in all five phases; historical Docker compatibility (E2) | U/F: current WSL2 native qualification. N/F: in-process Science quotas. Keep unsupported single-process/runtime limits; no new Docker/deployment gate |
| H10 steps 4–5 | P: exploratory commit/input/output identity, first/same-env replay, validation and independent fresh replay before admission; retained artifacts/archive guards (E5/E8) | U/F: operation-specific canonical/adverse scientific fidelity and promotion qualification; replay and allowed admission do not establish validity beyond scope |
| H10 step 6 | P: reserved metered transfer, disk preflight, aggregate prepare/install/test/execute/replay, failure usage and lease receipts (E2) | U/F: composed telemetry and local proof. Old clone/install-control build requirements are superseded by current delivery |
| H10a steps 1–3 / D8 | P: retained hash-bound optional wheels, offline installation and fresh replay. N/F: promotion-grade recoverable transitive-lock/reinstall qualification producer and drift/conflict/unavailable-package cases | Preserve trigger for reusable promotion OR measured repeatability/drift, exact installer/platform/dependency basis and H9 consumption. Freeze/hash/fresh replay alone does not close D8 |
| H10b steps 1–4 / D7 | P: scoped source-paired Pearson/simple OLS, effect-bound/multiplicity history and predeclared same-method GDC follow-ups (E8). N/F: selected broader operation families; U/F: operation-specific scientific/held-out comparisons | Retain concrete-need/input/reference gates and per-family eligible/ineligible/build/no-build decisions, not an unconditional promise to build all families |
| H11 original steps 1–4/exit | C: deployment, storage cutover/migration, target confinement/restart proof | Preserve historical receipts and original data. Local lifecycle/reconstruction/controls are H2/H3/H10/H15 obligations, not H11 blockers |
| H12 steps 1–2 | P: pinned deterministic renderer-v3, typed labels/IDs/hashes, populated paths, history/native global receipts, private-byte exclusion (E9) | U/F: broader-operation context utility and final composed trajectory. Rendered output cannot certify novelty |
| H12 steps 3–4 | P: separate publisher/CLI, approved remote, dirty-checkout preservation, three-attempt cap, SHA check, durable failure (E9). U: actual remote publication. N/F: event-to-separate-publisher automation if event-driven publication is required | Service event hooks record export identities; they do not invoke/schedule a separate publisher. Preserve that integration commitment separately from credential/connectivity setup |
| H13 steps 1–3 | P: generated selection/representation cases, versioned native receipts, failures/recall, fresh-condition harness (E10). N/F: much of scientific/method/relation/memory/context corpus and requested metrics. U/F: independent labels/matched-budget utility | Harness currently has science-only, science+Reasoner, science+Jev+Reasoner conditions, not all proposed comparisons. Its declared replication metric counts IDs, not verified independent replication |
| H13 steps 4–5 | N/F + U/F: growing-scale, multi-domain recall, promotion utility, repeated semantic instability, returned D gates and family scientific comparisons | D: report each gate once and let owning H phases consume its identity. Retain partial/failure reporting and model/resource/cost limitations |
| H14 steps 1–2 | P: explicit candidate/default/global/literature policy separation and receipt versioning (E10). C: redo caller split; U/F: independent calibration rationale | Keep delivered cleanup/history. Thresholds are policies, not scientific constants; dead-path removal is conditional, not presumed necessary |
| H14 steps 3–4; H14a steps 1–4 / D5 | D: D3 comparison/extraction from H4a. N/F: repeated-instability experiment, gated calibration/self-consistency/Autoresearch; U/F: measured no-change/adoption disposition | Preserve measured-instability and explicit budget triggers, native distributions/alternatives/fallback, reviewed adoption and no automatic production rewrites |
| H15 steps 1–2, 4 | P: substantial current docs and historical evidence; U/F: all owning-doc truth and full applicable integration verification. Stale descriptions remain | Preserve final documentation/checks/report; this review is not final certification and changes no authoritative status |
| H15 step 3 / R12 integration | P: separate local lifecycle/science/history/export slices. U/F: one exact-basis composed cancer trajectory plus qualified reuse and live publication where required | Preserve invalid/misleading alternative, contradiction/inconclusive outcome, memory-driven next selection, shutdown/reopen and distinct proof categories |

### Scientific additions R1–R12: retain exact unfinished scope

| Addition / owner | Classification and necessary retained acceptance |
| --- | --- |
| R1 / H5 | P: source-linked attempt/outcome memory-v4 for scoped methods/follow-ups/context. U/F: other selected-operation history, relevant failed/inconclusive retrieval, duplicate avoidance, distinct alternatives and new-evidence reopening utility. No inferred absence/negative |
| R2 / H6 | P: owned-input gate and one parsed gene-summary rung. N/F: broader modality/representation generation, matrices and validated transforms/joins; U/F: independent assay/representation recall and automatic discovery |
| R3 / H7 | P: structured need→local method alternatives→route/input assessment. U/F: independently labelled method/design fit, external candidate selection, competing valid methods and held-out utility |
| R4 / H8 | N/F: actual source→canonical callable/CLI/example inspection and runnable reference basis. Metadata references are P; no reference-validation producer found |
| R5 / H9 | P: qualification rejection contract. N/F: proof producers and reusable dispatcher; U/F: independently validated scoped accept/reject and changed-scope reuse. D: consumes R4/R6/D8/H13/local proof, not another qualification stack |
| R6 / H10 | P: controlled execution/replay and scoped exploratory example mechanism. U/F: independent upstream canonical/changed-parameter/invalid-input fidelity; N/F: durable reference-validation production. Replay alone is insufficient |
| R7 / H10b | P: exploratory source-paired effect intervals, explicit family-wise correction, source/denominator/missingness guards. N/F: selected mutation/annotation/burden/TMB, DE/signature/pathway, CNV/association, co-mutation/subtype/clinical, survival, cross-cohort/multi-omic and outlier/prioritization work where gates justify it; U/F: scientific design/controls/family comparisons |
| R8 / H10b | P: predeclared same-method case-paired follow-up intervals, overlap/exposure/coverage guards and outcome history. U/F: reviewed real independent-cohort validation and utility; N/F: other selected methods/representations, falsification/control operations. Replay is not biological replication |
| R9 / H12 | P: bounded literature acquisition and owned completed source-analysis context, native unknown/failure fallback, memory/export. U/F: independent classification, masked rediscovery/new-context/contrary literature truth and decision utility; broader future operations remain scoped work |
| R10 / H13 | P: small generated contract corpus. N/F + U/F: independent scientific truth labels, masked findings/nulls/confounding/leakage/invalid-design/replication/acquisition cases, held-out repeated comparable conditions and marginal Jev resource/benefit reporting |
| R11 / H14 | N/F + U/F: offline reflection/diversity/proximity/branch-budget variants and measured adoption/no-change decision. D: uses H4b/H13/H14a evidence; does not reopen delivered H4 mechanics for non-defects |
| R12 / H15 | U/F: exact source/registry/history/application-basis scientific trajectory composing R1–R11 or justified conditional dispositions, with an invalid alternative and challenge/inconclusive outcome; not proven by independent slice tests |

## Loops, copied gates and closure problems

- **Completion cycles, not a demonstrated runtime dependency loop:**
  H4 completion waits for H6/H7 domain mechanisms and H13/H14 comparisons;
  H7 build names H4 baseline; H14 waits for H4/H6/H7 and H13; H13 returns proof to
  all of them. The plan's build/return distinction permits baseline construction,
  but a scheduler interpreting whole-phase PARTIAL as an unmet prerequisite can
  deadlock this graph. Dependencies must name the delivered mechanism or required
  evidence, rather than whole-phase DONE.
- **H9/H10a/H13:** H9 waits for qualification and utility; H13 must evaluate
  unpromoted candidates before qualified acceptance. Requiring accepted H9 before
  evaluating utility would create a false loop. H5 revision mechanics already
  exist and need not wait for accepted reusable science. H12 can export proposals
  and rejected work without H9 acceptance.
- **Copied gates:** D3 appears in H4a, H14 step 3 and H13 step 5; D8/R5/R6/local
  qualification gates repeat through H5/H9/H9a/H10/H10a/H13/H15. R8/R9 trajectories
  recur in H5/H10b/H12/H13/H15. These are overlapping consumers, not independent
  implementations or repeated experiments. Preserve one production/evidence
  owner and explicit consumer references.
- **Stale unfinished notes:** H2 return acceptance, H2's offload table, H10's
  earlier proof note and open question 5 still request aggregate controls delivered
  in later resource batches. The baseline table still says `SandboxConfig`
  defaults to Docker, but code/config default to local-venv. H5's exit paragraph
  and H11's historical incomplete-target paragraph refer to a governance mismatch
  already repaired by `scoped-governance-v2-local`. Delta still says pins “follow
  H5” although pins exist. Treat recording-time statements as history; retain only
  their genuinely unmet current requirements.
- **Reopened DONE risk:** no evidence justifies reopening H0's historical audit,
  H1's role/tool delivery or H14's caller split. New aggregate controls belong to
  H2/H10; utility/calibration is separate acceptance. F0–F6 remain bounded history
  and protected invariants, not a new implementation queue.
- **Broad PARTIAL hides different closure paths:** H4 mixes delivered frontier,
  missing generation/lifecycle and utility; H6 mixes parser with absent modalities;
  H9 mixes rejection scaffold with missing execution/proof writers; H10 mixes
  landed controls with in-process quotas, conditional families and qualification;
  H13 mixes harness implementation with an unbuilt scientific corpus. No single
  phase label can identify the next executable task or explain why it remains open.
- **Gate disposition is not capability delivery:** measured no-change can close
  a conditional experiment; unavailable data can document a family's current
  ineligibility. Neither closes a still-required baseline capability, accepted
  reusable path or required composed/local proof. Preserve both facts explicitly.

## What the future plan must carry forward

**Build:** in-process Science resource control/Delta telemetry; broader actual
representation generation and selected schemas/transforms; missing portfolio
lifecycle/regeneration; source-bound canonical operation inspection; independent
qualification/reference/utility/local proof producers; supported reusable-method
dispatcher; event-to-isolated-publisher integration if retaining automatic event
publication; missing evaluation cases/metrics and only experimentally justified
D3/D4/D5/D6/D7 extensions.

**Qualify/evaluate:** exact-basis lifecycle/science/memory/next-selection/export
composition; current native WSL2 controls and one complete local receipt;
recoverable fresh dependency qualification; independently reviewed method,
representation, relation, memory, follow-up and literature utility; repeated
semantic/resource comparisons; accepted reuse in a subsequent fresh block; live
source/model/publication connectivity separately. Do not weaken required local
controls because deployment was cancelled.

**Preserve as delivered/history:** landed mechanisms above; all valid unfinished
D1–D8/R1–R12 obligations; F0–F6 invariants and their bounded historical evidence;
recording-time versions/counts/native/target observations; original local/remote
data and honest missing bytes/pins. R/Conda/GPU/pathology/wet-lab and unapproved
sources remain outside stage. Remote historical completeness remains unknown and
needs recovery work only if an exact required input/history depends on it.

## Verification and limits

- `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider -o addopts='' tests/invariants/test_boundaries.py tests/invariants/test_persistence.py tests/invariants/test_live_mode.py tests/invariants/test_evaluation.py -q`
  — **167 passed in 155.21s**. These four owning files prove local contracts; this
  is not the entire suite or a scientific utility evaluation.
- `.venv/Scripts/python.exe -B scripts/check_architecture.py` — passed.
- `git diff --check` — passed; Git emitted existing LF→CRLF notices.
- Full plan read, worktree/HEAD, code callers/config/routes, primary regressions
  and retained generated evaluation artifacts inspected. No upstream repository,
  external account, original database, provider or publisher was accessed; no
  dependency setup, Docker run, deployment or native WSL probe was performed.
- The plan and original worktree changes are preserved. Proposed planning changes
  were proposed in [the now-rejected archived ADR](ADR/PLAN_STATUS.md);
  neither this report nor that rejected proposal changes authoritative status.
