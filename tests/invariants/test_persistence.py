"""Phase 7: append-only persistence, reconstruction, and the read-only API."""

import json
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import DeltaToolCall, FunctionModel

from src.api.server import create_server
from src.autonomous import recover_interrupted_blocks
from src.application.service import ResearchApplication
from src.block.manager import BlockManager
from src.block.models import BlockStatus
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
from src.sources.models import AcquisitionRecord

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


def cycle_system():
    runtime = HarnessRuntime(manager=BlockManager(), jev=DeterministicJevClient(),
                             science=ScienceExecutor(), reasoner=DeterministicReasoner(),
                             max_jev_calls=4, max_reasoner_calls=2)
    agents = create_agents("test", "test")
    runtime.researcher = agents.researcher
    return ConfiguredSystem(agents=agents, runtime=runtime, mode=RuntimeMode.DETERMINISTIC)


@pytest.mark.parametrize("launch", ["nested", "fallback"])
@pytest.mark.parametrize("budget", ["researcher", "aggregate"])
def test_role_and_aggregate_request_limits_preserve_director_headroom(launch, budget):
    system = cycle_system()
    runtime = system.runtime
    runtime.researcher_factory = lambda block_id: system.agents.researcher
    runtime.max_model_requests = 1 if budget == "researcher" else 10
    runtime.cycle_request_limit = (2 if launch == "nested" else 3) if budget == "aggregate" else 20
    repository = ResearchRepository(SqliteResearchStore())
    director_calls = 0
    researcher_calls = 0

    async def director(messages, info):
        nonlocal director_calls
        director_calls += 1
        if director_calls == 1:
            code = 'block = await allocate_block(objective="bounded requests", why_now="test", seconds=60)\n'
            if launch == "nested":
                code += 'await launch_researcher(block_id=block["block_id"])\n'
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": code + "block"}, tool_call_id="d1")])
        return ModelResponse(parts=[TextPart("Director still has independent headroom")])

    async def researcher(messages, info):
        nonlocal researcher_calls
        researcher_calls += 1
        return ModelResponse(parts=[ToolCallPart("run_code", {"code": "await block_status()"}, tool_call_id=f"r{researcher_calls}")])

    with system.agents.director.override(model=scripted(director)), system.agents.researcher.override(model=scripted(researcher)):
        with pytest.raises(Exception):
            run_cycle(system, "direction", repository=repository)
    assert researcher_calls == 1
    assert director_calls == (1 if budget == "aggregate" and launch == "nested" else 2)
    assert runtime.total_usage().requests == director_calls + researcher_calls
    cycle = repository.store.latest(RecordKind.CYCLE)
    assert cycle.payload["status"] == "failed"
    assert cycle.payload["error_type"] == "UsageLimitExceeded"
    assert not reconstruct_block(repository.store, runtime.manager.blocks()[0].block_id).complete


@pytest.mark.parametrize("missing_cost", [False, True])
def test_aggregate_cost_failure_retains_reported_usage_and_partial_dossier(missing_cost):
    from decimal import Decimal
    from pydantic_ai.exceptions import UsageLimitExceeded
    from pydantic_ai.usage import RequestUsage

    system = cycle_system()
    runtime = system.runtime
    runtime.cycle_cost_limit = 0.5 if missing_cost else 0.6
    runtime.researcher_factory = lambda block_id: system.agents.researcher
    repository = ResearchRepository(SqliteResearchStore())
    calls = 0

    async def director(messages, info):
        nonlocal calls
        calls += 1
        parts = [ToolCallPart("run_code", {"code": 'await allocate_block(objective="cost bound", why_now="test", seconds=60)'}, tool_call_id="allocate")] if calls == 1 else [TextPart("allocated")]
        cost = None if missing_cost and calls == 2 else Decimal("0.1")
        return ModelResponse(parts=parts, usage=RequestUsage(cost=cost))

    async def researcher(messages, info):
        return ModelResponse(parts=[TextPart("expensive response")], usage=RequestUsage(cost=Decimal("0.5")))

    with system.agents.director.override(model=scripted(director)), system.agents.researcher.override(model=scripted(researcher)):
        with pytest.raises(UsageLimitExceeded):
            run_cycle(system, "direction", repository=repository)
    block = runtime.manager.blocks()[0]
    expected_cost = "0.6" if missing_cost else "0.7"
    assert runtime.total_usage().cost == Decimal(expected_cost)
    usage = next(event.payload for event in runtime.manager.ledger(block.block_id).history() if event.event_type == "ModelUsage")
    assert usage["cost_complete"] is not missing_cost
    assert usage["total"]["reported_cost"] == expected_cost
    assert repository.store.latest(RecordKind.CYCLE).payload["status"] == "failed"
    reconstruction = reconstruct_block(repository.store, block.block_id)
    assert reconstruction.dossier and not reconstruction.complete


