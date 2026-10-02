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


@pytest.mark.parametrize("timing", [(300, 900, 3600, 90), (20, 30, 40, 5), (1, 2, 3, 0)])
def test_testing_overlay_preserves_shorter_bounds_and_other_allowances(tmp_path, timing):
    import yaml
    from datetime import UTC, datetime, timedelta
    from src.block.manager import HandoffRequired
    from src.config.models import RuntimeConfig
    from src.oncolab.institution import application_identity

    values = yaml.safe_load((ROOT / "config/runtime.yaml").read_text())
    minimum, default, maximum, reserve = timing
    values["block"].update(min_seconds=minimum, default_seconds=default,
                           max_seconds=maximum, handoff_reserve_seconds=reserve)
    values['block']['max_download_bytes'] = 5
    values['resources'].update(max_block_download_bytes=7, max_service_download_bytes=11)
    path = tmp_path / "runtime.yaml"
    path.write_text(yaml.safe_dump(values))
    normal = load_runtime_config(path, testing=False)
    tested = load_runtime_config(path, testing=True)
    expected = normal.model_dump()
    expected['testing']['public_data'].update(max_response_bytes=5,
        max_block_download_bytes=7, max_service_download_bytes=11)
    if default == 900:
        expected["block"].update(min_seconds=60, default_seconds=90, max_seconds=90, handoff_reserve_seconds=15)
    assert tested.model_dump() == expected
    assert normal.model_dump() == RuntimeConfig.model_validate(values).model_dump()
    assert normal.mode == tested.mode == RuntimeMode.LIVE
    assert application_identity(normal).startswith("application-v1:")
    identity = application_identity(tested)
    assert identity.startswith("application-testing-v1:") and identity != application_identity(normal)
    now = datetime(2026, 10, 2, tzinfo=UTC)
    manager = BlockManager(lambda: now, policy=tested.block)
    block = manager.allocate("bounded work", "profile test")
    assert (block.handoff_at - now).total_seconds() == tested.block.default_seconds - tested.block.handoff_reserve_seconds
    now = block.handoff_at - timedelta(microseconds=1)
    manager.require_work_window(block)
    now = block.handoff_at
    with pytest.raises(HandoffRequired):
        manager.require_work_window(block)
    assert application_identity(load_runtime_config(path, testing=True)) == identity


@pytest.mark.parametrize("change", [
    {"min_seconds": 91}, {"default_seconds": 0}, {"max_seconds": 50},
    {"handoff_reserve_seconds": 60},
])
def test_testing_profile_revalidates_invalid_bounds_even_when_disabled(tmp_path, change):
    import yaml
    from pydantic import ValidationError
    values = {"testing": {"block": change}}
    path = tmp_path / "runtime.yaml"
    path.write_text(yaml.safe_dump(values))
    for enabled in (False, True):
        with pytest.raises(ValidationError):
            load_runtime_config(path, testing=enabled)

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


@pytest.mark.parametrize("provider", [None, "docker"])
def test_runtime_applies_sandbox_configuration(provider):
    from src.science.local import LocalVenvScientificBackend
    from src.science.sandbox import DockerScientificSandbox
    models = load_models_config(ROOT / "config/models.yaml")
    options = {"provider": provider} if provider else {}
    policy = load_runtime_config(ROOT / "config/runtime.yaml").model_copy(
        update={
            "mode": RuntimeMode.DETERMINISTIC,
            "sandbox": SandboxConfig(**options, image="custom/science:locked", cpu=3, memory_mb=2048, timeout_seconds=77),
        }
    )
    runtime = build_harness_runtime(models, policy, environment={})
    assert isinstance(runtime.sandbox, DockerScientificSandbox if provider else LocalVenvScientificBackend)
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
    resources = runtime.resources(block.block_id)
    assert resources["jev"]["attempted"] == 1 and resources["jev"]["remaining"] == 1
    assert resources["jev_questions"]["attempted"] == 2


