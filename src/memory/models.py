from datetime import datetime
from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from src.persistence.records import RecordKind


class MemoryReference(BaseModel, frozen=True):
    kind: RecordKind
    record_id: str
    seq: int = Field(gt=0)
    block_id: str | None = None
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class MemoryItem(BaseModel, frozen=True):
    item_id: str
    summary: str
    epistemic_status: Literal["hypothesis", "uncertainty", "operational_failure", "semantic_history", "proposal", "legacy_prose", "director_note", "scientific_negative", "scientific_attempt", "tentative_literature_context", "scientific_followup"]
    references: tuple[MemoryReference, ...] = ()
    details: dict[str, Any] = Field(default_factory=dict)


class CycleDigest(BaseModel, frozen=True):
    version: Literal["research-memory-v1", "research-memory-v2", "research-memory-v3", "research-memory-v4"] = "research-memory-v4"
    digest_id: str
    cycle_id: str
    mission_id: str | None = None
    direction: str
    recorded_at: datetime
    cycle_status: Literal["complete", "failed", "incomplete", "unknown"]
    director_outcome: Literal["unknown", "returned", "truncated", "failed", "interrupted"]
    failure_reason: str | None = None
    block_ids: tuple[str, ...] = ()
    objectives: tuple[str, ...] = ()
    lifecycle: tuple[dict[str, Any], ...] = ()
    references: tuple[MemoryReference, ...] = ()
    limitations: tuple[str, ...] = ()
    unresolved_references: tuple[str, ...] = ()
    hypotheses: tuple[MemoryItem, ...] = ()
    scientific_negative_findings: tuple[MemoryItem, ...] = ()
    scientific_attempts: tuple[MemoryItem, ...] = ()
    literature_contexts: tuple[MemoryItem, ...] = ()
    scientific_followups: tuple[MemoryItem, ...] = ()
    candidates: tuple[MemoryItem, ...] = ()
    operational_blockers: tuple[MemoryItem, ...] = ()
    uncertainties: tuple[MemoryItem, ...] = ()
    continuation_proposals: tuple[MemoryItem, ...] = ()
    resource_usage: dict[str, Any] = Field(default_factory=dict)
    entities: tuple[str, ...] = ()
    topics: tuple[str, ...] = ()
    inferred: bool = False
    legacy_notes: tuple[MemoryItem, ...] = ()
    director_note: MemoryItem | None = None


class MemoryContext(BaseModel, frozen=True):
    version: Literal["memory-context-v1"] = "memory-context-v1"
    query: str
    digests: tuple[dict[str, Any], ...] = ()
    omitted_digests: int = 0
    max_bytes: int = 32768
    retrieval: dict[str, Any] = Field(default_factory=dict)


class StartMemory(BaseModel, frozen=True):
    """Prior context does not inherit measurements, evidence or tool authority."""
    digest_ids: tuple[str, ...] = ()
    references: tuple[MemoryReference, ...] = ()
    prior_failures: tuple[str, ...] = ()
    prior_attempts: tuple[str, ...] = ()
    prior_contexts: tuple[str, ...] = ()
    prior_followups: tuple[str, ...] = ()
    uncertainties: tuple[str, ...] = ()
    candidate_directions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    omitted_digests: int = 0
    omitted_items: int = 0


class MemoryFilters(BaseModel, frozen=True):
    model_config = ConfigDict(extra="forbid")
    mission_id: str | None = None
    entity: str | None = None
    topic: str | None = None
    capability: str | None = None
    hypothesis: str | None = None
    shared_reference: str | None = None
    lineage: str | None = None
    since: AwareDatetime | None = None
    until: AwareDatetime | None = None


class MemoryRetrievalReceipt(BaseModel, frozen=True):
    receipt_id: str
    query: str
    mission_id: str | None
    cycle_id: str | None
    block_id: str | None
    digest_ids: tuple[str, ...]
    status: str
    failure_type: str | None = None
    semantic_call_ids: tuple[str, ...] = ()
    resources: dict[str, Any]
    duration_ms: float = Field(ge=0)
    retrieval_version: str = "memory-retrieval-v3-bounded-alternatives"
    retrieval: dict[str, Any] = Field(default_factory=dict)
