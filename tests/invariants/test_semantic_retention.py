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
    def output_validator(self, function): return function
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


def test_need_before_acquisition_is_retained_and_does_not_grant_method_readiness(tmp_path):
    from src.oncolab.methods import ScientificNeed
    from src.runtime.pydantic_ai.search_tools import register_search_page
    from src.sources.models import AcquisitionRecord
    from src.memory.models import MemoryReference
    from src.provenance import content_hash
    runtime, store, tools, ctx = runtime_case(tmp_path / 'need-first.sqlite3')
    need = {'question': 'Which capabilities support a descriptive mean?', 'estimand': 'mean',
        'population': 'retained observations', 'design': 'descriptive',
        'required_information': ['finite numeric values', 'observation identity'],
        'entity_relationships': ['one value per observation'], 'measurement_requirements': ['same declared unit'],
        'constraints': ['public inputs only'], 'known_uncertainty': ['input availability unmeasured']}
    validated = ScientificNeed.model_validate(need)
    assert validated.representation_need is None
    captured = ToolCapture(); register_search_page(captured)
    page = asyncio.run(captured.tools['search_oncolab_page'](ctx, need=need))
    receipt = ResearchMemory(store).resolve(MemoryReference.model_validate(page['context_reference']))
    assert receipt['scientific_need'] == validated.model_dump(mode='json')
    assert receipt['need_sha256'] == content_hash(receipt['scientific_need'])
    assert page['cards']
    # Even owned numbers do not substitute for a declared representation contract.
    record = AcquisitionRecord(source='fixture', request={}, records=({'id': 'a', 'value': 1},),
                               provenance=('explicit contract fixture',), origin='synthetic')
    runtime.retain_acquisition(ctx.deps.block_id, record)
    result = asyncio.run(tools['generate_method_candidates'](ctx, need, [record.acquisition_id], limit=8))
    assert result['candidates'] and all(not c['input_ready'] for c in result['candidates'])
    assert all(c['scientific_suitability'] == 'unmeasured' for c in result['candidates'])
    assert result['representations'][0]['checks']['status'] == 'unbound'
    assert not store.records(kind=RecordKind.EVIDENCE)
    assert not store.records(kind=RecordKind.JEV_CALL)
    store.close()


def test_need_discovery_is_generic_across_capability_kinds_and_preserves_constraints(tmp_path):
    from src.oncolab.registry import OncoLabIndex
    from src.oncolab.models import OncoLabKind, OncoLabExecutionMode, OncoLabAvailability
    from src.runtime.pydantic_ai.search_tools import register_search_page
    from src.memory.models import MemoryReference
    runtime, store, _, ctx = runtime_case(tmp_path / 'generic-need.sqlite3')
    base = runtime.oncolab.describe('source.gdc')
    descriptors = [base.model_copy(update={'capability_id': identity, 'kind': kind,
        'name': 'Sensor measurement contract', 'purpose': 'Sensor measurement availability',
        'tags': ('sensor', 'measurement'), 'input_contract': 'Unknown until inspected',
        'output_contract': 'Measurement metadata', 'availability': OncoLabAvailability.KNOWN,
        'execution_mode': OncoLabExecutionMode.METADATA_ONLY,
        'provenance': ('explicit metadata contract fixture',)})
        for identity, kind in [('fixture.sensor-source', OncoLabKind.SOURCE),
                               ('fixture.sensor-transform', OncoLabKind.TRANSFORMATION)]]
    runtime.oncolab = OncoLabIndex(descriptors, routes={})
    agent = ToolCapture(); register_search_page(agent)
    need = {'question': 'Find sensor measurements', 'estimand': 'measurement', 'population': 'devices',
            'design': 'descriptive', 'constraints': ['units must be comparable'],
            'known_uncertainty': ['source availability unknown']}
    page = asyncio.run(agent.tools['search_oncolab_page'](ctx, need=need))
    assert {c['capability_id'] for c in page['cards']} == {d.capability_id for d in descriptors}
    saved = ResearchMemory(store).resolve(MemoryReference.model_validate(page['context_reference']))
    assert saved['scientific_need']['constraints'] == need['constraints']
    assert saved['scientific_need']['known_uncertainty'] == need['known_uncertainty']
    assert not store.records(kind=RecordKind.JEV_CALL)
    assert not store.records(kind=RecordKind.EVIDENCE)
    store.close()


