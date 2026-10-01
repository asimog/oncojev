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
            if condition is not EvaluationCondition.SCIENCE_ONLY:
                lines.append('await generate_hypotheses(finding="measured association")')
            if condition is EvaluationCondition.SCIENCE_JEV_REASONER:
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
        agents_factory=lambda: create_agents("test", "test"),
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
        assert metrics.evidence == 2
        assert metrics.source_bound_evidence == 2
        assert metrics.deterministic_evidence is True
        assert metrics.dossiers == 1
        assert metrics.has_preferred_continuation is True


def test_report_does_not_hardcode_a_winner_and_path_is_dynamic():
    report = _evaluate(DIRECTIONS[1])
    assert "best" not in EvaluationReport.model_fields
    assert "winner" not in EvaluationReport.model_fields
    assert len(report.conditions) == 3
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
        agents_factory=lambda: create_agents("test", "test"),
        environment={},
        runner=_runner,
    )
    assert len(reports) == len(DIRECTIONS)
    assert all(len(report.conditions) == 3 for report in reports)


@pytest.mark.parametrize("failure", ["researcher", "custom_before_cycle", "custom_after_cycle", "setup_failure", "custom_no_receipt"])
def test_failed_condition_preserves_partial_results_and_continues(failure):
    visited = []
    builds = 0

    def agents_factory():
        nonlocal builds
        builds += 1
        if failure == "setup_failure" and builds == 1:
            raise ValueError("agent construction failed")
        return create_agents("test", "test")

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
        assert first.evidence == 2 and first.dossiers == 1
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
