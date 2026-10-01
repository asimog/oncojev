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


def test_notebook_export_and_publication_are_deterministic_downstream_only(tmp_path, monkeypatch):
    """Public rendering/publish failure cannot mutate evidence or consume notebook edits."""
    import subprocess
    from src.application.export import render_snapshot, write_snapshot
    from src.application.publication import publish_snapshot
    source = SqliteResearchStore(tmp_path / 'research.sqlite3')
    block = source.append(StoredRecord(kind=RecordKind.BLOCK, record_id='closed', block_id='owned',
        payload={'status': 'complete', 'start': {'objective': 'Evaluate a public cohort association'}}))
    evidence = source.append(StoredRecord(kind=RecordKind.EVIDENCE, record_id='original-evidence', block_id='owned',
        payload={'claim': 'A retained association', 'interpretation': 'associative', 'source_refs': ['measurement-1']}))
    source.append(StoredRecord(kind=RecordKind.DOSSIER, record_id='dossier', block_id='owned',
        payload={'uncertainties': ['Independent replication unavailable'], 'hypotheses': ['ghp_' + 'a' * 30],
                 'environment': {'OPENROUTER_API_KEY': 'private-sentinel'}, 'content_base64': 'private-bytes'}))
    prefix = source.count()
    baseline = source.records()
    files = render_snapshot(source, high_water=prefix)
    assert render_snapshot(source, high_water=prefix) == files
    manifest = json.loads(files['manifest.json'])
    assert manifest['source_high_water'] == prefix
    serialized = b''.join(files.values())
    assert b'private-sentinel' not in serialized and b'private-bytes' not in serialized and b'ghp_' not in serialized
    assert b'original-evidence' in serialized and b'Objective attainment: unknown' in serialized
    assert source.records() == baseline
    source.append(StoredRecord(kind=RecordKind.MEASUREMENT, record_id='later', payload={'values': {'x': 7}}))
    assert render_snapshot(source, high_water=prefix) == files
    checkout = tmp_path / 'notebook'
    checkout.mkdir()
    def git(*args):
        return subprocess.run(['git', '-C', str(checkout), *args], check=True, capture_output=True, text=True)
    git('init', '-b', 'main'); git('config', 'user.name', 'Fixture'); git('config', 'user.email', 'fixture@example.invalid')
    git('remote', 'add', 'origin', 'https://github.com/asimog/oncojevlab.git')
    real_run = subprocess.run
    pushes = []
    def transport(command, **kwargs):
        if command[:2] == ['git', '-C'] and command[3] == 'push':
            pushes.append(command)
            raise subprocess.TimeoutExpired(command, 60)
        return real_run(command, **kwargs)
    monkeypatch.setattr('src.application.publication.subprocess.run', transport)
    failure = publish_snapshot(source, files, checkout)
    assert failure['status'] == 'failed' and len(pushes) == 1
    assert source.record_at(block.seq) == block and source.record_at(evidence.seq) == evidence
    assert render_snapshot(source, high_water=prefix) == files
    def success_transport(command, **kwargs):
        if command[:2] == ['git', '-C'] and command[3] in ('push', 'ls-remote'):
            pushes.append(command)
            sha = real_run(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], check=True, capture_output=True, text=True).stdout.strip()
            return subprocess.CompletedProcess(command, 0, stdout=sha + '\trefs/heads/main\n', stderr='')
        return real_run(command, **kwargs)
    monkeypatch.setattr('src.application.publication.subprocess.run', success_transport)
    published = publish_snapshot(source, files, checkout)
    assert published['status'] == 'published'
    count = len(pushes)
    assert publish_snapshot(source, files, checkout) == published and len(pushes) == count
    (checkout / 'README.md').write_text('External notebook edit; never scientific input')
    assert source.record_at(evidence.seq) == evidence
    newer = render_snapshot(source)
    assert publish_snapshot(source, newer, checkout)['status'] == 'failed'
    assert (checkout / 'README.md').read_text() == 'External notebook edit; never scientific input'
    for _ in range(2):
        assert publish_snapshot(source, newer, checkout)['status'] == 'failed'
    receipts = source.records(kind=RecordKind.PUBLICATION)
    assert publish_snapshot(source, newer, checkout)['retry_exhausted'] is True
    assert source.records(kind=RecordKind.PUBLICATION) == receipts
    source.close()


def test_postgres_migration_preserves_reference_sequences_and_atomic_append(tmp_path):
    """Actual PostgreSQL boundary: migration identity, rollback and mutation denial."""
    import os
    import psycopg
    from src.persistence.postgres import PostgresResearchStore
    from scripts.migrate_records import migrate, configure_writer
    from src.provenance import content_hash
    url = os.environ.get('ONCOJEV_TEST_POSTGRES_URL')
    if not url:
        pytest.skip('requires isolated PostgreSQL integration database')
    source = SqliteResearchStore(tmp_path / 'source.sqlite3')
    first = source.append(StoredRecord(kind=RecordKind.MEASUREMENT, record_id='original',
        block_id='owned', payload={'values': {'effect': 2.5}, 'provenance': ['exact input']}))
    source.append(StoredRecord(kind=RecordKind.EVIDENCE, record_id='admitted-reference',
        block_id='owned', payload={'measurement_ref': {'seq': first.seq, 'record_id': first.record_id,
            'sha256': content_hash(first.payload)}, 'claim': 'retained source-bound observation'}))
    target = PostgresResearchStore(url, initialize=True)
    try:
        before = source.records()
        assert migrate(source, target)['status'] == 'migrated'
        assert target.records() == before
        assert migrate(source, target)['status'] == 'already_migrated'
        for sql in ('UPDATE records SET payload=payload', 'DELETE FROM records', 'TRUNCATE records'):
            with pytest.raises(psycopg.Error, match='append-only'):
                target._connection.execute(sql)
        circular = {}; circular['self'] = circular
        invalid = StoredRecord(kind=RecordKind.STATE_REVISION, record_id='invalid', payload=circular)
        with pytest.raises(ValueError, match='Circular'):
            target.append_many((StoredRecord(kind=RecordKind.STATE_REVISION, record_id='rolled-back', payload={}), invalid))
        assert target.records() == before
        saved = target.append(StoredRecord(kind=RecordKind.STATE_REVISION, record_id='next', payload={}))
        assert saved.seq > max(r.seq for r in before)
        assert target.high_water() == saved.seq and target.high_water() > target.count()
        from src.dossier.delta import build_delta
        block = BlockManager().create("migration fixture", "test", ResourceAllocation(seconds=60)).model_copy(update={"block_id":"owned"})
        delta = build_delta(target, block, "postgres-gap", 0, datetime.now(UTC))
        assert delta.end_sequence == saved.seq, "BlockDelta must pin a sequence, not a record count"
        assert target.record_at(first.seq) == first
        assert source.records() == before
        configure_writer(target, 'fixture-only-password-for-isolated-postgres-test')
        from urllib.parse import urlsplit, urlunsplit
        parsed = urlsplit(url)
        writer_url = urlunsplit(parsed._replace(netloc='oncojev_writer:fixture-only-password-for-isolated-postgres-test@' + parsed.netloc.rsplit('@', 1)[-1]))
        writer = PostgresResearchStore(writer_url)
        try:
            writer.append(StoredRecord(kind=RecordKind.STATE_REVISION, record_id='writer', payload={}))
            assert writer.count() == target.count()
            for sql in ('UPDATE records SET payload=payload', 'DELETE FROM records', 'TRUNCATE records',
                        'ALTER TABLE records ADD COLUMN forbidden TEXT'):
                with pytest.raises(psycopg.errors.InsufficientPrivilege):
                    writer._connection.execute(sql)
        finally:
            writer.close()
    finally:
        source.close(); target.close()


