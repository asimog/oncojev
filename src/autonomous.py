"""Durable autonomous service composition."""

from __future__ import annotations

import os
import threading
from pathlib import Path

from src.api.server import create_server
from src.application.service import ResearchApplication
from src.block.models import BlockStatus, JevBlock
from src.config.environment import load_local_environment
from src.config.loader import load_models_config, load_runtime_config
from src.dossier.builder import build_dossier
from src.ledger.events import LedgerEvent
from src.persistence.records import RecordKind
from src.persistence.repository import ResearchRepository
from src.persistence.store import SqliteResearchStore
from src.runtime.cycle import CycleResult, run_cycle
from src.runtime.pydantic_ai.factory import build_system


DEFAULT_DIRECTION = "Investigate a public oncology signal and admit only source-bound reproducible evidence."


def recover_interrupted_blocks(repository: ResearchRepository) -> tuple[str, ...]:
    """Close previously active blocks honestly after process interruption."""
    recovered: list[str] = []
    for block_id in repository.store.block_ids():
        latest = repository.store.latest(RecordKind.BLOCK, block_id=block_id)
        if latest is None or repository.store.latest(RecordKind.DOSSIER, block_id=block_id) is not None:
            continue
        block = JevBlock.model_validate(latest.payload)
        if block.status is not BlockStatus.COMPLETE:
            block = block.model_copy(update={"status": BlockStatus.COMPLETE, "termination_reason": "recovered_after_interruption"})
            event = LedgerEvent(
                event_type="InterruptedBlockRecovered",
                occurred_at=latest.recorded_at,
                payload={"block_id": block_id, "reason": "process_restart"},
            )
            repository.record_ledger_event(block_id, event)
            repository.record_block(block)
        stored_events = tuple(
            LedgerEvent.model_validate(record.payload)
            for record in repository.store.records(kind=RecordKind.LEDGER_EVENT, block_id=block_id)
        )
        repository.record_dossier(build_dossier(block, stored_events, None, block.termination_reason or "recovered_after_interruption"))
        recovered.append(block_id)
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

    def run_once(self, direction: str = DEFAULT_DIRECTION) -> CycleResult:
        system = build_system(self.models, self.policy, max_tool_calls=self.policy.block.max_tool_calls)
        return run_cycle(system, direction, repository=self.repository, mission_id=f"mission-{self.store.count() + 1}")

    def serve(self, host: str, port: int, direction: str, interval_seconds: int) -> None:
        server = create_server(self.application, host, port)
        api_thread = threading.Thread(target=server.serve_forever, name="oncojev-api", daemon=True)
        api_thread.start()
        try:
            while True:
                try:
                    self.run_once(direction)
                except Exception as error:
                    print(f"AUTONOMOUS CYCLE FAILED: {type(error).__name__}", flush=True)
                threading.Event().wait(interval_seconds)
        finally:
            server.shutdown()
            server.server_close()
            self.store.close()


def service_from_environment(root: Path) -> AutonomousService:
    database = Path(os.environ.get("ONCOJEV_DB_PATH", str(root / "var" / "oncojev.sqlite3")))
    return AutonomousService(root, database)
