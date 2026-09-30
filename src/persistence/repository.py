"""Domain-aware persistence adapters.

Each method maps one canonical domain object to one append-only record. The
repository cannot create evidence: `record_evidence` accepts an already-admitted
`ScientificEvidence` and stores it verbatim. Admission itself stays in
`src/science/admission.py` and is unreachable from storage or API code.
"""

from typing import Any

from src.dossier.models import JevBlockDossier
from src.evidence.models import ScientificEvidence
from src.jev.models import JevDecision, JevExecutionFailure
from src.ledger.events import LedgerEvent
from src.persistence.records import RecordKind, StoredRecord
from src.persistence.store import SqliteResearchStore
from src.researcher.state import ResearchState
from src.science.models import MeasuredResult
from src.visualization.models import FigureArtifact


class ResearchRepository:
    def __init__(self, store: SqliteResearchStore) -> None:
        self._store = store

    @property
    def store(self) -> SqliteResearchStore:
        return self._store

    def _append(self, kind: RecordKind, record_id: str, payload: dict[str, Any], block_id: str | None = None) -> StoredRecord:
        return self._store.append(StoredRecord(kind=kind, record_id=record_id, payload=payload, block_id=block_id))

    def record_cycle(self, mission_id: str, mode: str, direction: str, block_ids: tuple[str, ...]) -> StoredRecord:
        return self._append(RecordKind.CYCLE, mission_id, {"mode": mode, "direction": direction, "block_ids": list(block_ids)})

    def record_block(self, block: Any) -> StoredRecord:
        return self._append(RecordKind.BLOCK, block.block_id, block.model_dump(mode="json"), block.block_id)

    def record_state_revision(self, state: ResearchState) -> StoredRecord:
        revision = len(self._store.records(kind=RecordKind.STATE_REVISION, block_id=state.block_id))
        return self._append(RecordKind.STATE_REVISION, f"{state.block_id}:{revision}", state.model_dump(mode="json"), state.block_id)

    def record_capability_invocation(self, block_id: str, capability_id: str, detail: dict[str, Any]) -> StoredRecord:
        record_id = f"{block_id}:{capability_id}:{len(self._store.records(kind=RecordKind.CAPABILITY_INVOCATION, block_id=block_id))}"
        return self._append(RecordKind.CAPABILITY_INVOCATION, record_id, {"capability_id": capability_id, **detail}, block_id)

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

    def record_ledger_event(self, block_id: str, event: LedgerEvent) -> StoredRecord:
        return self._append(RecordKind.LEDGER_EVENT, event.event_id, event.model_dump(mode="json"), block_id)

    def record_artifact(self, block_id: str, artifact: FigureArtifact) -> StoredRecord:
        return self._append(RecordKind.ARTIFACT, artifact.artifact_id, artifact.model_dump(mode="json"), block_id)

    def record_dossier(self, dossier: JevBlockDossier) -> StoredRecord:
        return self._append(RecordKind.DOSSIER, dossier.block_id, dossier.model_dump(mode="json"), dossier.block_id)

    def record_research_memory(self, mission_id: str, summary: str, provenance: tuple[str, ...]) -> StoredRecord:
        record_id = f"{mission_id}:memory:{len(self._store.records(kind=RecordKind.RESEARCH_MEMORY))}"
        return self._append(RecordKind.RESEARCH_MEMORY, record_id, {"summary": summary, "provenance": list(provenance)})