def test_need_binding_retains_estimand_consistency_and_byte_bounds():
    from src.oncolab.methods import ScientificNeed
    need = {'question': 'Mean of retained values', 'estimand': 'mean', 'population': 'observations', 'design': 'descriptive'}
    with pytest.raises(ValueError, match='byte bound'):
        ScientificNeed.model_validate({**need, 'known_uncertainty': ['x' * 9000]})
    with pytest.raises(ValueError, match='share the declared estimand'):
        ScientificNeed.model_validate({**need, 'representation_need': {
            'estimand': 'correlation', 'representation': 'paired_data', 'entity_key': 'id',
            'fields': {'x': 'x', 'y': 'y'}}})


def test_unbound_structured_need_cannot_use_legacy_method_readiness(tmp_path):
    from src.sources.models import AcquisitionRecord
    runtime, store, tools, ctx = runtime_case(tmp_path / 'unbound-method.sqlite3')
    record = AcquisitionRecord(source='fixture', request={},
        records=({'id': 'a', 'values': 1}, {'id': 'b', 'values': 2}),
        provenance=('explicit contract fixture',), origin='synthetic')
    runtime.retain_acquisition(ctx.deps.block_id, record)
    result = asyncio.run(tools['assess_method'](ctx, 'stat.pandas',
        {'question': 'Describe values', 'estimand': 'mean', 'population': 'observations', 'design': 'descriptive'},
        [record.acquisition_id], operation='descriptive_summary'))
    assert not result['checks']['eligible']
    assert 'representation_prerequisites_unmet' in result['checks']['reasons']
    bound = asyncio.run(tools['assess_method'](ctx, 'stat.pandas',
        {'question': 'Describe values', 'estimand': 'mean', 'population': 'observations', 'design': 'descriptive',
         'representation_need': {'estimand': 'mean', 'representation': 'metadata', 'entity_key': 'id',
             'fields': {'values': 'values'}, 'numeric_roles': ['values'], 'minimum_complete_rows': 2}},
        [record.acquisition_id], operation='descriptive_summary'))
    assert bound['checks']['eligible']
    assert not store.records(kind=RecordKind.EVIDENCE)
    store.close()


