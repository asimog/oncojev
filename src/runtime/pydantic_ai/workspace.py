"""A command-only backend so Coder file tools also cross the Linux boundary."""

from dataclasses import dataclass
from pathlib import Path
import sys
import math
import json
from dataclasses import asdict

from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.workspaces import LocalWorkspaceBackend
from pydantic_ai.workspaces import CommandResult
from src.runtime.process import ProcessLimits, ProcessCleanupFailed, run_owned_command
from src.runtime.resources import ResourceRejected


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
        self.environment = {
            "PATH": str(Path(sys.executable).parent) + ":/usr/local/bin:/usr/bin:/bin",
            "HOME": str(self.workspace), "TMPDIR": str(temporary),
            "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "LC_CTYPE": "C.UTF-8",
            "PYTHONDONTWRITEBYTECODE": "1"}
        self.backend = LocalWorkspaceBackend(self.workspace, env=self.environment)

    @property
    def ref(self):
        return self.backend.ref

    async def working_dir(self):
        return str(self.workspace)

    async def run(self, command, *, shell=False, env=None, timeout=None):
        if timeout is not None and (not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0):
            raise ValueError("timeout must be positive and finite")
        if env:
            raise ValueError("Coder command environment overrides are forbidden")
        if isinstance(command, str):
            if not shell:
                raise TypeError("string command requires shell=True")
            command = ["/bin/sh", "-c", command]
        elif shell:
            raise TypeError("argv command requires shell=False")
        launcher = Path(__file__).with_name("landlock_exec.py")
        if self.runtime is None:
            raise RuntimeError("Coder requires service-owned execution resources")
        resources = self.runtime.service_resources
        limits = ProcessLimits(processes=resources.max_coder_processes, memory_mb=resources.max_coder_memory_mb,
            cpu=resources.max_coder_cpu, wall_seconds=min(timeout or resources.max_coder_seconds, resources.max_coder_seconds),
            workspace_bytes=resources.max_workspace_bytes, minimum_free_disk_bytes=resources.minimum_free_disk_bytes)
        argv = [sys.executable, "-I", str(launcher), str(self.workspace), str(self.application), json.dumps(asdict(limits)), *command]
        async with resources.heavy(self.owner) as receipt:
            # Offload drains bounded work even when the tool/run is cancelled.
            try:
                result = await self.runtime.offload(run_owned_command, self.workspace, argv, self.environment, limits)
            except ProcessCleanupFailed:
                resources.execution_failure = "owned_command_stop_unconfirmed"
                receipt["operational_error"] = resources.execution_failure
                raise ResourceRejected(resources.execution_failure, 0)
            except Exception as error:
                receipt["operational_error"] = type(error).__name__
                raise ResourceRejected("owned_command_controls_unavailable:" + type(error).__name__, 0) from error
            receipt["process_resources"] = result.resources
            if self.owner != "director":
                self.runtime.append_event(self.owner, "CoderExecutionReceipt", result.resources)
            elif self.runtime.repository is not None:
                from src.persistence.records import RecordKind, StoredRecord
                from uuid import uuid4
                self.runtime.repository.store.append(StoredRecord(kind=RecordKind.SERVICE_EVENT, record_id=str(uuid4()),
                    payload={"event_type": "CoderExecutionReceipt", "actor": "director",
                        "mission_id": self.runtime.mission_id, "cycle_id": self.runtime.cycle_id,
                        "resources": result.resources, "operational_only": True}))
            return CommandResult(exit_code=result.exit_code, stdout=result.stdout, stderr=result.stderr)



@dataclass
class ConfinedWorkspace(AbstractCapability):
    working_dir: Path
    application: Path

    def get_workspace(self, ctx, *, ref):
        paths = ctx.deps.runtime.runtime_paths
        if paths is not None:
            paths.require_owned(self.working_dir)
        backend = ConfinedBackend(self.working_dir, self.application, ctx.deps.runtime,
                                  getattr(ctx.deps, "block_id", "director"))
        return backend if ref is None or ref == backend.ref else None
