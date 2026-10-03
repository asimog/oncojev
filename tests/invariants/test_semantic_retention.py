import asyncio
from types import SimpleNamespace

import pytest
from src.block.manager import BlockManager
from src.block.models import CycleStatus
from src.director.models import ResourceAllocation
from src.jev.client import DeterministicJevClient
from src.memory.service import ResearchMemory
from src.persistence.records import RecordKind
from src.persistence.repository import ResearchRepository
from src.persistence.store import SqliteResearchStore
from src.reasoner.service import DeterministicReasoner
from src.runtime.pydantic_ai.contracts import HarnessRuntime, ResearcherDeps
from src.runtime.pydantic_ai.search_tools import register_local_semantic_tools
from src.science.execution import ScienceExecutor


class ToolCapture:
    def __init__(self): self.tools = {}
    def tool(self, function):
        self.tools[function.__name__] = function
        return function


def runtime_case(path):
    store = SqliteResearchStore(path)
    repository = ResearchRepository(store)
    manager = BlockManager()
    block = manager.create('Compare lung hypotheses', 'retention test', ResourceAllocation(seconds=300))
    runtime = HarnessRuntime(manager=manager, jev=DeterministicJevClient(), science=ScienceExecutor(),
        reasoner=DeterministicReasoner(), repository=repository, max_jev_calls=20, max_reasoner_calls=1)
    repository.record_block(block)
    runtime.persist_state(runtime.research_state.start(block.block_id, block.objective))
    agent = ToolCapture(); register_local_semantic_tools(agent)
    return runtime, store, agent.tools, SimpleNamespace(deps=ResearcherDeps(runtime, block.block_id))


def test_direct_hypothesis_survives_semantic_failure_and_memory_reopen(tmp_path):
    path = tmp_path / 'hypotheses.sqlite3'
    runtime, store, tools, ctx = runtime_case(path)
    class FailedJev:
        def evaluate(self, state, questions): raise RuntimeError('provider unavailable')
    runtime.jev = FailedJev()
    with pytest.raises(RuntimeError):
        asyncio.run(tools['assess_hypothesis'](ctx, 'X relates to Y', 'paired correlation'))
    state = runtime.research_state.get(ctx.deps.block_id)
    assert len([f for f in state.candidates if f.kind == 'hypothesis']) == 1
    runtime.repository.record_cycle('retention', 'deterministic', 'lung context', (ctx.deps.block_id,),
        status=CycleStatus.INCOMPLETE, error_type='ExplicitTestHandoff')
    ResearchMemory(store).backfill(); store.close()
    store = SqliteResearchStore(path)
    memory = ResearchMemory(store)
    hypothesis = memory.items('hypotheses', 'X relates')[0]
    assert hypothesis['details']['proposed_test'] == 'paired correlation'
    context = memory.context('X relates').model_dump(mode='json')
    assert context['digests'][0]['hypotheses'][0]['details']['proposed_test'] == 'paired correlation'
    assert not store.records(kind=RecordKind.EVIDENCE)
    store.close()


def test_hypothesis_annotations_append_lineage_and_never_resolve_science(tmp_path):
    runtime, store, tools, ctx = runtime_case(tmp_path / 'annotations.sqlite3')
    runtime.enable_jev = False
    first = asyncio.run(tools['assess_hypothesis'](ctx, 'X relates to Y', 'paired correlation'))
    revised = asyncio.run(tools['assess_hypothesis'](ctx, 'Common cause explains X and Y', 'adjusted association'))
    before = store.records(kind=RecordKind.STATE_REVISION)
    for status, related in [('challenged', None), ('reopened', None), ('revised', revised['identity']), ('superseded', revised['identity'])]:
        result = asyncio.run(tools['annotate_hypothesis'](ctx, first['identity'], status, 'Retain the original competing explanation', related))
        assert result['scientific_status'] == 'unknown'
    with pytest.raises(ValueError):
        asyncio.run(tools['annotate_hypothesis'](ctx, first['identity'], 'superseded', 'Self replacement', first['identity']))
    with pytest.raises(ValueError):
        asyncio.run(tools['annotate_hypothesis'](ctx, 'invented', 'reopened', 'No lineage'))
    assert store.records(kind=RecordKind.STATE_REVISION)[:len(before)] == before
    runtime.repository.record_cycle('annotations', 'deterministic', 'lung hypotheses', (ctx.deps.block_id,), status=CycleStatus.INCOMPLETE)
    memory = ResearchMemory(store); memory.backfill()
    context = memory.context('lung').model_dump(mode='json')
    transitions = [item for digest in context['digests'] for item in digest['candidates'] if item['epistemic_status'] == 'hypothesis_transition']
    assert {item['details']['status'] for item in transitions} == {'challenged', 'reopened', 'revised', 'superseded'}
    assert len(memory.items('hypotheses')) == 2
    assert not store.records(kind=RecordKind.EVIDENCE)
    store.close()


