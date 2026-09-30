"""Typed persistence envelopes.

Domain contracts under `src/` remain canonical. A stored record is only an
adapter: it carries a canonical `model_dump` payload plus provenance metadata.
Persistence never becomes the domain model and never re-implements domain policy.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class RecordKind(StrEnum):
    CYCLE = "cycle"
    BLOCK = "block"
    STATE_REVISION = "state_revision"
    CAPABILITY_INVOCATION = "capability_invocation"
    MEASUREMENT = "measurement"
    EVIDENCE = "evidence"
    JEV_OUTPUT = "jev_output"
    JEV_FAILURE = "jev_failure"
    LEDGER_EVENT = "ledger_event"
    ARTIFACT = "artifact"
    DOSSIER = "dossier"
    RESEARCH_MEMORY = "research_memory"


class StoredRecord(BaseModel, frozen=True):
    """One append-only record. `seq` is assigned by the store, never the caller."""

    kind: RecordKind
    record_id: str = Field(min_length=1)
    payload: dict[str, Any]
    block_id: str | None = None
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    schema_version: str = "1"
    seq: int | None = None
