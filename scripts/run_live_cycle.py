"""Run one complete live Director -> Researcher cycle with configured agents.

Requires OPENROUTER_API_KEY (Director/Researcher/Reasoner) and TYPESAFE_API_KEY
(Jev). Credentials enter this worker process only; they are never placed in
agent context and are never shared with the scientific sandbox.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from src.config.environment import load_local_environment
from src.autonomous import service_from_environment

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    load_local_environment(ROOT)
    missing = [name for name in ("OPENROUTER_API_KEY", "TYPESAFE_API_KEY") if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"live cycle requires: {', '.join(missing)}")

    service = service_from_environment(ROOT)
    try:
        result = service.run_once(
            "Validate one autonomous public-data path. Allocate exactly one block. In that block, acquire at most three public GDC case records, measure and admit their source-bound record count, evaluate that candidate once with Jev, ask the Reasoner for one hypothesis, then complete the block. Do not repeat equivalent calls.",
        )
    finally:
        service.close()

    print(
        json.dumps(
            {
                "mode": result.mode.value,
                "direction": result.direction,
                "director_output": result.director_output,
                "block_ids": list(result.block_ids),
                "dossiers": [dossier.model_dump(mode="json") for dossier in result.dossiers],
                "status": result.status.value,
                "director_outcome": result.director_outcome.value,
                "director_error_type": result.director_error_type,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