def test_swallowed_nested_failure_cannot_complete_cycle():
    from pydantic_ai.exceptions import UsageLimitExceeded

    system = cycle_system()
    repository = ResearchRepository(SqliteResearchStore())
    calls = 0
    attempts = 0

    async def director(messages, info):
        nonlocal calls
        calls += 1
        if calls == 1:
            code = ('block = await allocate_block(objective="partial investigation", why_now="test", seconds=60)\n'
                    'for attempt in range(2):\n'
                    '    try:\n'
                    '        await launch_researcher(block_id=block["block_id"])\n'
                    '    except Exception:\n'
                    '        pass\n'
                    'block')
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": code}, tool_call_id="d1")])
        return ModelResponse(parts=[TextPart("director returned normally")])

    async def researcher(messages, info):
        nonlocal attempts
        attempts += 1
        raise UsageLimitExceeded("Researcher budget exhausted")

    with system.agents.director.override(model=scripted(director)), system.agents.researcher.override(model=scripted(researcher)):
        with pytest.raises(RuntimeError):
            run_cycle(system, "direction", repository=repository)

    block_id = system.runtime.manager.blocks()[0].block_id
    view = reconstruct_block(repository.store, block_id)
    assert attempts == 1
    assert not view.complete
    assert view.block["status"] == "failed"
    assert view.dossier["termination_reason"] == "researcher_failed"
    cycle = repository.store.latest(RecordKind.CYCLE)
    assert cycle.payload["status"] == "failed"
    assert cycle.payload["error_type"] == "UsageLimitExceeded"


@pytest.mark.parametrize("scenario", ["completed", "handoff_failure", "fallback_failure", "before_allocation",
                                      "auth_failure", "transport_failure", "tool_failure", "unexpected_failure", "multiple_blocks",
                                      "no_allocation", "usage_truncation", "tool_truncation"])
def test_cycle_terminal_outcomes(scenario):
    from pydantic_ai.exceptions import IncompleteToolCall, ModelAPIError, ModelHTTPError, UnexpectedModelBehavior, UsageLimitExceeded

    system = cycle_system()
    # The existing factory boundary also exercises the Python fallback path.
    system.runtime.researcher_factory = lambda block_id: system.agents.researcher
    repository = ResearchRepository(SqliteResearchStore())
    director_calls = 0
    researcher_calls = 0
    errors = {"before_allocation": ModelHTTPError(401, "test"), "auth_failure": ModelHTTPError(401, "test"),
              "transport_failure": ModelAPIError("test", "transport failed"),
              "tool_failure": ValueError("tool crashed"), "unexpected_failure": UnexpectedModelBehavior("malformed response"),
              "usage_truncation": UsageLimitExceeded("Director limit"), "tool_truncation": IncompleteToolCall("token limit")}

    async def director(messages, info):
        nonlocal director_calls
        director_calls += 1
        if scenario == "before_allocation":
            raise errors[scenario]
        if scenario == "no_allocation":
            return ModelResponse(parts=[TextPart("no block")])
        if director_calls == 1:
            code = 'block = await allocate_block(objective="estimand may be unreachable", why_now="test", seconds=60)\n'
            if scenario == "multiple_blocks":
                code += 'await allocate_block(objective="invalid second block", why_now="test", seconds=60)\n'
            elif scenario != "fallback_failure":
                code += 'await launch_researcher(block_id=block["block_id"])\n'
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": code + "block"}, tool_call_id="d1")])
        if scenario in errors:
            raise errors[scenario]
        return ModelResponse(parts=[TextPart("Director returned")])

    async def researcher(messages, info):
        nonlocal researcher_calls
        researcher_calls += 1
        if scenario == "fallback_failure":
            raise UsageLimitExceeded("fallback failed")
        if scenario == "handoff_failure":
            if researcher_calls == 1:
                return ModelResponse(parts=[ToolCallPart("run_code", {"code": 'await complete_block(reason="handoff requested")'}, tool_call_id="r1")])
            raise UsageLimitExceeded("failed after handoff")
        return ModelResponse(parts=[TextPart("No scientific estimate is attainable with available inputs")])

    succeeds = scenario in {"completed", "usage_truncation", "tool_truncation"}
    with system.agents.director.override(model=scripted(director)), system.agents.researcher.override(model=scripted(researcher)):
        if succeeds:
            result = run_cycle(system, "direction", repository=repository)
            assert result.status.value == ("complete" if scenario == "completed" else "incomplete")
            assert result.director_outcome.value == ("returned" if scenario == "completed" else "truncated")
        else:
            with pytest.raises(Exception):
                run_cycle(system, "direction", repository=repository)
    cycles = repository.store.records(kind=RecordKind.CYCLE)
    assert len(cycles) == 1
    assert cycles[0].payload["status"] == ("complete" if scenario == "completed" else "incomplete" if succeeds else "failed")
    if scenario in errors:
        assert cycles[0].payload["director_error_type"] == type(errors[scenario]).__name__
    blocks = system.runtime.manager.blocks()
    assert len(blocks) == (0 if scenario in {"before_allocation", "no_allocation"} else 2 if scenario == "multiple_blocks" else 1)
    for block in blocks:
        view = reconstruct_block(repository.store, block.block_id)
        assert view.complete is succeeds
        assert view.dossier["objective_attainment"] == "unknown"
        assert view.block["status"] == ("complete" if succeeds else "failed")
        if scenario == "handoff_failure":
            assert view.run_outcome.value == "failed"
            assert any(e["event_type"] == "ResearcherHandoffRequested" for e in view.ledger)
            assert not any(e["event_type"] == "ResearcherRunCompleted" for e in view.ledger)
    if not blocks:
        assert not repository.store.records(kind=RecordKind.DOSSIER)


