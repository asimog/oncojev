from enum import StrEnum
from pydantic import BaseModel, Field
class RuntimeMode(StrEnum):
    DETERMINISTIC = "deterministic"
    LIVE = "live"
class ReasoningConfig(BaseModel, frozen=True):
    effort: str | None = None
    budget_tokens: int | None = None
class ModelRoleConfig(BaseModel, frozen=True):
    provider: str
    model: str
    api_base: str | None = None
    reasoning: ReasoningConfig = Field(default_factory=ReasoningConfig)
    max_output_tokens: int | None = None
    timeout_seconds: int | None = None
    fallbacks: tuple[str, ...] = ()
    http2: bool = False
class ModelsConfig(BaseModel, frozen=True):
    director: ModelRoleConfig
    researcher: ModelRoleConfig
    reasoner: ModelRoleConfig
    jev: ModelRoleConfig
class SandboxConfig(BaseModel, frozen=True):
    provider: str = "docker"
    image: str = "python:3.12-slim"
    cpu: int = Field(default=2, ge=1, le=8)
    memory_mb: int = Field(default=4096, ge=512, le=32768)
    timeout_seconds: int = Field(default=300, ge=10, le=1800)
class RuntimeConfig(BaseModel, frozen=True):
    mode: RuntimeMode = RuntimeMode.DETERMINISTIC
    block: dict[str, int | None]
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