def test_search_metrics_report_missed_alternatives_and_unknowns_without_labels_in_consumer():
    from src.evals.reference import search_metrics, summarize_search_rows
    labels = {'useful_ids': ['low-overlap'], 'fit_by_id': {'low-overlap': True}, 'low_overlap_ids': ['low-overlap']}
    observed = {'retrieved_ids': ['low-overlap', 'other'], 'retained_ids': ['low-overlap', 'other'],
        'selectable_ids': ['other'], 'fit_by_id': {'low-overlap': None}, 'unknown_scientific_status': True}
    metrics = search_metrics(observed, labels)
    assert metrics['useful_candidate_recall'] == 1 and metrics['selectable_useful_recall'] == 0
    assert metrics['fit_accuracy'] is None and metrics['alternative_preservation'] == 1
    rows = [{'case_id': 'paired', 'condition': condition, 'memory_alternative_limit': 3, 'repetition': 0,
        'observations': {}, 'search_metrics': {**metrics, 'selectable_useful_recall': score}}
        for condition, score in [('science_only', 1), ('science_jev', 0)]]
    assert summarize_search_rows(rows)['marginal_jev_deltas'][0]['metrics']['selectable_useful_recall'] == -1


def test_representation_omissions_keep_reproducible_source_and_candidate_identity():
    from src.sources.models import AcquisitionRecord
    from src.sources.representation import RepresentationNeed, representation_alternatives
    records = [AcquisitionRecord(source='fixture', request={'i': i}, records=({'x': i},), provenance=('fixture',)) for i in range(3)]
    result = representation_alternatives(records, [], RepresentationNeed(estimand='row description', representation='metadata'), limit=1)
    assert result['omitted_candidates'] == 2
    assert result['omitted_candidate_ids'] == [record.acquisition_id for record in records[1:]]
    assert result['acquisition_ids'] == [record.acquisition_id for record in records]


def test_reasoner_batch_is_retained_before_first_failed_semantic_call(tmp_path):
    from src.reasoner.models import Hypothesis, ReasonerOutput
    from src.runtime.pydantic_ai.agents import create_agents
    runtime, store, tools, ctx = runtime_case(tmp_path / 'batch.sqlite3')
    class Proposals:
        async def generate(self, objective, finding):
            return ReasonerOutput(interpretation='Competing explanations', uncertainty='Unknown causal interpretation',
                hypotheses=tuple(Hypothesis(hypothesis_id=f'reasoner-{i}', statement=f'Explanation {i}',
                    within_scope=True, proposed_test=f'Distinct test {i}') for i in range(7)))
    class FailedJev:
        def evaluate(self, state, questions):
            assert len([f for f in runtime.research_state.get(ctx.deps.block_id).candidates if f.kind == 'hypothesis']) == 7
            raise RuntimeError('provider unavailable')
    runtime.reasoner = Proposals(); runtime.jev = FailedJev()
    agent = create_agents('test', 'test', enable_coder=False).researcher
    asyncio.run(agent._function_toolset.tools['generate_hypotheses'].function(ctx, 'source finding'))
    assert len([f for f in runtime.research_state.get(ctx.deps.block_id).candidates if f.kind == 'hypothesis']) == 7
    assert not store.records(kind=RecordKind.EVIDENCE)
    store.close()


def test_method_byte_omissions_retain_full_durable_alternatives(tmp_path, monkeypatch):
    import src.oncolab.methods as methods
    from src.sources.models import AcquisitionRecord
    original = methods.method_alternative
    def expanded(*args, **kwargs):
        return {**original(*args, **kwargs), 'contract_context': 'x' * 30000}
    monkeypatch.setattr(methods, 'method_alternative', expanded)
    runtime, store, tools, ctx = runtime_case(tmp_path / 'method-omissions.sqlite3')
    acquisition = AcquisitionRecord(source='fixture', request={}, records=({'id': 'a', 'x': 1, 'y': 2}, {'id': 'b', 'x': 2, 'y': 3}), provenance=('fixture',))
    runtime.retain_acquisition(ctx.deps.block_id, acquisition)
    need = {'question': 'Do X and Y correlate?', 'estimand': 'correlation', 'population': 'retained rows', 'design': 'paired',
        'representation_need': {'estimand': 'correlation', 'representation': 'paired_data', 'entity_key': 'id',
            'fields': {'x': 'x', 'y': 'y'}, 'numeric_roles': ['x', 'y'], 'minimum_complete_rows': 2}}
    result = asyncio.run(tools['generate_method_candidates'](ctx, need, [acquisition.acquisition_id], limit=8))
    retained = store.latest(RecordKind.METHOD_CANDIDATES).payload
    assert result['omitted_candidates'] > 0 and retained['omitted_candidates'] == 0
    assert set(result['omitted_candidate_ids']) <= {candidate['capability_id'] for candidate in retained['candidates']}
    assert len(retained['candidates']) == len(result['candidates']) + result['omitted_candidates']
    store.close()


