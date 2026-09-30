"""Run a bounded public OncoLab demonstration with configured agents.

Loads local credentials only into this process. It never prints them or grants
Coder child commands credential or controlled-data access. Coder workspace tools
cannot substitute for typed acquisition or the scientific sandbox.
"""

import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from src.block.manager import BlockManager
from src.config.environment import load_local_environment
from src.config.loader import load_models_config, load_runtime_config
from src.director.models import ResourceAllocation
from src.jev.client import DeterministicJevClient
from src.ledger.events import LedgerEvent
from pydantic_ai.messages import ModelResponse
from src.reasoner.service import DeterministicReasoner
from src.runtime.pydantic_ai.agents import create_configured_agents
from src.runtime.pydantic_ai.contracts import HarnessRuntime, ResearcherDeps
from src.science.execution import ScienceExecutor


ROOT = Path(__file__).resolve().parents[1]


async def main() -> None:
    load_local_environment(ROOT)
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise RuntimeError("OPENROUTER_API_KEY is required in .env.local for a live run")

    models = load_models_config(ROOT / "config/models.yaml")
    policy = load_runtime_config(ROOT / "config/runtime.yaml")
    runtime = HarnessRuntime(
        manager=BlockManager(),
        jev=DeterministicJevClient(),
        science=ScienceExecutor(),
        reasoner=DeterministicReasoner(),
        max_jev_calls=int(policy.block["max_jev_calls"] or 4),
        max_reasoner_calls=int(policy.block["max_reasoner_calls"] or 2),
        max_source_calls=int(policy.block["max_source_calls"] or 20),
    )
    agents = create_configured_agents(models, max_tool_calls=int(policy.block["max_tool_calls"] or 100))
    runtime.researcher_factory = agents.fresh_researcher
    block = runtime.manager.create(
        "Explore a public oncology question using only methods justified by the OncoLab Index.",
        "Validate that independently selectable public acquisition, deterministic analysis, literature, and visualization tools can coexist in one bounded block.",
        allocation=ResourceAllocation(seconds=int(policy.block["default_seconds"] or 600)),
    )
    prompt = """You are operating a bounded public JevBlock. Search the OncoLab Index first.
Choose and invoke, when useful to this objective, a public source, public literature search,
one deterministic statistical method, and a visualization. Source output is acquisition context,
not evidence. Admit a result only after deterministic measurement. Do not request credentials,
controlled data, or a fixed analysis sequence. Do not use Coder shell/filesystem tools for
scientific execution; use typed wrappers and the scientific sandbox. Finish the block and report a
short summary of the independently chosen work."""
    ledger = runtime.manager.ledger(block.block_id)
    ledger.append(LedgerEvent(event_type="ResearcherRunStarted", occurred_at=datetime.now(UTC), payload={"block_id": block.block_id, "provider": "openrouter"}))
    try:
        result = await agents.fresh_researcher().run(prompt, deps=ResearcherDeps(runtime=runtime, block_id=block.block_id))
    except Exception as error:
        ledger.append(LedgerEvent(event_type="ResearcherRunFailed", occurred_at=datetime.now(UTC), payload={"error_type": type(error).__name__}))
        raise
    resolved_models = tuple(
        sorted(
            {
                message.model_name
                for message in result.all_messages()
                if isinstance(message, ModelResponse) and message.model_name
            }
        )
    )
    ledger.append(LedgerEvent(event_type="ResearcherRunCompleted", occurred_at=datetime.now(UTC), payload={"block_id": block.block_id, "resolved_models": resolved_models}))
    events = runtime.manager.ledger(block.block_id).history()
    print(json.dumps({"output": result.output, "block_id": block.block_id, "events": [event.model_dump(mode="json") for event in events]}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
