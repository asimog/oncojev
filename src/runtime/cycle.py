"""A complete Director -> Researcher research cycle.

The Director receives a broad direction, not a script. It searches the OncoLab
Index, allocates a bounded block, and launches the independent Researcher agent.
Dossiers are assembled deterministically from the append-only ledger and, when a
repository is supplied, the whole cycle is persisted as typed records.
"""

from dataclasses import dataclass
from uuid import uuid4

from src.block.models import BlockStatus, CycleStatus, DirectorOutcome, RunOutcome, run_outcome
from src.config.models import RuntimeMode
from src.dossier.builder import build_dossier
from src.dossier.models import JevBlockDossier
from src.persistence.repository import ResearchRepository
from src.runtime.pydantic_ai.factory import ConfiguredSystem, bind_repository
from src.runtime.pydantic_ai.contracts import DirectorDeps, ResearcherDeps, is_director_truncation


DIRECTOR_PROMPT = (
    "Broad research direction: {direction}\n"
    "Determine for yourself what to do. Read recent research memory, search the OncoLab Index for relevant capabilities, "
    "allocate exactly one bounded block with a defensible objective, then launch the Researcher "
    "inside it. Do not prescribe a fixed pipeline. When the block is complete, report a short summary."
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


def run_cycle(
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
    try:
        limits = system.runtime.usage_limits("director")
        result = system.agents.director.run_sync(DIRECTOR_PROMPT.format(direction=direction),
                                                deps=DirectorDeps(system.runtime), usage_limits=limits, usage=system.runtime.director_usage)
        director_output = result.output
    except Exception as error:
        director_error = type(error).__name__
        # These installed exception types identify budget exhaustion or a token-
        # truncated tool call. Generic UnexpectedModelBehavior is a hard failure.
        if is_director_truncation(error):
            director_outcome = DirectorOutcome.TRUNCATED
        else:
            director_outcome = DirectorOutcome.FAILED
            failure = error
        error_type = director_error

    new_blocks = tuple(block for block in manager.blocks() if block.block_id not in before)
    for block in new_blocks:
        if director_error:
            system.runtime.append_event(block.block_id, "DirectorRunTruncated" if director_outcome is DirectorOutcome.TRUNCATED else "DirectorRunFailed", {"error_type": director_error})

    if len(new_blocks) != 1:
        failure = failure or CycleFailed("InvalidBlockCount")
        error_type = error_type or "InvalidBlockCount"
    elif failure is None:
        block = new_blocks[0]
        events = manager.ledger(block.block_id).history()
        if not any(event.event_type == "ResearcherRunStarted" for event in events):
            try:
                system.runtime.start_researcher(block.block_id, "python_orchestrator")
                researcher = system.runtime.researcher_factory(block.block_id) if system.runtime.researcher_factory else system.agents.fresh_researcher(block.block_id)
                researcher.run_sync(f"Investigate block {block.block_id}: {block.objective}", deps=ResearcherDeps(system.runtime, block.block_id),
                                    usage=system.runtime.researcher_budget(block.block_id), usage_limits=system.runtime.usage_limits("researcher"))
                system.runtime.complete_researcher(block.block_id)
            except Exception as error:
                system.runtime.append_event(block.block_id, "ResearcherRunFailed", {"error_type": type(error).__name__})
                failure = error
                error_type = type(error).__name__
        outcome = run_outcome(manager.ledger(block.block_id).history())
        if outcome is not RunOutcome.COMPLETED:
            failures = [e for e in manager.ledger(block.block_id).history() if e.event_type == "ResearcherRunFailed"]
            error_type = failures[0].payload.get("error_type", "ResearcherRunFailed") if failures else "ResearcherRunIncomplete"
            failure = failure or CycleFailed(error_type)

    status = CycleStatus.FAILED if failure else (CycleStatus.INCOMPLETE if director_error else CycleStatus.COMPLETE)
    dossiers = []
    for original in new_blocks:
        block = manager.block(original.block_id)
        system.runtime.append_event(block.block_id, "ModelUsage", system.runtime.usage_summary())
        events = manager.ledger(block.block_id).history()
        if failure:
            reason = "researcher_failed" if run_outcome(events) is RunOutcome.FAILED else (
                "invalid_block_count" if len(new_blocks) != 1 else "director_failed" if director_outcome is DirectorOutcome.FAILED else "researcher_incomplete")
            block = manager.finalize(block, BlockStatus.FAILED, reason)
        state = None
        try:
            state = system.runtime.research_state.get(block.block_id)
        except KeyError:
            pass
        dossier = build_dossier(block, events, state, block.termination_reason or "unknown")
        if repository is not None:
            repository.record_terminal(block, dossier)
        system.runtime.append_event(block.block_id, "DossierHandoff", {"block_id": block.block_id, "status": block.status.value})
        dossiers.append(dossier)
    if repository is not None:
        if director_output:
            repository.record_research_memory(mission_id, director_output[:2000], ("run-cycle-v3", status.value, direction, *(b.block_id for b in new_blocks)))
        repository.record_cycle(mission_id, system.mode.value, direction, tuple(b.block_id for b in new_blocks),
                                status=status, error_type=error_type, director_outcome=director_outcome, director_error_type=director_error, cycle_id=cycle_id)
    if failure is not None:
        raise failure
    return CycleResult(direction, system.mode, director_output, tuple(b.block_id for b in new_blocks),
                       tuple(dossiers), status, director_outcome, director_error)
