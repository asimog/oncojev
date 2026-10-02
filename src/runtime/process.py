"""Owned Linux command families: cgroup limits, quota workspace and exact cleanup.

The caller holds its heavy lease until this bounded supervisor returns. No host
command runs when the user manager, namespaces, or required kernel controls fail.
"""
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
from uuid import uuid4


@dataclass(frozen=True)
class ProcessLimits:
    processes: int = 16
    memory_mb: int = 512
    cpu: int = 2
    wall_seconds: float = 60
    workspace_bytes: int = 100_000_000
    output_bytes: int = 1_000_000
    minimum_free_disk_bytes: int = 10_000_000


@dataclass(frozen=True)
class ProcessResult:
    exit_code: int
    stdout: str
    stderr: str
    resources: dict
    stdout_raw: bytes = b""
    stderr_raw: bytes = b""


class ProcessCleanupFailed(RuntimeError):
    """A family may still be active; all further heavy execution must fail closed."""


def workspace_bytes(root):
    """Count owned regular files, never traverse external links/junctions."""
    total = 0
    for directory, folders, files in os.walk(root, followlinks=False):
        folders[:] = [name for name in folders if not (Path(directory) / name).is_symlink()
                      and not (Path(directory) / name).is_junction()]
        for name in files:
            entry = (Path(directory) / name).lstat()
            if stat.S_ISREG(entry.st_mode): total += entry.st_size
    return total


def run_owned_command(workspace, argv, environment, limits=ProcessLimits()):
    """Execute a foreground family and stop every descendant before returning."""
    if sys.platform != "linux" or platform.machine() != "x86_64":
        raise RuntimeError("owned command controls require Linux x86_64")
    workspace = Path(workspace).resolve(strict=True)
    if (os.getuid() == 0 or not workspace.is_dir() or workspace.stat().st_uid != os.getuid()
        or not os.access(workspace.parent, os.W_OK | os.X_OK)):
        raise RuntimeError("owned commands require a nonroot service and an owned directory")
    if shutil.disk_usage(workspace).free < 2 * limits.workspace_bytes + limits.minimum_free_disk_bytes:
        raise RuntimeError("insufficient disk headroom for bounded workspace commit")
    unit = "oncojev-command-" + uuid4().hex + ".service"
    # Reports live outside the writable workspace, never in untrusted stdout.
    metadata = Path(tempfile.mkdtemp(prefix="oncojev-command-", dir=workspace.parent))
    try:
        report = metadata / "resources.json"
        settings = {**asdict(limits), "workspace": str(workspace), "metadata": str(metadata),
                    "report": str(report), "argv": list(argv), "environment": dict(environment)}
        command = ["systemd-run", "--user", "--pipe", "--wait", "--quiet", "--expand-environment=no", "--unit=" + unit,
            "--property=TasksMax=" + str(limits.processes),
            "--property=MemoryMax=" + str(limits.memory_mb * 1024 * 1024),
            "--property=MemorySwapMax=0", "--property=CPUQuota=" + str(limits.cpu * 100) + "%",
            "--property=RuntimeMaxSec=" + str(limits.wall_seconds), "--property=TimeoutStopSec=2",
            "--property=KillMode=control-group", "--property=OOMPolicy=kill",
            "unshare", "--user", "--map-root-user", "--mount", "--net",
            "/usr/bin/env", "-i", "PATH=/usr/local/bin:/usr/bin:/bin",
            sys.executable, "-I", str(Path(__file__).with_name("process_exec.py")), json.dumps(settings)]
        try:
            completed = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True,
                timeout=limits.wall_seconds + 10, check=False)
            observed = json.loads(report.read_text()) if report.exists() else {}
            # Failure units remain loaded long enough to read native OOM/runtime
            # status. A missing counter remains unknown, never reported as zero.
            native = subprocess.run(["systemctl", "--user", "show", unit,
                "--property=Result,CPUUsageNSec,MemoryPeak,ControlGroup,ActiveState"],
                capture_output=True, text=True, timeout=5, check=False)
            observed["unit_observation"] = dict(line.split("=", 1) for line in native.stdout.splitlines() if "=" in line)
            observed.update(unit=unit, control_version="owned-command-v1", limits=asdict(limits),
                stdout_bytes=len(completed.stdout), stderr_bytes=len(completed.stderr))
            stdout, stderr = completed.stdout[:limits.output_bytes], completed.stderr[:limits.output_bytes]
            return ProcessResult(completed.returncode, stdout.decode(errors="replace"),
                stderr.decode(errors="replace"), observed, stdout, stderr)
        finally:
            # This runs outside the confined family, including on client timeout.
            try:
                stopped = subprocess.run(["systemctl", "--user", "stop", unit],
                    capture_output=True, timeout=5, check=False)
            except (OSError, subprocess.TimeoutExpired) as error:
                raise ProcessCleanupFailed("owned command stop could not be confirmed") from error
            if stopped.returncode:
                try:
                    state = subprocess.run(["systemctl", "--user", "is-active", unit],
                        capture_output=True, text=True, timeout=5, check=False)
                except (OSError, subprocess.TimeoutExpired) as error:
                    raise ProcessCleanupFailed("owned command state could not be confirmed") from error
                if state.stdout.strip() not in {"inactive", "failed", "unknown"}:
                    raise ProcessCleanupFailed("owned command family could not be stopped")
            if "observed" in locals() and observed.get("cgroup"):
                # systemd stop must also leave the entire recorded cgroup empty.
                # cgroup.events includes descendant groups, unlike cgroup.procs.
                events = Path(observed["cgroup"]) / "cgroup.events"
                try:
                    populated = dict(line.split() for line in events.read_text().splitlines()).get("populated")
                except FileNotFoundError:
                    populated = "0"  # Unloaded unit: its cgroup is already gone.
                except OSError as error:
                    raise ProcessCleanupFailed("owned command cgroup state could not be confirmed") from error
                if populated != "0":
                    raise ProcessCleanupFailed("owned command cgroup remains populated")
            backup = metadata / "previous"
            if backup.exists() and not workspace.exists():
                os.rename(backup, workspace)
            if "observed" in locals(): observed["cleanup_confirmed"] = True
            # Reaching here confirms stop. On an unconfirmed stop the metadata
            # and any recovery copy stay intact and the resource governor locks.
            shutil.rmtree(metadata)
            try:
                subprocess.run(["systemctl", "--user", "reset-failed", unit],
                    capture_output=True, timeout=5, check=False)
            except subprocess.TimeoutExpired:
                pass  # Housekeeping only: family termination is already confirmed.
    except BaseException:
        # Preserve diagnostics on startup/cleanup failures. Never recursively
        # remove a live family's files or its original scratch recovery copy.
        raise
