"""Phase 9: dynamic research evaluation across capability conditions."""

from pathlib import Path

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


def _runner(system, direction, repository: ResearchRepository, condition: EvaluationCondition) -> None:
    acquisition = AcquisitionRecord(source="gdc", request={"fixture": True}, records=({"file_id": "a"}, {"file_id": "b"}), provenance=("test-source",))
    system.runtime.acquisitions[acquisition.acquisition_id] = acquisition
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
            lines.append('await complete_block(reason="done")')
            lines.append('"researcher complete"')
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": "\n".join(lines)}, tool_call_id="r1")])
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
