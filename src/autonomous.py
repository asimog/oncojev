"""Durable autonomous service composition."""

from __future__ import annotations

from src.runtime.paths import select_paths

import asyncio
import os
import threading
import json
from time import perf_counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from src.runtime.resources import ServiceResources
from src.api.server import create_server
from src.application.service import ResearchApplication
from src.block.models import BlockStatus, CycleStatus, DirectorOutcome, JevBlock, RunOutcome, run_outcome
from src.config.environment import process_settings
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


DEFAULT_DIRECTION = "Investigate scientifically useful questions using available public information and valid capabilities, preserving uncertainty and admitting only reproducible evidence."


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
    def __init__(self, root: Path, database_path: Path | None = None) -> None:
        self.root = root.resolve()
        self.settings = process_settings(self.root)
        self.paths = select_paths(self.root, self.settings)
        # Validate both overrides before any filesystem/store/recovery side effect.
        if self.settings.database_path is not None:
            self.paths.database(self.settings.database_path)
        database_path = self.paths.database(database_path if database_path is not None else self.settings.database_path)
        self.models = load_models_config(self.root / "config" / "models.yaml")
        self.policy = load_runtime_config(self.root / "config" / "runtime.yaml", testing=self.settings.testing)
        from src.oncolab.institution import application_identity
        self.application_content_identity = application_identity(self.policy)
        database_path.parent.mkdir(parents=True, exist_ok=True)
        self.store = SqliteResearchStore(database_path)
        self.repository = ResearchRepository(self.store)
        self.application = ResearchApplication(self.store)
        recover_interrupted_blocks(self.repository)
        ResearchMemory(self.store).backfill()
        self.resources = ServiceResources.from_policy(self.policy)
        print("SERVICE PROFILE " + json.dumps({"testing": self.settings.testing, "unbounded_work": self.policy.unbounded_work,
            "block": {key: getattr(self.policy.block, key) for key in
                ("default_seconds", "min_seconds", "max_seconds", "handoff_reserve_seconds")},
            "public_data": self.resources.snapshot()["public_data"],
            "data_root": str(self.paths.data), "database": str(database_path),
            "director": str(self.paths.director), "workspaces": str(self.paths.workspaces),
            "observation_target_seconds": self.policy.testing.observation_target_seconds if self.settings.testing else None}), flush=True)
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
                results=cleanup_workspaces(self.repository,self.paths.require_owned(self.paths.workspaces),
                    minimum_age_seconds=self.policy.retention.minimum_age_seconds,max_archive_bytes=self.policy.retention.max_archive_bytes,
                    max_workspaces=self.policy.retention.max_workspaces)
                for result in results:
                    if result["status"]!="removed":print(f"WORKSPACE CLEANUP {result['status']}: {result['error_type']}",flush=True)
            except Exception as error:
                print(f"WORKSPACE RETENTION UNAVAILABLE: {type(error).__name__}",flush=True)
        system = build_system(self.models, self.policy, repository=self.repository, director=self.director,
            resources=self.resources, paths=self.paths, application_content_identity=self.application_content_identity)
        self._last_system = system
        self.director = system.agents.director
        try:
            mission = self.store.latest(RecordKind.MISSION)
            if mission is None or mission.payload["direction"] != direction:
                # Preserve the latest legacy identity only when its exact human
                # direction matches. Never relabel historical cycles.
                prior = self.store.latest(RecordKind.CYCLE_START) if mission is None else None
                identity = (prior.payload.get("mission_id") if prior and prior.payload.get("direction") == direction else None)
                mission = self.store.append(StoredRecord(kind=RecordKind.MISSION,
                    record_id=identity or f"mission-{uuid4()}", payload={"direction": direction,
                        "parent_mission_id": mission.record_id if mission else None,
                        "basis": "human_supplied_direction", "legacy_identity_retained": bool(identity)}))
                system.runtime.retain_export("mission_boundary:" + mission.record_id)
            result = await run_cycle_async(system, direction, repository=self.repository, mission_id=mission.record_id)
            system.runtime.retain_export("cycle_terminal:" + system.runtime.cycle_id)
            return result
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
            started = perf_counter()
            try:
                return await self._run_once(direction)
            finally:
                if self.settings.testing:
                    elapsed = perf_counter() - started
                    target = self.policy.testing.observation_target_seconds
                    print("TESTING OBSERVATION " + json.dumps({"scope": "run_once: recovery, retention, composition, cycle and drain; excludes post-block review",
                        "elapsed_seconds": elapsed, "target_seconds": target, "target_exceeded": elapsed > target}), flush=True)

    def run_once(self, direction: str = DEFAULT_DIRECTION) -> CycleResult:
        return self._loop_runner.run(self.run_once_async(direction))

    async def _serve_cycles(self, direction: str, interval_seconds: int) -> None:
        if os.environ.get("ONCOJEV_MAINTENANCE") == "1":
            await asyncio.Event().wait()
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
    return AutonomousService(root)
