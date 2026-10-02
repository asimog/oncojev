"""Trusted user-namespace supervisor; never exposed as an agent tool.

An actual tmpfs quota bounds aggregate files and inodes. Only after all children
are gone does trusted code commit the resulting scratch tree. Original scratch
survives a command-family crash before commit. Authoritative data is never mounted.
"""
import ctypes
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time


def directory_bytes(root):
    return sum(path.stat().st_size for path in root.rglob("*") if not path.is_symlink() and path.is_file())


def main():
    settings = json.loads(sys.argv[1])
    workspace = Path(settings["workspace"])
    metadata = Path(settings["metadata"])
    report = Path(settings["report"])
    membership = Path("/proc/self/cgroup").read_text().strip()
    cgroup = Path("/sys/fs/cgroup") / Path(membership.split("::", 1)[1]).relative_to("/")
    quota = (cgroup / "cpu.max").read_text().split()
    if (int((cgroup / "pids.max").read_text()) != settings["processes"]
        or int((cgroup / "memory.max").read_text()) != settings["memory_mb"] * 1024 * 1024
        or int((cgroup / "memory.swap.max").read_text()) != 0
        or quota[0] == "max" or int(quota[0]) > settings["cpu"] * int(quota[1])):
        raise RuntimeError("required cgroup controls are not effective")
    observed = {"kernel_controls_verified": True, "cgroup": str(cgroup),
        "workspace_before_bytes": directory_bytes(workspace), "status": "starting"}
    report.write_text(json.dumps(observed))
    mount = metadata / "volume"
    mount.mkdir()
    subprocess.run(["mount", "-t", "tmpfs", "-o",
        f'size={settings["workspace_bytes"]},nr_inodes=20000,mode=700', "tmpfs", str(mount)], check=True)
    # Preserve symlinks as symlinks: never copy bytes through external pointers.
    shutil.copytree(workspace, mount, symlinks=True, dirs_exist_ok=True)
    subprocess.run(["mount", "--bind", str(mount), str(workspace)], check=True)
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:  # PR_SET_CHILD_SUBREAPER
        raise RuntimeError("descendant ownership unavailable")
    started = time.monotonic()
    stdout_path, stderr_path = mount / ".owned-stdout", mount / ".owned-stderr"
    output_flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
    with os.fdopen(os.open(stdout_path, output_flags, 0o600), "w+b") as stdout, \
         os.fdopen(os.open(stderr_path, output_flags, 0o600), "w+b") as stderr:
        # Keep bounded diagnostic headroom inside the same quota even when
        # scratch fills it. Read only the actual shared-descriptor write extent.
        for output in (stdout, stderr):
            output.write(b"\0" * min(65536, settings["output_bytes"]))
            output.flush(); output.seek(0)
        child = subprocess.Popen(settings["argv"], cwd=workspace, env=settings["environment"],
            stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, close_fds=True)
        timed_out = False
        try:
            exit_code = child.wait(timeout=settings["wall_seconds"])
        except subprocess.TimeoutExpired:
            timed_out = True
            exit_code = 124
        finally:
            # All members of this private family belong to this one command.
            # Reparent detached grandchildren to this subreaper and drain them.
            deadline = time.monotonic() + 2
            while True:
                pids = {int(value) for value in (cgroup / "cgroup.procs").read_text().split()} - {os.getpid()}
                for pid in pids:
                    try:
                        # Managed Python builds need not expose the optional
                        # pidfd wrappers. The required x86_64 kernel ABI does.
                        descriptor = libc.syscall(434, pid, 0)
                        if descriptor < 0: raise OSError(ctypes.get_errno(), "pidfd_open failed")
                        try:
                            if Path(f"/proc/{pid}/cgroup").read_text().strip() == membership:
                                if libc.syscall(424, descriptor, signal.SIGKILL, 0, 0) < 0:
                                    raise OSError(ctypes.get_errno(), "pidfd_send_signal failed")
                        finally: os.close(descriptor)
                    except (ProcessLookupError, FileNotFoundError): pass
                while True:
                    try:
                        if os.waitpid(-1, os.WNOHANG)[0] == 0: break
                    except ChildProcessError: break
                if not pids: break
                if time.monotonic() >= deadline: raise RuntimeError("descendants did not drain")
                time.sleep(.01)
        # Keep the trusted descriptors: a command may replace its stdout path
        # with a symlink, which must never make us read a host credential file.
        lengths = [os.lseek(output.fileno(), 0, os.SEEK_CUR) for output in (stdout, stderr)]
        stdout.seek(0); stderr.seek(0)
        sys.stdout.buffer.write(stdout.read(min(lengths[0], settings["output_bytes"])))
        sys.stderr.buffer.write(stderr.read(min(lengths[1], settings["output_bytes"])))
    observed.update(status="timed_out" if timed_out else "complete", exit_code=exit_code, descendants_drained=True,
        wall_seconds=time.monotonic() - started, workspace_after_bytes=directory_bytes(mount),
        cpu_stat=(cgroup / "cpu.stat").read_text(), memory_peak=int((cgroup / "memory.peak").read_text()),
        pids_peak=int((cgroup / "pids.peak").read_text()) if (cgroup / "pids.peak").exists() else None,
        disk_quota_bytes=settings["workspace_bytes"], inode_quota=20000)
    stdout_path.unlink(); stderr_path.unlink()
    if timed_out:
        observed["workspace_committed"] = False
        report.write_text(json.dumps(observed))
        sys.exit(exit_code)
    # Unmount the bind before changing the persistent path; the bounded tmpfs
    # remains mounted at `mount`. Stage on the same filesystem as scratch.
    subprocess.run(["umount", str(workspace)], check=True)
    stage, backup = metadata / "staged", metadata / "previous"
    shutil.copytree(mount, stage, symlinks=True)
    os.rename(workspace, backup)
    try: os.rename(stage, workspace)
    except BaseException:
        os.rename(backup, workspace)
        raise
    observed["workspace_committed"] = True
    report.write_text(json.dumps(observed))
    # `metadata` is service-created beside scratch; these paths never come
    # from an untrusted command. No recursive deletion follows symlinks.
    shutil.rmtree(backup)
    subprocess.run(["umount", str(mount)], check=True)
    sys.exit(exit_code)


if __name__ == "__main__":
    try: main()
    except Exception as error:
        print("Owned command controls unavailable: " + type(error).__name__ + ": " + str(error), file=sys.stderr)
        sys.exit(126)
