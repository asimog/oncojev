"""Trusted Linux launcher: filesystem rights are inherited by all child commands.

Requires Landlock ABI >= 3 (including cross-directory rename and truncation).
No fallback executes an unconfined command. This is a coding boundary, not the
network-isolated, replay-validated scientific execution boundary.
"""

import ctypes
import os
from pathlib import Path
import platform
import sys
import json
import resource


PUBLIC_TREE = ("src", "config", "docs", "skills", "scripts", ".venv", "README.md", "AGENTS.md", "pyproject.toml", "uv.lock")


def confine(workspace: Path, application: Path, limits) -> None:
    # Standalone -I execution cannot rely on application imports being enabled.
    import importlib.util
    path = Path(__file__).resolve().parents[1] / 'confinement.py'
    spec = importlib.util.spec_from_file_location('oncojev_confinement', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.restrict_filesystem((workspace,),
        (*tuple(application / name for name in PUBLIC_TREE), Path(sys.prefix), Path(sys.base_prefix)))
    for limit, value in ((resource.RLIMIT_AS, limits["memory_mb"] * 1024 * 1024),
                        (resource.RLIMIT_FSIZE, limits["output_bytes"]),
                        (resource.RLIMIT_CPU, max(1, int(limits["wall_seconds"]))),
                        (resource.RLIMIT_CORE, 0), (resource.RLIMIT_NOFILE, 128)):
        resource.setrlimit(limit, (value, value))
    module.restrict_process_authority()


if __name__ == "__main__":
    try:
        workspace = Path(sys.argv[1]).resolve(strict=True)
        application = Path(sys.argv[2]).resolve(strict=True)
        confine(workspace, application, json.loads(sys.argv[3]))
        os.execvpe(sys.argv[4], sys.argv[4:], os.environ)
    except Exception as error:
        print(f"Confined command unavailable: {type(error).__name__}", file=sys.stderr)
        sys.exit(126)
