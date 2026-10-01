"""Domain-aware persistence adapters.

Each method maps one canonical domain object to one append-only record. The
repository cannot create evidence: `record_evidence` accepts an already-admitted
`ScientificEvidence` and stores it verbatim. Admission itself stays in
`src/science/admission.py` and is unreachable from storage or API code.
"""

from typing import Any
from src.block.models import CycleStatus, DirectorOutcome, JevBlock

from src.dossier.models import JevBlockDossier
from src.evidence.models import ScientificEvidence
from src.jev.models import JevDecision, JevExecutionFailure, JevCallReceipt
from src.ledger.events import LedgerEvent
from src.persistence.records import RecordKind, StoredRecord
from src.persistence.store import SqliteResearchStore
from src.researcher.state import ResearchState
from src.science.models import MeasuredResult
from src.visualization.models import FigureArtifact
from src.sources.models import AcquisitionRecord, LiteratureSearchResult
from src.oncolab.registry import OncoLabVerificationRecord, IndexReceipt
from src.persistence.references import resolve_reference


class ResearchRepository:
    def __init__(self, store: SqliteResearchStore) -> None:
        self._store = store

    @property
    def store(self) -> SqliteResearchStore:
        return self._store

    def _append(self, kind: RecordKind, record_id: str, payload: dict[str, Any], block_id: str | None = None) -> StoredRecord:
        return self._store.append(StoredRecord(kind=kind, record_id=record_id, payload=payload, block_id=block_id))

    def record_cycle_start(self, mission_id: str, mode: str, direction: str, *, cycle_id: str | None = None) -> StoredRecord:
        return self._append(RecordKind.CYCLE_START, cycle_id or mission_id, {"mode": mode, "direction": direction, "mission_id": mission_id})

    def record_cycle(self, mission_id: str, mode: str, direction: str, block_ids: tuple[str, ...], *, status: CycleStatus = CycleStatus.COMPLETE, error_type: str | None = None, director_outcome: DirectorOutcome = DirectorOutcome.RETURNED, director_error_type: str | None = None, cycle_id: str | None = None) -> StoredRecord:
        receipt_id = cycle_id or mission_id
        existing = next((r for r in self.store.records(kind=RecordKind.CYCLE) if r.record_id == receipt_id), None)
        if existing is not None:
            return existing
        return self._append(RecordKind.CYCLE, receipt_id, {"mission_id": mission_id, "mode": mode, "direction": direction, "block_ids": list(block_ids), "status": CycleStatus(status).value, "error_type": error_type, "director_outcome": director_outcome.value, "director_error_type": director_error_type})

    def record_terminal(self, block: JevBlock, dossier: JevBlockDossier) -> None:
        """Atomically append closure and dossier; a dossier by itself is insufficient."""
        latest = self.store.latest(RecordKind.BLOCK, block_id=block.block_id)
        saved = self.store.latest(RecordKind.DOSSIER, block_id=block.block_id)
        payload = block.model_dump(mode="json")
        summary = dossier.model_dump(mode="json")
        if latest and saved and latest.payload == payload and saved.payload == summary:
            return
        self.store.append_many((
            StoredRecord(kind=RecordKind.BLOCK, record_id=block.block_id, block_id=block.block_id, payload=payload),
            StoredRecord(kind=RecordKind.DOSSIER, record_id=block.block_id, block_id=block.block_id, payload=summary),
        ))

    def record_block(self, block: Any) -> StoredRecord:
        return self._append(RecordKind.BLOCK, block.block_id, block.model_dump(mode="json"), block.block_id)

    def record_state_revision(self, state: ResearchState) -> StoredRecord:
        revision = len(self._store.records(kind=RecordKind.STATE_REVISION, block_id=state.block_id))
        return self._append(RecordKind.STATE_REVISION, f"{state.block_id}:{revision}", state.model_dump(mode="json"), state.block_id)

    def record_immutable(self, kind: RecordKind, record_id: str, value, block_id: str | None) -> StoredRecord:
        payload = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
        matches = [r for r in self.store.records(kind=kind) if r.record_id == record_id]
        if matches:
            if matches[-1].payload != payload or matches[-1].block_id != block_id:
                raise ValueError("immutable input identity cannot be rebound")
            return matches[-1]
        return self._append(kind, record_id, payload, block_id)

    def record_acquisition(self, block_id: str, record: AcquisitionRecord) -> StoredRecord:
        return self.record_immutable(RecordKind.ACQUISITION, record.acquisition_id, record, block_id)

    def record_literature(self, block_id: str, record: LiteratureSearchResult) -> StoredRecord:
        return self.record_immutable(RecordKind.LITERATURE, record.context_id, record, block_id)

    def resolve_acquisition(self, block_id: str, acquisition_id: str) -> AcquisitionRecord:
        matches = [r for r in self.store.records(kind=RecordKind.ACQUISITION, block_id=block_id) if r.record_id == acquisition_id]
        if not matches:
            raise ValueError("acquisition is not owned by this block")
        return AcquisitionRecord.model_validate(matches[-1].payload)

    def record_verification(self, record: OncoLabVerificationRecord) -> StoredRecord:
        resolve_reference(self.store, record.execution_reference)
        return self.record_immutable(RecordKind.VERIFICATION, f"{record.capability_id}:{record.verification_id}", record,
                                     record.execution_reference.block_id)

    def record_index_receipt(self, receipt: IndexReceipt) -> StoredRecord:
        return self._append(RecordKind.INDEX_RECEIPT, receipt.receipt_id, receipt.model_dump(mode="json"), receipt.block_id)

    def record_measurement(self, result: MeasuredResult, block_id: str | None = None) -> StoredRecord:
        return self._append(RecordKind.MEASUREMENT, result.analysis_id, result.model_dump(mode="json"), block_id)

    def record_evidence(self, evidence: ScientificEvidence, block_id: str | None = None) -> StoredRecord:
        """Store one already-admitted evidence item; never admits on its own."""
        return self._append(RecordKind.EVIDENCE, evidence.evidence_id, evidence.model_dump(mode="json"), block_id)

    def record_jev_decisions(self, block_id: str, decisions: tuple[JevDecision, ...]) -> StoredRecord:
        record_id = f"{block_id}:jev:{len(self._store.records(kind=RecordKind.JEV_OUTPUT, block_id=block_id))}"
        return self._append(RecordKind.JEV_OUTPUT, record_id, {"decisions": [decision.model_dump(mode="json") for decision in decisions]}, block_id)

    def record_jev_failure(self, block_id: str, failures: tuple[JevExecutionFailure, ...]) -> StoredRecord:
        record_id = f"{block_id}:jev-failure:{len(self._store.records(kind=RecordKind.JEV_FAILURE, block_id=block_id))}"
        return self._append(RecordKind.JEV_FAILURE, record_id, {"failures": [failure.model_dump(mode="json") for failure in failures]}, block_id)

    def record_jev_call(self, receipt: JevCallReceipt) -> StoredRecord:
        return self._append(RecordKind.JEV_CALL, receipt.call_id, receipt.model_dump(mode="json"), receipt.block_id)

    def record_ledger_event(self, block_id: str, event: LedgerEvent) -> StoredRecord:
        return self._append(RecordKind.LEDGER_EVENT, event.event_id, event.model_dump(mode="json"), block_id)

    def record_artifact(self, block_id: str, artifact: FigureArtifact) -> StoredRecord:
        return self._append(RecordKind.ARTIFACT, artifact.artifact_id, artifact.model_dump(mode="json"), block_id)

    def record_dossier(self, dossier: JevBlockDossier) -> StoredRecord:
        return self._append(RecordKind.DOSSIER, dossier.block_id, dossier.model_dump(mode="json"), dossier.block_id)

    def record_research_memory(self, mission_id: str, summary: str, provenance: tuple[str, ...], *, cycle_id: str | None = None) -> StoredRecord:
        record_id = f"{mission_id}:memory:{len(self._store.records(kind=RecordKind.RESEARCH_MEMORY))}"
        return self._append(RecordKind.RESEARCH_MEMORY, record_id, {"summary": summary, "provenance": list(provenance), "mission_id": mission_id, "cycle_id": cycle_id})
