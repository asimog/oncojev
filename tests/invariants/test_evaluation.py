"""Phase 9: dynamic research evaluation across capability conditions."""

from pathlib import Path
import pytest
from pydantic_ai.exceptions import UsageLimitExceeded

from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import DeltaToolCall, FunctionModel

from src.config.loader import load_models_config, load_runtime_config
from src.config.models import RuntimeMode
from src.evals.corpus import DIRECTIONS
from src.evals.harness import evaluate_corpus, evaluate_direction
from src.evals.models import EvaluationCondition, EvaluationReport
from src.persistence.repository import ResearchRepository
from src.runtime.cycle import run_cycle
from src.runtime.pydantic_ai.agents import create_agents
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


def _runner(system, direction, repository: ResearchRepository, condition: EvaluationCondition, *, fail_researcher=False) -> None:
    acquisition = AcquisitionRecord(source="gdc", request={"fixture": True}, records=({"file_id": "a"}, {"file_id": "b"}), provenance=("test-source",))
    system.runtime.acquisitions[acquisition.acquisition_id] = acquisition
    director_calls = 0
    researcher_calls = 0

    async def director_model(messages, info):
        nonlocal director_calls
        director_calls += 1
        if director_calls == 1:
            code = (
                'block = await allocate_block(objective="measure a public signal", why_now="test")\n'
                'await launch_researcher(block_id=block["block_id"])\nblock'
            )
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": code}, tool_call_id="d1")])
        return ModelResponse(parts=[TextPart("director complete")])

    async def researcher_model(messages, info):
        nonlocal researcher_calls
        researcher_calls += 1
        if researcher_calls == 1:
            lines = [
                f'await measure_acquisition(acquisition_id="{acquisition.acquisition_id}", analysis_id="summary")',
                'await admit_measurement(analysis_id="summary")',
                f'await measure_acquisition(acquisition_id="{acquisition.acquisition_id}", analysis_id="replicate")',
                'await admit_measurement(analysis_id="replicate")',
            ]
            if condition in {EvaluationCondition.SCIENCE_REASONER, EvaluationCondition.SCIENCE_JEV_REASONER}:
                lines.append('await generate_hypotheses(finding="measured association")')
            if condition in {EvaluationCondition.SCIENCE_JEV, EvaluationCondition.SCIENCE_JEV_REASONER}:
                lines.append('await evaluate_candidate(candidate_id="candidate", candidate_summary="synthetic subgroup")')
            if not fail_researcher:
                lines.append('await complete_block(reason="done")')
            lines.append('"researcher complete"')
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": "\n".join(lines)}, tool_call_id="r1")])
        if fail_researcher:
            raise UsageLimitExceeded("Researcher failed with partial evidence")
        return ModelResponse(parts=[TextPart("researcher complete")])

    with system.agents.director.override(model=scripted(director_model)), system.agents.researcher.override(model=scripted(researcher_model)):
        run_cycle(system, direction, repository=repository, mission_id=condition.value)


def _evaluate(direction: str) -> EvaluationReport:
    return evaluate_direction(
        direction,
        models=load_models_config(ROOT / "config/models.yaml"),
        policy=load_runtime_config(ROOT / "config/runtime.yaml").model_copy(update={"mode": RuntimeMode.DETERMINISTIC}),
        agents_factory=lambda: create_agents("test", "test", enable_coder=False),
        environment={},
        runner=_runner,
    )


def test_conditions_differ_only_in_semantic_capabilities_and_are_all_deterministic():
    report = _evaluate(DIRECTIONS[0])
    by_condition = {metrics.condition: metrics for metrics in report.conditions}
    assert set(by_condition) == set(EvaluationCondition)

    science_only = by_condition[EvaluationCondition.SCIENCE_ONLY]
    science_reasoner = by_condition[EvaluationCondition.SCIENCE_REASONER]
    full = by_condition[EvaluationCondition.SCIENCE_JEV_REASONER]

    assert science_only.jev_executions == 0 and science_only.reasoner_outputs == 0
    assert science_reasoner.reasoner_outputs >= 1 and science_reasoner.jev_executions == 0
    assert full.jev_executions >= 1 and full.reasoner_outputs >= 1

    for metrics in report.conditions:
        assert metrics.measurements == 2
        assert metrics.evidence == 1
        assert metrics.unique_analysis_outcomes == 1 and metrics.declared_replication_outcomes == 0
        assert metrics.source_bound_evidence == 1
        assert metrics.deterministic_evidence is True
        assert metrics.dossiers == 1
        assert metrics.has_preferred_continuation is True