def test_terminal_bundle_rollback_and_cycle_recovery(tmp_path):
    database = tmp_path / "partial.sqlite3"
    store = SqliteResearchStore(database)
    repository = ResearchRepository(store)
    block = BlockManager().create("interrupted writes", "test", ResourceAllocation(seconds=60), mission_id="m1")
    repository.record_cycle_start("m1", "deterministic", "direction")
    initial = repository.record_block(block)
    # Simulate an append failure at the second write using the real SQLite path.
    store._connection.execute("CREATE TRIGGER fail_dossier BEFORE INSERT ON records WHEN NEW.kind = 'dossier' BEGIN SELECT RAISE(ABORT, 'disk failure'); END")
    closed = block.model_copy(update={"status": BlockStatus.FAILED, "termination_reason": "failure"})
    with pytest.raises(sqlite3.IntegrityError):
        repository.record_terminal(closed, build_dossier(closed, (), None, "failure"))
    assert store.latest(RecordKind.BLOCK, block_id=block.block_id).seq == initial.seq
    assert store.latest(RecordKind.DOSSIER, block_id=block.block_id) is None
    store._connection.execute("DROP TRIGGER fail_dossier")
    store.close()
    store = SqliteResearchStore(database)
    repository = ResearchRepository(store)
    recover_interrupted_blocks(repository)
    assert reconstruct_block(store, block.block_id).block["status"] == "interrupted"
    assert store.latest(RecordKind.CYCLE).payload["status"] == "incomplete"
    assert store.latest(RecordKind.CYCLE).payload["block_ids"] == [block.block_id]
    count = store.count()
    assert recover_interrupted_blocks(repository) == ()
    assert store.count() == count


def test_legacy_failure_correction_preserves_original_records():
    from src.memory.service import ResearchMemory
    from src.researcher.state import StateFragment
    from src.provenance import canonical_bytes
    repository = ResearchRepository(SqliteResearchStore())
    manager = BlockManager()
    block = manager.create("legacy block 4", "test", ResourceAllocation(seconds=60))
    events = tuple(LedgerEvent.model_validate({"event_type": kind, "occurred_at": "2026-09-30T00:00:00Z",
                                             "payload": {"error_type": "UsageLimitExceeded"}})
                   for kind in ("ResearcherRunStarted", "ResearcherRunFailed", "ResearcherRunStarted", "ResearcherRunFailed"))
    for event in events:
        repository.record_ledger_event(block.block_id, event)
    acquisition = AcquisitionRecord(source="gdc", request={"fixture": True}, records=({"file_id": "a"},), provenance=("test",))
    result = ScienceExecutor().measure_acquisition(acquisition, "legacy-descriptive-count")
    evidence = admit_scientific_evidence(result)
    repository.record_measurement(result, block.block_id)
    repository.record_evidence(evidence, block.block_id)
    closed = manager.complete(block, "researcher_returned")
    repository.record_terminal(closed, build_dossier(closed, events, None, "researcher_returned"))
    repository.record_cycle("legacy", "live", "direction", (block.block_id,))
    originals = repository.store.records()
    application = ResearchApplication(repository.store)
    assert application.overview()["latest_cycle"]["status"] == "failed"
    assert application.blocks()[0]["block"]["status"] == "failed"
    assert not reconstruct_block(repository.store, block.block_id).complete
    memory = ResearchMemory(repository.store)
    memory.backfill()
    old_digest = memory.search("legacy")[0]
    assert old_digest.inferred and old_digest.lifecycle[0]["status"] == "failed"
    assert memory.get_evidence(evidence.evidence_id, block.block_id)["evidence"] == evidence.model_dump(mode="json")
    with pytest.raises(ValueError, match="unresolved or changed"):
        memory.resolve(old_digest.references[0].model_copy(update={"sha256": "0" * 64}))
    recover_interrupted_blocks(repository)
    correction = repository.store.latest(RecordKind.OUTCOME_CORRECTION, block_id=block.block_id)
    assert correction.payload["original_seqs"] == [record.seq for record in originals if record.kind in {RecordKind.BLOCK, RecordKind.DOSSIER, RecordKind.LEDGER_EVENT, RecordKind.CYCLE}]
    assert repository.store.records()[:len(originals)] == originals
    memory.backfill()
    assert memory.search("legacy")[0].digest_id != old_digest.digest_id
    assert memory.get_dossier(block.block_id)["lifecycle_status"] == "failed"
    large = ResearchState(block_id=block.block_id, objective=block.objective,
        uncertainties=tuple(StateFragment(fragment_id=str(i), kind="uncertainty", summary="unknown ÃŽÂ©" * 1000, provenance=("fixture",)) for i in range(50)))
    repository.record_state_revision(large)
    memory.backfill()
    context = memory.context("legacy")
    assert len(canonical_bytes(context.model_dump(mode="json"))) <= 32768
    assert context.digests and context.digests[0]["operational_blockers"]
    assert context.digests[0]["omitted_items"]["uncertainties"] > 0
    assert len(canonical_bytes(memory.start_context("legacy").model_dump(mode="json"))) <= 16384
    count = repository.store.count()
    recover_interrupted_blocks(repository)
    assert repository.store.count() == count


