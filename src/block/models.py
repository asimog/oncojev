from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel
from src.director.models import JevBlockStart
class BlockStatus(StrEnum):
    ACTIVE = "active"
    HANDOFF = "handoff"
    COMPLETE = "complete"
class JevBlock(BaseModel, frozen=True):
    block_id: str
    start: JevBlockStart
    started_at: datetime
    deadline: datetime
    status: BlockStatus=BlockStatus.ACTIVE
    termination_reason: str|None=None
    @property
    def objective(self)->str: return self.start.objective
    @property
    def handoff_at(self) -> datetime:
        from datetime import timedelta
        return self.deadline - timedelta(seconds=self.start.allocation.handoff_reserve_seconds)
