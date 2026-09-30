"""Evaluation harness: compare capability conditions without ranking them.

Each condition runs the same broad direction through a fresh runtime and a fresh
append-only store. The Director still chooses what to do; the only difference is
which capabilities the Researcher may use. No condition is declared best.
"""

from collections.abc import Callable
from typing import Any

from src.block.manager import BlockManager
from src.config.models import ModelsConfig, RuntimeConfig, RuntimeMode
from src.evals.models import ConditionMetrics, EvaluationCondition, EvaluationReport
from src.persistence.records import RecordKind
from src.persistence.repository import ResearchRepository
from src.persistence.store import SqliteResearchStore
from src.runtime.cycle import run_cycle
from src.runtime.pydantic_ai.agents import OncoJevAgents, create_configured_agents
from src.runtime.pydantic_ai.contracts import HarnessRuntime
from src.runtime.pydantic_ai.factory import ConfiguredSystem, build_harness_runtime


CONDITIONS: tuple[EvaluationCondition, ...] = (
    EvaluationCondition.SCIENCE_ONLY,
    EvaluationCondition.SCIENCE_REASONER,
    EvaluationCondition.SCIENCE_JEV_REASONER,
)

Runner = Callable[[ConfiguredSystem, str, ResearchRepository, EvaluationCondition], None]
AgentsFactory = Callable[[], OncoJevAgents]


def apply_condition(runtime: HarnessRuntime, condition: EvaluationCondition) -> HarnessRuntime:
    """Gate semantic capabilities for one condition; science always stays available."""
    runtime.enable_jev = condition is EvaluationCondition.SCIENCE_JEV_REASONER
    runtime.enable_reasoner = condition is not EvaluationCondition.SCIENCE_ONLY
    return runtime


def _metrics(condition: EvaluationCondition, store: SqliteResearchStore) -> ConditionMetrics:
    evidence = store.records(kind=RecordKind.EVIDENCE)
    deterministic = all(
        record.payload.get("measurement", {}).get("deterministic") is True for record in evidence
    )
    ledger = [record.payload for record in store.records(kind=RecordKind.LEDGER_EVENT)]
    dossiers = [record.payload for record in store.records(kind=RecordKind.DOSSIER)]
    return ConditionMetrics(
        condition=condition,
        blocks=len(store.records(kind=RecordKind.BLOCK)),
        measurements=len(store.records(kind=RecordKind.MEASUREMENT)),
        evidence=len(evidence),
        deterministic_evidence=deterministic,
        jev_executions=sum(1 for payload in ledger if payload.get("event_type") == "JevExecution"),
        reasoner_outputs=sum(1 for payload in ledger if payload.get("event_type") == "ReasonerOutput"),
        dossiers=len(dossiers),
        hypotheses=sum(len(payload.get("hypotheses", [])) for payload in dossiers),
        proposed_new_blocks=sum(len(payload.get("recommended_next_blocks", [])) for payload in dossiers),
        has_preferred_continuation=any(bool(payload.get("preferred_continuation")) for payload in dossiers),
        records=store.count(),
    )


def evaluate_condition(
    direction: str,
    condition: EvaluationCondition,
    *,
    models: ModelsConfig,
    policy: RuntimeConfig,
    agents_factory: AgentsFactory | None = None,
    environment: dict[str, str] | None = None,
    runner: Runner | None = None,
) -> ConditionMetrics:
    manager = BlockManager()
    runtime = build_harness_runtime(models, policy, manager=manager, environment=environment)
    apply_condition(runtime, condition)
    agents = (agents_factory or (lambda: create_configured_agents(models, 100)))()
    runtime.researcher = agents.researcher
    system = ConfiguredSystem(agents=agents, runtime=runtime, mode=RuntimeMode.DETERMINISTIC)
    store = SqliteResearchStore()
    repository = ResearchRepository(store)
    if runner is not None:
        runner(system, direction, repository, condition)
    else:
        run_cycle(system, direction, repository=repository, mission_id=condition.value)
    return _metrics(condition, store)


def evaluate_direction(
    direction: str,
    *,
    models: ModelsConfig,
    policy: RuntimeConfig,
    agents_factory: AgentsFactory | None = None,
    environment: dict[str, str] | None = None,
    runner: Runner | None = None,
    conditions: tuple[EvaluationCondition, ...] = CONDITIONS,
) -> EvaluationReport:
    metrics = tuple(
        evaluate_condition(
            direction,
            condition,
            models=models,
            policy=policy,
            agents_factory=agents_factory,
            environment=environment,
            runner=runner,
        )
        for condition in conditions
    )
    return EvaluationReport(direction=direction, mode="deterministic", conditions=metrics)


def evaluate_corpus(
    directions: tuple[str, ...],
    *,
    models: ModelsConfig,
    policy: RuntimeConfig,
    agents_factory: AgentsFactory | None = None,
    environment: dict[str, str] | None = None,
    runner: Runner | None = None,
) -> tuple[EvaluationReport, ...]:
    return tuple(
        evaluate_direction(
            direction,
            models=models,
            policy=policy,
            agents_factory=agents_factory,
            environment=environment,
            runner=runner,
        )
        for direction in directions
    )
