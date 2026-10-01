"""A complete Director -> Researcher research cycle.

The Director receives a broad direction, not a script. It searches the OncoLab
Index, allocates a bounded block, and launches the independent Researcher agent.
Dossiers are assembled deterministically from the append-only ledger and, when a
repository is supplied, the whole cycle is persisted as typed records.
"""

from dataclasses import dataclass
from decimal import Decimal

from pydantic_ai.usage import UsageLimits

from src.block.models import BlockStatus
from src.config.models import RuntimeMode
from src.dossier.builder import build_dossier
from src.dossier.models import JevBlockDossier
from src.persistence.repository import ResearchRepository
from src.runtime.pydantic_ai.factory import ConfiguredSystem
from src.runtime.pydantic_ai.contracts import DirectorDeps, ResearcherDeps


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


def run_cycle(
    system: ConfiguredSystem,
    direction: str,
    *,
    repository: ResearchRepository | None = None,
    mission_id: str = "mission",
) -> CycleResult:
    """Run one bounded cycle; the Director chooses scope and the Researcher investigates."""
    manager = system.runtime.manager
    system.runtime.repository = repository
    before = {block.block_id for block in manager.blocks()}
    director_output = ""
    try:
        limits = UsageLimits(
            request_limit=system.runtime.max_model_requests,
            tool_calls_limit=system.runtime.max_tool_calls,
            cost_limit=Decimal(str(system.runtime.max_cost)) if system.runtime.max_cost is not None else None,
        )
        result = system.agents.director.run_sync(
            DIRECTOR_PROMPT.format(direction=direction), deps=DirectorDeps(system.runtime), usage_limits=limits
        )
        director_output = result.output
    except Exception as error:
        created_blocks = tuple(block for block in manager.blocks() if block.block_id not in before)
        can_finalize = len(created_blocks) == 1 and not any(
            event.event_type == "ResearcherRunFailed"
            for event in manager.ledger(created_blocks[0].block_id).history()
        )
        if not can_finalize:
            created = tuple(block.block_id for block in created_blocks)
            if repository is not None:
                repository.record_cycle(mission_id, system.mode.value, direction, created, status="failed", error_type=type(error).__name__)
            raise
        director_output = f"Director ended after allocating a recoverable block: {type(error).__name__}"
        system.runtime.append_event(created_blocks[0].block_id, "DirectorRunTruncated", {"error_type": type(error).__name__})
    new_blocks = tuple(block for block in manager.blocks() if block.block_id not in before)
    if len(new_blocks) != 1:
        if repository is not None:
            repository.record_cycle(mission_id, system.mode.value, direction, tuple(block.block_id for block in new_blocks), status="failed", error_type="InvalidBlockCount")
        raise RuntimeError(f"autonomous cycle must allocate exactly one block; allocated {len(new_blocks)}")
    block = new_blocks[0]
    event_types = {event.event_type for event in manager.ledger(block.block_id).history()}
    if "ResearcherRunStarted" not in event_types:
        researcher = system.runtime.researcher_factory(block.block_id) if system.runtime.researcher_factory else system.agents.fresh_researcher(block.block_id)
        system.runtime.append_event(block.block_id, "ResearcherRunStarted", {"block_id": block.block_id, "launched_by": "python_orchestrator", "workspace": f"var/workspaces/{block.block_id}"})
        try:
            researcher.run_sync(f"Investigate block {block.block_id}: {block.objective}", deps=ResearcherDeps(system.runtime, block.block_id))
        except Exception as error:
            system.runtime.append_event(block.block_id, "ResearcherRunFailed", {"error_type": type(error).__name__})
            if repository is not None:
                repository.record_cycle(mission_id, system.mode.value, direction, (block.block_id,), status="failed", error_type=type(error).__name__)
            raise
        system.runtime.append_event(block.block_id, "ResearcherRunCompleted", {"block_id": block.block_id})
    block = manager.block(block.block_id)
    if manager.status(block) is not BlockStatus.COMPLETE:
        reason = "soft_deadline_handoff" if manager.status(block) is BlockStatus.HANDOFF else "researcher_returned"
        block = manager.complete(block, reason)
        system.runtime.append_event(block.block_id, "ResearcherCompletion", {"status": block.status.value, "reason": reason})
        if repository is not None:
            repository.record_block(block)
    state = system.runtime.research_state.get(block.block_id)
    events = manager.ledger(block.block_id).history()
    dossier = build_dossier(block, events, state, block.termination_reason or "unknown")
    system.runtime.append_event(block.block_id, "DossierHandoff", {"block_id": block.block_id})
    if repository is not None:
        repository.record_dossier(dossier)
        repository.record_research_memory(mission_id, director_output[:2000], ("run-cycle-v2", direction, block.block_id))
        repository.record_cycle(mission_id, system.mode.value, direction, (block.block_id,))
    return CycleResult(
        direction=direction,
        mode=system.mode,
        director_output=director_output,
        block_ids=(block.block_id,),
        dossiers=(dossier,),
    )