@pytest.mark.parametrize("resource,code", [
    ("source", 'await acquire_gdc(endpoint="files", filters={}, fields=["file_id"])'),
    ("jev", 'await evaluate_candidate(candidate_id="c", candidate_summary="unknown")'),
    ("jev_questions", 'await evaluate_candidate(candidate_id="c", candidate_summary="unknown")'),
    ("reasoner", 'await generate_hypotheses(finding="unknown")'),
    ("tool", 'await create_line_figure(title="denied", x=[1.0], y=[1.0])'),
    ("sandbox", 'await acquire_github_scientific_method(capability_need="newzzz", why_existing_capabilities_are_inadequate="missing method", repository_url="https://github.com/example/method", requested_ref="main", install_command=["true"], test_command=["true"], execute_command=["true"], input_json={})'),
])
def test_zero_resource_budgets_stop_before_side_effects_and_allow_handoff(resource, code, monkeypatch):
    models = load_models_config(ROOT / "config/models.yaml")
    policy = load_runtime_config(ROOT / "config/runtime.yaml")
    field = "max_jev_questions" if resource == "jev_questions" else f"max_{resource}_calls"
    policy = policy.model_copy(update={"mode": RuntimeMode.DETERMINISTIC,
                                      "block": policy.block.model_copy(update={field: 0})})
    runtime = build_harness_runtime(models, policy, environment={})
    assert getattr(runtime, field) == 0
    block = runtime.manager.allocate("bounded work", "test")
    effects = []

    def effect(*args, **kwargs):
        effects.append(resource)
        raise RuntimeError("side effect started")

    async def async_effect(*args, **kwargs):
        return effect(*args, **kwargs)

    monkeypatch.setattr(runtime.gdc, "search", async_effect)
    monkeypatch.setattr(runtime.jev, "evaluate", effect)
    monkeypatch.setattr(runtime.reasoner, "generate", async_effect)
    monkeypatch.setattr(runtime.sandbox, "acquire_and_execute", effect)
    monkeypatch.setattr("src.runtime.pydantic_ai.contracts.line_figure", effect)
    calls = 0

    async def model(messages, info):
        nonlocal calls
        calls += 1
        if calls == 1:
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": f'result = {code}\nassert result["retryable"] == False\nawait block_status()\nawait complete_block(reason="budget handoff")'}, tool_call_id="blocked")])
        return ModelResponse(parts=[TextPart("done")])

    agent = create_agents("test", "test").researcher
    with agent.override(model=scripted(model)):
        agent.run_sync("bounded work", deps=ResearcherDeps(runtime, block.block_id))
    assert not effects
    events = runtime.manager.ledger(block.block_id).history()
    assert any(e.event_type == "WorkNotStarted" and e.payload["retryable"] is False for e in events)
    assert any(e.event_type == "ResearcherHandoffRequested" for e in events)


def test_factory_allocation_defaults_and_bounds_are_enforced_through_tools():
    from src.runtime.pydantic_ai.contracts import DirectorDeps

    policy = load_runtime_config(ROOT / "config/runtime.yaml").model_copy(update={"mode": RuntimeMode.DETERMINISTIC})
    runtime = build_harness_runtime(load_models_config(ROOT / "config/models.yaml"), policy, environment={})
    calls = 0

    async def model(messages, info):
        nonlocal calls
        calls += 1
        if calls == 1:
            code = ('try:\n'
                    '    await allocate_block(objective="oversized", why_now="test", seconds=3601)\n'
                    'except Exception:\n'
                    '    pass\n'
                    'await allocate_block(objective="default duration", why_now="test")')
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": code}, tool_call_id="allocation")])
        return ModelResponse(parts=[TextPart("allocated")])

    agent = create_agents("test", "test").director
    with agent.override(model=scripted(model)):
        agent.run_sync("allocate", deps=DirectorDeps(runtime))
    blocks = runtime.manager.blocks()
    assert len(blocks) == 1
    assert blocks[0].start.allocation.seconds == 900
    assert blocks[0].start.allocation.handoff_reserve_seconds == 90