def test_inspected_capability_grounds_fresh_frontier_and_survives_reopen(tmp_path):
    from src.runtime.pydantic_ai.contracts import DirectorDeps, register_director_tools
    from src.director.frontier import authored_investigations
    from src.memory.models import MemoryReference
    from src.persistence.records import StoredRecord
    path = tmp_path / 'grounding.sqlite3'
    runtime, store, _, _ = runtime_case(path)
    runtime.mission_id = 'fresh-mission'
    store.append(StoredRecord(kind=RecordKind.MISSION, record_id=runtime.mission_id,
                             payload={'direction': 'Investigate useful public data'}))
    agent = ToolCapture(); register_director_tools(agent)
    ctx = SimpleNamespace(deps=DirectorDeps(runtime))
    inspected = asyncio.run(agent.tools['describe_oncolab'](ctx, 'source.gdc'))
    ref = MemoryReference.model_validate(inspected['context_reference'])
    assert ref.kind == RecordKind.INDEX_RECEIPT.value
    retained = ResearchMemory(store).resolve(ref)
    assert retained['requested_id'] == 'source.gdc'
    candidates = authored_investigations(runtime, [{
        'objective': 'Investigate an available public cohort', 'proposed_test': 'Inspect coverage',
        'population': 'Public cases', 'design': 'Descriptive', 'capability_ids': ['source.gdc'],
        'context_refs': [ref.model_dump(mode='json')]}])
    assert candidates[0].source_refs[-1] == ref
    cards = asyncio.run(agent.tools['search_oncolab'](ctx, 'gdc'))
    assert cards
    for card in cards:
        context = MemoryReference.model_validate(card['context_reference'])
        assert card['capability_id'] in ResearchMemory(store).resolve(context)['returned_ids']
    from src.runtime.pydantic_ai.search_tools import register_search_page
    register_search_page(agent)
    page = asyncio.run(agent.tools['search_oncolab_page'](ctx, 'gdc'))
    page_ref = MemoryReference.model_validate(page['context_reference'])
    assert ResearchMemory(store).resolve(page_ref)['receipt_id'] == page['receipt_id']
    altered = ref.model_copy(update={'sha256': '0' * 64})
    with pytest.raises(ValueError, match='unresolved or changed'):
        ResearchMemory(store).resolve(altered)
    assert not store.records(kind=RecordKind.EVIDENCE)
    store.close()
    reopened = SqliteResearchStore(path)
    assert ResearchMemory(reopened).resolve(ref) == retained
    reopened.close()


def test_external_inspection_exposes_resolvable_context_without_evidence(tmp_path):
    import httpx
    from src.oncolab.discovery import ExternalDiscovery
    from src.runtime.pydantic_ai.contracts import DirectorDeps
    from src.runtime.pydantic_ai.discovery_tools import register_discovery_tools
    from src.memory.models import MemoryReference
    runtime, store, _, _ = runtime_case(tmp_path / 'external-grounding.sqlite3')
    runtime.external_discovery = ExternalDiscovery(httpx.MockTransport(lambda request:
        httpx.Response(200, json={'list': [{'biotoolsID': 'method', 'name': 'Method',
            'description': 'Public metadata'}], 'count': 1})))
    agent = ToolCapture(); register_discovery_tools(agent)
    view = asyncio.run(agent.tools['search_external_capabilities'](
        SimpleNamespace(deps=DirectorDeps(runtime)), 'bio.tools', 'method'))
    ref = MemoryReference.model_validate(view['context_reference'])
    assert ref.kind == RecordKind.EXTERNAL_LOOKUP.value
    assert ResearchMemory(store).resolve(ref)['lookup_id'] == view['lookup_id']
    assert 'raw_json' not in view
    assert not store.records(kind=RecordKind.EVIDENCE)
    store.close()


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
    from evals.reference import search_metrics, summarize_search_rows
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


def test_method_comparison_scores_generator_recall_instead_of_supplied_ids():
    from pathlib import Path
    from src.config.loader import load_models_config, load_runtime_config
    from src.config.models import RuntimeMode
    from evals.reference import load_reference_corpus, evaluate_reference_cases, reference_consumer_adapter
    from evals.models import EvaluationCondition
    from src.runtime.pydantic_ai.agents import create_agents
    root = Path(__file__).resolve().parents[2]
    case = next(c for c in load_reference_corpus(root / 'evals/reference/scientific-v1.json')
                if c.case_id == 'search-method-tuning')
    # The summary route is supplied to the comparison but not retrieved by this query.
    case = case.model_copy(update={'search_labels': {'useful_ids': ['science.acquisition-summary']}})
    report = evaluate_reference_cases((case,), reference_consumer_adapter,
        models=load_models_config(root / 'config/models.yaml'),
        policy=load_runtime_config(root / 'config/runtime.yaml').model_copy(update={'mode': RuntimeMode.DETERMINISTIC}),
        environment={}, agents_factory=lambda: create_agents('test', 'test', enable_coder=False),
        conditions=(EvaluationCondition.SCIENCE_ONLY,), memory_alternatives=(3,))
    row = report['rows'][0]
    actual = [c['capability_id'] for c in row['observations']['generation']['candidates']]
    assert 'science.acquisition-summary' not in actual
    assert row['observations']['retrieved_ids'] == actual
    assert row['search_metrics']['useful_candidate_recall'] == 0
    assert set(row['observations']['selectable_ids']) <= set(actual)


