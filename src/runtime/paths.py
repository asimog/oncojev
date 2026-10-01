"""Service-owned durable paths; no agent-selected storage roots."""
import os
from pathlib import Path


def data_root(application: Path) -> Path:
    configured = os.environ.get("ONCOJEV_DATA_ROOT")
    root = Path(configured) if configured else application / "var"
    if not root.is_absolute():
        raise ValueError("ONCOJEV_DATA_ROOT must be absolute")
    return root


def workspace_root(application: Path) -> Path:
    return data_root(application) / "workspaces"


def director_root(application: Path) -> Path:
    return data_root(application) / "director" if os.environ.get("ONCOJEV_DATA_ROOT") else Path("/work/director")
