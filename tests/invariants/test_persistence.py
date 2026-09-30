"""Phase 7: append-only persistence, reconstruction, and the read-only API."""

import json
import sqlite3
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import DeltaToolCall, FunctionModel

from src.api.server import create_server
from src.application.service import ResearchApplication
from src.block.manager import BlockManager
from src.config.models import RuntimeMode
from src.director.models import ResourceAllocation
from src.dossier.builder import build_dossier
from src.jev.client import DeterministicJevClient
from src.ledger.events import LedgerEvent
from src.persistence.records import RecordKind, StoredRecord
from src.persistence.reconstruct import reconstruct_block
from src.persistence.repository import ResearchRepository
from src.persistence.store import SqliteResearchStore
from src.reasoner.service import DeterministicReasoner
from src.researcher.state import ResearchState
from src.runtime.cycle import run_cycle
from src.runtime.pydantic_ai.agents import create_agents
from src.runtime.pydantic_ai.contracts import HarnessRuntime
from src.runtime.pydantic_ai.factory import ConfiguredSystem
from src.science.admission import admit_scientific_evidence
from src.science.execution import ScienceExecutor
from src.science.models import AnalysisSpec

ROOT = Path(__file__).resolve().parents[2]


def scripted(function):
    async def stream(messages, info):
        response = await function(messages, info)
        tool_calls = {index: part for index, part in enumerate(response.parts) if isinstance(part, ToolCallPart)}
        if tool_calls:
            yield {
                index: DeltaToolCall(name=part.tool_name, json_args=part.args_as_json_str(), tool_call_id=part.tool_call_id)
                for index, part in tool_calls.items()
            }
            return
        text = "".join(part.content for part in response.parts if isinstance(part, TextPart))
        if text:
            yield text

    return FunctionModel(function=function, stream_function=stream)


def test_store_is_append_only_at_the_database_level():
    store = SqliteResearchStore()
    store.append(StoredRecord(kind=RecordKind.RESEARCH_MEMORY, record_id="m0", payload={"summary": "x"}))
    with pytest.raises(sqlite3.IntegrityError):
        store._connection.execute("UPDATE records SET payload = '{}' WHERE record_id = 'm0'")
    with pytest.raises(sqlite3.IntegrityError):
        store._connection.execute("DELETE FROM records WHERE record_id = 'm0'")
    assert store.count() == 1


def test_repository_records_typed_objects_and_reconstruction_preserves_provenance():
    store = SqliteResearchStore()
    repository = ResearchRepository(store)
    manager = BlockManager()
    block = manager.create("reconstruct me", "test", ResourceAllocation(seconds=60))
    ledger = manager.ledger(block.block_id)
    ledger.append(LedgerEvent.model_validate({"event_type": "DirectorBlockAllocated", "occurred_at": "2026-09-30T00:00:00Z", "payload": {}}))
    result = ScienceExecutor().execute(
        AnalysisSpec(
            analysis_id="a", question="q", population="p", estimand="mean",
            method="descriptive_summary", variables=("values",), inputs={"values": [1.0, 2.0, 3.0]},
        )
    )
    evidence = admit_scientific_evidence(result)
    state = ResearchState(block_id=block.block_id, objective=block.objective).add_measurement(result).add_evidence(evidence.evidence_id)

    repository.record_block(block)
    for event in ledger.history():
        repository.record_ledger_event(block.block_id, event)
    repository.record_state_revision(state)
    repository.record_measurement(result, block.block_id)
    repository.record_evidence(evidence, block.block_id)
    repository.record_dossier(build_dossier(block, ledger.history(), state, "complete"))

    reconstruction = reconstruct_block(store, block.block_id)
    assert reconstruction.complete
    assert reconstruction.evidence[0]["evidence_id"] == evidence.evidence_id
    assert reconstruction.evidence[0]["measurement"]["values"]["mean"] == 2.0
    assert reconstruction.measurements[0]["analysis_id"] == "a"
    assert reconstruction.ledger[0]["event_type"] == "DirectorBlockAllocated"
    assert reconstruction.dossier["block_id"] == block.block_id


