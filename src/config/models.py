from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
class RuntimeMode(StrEnum):
    DETERMINISTIC = "deterministic"
    LIVE = "live"
class ReasoningConfig(StrictModel):
    effort: str | None = None
    budget_tokens: int | None = None
class ModelRoleConfig(StrictModel):
    provider: str
    model: str
    api_base: str | None = None
    reasoning: ReasoningConfig = Field(default_factory=ReasoningConfig)
    max_output_tokens: int | None = None
    timeout_seconds: int | None = None
    fallbacks: tuple[str, ...] = ()
    http2: bool = False
class ModelsConfig(StrictModel):
    director: ModelRoleConfig
    researcher: ModelRoleConfig
    reasoner: ModelRoleConfig
    jev: ModelRoleConfig
class SandboxConfig(StrictModel):
    provider: Literal["docker"] = "docker"
    image: str = "python:3.12-slim"
    cpu: int = Field(default=2, ge=1, le=8)
    memory_mb: int = Field(default=4096, ge=512, le=32768)
    timeout_seconds: int = Field(default=300, ge=10, le=1800)
class BlockConfig(StrictModel):
    default_seconds: int = Field(default=600, gt=0)
    handoff_reserve_seconds: int = Field(default=60, ge=0)
    max_tool_calls: int = Field(default=100, gt=0)
    max_model_requests: int = Field(default=200, gt=0)
    max_source_calls: int = Field(default=20, ge=0)
    max_jev_calls: int = Field(default=100, ge=0)
    max_reasoner_calls: int = Field(default=5, ge=0)
    max_sandbox_calls: int = Field(default=2, ge=0)
    max_download_bytes: int = Field(default=100_000_000, gt=0)
    max_cost: float | None = Field(default=None, gt=0)

    def __getitem__(self, key: str) -> int | float | None:
        return getattr(self, key)


class RetrievalConfig(StrictModel):
    retrieval_k: int = Field(default=20, ge=1, le=20)
    semantic_frontier_k: int = Field(default=8, ge=1, le=20)


class SearchConfig(StrictModel):
    search_k: int = Field(default=20, ge=1, le=20)


class RuntimeConfig(StrictModel):
    mode: RuntimeMode = RuntimeMode.DETERMINISTIC
    block: BlockConfig = Field(default_factory=BlockConfig)
    director: RetrievalConfig = Field(default_factory=RetrievalConfig)
    oncolab: SearchConfig = Field(default_factory=SearchConfig)
    jev: SearchConfig = Field(default_factory=SearchConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