@pytest.mark.parametrize("active_block", [False, True])
def test_director_can_inspect_independent_resources_without_mutating_active_research(active_block):
    """The real tool boundary reports limits before allocation and during a block.

    Existing block inspection requires a block and cannot protect pre-allocation
    planning or the Director CodeMode accounting path.
    """
    from decimal import Decimal
    from pydantic_ai.messages import ToolReturnPart
    from pydantic_ai.usage import RunUsage
    from src.runtime.pydantic_ai.contracts import DirectorDeps

    policy = load_runtime_config(ROOT / "config/runtime.yaml").model_copy(update={"mode": RuntimeMode.DETERMINISTIC})
    runtime = build_harness_runtime(load_models_config(ROOT / "config/models.yaml"), policy, environment={})
    runtime.director_cost_limit = 0.25
    runtime.cycle_cost_limit = 0.75
    runtime.director_tool_limit = 3
    runtime.director_code_limit = 2
    runtime.director_usage = RunUsage(requests=1, cost=Decimal("0.1"))
    block = runtime.manager.allocate("independent investigation", "test") if active_block else None
    state = runtime.research_state.start(block.block_id, block.objective) if block else None
    if block:
        runtime.researcher_budget(block.block_id).requests = 9
    runtime.memory_elapsed = 3
    runtime._counts["memory_questions"] = 2
    before = block.model_dump(mode="json") if block else None
    calls = 0

    async def model(messages, info):
        nonlocal calls
        calls += 1
        if calls == 1:
            return ModelResponse(parts=[ToolCallPart(
                "run_code", {"code": "await inspect_director_resources()"}, tool_call_id="resources")])
        return ModelResponse(parts=[TextPart("reviewed")])

    agent = create_agents("test", "test").director
    with agent.override(model=scripted(model)):
        result = agent.run_sync("Review global allowances", deps=DirectorDeps(runtime), usage=runtime.director_usage)
    returned = next(part.content for message in result.new_messages() for part in message.parts
                    if isinstance(part, ToolReturnPart))
    assert returned["director_cost_limit"] == 0.25 and returned["aggregate_cost_limit"] == 0.75
    assert returned["director"]["reported_cost"] == "0.1" and returned["cost_complete"] is False
    assert returned["director_budgets"]["model_requests"]["attempted"] == 2
    assert returned["aggregate_budgets"]["model_requests"]["attempted"] == (11 if block else 2)
    # Both the snippet and its inner typed tool consume provider-tool allowance.
    assert returned["director_budgets"]["provider_tools"]["remaining"] == 1
    assert returned["director_budgets"]["code_mode_executions"]["remaining"] == 1
    assert returned["memory_semantics"]["questions"]["remaining"] == 18
    assert returned["memory_semantics"]["seconds"]["remaining"] == 17
    assert runtime.manager.blocks() == ((block,) if block else ())
    if block:
        assert block.model_dump(mode="json") == before
        assert runtime.research_state.get(block.block_id) == state


@pytest.mark.parametrize("limit", ["director_tool_limit", "director_code_limit", "snippet_tools"])
def test_zero_director_coding_allowance_denies_allocation_before_effects(limit):
    """Director's independent limits must guard CodeMode and its lifecycle effects."""
    from pydantic_ai.messages import ToolReturnPart
    from src.runtime.pydantic_ai.contracts import DirectorDeps

    policy = load_runtime_config(ROOT / "config/runtime.yaml").model_copy(update={"mode": RuntimeMode.DETERMINISTIC})
    runtime = build_harness_runtime(load_models_config(ROOT / "config/models.yaml"), policy, environment={})
    if limit != "snippet_tools":
        setattr(runtime, limit, 0)
    calls = 0

    async def model(messages, info):
        nonlocal calls
        calls += 1
        if calls == 1:
            return ModelResponse(parts=[ToolCallPart("run_code", {
                "code": 'await allocate_block(objective="must not start", why_now="budget test")'
            }, tool_call_id="denied")])
        return ModelResponse(parts=[TextPart("stopped")])

    agent = create_agents("test", "test", max_tool_calls=0 if limit == "snippet_tools" else 100).director
    with agent.override(model=scripted(model)):
        result = agent.run_sync("Review allowance", deps=DirectorDeps(runtime))
    returned = next(part.content for message in result.new_messages() for part in message.parts
                    if isinstance(part, ToolReturnPart))
    assert returned["retryable"] is False
    assert runtime.manager.blocks() == ()
    assert runtime.researcher_usage == {}


@pytest.mark.parametrize("limit", ["max_provider_tool_calls", "max_code_mode_executions", "max_code_mode_tool_calls"])
def test_zero_framework_budgets_deny_code_before_source_execution(limit, monkeypatch):
    from pydantic_ai.messages import ToolReturnPart

    policy = load_runtime_config(ROOT / "config/runtime.yaml").model_copy(update={"mode": RuntimeMode.DETERMINISTIC})
    runtime = build_harness_runtime(load_models_config(ROOT / "config/models.yaml"), policy, environment={})
    if limit != "max_code_mode_tool_calls":
        setattr(runtime, limit, 0)
    block = runtime.manager.allocate("framework budget", "test")
    effects = []

    async def source(*args, **kwargs):
        effects.append("source")
        raise RuntimeError("source started")

    monkeypatch.setattr(runtime.gdc, "search", source)
    calls = 0

    async def model(messages, info):
        nonlocal calls
        calls += 1
        if calls == 1:
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": 'await acquire_gdc(endpoint="files", filters={}, fields=["file_id"])'}, tool_call_id="denied")])
        return ModelResponse(parts=[TextPart("handoff")])

    agent = create_agents("test", "test", max_tool_calls=0 if limit == "max_code_mode_tool_calls" else 100).researcher
    with agent.override(model=scripted(model)):
        result = agent.run_sync("investigate", deps=ResearcherDeps(runtime, block.block_id))
    returns = [part.content for message in result.new_messages() for part in message.parts if isinstance(part, ToolReturnPart)]
    assert any(isinstance(value, dict) and value.get("retryable") is False for value in returns)
    assert not effects
    assert runtime.resources(block.block_id)["source"]["attempted"] == 0


