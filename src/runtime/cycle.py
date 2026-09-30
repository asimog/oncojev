"""A complete Director -> Researcher research cycle.

The Director receives a broad direction, not a script. It searches the OncoLab
Index, allocates a bounded block, and launches the independent Researcher agent.
Dossiers are assembled deterministically from the append-only ledger and, when a
repository is supplied, the whole cycle is persisted as typed records.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

from src.block.models import BlockStatus
from src.config.models import RuntimeMode
from src.dossier.builder import build_dossier
from src.dossier.models import JevBlockDossier
from src.ledger.events import LedgerEvent
from src.persistence.repository import ResearchRepository
from src.runtime.pydantic_ai.factory import ConfiguredSystem
from src.runtime.pydantic_ai.contracts import DirectorDeps


DIRECTOR_PROMPT = (
    "Broad research direction: {direction}\n"
    "Determine for yourself what to do. Search the OncoLab Index for relevant capabilities, "
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
    result = system.agents.director.run_sync(DIRECTOR_PROMPT.format(direction=direction), deps=DirectorDeps(system.runtime))
    manager = system.runtime.manager
    dossiers: list[JevBlockDossier] = []
    for block in manager.blocks():
        ledger = manager.ledger(block.block_id)
        if manager.status(block) is not BlockStatus.COMPLETE and block.termination_reason is None:
            continue
        state = None
        try:
            state = system.runtime.research_state.get(block.block_id)
        except KeyError:
            state = None
        events = ledger.history()
        dossier = build_dossier(block, events, state, block.termination_reason or "unknown")
        ledger.append(LedgerEvent(event_type="DossierHandoff", occurred_at=datetime.now(UTC), payload={"block_id": block.block_id}))
        dossiers.append(dossier)
        if repository is not None:
            _persist_block(repository, system, block, state, events, dossier)
    if repository is not None:
        repository.record_research_memory(mission_id, result.output[:2000], ("run-cycle-v1", direction))
        repository.record_cycle(mission_id, system.mode.value, direction, tuple(block.block_id for block in manager.blocks()))
    return CycleResult(
        direction=direction,
        mode=system.mode,
        director_output=result.output,
        block_ids=tuple(block.block_id for block in manager.blocks()),
        dossiers=tuple(dossiers),
    )


def _persist_block(repository, system, block, state, events, dossier) -> None:
    repository.record_block(block)
    for event in events:
        repository.record_ledger_event(block.block_id, event)
    if state is None:
        repository.record_dossier(dossier)
        return
    repository.record_state_revision(state)
    for measurement in state.measurements:
        repository.record_measurement(measurement, block.block_id)
    for evidence_id in state.evidence_ids:
        evidence = system.runtime.evidence.get(evidence_id)
        if evidence is not None:
            repository.record_evidence(evidence, block.block_id)
    for artifact in system.runtime.artifacts.values():
        repository.record_artifact(block.block_id, artifact)
    if system.runtime.jev_history:
        repository.record_jev_decisions(block.block_id, tuple(system.runtime.jev_history))
    repository.record_dossier(dossier)
