"""Stable JSON identities, independent of run and acquisition UUIDs."""

import hashlib
import json
from typing import Literal
from pydantic import BaseModel, Field, model_validator


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def content_hash(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


class ExecutionReference(BaseModel, frozen=True):
    kind: Literal["file", "measurement", "evidence", "artifact", "acquisition", "literature", "sandbox_candidate", "scientific_artifact"]
    value: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    block_id: str | None = None

    @model_validator(mode="after")
    def record_scope(self):
        if self.kind != "file" and not self.block_id:
            raise ValueError("record references require a block identity")
        return self
