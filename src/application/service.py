"""Application policy boundary between append-only records and the API.

Read models are assembled here from typed records. The application never admits
evidence, never runs science, and never mutates append-only history; those
operations remain in the domain and are unreachable from the API.
"""

from typing import Any

from src.persistence.records import RecordKind
from src.persistence.reconstruct import BlockReconstruction, reconstruct_block, effective_cycle
from src.persistence.repository import ResearchRepository
from src.persistence.store import SqliteResearchStore
from src.memory.service import ResearchMemory


class ResearchApplication:
    def __init__(self, store: SqliteResearchStore) -> None:
        self._store = store
        self.repository = ResearchRepository(store)

    def health(self) -> dict[str, Any]:
        return {"status": "ok", "records": self._store.count()}

    def overview(self) -> dict[str, Any]:
        with self._store.transaction():
            latest_cycle = self._store.latest(RecordKind.CYCLE)
            return {
                "records": self._store.count(),
                "blocks": len(self._store.block_ids()),
                "cycles": len(self._store.records(kind=RecordKind.CYCLE)),
                "dossiers": len(self._store.records(kind=RecordKind.DOSSIER)),
                "evidence": len(self._store.records(kind=RecordKind.EVIDENCE)),
                "latest_cycle": effective_cycle(self._store, latest_cycle.payload) if latest_cycle else None,
                "data_provenance": "synthetic_fixture" if self._store.records(kind=RecordKind.ACQUISITION) and all(r.payload.get("origin")=="synthetic" for r in self._store.records(kind=RecordKind.ACQUISITION)) else "retained_records",
                "source_activity": self._source_activity(),
            }

    def _source_activity(self) -> dict[str,int]:
        events=[r.payload for r in self._store.records(kind=RecordKind.LEDGER_EVENT)]
        attempts={e["payload"].get("invocation_id") for e in events if e.get("event_type")=="CapabilityInvocation" and e.get("payload",{}).get("capability_id","").startswith(("source.","literature."))}
        attempts.discard(None)
        success={e["payload"].get("invocation_id") for e in events if e.get("event_type")=="CapabilityResult"}
        failed={e["payload"].get("invocation_id") for e in events if e.get("event_type")=="CapabilityFailure"}
        return {"attempts":len(attempts),"successes":len(attempts & success),"failures":len(attempts & failed),"unresolved":len(attempts-success-failed)}

    def blocks(self) -> tuple[dict[str, Any], ...]:
        views = []
        for block_id in self._store.block_ids():
            view = reconstruct_block(self._store, block_id)
            views.append(
                {
                    "block_id": block_id,
                    "block": view.block,
                    "has_dossier": view.dossier is not None,
                    "run_outcome": view.run_outcome.value,
                    "complete": view.complete,
                }
            )
        return tuple(views)

    def reconstruction(self, block_id: str) -> BlockReconstruction:
        view=reconstruct_block(self._store, block_id)
        def metadata(value):
            if isinstance(value,list):return [metadata(v) for v in value]
            if isinstance(value,dict):
                artifact="content_base64" in value and {"artifact_id","byte_sha256","size_bytes","block_id"}.issubset(value)
                result={k:metadata(v) for k,v in value.items() if not (artifact and k=="content_base64")}
                if artifact:result["content_bytes_omitted"]=True
                return result
            return value
        # UI/API views retain input identity; exact bytes remain in owned durable storage.
        return BlockReconstruction.model_validate(metadata(view.model_dump(mode="json")))

    def research_memory(self) -> tuple[dict[str, Any], ...]:
        views = ResearchMemory(self._store).context("", limit=20).digests
        if not views:
            # Read-only compatibility for archives not yet backfilled by the
            # autonomous service. Narrative is explicitly unverified context.
            return tuple({"summary": "Legacy prose (unverified context): " + r.payload.get("summary", "")[:1000],
                          "provenance": ["legacy-prose", r.record_id], "epistemic_status": "legacy_prose"}
                         for r in self._store.records(kind=RecordKind.RESEARCH_MEMORY)[-20:])
        return tuple({**d, "summary": f"{d['cycle_status']}: " + "; ".join(d["objectives"] or [d["direction"]]) +
                       (f"; failure: {d['failure_reason']}" if d["failure_reason"] else ""),
                       "provenance": [d["version"], d["digest_id"]]} for d in views)
