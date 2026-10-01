"""Durable autonomous service composition."""

from __future__ import annotations

import asyncio
import os
import threading
from datetime import UTC, datetime
from pathlib import Path

from src.runtime.resources import ServiceResources
from src.api.server import create_server
from src.application.service import ResearchApplication
from src.block.models import BlockStatus, CycleStatus, DirectorOutcome, JevBlock, RunOutcome, run_outcome
from src.config.environment import load_local_environment
from src.config.loader import load_models_config, load_runtime_config
from src.dossier.builder import build_dossier
from src.ledger.events import LedgerEvent
from src.persistence.records import RecordKind, StoredRecord
from src.persistence.reconstruct import reconstruct_block
from src.researcher.state import ResearchState
from src.persistence.repository import ResearchRepository
from src.persistence.store import SqliteResearchStore
from src.runtime.cycle import CycleResult, run_cycle_async
from src.runtime.pydantic_ai.factory import build_system
from src.memory.service import ResearchMemory


DEFAULT_DIRECTION = "Investigate a public oncology signal and admit only source-bound reproducible evidence."


def recover_interrupted_blocks(repository: ResearchRepository) -> tuple[str, ...]:
    """Close previously active blocks honestly after process interruption."""
    recovered: list[str] = []
    for block_id in repository.store.block_ids():
        latest = repository.store.latest(RecordKind.BLOCK, block_id=block_id)
        if latest is None:
            continue
        view = reconstruct_block(repository.store, block_id)
        if view.outcome_inferred:
            # Link the correction to every original outcome-bearing record. No
            # historical dossier, cycle, measurement or evidence is modified.
            originals = [r.seq for r in repository.store.records(block_id=block_id)
                         if r.kind in {RecordKind.BLOCK, RecordKind.DOSSIER, RecordKind.LEDGER_EVENT}]
            originals.extend(r.seq for r in repository.store.records(kind=RecordKind.CYCLE)
                             if block_id in r.payload.get("block_ids", []))
            repository.store.append(StoredRecord(kind=RecordKind.OUTCOME_CORRECTION,
                record_id=f"{block_id}:outcome-correction", block_id=block_id,
                payload={"original_seqs": originals, "reason": "legacy_completion_contradicts_run_receipts",
                         "effective_block": {"status": view.block["status"], "termination_reason": view.block["termination_reason"]}}))
            if view.dossier is not None:
                continue
        block = JevBlock.model_validate(view.block)
        terminal = block.status in {BlockStatus.COMPLETE, BlockStatus.FAILED, BlockStatus.INTERRUPTED}
        if terminal and view.dossier is not None:
            continue
        stored_events = tuple(LedgerEvent.model_validate(record.payload)
            for record in repository.store.records(kind=RecordKind.LEDGER_EVENT, block_id=block_id))
        if not terminal:
            failed = run_outcome(stored_events) is RunOutcome.FAILED
            block = block.model_copy(update={"status": BlockStatus.FAILED if failed else BlockStatus.INTERRUPTED,
                                            "termination_reason": "researcher_failed" if failed else "recovered_after_interruption"})
        elif block.status is BlockStatus.COMPLETE:
            block = block.model_copy(update={"status": BlockStatus.INTERRUPTED, "termination_reason": "recovered_after_interruption"})
        if not any(e.event_type == "InterruptedBlockRecovered" for e in stored_events):
            event = LedgerEvent(
                event_type="InterruptedBlockRecovered",
                occurred_at=datetime.now(UTC),
                payload={"block_id": block_id, "reason": "process_restart"},
            )
            repository.record_ledger_event(block_id, event)
            stored_events = (*stored_events, event)
        state_record = repository.store.latest(RecordKind.STATE_REVISION, block_id=block_id)
        state = ResearchState.model_validate(state_record.payload) if state_record else None
        evidence_records={r.record_id:r.payload for r in repository.store.records(kind=RecordKind.EVIDENCE,block_id=block_id)}
        repository.record_terminal(block, build_dossier(block, stored_events, state, block.termination_reason or "recovered_after_interruption",evidence_records=evidence_records))
        recovered.append(block_id)
    finished = {r.record_id for r in repository.store.records(kind=RecordKind.CYCLE)}
    for started in repository.store.records(kind=RecordKind.CYCLE_START):
        if started.record_id in finished:
            continue
        allocated = [r.block_id for r in repository.store.records(kind=RecordKind.BLOCK)
                     if r.payload.get("cycle_id") == started.record_id or
                     (not r.payload.get("cycle_id") and r.payload.get("mission_id") == started.record_id)]
        allocated.extend(r.block_id for r in repository.store.records(kind=RecordKind.LEDGER_EVENT)
                          if r.payload.get("event_type") == "DirectorBlockAllocated"
                          and (r.payload.get("payload", {}).get("cycle_id") == started.record_id or
                               (not r.payload.get("payload", {}).get("cycle_id") and r.payload.get("payload", {}).get("mission_id") == started.record_id)))
        block_ids = tuple(dict.fromkeys(allocated))
        views = [reconstruct_block(repository.store, block_id) for block_id in block_ids]
        failures = [e for view in views for e in view.ledger if e.get("event_type") in {"ResearcherRunFailed", "DirectorRunFailed"}]
        failed = bool(failures) or any(view.block and view.block["status"] == "failed" for view in views)
        error_type = failures[0]["payload"].get("error_type", "ProcessInterrupted") if failures else "ProcessInterrupted"
        repository.record_cycle(started.payload.get("mission_id", started.record_id), started.payload["mode"], started.payload["direction"], block_ids,
                                status=CycleStatus.FAILED if failed else CycleStatus.INCOMPLETE, error_type=error_type,
                                director_outcome=DirectorOutcome.INTERRUPTED, cycle_id=started.record_id)
        finished.add(started.record_id)
    return tuple(recovered)


