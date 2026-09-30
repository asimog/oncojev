"""Application policy boundary between append-only records and the API.

Read models are assembled here from typed records. The application never admits
evidence, never runs science, and never mutates append-only history; those
operations remain in the domain and are unreachable from the API.
"""

from typing import Any

from src.persistence.records import RecordKind
from src.persistence.reconstruct import BlockReconstruction, reconstruct_block
from src.persistence.repository import ResearchRepository
from src.persistence.store import SqliteResearchStore


class ResearchApplication:
    def __init__(self, store: SqliteResearchStore) -> None:
        self._store = store
        self.repository = ResearchRepository(store)

    def health(self) -> dict[str, Any]:
        return {"status": "ok", "records": self._store.count()}

    def overview(self) -> dict[str, Any]:
        latest_cycle = self._store.latest(RecordKind.CYCLE)
        return {
            "records": self._store.count(),
            "blocks": len(self._store.block_ids()),
            "cycles": len(self._store.records(kind=RecordKind.CYCLE)),
            "dossiers": len(self._store.records(kind=RecordKind.DOSSIER)),
            "evidence": len(self._store.records(kind=RecordKind.EVIDENCE)),
            "latest_cycle": latest_cycle.payload if latest_cycle else None,
        }

    def blocks(self) -> tuple[dict[str, Any], ...]:
        views = []
        for block_id in self._store.block_ids():
            block = self._store.latest(RecordKind.BLOCK, block_id=block_id)
            dossier = self._store.latest(RecordKind.DOSSIER, block_id=block_id)
            views.append(
                {
                    "block_id": block_id,
                    "block": block.payload if block else None,
                    "has_dossier": dossier is not None,
                }
            )
        return tuple(views)

    def reconstruction(self, block_id: str) -> BlockReconstruction:
        return reconstruct_block(self._store, block_id)

    def research_memory(self) -> tuple[dict[str, Any], ...]:
        return tuple(record.payload for record in self._store.records(kind=RecordKind.RESEARCH_MEMORY))
