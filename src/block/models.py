from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel
from src.director.models import JevBlockStart
class BlockStatus(StrEnum): ACTIVE="active"; COMPLETE="complete"; EXPIRED="expired"
class JevBlock(BaseModel, frozen=True):
    block_id: str
    start: JevBlockStart
    started_at: datetime
    deadline: datetime
    status: BlockStatus=BlockStatus.ACTIVE
    termination_reason: str|None=None
    @property
    def objective(self)->str: return self.start.objective
