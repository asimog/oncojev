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
    REPRESENTATION_PARSE = "representation_parse"
    METHOD_CANDIDATES = "method_candidates"
    SCIENTIFIC_ATTEMPT = "scientific_attempt"
    MISSION = "mission"
    EXPORT = "export"
    PUBLICATION = "publication"
    CAPABILITY_PROPOSAL = "capability_proposal"
    ENVIRONMENT_QUALIFICATION = "environment_qualification"
    REFERENCE_VALIDATION = "reference_validation"
    DEPLOYMENT_VERIFICATION = "deployment_verification"
    LOCAL_VERIFICATION = "local_verification"
    UTILITY_EVALUATION = "utility_evaluation"
    EXTERNAL_LOOKUP = "external_lookup"
    REGISTRY_REVISION = "registry_revision"
    REGISTRY_REVIEW = "registry_review"
    INSTITUTIONAL_OBSERVATION = "institutional_observation"
    GLOBAL_FRONTIER = "global_frontier"
    PROGRAM_REVIEW = "program_review"
    GLOBAL_RELATION = "global_relation"
    ENGINEERING_PROPOSAL = "engineering_proposal"
    SERVICE_EVENT = "service_event"
    BLOCK_DELTA = "block_delta"
    CYCLE = "cycle"
    CYCLE_START = "cycle_start"
    OUTCOME_CORRECTION = "outcome_correction"
    ACQUISITION = "acquisition"
    SCIENTIFIC_ARTIFACT = "scientific_artifact"
    WORKSPACE_ARCHIVE = "workspace_archive"
    WORKSPACE_CLEANUP = "workspace_cleanup"
    LITERATURE = "literature"
    LITERATURE_CONTEXT = "literature_context"
    FOLLOWUP_PLAN = "followup_plan"
    FOLLOWUP_RESULT = "followup_result"
    SANDBOX_REQUEST = "sandbox_request"
    SANDBOX_CANDIDATE = "sandbox_candidate"
    VERIFICATION = "verification"
    INDEX_RECEIPT = "index_receipt"
    JEV_CALL = "jev_call"
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
    MEMORY_DIGEST = "memory_digest"
    MEMORY_RETRIEVAL = "memory_retrieval"


class StoredRecord(BaseModel, frozen=True):
    """One append-only record. `seq` is assigned by the store, never the caller."""

    kind: RecordKind
    record_id: str = Field(min_length=1)
    payload: dict[str, Any]
    block_id: str | None = None
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    schema_version: str = "1"
    seq: int | None = None
