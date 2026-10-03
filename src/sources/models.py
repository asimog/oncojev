from typing import Any, Literal
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field, model_validator
from src.provenance import content_hash


class CoverageContract(BaseModel, frozen=True):
    endpoint: str | None = None
    offset: int = Field(default=0, ge=0)
    requested_size: int | None = Field(default=None, ge=1)
    returned_rows: int = Field(default=0, ge=0)
    reported_total: int | None = Field(default=None, ge=0)
    ordering: str | None = None
    id_field: str | None = None
    unique_entities: int | None = Field(default=None, ge=0)
    duplicate_rows: int = Field(default=0, ge=0)
    complete: bool = False
    limitations: tuple[str, ...] = ("Population coverage unknown.",)


class AcquisitionRecord(BaseModel, frozen=True):
    acquisition_id: str = Field(default_factory=lambda: str(uuid4()))
    source: str
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    request: dict[str, Any]
    records: tuple[dict[str, Any], ...]
    public_only: bool = True
    origin: Literal["public","synthetic"] = "public"
    provenance: tuple[str, ...] = Field(min_length=1)
    response_bytes: int | None = Field(default=None, ge=0)
    coverage: CoverageContract | None = None

    @computed_field
    @property
    def content_sha256(self) -> str:
        payload = {"source": self.source, "request": self.request, "records": self.records,
                   "public_only": self.public_only, "provenance": self.provenance}
        if self.origin != "public":payload["origin"] = self.origin
        if self.coverage is not None:
            payload["coverage"] = self.coverage.model_dump(mode="json")
        return content_hash(payload)


class LiteratureRecord(BaseModel, frozen=True):
    title: str
    doi: str | None = None
    url: str | None = None
    source: str
    abstract: str | None = None
    abstract_truncated: bool = False


class LiteratureSearchResult(BaseModel, frozen=True):
    context_id: str = Field(default_factory=lambda: str(uuid4()))
    query: str
    request: dict[str, Any] = Field(default_factory=dict)
    records: tuple[LiteratureRecord, ...]
    provenance: tuple[str, ...] = Field(min_length=1)
    response_bytes: int | None = Field(default=None, ge=0)
    retrieved_at: datetime | None = None
    coverage: CoverageContract | None = None

    @computed_field
    @property
    def content_sha256(self) -> str:
        # Old title-only records retain their original content identity on reopen.
        records = []
        for record in self.records:
            payload = record.model_dump(mode="json", exclude={"abstract", "abstract_truncated"})
            if record.abstract is not None:
                payload["abstract"] = record.abstract
            if record.abstract_truncated:
                payload["abstract_truncated"] = True
            records.append(payload)
        payload = {"query": self.query, "request": self.request, "records": records,
                   "provenance": self.provenance}
        if self.retrieved_at is not None:
            payload["retrieved_at"] = self.model_dump(mode="json", include={"retrieved_at"})["retrieved_at"]
        if self.coverage is not None:
            payload["coverage"] = self.coverage.model_dump(mode="json")
        return content_hash(payload)


class ScientificArtifact(BaseModel, frozen=True):
    """Exact retained bytes; content identity is separate from logical acquisition."""
    artifact_id: str = Field(default_factory=lambda: str(uuid4()))
    block_id: str = Field(min_length=1)
    source: str
    request: dict[str, Any]
    source_identity: str
    content_base64: str
    byte_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)
    format: str
    access: str = "open"
    release: str | None = None
    licence: str | None = None
    provenance: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_bytes(self):
        import base64
        import hashlib
        data = base64.b64decode(self.content_base64, validate=True)
        if len(data) != self.size_bytes or hashlib.sha256(data).hexdigest() != self.byte_sha256:
            raise ValueError("artifact byte identity mismatch")
        return self

    def bytes(self) -> bytes:
        import base64
        # Revalidate nested mutable payloads before use.
        self.validate_bytes()
        return base64.b64decode(self.content_base64, validate=True)

    @computed_field
    @property
    def content_sha256(self) -> str:
        return self.byte_sha256


class DataAssetCard(BaseModel, frozen=True):
    """Retained source metadata, never an executable capability or usable matrix."""
    acquisition_id: str
    file_id: str | None
    file_name: str | None = None
    access: Literal["open", "controlled", "unknown"] = "unknown"
    state: str | None = None
    data_category: str | None = None
    data_type: str | None = None
    data_format: str | None = None
    experimental_strategy: str | None = None
    platform: str | None = None
    workflow: str | None = None
    file_size: int | None = Field(default=None, ge=0)
    md5sum: str | None = None
    cases: tuple[str, ...] = ()
    projects: tuple[str, ...] = ()
    entity_unit: Literal["file"] = "file"
    request_sha256: str
    content_sha256: str
    retrieved_at: str
    omissions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ("Metadata does not establish usable assay units, pairing or population coverage.",)
