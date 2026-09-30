"""Two authentication domains that must never be conflated.

Model-provider credentials authorize LLM/Jev inference. Scientific-data access
authorizes biological source retrieval. They are separate concerns: a provider
key must never be reused to reach controlled scientific data, and public
scientific wrappers must never receive a provider credential.
"""

from collections.abc import Mapping
from enum import StrEnum
import os

from src.config.models import RuntimeMode


class AuthenticationDomain(StrEnum):
    MODEL_PROVIDER = "model_provider"
    SCIENTIFIC_DATA = "scientific_data"


MODEL_PROVIDER_ENV: frozenset[str] = frozenset(
    {"OPENROUTER_API_KEY", "TYPESAFE_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"}
)
SCIENTIFIC_DATA_ENV: frozenset[str] = frozenset()

_OVERLAP = MODEL_PROVIDER_ENV & SCIENTIFIC_DATA_ENV
if _OVERLAP:
    raise RuntimeError(f"authentication domains overlap: {sorted(_OVERLAP)}")


def provider_credentials_present(environment: Mapping[str, str] | None = None) -> dict[str, bool]:
    """Safe readiness signal for model providers; never returns secret values."""
    source = environment if environment is not None else os.environ
    return {
        "openrouter": bool(source.get("OPENROUTER_API_KEY")),
        "typesafe": bool(source.get("TYPESAFE_API_KEY")),
    }


def live_providers_available(environment: Mapping[str, str] | None = None) -> bool:
    """True only when live mode has every credential the configured roles need."""
    present = provider_credentials_present(environment)
    return present["openrouter"] and present["typesafe"]


def resolve_mode(requested: RuntimeMode, environment: Mapping[str, str] | None = None) -> RuntimeMode:
    """A live request without credentials degrades to deterministic, never to a partial live run."""
    if requested is RuntimeMode.LIVE and not live_providers_available(environment):
        return RuntimeMode.DETERMINISTIC
    return requested


def scientific_data_credentials() -> dict[str, bool]:
    """Scientific-data authentication is a distinct, currently empty domain."""
    return {name: False for name in sorted(SCIENTIFIC_DATA_ENV)}
