"""Service-owned durable paths; no agent-selected storage roots."""
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from src.config.environment import ProcessSettings, process_settings

# One namespace per interpreter process, shared by services/cycles, never by PID.
_TEST_RUN_ID = uuid4().hex


@dataclass(frozen=True)
class RuntimePaths:
    data: Path
    workspaces: Path
    director: Path
    testing: bool = False

    def database(self, override: Path | str | None = None) -> Path:
        target = Path(override) if override is not None else self.data / "oncojev.sqlite3"
        target = target.resolve()
        self.require_owned(target)
        return target

    def require_owned(self, target: Path) -> Path:
        resolved = target.resolve()
        if self.testing and not resolved.is_relative_to(self.data):
            raise ValueError("testing path must remain inside its isolated run root")
        return resolved


def select_paths(application: Path, settings: ProcessSettings) -> RuntimePaths:
    base = Path(settings.data_root) if settings.data_root else application.resolve() / "var"
    if not base.is_absolute():
        raise ValueError("ONCOJEV_DATA_ROOT must be absolute")
    base = base.resolve()
    root = base / "testing" / _TEST_RUN_ID if settings.testing else base
    if settings.testing and root.resolve() != root:
        raise ValueError("linked testing root escapes configured data root")
    paths = RuntimePaths(root, root / "workspaces",
        root / "director" if settings.testing or settings.data_root else Path("/work/director"), settings.testing)
    if settings.testing:
        for target in (paths.workspaces, paths.director):
            paths.require_owned(target)
    return paths


def data_root(application: Path) -> Path:
    return select_paths(application, process_settings(application)).data


def workspace_root(application: Path) -> Path:
    return select_paths(application, process_settings(application)).workspaces


def director_root(application: Path) -> Path:
    return select_paths(application, process_settings(application)).director
