from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, Field, model_validator
from src.memory.models import StartMemory
MemoryTag = Annotated[str, Field(min_length=1, max_length=200)]
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
    objective: str = Field(min_length=1, max_length=4000)
    why_now: str = Field(max_length=2000)
    relevant_evidence_refs: tuple[str,...] = ()
    known_uncertainties: tuple[str,...] = ()
    candidate_directions: tuple[str,...] = ()
    constraints: tuple[str,...] = ()
    allocation: ResourceAllocation
    deadline: datetime
    memory: StartMemory = Field(default_factory=StartMemory)
    entities: tuple[MemoryTag, ...] = Field(default=(), max_length=20)
    topics: tuple[MemoryTag, ...] = Field(default=(), max_length=20)
    oncolab_registry_revision: str | None = None
    oncolab_history_high_water: int | None = Field(default=None, ge=0)
    application_identity: str | None = None