def test_instability_separates_classification_policy_and_downstream_choice():
    from evals.reference import summarize_search_rows, search_metrics
    rows = [{'case_id': 'separate', 'condition': 'science_jev', 'memory_alternative_limit': 3,
        'repetition': i, 'observations': {'fit_by_id': {'a': fit}, 'policy_actions': {'a': 'keep_alive'},
            'selected_id': 'a', 'selectable_ids': ['a']}} for i, fit in enumerate((True, None))]
    series = summarize_search_rows(rows)['series'][0]
    assert series['label_classification_instability'] is True
    assert series['policy_instability'] is False
    assert series['downstream_choice_instability'] is False
    rows[1]['observations']['policy_actions']['a'] = 'advance'
    assert summarize_search_rows(rows)['series'][0]['policy_instability'] is True
    assert summarize_search_rows(rows)['series'][0]['downstream_choice_instability'] is False
    labels = {'fit_by_id': {'a': True, 'b': False}, 'nonduplicate_ids': ['a']}
    assert search_metrics({'fit_by_id': {'a': None, 'b': False}, 'duplicate_ids': ['a']}, labels)['unknown_rate'] == .5
    assert search_metrics({}, labels)['unknown_rate'] is None
    assert search_metrics({'duplicate_ids': ['a']}, labels)['false_duplicate_rate'] == 1


@pytest.mark.parametrize('domain', ('representation', 'method'))
def test_source_search_comparison_transforms_and_executes_selected_owned_input(domain):
    from pathlib import Path
    from src.config.loader import load_models_config, load_runtime_config
    from src.config.models import RuntimeMode
    from evals.reference import ReferenceCase, evaluate_reference_cases, reference_consumer_adapter
    from evals.models import EvaluationCondition
    from src.runtime.pydantic_ai.agents import create_agents
    from src.sources.models import AcquisitionRecord, CoverageContract
    source = AcquisitionRecord(source='gdc', origin='synthetic', request={},
        records=tuple({'case_id': str(i), 'demographic': {'age_at_index': 20 + i * 10,
            'days_to_death': v, 'vital_status': 'Dead'}} for i, v in enumerate((10, 45, 20, 55, 30))),
        coverage=CoverageContract(endpoint='cases', requested_size=5, returned_rows=5,
            reported_total=5, id_field='case_id', unique_entities=5, ordering='fixture', complete=True),
        provenance=('generated source schema; never scientific evidence',))
    need = {'estimand': 'recorded age', 'representation': 'clinical', 'entity_key': 'case_id',
        'entity_unit': 'case', 'fields': {'values': 'demographic.age_at_index'}, 'numeric_roles': ['values']}
    inputs = {'operation': 'search_comparison', 'search_domain': domain, 'need': need,
        'candidates': [{'id': 'raw', 'acquisition': source.model_dump(mode='json')}],
        'representation_transforms': [{'id': m, 'source_id': 'raw', 'representation': m} for m in ('clinical', 'survival')],
        'downstream_numeric_field': 'demographic.age_at_index'}
    if domain == 'method':
        estimand = 'correlation'
        inputs = {'operation': 'search_comparison', 'search_domain': domain, 'candidates': [],
            'acquisition': source.model_dump(mode='json'), 'derive_clinical': True,
            'downstream_method': 'pearson_correlation', 'need': {'question': 'Do recorded fields correlate?',
                'estimand': estimand, 'population': 'generated rows', 'design': 'paired exploratory',
                'representation_need': {**need, 'estimand': estimand, 'representation': 'paired_data',
                    'fields': {'x': 'demographic.age_at_index', 'y': 'demographic.days_to_death'}, 'numeric_roles': ['x', 'y']}}}
    case = ReferenceCase(case_id='owned-search', split='tuning', domain=domain, public_inputs=inputs,
        expected={'selected_id': 'clinical' if domain == 'representation' else 'science.source-paired'},
        reference_url='https://example.invalid', label_basis='generated contract')
    root = Path(__file__).resolve().parents[2]
    report = evaluate_reference_cases((case,), reference_consumer_adapter,
        models=load_models_config(root / 'config/models.yaml'),
        policy=load_runtime_config(root / 'config/runtime.yaml').model_copy(update={'mode': RuntimeMode.DETERMINISTIC}),
        environment={}, agents_factory=lambda: create_agents('test', 'test', enable_coder=False),
        conditions=(EvaluationCondition.SCIENCE_ONLY,), memory_alternatives=(3,))
    row = report['rows'][0]; observation = row['observations']
    assert row['agreement'] is True, observation.get('adapter_error_detail')
    measurement = observation['downstream_measurement']
    assert measurement['origin'] == 'synthetic' and row['metrics']['evidence'] == 0
    if domain == 'representation': assert measurement['values']['mean'] == 40
    else: assert measurement['values']['n'] == 5
    assert {r['payload']['stage'] for r in observation['scientific_attempts']} == {'started', 'completed'}
    assert observation['representation_receipts']
    assert any(r['payload']['acquisition_id'] in measurement['source_refs'] for r in observation['source_acquisitions'])


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
    from evals.reference import ReferenceCase, evaluate_reference_cases, reference_consumer_adapter
    from evals.models import EvaluationCondition
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


