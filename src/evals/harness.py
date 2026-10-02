"""Evaluation harness: compare capability conditions without ranking them.

Each condition runs the same broad direction through a fresh runtime and a fresh
append-only store. The Director still chooses what to do; the only difference is
which capabilities the Researcher may use. No condition is declared best.
"""

from collections.abc import Callable
from time import perf_counter
from typing import Any

from src.block.manager import BlockManager
from src.config.models import ModelsConfig, RuntimeConfig, RuntimeMode
from src.evals.models import ConditionMetrics, EvaluationCondition, EvaluationReport
from src.persistence.records import RecordKind
from src.persistence.repository import ResearchRepository
from src.persistence.store import SqliteResearchStore
from src.persistence.reconstruct import reconstruct_block, effective_cycle
from src.block.models import CycleStatus, DirectorOutcome
from src.autonomous import recover_interrupted_blocks
from src.runtime.cycle import run_cycle
from src.runtime.pydantic_ai.agents import OncoJevAgents, create_configured_agents
from src.runtime.pydantic_ai.contracts import HarnessRuntime
from src.runtime.pydantic_ai.factory import ConfiguredSystem, build_harness_runtime


CONDITIONS: tuple[EvaluationCondition, ...] = (
    EvaluationCondition.SCIENCE_ONLY,
    EvaluationCondition.SCIENCE_REASONER,
    EvaluationCondition.SCIENCE_JEV,
    EvaluationCondition.SCIENCE_JEV_REASONER,
)

Runner = Callable[[ConfiguredSystem, str, ResearchRepository, EvaluationCondition], None]
AgentsFactory = Callable[[], OncoJevAgents]


def apply_condition(runtime: HarnessRuntime, condition: EvaluationCondition) -> HarnessRuntime:
    """Gate semantic capabilities for one condition; science always stays available."""
    runtime.enable_jev = condition in {EvaluationCondition.SCIENCE_JEV, EvaluationCondition.SCIENCE_JEV_REASONER}
    runtime.enable_reasoner = condition in {EvaluationCondition.SCIENCE_REASONER, EvaluationCondition.SCIENCE_JEV_REASONER}
    return runtime


