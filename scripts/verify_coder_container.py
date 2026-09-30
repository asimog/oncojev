"""Verify both OncoJev roles compose Coder and Code Mode in Linux Docker."""

from __future__ import annotations

import json

from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import FunctionModel

from src.block.manager import BlockManager
from src.director.models import ResourceAllocation
from src.jev.client import DeterministicJevClient
from src.reasoner.service import DeterministicReasoner
from src.runtime.pydantic_ai.agents import create_agents
from src.runtime.pydantic_ai.contracts import DirectorDeps, HarnessRuntime, ResearcherDeps
from src.science.execution import ScienceExecutor


def _model(role: str):
    calls = 0

    async def respond(_messages, info):
        nonlocal calls
        calls += 1
        tools = {tool.name for tool in info.function_tools}
        assert {"list_files", "shell", "run_code"} <= tools
        if calls == 1:
            return ModelResponse(parts=[ToolCallPart("list_files", {"path": "."}, tool_call_id=f"{role}-coder")])
        if calls == 2:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "run_code",
                        {"code": f'await search_oncolab(query="GDC", kinds=["source"], limit=1)\n"{role} code mode complete"'},
                        tool_call_id=f"{role}-code-mode",
                    )
                ]
            )
        return ModelResponse(parts=[TextPart(f"{role} complete")])

    return FunctionModel(respond)


def main() -> None:
    runtime = HarnessRuntime(
        manager=BlockManager(),
        jev=DeterministicJevClient(),
        science=ScienceExecutor(),
        reasoner=DeterministicReasoner(),
        max_jev_calls=2,
        max_reasoner_calls=1,
    )
    block = runtime.manager.create("Coder smoke block", "verify harness composition", ResourceAllocation(seconds=60))
    runtime.research_state.start(block.block_id, block.objective)
    runtime.skills.start(block.block_id)
    agents = create_agents("test", "test")

    with agents.director.override(model=_model("director")):
        director = agents.director.run_sync("Inspect the workspace and OncoLab Index.", deps=DirectorDeps(runtime))
    with agents.fresh_researcher().override(model=_model("researcher")):
        researcher = agents.fresh_researcher().run_sync(
            "Inspect the workspace and OncoLab Index.", deps=ResearcherDeps(runtime, block.block_id)
        )

    assert director.output == "director complete"
    assert researcher.output == "researcher complete"
    print(json.dumps({"director": director.output, "researcher": researcher.output, "workspace": "container"}))


if __name__ == "__main__":
    main()
