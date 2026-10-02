"""Pydantic AI construction; each JevBlock receives a fresh Researcher instance."""

from collections.abc import Callable
from dataclasses import dataclass
import os
import math
from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai_harness import CodeMode
from pydantic_ai_harness.coder import Coder
from pydantic_ai_harness.shell import Shell

from src.config.environment import load_local_environment
from src.config.models import ModelsConfig
from src.director.agent import DIRECTOR_INSTRUCTIONS
from src.researcher.agent import RESEARCHER_INSTRUCTIONS
from src.runtime.pydantic_ai.contracts import DirectorDeps, ResearcherDeps, register_director_tools, register_researcher_tools
from src.runtime.pydantic_ai.providers import configured_model, model_settings
from src.runtime.pydantic_ai.telemetry import configure_agent_telemetry
from src.runtime.pydantic_ai.controls import RuntimeControls
from src.runtime.pydantic_ai.workspace import ConfinedWorkspace
from src.runtime.pydantic_ai.shell import owned_shell
from src.runtime.paths import select_paths
from src.config.environment import process_settings


def _code_mode_tools(_ctx: object, tool_definition: object) -> bool:
    """Keep Coder workspace tools direct and domain tools available in Code Mode."""
    return getattr(tool_definition, "name", None) not in {
        "read_file", "write_file", "edit_file", "list_files", "grep", "shell", "delegate_task"
    }


def _runtime_capabilities(workspace: Path, max_tool_calls: int, role: str, *, enable_coder: bool = True, unbounded_work: bool = False) -> list[object]:
    """Compose writable Coder workspace tools with typed domain orchestration."""
    # The SDK requires a positive snippet limit. Our preflight disables run_code
    # entirely for configured zero, before the SDK can execute a snippet.
    sdk_tool_calls = 1 if max_tool_calls == 0 else max_tool_calls
    # The pinned SDK compares integer counts against this value; infinity
    # removes its application dispatch/retry ceilings without a larger quota.
    code = CodeMode(tools=_code_mode_tools, max_tool_calls=math.inf if unbounded_work else sdk_tool_calls,
                    max_retries=math.inf if unbounded_work else 3,
                    resource_limits={"max_duration_secs": None, "max_memory": None,
                                     "max_suspensions": (1 << 64) - 1} if unbounded_work else None)
    capabilities: list[object] = [RuntimeControls(role, max_tool_calls), code]
    if enable_coder and os.name == "posix":
        workspace.mkdir(parents=True, exist_ok=True)
        coder = Coder(sub_agents=False, unrestricted_filesystem=True).visit_and_replace(
            lambda capability: owned_shell() if isinstance(capability, Shell) else capability)
        capabilities[:0] = [
            ConfinedWorkspace(workspace, Path(__file__).resolve().parents[3]),
            coder,
        ]
    return capabilities


@dataclass(frozen=True)
class OncoJevAgents:
    director: Agent[DirectorDeps, str]
    researcher: Agent[ResearcherDeps, str]
    _fresh_researcher: Callable[[str | None], Agent[ResearcherDeps, str]]

    def fresh_researcher(self, block_id: str | None = None) -> Agent[ResearcherDeps, str]:
        """Create an agent with no previous run history or block skill selections."""
        return self._fresh_researcher(block_id)


def _build(
    director_model: object, researcher_model: object, max_tool_calls: int,
    director_settings: dict | None = None, researcher_settings: dict | None = None,
    researcher_code_calls: int | None = None,
    director=None,
    paths=None,
    enable_coder: bool = True,
    unbounded_work: bool = False,
) -> OncoJevAgents:
    workspace = Path(__file__).resolve().parents[3]
    paths = paths or select_paths(workspace, process_settings(workspace))

    def build_researcher(block_id: str | None = None) -> Agent[ResearcherDeps, str]:
        researcher_workspace = paths.workspaces / (block_id or "unassigned")
        paths.require_owned(researcher_workspace)
        if not researcher_workspace.resolve().is_relative_to(paths.workspaces.resolve()):
            raise ValueError("Researcher workspace must remain under the block workspace root")
        researcher = Agent(
            researcher_model, name="oncojev-researcher", instructions=RESEARCHER_INSTRUCTIONS,
            deps_type=ResearcherDeps, model_settings=researcher_settings,
            capabilities=_runtime_capabilities(researcher_workspace, max_tool_calls if researcher_code_calls is None else researcher_code_calls, "researcher", enable_coder=enable_coder, unbounded_work=unbounded_work),
            retries={"tools": math.inf, "output": math.inf} if unbounded_work else 1, defer_model_check=True,
        )
        register_researcher_tools(researcher)
        return researcher

    fresh_director = director is None
    director = director or Agent(
        director_model, name="oncojev-director", instructions=DIRECTOR_INSTRUCTIONS,
        deps_type=DirectorDeps, model_settings=director_settings,
        capabilities=_runtime_capabilities(paths.require_owned(paths.director), max_tool_calls, "director", enable_coder=enable_coder, unbounded_work=unbounded_work),
        retries={"tools": math.inf, "output": math.inf} if unbounded_work else 1, defer_model_check=True,
    )
    if fresh_director:
        register_director_tools(director)
    return OncoJevAgents(director=director, researcher=build_researcher(), _fresh_researcher=build_researcher)


def create_agents(director_model: str, researcher_model: str, max_tool_calls: int = 100, *, enable_coder: bool = True, unbounded_work: bool = False) -> OncoJevAgents:
    """Fixture entry point; disable Coder explicitly for offline scripted checks."""
    return _build(director_model, researcher_model, max_tool_calls, enable_coder=enable_coder, unbounded_work=unbounded_work)


def create_configured_agents(config: ModelsConfig, max_tool_calls: int = 100, researcher_code_calls: int | None = None, *, director=None, paths=None, unbounded_work: bool = False) -> OncoJevAgents:
    if paths is None:
        load_local_environment()
    configure_agent_telemetry()
    return _build(
        configured_model(config.director), configured_model(config.researcher), max_tool_calls,
        model_settings(config.director), model_settings(config.researcher),
        researcher_code_calls,
        director,
        paths,
        unbounded_work=unbounded_work,
    )