def test_service_recovers_pending_work_before_each_cycle(tmp_path, monkeypatch):
    from src.autonomous import AutonomousService

    service = AutonomousService(ROOT, tmp_path / "service.sqlite3")
    pending = BlockManager().create("pending after service startup", "test", ResourceAllocation(seconds=60), mission_id="interrupted")
    service.repository.record_cycle_start("interrupted", "deterministic", "old direction")
    service.repository.record_block(pending)
    service.repository.record_dossier(build_dossier(pending, (), None, "partial"))
    system = cycle_system()
    system.runtime.researcher_factory = lambda block_id: system.agents.researcher
    monkeypatch.setattr("src.autonomous.build_system", lambda *args, **kwargs: system)
    calls = 0

    async def director(messages, info):
        nonlocal calls
        calls += 1
        if calls == 1:
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": 'await allocate_block(objective="new work", why_now="test", seconds=60)'}, tool_call_id="d1")])
        return ModelResponse(parts=[TextPart("returned")])

    async def researcher(messages, info):
        return ModelResponse(parts=[TextPart("completed investigation with no evidence")])

    try:
        with system.agents.director.override(model=scripted(director)), system.agents.researcher.override(model=scripted(researcher)):
            result = service.run_once("new direction")
        assert result.status.value == "complete"
        assert service.application.reconstruction(pending.block_id).block["status"] == "interrupted"
        assert [r.payload["status"] for r in service.store.records(kind=RecordKind.CYCLE)] == ["incomplete", "complete"]
    finally:
        service.store.close()


