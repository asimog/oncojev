from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel
from src.director.models import JevBlockStart
class BlockStatus(StrEnum):
    ACTIVE = "active"
    HANDOFF = "handoff"
    COMPLETE = "complete"
    FAILED = "failed"
    INTERRUPTED = "interrupted"

class RunOutcome(StrEnum):
    NOT_STARTED = "not_started"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"

class CycleStatus(StrEnum):
    COMPLETE = "complete"
    FAILED = "failed"
    INCOMPLETE = "incomplete"

class DirectorOutcome(StrEnum):
    UNKNOWN = "unknown"
    RETURNED = "returned"
    TRUNCATED = "truncated"
    FAILED = "failed"
    INTERRUPTED = "interrupted"

class ObjectiveAttainment(StrEnum):
    UNKNOWN = "unknown"
    ATTAINED = "attained"
    UNREACHABLE = "unreachable"

def run_outcome(events) -> RunOutcome:
    """No retry contract: any failed attempt takes precedence over completion."""
    kinds = {event.event_type for event in events}
    if "ResearcherRunFailed" in kinds:
        return RunOutcome.FAILED
    if "ResearcherRunCompleted" in kinds:
        return RunOutcome.COMPLETED
    if "ResearcherRunStarted" in kinds or "InterruptedBlockRecovered" in kinds:
        return RunOutcome.INTERRUPTED
    return RunOutcome.NOT_STARTED

class JevBlock(BaseModel, frozen=True):
    block_id: str
    start: JevBlockStart
    started_at: datetime
    deadline: datetime
    status: BlockStatus=BlockStatus.ACTIVE
    termination_reason: str|None=None
    mission_id: str|None=None
    cycle_id: str|None=None
    @property
    def objective(self)->str: return self.start.objective
    @property
    def handoff_at(self) -> datetime:
        from datetime import timedelta
        return self.deadline - timedelta(seconds=self.start.allocation.handoff_reserve_seconds)
