"""Deterministic reconstruction of a block for provenance and review.

Reconstruction reads append-only records and returns typed views. It never
re-runs research, never admits evidence, and never mutates history.
"""

from typing import Any

from pydantic import BaseModel
from src.block.models import BlockStatus, RunOutcome, run_outcome
from src.ledger.events import LedgerEvent

from src.persistence.records import RecordKind
from src.persistence.store import SqliteResearchStore


class BlockReconstruction(BaseModel, frozen=True):
    block_id: str
    block: dict[str, Any] | None
    state_revisions: tuple[dict[str, Any], ...]
    capability_invocations: tuple[dict[str, Any], ...]
    measurements: tuple[dict[str, Any], ...]
    evidence: tuple[dict[str, Any], ...]
    jev_outputs: tuple[dict[str, Any], ...]
    jev_failures: tuple[dict[str, Any], ...]
    artifacts: tuple[dict[str, Any], ...]
    ledger: tuple[dict[str, Any], ...]
    dossier: dict[str, Any] | None
    complete: bool
    run_outcome: RunOutcome
    outcome_inferred: bool = False


def reconstruct_block(store: SqliteResearchStore, block_id: str) -> BlockReconstruction:
    def payloads(kind: RecordKind) -> tuple[dict[str, Any], ...]:
        return tuple(record.payload for record in store.records(kind=kind, block_id=block_id))

    block_record = store.latest(RecordKind.BLOCK, block_id=block_id)
    dossier = store.latest(RecordKind.DOSSIER, block_id=block_id)
    events = tuple(LedgerEvent.model_validate(p) for p in payloads(RecordKind.LEDGER_EVENT))
    outcome = run_outcome(events)
    block_payload = dict(block_record.payload) if block_record else None
    dossier_payload = dict(dossier.payload) if dossier else None
    correction = store.latest(RecordKind.OUTCOME_CORRECTION, block_id=block_id)
    inferred = False
    if block_payload:
        if correction:
            block_payload.update(correction.payload["effective_block"])
        elif block_payload.get("status") == "complete" and outcome is not RunOutcome.COMPLETED:
            inferred = True
            block_payload.update(status="failed" if outcome is RunOutcome.FAILED else "interrupted",
                                 termination_reason="legacy_researcher_failed" if outcome is RunOutcome.FAILED else "legacy_completion_unverified")
        if dossier_payload:
            dossier_payload.update(lifecycle_status=block_payload["status"], run_outcome=outcome.value,
                                   termination_reason=block_payload.get("termination_reason") or dossier_payload["termination_reason"])
            dossier_payload.setdefault("objective_attainment", "unknown")
            dossier_payload["operational_failures"] = [
                {"event_type": event.event_type, **event.payload} for event in events
                if event.event_type in {"ResearcherRunFailed", "DirectorRunFailed", "DirectorRunTruncated", "InterruptedBlockRecovered"}]
    return BlockReconstruction(
        block_id=block_id,
        block=block_payload,
        state_revisions=payloads(RecordKind.STATE_REVISION),
        capability_invocations=payloads(RecordKind.CAPABILITY_INVOCATION),
        measurements=payloads(RecordKind.MEASUREMENT),
        evidence=payloads(RecordKind.EVIDENCE),
        jev_outputs=payloads(RecordKind.JEV_OUTPUT),
        jev_failures=payloads(RecordKind.JEV_FAILURE),
        artifacts=payloads(RecordKind.ARTIFACT),
        ledger=payloads(RecordKind.LEDGER_EVENT),
        dossier=dossier_payload,
        run_outcome=outcome,
        outcome_inferred=inferred,
        complete=bool(block_payload and block_payload.get("status") == BlockStatus.COMPLETE.value and outcome is RunOutcome.COMPLETED and dossier is not None),
    )


def effective_cycle(store: SqliteResearchStore, payload: dict[str, Any]) -> dict[str, Any]:
    """Expose legacy contradictions without rewriting their historical receipts."""
    result = dict(payload)
    result.setdefault("director_outcome", "unknown")
    if result.get("status") == "complete":
        views = [reconstruct_block(store, block_id) for block_id in result.get("block_ids", [])]
        if len(views) != 1 or not all(view.complete for view in views):
            result["status"] = "failed" if any(view.run_outcome is RunOutcome.FAILED or (view.block and view.block.get("status") == "failed") for view in views) else "incomplete"
            result["outcome_inferred"] = True
            failures = [e for view in views for e in view.ledger if e.get("event_type") == "ResearcherRunFailed"]
            if failures:
                result["error_type"] = failures[0]["payload"].get("error_type", "ResearcherRunFailed")
    return result
