from datetime import datetime
from pydantic import BaseModel, Field
class ResourceAllocation(BaseModel, frozen=True):
    seconds: int = Field(gt=0)
class JevBlockStart(BaseModel, frozen=True):
    block_id: str
    objective: str = Field(min_length=1)
    why_now: str
    relevant_evidence_refs: tuple[str,...] = ()
    known_uncertainties: tuple[str,...] = ()
    candidate_directions: tuple[str,...] = ()
    constraints: tuple[str,...] = ()
    allocation: ResourceAllocation
    deadline: datetime
StartPacket = JevBlockStart