class AutonomousService:
    def __init__(self, root: Path, database_path: Path) -> None:
        load_local_environment(root)
        database_path.parent.mkdir(parents=True, exist_ok=True)
        self.root = root
        self.store = SqliteResearchStore(database_path)
        self.repository = ResearchRepository(self.store)
        self.application = ResearchApplication(self.store)
        self.models = load_models_config(root / "config" / "models.yaml")
        self.policy = load_runtime_config(root / "config" / "runtime.yaml")
        recover_interrupted_blocks(self.repository)
        ResearchMemory(self.store).backfill()
        self.resources = ServiceResources(max_file_bytes=self.policy.block.max_download_bytes,
            max_block_download_bytes=self.policy.resources.max_block_download_bytes,
            max_service_download_bytes=self.policy.resources.max_service_download_bytes,
            max_workspace_bytes=self.policy.resources.max_workspace_bytes,
            max_durable_artifact_bytes=self.policy.resources.max_durable_artifact_bytes,
            minimum_free_disk_bytes=self.policy.resources.minimum_free_disk_bytes)
        self._last_system = None
        self.director = None
        self._loop_runner = asyncio.Runner()
        self._cycle_lock = asyncio.Lock()
        self._owner_loop = None

    async def _run_once(self, direction: str = DEFAULT_DIRECTION) -> CycleResult:
        recover_interrupted_blocks(self.repository)
        if self.policy.retention.enabled:
            from src.persistence.retention import cleanup_workspaces
            try:
                results=cleanup_workspaces(self.repository,self.root / "var" / "workspaces",
                    minimum_age_seconds=self.policy.retention.minimum_age_seconds,max_archive_bytes=self.policy.retention.max_archive_bytes,
                    max_workspaces=self.policy.retention.max_workspaces)
                for result in results:
                    if result["status"]!="removed":print(f"WORKSPACE CLEANUP {result['status']}: {result['error_type']}",flush=True)
            except Exception as error:
                print(f"WORKSPACE RETENTION UNAVAILABLE: {type(error).__name__}",flush=True)
        system = build_system(self.models, self.policy, repository=self.repository, director=self.director, resources=self.resources)
        self._last_system = system
        self.director = system.agents.director
        try:
            return await run_cycle_async(system, direction, repository=self.repository, mission_id=f"mission-{self.store.count() + 1}")
        finally:
            await asyncio.gather(*(client.aclose() for client in
                (system.runtime.gdc, system.runtime.xena, system.runtime.literature)))

    async def run_once_async(self, direction: str = DEFAULT_DIRECTION) -> CycleResult:
        loop = asyncio.get_running_loop()
        if self._owner_loop is not None and self._owner_loop is not loop:
            raise RuntimeError("service lifecycle belongs to another event loop")
        self._owner_loop = loop
        if self._cycle_lock.locked():
            raise RuntimeError("one service cycle is already active")
        async with self._cycle_lock:
            return await self._run_once(direction)

    def run_once(self, direction: str = DEFAULT_DIRECTION) -> CycleResult:
        return self._loop_runner.run(self.run_once_async(direction))

    async def _serve_cycles(self, direction: str, interval_seconds: int) -> None:
        while True:
            try:
                await self.run_once_async(direction)
            except Exception as error:
                print(f"AUTONOMOUS CYCLE FAILED: {type(error).__name__}", flush=True)
                active = self._last_system.runtime.active_research if self._last_system else None
                if active is None or not active.finished.is_set():
                    await asyncio.sleep(interval_seconds)
                    continue
                await self._post_block_review(direction)
                continue
            await self._post_block_review(direction)
            # An early finish is an event, not a reason to wait out its deadline.
            # The next real allocation uses unchanged deterministic defaults.


    async def _post_block_review(self, direction):
        async with self._cycle_lock:
            await self._review_terminal(direction)

    async def _review_terminal(self, direction):
        from src.runtime.pydantic_ai.contracts import DirectorDeps
        from src.block.models import ServiceResearchState
        from src.provenance import canonical_bytes
        system = self._last_system
        active = system.runtime.active_research if system else None
        if active is None or not active.finished.is_set():
            return
        runtime = system.runtime
        if any(e.event_type == "PostBlockReviewStarted" and e.payload.get("run_id") == active.run_id
               for e in runtime.manager.ledger(active.block_id).history()):
            return
        runtime.append_event(active.block_id, "PostBlockReviewStarted", {"run_id": active.run_id})
        runtime.set_service_state(ServiceResearchState.POST_BLOCK_REVIEW, cause=active.run_id)
        prompt = ("Researcher terminal event. Review these persisted changes for the next investigation. "
                  "Do bounded global work and yield; Python starts the next allocation cycle. "
                  "Do not allocate or launch another block in this review turn. Broad direction: " + direction +
                  "\nBlockDelta (reference-linked derived context, never evidence):\n" +
                  canonical_bytes(active.delta.model_dump(mode="json") if active.delta else {}).decode())
        try:
            result = await system.agents.director.run(prompt, deps=DirectorDeps(runtime),
                usage=runtime.director_usage, usage_limits=runtime.usage_limits("director"))
            if result.output:
                self.repository.record_research_memory(runtime.mission_id, result.output[:2000],
                    ("post-block-review-v1", active.run_id), cycle_id=runtime.cycle_id)
            runtime.append_event(active.block_id, "PostBlockReviewed", {"run_id": active.run_id})
        except Exception as error:
            runtime.append_event(active.block_id, "PostBlockReviewFailed", {"run_id": active.run_id, "error_type": type(error).__name__})

    def close(self):
        self._loop_runner.close()
        self.store.close()

    def serve(self, host: str, port: int, direction: str, interval_seconds: int) -> None:
        server = create_server(self.application, host, port)
        api_thread = threading.Thread(target=server.serve_forever, name="oncojev-api", daemon=True)
        api_thread.start()
        try:
            self._loop_runner.run(self._serve_cycles(direction, interval_seconds))
        finally:
            server.shutdown()
            server.server_close()
            self.close()


def service_from_environment(root: Path) -> AutonomousService:
    database = Path(os.environ.get("ONCOJEV_DB_PATH", str(root / "var" / "oncojev.sqlite3")))
    return AutonomousService(root, database)