def test_live_reasoner_requests_consume_researcher_allocation():
    from pydantic_ai.exceptions import UsageLimitExceeded
    from pydantic_ai.models.test import TestModel
    from src.runtime.pydantic_ai.reasoner import BudgetedLiveReasoner

    policy = load_runtime_config(ROOT / "config/runtime.yaml").model_copy(update={"mode": RuntimeMode.DETERMINISTIC})
    runtime = build_harness_runtime(load_models_config(ROOT / "config/models.yaml"), policy, environment={})
    runtime.max_model_requests = 2
    runtime.reasoner = BudgetedLiveReasoner(TestModel(custom_output_args={
        "interpretation": "unknown", "uncertainty": "needs measurement",
        "hypotheses": [{"hypothesis_id": "h", "statement": "possible signal", "within_scope": True, "proposed_test": "measure"}],
    }))
    block = runtime.manager.allocate("Reasoner accounting", "test")
    calls = 0

    async def model(messages, info):
        nonlocal calls
        calls += 1
        return ModelResponse(parts=[ToolCallPart("run_code", {"code": 'await generate_hypotheses(finding="unknown")'}, tool_call_id="reasoner")])

    agent = create_agents("test", "test").researcher
    with agent.override(model=scripted(model)):
        with pytest.raises(UsageLimitExceeded):
            agent.run_sync("investigate", deps=ResearcherDeps(runtime, block.block_id), usage_limits=runtime.usage_limits("researcher"))
    assert calls == 1
    assert runtime.researcher_usage[block.block_id].requests == 1
    assert runtime.reasoner_usage[block.block_id].requests == 1
    assert runtime.total_usage().requests == 2
    assert any(event.event_type == "ReasonerOutput" for event in runtime.manager.ledger(block.block_id).history())


def test_allocation_configuration_rejects_inconsistent_bounds():
    from pydantic import ValidationError
    from src.config.models import BlockConfig

    for options in ({"default_seconds": 3601}, {"min_seconds": 1000}, {"handoff_reserve_seconds": 300}):
        with pytest.raises(ValidationError):
            BlockConfig(**options)


def test_handoff_preserves_in_flight_source_result_and_blocks_next_request():
    from datetime import UTC, datetime, timedelta
    import httpx
    from src.sources.public import GdcPublicSource

    clock = [datetime(2026, 10, 1, tzinfo=UTC)]
    manager = BlockManager(now=lambda: clock[0])
    policy = load_runtime_config(ROOT / "config/runtime.yaml").model_copy(update={"mode": RuntimeMode.DETERMINISTIC})
    runtime = build_harness_runtime(load_models_config(ROOT / "config/models.yaml"), policy, manager=manager, environment={})
    block = manager.allocate("in-flight work", "test")
    requests = []

    async def transport(request):
        requests.append(request)
        clock[0] = block.handoff_at + timedelta(seconds=1)
        return httpx.Response(200, json={"data": {"hits": [{"file_id": "a"}]}})

    runtime.gdc = GdcPublicSource(httpx.MockTransport(transport))
    calls = 0

    async def model(messages, info):
        nonlocal calls
        calls += 1
        if calls == 1:
            code = ('first = await acquire_gdc(endpoint="files", filters={}, fields=["file_id"])\n'
                    'second = await acquire_gdc(endpoint="files", filters={}, fields=["file_id"])\n'
                    'assert second["retryable"] == False\n'
                    'await block_status()\n'
                    'await complete_block(reason="soft handoff")')
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": code}, tool_call_id="handoff")])
        return ModelResponse(parts=[TextPart("done")])

    agent = create_agents("test", "test").researcher
    with agent.override(model=scripted(model)):
        agent.run_sync("investigate", deps=ResearcherDeps(runtime, block.block_id))
    assert len(requests) == 1
    assert len(runtime.acquisitions) == 1
    assert runtime.resources(block.block_id)["source"]["attempted"] == 1
    assert any(e.event_type == "ResearcherHandoffRequested" for e in manager.ledger(block.block_id).history())


