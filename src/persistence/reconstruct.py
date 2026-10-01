"""Deterministic reconstruction of a block for provenance and review.

Reconstruction reads append-only records and returns typed views. It never
re-runs research, never admits evidence, and never mutates history.
"""

from typing import Any

from pydantic import BaseModel

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


def reconstruct_block(store: SqliteResearchStore, block_id: str) -> BlockReconstruction:
    def payloads(kind: RecordKind) -> tuple[dict[str, Any], ...]:
        return tuple(record.payload for record in store.records(kind=kind, block_id=block_id))

    block_record = store.latest(RecordKind.BLOCK, block_id=block_id)
    dossier = store.latest(RecordKind.DOSSIER, block_id=block_id)
    return BlockReconstruction(
        block_id=block_id,
        block=block_record.payload if block_record else None,
        state_revisions=payloads(RecordKind.STATE_REVISION),
        capability_invocations=payloads(RecordKind.CAPABILITY_INVOCATION),
        measurements=payloads(RecordKind.MEASUREMENT),
        evidence=payloads(RecordKind.EVIDENCE),
        jev_outputs=payloads(RecordKind.JEV_OUTPUT),
        jev_failures=payloads(RecordKind.JEV_FAILURE),
        artifacts=payloads(RecordKind.ARTIFACT),
        ledger=payloads(RecordKind.LEDGER_EVENT),
        dossier=dossier.payload if dossier else None,
        complete=bool(block_record and block_record.payload.get("status") == "complete" and dossier is not None),
    )