@pytest.mark.parametrize('route', ('typed', 'candidate'))
@pytest.mark.parametrize('corruption', ('empty', 'partial', 'duplicate', 'projection', 'version', 'primitive', 'nonfinite', 'metadata'))
def test_runtime_rejects_malformed_semantic_batches_before_policy(tmp_path, route, corruption):
    from src.jev.failure import JevOperationalFailure
    from src.jev.models import ChoiceDecision
    from src.runtime.pydantic_ai.agents import create_agents
    runtime, store, tools, ctx = runtime_case(tmp_path / f'{route}-{corruption}.sqlite3')
    class CorruptJev:
        def evaluate(self, payload, questions):
            decisions = list(DeterministicJevClient().evaluate(payload, questions))
            if corruption == 'empty': return ()
            if corruption == 'partial': return tuple(decisions[:-1])
            if corruption == 'duplicate': decisions[-1] = decisions[0]
            if corruption == 'projection': decisions[0] = decisions[0].model_copy(update={'projection_id': 'another-projection'})
            if corruption == 'version': decisions[0] = decisions[0].model_copy(update={'question_version': 'another-version'})
            if corruption == 'nonfinite': decisions[0] = decisions[0].model_copy(update={'p_true': float('nan')})
            if corruption == 'primitive':
                fields = decisions[0].model_dump(exclude={'p_true'})
                decisions[0] = ChoiceDecision(**fields, selected_option='yes', probabilities={'yes': .9, 'no': .1}, confidence=.9)
            if corruption == 'metadata':
                from src.jev.client import JevBatch
                decisions[0] = decisions[0].model_copy(update={'question_version': 'another-version'})
                return JevBatch(decisions, {'usage': {}})
            return tuple(decisions)
    runtime.jev = CorruptJev()
    if route == 'typed':
        call = tools['assess_hypothesis'](ctx, 'X relates to Y', 'paired correlation')
    else:
        agent = create_agents('test', 'test', enable_coder=False).researcher
        call = agent._function_toolset.tools['evaluate_candidate'].function(ctx, 'candidate', 'public association')
    try:
        with pytest.raises(JevOperationalFailure): asyncio.run(call)
        assert store.latest(RecordKind.JEV_CALL).payload['outcome'] == 'failed'
        assert not store.records(kind=RecordKind.JEV_OUTPUT)
        assert not any(r.payload['event_type'] == 'FrontierDecision' for r in store.records(kind=RecordKind.LEDGER_EVENT))
        assert not store.records(kind=RecordKind.EVIDENCE)
        assert runtime.research_state.get(ctx.deps.block_id).candidates
    finally: store.close()