@pytest.mark.parametrize("reopen", [False, True])
@pytest.mark.parametrize("launch", ["nested", "fallback"])
def test_service_delivers_relevant_failed_history_to_fresh_researcher(tmp_path, monkeypatch, reopen, launch):
    """Real service/factory/tools preserve failed context without inheriting evidence or transcripts."""
    import httpx
    from pydantic_ai.exceptions import UsageLimitExceeded
    from src.autonomous import AutonomousService
    from src.runtime.pydantic_ai.factory import build_system
    from src.sources.public import GdcPublicSource

    monkeypatch.setenv("OPENROUTER_API_KEY", "fixture")
    monkeypatch.setenv("TYPESAFE_API_KEY", "fixture")
    monkeypatch.setattr("src.runtime.pydantic_ai.factory.build_reasoner", lambda *args: DeterministicReasoner())
    monkeypatch.setattr("src.runtime.pydantic_ai.factory.build_jev_client", lambda *args: DeterministicJevClient())
    monkeypatch.setattr("src.runtime.pydantic_ai.agents.configure_agent_telemetry", lambda: None)
    phase = 1
    systems = []
    delivered = []
    previous_block = None

    async def director(messages, info):
        first = not any(isinstance(m, ModelResponse) for m in messages)
        if first:
            prompt = " ".join(str(p.content) for m in messages for p in m.parts if hasattr(p, "content"))
            if phase == 2:
                assert "UsageLimitExceeded" in prompt, "Director lost the prior failed cycle outcome"
                assert "not biological absence" in prompt
                assert "unrelated-newest" not in prompt
            code = 'memory = await read_research_memory(query="melanoma")\n'
            if phase == 2:
                code += ('filtered = await search_research_memory(query="melanoma", filters={"entity": "TCGA-SKCM", "topic": "expression"})\n'
                         'assert filtered["digests"]\n'
                         'reference = memory["digests"][0]["references"][0]\n'
                         'resolved = await resolve_memory_reference(kind=reference["kind"], record_id=reference["record_id"], seq=reference["seq"], sha256=reference["sha256"], block_id=reference["block_id"])\nassert resolved\n'
                         f'dossier = await get_dossier(block_id="{previous_block}")\n'
                         'hypotheses = await get_hypotheses(query="melanoma")\n'
                         'negative = await get_negative_results(query="melanoma")\n'
                         'uncertainty = await get_open_uncertainties(query="melanoma")\n'
                         'assert dossier is not None\nassert dossier["lifecycle_status"] == "failed"\nassert hypotheses\nassert uncertainty\nassert not negative\n')
            code += 'block = await allocate_block(objective="melanoma public expression", why_now="review recorded failure", entities=["TCGA-SKCM"], topics=["expression"])\n'
            if launch == "nested":
                code += 'await launch_researcher(block_id=block["block_id"])\n'
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": code + 'block'}, tool_call_id="allocate")])
        if phase == 2:
            returns = [str(p.content) for m in messages for p in m.parts if hasattr(p, "content")]
            assert not any("Type error in code" in value or "AssertionError" in value or "Exception:" in value for value in returns), returns[-1]
            assert systems[-1].runtime.manager.blocks(), returns[-1]
        return ModelResponse(parts=[TextPart("Optional prose claiming victory is not scientific evidence")])

    async def researcher(messages, info):
        first = not any(isinstance(m, ModelResponse) for m in messages)
        if phase == 1:
            if first:
                return ModelResponse(parts=[ToolCallPart("run_code", {"code":
                    'try:\n    await acquire_gdc(endpoint="files", filters={}, fields=["file_id"])\nexcept Exception:\n    pass\n'
                    'await generate_hypotheses(finding="melanoma source unavailable; unknown")'}, tool_call_id="partial")])
            raise UsageLimitExceeded("failed researcher")
        if first:
            prompt = " ".join(str(p.content) for m in messages for p in m.parts if hasattr(p, "content"))
            assert "UsageLimitExceeded" in prompt and "Replication needed" in prompt
            assert "unrelated-newest" not in prompt
            assert "Optional prose claiming victory" not in prompt
            delivered.append(prompt)
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": 'await inspect_research_state()'}, tool_call_id="fresh")])
        return ModelResponse(parts=[TextPart("reviewed prior failure without repeating source call")])

    monkeypatch.setattr("src.runtime.pydantic_ai.agents.configured_model", lambda role: scripted(researcher if role.max_output_tokens == 16000 else director))

    def compose(*args, **kwargs):
        system = build_system(*args, **kwargs)
        system.runtime.gdc = GdcPublicSource(httpx.MockTransport(lambda request: httpx.Response(503, json={"error": "unavailable"})))
        systems.append(system)
        return system

    monkeypatch.setattr("src.autonomous.build_system", compose)
    database = tmp_path / "memory-service.sqlite3"
    service = AutonomousService(ROOT, database)
    try:
        with pytest.raises((UsageLimitExceeded, RuntimeError)):
            service.run_once("melanoma public expression")
        previous_block = service.store.block_ids()[0]
        # A newer unrelated, actually recorded cycle must not replace relevant history.
        service.repository.record_cycle("unrelated", "live", "unrelated-newest cardiology", (), status="failed", error_type="NoAllocation")
        service.repository.record_research_memory("legacy-only", "melanoma fabricated scientific negative", ("legacy",))
        if reopen:
            service.store.close()
            service = AutonomousService(ROOT, database)
        phase = 2
        result = service.run_once("melanoma public expression")
        assert result.status.value == "complete" and len(delivered) == 1
        assert systems[0].runtime is not systems[1].runtime
        assert (systems[0].agents.director is systems[1].agents.director) is not reopen
        assert systems[1].runtime.manager.blocks()[0].start.memory.prior_failures
        fresh = systems[1].runtime.research_state.get(result.block_ids[0])
        assert not fresh.evidence_ids and not fresh.measurements and not fresh.uncertainties
        from src.memory.service import ResearchMemory
        memory = ResearchMemory(service.store)
        count = service.store.count()
        memory.backfill()
        assert service.store.count() == count
        assert memory.get_evidence("missing", previous_block) is None
        assert not memory.items("scientific_negative_findings", "melanoma")
        assert memory.search("melanoma", mission_id=systems[0].runtime.mission_id)
        assert memory.search("melanoma", entity="TCGA-SKCM", topic="expression")
        assert systems[1].runtime.resources(result.block_ids[0])["source"]["attempted"] == 0
        assert not memory.search("melanoma", entity="unknown-entity")
        assert not memory.search("melanoma", topic="unknown-topic")
        assert not memory.search("melanoma", since=datetime(2100, 1, 1, tzinfo=UTC))
        assert any(d.legacy_notes and d.inferred for d in memory.digests())
    finally:
        service.store.close()


def test_store_is_append_only_at_the_database_level():
    store = SqliteResearchStore()
    store.append(StoredRecord(kind=RecordKind.RESEARCH_MEMORY, record_id="m0", payload={"summary": "x"}))
    with pytest.raises(sqlite3.IntegrityError):
        store._connection.execute("UPDATE records SET payload = '{}' WHERE record_id = 'm0'")
    with pytest.raises(sqlite3.IntegrityError):
        store._connection.execute("DELETE FROM records WHERE record_id = 'm0'")
    assert store.count() == 1


