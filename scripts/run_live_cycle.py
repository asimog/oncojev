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
from src.config.loader import load_models_config, load_runtime_config
from src.config.models import RuntimeMode
from src.runtime.cycle import run_cycle
from src.runtime.pydantic_ai.factory import build_system

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    load_local_environment(ROOT)
    missing = [name for name in ("OPENROUTER_API_KEY", "TYPESAFE_API_KEY") if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"live cycle requires: {', '.join(missing)}")

    models = load_models_config(ROOT / "config/models.yaml")
    policy = load_runtime_config(ROOT / "config/runtime.yaml")
    live_policy = policy.model_copy(update={"mode": RuntimeMode.LIVE})
    system = build_system(models, live_policy, max_tool_calls=int(policy.block["max_tool_calls"] or 100))
    result = run_cycle(system, "Investigate a public oncology question relevant to the project thesis.")

    print(
        json.dumps(
            {
                "mode": result.mode.value,
                "direction": result.direction,
                "director_output": result.director_output,
                "block_ids": list(result.block_ids),
                "dossiers": [dossier.model_dump(mode="json") for dossier in result.dossiers],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