def test_method_generation_byte_failure_preserves_discovered_alternatives(tmp_path):
    from src.sources.models import AcquisitionRecord
    runtime, store, tools, ctx = runtime_case(tmp_path / 'method-byte-failure.sqlite3')
    records = [AcquisitionRecord(source='fixture', request={'slice': i},
        records=({'id': str(i), 'x': 1, 'y': 2},), provenance=('generated input contract',)) for i in range(10)]
    for record in records: runtime.retain_acquisition(ctx.deps.block_id, record)
    need = {'question': 'Compare paired measurements', 'estimand': 'correlation', 'population': 'retained rows', 'design': 'paired',
        'representation_need': {'estimand': 'correlation', 'representation': 'paired_data', 'entity_key': 'id',
            'fields': {'x': 'x', 'y': 'y'}, 'numeric_roles': ['x', 'y'], 'units': {'x': 'u' * 2000, 'y': 'v' * 2000}}}
    try:
        with pytest.raises(ValueError, match='method generation byte bound'):
            asyncio.run(tools['generate_method_candidates'](ctx, need, [r.acquisition_id for r in records], limit=8))
        retained = store.latest(RecordKind.METHOD_CANDIDATES)
        assert retained is not None and retained.payload['candidates']
        assert retained.payload['omitted_candidates'] == 0
        ids = {c['capability_id'] for c in retained.payload['candidates']}
        index = store.latest(RecordKind.INDEX_RECEIPT)
        assert ids == set(index.payload['returned_ids'])
        assert not store.records(kind=RecordKind.EVIDENCE)
    finally: store.close()


def test_global_investigation_uses_only_its_neighbours_measured_relations(tmp_path, monkeypatch):
    from src.director.frontier import Investigation
    from src.memory.service import reference
    from src.persistence.records import StoredRecord
    import src.runtime.pydantic_ai.global_tools as global_tools
    runtime, store, tools, ctx = runtime_case(tmp_path / 'global-relations.sqlite3')
    runtime.unbounded_work = True
    record = store.append(StoredRecord(kind=RecordKind.SERVICE_EVENT, record_id='relation-fixture', payload={'scope': 'generated test'}))
    candidates = tuple(Investigation(candidate_id=f'c{i}', objective=f'Distinct oncology question {i}',
        origin='hypotheses', source_refs=(reference(record),), scope={'proposed_test': f'test {i}'}) for i in range(4))
    monkeypatch.setattr(global_tools, 'generate', lambda *args, **kwargs: (candidates, 0))
    payloads = []
    class CaptureJev:
        def evaluate(self, payload, questions):
            if questions[0].semantic_purpose.startswith('global_investigation.'):
                payloads.append(payload)
            return DeterministicJevClient().evaluate(payload, questions)
    runtime.jev = CaptureJev()
    try:
        frontier = asyncio.run(global_tools.prepare_frontier(runtime, 'oncology', limit=4))
        assert len(payloads) == 4
        for payload in payloads:
            identity = payload['candidate']['candidate_id']
            neighbours = {c['candidate_id'] for c in payload['comparison']}
            assert payload['relations'] and len(payload['relations']) <= 2
            for relation in payload['relations']:
                pair = {relation['left_id'], relation['right_id']}
                assert identity in pair and pair - {identity} <= neighbours
                assert relation['decisions'] and relation['semantic_call_id']
                durable = next(r for r in frontier.relations if r['relation_id'] == relation['relation_id'])
                assert relation['decisions'] == durable['decisions']
        assert not store.records(kind=RecordKind.EVIDENCE)
    finally: store.close()


