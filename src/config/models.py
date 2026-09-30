from pydantic import BaseModel, Field
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
class RuntimeConfig(BaseModel, frozen=True):
    block: dict[str, int | None]
