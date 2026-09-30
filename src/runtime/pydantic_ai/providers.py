from typing import Any

from src.config.models import ModelRoleConfig
from pydantic_ai.models.fallback import FallbackModel


def model_settings(role: ModelRoleConfig) -> dict[str, Any]:
    """Translate portable configuration to Pydantic AI's portable settings only."""
    settings: dict[str, Any] = {}
    if role.max_output_tokens is not None:
        settings["max_tokens"] = role.max_output_tokens
    # Reasoning controls differ by provider and are intentionally not guessed here.
    return settings


def configured_model(role: ModelRoleConfig) -> str | FallbackModel:
    """Use the configured primary and only declared fallback models."""
    return role.model if not role.fallbacks else FallbackModel(role.model, *role.fallbacks)
