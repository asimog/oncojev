"""Prepare only the configured data root, then permanently drop worker privileges."""
import os
from pathlib import Path
import sys

from src.runtime.paths import data_root


def main():
    if os.getuid() == 0:
        root = data_root(Path(__file__).resolve().parents[1])
        if any(p.is_symlink() for p in (root, *root.parents)):
            raise RuntimeError("worker data root must not traverse links")
        root.mkdir(parents=True, exist_ok=True)
        os.chown(root, 1000, 1000)
        os.setgroups([])
        os.setgid(1000)
        os.setuid(1000)
    os.execv(sys.executable, [sys.executable, *sys.argv[1:]])


if __name__ == "__main__":
    main()
