from datetime import datetime
from pydantic import BaseModel, Field, model_validator
class ResourceAllocation(BaseModel, frozen=True):
    seconds: int = Field(gt=0)
    handoff_reserve_seconds: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def reserve_fits_allocation(self) -> "ResourceAllocation":
        if self.handoff_reserve_seconds >= self.seconds:
            raise ValueError("handoff reserve must be shorter than the block allocation")
        return self
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
