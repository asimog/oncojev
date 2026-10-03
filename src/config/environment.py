"""Provider credentials enter the worker process, never agent context."""

import os
from dataclasses import dataclass
from pathlib import Path

from src.config.authentication import provider_credentials_present

__all__ = ("load_local_environment", "provider_credentials_present")


@dataclass(frozen=True)
class ProcessSettings:
    testing: bool = False
    data_root: str | None = None
    database_path: str | None = None


def process_settings(root: Path, environment: dict[str, str] | None = None) -> ProcessSettings:
    """Establish frozen settings before paths or storage have side effects."""
    if environment is None:
        load_local_environment(root)
        environment = os.environ
    switch = environment.get("ONCOJEV_TESTING", "0")
    if switch not in {"0", "1"}:
        raise ValueError("ONCOJEV_TESTING must be literal 0 or 1")
    return ProcessSettings(switch == "1", environment.get("ONCOJEV_DATA_ROOT"),
                           environment.get("ONCOJEV_DB_PATH"))


def load_local_environment(root: Path | None = None) -> None:
    """Load ignored `.env.local` without overriding existing process variables."""
    path = (root or Path.cwd()) / ".env.local"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
