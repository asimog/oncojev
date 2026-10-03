"""A complete Director -> Researcher research cycle.

The Director receives a broad direction, not a script. It searches the OncoLab
Index, allocates a bounded block, and launches the independent Researcher agent.
Dossiers are assembled deterministically from the append-only ledger and, when a
repository is supplied, the whole cycle is persisted as typed records.
"""

import asyncio
from time import perf_counter
from dataclasses import dataclass
from uuid import uuid4

from src.block.models import BlockStatus, CycleStatus, DirectorOutcome, ServiceResearchState, RunOutcome, run_outcome
from src.config.models import RuntimeMode
from src.dossier.builder import build_dossier
from src.dossier.models import JevBlockDossier
from src.persistence.repository import ResearchRepository
from src.persistence.records import RecordKind
from src.runtime.pydantic_ai.factory import ConfiguredSystem, bind_repository
from src.runtime.pydantic_ai.contracts import DirectorDeps, is_director_truncation, is_director_event_yield
from src.provenance import canonical_bytes


DIRECTOR_PROMPT = (
    "Broad research direction: {direction}\n"
    "Determine for yourself what to do. Read recent research memory, search the OncoLab Index for relevant capabilities, "
    "allocate exactly one bounded block with a defensible objective, then launch the Researcher "
    "inside it. Launch returns promptly; perform bounded global planning using immutable views. "
    "Do not prescribe a fixed pipeline. Python awaits and persists the real block outcome."
)


@dataclass(frozen=True)
class CycleResult:
    direction: str
    mode: RuntimeMode
    director_output: str
    block_ids: tuple[str, ...]
    dossiers: tuple[JevBlockDossier, ...]
    status: CycleStatus = CycleStatus.COMPLETE
    director_outcome: DirectorOutcome = DirectorOutcome.RETURNED
    director_error_type: str | None = None


class CycleFailed(RuntimeError):
    """The ledger contradicts a normal agent return."""

    def __init__(self, error_type: str):
        self.error_type = error_type
        super().__init__(f"Research cycle failed: {error_type}")


