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
from src.reasoner.service import DeterministicReasoner, ReasonerService
from src.runtime.pydantic_ai.agents import OncoJevAgents, create_configured_agents
from src.runtime.pydantic_ai.contracts import HarnessRuntime
from src.runtime.pydantic_ai.providers import configured_model, model_settings
from src.runtime.pydantic_ai.telemetry import configure_agent_telemetry
from src.runtime.pydantic_ai.reasoner import BudgetedLiveReasoner
from src.science.execution import ScienceExecutor
from src.science.sandbox import DockerScientificSandbox, SandboxPolicy
from src.runtime.paths import workspace_root
from src.oncolab.registry import OncoLabVerificationRecord
from src.persistence.records import RecordKind
from src.persistence.references import resolve_reference
from src.sources.public import GdcPublicSource, PublicLiteratureSource, XenaPublicSource
from src.memory.service import ResearchMemory


def build_jev_client(models: ModelsConfig, mode: RuntimeMode, environment: dict[str, str] | None = None, policy=None) -> JevClient:
    """Live TypeSafe only when the mode is live and a credential is actually present."""
    source = environment if environment is not None else os.environ
    if resolve_mode(mode, source) is RuntimeMode.LIVE:
        return TypeSafeJevClient(
            api_key=source.get("TYPESAFE_API_KEY"),
            model=models.jev.model,
            http2=models.jev.http2,
            base_url=models.jev.api_base,
            max_questions=policy.jev.max_questions_per_call if policy is not None else 100,
            max_payload_bytes=policy.jev.max_payload_bytes if policy is not None else 131072,
        )
    return DeterministicJevClient()


def build_reasoner(models: ModelsConfig, mode: RuntimeMode, environment: dict[str, str] | None = None) -> ReasonerService:
    """The Reasoner is a separate sub-agent in live mode and a fixture otherwise."""
    source = environment if environment is not None else os.environ
    if resolve_mode(mode, source) is RuntimeMode.LIVE:
        configure_agent_telemetry()
        return BudgetedLiveReasoner(configured_model(models.reasoner), model_settings(models.reasoner))
    return DeterministicReasoner()


@dataclass(frozen=True)
class ConfiguredSystem:
    agents: OncoJevAgents
    runtime: HarnessRuntime
    mode: RuntimeMode


def bind_repository(runtime: HarnessRuntime, repository) -> None:
    """Seed the shared Index from resolvable durable receipts, without resuming work."""
    runtime.repository = repository
    if repository is not None:
        ResearchMemory(repository.store).backfill()
        for saved in repository.store.records(kind=RecordKind.VERIFICATION):
            record = OncoLabVerificationRecord.model_validate(saved.payload)
            resolve_reference(repository.store, record.execution_reference)
        runtime.initialize_institution()
        from src.oncolab.governance import review_pending
        if review_pending(runtime.institution):
            runtime.retain_export("registry_review_boundary")
        runtime.index_for()


