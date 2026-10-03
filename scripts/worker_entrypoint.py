"""Prepare only the configured data root, then permanently drop worker privileges."""
import os
from pathlib import Path
import sys

from src.config.environment import process_settings


def main():
    if os.getuid() == 0:
        application = Path(__file__).resolve().parents[1]
        settings = process_settings(application)
        # Bootstrap prepares the base only. The final exec process owns its UUID.
        root = Path(settings.data_root) if settings.data_root else application / "var"
        if not root.is_absolute():
            raise ValueError("ONCOJEV_DATA_ROOT must be absolute")
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
