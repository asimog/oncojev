"""A command-only backend so Coder file tools also cross the Linux boundary."""

from dataclasses import dataclass
from pathlib import Path
import sys

from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.workspaces import LocalWorkspaceBackend


class ConfinedBackend:
    # Deliberately no SupportsFilesystem: Workspace uses its shell filesystem
    # adapter, so reads, edits, symlink traversal and shell share one policy.
    def __init__(self, workspace: Path, application: Path, runtime=None, owner="director"):
        self.runtime = runtime
        self.owner = owner
        self.application = application.resolve()
        self.workspace = workspace.resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        temporary = self.workspace / ".tmp"
        temporary.mkdir(exist_ok=True)
        self.backend = LocalWorkspaceBackend(self.workspace, env={
            "PATH": str(Path(sys.executable).parent) + ":/usr/local/bin:/usr/bin:/bin",
            "HOME": str(self.workspace), "TMPDIR": str(temporary),
            "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "LC_CTYPE": "C.UTF-8",
            "PYTHONDONTWRITEBYTECODE": "1"})

    @property
    def ref(self):
        return self.backend.ref

    async def working_dir(self):
        return str(self.workspace)

    async def run(self, command, *, shell=False, env=None, timeout=None):
        if env:
            raise ValueError("Coder command environment overrides are forbidden")
        if isinstance(command, str):
            if not shell:
                raise TypeError("string command requires shell=True")
            command = ["/bin/sh", "-c", command]
        elif shell:
            raise TypeError("argv command requires shell=False")
        launcher = Path(__file__).with_name("landlock_exec.py")
        argv = [sys.executable, "-I", str(launcher), str(self.workspace), str(self.application), *command]
        if self.runtime is None:
            raise RuntimeError("Coder requires service-owned execution resources")
        async with self.runtime.service_resources.heavy(self.owner):
            return await self.backend.run(argv, timeout=timeout)



@dataclass
class ConfinedWorkspace(AbstractCapability):
    working_dir: Path
    application: Path

    def get_workspace(self, ctx, *, ref):
        backend = ConfinedBackend(self.working_dir, self.application, ctx.deps.runtime,
                                  getattr(ctx.deps, "block_id", "director"))
        return backend if ref is None or ref == backend.ref else None