def test_report_does_not_hardcode_a_winner_and_path_is_dynamic():
    report = _evaluate(DIRECTIONS[1])
    assert "best" not in EvaluationReport.model_fields
    assert "winner" not in EvaluationReport.model_fields
    assert len(report.conditions) == 4
    assert all(metrics.blocks == 1 for metrics in report.conditions)


def test_provider_and_method_changes_need_no_architecture_change():
    models = load_models_config(ROOT / "config/models.yaml")
    swapped = models.model_copy(
        update={"director": models.director.model_copy(update={"model": "openrouter:some-other-model"})}
    )
    assert swapped.director.model != models.director.model
    assert swapped.researcher.model == models.researcher.model
    assert models.researcher.max_output_tokens == 16000


def test_evaluation_corpus_runs_reproducibly_in_deterministic_mode():
    reports = evaluate_corpus(
        DIRECTIONS,
        models=load_models_config(ROOT / "config/models.yaml"),
        policy=load_runtime_config(ROOT / "config/runtime.yaml").model_copy(update={"mode": RuntimeMode.DETERMINISTIC}),
        agents_factory=lambda: create_agents("test", "test", enable_coder=False),
        environment={},
        runner=_runner,
    )
    assert len(reports) == len(DIRECTIONS)
    assert all(len(report.conditions) == 4 for report in reports)


@pytest.mark.parametrize("failure", ["researcher", "custom_before_cycle", "custom_after_cycle", "setup_failure", "custom_no_receipt"])
def test_failed_condition_preserves_partial_results_and_continues(failure):
    visited = []
    builds = 0

    def agents_factory():
        nonlocal builds
        builds += 1
        if failure == "setup_failure" and builds == 1:
            raise ValueError("agent construction failed")
        return create_agents("test", "test", enable_coder=False)

    def runner(system, direction, repository, condition):
        visited.append(condition)
        if condition is EvaluationCondition.SCIENCE_ONLY:
            if failure == "custom_no_receipt":
                return
            if failure == "custom_before_cycle":
                raise ValueError("custom runner failed")
            _runner(system, direction, repository, condition, fail_researcher=failure == "researcher")
            raise ValueError("custom runner failed after completed cycle")
        _runner(system, direction, repository, condition)

    report = evaluate_direction(DIRECTIONS[0], models=load_models_config(ROOT / "config/models.yaml"),
                                policy=load_runtime_config(ROOT / "config/runtime.yaml").model_copy(update={"mode": RuntimeMode.DETERMINISTIC}),
                                agents_factory=agents_factory, environment={}, runner=runner)
    assert visited == (list(EvaluationCondition)[1:] if failure == "setup_failure" else list(EvaluationCondition))
    first, *remaining = report.conditions
    assert first.status.value == ("incomplete" if failure == "custom_no_receipt" else "failed")
    assert first.error_type
    assert all(m.cycles == 1 for m in report.conditions)
    assert all(m.status.value == "complete" and m.completed_blocks == 1 for m in remaining)
    if failure == "researcher":
        assert first.evidence == 1 and first.dossiers == 1
        assert first.completed_blocks == 0 and first.failed_cycles == 1
    elif failure in {"custom_before_cycle", "setup_failure"}:
        assert first.completed_blocks == 0 and first.failed_cycles == 1
    elif failure == "custom_no_receipt":
        assert first.completed_blocks == 0 and first.incomplete_cycles == 1
    else:
        assert first.completed_blocks == 1 and first.failed_cycles == 0


def test_selection_evaluation_exposes_recall_unknown_denominators_and_non_gdc_space():
    from src.evals.selection import evaluate_selection,SelectionTask
    from src.runtime.pydantic_ai.contracts import HarnessRuntime
    from src.block.manager import BlockManager
    from src.director.models import ResourceAllocation
    from src.jev.client import DeterministicJevClient
    from src.reasoner.service import DeterministicReasoner
    from src.science.execution import ScienceExecutor
    manager=BlockManager();block=manager.create('select','test',ResourceAllocation(seconds=300))
    runtime=HarnessRuntime(manager=manager,jev=DeterministicJevClient(),science=ScienceExecutor(),reasoner=DeterministicReasoner(),max_jev_calls=100,max_reasoner_calls=1,oncolab_candidate_k=200)
    report=evaluate_selection(runtime,block.block_id,condition='deterministic')
    assert 'winner' not in report
    assert all(row['retrieval_recall']==1 for row in report['rows'] if row['labels'])
    assert any(row['information_space']=='literature' for row in report['rows'])
    assert all(row['downstream_scientific_utility'] is None and row['cost'] is None for row in report['rows'])
    assert next(row for row in report['rows'] if row['task_id']=='unimplemented-survival')['retrieval_recall'] is None