def build_harness_runtime(
    models: ModelsConfig,
    policy: RuntimeConfig,
    *,
    manager: BlockManager | None = None,
    environment: dict[str, str] | None = None,
    repository=None,
    resources=None,
) -> HarnessRuntime:
    source = environment if environment is not None else os.environ
    mode = resolve_mode(policy.mode, source)
    manager = manager or BlockManager()
    manager.policy = policy.block
    runtime = HarnessRuntime(
        manager=manager,
        jev=build_jev_client(models, mode, source, policy),
        science=ScienceExecutor(),
        reasoner=build_reasoner(models, mode, source),
        max_tool_calls=policy.block.max_tool_calls,
        max_model_requests=policy.block.max_model_requests,
        max_provider_tool_calls=policy.block.max_provider_tool_calls,
        max_code_mode_executions=policy.block.max_code_mode_executions,
        max_jev_questions=policy.block.max_jev_questions,
        projection_max_items=policy.jev.projection_max_items,
        projection_max_payload_bytes=policy.jev.projection_max_payload_bytes,
        director_event_turn_limit=policy.director.max_event_turns,
        director_review_interval_seconds=policy.director.program_review_interval_seconds,
        director_request_limit=policy.director.max_model_requests,
        director_tool_limit=policy.director.max_provider_tool_calls,
        director_code_limit=policy.director.max_code_mode_executions,
        director_cost_limit=policy.director.max_cost,
        cycle_request_limit=policy.cycle.max_model_requests,
        cycle_tool_limit=policy.cycle.max_provider_tool_calls,
        cycle_cost_limit=policy.cycle.max_cost,
        handoff_reserve_seconds=policy.block.handoff_reserve_seconds,
        max_cost=policy.block.max_cost,
        max_jev_calls=policy.block.max_jev_calls,
        max_reasoner_calls=policy.block.max_reasoner_calls,
        max_reasoner_model_requests=policy.block.max_reasoner_model_requests,
        max_source_calls=policy.block.max_source_calls,
        max_sandbox_calls=policy.block.max_sandbox_calls,
        oncolab_search_k=policy.oncolab.search_k,
        memory_limit=policy.director.retrieval_k,
        oncolab_candidate_k=policy.oncolab.candidate_k,
        memory_jev_calls=policy.director.max_memory_jev_calls,
        memory_jev_questions=policy.director.max_memory_jev_questions,
        memory_jev_bytes=policy.director.max_memory_jev_bytes,
        memory_jev_seconds=policy.director.max_memory_jev_seconds,
        sandbox=DockerScientificSandbox(SandboxPolicy(image=policy.sandbox.image, cpu=policy.sandbox.cpu, memory_mb=policy.sandbox.memory_mb, timeout_seconds=policy.sandbox.timeout_seconds)),
        gdc=GdcPublicSource(max_download_bytes=policy.block.max_download_bytes),
        xena=XenaPublicSource(max_download_bytes=policy.block.max_download_bytes),
        literature=PublicLiteratureSource(max_download_bytes=policy.block.max_download_bytes),
    )
    if resources is not None:
        runtime.service_resources = resources
    else:
        from src.runtime.resources import ServiceResources
        runtime.service_resources = ServiceResources(max_file_bytes=policy.block.max_download_bytes,
            max_block_download_bytes=policy.resources.max_block_download_bytes,
            max_service_download_bytes=policy.resources.max_service_download_bytes,
            max_workspace_bytes=policy.resources.max_workspace_bytes,
            max_durable_artifact_bytes=policy.resources.max_durable_artifact_bytes,
            minimum_free_disk_bytes=policy.resources.minimum_free_disk_bytes)
    def meter_download(byte_count):
        active = runtime.active_research
        owner = active.block_id if active else "unassigned"
        try:
            runtime.service_resources.charge_download(owner, byte_count)
        except ValueError as error:
            if active:
                runtime.append_event(owner, "ResourceRejected", getattr(error, "directive", {"reason": str(error)}))
            raise
        finally:
            if active:
                runtime.append_event(owner, "DownloadUsage", {"bytes": byte_count,
                    "service_consumed_bytes": runtime.service_resources.downloaded_bytes})
    for client in (runtime.gdc, runtime.xena, runtime.literature):
        client.meter = meter_download
    from src.oncolab.discovery import ExternalDiscovery
    runtime.external_discovery = ExternalDiscovery()
    bind_repository(runtime, repository)
    def reserve_file(owner, declared):
        from pathlib import Path
        from src.runtime.resources import ResourceRejected
        root = Path(__file__).resolve().parents[3]
        workspace = workspace_root(root) / owner
        if workspace.exists() and (workspace.is_symlink() or workspace.is_junction()):
            raise ResourceRejected("workspace capacity cannot follow linked paths", 0)
        used = 0
        if workspace.exists():
            for entry in workspace.rglob("*"):
                if entry.is_symlink() or entry.is_junction():
                    raise ResourceRejected("workspace capacity cannot follow linked paths", 0)
                if entry.is_file():
                    used += entry.stat().st_size
        durable = 0
        paths = [workspace]
        if runtime.repository is not None:
            durable = sum(r.payload.get('size_bytes', 0) for r in runtime.repository.store.records(kind=RecordKind.SCIENTIFIC_ARTIFACT))
            if runtime.repository.store.path is not None:
                paths.append(runtime.repository.store.path.parent)
        return runtime.service_resources.reserve_download(owner, declared, workspace_used=used,
            durable_used=durable, paths=tuple(paths), archive_limit=policy.retention.max_archive_bytes)
    if policy.sandbox.provider == "local_venv":
        from src.science.local import LocalVenvScientificBackend
        from pathlib import Path
        runtime.sandbox = LocalVenvScientificBackend(workspace_root(Path(__file__).resolve().parents[3]), runtime.sandbox.policy)
    runtime.gdc.reserve = reserve_file
    runtime.gdc.transfer_receipt = lambda owner, detail: runtime.append_event(owner, "DataTransferReceipt", detail)
    return runtime


def build_system(
    models: ModelsConfig,
    policy: RuntimeConfig,
    *,
    max_tool_calls: int | None = None,
    manager: BlockManager | None = None,
    environment: dict[str, str] | None = None,
    repository=None,
    director=None,
    resources=None,
) -> ConfiguredSystem:
    """Wire the autonomous live system; offline fixtures are constructed explicitly in tests."""
    if policy.mode is not RuntimeMode.LIVE:
        raise RuntimeError("build_system requires live mode; deterministic fixtures must be explicit")
    resolve_mode(policy.mode, environment)
    director_code = policy.director.max_code_mode_tool_calls
    researcher_code = policy.block.max_code_mode_tool_calls
    if max_tool_calls is not None:
        director_code = min(director_code, max_tool_calls)
        researcher_code = min(researcher_code, max_tool_calls)
    agents = create_configured_agents(models, director_code, researcher_code, director=director)
    runtime = build_harness_runtime(models, policy, manager=manager, environment=environment, repository=repository, resources=resources)
    runtime.researcher_factory = agents.fresh_researcher
    return ConfiguredSystem(agents=agents, runtime=runtime, mode=RuntimeMode.LIVE)