async def run_cycle_async(
    system: ConfiguredSystem,
    direction: str,
    *,
    repository: ResearchRepository | None = None,
    mission_id: str | None = None,
) -> CycleResult:
    """Run one bounded cycle; the Director chooses scope and the Researcher investigates."""
    manager = system.runtime.manager
    mission_id = mission_id or f"mission-{uuid4()}"
    cycle_id = f"cycle-{uuid4()}"
    bind_repository(system.runtime, repository)
    system.runtime.mission_id = mission_id
    system.runtime.cycle_id = cycle_id
    before = {block.block_id for block in manager.blocks()}
    if repository is not None:
        repository.record_cycle_start(mission_id, system.mode.value, direction, cycle_id=cycle_id)
    director_output = ""
    director_outcome = DirectorOutcome.RETURNED
    director_error = None
    failure = None
    error_type = None
    cancelled = False
    system.runtime.set_service_state(ServiceResearchState.ALLOCATING, cause=cycle_id)
    director_started = perf_counter()
    system.runtime.director_turn_started = director_started
    system.runtime.director_supervising_turn = True
    system.runtime.director_context = None
    system.runtime.director_terminal_yield = False
    system.runtime.director_request_error = None
    try:
        limits = system.runtime.usage_limits("director")
        memory = system.runtime.memory_service()
        from src.runtime.pydantic_ai.search_tools import semantic_memory_context_async
        context = await semantic_memory_context_async(system.runtime,direction,limit=min(5,system.runtime.memory_limit))
        prompt = DIRECTOR_PROMPT.format(direction=direction) + "\nRetrieved structured memory (context, not evidence):\n" + canonical_bytes(context).decode("utf-8")
        result = await system.agents.director.run(prompt,
                                                deps=DirectorDeps(system.runtime), usage_limits=limits, usage=system.runtime.director_usage)
        director_output = result.output
    except asyncio.CancelledError:
        cancelled = True
        director_error = "CancelledError"
        director_outcome = DirectorOutcome.FAILED
        failure = CycleFailed("ServiceShutdown")
        error_type = "ServiceShutdown"
    except Exception as error:
        if system.runtime.director_request_error is not None:
            error = system.runtime.director_request_error
        director_error = type(error).__name__
        # These installed exception types identify budget exhaustion or a token-
        # truncated tool call. Generic UnexpectedModelBehavior is a hard failure.
        if system.runtime.director_terminal_yield and is_director_event_yield(error):
            director_outcome = DirectorOutcome.INTERRUPTED
            director_error = "ResearcherTerminalEvent"
        elif is_director_truncation(error):
            director_outcome = DirectorOutcome.TRUNCATED
        else:
            director_outcome = DirectorOutcome.FAILED
            failure = error
        error_type = None if director_outcome is DirectorOutcome.INTERRUPTED else director_error

    system.runtime.director_supervising_turn = False
    system.runtime.director_context = None
    system.runtime.director_turn_seconds += perf_counter() - director_started
    system.runtime.director_turn_started = None
    new_blocks = tuple(block for block in manager.blocks() if block.block_id not in before)
    for block in new_blocks:
        if director_error:
            system.runtime.append_event(block.block_id, "DirectorYieldedForResearchEvent" if director_outcome is DirectorOutcome.INTERRUPTED else "DirectorRunTruncated" if director_outcome is DirectorOutcome.TRUNCATED else "DirectorRunFailed", {"error_type": director_error})

    allocation_rejected = any(e.event_type == "DirectorAllocationRejected" for b in new_blocks for e in manager.ledger(b.block_id).history())
    if len(new_blocks) != 1 or allocation_rejected:
        failure = failure or CycleFailed("InvalidBlockCount")
        error_type = error_type or "InvalidBlockCount"
    elif failure is None or system.runtime.active_research is not None:
        block = new_blocks[0]
        events = manager.ledger(block.block_id).history()
        if not any(event.event_type == "ResearcherRunStarted" for event in events):
            try:
                system.runtime.schedule_researcher(block.block_id, "python_orchestrator")
            except Exception as error:
                system.runtime.append_event(block.block_id, "ResearcherRunFailed", {"error_type": type(error).__name__})
                failure = error
                error_type = type(error).__name__
    active = system.runtime.active_research
    if active is not None:
        if not active.task.done():
            system.runtime.set_service_state(ServiceResearchState.WAITING_FOR_RESEARCH_EVENT, cause=active.run_id)
        from src.runtime.pydantic_ai.lifecycle import wait_for_research
        try:
            await wait_for_research(system.runtime, system.agents.director, direction,
                allow_global_work=failure is None and not cancelled and director_outcome is not DirectorOutcome.TRUNCATED)
        except asyncio.CancelledError:
            cancelled = True
            while not active.task.done():
                try:
                    await asyncio.shield(active.task)
                except asyncio.CancelledError:
                    cancelled = True
        if active.error is not None:
            failure = active.error
            error_type = type(active.error).__name__
    for block in new_blocks:
        if failure is None and run_outcome(manager.ledger(block.block_id).history()) is not RunOutcome.COMPLETED:
            failure = CycleFailed("ResearcherRunIncomplete")
            error_type = "ResearcherRunIncomplete"

    status = CycleStatus.FAILED if failure else (CycleStatus.INCOMPLETE if director_outcome is DirectorOutcome.TRUNCATED else CycleStatus.COMPLETE)
    dossiers = []
    for original in new_blocks:
        block = manager.block(original.block_id)
        system.runtime.append_event(block.block_id, "ModelUsage", system.runtime.usage_summary())
        events = manager.ledger(block.block_id).history()
        if active is not None and active.block_id == block.block_id and active.dossier is not None:
            dossiers.append(active.dossier)
            continue
        if failure:
            reason = "researcher_failed" if run_outcome(events) is RunOutcome.FAILED else (
                "invalid_block_count" if len(new_blocks) != 1 else "director_failed" if director_outcome is DirectorOutcome.FAILED else "researcher_incomplete")
            block = manager.finalize(block, BlockStatus.FAILED, reason)
        state = None
        try:
            state = system.runtime.research_state.get(block.block_id)
        except KeyError:
            pass
        evidence_records={r.record_id:r.payload for r in repository.store.records(kind=RecordKind.EVIDENCE,block_id=block.block_id)} if repository else {i:e.model_dump(mode="json") for i,e in system.runtime.evidence.items() if state and i in state.evidence_ids}
        dossier = build_dossier(block, events, state, block.termination_reason or "unknown", evidence_records=evidence_records)
        if repository is not None:
            repository.record_terminal(block, dossier)
        system.runtime.append_event(block.block_id, "DossierHandoff", {"block_id": block.block_id, "status": block.status.value})
        dossiers.append(dossier)
    if repository is not None:
        if director_output:
            repository.record_research_memory(mission_id, director_output[:2000], ("run-cycle-v3", status.value, direction, *(b.block_id for b in new_blocks)), cycle_id=cycle_id)
        repository.record_cycle(mission_id, system.mode.value, direction, tuple(b.block_id for b in new_blocks),
                                status=status, error_type=error_type, director_outcome=director_outcome, director_error_type=director_error, cycle_id=cycle_id)
        system.runtime.memory_service().backfill()
    if cancelled:
        raise asyncio.CancelledError
    if failure is not None:
        raise failure
    return CycleResult(direction, system.mode, director_output, tuple(b.block_id for b in new_blocks),
                       tuple(dossiers), status, director_outcome, director_error)


def run_cycle(system: ConfiguredSystem, direction: str, *, repository=None, mission_id=None) -> CycleResult:
    """Synchronous CLI boundary; all run ownership stays on one event loop."""
    return asyncio.run(run_cycle_async(system, direction, repository=repository, mission_id=mission_id))