def test_representation_evaluation_isolates_labels_and_keeps_failure_fallback_gated(tmp_path):
    """Evaluation receipts expose misses/failures without leaking labels or granting absent inputs."""
    import asyncio, json
    from src.evals.representation import RepresentationCase, evaluate_representations
    from src.runtime.pydantic_ai.contracts import HarnessRuntime
    from src.persistence.store import SqliteResearchStore
    from src.persistence.records import RecordKind
    from src.block.manager import BlockManager
    from src.director.models import ResourceAllocation
    from src.reasoner.service import DeterministicReasoner
    from src.science.execution import ScienceExecutor
    from src.sources.representation import RepresentationNeed
    payloads = []
    class FailedProvider:
        def evaluate(self, state, questions):
            payloads.append(state)
            raise TimeoutError('fixture provider unavailable')
    store = SqliteResearchStore(tmp_path / 'evaluation.sqlite3')
    manager = BlockManager(); block = manager.create('representation comparison', 'evaluation', ResourceAllocation(seconds=300))
    runtime = HarnessRuntime(manager=manager, jev=FailedProvider(), science=ScienceExecutor(),
        reasoner=DeterministicReasoner(), max_jev_calls=10, max_reasoner_calls=1, repository=ResearchRepository(store))
    record = AcquisitionRecord(source='fixture-table', request={}, provenance=('input-contract fixture',), origin='synthetic',
        records=({'id':'a','x':1,'y':2}, {'id':'b','x':2,'y':5}))
    runtime.retain_acquisition(block.block_id, record)
    need = RepresentationNeed(estimand='pair', representation='paired_data', entity_key='id', fields={'x':'x','y':'y'}, numeric_roles=('x','y'))
    cases = (
        RepresentationCase(case_id='label-sentinel-valid', split='held_out', need=need,
            candidate_ids=(record.acquisition_id, 'unresolved'), useful_ids=(record.acquisition_id,), label_basis='label-sentinel-basis'),
        RepresentationCase(case_id='label-sentinel-missing', split='held_out', need=need.model_copy(update={'units':{'x':'TPM'}}),
            candidate_ids=(record.acquisition_id,), useful_ids=(), label_basis='label-sentinel-unmeasured-units'),
    )
    try:
        report = asyncio.run(evaluate_representations(runtime, block.block_id, cases, condition='jev_assisted'))
        valid, missing = report['rows']
        assert valid['retained_ids'] == [record.acquisition_id] and valid['retained_recall'] == 1
        assert valid['unresolved_ids'] == ['unresolved']
        assert valid['operational_failures'] and missing['operational_failures']
        assert missing['retained_ids'] == [] and missing['retained_recall'] is None
        assert all(not row['invalid_retained_ids'] and row['scientific_utility'] is None and row['cost'] is None for row in report['rows'])
        assert 'label-sentinel' not in json.dumps(payloads)
        assert not store.records(kind=RecordKind.EVIDENCE)
        assert all(r.payload['outcome'] in {'started','failed'} for r in store.records(kind=RecordKind.JEV_CALL))
    finally:
        store.close()


def test_reference_comparison_withholds_labels_and_matches_fresh_conditions():
    from src.evals.reference import ReferenceCase, evaluate_reference_cases
    case = ReferenceCase(case_id='held-out-secret', split='held_out', domain='contract', public_inputs={'direction': 'lung cancer', 'values': [1, 2]},
        expected={'result': 3}, reference_url='https://example.invalid/reference', label_basis='independent review pending')
    stores, gates = [], []
    def adapter(system, repository, condition, inputs, *, alternative_limit):
        assert set(inputs) == {'direction', 'values'}
        stores.append(repository.store)
        gates.append((condition, system.runtime.enable_jev, system.runtime.enable_reasoner))
        return {'result': sum(inputs['values'])}
    report = evaluate_reference_cases((case,), adapter, models=load_models_config(ROOT / 'config/models.yaml'),
        policy=load_runtime_config(ROOT / 'config/runtime.yaml').model_copy(update={'mode': RuntimeMode.DETERMINISTIC}),
        agents_factory=lambda: create_agents('test', 'test', enable_coder=False), environment={}, memory_alternatives=(0, 3))
    assert len(report['rows']) == 8 and all(row['agreement'] for row in report['rows'])
    assert len({id(store) for store in stores}) == 8
    assert {gate for gate in gates if gate[0] == EvaluationCondition.SCIENCE_JEV} == {(EvaluationCondition.SCIENCE_JEV, True, False)}
    assert report['scientific_utility'] is None and all(row['independent_review'] == 'pending' for row in report['rows'])


