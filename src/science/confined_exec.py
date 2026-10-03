"""Trusted scientific subprocess launcher, fail-closed before external code."""
import ctypes
import importlib.util
import json
import os
from pathlib import Path
import platform
import resource
import sys


class Filter(ctypes.Structure):
    _fields_=[('code',ctypes.c_ushort),('jt',ctypes.c_ubyte),('jf',ctypes.c_ubyte),('k',ctypes.c_uint)]


class Program(ctypes.Structure):
    _fields_=[('len',ctypes.c_ushort),('filter',ctypes.POINTER(Filter))]


def deny_external_authority():
    if sys.platform!='linux' or platform.machine()!='x86_64':raise RuntimeError('scientific seccomp requires Linux x86_64')
    # Validate ABI and reject x32 before interpreting syscall numbers. External
    # operations are single-process: no fork/threads, networking, process access,
    # signalling, namespace changes or io_uring bypass. Restrictions inherit.
    instructions=[(0x20,0,0,4),(0x15,1,0,0xc000003e),(0x06,0,0,0x80000000),
                  (0x20,0,0,0),(0x35,0,1,0x40000000),(0x06,0,0,0x80000000)]
    denied=(41,42,43,49,50,53,288,56,57,58,435,62,101,109,112,200,234,310,311,
            165,166,169,246,272,308,298,304,321,424,425,434,438)
    for syscall in denied:instructions.extend(((0x15,0,1,syscall),(0x06,0,0,0x00050001)))
    instructions.append((0x06,0,0,0x7fff0000))
    filters=(Filter*len(instructions))(*(Filter(*item) for item in instructions))
    program=Program(len(instructions),filters)
    libc=ctypes.CDLL(None,use_errno=True)
    if libc.prctl(38,1,0,0,0)!=0 or libc.prctl(22,2,ctypes.byref(program),0,0)!=0:
        raise OSError(ctypes.get_errno(),'scientific syscall confinement unavailable')


def main():
    settings=json.loads(sys.argv[1])
    root=Path(settings['root']).resolve(strict=True)
    application=Path(settings['application']).resolve(strict=True)
    phase=settings['phase']
    path=application/'src'/'runtime'/'confinement.py'
    spec=importlib.util.spec_from_file_location('oncojev_confinement',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    # Inputs are read-only. Install mutates its fresh venv and bounded temporary directory;
    # tests/execution write only inherited bounded stdout/stderr, never filesystem state.
    writable=(root/'venv',root/'outputs'/'install-temp') if phase=='install' else ()
    readonly=(root/'repository',root/'venv',root/'inputs',application/'src',application/'config',Path(sys.base_prefix))
    module.restrict_filesystem(writable,readonly)
    for limit,value in ((resource.RLIMIT_AS,settings['memory_mb']*1024*1024),
                        (resource.RLIMIT_CPU,settings['timeout']),
                        (resource.RLIMIT_FSIZE,settings['max_output_bytes']),
                        (resource.RLIMIT_NOFILE,64),(resource.RLIMIT_CORE,0)):
        resource.setrlimit(limit,(value,value))
    deny_external_authority()
    os.chdir(root/'repository')
    os.execvpe(sys.argv[2],sys.argv[2:],os.environ)


if __name__=='__main__':
    try:main()
    except BaseException as error:
        print('Scientific confinement unavailable: '+type(error).__name__,file=sys.stderr)
        sys.exit(126)