def test_persistence_and_api_cannot_bypass_evidence_admission():
    for relative in ("src/persistence/repository.py", "src/persistence/store.py", "src/application/service.py", "src/api/server.py"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "admit_scientific_evidence" not in text
        assert "src.science.admission" not in text
    repository = ResearchRepository(SqliteResearchStore())
    assert not hasattr(repository, "admit")
    assert not hasattr(repository, "create_evidence")


def test_api_is_read_only_and_serves_application_read_models():
    store = SqliteResearchStore()
    repository = ResearchRepository(store)
    manager = BlockManager()
    block = manager.create("api block", "test", ResourceAllocation(seconds=60))
    repository.record_block(block)
    repository.record_dossier(build_dossier(block, (), None, "complete"))
    repository.record_cycle("m1", "deterministic", "direction", (block.block_id,))
    application = ResearchApplication(store)
    server = create_server(application, "127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_address[1]}"
        overview = json.loads(urlopen(f"{base}/api/overview").read())
        assert overview["blocks"] == 1 and overview["cycles"] == 1
        reconstruction = json.loads(urlopen(f"{base}/api/blocks/{block.block_id}/reconstruction").read())
        assert reconstruction["block_id"] == block.block_id
        with pytest.raises(HTTPError) as raised:
            urlopen(Request(f"{base}/api/blocks", method="POST", data=b"{}"))
        assert raised.value.code == 405
    finally:
        server.shutdown()
        server.server_close()


def test_deterministic_cycle_persists_blocks_dossiers_and_memory():
    store = SqliteResearchStore()
    repository = ResearchRepository(store)
    manager = BlockManager()
    runtime = HarnessRuntime(
        manager=manager,
        jev=DeterministicJevClient(),
        science=ScienceExecutor(),
        reasoner=DeterministicReasoner(),
        max_jev_calls=4,
        max_reasoner_calls=2,
    )
    agents = create_agents("test", "test")
    runtime.researcher = agents.researcher
    system = ConfiguredSystem(agents=agents, runtime=runtime, mode=RuntimeMode.DETERMINISTIC)
    director_calls = 0
    researcher_calls = 0

    async def director_model(messages, info):
        nonlocal director_calls
        director_calls += 1
        if director_calls == 1:
            code = (
                'block = await allocate_block(objective="measure a public signal", why_now="test", seconds=60)\n'
                'await launch_researcher(block_id=block["block_id"])\nblock'
            )
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": code}, tool_call_id="d1")])
        return ModelResponse(parts=[TextPart("director complete")])

    async def researcher_model(messages, info):
        nonlocal researcher_calls
        researcher_calls += 1
        if researcher_calls == 1:
            code = (
                'await run_statistics(analysis_id="a", question="q", estimand="mean", method="descriptive_summary", inputs={"values": [1.0, 2.0, 3.0]})\n'
                'await admit_measurement(analysis_id="a")\n'
                'await complete_block(reason="done")\n"researcher complete"'
            )
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": code}, tool_call_id="r1")])
        return ModelResponse(parts=[TextPart("researcher complete")])

    with agents.director.override(model=scripted(director_model)), agents.researcher.override(model=scripted(researcher_model)):
        result = run_cycle(system, "investigate a public signal", repository=repository, mission_id="m1")

    assert result.block_ids
    assert result.dossiers and result.dossiers[0].evidence_refs
    kinds = {record.kind for record in store.records()}
    assert {RecordKind.BLOCK, RecordKind.DOSSIER, RecordKind.MEASUREMENT, RecordKind.EVIDENCE, RecordKind.CYCLE, RecordKind.RESEARCH_MEMORY} <= kinds
    assert reconstruct_block(store, result.block_ids[0]).complete
