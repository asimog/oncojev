from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from src.science.models import MeasuredResult


class ScientificEvidence(BaseModel, frozen=True):
    evidence_id: str = Field(default_factory=lambda: str(uuid4()))
    admitted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    measurement: MeasuredResult
