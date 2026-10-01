"""One composition point that chooses deterministic or live services.

Every role model comes from `config/models.yaml`; this module never hardcodes a
model, provider, or credential. Autonomous mode fails closed unless every live
provider credential is present. Deterministic services are explicit test fixtures.
"""

from dataclasses import dataclass
import os

from src.block.manager import BlockManager
from src.config.authentication import resolve_mode
from src.config.models import ModelsConfig, RuntimeConfig, RuntimeMode
from src.jev.client import DeterministicJevClient, JevClient, TypeSafeJevClient
from src.reasoner.agent import LiveReasoner
from src.reasoner.service import DeterministicReasoner, ReasonerService
from src.runtime.pydantic_ai.agents import OncoJevAgents, create_configured_agents
from src.runtime.pydantic_ai.contracts import HarnessRuntime
from src.runtime.pydantic_ai.providers import configured_model, model_settings
from src.science.execution import ScienceExecutor
from src.science.sandbox import DockerScientificSandbox, SandboxPolicy
from src.sources.public import GdcPublicSource, PublicLiteratureSource, XenaPublicSource


def build_jev_client(models: ModelsConfig, mode: RuntimeMode, environment: dict[str, str] | None = None) -> JevClient:
    """Live TypeSafe only when the mode is live and a credential is actually present."""
    source = environment if environment is not None else os.environ
    if resolve_mode(mode, source) is RuntimeMode.LIVE:
        return TypeSafeJevClient(
            api_key=source.get("TYPESAFE_API_KEY"),
            model=models.jev.model,
            http2=models.jev.http2,
            base_url=models.jev.api_base,
        )
    return DeterministicJevClient()


def build_reasoner(models: ModelsConfig, mode: RuntimeMode, environment: dict[str, str] | None = None) -> ReasonerService:
    """The Reasoner is a separate sub-agent in live mode and a fixture otherwise."""
    source = environment if environment is not None else os.environ
    if resolve_mode(mode, source) is RuntimeMode.LIVE:
        return LiveReasoner(configured_model(models.reasoner), model_settings(models.reasoner))
    return DeterministicReasoner()


@dataclass(frozen=True)
class ConfiguredSystem:
    agents: OncoJevAgents
    runtime: HarnessRuntime
    mode: RuntimeMode


def build_harness_runtime(
    models: ModelsConfig,
    policy: RuntimeConfig,
    *,
    manager: BlockManager | None = None,
    environment: dict[str, str] | None = None,
) -> HarnessRuntime:
    source = environment if environment is not None else os.environ
    mode = resolve_mode(policy.mode, source)
    return HarnessRuntime(
        manager=manager or BlockManager(),
        jev=build_jev_client(models, mode, source),
        science=ScienceExecutor(),
        reasoner=build_reasoner(models, mode, source),
        max_tool_calls=policy.block.max_tool_calls,
        max_model_requests=policy.block.max_model_requests,
        handoff_reserve_seconds=policy.block.handoff_reserve_seconds,
        max_cost=policy.block.max_cost,
        max_jev_calls=int(policy.block["max_jev_calls"] or 4),
        max_reasoner_calls=int(policy.block["max_reasoner_calls"] or 2),
        max_source_calls=int(policy.block["max_source_calls"] or 20),
        max_sandbox_calls=int(policy.block["max_sandbox_calls"] or 2),
        oncolab_search_k=policy.oncolab.search_k,
        sandbox=DockerScientificSandbox(SandboxPolicy(image=policy.sandbox.image, cpu=policy.sandbox.cpu, memory_mb=policy.sandbox.memory_mb, timeout_seconds=policy.sandbox.timeout_seconds)),
        gdc=GdcPublicSource(max_download_bytes=policy.block.max_download_bytes),
        xena=XenaPublicSource(max_download_bytes=policy.block.max_download_bytes),
        literature=PublicLiteratureSource(max_download_bytes=policy.block.max_download_bytes),
    )


def build_system(
    models: ModelsConfig,
    policy: RuntimeConfig,
    *,
    max_tool_calls: int = 100,
    manager: BlockManager | None = None,
    environment: dict[str, str] | None = None,
) -> ConfiguredSystem:
    """Wire the autonomous live system; offline fixtures are constructed explicitly in tests."""
    if policy.mode is not RuntimeMode.LIVE:
        raise RuntimeError("build_system requires live mode; deterministic fixtures must be explicit")
    resolve_mode(policy.mode, environment)
    agents = create_configured_agents(models, max_tool_calls)
    runtime = build_harness_runtime(models, policy, manager=manager, environment=environment)
    runtime.researcher_factory = agents.fresh_researcher
    return ConfiguredSystem(agents=agents, runtime=runtime, mode=RuntimeMode.LIVE)
