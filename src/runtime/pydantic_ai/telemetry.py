"""Process-wide agent diagnostics, separate from scientific records."""

from importlib.metadata import version
import os
from pathlib import Path
from threading import Lock

import logfire


_lock = Lock()
_configured = False


def configure_agent_telemetry() -> None:
    """Configure once before constructing live agents; never capture message content."""
    global _configured
    with _lock:
        if _configured:
            return
        root = Path(__file__).resolve().parents[3]
        logfire.configure(
            send_to_logfire=None if "LOGFIRE_SEND_TO_LOGFIRE" in os.environ else "if-token-present",
            service_name="oncojev-agents",
            service_version=version("oncojev"),
            data_dir=root / ".logfire",
            config_dir=root,
            console=False,
        )
        logfire.instrument_pydantic_ai(include_content=False, include_binary_content=False)
        _configured = True