@pytest.mark.parametrize("partial_dossier", [False, True])
def test_restart_recovery_closes_interrupted_block_with_dossier(tmp_path, partial_dossier):
    database = tmp_path / "recovery.sqlite3"
    store = SqliteResearchStore(database)
    repository = ResearchRepository(store)
    block = BlockManager().create("interrupted", "test", ResourceAllocation(seconds=60))
    initial = repository.record_block(block)
    if partial_dossier:
        repository.record_dossier(build_dossier(block, (), None, "premature_dossier"))
    store.close()
    store = SqliteResearchStore(database)
    repository = ResearchRepository(store)
    assert recover_interrupted_blocks(repository) == (block.block_id,)
    reconstruction = reconstruct_block(store, block.block_id)
    assert not reconstruction.complete
    assert reconstruction.block["status"] == "interrupted"
    recovered_event = next(e for e in reconstruction.ledger if e["event_type"] == "InterruptedBlockRecovered")
    assert recovered_event["occurred_at"] > initial.recorded_at.isoformat()
    assert reconstruction.block["termination_reason"] == "recovered_after_interruption"
    assert reconstruction.dossier["termination_reason"] == "recovered_after_interruption"
    count = store.count()
    assert recover_interrupted_blocks(repository) == ()
    assert store.count() == count


def test_repository_records_typed_objects_and_reconstruction_preserves_provenance():
    store = SqliteResearchStore()
    repository = ResearchRepository(store)
    manager = BlockManager()
    block = manager.create("reconstruct me", "test", ResourceAllocation(seconds=60))
    ledger = manager.ledger(block.block_id)
    ledger.append(LedgerEvent.model_validate({"event_type": "DirectorBlockAllocated", "occurred_at": "2026-09-30T00:00:00Z", "payload": {}}))
    ledger.append(LedgerEvent.model_validate({"event_type": "ResearcherRunCompleted", "occurred_at": "2026-09-30T00:00:01Z", "payload": {}}))
    acquisition = AcquisitionRecord(source="gdc", request={"test": True}, records=({"file_id": "a"},), provenance=("test",))
    result = ScienceExecutor().measure_acquisition(acquisition, "a")
    evidence = admit_scientific_evidence(result)
    state = ResearchState(block_id=block.block_id, objective=block.objective).add_measurement(result).add_evidence(evidence.evidence_id)

    block = manager.complete(block, "complete")
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
    assert reconstruction.evidence[0]["measurement"]["values"]["record_count"] == 1
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
    acquisition = AcquisitionRecord(source="gdc", request={"test": True}, records=({"file_id": "a"},), provenance=("test",))
    runtime.acquisitions[acquisition.acquisition_id] = acquisition
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
                f'await measure_acquisition(acquisition_id="{acquisition.acquisition_id}", analysis_id="a")\n'
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
    # Two allocations may belong to one mission; receipt idempotence must not
    # collapse distinct cycles or confuse recovery of their terminal writes.
    director_calls = researcher_calls = 0
    repeat = cycle_system()
    repeat.runtime.acquisitions[acquisition.acquisition_id] = acquisition
    with repeat.agents.director.override(model=scripted(director_model)), repeat.agents.researcher.override(model=scripted(researcher_model)):
        second = run_cycle(repeat, "investigate a public signal", repository=repository, mission_id="m1")
    cycles = store.records(kind=RecordKind.CYCLE)
    assert len(cycles) == 2 and len({r.record_id for r in cycles}) == 2
    assert all(r.payload["mission_id"] == "m1" for r in cycles)
    assert second.block_ids != result.block_ids
    count = store.count()
    assert recover_interrupted_blocks(repository) == ()
    assert store.count() == count


