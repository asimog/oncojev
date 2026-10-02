# Task Log

Completed verification only. Keep the most recent completed task and its immediate
predecessor, newest first; append displaced entries intact to
[Previous Task Log](Archive/PREVIOUS_TASK_LOG.md). The architecture checker rejects
a third level-two entry. Future work belongs only in IMPLEMENTATION_PLAN.

## 2026-10-02 — Archive surplus docs and enforce a two-task log

Result: Archived nine docs, including the retired ADRs/guide and all previous log
content. Restored all ten READMEs outside `docs/` and removed their empty archive
directories after scope correction. Root navigation and one subsystem link were
then updated. Package metadata and native-copy inputs remain unchanged.
AGENTS and the existing checker enforce docs-only archiving, scoped historical
exceptions and at most two completed log entries. The testing ADR now compares
current/proposed limits and separates a 90 s block allowance from a 120 s observation
target; recommends WSL2/local_venv for full execution and Windows for fast contracts.

Basis: HEAD `2302b4bcc0ede6b94da466f5b3d6342548271b6c` plus the existing worktree.
Completed Task 18 removed from the plan. Runtime/scientific records are unchanged.
Proof: [previous log](Archive/PREVIOUS_TASK_LOG.md), [ADR](PROPOSED_ADR_FAST_LOCAL_TESTING.md),
checker/tests; local relocation snapshot at
`var/document-cleanup-02e3557814c741599a5cf71894a98c47/baseline.json` (ignored).

Checks: `.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider -o addopts='' tests/invariants/test_architecture_checks.py tests/invariants/test_repo_index.py tests/invariants/test_native_setup.py -q`
— 51 passed in 14.75 s. The third-entry case first failed because the old checker
accepted it; the revised checker rejects it and preserves external READMEs.
Full and `--docs-only` architecture checks passed; projection semantics retained,
only reviewed canonical hashes refreshed. Relocation/body/hash preservation and
`git diff --check` passed.
Limits: Local governance/fixture proof only; no native/provider execution or platform
speed measurement. Testing-profile implementation remains proposed in Task 17.

## 2026-10-02 — Investigate the fast local testing proposal

Result: Traced environment/config/path, download/resource, lifecycle, admission and
qualification owners. Appended the investigation and reconciled Task 17. No runtime
or actual local environment settings changed; decision remained PROPOSED.

Basis: HEAD `2302b4bcc0ede6b94da466f5b3d6342548271b6c` plus the existing worktree.
Proof: [current testing ADR](PROPOSED_ADR_FAST_LOCAL_TESTING.md).
Checks: explicit active document/ADR link, whitespace and earlier-plan preservation
checks passed (exit 0); `git diff --check` passed (exit 0). Documentation-only
architecture checking failed (exit 1) on the pre-existing stale AGENTS projection hash.
Limits: Source/document assessment only; no behavior, provider or native qualification.
