from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field
from src.provenance import content_hash


class AcquisitionRecord(BaseModel, frozen=True):
    acquisition_id: str = Field(default_factory=lambda: str(uuid4()))
    source: str
    request: dict[str, Any]
    records: tuple[dict[str, Any], ...]
    public_only: bool = True
    provenance: tuple[str, ...] = Field(min_length=1)
    response_bytes: int | None = Field(default=None, ge=0)

    @computed_field
    @property
    def content_sha256(self) -> str:
        return content_hash({"source": self.source, "request": self.request, "records": self.records,
                             "public_only": self.public_only, "provenance": self.provenance})


class LiteratureRecord(BaseModel, frozen=True):
    title: str
    doi: str | None = None
    url: str | None = None
    source: str


class LiteratureSearchResult(BaseModel, frozen=True):
    context_id: str = Field(default_factory=lambda: str(uuid4()))
    query: str
    request: dict[str, Any] = Field(default_factory=dict)
    records: tuple[LiteratureRecord, ...]
    provenance: tuple[str, ...] = Field(min_length=1)
    response_bytes: int | None = Field(default=None, ge=0)

    @computed_field
    @property
    def content_sha256(self) -> str:
        return content_hash({"query": self.query, "request": self.request, "records": [r.model_dump(mode="json") for r in self.records],
                             "provenance": self.provenance})