@pytest.mark.parametrize('primitive', ('choice', 'score'))
@pytest.mark.parametrize('corruption', ('support', 'distribution', 'selection'))
def test_shared_batch_validation_rejects_invalid_native_distributions(primitive, corruption):
    from src.jev.client import validate_jev_batch
    from src.jev.failure import JevOperationalFailure
    from src.jev.models import JevQuestionSpec
    question = JevQuestionSpec(question_id='native', semantic_purpose='native validation', primitive=primitive,
        projection_id='projection', question_version='v1', instructions='generated contract',
        criteria={'yes': 'yes', 'no': 'no'} if primitive == 'choice' else ['low', 'medium', 'high'])
    decisions = list(DeterministicJevClient().evaluate({}, (question,)))
    field = 'probabilities' if primitive == 'choice' else 'level_probabilities'
    if corruption == 'support': changes = {field: {'other': 1.0}}
    elif corruption == 'distribution': changes = {field: {key: 0.9 for key in getattr(decisions[0], field)}}
    else: changes = {'selected_option': 'unlisted'} if primitive == 'choice' else {'expected_score': 10.0}
    decisions[0] = decisions[0].model_copy(update=changes)
    with pytest.raises(JevOperationalFailure): validate_jev_batch(tuple(decisions), (question,))


def test_clean_service_bootstrap_and_restart_never_load_historical_seed(tmp_path, monkeypatch):
    from src.autonomous import service_from_environment
    from src.oncolab.registry import OncoLabIndex
    from src.runtime.pydantic_ai.factory import build_system
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    data = tmp_path / 'fresh-production-data'
    monkeypatch.setenv('ONCOJEV_TESTING', '0')
    monkeypatch.setenv('ONCOJEV_DATA_ROOT', str(data))
    monkeypatch.delenv('ONCOJEV_DB_PATH', raising=False)
    monkeypatch.setenv('OPENROUTER_API_KEY', 'fixture')
    monkeypatch.setenv('TYPESAFE_API_KEY', 'fixture')
    environment = {'OPENROUTER_API_KEY': 'fixture', 'TYPESAFE_API_KEY': 'fixture', 'ONCOJEV_TESTING': '0', 'ONCOJEV_DATA_ROOT': str(data)}
    def historical_load(*args, **kwargs): raise AssertionError('historical seed is not production input')
    monkeypatch.setattr(OncoLabIndex, 'load_verification_records', historical_load)
    first = service_from_environment(root)
    assert first.store.records() == ()
    identities = []
    try:
        for service in (first,):
            system = build_system(service.models, service.policy,
                environment=environment, repository=service.repository, resources=service.resources, paths=service.paths)
            identities.append(system.runtime.institution.pin().oncolab_registry_revision)
            assert system.runtime.index_for().count() >= 100
            assert not service.store.records(kind=RecordKind.INSTITUTIONAL_OBSERVATION)
            assert not service.store.records(kind=RecordKind.VERIFICATION)
            async def close_clients():
                for client in (system.runtime.gdc, system.runtime.xena, system.runtime.literature): await client.aclose()
            asyncio.run(close_clients())
    finally: first.close()
    second = service_from_environment(root)
    try:
        system = build_system(second.models, second.policy,
            environment=environment, repository=second.repository, resources=second.resources, paths=second.paths)
        assert system.runtime.institution.pin().oncolab_registry_revision == identities[0]
        assert len(second.store.records(kind=RecordKind.REGISTRY_REVISION)) == 1
        assert not second.store.records(kind=RecordKind.INSTITUTIONAL_OBSERVATION)
        assert not second.store.records(kind=RecordKind.EVIDENCE)
        asyncio.run(close_clients())
    finally: second.close()