def test_restart_resolves_exact_acquisition_input_and_preallocation_index_receipt(tmp_path):
    import httpx
    from src.sources.public import GdcPublicSource, PublicLiteratureSource

    database = tmp_path / "inputs.sqlite3"
    store = SqliteResearchStore(database)
    repository = ResearchRepository(store)
    system = cycle_system()
    runtime = system.runtime
    runtime.researcher_factory = lambda block_id: system.agents.researcher
    runtime.oncolab_search_k = 1
    source_calls = []

    def source(request):
        source_calls.append(request)
        return httpx.Response(200, json={"data": {"hits": [{"file_id": "a", "count": 7}]}}) if len(source_calls) == 1 else httpx.Response(503, json={"detail": "unavailable"})

    runtime.gdc = GdcPublicSource(httpx.MockTransport(source))
    runtime.literature = PublicLiteratureSource(httpx.MockTransport(lambda request: httpx.Response(200, json={"message": {"items": [{"title": ["Public study"], "DOI": "10.1/study"}]}})))
    director_calls = researcher_calls = 0

    async def director(messages, info):
        nonlocal director_calls
        director_calls += 1
        if director_calls == 1:
            code = 'await search_oncolab(query="GDC", limit=20)\nblock = await allocate_block(objective="stored input", why_now="test", seconds=60)\nawait launch_researcher(block_id=block["block_id"])'
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": code}, tool_call_id="director")])
        return ModelResponse(parts=[TextPart("done")])

    async def researcher(messages, info):
        nonlocal researcher_calls
        researcher_calls += 1
        if researcher_calls == 1:
            code = ('await search_oncolab(query="GDC", limit=20)\n'
                    'record = await acquire_gdc(endpoint="files", filters={}, fields=["file_id", "count"])\n'
                    'await measure_acquisition(acquisition_id=record["acquisition_id"], analysis_id="count")\n'
                    'await admit_measurement(analysis_id="count")\n'
                    'await search_public_literature(query="public study", limit=1)\n'
                    'try:\n    await acquire_gdc(endpoint="files", filters={}, fields=["file_id"])\nexcept Exception:\n    pass\n'
                    'await evaluate_candidate(candidate_id="c", candidate_summary="public metadata signal")\n'
                    'await complete_block(reason="done")')
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": code}, tool_call_id="researcher")])
        return ModelResponse(parts=[TextPart("done")])

    with system.agents.director.override(model=scripted(director)), system.agents.researcher.override(model=scripted(researcher)):
        result = run_cycle(system, "direction", repository=repository)
    block_id = result.block_ids[0]
    store.close()
    store = SqliteResearchStore(database)
    view = reconstruct_block(store, block_id)
    assert len(view.measurements) == 1
    source_id = view.measurements[0]["source_refs"][0]
    stored = getattr(view, "resolved_inputs", {}).get(source_id)
    assert stored is not None, "restart lost exact acquired scientific input"
    assert stored["records"] == [{"file_id": "a", "count": 7}]
    assert stored["request"]["filters"]["content"][-1]["content"]["value"] == ["open"]
    assert view.measurements[0]["input_sha256"] == stored["content_sha256"]
    from src.sources.models import AcquisitionRecord
    copy = AcquisitionRecord.model_validate(stored).model_copy(update={"acquisition_id": "different-run"})
    assert copy.content_sha256 == stored["content_sha256"]
    assert not view.unresolved_source_refs
    assert view.literature[0]["records"][0]["doi"] == "10.1/study"
    assert view.literature[0]["request"] == {"query": "public study", "rows": 1}
    usage = view.dossier["resource_usage"]
    assert usage["source_attempts"] == 3 and usage["source_successes"] == 2 and usage["source_failures"] == 1
    assert usage["source_byte_reports"] == 3 and usage["source_bytes_reported"] > 0
    searches = [p for p in view.index_receipts if p["operation"] == "search"]
    assert {p["actor"] for p in searches} == {"director", "researcher"}
    assert all(p["effective_limit"] == 1 and len(p["returned_ids"]) == 1 for p in searches)
    assert next(p for p in searches if p["actor"] == "director")["block_id"] is None
    assert any(p["selected_id"] == "source.gdc" for p in view.index_receipts)
    assert view.capability_invocations[0]["status"] == "completed"
    assert any(p["status"] == "failed" for p in view.capability_invocations)
    assert view.candidate_history[0]["action"] == "keep_alive"
    assert view.candidate_history[0]["epistemic_status"] == "semantic_search_history"
    assert view.jev_calls[0]["question_hashes"] and len(view.jev_calls[0]["questions"]) == 2
    assert view.jev_calls[0]["projection"]["payload"]["measurements"][0]["origin"] == "source"
    assert view.jev_calls[0]["projection"]["payload"]["uncertainties"][0]["kind"] == "operational_failure"
    from src.config.loader import load_models_config, load_runtime_config
    from src.runtime.pydantic_ai.factory import build_harness_runtime, bind_repository
    policy = load_runtime_config(ROOT / "config/runtime.yaml").model_copy(update={"mode": RuntimeMode.DETERMINISTIC})
    fresh = build_harness_runtime(load_models_config(ROOT / "config/models.yaml"), policy, environment={}, repository=ResearchRepository(store))
    assert fresh.oncolab.verification_records("science.acquisition-summary")
    count = len(fresh.oncolab.verification_records("source.gdc"))
    bind_repository(fresh, ResearchRepository(store))
    assert len(fresh.oncolab.verification_records("source.gdc")) == count
    assert fresh.manager.blocks() == ()  # Loading receipts never resumes research.
    with pytest.raises(ValueError, match="owned"):
        fresh.resolve_acquisition("foreign-block", source_id)
    from src.provenance import ExecutionReference
    from src.oncolab.registry import OncoLabVerificationRecord
    missing = OncoLabVerificationRecord(capability_id="source.gdc", verification_id="missing", execution_scope="test",
        execution_reference=ExecutionReference(kind="measurement", value="missing", block_id=block_id, sha256="0"*64), evidence=("test",))
    with pytest.raises(ValueError, match="unresolved measurement"):
        ResearchRepository(store).record_verification(missing)
    store.close()


