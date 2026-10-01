"""Export a deterministic research snapshot for the observability UI.

Runs one fully offline scripted cycle (no provider credentials, no network) so a
representative, reproducible snapshot can be committed for the web build. This is
tooling, not part of the runtime: Pydantic AI models are scripted here only.

Usage: python scripts/export_snapshot.py [--out web/data/snapshot.json]
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import DeltaToolCall, FunctionModel

from src.application.service import ResearchApplication
from src.block.manager import BlockManager
from src.config.models import RuntimeMode
from src.evals.harness import CONDITIONS
from src.jev.client import DeterministicJevClient
from src.persistence.repository import ResearchRepository
from src.persistence.store import SqliteResearchStore
from src.reasoner.service import DeterministicReasoner
from src.runtime.cycle import run_cycle
from src.runtime.pydantic_ai.agents import create_agents
from src.runtime.pydantic_ai.contracts import HarnessRuntime
from src.runtime.pydantic_ai.factory import ConfiguredSystem
from src.science.execution import ScienceExecutor
from src.sources.models import AcquisitionRecord

ROOT = Path(__file__).resolve().parents[1]


def scripted(function):
    async def stream(messages, info):
        response = await function(messages, info)
        tool_calls = {index: part for index, part in enumerate(response.parts) if isinstance(part, ToolCallPart)}
        if tool_calls:
            yield {
                index: DeltaToolCall(name=part.tool_name, json_args=part.args_as_json_str(), tool_call_id=part.tool_call_id)
                for index, part in tool_calls.items()
            }
            return
        text = "".join(part.content for part in response.parts if isinstance(part, TextPart))
        if text:
            yield text

    return FunctionModel(function=function, stream_function=stream)


def _run_scripted_cycle() -> tuple[SqliteResearchStore, ResearchApplication]:
    store = SqliteResearchStore()
    repository = ResearchRepository(store)
    manager = BlockManager()
    runtime = HarnessRuntime(
        manager=manager,
        jev=DeterministicJevClient(),
        science=ScienceExecutor(),
        reasoner=DeterministicReasoner(),
        max_jev_calls=4,
        max_reasoner_calls=2,
    )
    acquisition = AcquisitionRecord(source="gdc", request={"snapshot": True}, records=({"file_id": "demo-a"}, {"file_id": "demo-b"}), provenance=("offline-snapshot",))
    runtime.acquisitions[acquisition.acquisition_id] = acquisition
    agents = create_agents("test", "test")
    runtime.researcher = agents.researcher
    system = ConfiguredSystem(agents=agents, runtime=runtime, mode=RuntimeMode.DETERMINISTIC)
    director_calls = 0
    researcher_calls = 0

    async def director_model(messages, info):
        nonlocal director_calls
        director_calls += 1
        if director_calls == 1:
            code = (
                'block = await allocate_block(objective="Assess a public treatment-resistance signal", why_now="No admitted evidence addresses the direction.", seconds=600)\n'
                'await launch_researcher(block_id=block["block_id"])\nblock'
            )
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": code}, tool_call_id="d1")])
        return ModelResponse(parts=[TextPart("Director allocated one bounded block and launched the Researcher.")])

    async def researcher_model(messages, info):
        nonlocal researcher_calls
        researcher_calls += 1
        if researcher_calls == 1:
            code = "\n".join(
                [
                    f'await measure_acquisition(acquisition_id="{acquisition.acquisition_id}", analysis_id="summary")',
                    'await admit_measurement(analysis_id="summary")',
                    f'await measure_acquisition(acquisition_id="{acquisition.acquisition_id}", analysis_id="replicate")',
                    'await admit_measurement(analysis_id="replicate")',
                    'await evaluate_candidate(candidate_id="candidate", candidate_summary="synthetic subgroup signal")',
                    'await generate_hypotheses(finding="Measured association with a modest effect")',
                    'await complete_block(reason="researcher_complete")',
                    '"researcher complete"',
                ]
            )
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": code}, tool_call_id="r1")])
        return ModelResponse(parts=[TextPart("Researcher completed bounded deterministic measurements.")])

    with agents.director.override(model=scripted(director_model)), agents.researcher.override(model=scripted(researcher_model)):
        run_cycle(system, "Investigate a public oncology direction relevant to the project thesis.", repository=repository, mission_id="demo-mission")
    return store, ResearchApplication(store)


def build_snapshot() -> dict:
    store, application = _run_scripted_cycle()
    blocks = []
    for view in application.blocks():
        reconstruction = application.reconstruction(view["block_id"])
        blocks.append(
            {
                "summary": view,
                "reconstruction": reconstruction.model_dump(mode="json"),
            }
        )
    snapshot = {
        "generated_at": datetime.now(UTC).isoformat(),
        "conditions": [condition.value for condition in CONDITIONS],
        "overview": application.overview(),
        "research_memory": list(application.research_memory()),
        "blocks": blocks,
    }
    store.close()
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(ROOT / "web/data/snapshot.json"))
    arguments = parser.parse_args()
    out = Path(arguments.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build_snapshot(), indent=2, default=str), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