@pytest.mark.parametrize("failure", [False, True])
def test_director_global_frontier_retains_replication_relations_and_rejects_stale_basis(tmp_path, failure):
    """H4: real Director tool route, native receipts, immutable originals and reopen."""
    import asyncio
    from src.memory.models import CycleDigest, MemoryItem
    from src.memory.service import reference
    from src.runtime.pydantic_ai.contracts import DirectorDeps
    from src.runtime.pydantic_ai.global_tools import validate_selection
    system = cycle_system()
    runtime = system.runtime
    path = tmp_path / 'global.sqlite3'
    store = SqliteResearchStore(path)
    runtime.repository = ResearchRepository(store)
    runtime.memory_jev_calls = 20
    runtime.memory_jev_questions = 200
    runtime.memory_jev_bytes = 1000000
    for number, population in enumerate(('original', 'replication', 'other population', 'original')):
        record = store.append(StoredRecord(kind=RecordKind.STATE_REVISION, record_id=f's{number}',
            block_id=f'b{number}', payload={'statement': 'Melanoma expression predicts response', 'population': population}))
        item = MemoryItem(item_id=f'h{number}', summary=' MELANOMA  expression predicts response ' if number == 3 else 'Melanoma expression predicts response',
            epistemic_status='hypothesis', references=(reference(record),),
            details={'proposed_test': ' INDEPENDENT  cohort association ' if number == 3 else 'independent cohort association', 'population': population,
                     'replication': population == 'replication', 'capability_id': 'stat.scipy'})
        digest = CycleDigest(digest_id=f'd{number}', cycle_id=f'c{number}', direction='melanoma expression',
            recorded_at=datetime.now(UTC), cycle_status='complete', director_outcome='returned',
            hypotheses=(item,), references=(reference(record),))
        store.append(StoredRecord(kind=RecordKind.MEMORY_DIGEST, record_id=digest.digest_id, payload=digest.model_dump(mode='json')))
    from src.memory.service import ResearchMemory
    memory = ResearchMemory(store)
    assert len(memory.search('melanoma', capability='stat.scipy', hypothesis='h0', shared_reference='s0', lineage='c0')) == 1
    assert not memory.search('melanoma', capability='unavailable')
    if failure:
        class FailedJev:
            def evaluate(self, state, questions):
                raise TimeoutError('bounded fixture failure')
        runtime.jev = FailedJev()
    responses = []
    async def model(messages, info):
        if not any(isinstance(m, ModelResponse) for m in messages):
            return ModelResponse(parts=[ToolCallPart('run_code', {'code':
                'frontier = await prepare_global_frontier(objective="melanoma expression", limit=5)\n'
                'assert len(frontier["candidates"]) == 3\n'
                'assert len(frontier["beam"]) == 3\n'
                'candidate = frontier["candidates"][0]\n'
                'block = await allocate_block(objective=candidate["objective"], why_now="compare referenced hypotheses", '
                'frontier_id=frontier["frontier_id"], candidate_id=candidate["candidate_id"])\n'
                'assert block["objective"] == candidate["objective"]\nfrontier["frontier_id"]'}, tool_call_id='frontier')])
        responses.extend(str(p.content) for m in messages for p in m.parts if hasattr(p, 'content'))
        return ModelResponse(parts=[TextPart('planned')])
    with system.agents.director.override(model=scripted(model)):
        asyncio.run(system.agents.director.run('prepare a referenced next question', deps=DirectorDeps(runtime)))
    assert not any('AssertionError' in s or 'Exception:' in s or 'Type error' in s for s in responses), responses
    records = store.records(kind=RecordKind.GLOBAL_FRONTIER)
    assert len(records) == 1 and len(runtime.manager.blocks()) == 1
    frontier = records[0].payload
    candidate = frontier['candidates'][0]
    with pytest.raises(ValueError, match='stale'):
        validate_selection(runtime, frontier['frontier_id'], candidate['candidate_id'], candidate['objective'])
    assert frontier['relations'] and all(r['left']['source_refs'] and r['right']['source_refs'] for r in frontier['relations'])
    assert all(c['status'] == 'keep_alive' for c in frontier['candidates'])
    calls = store.records(kind=RecordKind.JEV_CALL)
    assert any(r.payload['context_type'] == 'global_investigation' for r in calls)
    assert all(r.payload['policy_version'] == 'global-frontier-policy-v1' for r in calls if r.payload['context_type'].startswith('global_'))
    assert all(r.block_id is None for r in calls)
    assert not store.records(kind=RecordKind.EVIDENCE)
    store.close()
    reopened = SqliteResearchStore(path)
    assert reopened.records(kind=RecordKind.GLOBAL_FRONTIER)[0].payload == frontier
    assert len(reopened.records(kind=RecordKind.GLOBAL_RELATION)) == len(frontier['relations'])
    reopened.close()