@pytest.mark.parametrize("failure", [False, True])
def test_statement_support_remains_terminal_under_semantic_failure(tmp_path, failure):
    from src.dossier.builder import build_dossier
    from src.runtime.pydantic_ai.agents import create_agents
    from src.runtime.pydantic_ai.contracts import ResearcherDeps
    from src.sources.models import AcquisitionRecord
    from src.jev.failure import JevOperationalFailure
    from src.jev.models import JevExecutionFailure,JevFailureCategory
    manager=BlockManager();block=manager.create('response slice','test',ResourceAllocation(seconds=300))
    store=SqliteResearchStore(tmp_path/'statements.sqlite3');repo=ResearchRepository(store)
    runtime=HarnessRuntime(manager=manager,jev=DeterministicJevClient(),science=ScienceExecutor(),reasoner=DeterministicReasoner(),max_jev_calls=5,max_reasoner_calls=1,repository=repo)
    repo.record_block(block);runtime.research_state.start(block.block_id,block.objective)
    record=AcquisitionRecord(source='fixture',request={},records=({'x':1},),provenance=('fixture',))
    runtime.retain_acquisition(block.block_id,record)
    if failure:
        class FailedJev:
            def evaluate(self,state,questions):
                raise JevOperationalFailure(tuple(JevExecutionFailure(question_id=q.question_id,category=JevFailureCategory.TRANSPORT,detail='fixture') for q in questions))
        runtime.jev=FailedJev()
    async def model(messages,info):
        if not any(isinstance(m,ModelResponse) for m in messages):
            code=f'm = await measure_acquisition(acquisition_id="{record.acquisition_id}", analysis_id="slice")\ne = await admit_measurement(analysis_id="slice")\nawait record_dossier_statement(statement="This slice contains one response row", epistemic_type="descriptive", evidence_ids=[e["evidence_id"]])\nawait record_dossier_statement(statement="A hypothesis without resolved support", epistemic_type="hypothesis", evidence_ids=["missing"])\nawait complete_block(reason="handoff")'
            return ModelResponse(parts=[ToolCallPart('run_code',{'code':code},tool_call_id='statement')])
        return ModelResponse(parts=[TextPart('done')])
    agent=create_agents('test','test').researcher
    with agent.override(model=scripted(model)):agent.run_sync('summarize',deps=ResearcherDeps(runtime,block.block_id))
    evidence_records={r.record_id:r.payload for r in store.records(kind=RecordKind.EVIDENCE,block_id=block.block_id)}
    dossier=build_dossier(manager.block(block.block_id),manager.ledger(block.block_id).history(),runtime.research_state.get(block.block_id),'handoff',evidence_records=evidence_records)
    assert len(dossier.statements)==3
    assert dossier.statements[1].semantic_status==('unavailable' if failure else 'measured')
    assert dossier.statements[2].unresolved_refs==('missing',)
    repo.record_terminal(manager.block(block.block_id),dossier)
    store.close();store=SqliteResearchStore(tmp_path/'statements.sqlite3')
    view=reconstruct_block(store,block.block_id)
    assert len(view.dossier['statements'])==3 and len(view.evidence)==1
    assert bool(view.jev_failures)==failure
    store.close()


@pytest.mark.parametrize("failure", [False, True])
def test_semantic_memory_has_separate_global_budget_and_deterministic_fallback(tmp_path, failure):
    from src.runtime.pydantic_ai.search_tools import semantic_memory_context
    from src.memory.service import ResearchMemory
    store=SqliteResearchStore(tmp_path/'memory-semantic.sqlite3');repo=ResearchRepository(store)
    repo.record_cycle('m','live','melanoma expression',(),status='failed',error_type='SourceUnavailable')
    memory=ResearchMemory(store);memory.backfill()
    system=cycle_system();runtime=system.runtime;runtime.repository=repo;runtime.memory_jev_calls=1;runtime.memory_jev_questions=5
    if failure:
        class FailedJev:
            def evaluate(self,state,questions):raise TimeoutError('fixture timeout')
        runtime.jev=FailedJev()
    context=semantic_memory_context(runtime,'melanoma expression')
    assert context['digests'][0]['failure_reason']=='SourceUnavailable'
    assert context['semantic_status']==('deterministic_fallback' if failure else 'measured_context')
    assert runtime._counts['memory_jev']==1 and runtime._counts['memory_questions']==5
    again=semantic_memory_context(runtime,'melanoma expression')
    assert again['semantic_status']=='deterministic_fallback' and again['semantic_failure']=='WorkStopped'
    assert again['digests']==memory.context('melanoma expression').model_dump(mode='json')['digests']
    assert not runtime.manager.blocks() and not store.records(kind=RecordKind.EVIDENCE)
    calls=store.records(kind=RecordKind.JEV_CALL)
    assert len(calls)==2 and calls[-1].block_id is None
    assert len(store.records(kind=RecordKind.MEMORY_RETRIEVAL))==2
    store.close()
