"""Provider credentials enter the worker process, never agent context."""

import os
from pathlib import Path


def load_local_environment(root: Path | None = None) -> None:
    """Load ignored `.env.local` for local runs; Railway injects runtime variables."""
    path = (root or Path.cwd()) / ".env.local"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def provider_credentials_present() -> dict[str, bool]:
    """Safe readiness signal: never return or log secret values."""
    return {"openrouter": bool(os.environ.get("OPENROUTER_API_KEY")), "typesafe": bool(os.environ.get("TYPESAFE_API_KEY"))}