def test_utility_producer_binds_candidate_scope_comparison_without_fabricating_qualification():
    from src.evals.reference import retain_utility_evaluation
    from src.persistence.store import SqliteResearchStore
    from src.persistence.records import RecordKind, StoredRecord
    from src.provenance import content_hash
    store = SqliteResearchStore()
    candidate = store.append(StoredRecord(kind=RecordKind.SANDBOX_CANDIDATE, record_id='fixture-candidate', payload={'fixture': True}))
    scope = {'population': 'reference fixture'}
    report = {'rows': [{'case_id': 'reference', 'agreement': True, 'independent_review': 'pending',
        'observations': {'candidate_id': candidate.record_id, 'scope_sha256': content_hash(scope)}}],
        'mode': 'deterministic', 'repeats': 1, 'scientific_utility': None}
    proof = retain_utility_evaluation(store, candidate.record_id, scope, report, application_identity='fixture')
    assert proof.payload['status'] == 'unsupported' and proof.payload['candidate_sha256'] == content_hash(candidate.payload)
    comparison = store.record_at(proof.payload['comparison_reference']['seq'])
    assert content_hash(comparison.payload) == proof.payload['comparison_reference']['sha256']
    with pytest.raises(ValueError, match='scope'):
        retain_utility_evaluation(store, candidate.record_id, {'population': 'changed'}, report, application_identity='fixture')
    assert not store.records(kind=RecordKind.EVIDENCE)
    store.close()


def test_whole_lab_memory_and_open_proposal_variants_keep_actual_choice_lineage():
    from src.evals.reference import evaluate_reference_cases, load_reference_corpus, reference_consumer_adapter
    cases = load_reference_corpus(ROOT / 'evals/reference/scientific-v1.json')
    case = cases[0].model_copy(update={'public_inputs': {**cases[0].public_inputs, 'operation': 'whole_lab', 'search_mode': 'retained_only'}})
    report = evaluate_reference_cases((case,), reference_consumer_adapter, models=load_models_config(ROOT / 'config/models.yaml'),
        policy=load_runtime_config(ROOT / 'config/runtime.yaml').model_copy(update={'mode': RuntimeMode.DETERMINISTIC}),
        agents_factory=lambda: create_agents('test', 'test', enable_coder=False), environment={}, memory_alternatives=(0, 3),
        conditions=(EvaluationCondition.SCIENCE_ONLY,))
    withheld, retained = (row['observations'] for row in report['rows'])
    assert all(row['agreement'] is True for row in report['rows'])
    assert withheld['blocks_observed'] == 1 and not withheld['next_block_allocated']
    assert retained['blocks_observed'] == 2 and retained['next_block_allocated'] and retained['review_to_choice']
    assert retained['allocation_lineage'][0]['payload']['experience_refs']
    assert retained['program_reviews'] and all(review['scientific_value'] == 'unknown' for review in retained['program_reviews'])
    assert withheld['scientific_utility'] is None and retained['scientific_utility'] is None
    assert not any(row['observations']['native_semantic_receipts'] for row in report['rows'])


def test_reference_adapter_exception_is_not_masked_by_an_earlier_incomplete_cycle():
    from src.evals.reference import evaluate_reference_cases, ReferenceCase
    from src.block.models import CycleStatus
    case = ReferenceCase(case_id='failure', split='held_out', domain='operational', public_inputs={'direction': 'lung cancer'},
        expected={'result': 1}, reference_url='https://example.test/fixture', label_basis='Operational failure fixture')
    def failing(system, repository, condition, inputs, *, alternative_limit):
        repository.record_cycle('prior', 'deterministic', 'lung cancer', (), status=CycleStatus.INCOMPLETE, error_type='PriorIncomplete')
        raise ValueError('actual adapter failure')
    report = evaluate_reference_cases((case,), failing, models=load_models_config(ROOT / 'config/models.yaml'),
        policy=load_runtime_config(ROOT / 'config/runtime.yaml').model_copy(update={'mode': RuntimeMode.DETERMINISTIC}),
        agents_factory=lambda: create_agents('test', 'test', enable_coder=False), environment={}, memory_alternatives=(0,),
        conditions=(EvaluationCondition.SCIENCE_ONLY,))
    row = report['rows'][0]
    assert row['agreement'] is None and row['observations']['adapter_error_type'] == 'ValueError'
    assert row['metrics']['error_type'] == 'ValueError'
