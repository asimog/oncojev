"""Shared unprivileged Linux filesystem boundary for Coder and Science."""
import ctypes
import os
from pathlib import Path
import platform
import sys

READ = (1 << 0) | (1 << 2) | (1 << 3)
ALL = (1 << 15) - 1


class Ruleset(ctypes.Structure):
    _fields_ = [("handled_access_fs", ctypes.c_uint64)]


class PathRule(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int)]


def restrict_filesystem(writable: tuple[Path, ...], readonly: tuple[Path, ...]) -> int:
    if sys.platform != "linux" or platform.machine() not in {"x86_64", "aarch64"}:
        raise RuntimeError("filesystem confinement requires Linux x86_64/aarch64")
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_long

    def syscall(number, *args):
        result = libc.syscall(ctypes.c_long(number), *args)
        if result < 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error))
        return result

    abi = syscall(444, 0, 0, 1)
    if abi < 3:
        raise RuntimeError("Landlock ABI >= 3 is required")
    handled = ALL | ((1 << 15) if abi >= 5 else 0)
    attributes = Ruleset(handled)
    ruleset = syscall(444, ctypes.byref(attributes), ctypes.sizeof(attributes), 0)
    try:
        def allow(path: Path, rights: int):
            if not path.exists():
                return
            descriptor = os.open(path, os.O_PATH | os.O_CLOEXEC)
            try:
                # Directory-only rights cannot be granted to individual files.
                if not path.is_dir():
                    rights &= (1 << 0) | (1 << 1) | (1 << 2) | (1 << 14) | (1 << 15)
                rule = PathRule(rights, descriptor)
                syscall(445, ruleset, 1, ctypes.byref(rule), 0)
            finally:
                os.close(descriptor)

        for root in ("/usr", "/bin", "/sbin", "/lib", "/lib64", "/etc"):
            allow(Path(root), READ)
        for path in readonly:
            allow(path, READ)
        for path in writable:
            allow(path, handled)
        for device in ("/dev/null", "/dev/zero", "/dev/random", "/dev/urandom"):
            allow(Path(device), (1 << 1) | (1 << 2) | ((1 << 15) if abi >= 5 else 0))
        if libc.prctl(38, 1, 0, 0, 0) != 0:  # PR_SET_NO_NEW_PRIVS
            raise OSError(ctypes.get_errno(), "no_new_privs failed")
        syscall(446, ruleset, 0)
    finally:
        os.close(ruleset)

    return abi
