from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class LedgerEvent(BaseModel, frozen=True):
    event_type: str = Field(min_length=1)
    occurred_at: datetime
    payload: dict[str, Any] = Field(default_factory=dict)
    event_id: str = Field(default_factory=lambda: str(uuid4()))
