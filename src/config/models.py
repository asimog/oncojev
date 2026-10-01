from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
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
    default_seconds: int = Field(default=900, gt=0)
    min_seconds: int = Field(default=300, gt=0)
    max_seconds: int = Field(default=3600, gt=0)
    handoff_reserve_seconds: int = Field(default=90, ge=0)
    max_tool_calls: int = Field(default=100, ge=0)
    max_model_requests: int = Field(default=200, ge=0)
    max_provider_tool_calls: int = Field(default=500, ge=0)
    max_code_mode_executions: int = Field(default=100, ge=0)
    max_code_mode_tool_calls: int = Field(default=100, ge=0)
    max_source_calls: int = Field(default=20, ge=0)
    max_jev_calls: int = Field(default=100, ge=0)
    max_jev_questions: int = Field(default=200, ge=0)
    max_reasoner_calls: int = Field(default=5, ge=0)
    max_reasoner_model_requests: int = Field(default=10, ge=0)
    max_sandbox_calls: int = Field(default=2, ge=0)
    max_download_bytes: int = Field(default=10_000_000, gt=0, le=10_000_000)
    max_cost: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def allocation_bounds(self):
        if not self.min_seconds <= self.default_seconds <= self.max_seconds:
            raise ValueError("require min_seconds <= default_seconds <= max_seconds")
        if self.handoff_reserve_seconds >= self.min_seconds:
            raise ValueError("handoff reserve must be shorter than the minimum allocation")
        return self

    def __getitem__(self, key: str) -> int | float | None:
        return getattr(self, key)


class RetrievalConfig(StrictModel):
    retrieval_k: int = Field(default=20, ge=1, le=20)
    max_model_requests: int = Field(default=50, ge=0)
    max_provider_tool_calls: int = Field(default=100, ge=0)
    max_code_mode_executions: int = Field(default=30, ge=0)
    max_code_mode_tool_calls: int = Field(default=100, ge=0)
    max_cost: float | None = Field(default=None, gt=0)
    max_memory_jev_calls: int = Field(default=4, ge=0, le=100)
    max_memory_jev_questions: int = Field(default=20, ge=0, le=500)
    max_memory_jev_bytes: int = Field(default=131072, ge=0)
    max_memory_jev_seconds: float = Field(default=20, ge=0)


class CycleBudgetConfig(StrictModel):
    max_model_requests: int = Field(default=300, ge=0)
    max_provider_tool_calls: int = Field(default=700, ge=0)
    max_cost: float | None = Field(default=None, gt=0)


class SearchConfig(StrictModel):
    search_k: int = Field(default=20, ge=1, le=20)
    candidate_k: int = Field(default=80, ge=1, le=200)


class JevConfig(StrictModel):
    max_questions_per_call: int = Field(default=100, ge=1, le=1000)
    max_payload_bytes: int = Field(default=131072, ge=4096, le=1000000)
    projection_max_items: int = Field(default=20, ge=1, le=100)
    projection_max_payload_bytes: int = Field(default=65536, ge=4096, le=1000000)


class RetentionConfig(StrictModel):
    enabled: bool = True
    minimum_age_seconds: int = Field(default=604800, ge=0)
    max_archive_bytes: int = Field(default=100_000_000, gt=0)
    max_workspaces: int = Field(default=20, ge=1, le=100)


class ServiceResourceConfig(StrictModel):
    max_block_download_bytes: int = Field(default=50_000_000, gt=0)
    max_service_download_bytes: int = Field(default=500_000_000, gt=0)


class RuntimeConfig(StrictModel):
    mode: RuntimeMode = RuntimeMode.DETERMINISTIC
    block: BlockConfig = Field(default_factory=BlockConfig)
    director: RetrievalConfig = Field(default_factory=RetrievalConfig)
    cycle: CycleBudgetConfig = Field(default_factory=CycleBudgetConfig)
    oncolab: SearchConfig = Field(default_factory=SearchConfig)
    jev: JevConfig = Field(default_factory=JevConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    retention: RetentionConfig = Field(default_factory=RetentionConfig)
    resources: ServiceResourceConfig = Field(default_factory=ServiceResourceConfig)