def _metrics(condition: EvaluationCondition, store: SqliteResearchStore, elapsed_seconds: float) -> ConditionMetrics:
    evidence = store.records(kind=RecordKind.EVIDENCE)
    deterministic = all(
        record.payload.get("measurement", {}).get("deterministic") is True for record in evidence
    )
    ledger = [record.payload for record in store.records(kind=RecordKind.LEDGER_EVENT)]
    dossiers = [record.payload for record in store.records(kind=RecordKind.DOSSIER)]
    cycles = [effective_cycle(store, r.payload) for r in store.records(kind=RecordKind.CYCLE)]
    failed = [c for c in cycles if c.get("status") == "failed"]
    incomplete = [c for c in cycles if c.get("status") == "incomplete"]
    return ConditionMetrics(
        condition=condition,
        blocks=len(store.block_ids()),
        measurements=len(store.records(kind=RecordKind.MEASUREMENT)),
        evidence=len({r.record_id for r in evidence}),
        unique_analysis_outcomes=len({r.payload["measurement"]["analysis_key"] for r in evidence}) if evidence and all(r.payload.get("measurement",{}).get("analysis_key") for r in evidence) else None,
        declared_replication_outcomes=sum(bool(r.payload.get("measurement",{}).get("replication_id")) for r in evidence),
        deterministic_evidence=deterministic,
        jev_executions=sum(1 for payload in ledger if payload.get("event_type") == "JevExecution"),
        reasoner_outputs=sum(1 for payload in ledger if payload.get("event_type") == "ReasonerOutput"),
        dossiers=len(dossiers),
        hypotheses=sum(len(payload.get("hypotheses", [])) for payload in dossiers),
        proposed_new_blocks=sum(len(payload.get("recommended_next_blocks", [])) for payload in dossiers),
        has_preferred_continuation=any(bool(payload.get("preferred_continuation")) for payload in dossiers),
        records=store.count(),
        source_bound_evidence=sum(1 for record in evidence if record.payload.get("measurement", {}).get("origin") in {"source", "sandbox"}),
        jev_failures=len(store.records(kind=RecordKind.JEV_FAILURE)),
        verified_replications=sum(r.payload.get('outcome') == 'replicated' and r.payload.get('independence') == 'observed_disjoint_complete_case_queries'
            and r.payload.get('confirmation_access') == 'fresh_local_query' for r in store.records(kind=RecordKind.FOLLOWUP_RESULT)),
        invalid_designs=sum(r.payload.get('stage') == 'invalid' for r in store.records(kind=RecordKind.SCIENTIFIC_ATTEMPT)),
        memory_retrievals=len(store.records(kind=RecordKind.MEMORY_RETRIEVAL)),
        completed_blocks=sum(reconstruct_block(store, block_id).complete for block_id in store.block_ids()),
        status=CycleStatus.FAILED if failed else CycleStatus.INCOMPLETE if incomplete else CycleStatus.COMPLETE,
        error_type=(failed or incomplete or [{}])[-1].get("error_type"),
        failed_cycles=len(failed), incomplete_cycles=len(incomplete),
        cycles=len(cycles),
        elapsed_seconds=elapsed_seconds,
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
    store = SqliteResearchStore()
    repository = ResearchRepository(store)
    started = perf_counter()
    try:
        try:
            runtime = build_harness_runtime(models, policy, manager=manager, environment=environment, repository=repository)
            runtime.mission_id = condition.value
            apply_condition(runtime, condition)
            agents = (agents_factory or (lambda: create_configured_agents(models, policy.director.max_code_mode_tool_calls,
                                                                          policy.block.max_code_mode_tool_calls)))()
            runtime.researcher = agents.researcher
            system = ConfiguredSystem(agents=agents, runtime=runtime, mode=policy.mode)
            if runner is not None:
                runner(system, direction, repository, condition)
            else:
                run_cycle(system, direction, repository=repository, mission_id=condition.value)
            if not store.records(kind=RecordKind.CYCLE):
                for block in manager.blocks():
                    if store.latest(RecordKind.BLOCK, block_id=block.block_id) is None:
                        repository.record_block(block)
                pending = store.latest(RecordKind.CYCLE_START)
                repository.record_cycle(pending.payload.get("mission_id", pending.record_id) if pending else condition.value, policy.mode.value, direction,
                                        tuple(b.block_id for b in manager.blocks()), status=CycleStatus.INCOMPLETE,
                                        error_type="MissingCycleReceipt", director_outcome=DirectorOutcome.UNKNOWN,
                                        cycle_id=pending.record_id if pending else None)
                recover_interrupted_blocks(repository)
        except Exception as error:
            # run_cycle already writes its receipt. Custom runners may fail
            # outside that owner; persist their partial work without duplicating it.
            if not store.records(kind=RecordKind.CYCLE):
                for block in manager.blocks():
                    if store.latest(RecordKind.BLOCK, block_id=block.block_id) is None:
                        repository.record_block(block)
                pending = store.latest(RecordKind.CYCLE_START)
                repository.record_cycle(pending.payload.get("mission_id", pending.record_id) if pending else condition.value, policy.mode.value, direction, tuple(b.block_id for b in manager.blocks()),
                                        status=CycleStatus.FAILED, error_type=type(error).__name__, director_outcome=DirectorOutcome.FAILED,
                                        cycle_id=pending.record_id if pending else None)
                recover_interrupted_blocks(repository)
            metrics = _metrics(condition, store, perf_counter() - started)
            return metrics.model_copy(update={"status": CycleStatus.FAILED, "error_type": type(error).__name__})
        return _metrics(condition, store, perf_counter() - started)
    finally:
        store.close()


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
    return EvaluationReport(direction=direction, mode=policy.mode.value, conditions=metrics)


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