def test_source_trajectory_uses_owned_launch_and_reconstructs_outcome_linked_next_choice():
    from src.config.loader import load_models_config, load_runtime_config
    from src.config.models import RuntimeMode
    from src.evals.reference import ReferenceCase, evaluate_reference_cases, reference_consumer_adapter
    from src.evals.models import EvaluationCondition
    from src.runtime.pydantic_ai.agents import create_agents
    from src.sources.models import AcquisitionRecord
    from src.provenance import content_hash
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    record = AcquisitionRecord(source='fixture', origin='synthetic', request={'scope': 'generated contract'},
        records=tuple({'id': str(i), 'demographic': {'age_at_index': i+1, 'days_to_death': value}}
            for i, value in enumerate([1, 8, 2, 7, 3, 6, 4, 5])), provenance=('generated contract; not scientific evidence',))
    case = ReferenceCase(case_id='source-path-contract', split='tuning', domain='source_trajectory',
        public_inputs={'operation': 'source_trajectory', 'acquisition': record.model_dump(mode='json'),
            'source_replay_basis': {'payload_sha256': content_hash(record.model_dump(mode='json')), 'scope': 'synthetic contract'}},
        expected={'changed_next_objective': True}, reference_url='https://example.invalid', label_basis='generated contract')
    report = evaluate_reference_cases((case,), reference_consumer_adapter, models=load_models_config(root/'config/models.yaml'),
        policy=load_runtime_config(root/'config/runtime.yaml').model_copy(update={'mode': RuntimeMode.DETERMINISTIC}),
        environment={}, agents_factory=lambda: create_agents('test', 'test', enable_coder=False),
        conditions=(EvaluationCondition.SCIENCE_JEV,), memory_alternatives=(3,))
    row = report['rows'][0]; observed = row['observations']
    assert row['agreement'] is True, observed.get('adapter_error_detail')
    assert row['metrics']['completed_blocks'] == 2 and row['metrics']['dossiers'] == 2
    assert observed['source_measurement']['origin'] == 'synthetic' and row['metrics']['evidence'] == 0
    assert all(block['run_outcome'] == 'completed' and not block['unresolved_source_refs'] for block in observed['reconstruction'])
    assert all(record['payload']['payload']['candidate_id'] for record in observed['allocation_lineage'])
    assert observed['source_outcome'] == 'inconclusive' and len(observed['final_digest_ids']) > len(observed['initial_digest_ids'])


def test_historical_hypothesis_wording_does_not_suppress_independent_scope_comparison(tmp_path):
    from src.block.models import BlockStatus
    runtime, store, tools, ctx = runtime_case(tmp_path / 'replication-scope.sqlite3')
    first = asyncio.run(tools['assess_hypothesis'](ctx, 'X relates to Y', 'paired correlation'))
    runtime.manager.finalize(runtime.manager.block(ctx.deps.block_id), BlockStatus.INTERRUPTED, 'fixture handoff')
    runtime.repository.record_block(runtime.manager.block(ctx.deps.block_id))
    runtime.repository.record_cycle('retention', 'deterministic', 'lung', (ctx.deps.block_id,), status=CycleStatus.INCOMPLETE)
    ResearchMemory(store).backfill()
    second = runtime.manager.create('Same question in an independent lung cohort', 'scope comparison', ResourceAllocation(seconds=300))
    runtime.repository.record_block(second)
    runtime.persist_state(runtime.research_state.start(second.block_id, second.objective))
    result = asyncio.run(tools['assess_hypothesis'](SimpleNamespace(deps=ResearcherDeps(runtime, second.block_id)), 'X relates to Y', 'paired correlation'))
    assert result['identity'] == first['identity'] and not result['exact_duplicate'] and result['call_id'] != first['call_id']
    assert len([f for f in runtime.research_state.get(second.block_id).candidates if f.kind == 'hypothesis']) == 1
    assert not store.records(kind=RecordKind.EVIDENCE)
    store.close()