def test_duplicate_jev_question_ids_are_rejected_before_provider_dispatch(monkeypatch):
    from typesafe_sdk import SystemOneResponse
    client = TypeSafeJevClient(api_key="fake", model="jev-test")
    calls = []

    def provider(state, questions):
        calls.append(questions)
        return SystemOneResponse.model_validate({"model": "jev-test", "usage": {}, "answers": {"q": {"type": "noul", "noul": 0.7}}})

    monkeypatch.setattr(client._client, "system_one", provider)
    with pytest.raises(JevOperationalFailure):
        client.evaluate({}, (QUESTION, QUESTION))
    assert calls == []


@pytest.mark.parametrize("outcome", ["construction", "decoding", "success"])
def test_jev_call_receipt_preserves_sdk_failures_and_native_semantic_history(outcome, monkeypatch):
    from typesafe_sdk import SystemOneResponse
    from src.persistence.store import SqliteResearchStore
    from src.persistence.repository import ResearchRepository
    from src.persistence.records import RecordKind
    from src.persistence.reconstruct import reconstruct_block
    import src.jev.client as client_module

    manager = BlockManager()
    block = manager.create("inspect signal", "test", ResourceAllocation(seconds=60))
    client = TypeSafeJevClient(api_key="fake", model="jev-requested")
    repository = ResearchRepository(SqliteResearchStore())
    runtime = HarnessRuntime(manager=manager, jev=client, science=ScienceExecutor(), reasoner=DeterministicReasoner(),
                             max_jev_calls=2, max_reasoner_calls=1, repository=repository)
    repository.record_block(block)
    requests = []

    def provider(state, questions):
        requests.append(questions)
        assert questions["c-relevance"].instructions["known_exclusions"]
        assert "missing" in str(questions["c-action"].instructions).lower()
        answers = {"c-relevance": {"type": "noul", "noul": 0.8},
                   "c-action": {"type": "choice", "choice": "NONE", "probabilities": {"ADVANCE": 0.02, "DEFER": 0.08, "NONE": 0.9}, "confidence": 0.9}}
        if outcome == "decoding":
            answers.pop("c-action")
        return SystemOneResponse.model_validate({"model": "jev-resolved", "usage": {"input_tokens": 11, "output_tokens": 7}, "answers": answers})

    monkeypatch.setattr(client._client, "system_one", provider)
    if outcome == "construction":
        spec_for = client_module._spec_for

        def invalid_spec(question):
            return spec_for(question.model_copy(update={"criteria": {"true": object()}}))

        monkeypatch.setattr(client_module, "_spec_for", invalid_spec)
    calls = 0

    async def model(messages, info):
        nonlocal calls
        calls += 1
        if calls == 1:
            code = 'await evaluate_candidate(candidate_id="c", candidate_summary="unknown signal")'
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": code}, tool_call_id="jev")])
        return ModelResponse(parts=[TextPart("done")])

    agent = create_agents("test", "test").researcher
    with agent.override(model=scripted(model)):
        agent.run_sync("inspect signal", deps=ResearcherDeps(runtime, block.block_id))
    view = reconstruct_block(repository.store, block.block_id)
    receipt = view.jev_calls[0]
    assert len(receipt["questions"]) == 2 and len(receipt["question_hashes"]) == 2
    assert receipt["projection_sha256"] == receipt["projection"]["payload_sha256"]
    assert receipt["duration_ms"] >= 0 and receipt["model_requested"] == "jev-requested"
    assert runtime.resources(block.block_id)["jev"]["attempted"] == 1
    assert runtime.resources(block.block_id)["jev_questions"]["attempted"] == 2
    assert not repository.store.records(kind=RecordKind.EVIDENCE)
    if outcome == "success":
        assert receipt["outcome"] == "completed" and receipt["models_resolved"] == ["jev-resolved"]
        assert receipt["reported_metadata"]["usage"] == {"input_tokens": 11, "output_tokens": 7}
        assert receipt["reported_metadata"]["reported_retries"] is None
        history = view.candidate_history[0]
        assert history["candidate_id"] == "c" and history["candidate_summary"] == "unknown signal"
        assert history["action"] == "reject_retain" and history["decisions"][1]["probabilities"]["NONE"] == 0.9
        assert history["call_id"] == receipt["call_id"]
    else:
        assert receipt["outcome"] == "failed" and view.jev_failures and not view.candidate_history
        assert all(f["category"] == "validation" for f in receipt["failures"])
        assert len(requests) == (0 if outcome == "construction" else 1)
    repository.store.close()
