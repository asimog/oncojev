from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class AcquisitionRecord(BaseModel, frozen=True):
    acquisition_id: str = Field(default_factory=lambda: str(uuid4()))
    source: str
    request: dict[str, Any]
    records: tuple[dict[str, Any], ...]
    public_only: bool = True
    provenance: tuple[str, ...] = Field(min_length=1)


class LiteratureRecord(BaseModel, frozen=True):
    title: str
    doi: str | None = None
    url: str | None = None
    source: str


class LiteratureSearchResult(BaseModel, frozen=True):
    query: str
    records: tuple[LiteratureRecord, ...]
    provenance: tuple[str, ...] = Field(min_length=1)
