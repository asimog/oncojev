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


def restrict_process_authority(*, single_process=False):
    """Inherited x86_64 seccomp: no network, host process or namespace authority.

    Coder may create bounded children; scientific external operations are single
    process. Trusted supervisors apply quotas before installing this filter.
    """
    if sys.platform != "linux" or platform.machine() != "x86_64":
        raise RuntimeError("process confinement requires Linux x86_64")
    class Filter(ctypes.Structure):
        _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte), ("jf", ctypes.c_ubyte), ("k", ctypes.c_uint)]
    class Program(ctypes.Structure):
        _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.POINTER(Filter))]
    instructions = [(0x20, 0, 0, 4), (0x15, 1, 0, 0xc000003e), (0x06, 0, 0, 0x80000000),
                    (0x20, 0, 0, 0), (0x35, 0, 1, 0x40000000), (0x06, 0, 0, 0x80000000)]
    denied = (41, 42, 43, 49, 50, 53, 288, 62, 101, 200, 234, 310, 311,
              133, 259, 165, 166, 169, 246, 272, 308, 298, 304, 321, 424, 425, 434, 438)
    if single_process: denied += (56, 57, 58, 435, 109, 112)
    for syscall in denied: instructions.extend(((0x15, 0, 1, syscall), (0x06, 0, 0, 0x00050001)))
    instructions.append((0x06, 0, 0, 0x7fff0000))
    filters = (Filter * len(instructions))(*(Filter(*item) for item in instructions))
    program = Program(len(instructions), filters)
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(38, 1, 0, 0, 0) != 0 or libc.prctl(22, 2, ctypes.byref(program), 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "syscall confinement unavailable")


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