def test_block_registry_search_remains_pinned_after_governed_change(tmp_path):
    """Old tool contracts/history survive accepted changes; next allocation refreshes."""
    import asyncio
    from src.oncolab.institution import InstitutionalObservation
    from src.oncolab.models import OncoLabAvailability
    from src.provenance import content_hash
    from src.runtime.pydantic_ai.contracts import ResearcherDeps
    from src.runtime.pydantic_ai.factory import bind_repository
    system = cycle_system()
    runtime = system.runtime
    store = SqliteResearchStore(tmp_path / 'institution.sqlite3')
    bind_repository(runtime, ResearchRepository(store))
    first = runtime.manager.allocate('check registry', 'pin initial contracts')
    old = runtime.index_for(first.block_id)
    descriptor = old.describe('stat.scipy')
    changed = descriptor.model_copy(update={'purpose': 'Governed changed scientific contract', 'availability': OncoLabAvailability.FORBIDDEN})
    descriptors = tuple(changed if d.capability_id == changed.capability_id else d for d in old.descriptors())
    change = {'descriptors': [d.model_dump(mode='json') for d in descriptors],
              'routes': {k: [r.model_dump(mode='json') for r in v] for k, v in old.routes.items()}}
    review = store.append(StoredRecord(kind=RecordKind.REGISTRY_REVIEW, record_id='review',
        payload={'status': 'accepted', 'parent': old.revision_id, 'change_sha256': content_hash(change)}))
    runtime.institution.accept(descriptors, old.routes, expected_parent=old.revision_id, governance_reference=review.seq)
    runtime.institution.observe(InstitutionalObservation(observation_id='demand', capability_id='stat.scipy',
        kind='demand', source_seq=review.seq, payload={'need': 'distinct test'}, provenance='review-linked demand'))
    second = runtime.manager.allocate('check next registry', 'refresh accepted contracts')
    assert second.start.oncolab_registry_revision != first.start.oncolab_registry_revision
    assert second.start.oncolab_history_high_water > first.start.oncolab_history_high_water
    runtime.index_for()  # Director sees new state while the old Researcher is active.
    results = []
    async def model(messages, info):
        if not any(isinstance(m, ModelResponse) for m in messages):
            return ModelResponse(parts=[ToolCallPart('run_code', {'code':
                'contract = await describe_oncolab(capability_id="stat.scipy")\n'
                'assert contract is not None\ncontract["descriptor"]["purpose"]'}, tool_call_id='pinned')])
        results.extend(str(p.content) for m in messages for p in m.parts if hasattr(p, 'content'))
        return ModelResponse(parts=[TextPart('checked')])
    with system.agents.researcher.override(model=scripted(model)):
        asyncio.run(system.agents.researcher.run('describe original contract', deps=ResearcherDeps(runtime, first.block_id)))
    assert any(descriptor.purpose in result for result in results), results
    receipts = store.records(kind=RecordKind.INDEX_RECEIPT)
    assert receipts[-1].payload['oncolab_registry_revision'] == old.revision_id
    assert receipts[-1].payload['oncolab_history_high_water'] == first.start.oncolab_history_high_water
    assert runtime.index_for(second.block_id).describe('stat.scipy').purpose == changed.purpose
    revision = runtime.institution.pin().oncolab_registry_revision
    runtime.append_event(first.block_id, 'CapabilityInvocation', {'capability_id': 'stat.scipy', 'invocation_id': 'old-scope'})
    assert runtime.institution.pin().oncolab_registry_revision == revision
    assert runtime.institution.pin().oncolab_history_high_water > second.start.oncolab_history_high_water
    assert runtime.index_for(first.block_id).history_high_water == first.start.oncolab_history_high_water
    with pytest.raises(ValueError, match='pinned registry'):
        runtime.append_event(second.block_id, 'CapabilityInvocation', {'capability_id': 'stat.scipy'})
    cursor = old.search_page(limit=1).continuation
    with pytest.raises(ValueError, match='continuation'):
        runtime.index_for(second.block_id).search_page(limit=1, continuation=cursor)
    pin = first.start
    store.close()
    reopened = SqliteResearchStore(tmp_path / 'institution.sqlite3')
    from src.oncolab.institution import OncoLabInstitution, RegistryPin
    institution = OncoLabInstitution(reopened, old, pin.application_identity)
    historical = institution.index(RegistryPin(oncolab_registry_revision=pin.oncolab_registry_revision,
        oncolab_history_high_water=pin.oncolab_history_high_water, application_identity=pin.application_identity))
    assert historical.describe('stat.scipy') == descriptor
    reopened.close()

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

    import asyncio
    director_response_started = asyncio.Event()
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
        director_response_started.set()
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
        await director_response_started.wait()
        return ModelResponse(parts=[TextPart("No scientific estimate is attainable with available inputs")])

    succeeds = scenario in {"completed", "usage_truncation", "tool_truncation"}
    with system.agents.director.override(model=scripted(director)), system.agents.researcher.override(model=scripted(researcher)):
        if succeeds:
            result = run_cycle(system, "direction", repository=repository)
            assert result.status.value == ("complete" if scenario == "completed" else "incomplete")
            assert result.director_outcome.value in ({"returned", "interrupted"} if scenario == "completed" else {"truncated"})
        else:
            with pytest.raises(Exception):
                run_cycle(system, "direction", repository=repository)
    cycles = repository.store.records(kind=RecordKind.CYCLE)
    assert len(cycles) == 1
    assert cycles[0].payload["status"] == ("complete" if scenario == "completed" else "incomplete" if succeeds else "failed")
    if scenario in errors:
        assert cycles[0].payload["director_error_type"] == type(errors[scenario]).__name__
    blocks = system.runtime.manager.blocks()
    assert len(blocks) == (0 if scenario in {"before_allocation", "no_allocation"} else 1)
    for block in blocks:
        view = reconstruct_block(repository.store, block.block_id)
        researcher_completed = researcher_calls > 0 and scenario not in {"handoff_failure", "fallback_failure"}
        assert view.complete is researcher_completed
        assert view.dossier["objective_attainment"] == "unknown"
        assert view.block["status"] == ("complete" if researcher_completed else "failed")
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
    expanded = context.model_dump(mode="json")
    expanded["digests"][0]["literature_contexts"] = [{"summary": "癌" * 1000} for _ in range(20)]
    bounded = memory.start_context("legacy", context=expanded)
    assert len(canonical_bytes(bounded.model_dump(mode="json"))) <= 16384
    assert bounded.prior_contexts and bounded.omitted_items > 0
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
        original_mission = service.store.latest(RecordKind.CYCLE).payload["mission_id"]
        system = cycle_system()
        system.runtime.researcher_factory = lambda block_id: system.agents.researcher
        calls = 0
        system.agents.director.model = scripted(director)
        system.agents.researcher.model = scripted(researcher)
        service.run_once("changed human direction")
        changed_mission = service.store.latest(RecordKind.CYCLE).payload["mission_id"]
        assert changed_mission != original_mission
        assert service.store.latest(RecordKind.MISSION).payload["parent_mission_id"] == original_mission
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
                code += ('frontier = await prepare_global_frontier(objective="melanoma public expression", limit=5)\n'
                         'assert frontier["candidates"], "unchanged mission lost prior investigations"\n'
                         'filtered = await search_research_memory(query="melanoma", filters={"entity": "TCGA-SKCM", "topic": "expression"})\n'
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
    runtime.literature = PublicLiteratureSource(httpx.MockTransport(lambda request: httpx.Response(200, json={"message": {
        "total-results": 100, "items": [
            {"title": ["Public study"], "DOI": "10.1/study", "abstract": "<jats:p>Retained population and endpoint.</jats:p>"},
            {"title": ["Title only"], "DOI": "10.1/title"},
        ]}})))
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
                    'await search_public_literature(query="public study", limit=2)\n'
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
    assert stored["request"].get("filters", {}) == {}, "discovery must retain the exact requested filter without hiding access alternatives"
    assert view.measurements[0]["input_sha256"] == stored["content_sha256"]
    from src.sources.models import AcquisitionRecord
    copy = AcquisitionRecord.model_validate(stored).model_copy(update={"acquisition_id": "different-run"})
    assert copy.content_sha256 == stored["content_sha256"]
    assert not view.unresolved_source_refs
    assert view.literature[0]["records"][0]["doi"] == "10.1/study"
    assert view.literature[0]["request"] == {"query": "public study", "rows": 2}
    literature = view.literature[0]
    assert literature["records"][0]["abstract"] == "<jats:p>Retained population and endpoint.</jats:p>"
    assert literature["records"][1]["abstract"] is None
    assert literature["coverage"]["reported_total"] == 100
    assert literature["coverage"]["returned_rows"] == 2
    assert literature["coverage"]["complete"] is False
    from src.sources.models import LiteratureSearchResult
    reopened_literature = LiteratureSearchResult.model_validate(literature)
    assert reopened_literature.retrieved_at is not None
    assert reopened_literature.content_sha256 == literature["content_sha256"]
    altered_record = reopened_literature.records[0].model_copy(update={"abstract": "Different endpoint"})
    assert reopened_literature.model_copy(update={"records": (altered_record,)}).content_sha256 != literature["content_sha256"]
    legacy = LiteratureSearchResult.model_validate({"query": "public study", "records": [
        {"title": "Public study", "doi": "10.1/study", "url": None, "source": "crossref"}],
        "provenance": ["https://api.crossref.org/works"]})
    assert legacy.retrieved_at is None and legacy.coverage is None
    assert legacy.content_sha256 == "7932afaee924646f538dc179d25e66b1ed1faef86f8f491f1405b3d47facbf55"
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


def test_source_resolved_paired_analysis_and_repeat_admission_survive_reopen(tmp_path):
 from src.runtime.pydantic_ai.contracts import ResearcherDeps
 system=cycle_system();runtime=system.runtime
 repository=ResearchRepository(SqliteResearchStore(tmp_path/"analysis.sqlite3"));runtime.repository=repository
 block=runtime.manager.create("paired association","curated need",ResourceAllocation(seconds=60,handoff_reserve_seconds=5))
 repository.record_block(block)
 record=AcquisitionRecord(source="controlled-public",request={"fields":["id","x","y"]},
  records=({"id":"a","x":1,"y":2},{"id":"b","x":2,"y":4},{"id":"c","x":3,"y":5},{"id":"d","x":None,"y":100}),provenance=("controlled-response",))
 runtime.retain_acquisition(block.block_id,record)
 calls=0
 async def respond(messages,info):
  nonlocal calls
  calls+=1
  if calls>1:return ModelResponse(parts=[TextPart("finished")])
  args=f'acquisition_id="{record.acquisition_id}", question="association", population="stored public response", estimand="Pearson r", method="pearson_correlation", fields={{"x":"x","y":"y"}}, entity_field="id", entity_unit="sample", design="paired independent sample rows"'
  code=f'a=await run_source_analysis(analysis_id="a", {args})\ne=await admit_measurement(analysis_id="a")\ne2=await admit_measurement(analysis_id="a")\nb=await run_source_analysis(analysis_id="b", {args})\ne3=await admit_measurement(analysis_id="b")\nr=await run_source_analysis(analysis_id="r", replication_id="declared-repeat-1", {args})\ner=await admit_measurement(analysis_id="r")'
  return ModelResponse(parts=[ToolCallPart("run_code",{"code":code},tool_call_id="paired")])
 with system.agents.researcher.override(model=scripted(respond)):
  response=system.agents.researcher.run_sync("execute paired analysis",deps=ResearcherDeps(runtime=runtime,block_id=block.block_id))
 measurements=repository.store.records(kind=RecordKind.MEASUREMENT,block_id=block.block_id)
 assert len(measurements)==3, [str(p) for m in response.all_messages() for p in m.parts if p.part_kind not in {"user-prompt","text","tool-call"}]
 values=measurements[0].payload["values"]
 assert values["correlation"]==pytest.approx(0.9819805060619657)
 assert measurements[0].payload["analysis_key"]=="fc132fe80615e13ae64f6be89894ac33f869ba79acef62bb84af32f67c943a77", "historical unplanned v1 identity must remain stable"
 assert measurements[0].payload["diagnostics"]["paired_entities"]==["a","b","c"]
 assert measurements[0].payload["diagnostics"]["counts"]=={"total_rows":4,"complete_pairs":3,"excluded_rows":1}
 assert len(repository.store.records(kind=RecordKind.EVIDENCE))==2
 assert len(runtime.research_state.get(block.block_id).evidence_ids)==2
 spec=AnalysisSpec(analysis_id="bad",question="q",population="slice",estimand="r",method="pearson_correlation",variables=("x","y"),fields={"x":"x","y":"y"},entity_field="id",source_refs=(record.acquisition_id,))
 with pytest.raises(ValueError,match="duplicate entity"):
  runtime.science.execute_source(record.model_copy(update={"records":({"id":"same","x":1,"y":2},{"id":"same","x":3,"y":4})}),spec)
 with pytest.raises(ValueError,match="nonconstant"):
  runtime.science.execute_source(record.model_copy(update={"records":({"id":"a","x":1,"y":2},{"id":"b","x":1,"y":4})}),spec)
 from src.sources.models import CoverageContract
 file_rows=record.model_copy(update={"source":"gdc","coverage":CoverageContract(endpoint="files",returned_rows=4)})
 with pytest.raises(ValueError,match="entity unit/key"):
  runtime.science.execute_source(file_rows,spec.model_copy(update={"entity_unit":"patient"}))
 with pytest.raises(ValueError,match="not supplied arrays"):
  runtime.science.execute_source(record,spec.model_copy(update={"inputs":{"x":[1,2],"y":[3,4]}}))
 repository.store.close()
 reopened=SqliteResearchStore(tmp_path/"analysis.sqlite3")
 assert len(reopened.records(kind=RecordKind.EVIDENCE))==2
 assert reconstruct_block(reopened,block.block_id).unresolved_source_refs==()
 reopened.close()


def test_literature_context_cycle_retains_native_basis_and_unknowns_without_changing_evidence(tmp_path):
    """Scripted native judgments prove context plumbing/abstention, not classification truth."""
    import httpx
    from src.sources.public import GdcPublicSource, PublicLiteratureSource
    from src.jev.models import ChoiceDecision, NoulDecision
    from src.memory.service import ResearchMemory
    from src.application.export import render_snapshot
    system = cycle_system(); runtime = system.runtime
    runtime.researcher_factory = lambda block_id: system.agents.researcher
    runtime.max_jev_calls = 20; runtime.max_tool_calls = 100
    database = tmp_path / 'literature-context.sqlite3'
    repository = ResearchRepository(SqliteResearchStore(database))
    rows = [{'id':str(i), 'case_id':str(i), 'x':i, 'y':2*i + (0.2 if i%2 else -0.2)} for i in range(8)]
    runtime.gdc = GdcPublicSource(httpx.MockTransport(lambda request: httpx.Response(200,
        json={'data':{'hits':rows, 'pagination':{'total':8}}})))
    def literature(request):
        query = request.url.params['query']
        if query == 'search_failure': return httpx.Response(503)
        item = {'title':['Retained report'], 'DOI':'10.1/report',
                'abstract':'Association of X and Y in inspected case rows; context and uncertainty require comparison.'}
        if query == 'title_only': item.pop('abstract')
        return httpx.Response(200, json={'message':{'items':[] if query == 'empty' else [item],
            'total-results':0 if query == 'empty' else 100 if query == 'incomplete' else 1}})
    runtime.literature = PublicLiteratureSource(httpx.MockTransport(literature))
    measured = []
    class NativeFixture(DeterministicJevClient):
        def evaluate(self, state, questions):
            if not questions[0].semantic_purpose.startswith('literature_context.'):
                return super().evaluate(state, questions)
            query = state['literature'][0]['query']; measured.append(query)
            if query == 'provider_failure': raise RuntimeError('fixture provider unavailable')
            category = query if query in {'known_result','rediscovery','known_mechanism_new_context',
                'contradictory_finding','potentially_novel_observation'} else 'potentially_novel_observation'
            decisions = []
            for q in questions:
                context = dict(question_id=q.question_id, model_requested='fixture', model_resolved='fixture',
                    question_version=q.question_version, projection_id=q.projection_id)
                if q.primitive == 'choice':
                    probabilities = {key:(.9 if key == category else .02) for key in q.criteria}
                    if query == 'uncertain': probabilities = {key:(.5 if key in {category,'unknown'} else 0) for key in q.criteria}
                    decisions.append(ChoiceDecision(**context, selected_option=category, probabilities=probabilities, confidence=.9))
                else:
                    decisions.append(NoulDecision(**context, p_true=.5 if query == 'scope_missing' and
                        q.semantic_purpose.endswith('scope_known') else .9))
            return tuple(decisions)
    runtime.jev = NativeFixture()
    cases = ['known_result','rediscovery','known_mechanism_new_context','contradictory_finding',
             'potentially_novel_observation','uncertain','scope_missing','provider_failure','title_only','empty','incomplete']
    async def director(messages, info):
        if not any(isinstance(m, ModelResponse) for m in messages):
            return ModelResponse(parts=[ToolCallPart('run_code', {'code':
                'b = await allocate_block(objective="literature association context", why_now="compare retained reports", seconds=120)\n'
                'await launch_researcher(block_id=b["block_id"])'}, tool_call_id='launch-context')])
        return ModelResponse(parts=[TextPart('review tentative context')])
    outputs = []
    async def researcher(messages, info):
        if not any(isinstance(m, ModelResponse) for m in messages):
            code = ['a = await acquire_gdc(endpoint="cases", filters={}, fields=["case_id","x","y"], size=10)',
                'h = await assess_hypothesis(hypothesis="X has a positive association with Y", proposed_test="directional Pearson association")',
                'plan = {"hypothesis_id":h["identity"], "direction":"positive", "minimum_effect":0.3, "multiplicity_family":[h["identity"]]}',
                'r = await run_source_analysis(acquisition_id=a["acquisition_id"], analysis_id="association", question="association", population="inspected fixture cases", estimand="Pearson r", method="pearson_correlation", fields={"x":"x","y":"y"}, entity_field="id", entity_unit="case", design="unadjusted complete-row association", test_plan=plan)',
                'await admit_measurement(analysis_id="association")']
            for query in cases:
                code.append(f'l = await search_public_literature(query="{query}", limit=1)')
                if query == 'potentially_novel_observation': code.append('novel_search = l["context_id"]')
                code.append('await assess_literature_context(analysis_id="association", claim="X is positively associated with Y in the inspected rows.", literature_ids=[l["context_id"]])')
            code.extend(['try:\n    await search_public_literature(query="search_failure", limit=1)\nexcept Exception:\n    pass',
                'await assess_literature_context(analysis_id="association", claim="X is positively associated with Y in the inspected rows.", literature_ids=[novel_search])',
                'try:\n    await assess_literature_context(analysis_id="foreign", claim="Invented finding", literature_ids=[novel_search])\nexcept ValueError:\n    pass',
                'await complete_block(reason="context retained")'])
            return ModelResponse(parts=[ToolCallPart('run_code', {'code':'\n'.join(code)}, tool_call_id='assess-context')])
        outputs.extend(str(p.content) for m in messages for p in m.parts if getattr(p, 'content', None))
        return ModelResponse(parts=[TextPart('Tentative context, no novelty proof')])
    with system.agents.director.override(model=scripted(director)), system.agents.researcher.override(model=scripted(researcher)):
        result = run_cycle(system, 'literature association context', repository=repository)
    assert result.status.value == 'complete'
    assert not any('Runtime error' in value or 'Type error' in value for value in outputs), outputs
    saved = repository.store.records(kind=RecordKind.LITERATURE_CONTEXT)
    assert len(saved) == 12
    assert [r.payload['category'] for r in saved] == cases[:5] + ['unknown']*7
    assert saved[7].payload['semantic_status'] == 'unavailable'
    assert all(r.payload['epistemic_status'] == 'tentative_literature_context' for r in saved)
    assert all(any(ref['kind'] == 'state_revision' for ref in r.payload['basis']) for r in saved)
    assert 'title_only' not in measured and 'empty' not in measured
    assert saved[-1].payload['unresolved']
    memory = ResearchMemory(repository.store)
    for item in saved:
        for ref in item.payload['basis']:
            from src.memory.models import MemoryReference
            memory.resolve(MemoryReference.model_validate(ref))
    assert any(ref['kind'] == 'jev_call' for ref in saved[7].payload['basis'])
    failed_query_basis = [memory.resolve(MemoryReference.model_validate(ref)) for ref in saved[-1].payload['basis'] if ref['kind'] == 'ledger_event']
    assert any(p.get('event_type') == 'CapabilityFailure' for p in failed_query_basis)
    assert any(p.get('event_type') == 'CapabilityInvocation' and p['payload'].get('query') == 'search_failure' for p in failed_query_basis)
    measurements = repository.store.records(kind=RecordKind.MEASUREMENT)
    evidence = repository.store.records(kind=RecordKind.EVIDENCE)
    assert len(measurements) == len(evidence) == 1 and evidence[0].payload['measurement'] == measurements[0].payload
    digest = memory.search('literature')[0]
    assert len(digest.literature_contexts) == 12 and not digest.scientific_negative_findings
    assert memory.start_context('literature').prior_contexts
    assert memory.context('literature').digests[0]['literature_contexts'][0]['details']['category'] == 'known_result'
    assert len(runtime.active_research.delta.references['literature_contexts']) == 12
    exported = render_snapshot(repository.store)
    exported_records = next(json.loads(data) for name,data in exported.items() if name.startswith('blocks/') and name.endswith('records.json'))
    assert len([r for r in exported_records if r['kind'] == 'literature_context']) == 12
    assert any(r['kind'] == 'jev_call' and r['payload']['outcome'] == 'failed' for r in exported_records)
    summary = next(data.decode() for name,data in exported.items() if name.startswith('blocks/') and name.endswith('summary.md'))
    assert 'rediscovery: 1' in summary and 'unknown: 7' in summary
    assert 'not proof of novelty or independent replication' in summary
    repository.store.close()
    reopened = SqliteResearchStore(database)
    try:
        assert len(reconstruct_block(reopened, result.block_ids[0]).literature_contexts) == 12
        assert len(ResearchMemory(reopened).search('literature')[0].literature_contexts) == 12
    finally:
        reopened.close()


def test_directional_scientific_attempt_history_retains_effect_bounds_and_unknowns(tmp_path):
    """Real cycle/source/tools/admission -> resolved history, with model-conditional outcomes."""
    import httpx
    from src.sources.public import GdcPublicSource
    from src.memory.service import ResearchMemory
    system = cycle_system(); runtime = system.runtime
    runtime.researcher_factory = lambda block_id: system.agents.researcher
    runtime.max_tool_calls = 100
    database = tmp_path / 'scientific-history.sqlite3'
    repository = ResearchRepository(SqliteResearchStore(database))
    positive = [{'id':str(i), 'case_id':str(i), 'x':i-3, 'y':2*(i-3) + (0.25 if i%2 else -0.25)} for i in range(8)]
    fixtures = {
        'positive':positive,
        'reversed':[{**r,'y':-r['y']} for r in positive],
        'null':[{'id':str(i),'case_id':str(i),'x':i-3,'y':(i-3)**2} for i in range(7)],
        'duplicate':[positive[0],positive[0],*positive[2:]],
    }
    calls = 0
    def transport(request):
        nonlocal calls
        name = tuple(fixtures)[calls]; calls += 1
        return httpx.Response(200, json={'data':{'hits':fixtures[name], 'pagination':{'total':len(fixtures[name])}}})
    runtime.gdc = GdcPublicSource(httpx.MockTransport(transport))
    async def director(messages, info):
        if not any(isinstance(m, ModelResponse) for m in messages):
            return ModelResponse(parts=[ToolCallPart('run_code', {'code':
                'b = await allocate_block(objective="directional association", why_now="inspect effect uncertainty", seconds=120)\n'
                'await launch_researcher(block_id=b["block_id"])'}, tool_call_id='launch')])
        return ModelResponse(parts=[TextPart('review retained outcomes')])
    outputs = []
    external_lease = None
    busy_requested = False
    async def researcher(messages, info):
        nonlocal external_lease, busy_requested
        if not any(isinstance(m, ModelResponse) for m in messages):
            code = ['h = await assess_hypothesis(hypothesis="X has a positive association with Y", proposed_test="directional Pearson association")',
                    'plan = {"hypothesis_id":h["identity"], "direction":"positive", "minimum_effect":0.3, "multiplicity_family":[h["identity"]]}']
            for name in fixtures:
                code.append(f'a = await acquire_gdc(endpoint="cases", filters={{}}, fields=["case_id","x","y"], size=10)')
                call = (f'r = await run_source_analysis(acquisition_id=a["acquisition_id"], analysis_id="{name}", '
                    'question="directional association", population="inspected fixture cases", estimand="Pearson r", '
                    'method="pearson_correlation", fields={"x":"x","y":"y"}, entity_field="id", entity_unit="case", '
                    'design="unadjusted association with declared independent cases", test_plan=plan)')
                if name == 'positive':
                    code.append('positive_acquisition = a["acquisition_id"]')
                if name == 'duplicate':
                    code.append('try:\n    '+call+'\nexcept Exception:\n    pass')
                else:
                    code.extend([call, f'await admit_measurement(analysis_id="{name}")'])
            code.extend([
                'family = {**plan, "multiplicity_family":[h["identity"], "comparison-2", "comparison-3", "comparison-4"]}',
                'adjusted = await run_source_analysis(acquisition_id=positive_acquisition, analysis_id="family", question="directional association", population="inspected fixture cases", estimand="Pearson r", method="pearson_correlation", fields={"x":"x","y":"y"}, entity_field="id", entity_unit="case", design="exploratory family", test_plan=family)',
                'ols_plan = {**plan, "minimum_effect":1.0}',
                'ols = await run_source_analysis(acquisition_id=positive_acquisition, analysis_id="ols", question="directional slope association", population="inspected fixture cases", estimand="OLS slope", method="ordinary_least_squares", fields={"x":"x","y":"y"}, entity_field="id", entity_unit="case", design="unadjusted linear model", test_plan=ols_plan)',
            ])
            return ModelResponse(parts=[ToolCallPart('run_code', {'code':'\n'.join(code)}, tool_call_id='analyses')])
        outputs.extend(str(p.content) for m in messages for p in m.parts if hasattr(p,'content'))
        if not busy_requested:
            busy_requested = True
            external_lease = runtime.service_resources.heavy("other-host-operation")
            await external_lease.__aenter__()
            return ModelResponse(parts=[ToolCallPart('run_code', {'code':
                'try:\n    await run_source_analysis(acquisition_id=positive_acquisition, analysis_id="busy", question="directional association", population="inspected fixture cases", estimand="Pearson r", method="pearson_correlation", fields={"x":"x","y":"y"}, entity_field="id", entity_unit="case", design="declared independent cases", test_plan=plan)\nexcept Exception:\n    pass\n'
                'await complete_block(reason="retained explicit scientific and operational outcomes")'}, tool_call_id='busy')])
        if external_lease:
            await external_lease.__aexit__(None, None, None)
            external_lease = None
        return ModelResponse(parts=[TextPart('No causal or scientific-absence claim')])
    try:
        with system.agents.director.override(model=scripted(director)), system.agents.researcher.override(model=scripted(researcher)):
            result = run_cycle(system, 'directional association', repository=repository)
        assert result.status.value == 'complete'
        assert not any('Runtime error' in value or 'Type error' in value for value in outputs), outputs
        terminal = {r.payload['analysis']['analysis_id']:r.payload for r in repository.store.records(kind=RecordKind.SCIENTIFIC_ATTEMPT)
                    if r.payload['stage'] != 'started'}
        assert {key:value['outcome'] for key,value in terminal.items()} == {
            'positive':'supported', 'reversed':'contradicted', 'null':'inconclusive', 'duplicate':'invalid',
            'family':'supported', 'ols':'supported', 'busy':'attempted'}
        measurements = {r.record_id:r.payload for r in repository.store.records(kind=RecordKind.MEASUREMENT)}
        assert measurements['null']['values']['correlation'] == pytest.approx(0)
        assert measurements['null']['values']['p_value_adjusted'] == pytest.approx(1)
        assert measurements['positive']['values']['effect_ci_low'] > 0.3
        assert measurements['reversed']['values']['effect_ci_high'] < -0.3
        assert terminal['busy']['stage'] == 'operational_failed' and terminal['busy']['failure_type'] == 'ResourceBusy'
        assert measurements['family']['values']['alpha_per_test'] == pytest.approx(0.0125)
        assert measurements['family']['values']['effect_ci_low'] <= measurements['positive']['values']['effect_ci_low']
        assert measurements['family']['values']['effect_ci_high'] >= measurements['positive']['values']['effect_ci_high']
        assert measurements['ols']['values']['slope'] == pytest.approx(2.0238095238095237)
        assert measurements['ols']['values']['effect_ci_low'] > 1
        assert 'busy' not in measurements
        assert 'duplicate' not in measurements and len(repository.store.records(kind=RecordKind.EVIDENCE)) == 3
        memory = ResearchMemory(repository.store)
        digest = memory.search('directional')[0]
        assert len(runtime.active_research.delta.references['scientific_attempts']) == 14
        assert len(digest.scientific_attempts) == 7 and not digest.scientific_negative_findings
        assert {item.details['outcome'] for item in digest.scientific_attempts} == {'supported','contradicted','inconclusive','invalid','attempted'}
        for item in digest.scientific_attempts:
            assert item.references
            for ref in item.references: memory.resolve(ref)
        start = memory.start_context('directional')
        assert any('inconclusive' in value for value in start.prior_attempts)
        assert any('invalid' in value for value in start.prior_attempts)
        assert not memory.items('scientific_negative_findings', 'directional')
        assert memory.context('directional').digests[0]['scientific_attempts'][0]['details']['meaning']
    finally:
        if external_lease:
            import asyncio
            asyncio.run(external_lease.__aexit__(None, None, None))
        repository.store.close()
    reopened = SqliteResearchStore(database)
    try:
        memory = ResearchMemory(reopened)
        assert len(memory.search('directional')[0].scientific_attempts) == 7
        assert reconstruct_block(reopened, result.block_ids[0]).complete
    finally:
        reopened.close()


def test_exact_public_artifact_retention_ownership_and_sandbox_replay(tmp_path):
 import asyncio,hashlib,subprocess
 import httpx
 from src.sources.public import GdcPublicSource
 from src.sources.models import ScientificArtifact
 from src.science.sandbox import DockerScientificSandbox,GithubMethodRequest,SandboxError,validate_sandbox_candidate
 data=b"sample\tx\ty\na\t1\t2\nb\t2\t4\n"
 file_id="11111111-1111-4111-8111-111111111111"
 class Stream(httpx.AsyncByteStream):
  async def __aiter__(self):yield data
 def transport(request):
  if request.url.path.startswith("/files/"):
   return httpx.Response(200,json={"data":{"access":"open","file_size":len(data),"md5sum":hashlib.md5(data).hexdigest()}})
  return httpx.Response(200,stream=Stream())
 source=GdcPublicSource(httpx.MockTransport(transport),max_download_bytes=1000)
 artifact=asyncio.run(source.acquire_file(file_id,"owner","tsv"))
 database=tmp_path/"artifacts.sqlite3";store=SqliteResearchStore(database);repo=ResearchRepository(store)
 repo.record_scientific_artifact(artifact);store.close()
 store=SqliteResearchStore(database);repo=ResearchRepository(store)
 retained=repo.resolve_scientific_artifact("owner",artifact.artifact_id)
 assert retained.bytes()==data and retained.byte_sha256==hashlib.sha256(data).hexdigest()
 assert retained.licence is None and retained.release is None
 with pytest.raises(ValueError,match="not owned"):repo.resolve_scientific_artifact("peer",artifact.artifact_id)
 with pytest.raises(ValueError,match="byte identity"):ScientificArtifact.model_validate(retained.model_dump(mode="json")|{"size_bytes":100})
 seen=[]
 def runner(arguments,**kwargs):
  if arguments[:2]==("git","ls-remote"):return subprocess.CompletedProcess(arguments,0,"a"*40+"\tHEAD\n","")
  if arguments[:3]==("docker","image","inspect"):return subprocess.CompletedProcess(arguments,0,"sha256:"+"b"*64+"\n","")
  if arguments[:2]==("docker","run"):
   seen.append(arguments)
   command=arguments[arguments.index("sha256:"+"b"*64)+1:]
   if command==("python","method.py","/input/request.json"):
    mount=next(x for x in arguments if x.endswith(":/input/artifacts:ro"))
    host=Path(mount.removesuffix(":/input/artifacts:ro"))
    assert (host/retained.byte_sha256).read_bytes()==data
    return subprocess.CompletedProcess(arguments,0,'{"values":{"rows":2}}\n',"")
  return subprocess.CompletedProcess(arguments,0,"ok\n","")
 request=GithubMethodRequest(repository_url="https://github.com/example/method",test_command=("pytest",),execute_command=("python","method.py","/input/request.json"),input_json={"path":f"/input/artifacts/{retained.byte_sha256}"},input_artifacts=(retained,))
 sandbox=DockerScientificSandbox(runner=runner);candidate=sandbox.acquire_and_execute(request)
 result=validate_sandbox_candidate(candidate,"file-analysis")
 assert result.values=={"rows":2.0} and result.origin=="sandbox"
 assert sandbox.replay(candidate).receipt.input_sha256==candidate.receipt.input_sha256
 assert all("none" in args for args in seen if ":/input/artifacts:ro" in " ".join(args))
 mutated=retained.model_copy(update={"content_base64":"YmFk"})
 with pytest.raises(ValueError,match="byte identity"):sandbox.acquire_and_execute(request.model_copy(update={"input_artifacts":(mutated,)}))
 # Exercise the real Code Mode acquisition -> owned byte resolution -> sandbox -> admission path.
 from src.runtime.pydantic_ai.contracts import ResearcherDeps
 system=cycle_system();runtime=system.runtime;runtime.repository=repo;runtime.gdc=source;runtime.sandbox=sandbox
 block=runtime.manager.create("scientific file measurement","fixture bridge",ResourceAllocation(seconds=60,handoff_reserve_seconds=5))
 repo.record_block(block)
 calls=0
 async def respond(messages,info):
  nonlocal calls
  calls+=1
  if calls>1:return ModelResponse(parts=[TextPart("complete")])
  code=f'a=await acquire_gdc_file(file_id="{file_id}",format="tsv")\nc=await acquire_github_scientific_method(capability_need="paired file rows",why_existing_capabilities_are_inadequate="Existing metadata wrappers do not parse this file",repository_url="https://github.com/example/method",requested_ref="HEAD",install_command=["python","-m","pip","install","."],test_command=["pytest"],execute_command=["python","method.py","/input/request.json"],input_json={{"path":a["sandbox_path"]}},artifact_ids=[a["artifact_id"]])\nawait validate_sandbox_measurement(candidate_id=c["candidate_id"],analysis_id="bridge")\nawait admit_measurement(analysis_id="bridge")'
  return ModelResponse(parts=[ToolCallPart("run_code",{"code":code},tool_call_id="bridge")])
 with system.agents.researcher.override(model=scripted(respond)):
  response=system.agents.researcher.run_sync("bounded file bridge",deps=ResearcherDeps(runtime=runtime,block_id=block.block_id))
 assert len(store.records(kind=RecordKind.EVIDENCE,block_id=block.block_id))==1, response.all_messages()
 assert len(store.records(kind=RecordKind.SCIENTIFIC_ARTIFACT,block_id=block.block_id))==1
 presentation=ResearchApplication(store).reconstruction(block.block_id)
 assert presentation.scientific_artifacts[0]["content_bytes_omitted"] is True
 assert "content_base64" not in presentation.scientific_artifacts[0]
 assert "content_base64" in reconstruct_block(store,block.block_id).scientific_artifacts[0]
 assert reconstruct_block(store,block.block_id).unresolved_source_refs==()
 # Access and byte limits are transport failures, never negative scientific results.
 denied=GdcPublicSource(httpx.MockTransport(lambda req:httpx.Response(200,json={"data":{"access":"controlled"}})))
 with pytest.raises(ValueError,match="explicitly open"):asyncio.run(denied.acquire_file(file_id,"owner","tsv"))
 bounded=GdcPublicSource(httpx.MockTransport(transport),max_download_bytes=10)
 with pytest.raises(ValueError,match="byte budget"):asyncio.run(bounded.acquire_file(file_id,"owner","tsv"))
 store.close()


def test_workspace_retention_exports_before_cleanup_and_preserves_active_or_unresolved(tmp_path,monkeypatch):
 from datetime import timedelta
 from src.persistence.retention import cleanup_workspaces
 store=SqliteResearchStore(tmp_path/"retention.sqlite3");repo=ResearchRepository(store);manager=BlockManager()
 workspace=tmp_path/"workspaces";workspace.mkdir()
 def make(status="failed",unresolved=False):
  block=manager.create("retention","archive",ResourceAllocation(seconds=60,handoff_reserve_seconds=5))
  directory=workspace/block.block_id;directory.mkdir();(directory/"method.py").write_bytes(b"print('retained')\n")
  if status=="active":repo.record_block(block)
  else:
   terminal=block.model_copy(update={"status":BlockStatus.FAILED,"termination_reason":"fixture_failed"})
   repo.record_terminal(terminal,build_dossier(terminal,(),None,"fixture_failed"))
  if unresolved:
   from src.science.models import MeasuredResult
   repo.record_measurement(MeasuredResult(analysis_id="lost",values={"n":1},origin="source",source_refs=("missing-acquisition",),provenance=("legacy",),input_sha256="0"*64),block.block_id)
  return block,directory
 closed,closed_dir=make();active,active_dir=make("active");lost,lost_dir=make(unresolved=True)
 peer=tmp_path/"peer";peer.mkdir();(peer/"keep").write_text("peer")
 future=datetime.now(UTC)+timedelta(days=8)
 before=store.count()
 results=cleanup_workspaces(repo,workspace,now=future)
 assert len(results)==1 and results[0]["status"]=="removed"
 assert not closed_dir.exists() and active_dir.exists() and lost_dir.exists() and (peer/"keep").exists()
 archive=store.latest(RecordKind.WORKSPACE_ARCHIVE,block_id=closed.block_id)
 retained_id=archive.payload["files"][0]["artifact_id"]
 assert repo.resolve_scientific_artifact(closed.block_id,retained_id).bytes()==b"print('retained')\n"
 broken,broken_dir=make()
 original=repo.record_scientific_artifact
 monkeypatch.setattr(repo,"record_scientific_artifact",lambda artifact:(_ for _ in ()).throw(OSError("export failed")))
 failed=cleanup_workspaces(repo,workspace,now=future)
 assert failed[0]["status"]=="skipped" and broken_dir.exists()
 monkeypatch.setattr(repo,"record_scientific_artifact",original)
 assert cleanup_workspaces(repo,workspace,now=future,max_archive_bytes=1)[0]["status"]=="skipped" and broken_dir.exists()
 assert cleanup_workspaces(repo,workspace,now=future,excluded_block_ids=(broken.block_id,))==()
 escaped,escaped_dir=make()
 import os,subprocess
 link=escaped_dir/"peer-link"
 if os.name=="nt":
  created=subprocess.run(["cmd","/c","mklink","/J",str(link),str(peer)],capture_output=True).returncode==0
 else:
  link.symlink_to(peer,target_is_directory=True);created=True
 if created:
  skipped=cleanup_workspaces(repo,workspace,now=future,excluded_block_ids=(broken.block_id,))
  assert skipped[0]["status"]=="skipped" and escaped_dir.exists() and (peer/"keep").read_text()=="peer"

 store.close();store=SqliteResearchStore(tmp_path/"retention.sqlite3");repo=ResearchRepository(store)
 assert repo.resolve_scientific_artifact(closed.block_id,retained_id).bytes()==b"print('retained')\n"
 assert len(store.records(kind=RecordKind.WORKSPACE_CLEANUP))==1
 assert store.count()>before and store.latest(RecordKind.DOSSIER,block_id=closed.block_id)
 store.close()


@pytest.mark.parametrize("truncated", [False, True])
def test_owned_launch_keeps_director_responsive_during_blocking_jev(tmp_path, truncated):
    """Launch and inspection stay responsive; blocking transport cannot own SQLite."""
    import asyncio
    from pydantic_ai.exceptions import UsageLimitExceeded
    from src.runtime.cycle import run_cycle_async

    started = threading.Event()
    release = threading.Event()
    owner_thread = threading.get_ident()
    calls = 0
    researcher_calls = 0
    system = cycle_system()
    repository = ResearchRepository(SqliteResearchStore(tmp_path / "async.sqlite3"))

    class PendingJev(DeterministicJevClient):
        def evaluate(self, payload, questions):
            assert threading.get_ident() != owner_thread
            started.set()
            if not release.wait(3):
                raise RuntimeError("Director could not run during Jev transport")
            return super().evaluate(payload, questions)

    system.runtime.jev = PendingJev()

    async def director(messages, info):
        nonlocal calls
        calls += 1
        if calls == 1:
            code = ('block = await allocate_block(objective="responsive investigation", why_now="test", seconds=60)\n'
                    'handle = await launch_researcher(block_id=block["block_id"])\n'
                    'assert handle["status"] == "active"\n'
                    'try:\n    await launch_researcher(block_id=block["block_id"])\n'
                    'except Exception:\n    pass\n'
                    'resources = await inspect_director_resources()\nresources')
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": code}, tool_call_id="start")])
        assert await asyncio.wait_for(asyncio.to_thread(started.wait, 2), 2.5)
        assert not system.runtime.active_research.task.done()
        assert repository.store.latest(RecordKind.LEDGER_EVENT) is not None
        release.set()
        if truncated:
            raise UsageLimitExceeded("Director ended independently")
        return ModelResponse(parts=[TextPart("bounded planning completed")])

    async def researcher(messages, info):
        nonlocal researcher_calls
        researcher_calls += 1
        if researcher_calls == 1:
            return ModelResponse(parts=[ToolCallPart("run_code", {"code":
                'await evaluate_candidate(candidate_id="c", candidate_summary="public association")'}, tool_call_id="jev")])
        return ModelResponse(parts=[TextPart("investigation returned")])

    async def run():
        with system.agents.director.override(model=scripted(director)), system.agents.researcher.override(model=scripted(researcher)):
            return await run_cycle_async(system, "direction", repository=repository)

    try:
        result = asyncio.run(run())
        assert result.status.value == ("incomplete" if truncated else "complete")
        block_id = result.block_ids[0]
        history = system.runtime.manager.ledger(block_id).history()
        assert sum(e.event_type == "ResearcherRunStarted" for e in history) == 1
        assert sum(e.event_type == "ResearcherRunCompleted" for e in history) == 1
        assert len(repository.store.records(kind=RecordKind.DOSSIER, block_id=block_id)) == 1
        assert len(repository.store.records(kind=RecordKind.CYCLE)) == 1
        assert reconstruct_block(repository.store, block_id).complete
    finally:
        release.set()
        repository.store.close()


@pytest.mark.parametrize("terminal", ["returned", "failed", "cancelled"])
def test_heavy_work_drains_and_preserves_one_lease_until_child_returns(terminal):
    import asyncio
    from src.runtime.resources import ResourceBusy

    system = cycle_system()
    runtime = system.runtime
    repository = ResearchRepository(SqliteResearchStore())
    runtime.repository = repository
    block = runtime.manager.allocate("bounded work", "test", 60)
    repository.record_block(block)
    server = create_server(ResearchApplication(repository.store), port=0) if terminal == "returned" else None
    api_thread = threading.Thread(target=server.serve_forever, daemon=True) if server else None
    if api_thread:
        api_thread.start()
    started = threading.Event()
    release = threading.Event()

    def compute():
        started.set()
        if not release.wait(3):
            raise RuntimeError("child was not drained")
        if terminal == "failed":
            raise ValueError("scientific operation failed")
        return 7

    async def run():
        task = asyncio.create_task(runtime.heavy_operation(block.block_id, compute))
        assert await asyncio.to_thread(started.wait, 2)
        if terminal == "cancelled":
            task.cancel()
            await asyncio.sleep(0)
        with pytest.raises(ResourceBusy) as busy:
            async with runtime.service_resources.heavy("director"):
                pytest.fail("Director stole the active science lease")
        assert busy.value.directive["scientific_negative"] is False
        assert not task.done()
        if server:
            def read_api():
                address = f"http://127.0.0.1:{server.server_address[1]}/api/blocks/{block.block_id}"
                with urlopen(address, timeout=2) as response:
                    return json.loads(response.read())
            view = await asyncio.wait_for(asyncio.to_thread(read_api), 2.5)
            assert view["block"]["status"] == "active"
            assert not view["complete"] and view["dossier"] is None
            assert any(e["event_type"] == "HeavyExecutionLease" for e in view["ledger"])
            assert not task.done()
        release.set()
        if terminal == "failed":
            with pytest.raises(ValueError, match="scientific operation failed"):
                await task
        else:
            assert await task == 7
        assert runtime.service_resources.heavy_owner is None
        async with runtime.service_resources.heavy("director"):
            assert runtime.service_resources.heavy_owner == "director"

    try:
        asyncio.run(run())
        events = repository.store.records(kind=RecordKind.LEDGER_EVENT, block_id=block.block_id)
        assert sum(e.payload["event_type"] == "HeavyExecutionLease" for e in events) == 1
        assert sum(e.payload["event_type"] == "HeavyExecutionReleased" for e in events) == 1
        assert runtime.service_resources.receipts[0]["status"] == "released"
    finally:
        release.set()
        if server:
            server.shutdown()
            server.server_close()
            api_thread.join(timeout=2)
        repository.store.close()


def test_cycle_shutdown_drains_active_research_and_persists_before_reopen(tmp_path):
    import asyncio
    from src.runtime.cycle import run_cycle_async

    system = cycle_system()
    database = tmp_path / "shutdown.sqlite3"
    repo = ResearchRepository(SqliteResearchStore(database))
    started = asyncio.Event()
    release = asyncio.Event()
    calls = 0

    async def director(messages, info):
        nonlocal calls
        calls += 1
        if calls == 1:
            return ModelResponse(parts=[ToolCallPart("run_code", {"code":
                'b = await allocate_block(objective="shutdown", why_now="test", seconds=60)\n'
                'await launch_researcher(block_id=b["block_id"])'}, tool_call_id="start")])
        await release.wait()
        return ModelResponse(parts=[TextPart("Director finished")])

    async def researcher(messages, info):
        started.set()
        await release.wait()
        return ModelResponse(parts=[TextPart("Researcher finished")])

    async def run():
        with system.agents.director.override(model=scripted(director)), system.agents.researcher.override(model=scripted(researcher)):
            task = asyncio.create_task(run_cycle_async(system, "direction", repository=repo))
            await asyncio.wait_for(started.wait(), 2)
            task.cancel()
            await asyncio.sleep(0)
            assert not task.done()
            assert not system.runtime.active_research.task.done()
            release.set()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert system.runtime.active_research.task.done()

    asyncio.run(run())
    block_id = system.runtime.manager.blocks()[0].block_id
    assert len(repo.store.records(kind=RecordKind.DOSSIER, block_id=block_id)) == 1
    assert len(repo.store.records(kind=RecordKind.CYCLE)) == 1
    repo.store.close()
    reopened = ResearchRepository(SqliteResearchStore(database))
    try:
        before = reopened.store.count()
        assert recover_interrupted_blocks(reopened) == ()
        assert reopened.store.count() == before
        view = reconstruct_block(reopened.store, block_id)
        assert view.dossier is not None
        assert view.run_outcome.value == "completed"
    finally:
        reopened.store.close()


@pytest.mark.parametrize("researcher_fails", [False, True])
def test_terminal_event_yields_pending_director_without_losing_bundle(researcher_fails):
    import asyncio
    from src.runtime.cycle import run_cycle_async

    system = cycle_system()
    repo = ResearchRepository(SqliteResearchStore())
    director_pending = asyncio.Event()
    never = asyncio.Event()
    drained = []
    calls = 0

    async def director(messages, info):
        nonlocal calls
        calls += 1
        if calls == 1:
            return ModelResponse(parts=[ToolCallPart("run_code", {"code":
                'b = await allocate_block(objective="terminal visibility", why_now="test", seconds=60)\n'
                'await launch_researcher(block_id=b["block_id"])'}, tool_call_id="start")])
        director_pending.set()
        try:
            await never.wait()
        finally:
            drained.append(True)
        return ModelResponse(parts=[TextPart("late Director result")])

    async def researcher(messages, info):
        await director_pending.wait()
        if researcher_fails:
            raise ValueError("investigation failed")
        return ModelResponse(parts=[TextPart("investigation returned")])

    async def run():
        with system.agents.director.override(model=scripted(director)), system.agents.researcher.override(model=scripted(researcher)):
            if researcher_fails:
                with pytest.raises(ValueError, match="investigation failed"):
                    await asyncio.wait_for(run_cycle_async(system, "direction", repository=repo), 2)
            else:
                result = await asyncio.wait_for(run_cycle_async(system, "direction", repository=repo), 2)
                assert result.status.value == "complete"
                assert result.director_outcome.value == "interrupted"
                assert result.director_error_type == "ResearcherTerminalEvent"

    try:
        asyncio.run(run())
        assert calls == 2 and drained == [True]
        assert len(repo.store.records(kind=RecordKind.DOSSIER)) == 1
        assert len(repo.store.records(kind=RecordKind.CYCLE)) == 1
        active = system.runtime.active_research
        view = reconstruct_block(repo.store, active.block_id)
        assert view.run_outcome.value == ("failed" if researcher_fails else "completed")
        assert view.block["status"] == ("failed" if researcher_fails else "complete")
        assert active.finished.is_set() and active.task.done()
        assert any(e["event_type"] == "DirectorYieldedForResearchEvent" for e in view.ledger)
    finally:
        repo.store.close()


@pytest.mark.parametrize("first_fails", [False, True])
def test_service_completion_reviews_delta_and_allocates_again_without_deadline_sleep(tmp_path, monkeypatch, first_fails):
    import asyncio
    from contextlib import ExitStack
    from src.autonomous import AutonomousService
    from src.memory.models import MemoryReference
    from src.provenance import content_hash

    service = AutonomousService(ROOT, tmp_path / "events.sqlite3")
    systems = [cycle_system(), cycle_system()]
    reviews = []
    allocations = []
    composed = 0

    async def director(messages, info):
        prompts = " ".join(str(p.content) for m in messages for p in m.parts if hasattr(p, "content"))
        if "Researcher terminal event" in prompts:
            assert "BlockDelta" in prompts and "allocated_seconds" in prompts
            assert "hypotheses" in prompts and "uncertainties" in prompts
            reviews.append(prompts)
            return ModelResponse(parts=[TextPart("Review retained the uncertainty and proposes a next investigation")])
        if not any(isinstance(m, ModelResponse) for m in messages):
            allocations.append(True)
            return ModelResponse(parts=[ToolCallPart("run_code", {"code":
                'b = await allocate_block(objective="continuous investigation", why_now="test")\n'
                'await launch_researcher(block_id=b["block_id"])'}, tool_call_id="allocate")])
        return ModelResponse(parts=[TextPart("Independent global work finished; yield")])

    async def researcher(messages, info):
        if not any(isinstance(m, ModelResponse) for m in messages):
            return ModelResponse(parts=[ToolCallPart("run_code", {"code":
                'await generate_hypotheses(finding="synthetic association requiring replication")'}, tool_call_id="hypothesis")])
        if first_fails and composed == 1:
            raise ValueError("recoverable local investigation failure")
        return ModelResponse(parts=[TextPart("Researcher returned early")])

    def compose(*args, **kwargs):
        nonlocal composed
        if composed == 2:
            raise asyncio.CancelledError
        system = systems[composed]
        composed += 1
        if kwargs.get("director") is not None:
            from src.runtime.pydantic_ai.agents import OncoJevAgents
            system = ConfiguredSystem(OncoJevAgents(kwargs["director"], system.agents.researcher,
                system.agents.fresh_researcher), system.runtime, system.mode)
            systems[composed-1] = system
        system.runtime.service_resources = kwargs["resources"]
        return system

    monkeypatch.setattr("src.autonomous.build_system", compose)
    try:
        with ExitStack() as stack:
            for system in systems:
                stack.enter_context(system.agents.director.override(model=scripted(director)))
                stack.enter_context(system.agents.researcher.override(model=scripted(researcher)))
            async def run():
                with pytest.raises(asyncio.CancelledError):
                    await asyncio.wait_for(service._serve_cycles("direction", 3600), 10)
            service._loop_runner.run(run())
        assert len(allocations) == len(reviews) == 2
        assert systems[0].agents.director is systems[1].agents.director
        cycles = service.store.records(kind=RecordKind.CYCLE)
        assert len(cycles) == 2
        assert [c.payload["status"] for c in cycles] == (["failed", "complete"] if first_fails else ["complete", "complete"])
        assert len(service.store.records(kind=RecordKind.BLOCK_DELTA)) == 2
        for system in systems:
            active = system.runtime.active_research
            delta = active.delta
            assert delta.resources["allocated_seconds"] == 900
            assert delta.resources["unused_allowance_seconds"] > 890
            assert delta.resources["workspace_peak_bytes"] is None
            assert not delta.references.get("scientific_negatives")
            assert not delta.references.get("resolutions")
            assert delta.references["hypotheses"] and delta.references["uncertainties"]
            for values in delta.references.values():
                for reference in values:
                    assert isinstance(reference, MemoryReference)
                    record = service.store.record_at(reference.seq)
                    assert record.block_id == active.block_id
                    assert content_hash(record.payload) == reference.sha256
            events = system.runtime.manager.ledger(active.block_id).history()
            assert sum(e.event_type == "PostBlockReviewed" for e in events) == 1
            view = service.application.reconstruction(active.block_id)
            assert len(view.block_deltas) == 1 and view.service_events
        # A repeated notification cannot create another model review.
        service._loop_runner.run(service._post_block_review("direction"))
        assert len(reviews) == 2
    finally:
        service.close()


@pytest.mark.parametrize("notification", ["material", "scheduled"])
@pytest.mark.parametrize("global_failure", [False, True])
def test_research_event_turn_is_bounded_and_never_cancels_the_researcher(notification, global_failure):
    import asyncio
    from pydantic_ai.exceptions import UsageLimitExceeded
    from src.runtime.cycle import run_cycle_async

    system = cycle_system()
    runtime = system.runtime
    runtime.director_review_interval_seconds = 0.03
    runtime.director_event_turn_limit = 1
    repo = ResearchRepository(SqliteResearchStore())
    yielded = asyncio.Event()
    release = asyncio.Event()
    observed = []
    director_calls = 0
    researcher_calls = 0

    async def director(messages, info):
        nonlocal director_calls
        director_calls += 1
        prompt = " ".join(str(p.content) for m in messages for p in m.parts if hasattr(p, "content"))
        if "Persisted research event permits" in prompt:
            expected = "ScopeEscalationRequested" if notification == "material" else "ScheduledProgramReview"
            assert expected in prompt
            assert not runtime.active_research.finished.is_set()
            observed.append(expected)
            release.set()
            if global_failure:
                raise UsageLimitExceeded("bounded global turn exhausted")
            return ModelResponse(parts=[TextPart("useful independent comparison; yield")])
        if director_calls == 1:
            return ModelResponse(parts=[ToolCallPart("run_code", {"code":
                'b = await allocate_block(objective="event supervision", why_now="test", seconds=60)\n'
                'await launch_researcher(block_id=b["block_id"])'}, tool_call_id="allocate")])
        yielded.set()
        return ModelResponse(parts=[TextPart("initial work ended; wait for an event")])

    async def researcher(messages, info):
        nonlocal researcher_calls
        researcher_calls += 1
        await yielded.wait()
        if notification == "material" and researcher_calls == 1:
            return ModelResponse(parts=[ToolCallPart("run_code", {"code":
                'await request_scope_escalation(proposed_test="replicate in another cohort", rationale="outside current scope")'}, tool_call_id="material")])
        await release.wait()
        return ModelResponse(parts=[TextPart("Researcher completed independently")])

    async def run():
        with system.agents.director.override(model=scripted(director)), system.agents.researcher.override(model=scripted(researcher)):
            return await asyncio.wait_for(run_cycle_async(system, "direction", repository=repo), 2)

    try:
        result = asyncio.run(run())
        assert result.status.value == "complete"
        assert len(observed) == 1 and director_calls == 3
        active = runtime.active_research
        events = runtime.manager.ledger(active.block_id).history()
        starts = [e for e in events if e.event_type == "DirectorEventTurnStarted"]
        terminals = [e for e in events if e.event_type in {"DirectorEventTurnCompleted", "DirectorEventTurnYielded", "DirectorEventTurnFailed"}]
        assert len(starts) == len(terminals) == 1
        assert starts[0].payload["event_id"] == terminals[0].payload["event_id"]
        if notification == "material":
            record = repo.store.record_at(starts[0].payload["ledger_seq"])
            assert record.kind is RecordKind.LEDGER_EVENT
            assert record.payload["event_type"] == "ScopeEscalationRequested"
        if global_failure:
            assert terminals[0].event_type == "DirectorEventTurnFailed"
            assert terminals[0].payload["error_type"] == "UsageLimitExceeded"
        assert sum(e.event_type == "ResearcherRunCompleted" for e in events) == 1
        assert not any(e.event_type == "ResearcherRunFailed" for e in events)
        assert runtime._counts["director:event_turns"] == 1
        assert runtime.director_turn_seconds > 0 and runtime.director_idle_seconds >= 0
        assert runtime.director_context is None
        assert active.task.done()
    finally:
        release.set()
        repo.store.close()


@pytest.mark.parametrize("outage", [False, True])
def test_external_discovery_tool_retains_query_identity_and_has_no_execution_authority(tmp_path, outage):
    import asyncio
    import httpx
    from src.oncolab.discovery import ExternalDiscovery
    from src.runtime.pydantic_ai.contracts import DirectorDeps
    from src.runtime.pydantic_ai.factory import bind_repository
    requests = []
    row = {"biotoolsID": "method", "name": "Method", "description": "Reference operation with count inputs",
        "license": "GPL-3.0", "function": [{"operation": [{"uri": "http://edamontology.org/operation_1", "term": "Testing"}],
            "input": [{"data": {"uri": "http://edamontology.org/data_1", "term": "Counts"}}]}],
        "link": [{"url": "https://github.com/example/method", "type": ["Repository"]}]}
    def transport(request):
        requests.append(request)
        if outage:return httpx.Response(503, json={"error": "registry temporarily unavailable"})
        return httpx.Response(200, json={"list": [row], "count": 2, "next": "?page=2"})
    system = cycle_system()
    runtime = system.runtime
    path = tmp_path / 'external.sqlite3'
    store = SqliteResearchStore(path)
    bind_repository(runtime, ResearchRepository(store))
    revision = runtime.institution.pin().oncolab_registry_revision
    runtime.external_discovery = ExternalDiscovery(httpx.MockTransport(transport))
    results = []
    async def model(messages, info):
        if not any(isinstance(m, ModelResponse) for m in messages):
            return ModelResponse(parts=[ToolCallPart('run_code', {'code':
                'await search_external_capabilities(source="bio.tools", need="count testing", filters={"operationID":"operation_1"}, limit=1)'}, tool_call_id='external')])
        results.extend(str(p.content) for m in messages for p in m.parts if hasattr(p, 'content'))
        return ModelResponse(parts=[TextPart('registry inspected')])
    with system.agents.director.override(model=scripted(model)):
        asyncio.run(system.agents.director.run('inspect a missing method', deps=DirectorDeps(runtime)))
    saved = store.records(kind=RecordKind.EXTERNAL_LOOKUP)
    assert len(saved) == 1
    assert requests[0].url.params['operationID'] == '"operation_1"'
    if outage:
        assert saved[0].payload['status'] == 'failed' and saved[0].payload['error_type'] == 'HTTPStatusError'
    else:
        payload = saved[0].payload
        assert payload['cards'][0]['external_id'] == 'method'
        assert payload['cards'][0]['inputs'][0]['data']['term'] == 'Counts'
        assert payload['raw_json'] and payload['response_sha256']
        assert all('raw_json' not in result for result in results)
        assert any('Counts' in result and 'metadata_only' in result for result in results), results
        with pytest.raises(ValueError, match='continuation'):
            asyncio.run(runtime.external_discovery.search('bio.tools','changed need',continuation=payload['continuation'],limit=1))
        with pytest.raises(ValueError, match='catalogue'):
            runtime.index_receipt('director','execute',selected_id='bio.tools:method')
    assert runtime.institution.pin().oncolab_registry_revision == revision
    assert not store.records(kind=RecordKind.EVIDENCE)
    store.close()
    reopened = SqliteResearchStore(path)
    assert reopened.records(kind=RecordKind.EXTERNAL_LOOKUP)[0].payload == saved[0].payload
    reopened.close()


@pytest.mark.parametrize('requires_code', [False, True])
def test_governance_rejects_unqualified_use_without_revision_or_evidence_mutation(tmp_path, requires_code):
    from src.oncolab.governance import CapabilityProposal, propose, review_pending
    from src.oncolab.models import OncoLabAvailability, OncoLabValidationState
    from src.oncolab.execution import ExecutionRoute
    from src.memory.service import reference
    from src.runtime.pydantic_ai.factory import bind_repository
    from src.provenance import content_hash
    system=cycle_system();runtime=system.runtime
    store=SqliteResearchStore(tmp_path/'governance.sqlite3')
    bind_repository(runtime,ResearchRepository(store))
    block=runtime.manager.allocate('descriptive attempt','qualification is separate')
    acquisition=AcquisitionRecord(source='fixture',request={},records=({'id':'participant'},),provenance=('controlled-source',))
    runtime.repository.record_acquisition(block.block_id,acquisition)
    result=runtime.science.measure_acquisition(acquisition,'summary')
    measured=runtime.repository.record_measurement(result,block.block_id)
    evidence=runtime.repository.record_evidence(admit_scientific_evidence(result),block.block_id)
    scope={'design':'response slice','external_id':'method'}
    descriptor=runtime.index_for(block.block_id).describe('science.acquisition-summary').model_copy(update={
        'capability_id':'proposed.method','availability':OncoLabAvailability.REUSABLE,
        'validation_state':OncoLabValidationState.REUSABLE,'version':'a'*40})
    parent=runtime.institution.pin().oncolab_registry_revision
    proposal=CapabilityProposal(capability_id=descriptor.capability_id,transition='promotion',parent=parent,
        descriptor=descriptor,routes=(ExecutionRoute(tool='run_reusable_method',candidate_id='unknown',scope_sha256=content_hash(scope)),),
        scope=scope,references=(reference(measured),reference(evidence)),requires_code_change=requires_code,rationale='one observed analysis')
    propose(runtime.institution,proposal)
    assert runtime.institution.pin().oncolab_registry_revision==parent
    decisions=review_pending(runtime.institution)
    assert len(decisions)==1 and decisions[0]['status']=='rejected'
    assert 'missing:environment_qualification' in decisions[0]['reasons']
    assert 'missing:deployment_verification' in decisions[0]['reasons']
    assert 'missing_repeated_validated_use_history' in decisions[0]['reasons']
    assert not review_pending(runtime.institution)
    assert runtime.institution.pin().oncolab_registry_revision==parent
    assert store.records(kind=RecordKind.EVIDENCE)==(evidence,)
    assert bool(store.records(kind=RecordKind.ENGINEERING_PROPOSAL))==requires_code
    store.close()
