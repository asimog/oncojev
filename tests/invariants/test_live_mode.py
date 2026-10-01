"""Phase 6: centralized model configuration, live/deterministic selection, and failure semantics."""

from pathlib import Path

import pytest
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import DeltaToolCall, FunctionModel

from src.block.manager import BlockManager
from src.config.authentication import (
    MODEL_PROVIDER_ENV,
    SCIENTIFIC_DATA_ENV,
    AuthenticationDomain,
    live_providers_available,
    resolve_mode,
)
from src.config.loader import load_models_config, load_runtime_config
from src.config.models import RuntimeMode, SandboxConfig
from src.director.models import ResourceAllocation
from src.jev.client import DeterministicJevClient, TypeSafeJevClient
from src.jev.failure import JevOperationalFailure, classify_jev_exception
from src.jev.models import JevExecutionFailure, JevFailureCategory, JevQuestionSpec
from src.reasoner.agent import LiveReasoner
from src.reasoner.service import DeterministicReasoner
from src.runtime.pydantic_ai.agents import create_agents
from src.runtime.pydantic_ai.contracts import HarnessRuntime, ResearcherDeps
from src.runtime.pydantic_ai.factory import build_harness_runtime, build_jev_client, build_reasoner, build_system
from src.science.execution import ScienceExecutor

ROOT = Path(__file__).resolve().parents[2]

LIVE_ENV = {"OPENROUTER_API_KEY": "k", "TYPESAFE_API_KEY": "k"}
QUESTION = JevQuestionSpec(
    question_id="q",
    semantic_purpose="p",
    primitive="noul",
    projection_id="proj",
    instructions="i",
    criteria={},
    question_version="1",
)


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


def test_model_configuration_is_centralized_and_repo_owned():
    models = load_models_config(ROOT / "config/models.yaml")
    policy = load_runtime_config(ROOT / "config/runtime.yaml")
    assert policy.mode is RuntimeMode.LIVE
    assert all(role.provider for role in (models.director, models.researcher, models.reasoner, models.jev))


def test_deterministic_fixture_needs_no_credentials_and_live_fails_closed_without_them():
    models = load_models_config(ROOT / "config/models.yaml")
    assert isinstance(build_jev_client(models, RuntimeMode.DETERMINISTIC, {}), DeterministicJevClient)
    assert isinstance(build_reasoner(models, RuntimeMode.DETERMINISTIC, {}), DeterministicReasoner)
    with pytest.raises(RuntimeError, match="requires OPENROUTER_API_KEY"):
        build_reasoner(models, RuntimeMode.LIVE, {})
    with pytest.raises(RuntimeError, match="requires OPENROUTER_API_KEY"):
        resolve_mode(RuntimeMode.LIVE, {"OPENROUTER_API_KEY": "k"})
    assert resolve_mode(RuntimeMode.LIVE, LIVE_ENV) is RuntimeMode.LIVE
    assert live_providers_available(LIVE_ENV) and not live_providers_available({})


def test_live_clients_are_built_only_when_both_credentials_exist():
    models = load_models_config(ROOT / "config/models.yaml")
    assert isinstance(build_jev_client(models, RuntimeMode.LIVE, LIVE_ENV), TypeSafeJevClient)
    assert isinstance(build_reasoner(models, RuntimeMode.LIVE, LIVE_ENV), LiveReasoner)


def test_authentication_domains_are_separate_and_disjoint():
    assert MODEL_PROVIDER_ENV & SCIENTIFIC_DATA_ENV == frozenset()
    assert AuthenticationDomain.MODEL_PROVIDER != AuthenticationDomain.SCIENTIFIC_DATA


def test_build_system_is_live_fail_closed_and_roles_stay_independent():
    models = load_models_config(ROOT / "config/models.yaml")
    policy = load_runtime_config(ROOT / "config/runtime.yaml")
    with pytest.raises(RuntimeError, match="requires OPENROUTER_API_KEY"):
        build_system(models, policy, environment={})
    system = build_system(models, policy, environment=LIVE_ENV)
    assert system.mode is RuntimeMode.LIVE
    assert isinstance(system.runtime.jev, TypeSafeJevClient)
    assert isinstance(system.runtime.reasoner, LiveReasoner)
    assert system.agents.director is not system.agents.researcher
    assert system.runtime.researcher_factory is not None


def test_runtime_applies_sandbox_configuration():
    models = load_models_config(ROOT / "config/models.yaml")
    policy = load_runtime_config(ROOT / "config/runtime.yaml").model_copy(
        update={
            "mode": RuntimeMode.DETERMINISTIC,
            "sandbox": SandboxConfig(image="custom/science:locked", cpu=3, memory_mb=2048, timeout_seconds=77),
        }
    )
    runtime = build_harness_runtime(models, policy, environment={})
    assert runtime.sandbox.policy.image == "custom/science:locked"
    assert runtime.sandbox.policy.cpu == 3
    assert runtime.sandbox.policy.timeout_seconds == 77


def test_typesafe_failure_is_operational_and_never_a_decision():
    client = TypeSafeJevClient(api_key="k", model="jev-1.13.0")

    class Boom:
        def system_one(self, state, specs):
            raise TimeoutError("upstream timed out")

    client._client = Boom()
    with pytest.raises(JevOperationalFailure) as raised:
        client.evaluate({}, (QUESTION,))
    assert raised.value.failures[0].category is JevFailureCategory.TIMEOUT
    assert classify_jev_exception(ValueError("bad schema")) is JevFailureCategory.VALIDATION
    assert classify_jev_exception(Exception("rate limit exceeded")) is JevFailureCategory.RATE_LIMIT


def test_jev_failure_is_recorded_operationally_and_yields_no_frontier_or_evidence():
    class FailingJev:
        def evaluate(self, state, questions):
            raise JevOperationalFailure(
                tuple(
                    JevExecutionFailure(question_id=question.question_id, category=JevFailureCategory.TRANSPORT, detail="down")
                    for question in questions
                )
            )

    manager = BlockManager()
    block = manager.create("fail jev", "test", ResourceAllocation(seconds=60))
    runtime = HarnessRuntime(
        manager=manager,
        jev=FailingJev(),
        science=ScienceExecutor(),
        reasoner=DeterministicReasoner(),
        max_jev_calls=2,
        max_reasoner_calls=1,
    )
    runtime.research_state.start(block.block_id, block.objective)
    runtime.skills.start(block.block_id)
    calls = 0

    async def model(messages, info):
        nonlocal calls
        calls += 1
        if calls == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "run_code",
                        {"code": 'await evaluate_candidate(candidate_id="candidate", candidate_summary="synthetic")'},
                        tool_call_id="jev",
                    )
                ]
            )
        return ModelResponse(parts=[TextPart("done")])

    researcher = create_agents("test", "test").fresh_researcher()
    with researcher.override(model=scripted(model)):
        result = researcher.run_sync("evaluate", deps=ResearcherDeps(runtime=runtime, block_id=block.block_id))
    events = {event.event_type for event in manager.ledger(block.block_id).history()}
    assert result.output == "done"
    assert "JevExecutionFailure" in events
    assert "FrontierDecision" not in events
    assert "EvidenceAdmission" not in events
