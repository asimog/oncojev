from dataclasses import dataclass
from pathlib import Path
from pydantic_ai import Agent
from pydantic_ai_harness import CodeMode
from src.config.environment import load_local_environment
from src.config.models import ModelsConfig
from src.director.agent import DIRECTOR_INSTRUCTIONS
from src.researcher.agent import RESEARCHER_INSTRUCTIONS
from src.runtime.pydantic_ai.contracts import DirectorDeps,ResearcherDeps,register_director_tools,register_researcher_tools
from src.runtime.pydantic_ai.workspace_tools import register_workspace_tools
from src.runtime.pydantic_ai.providers import configured_model, model_settings
@dataclass(frozen=True)
class OncoJevAgents: director:Agent[DirectorDeps,str]; researcher:Agent[ResearcherDeps,str]
def _build(director_model:object,researcher_model:object,max_tool_calls:int,director_settings:dict|None=None,researcher_settings:dict|None=None)->OncoJevAgents:
 workspace=Path.cwd()
 def harness(): return [CodeMode(tools="all",max_tool_calls=max_tool_calls)]
 researcher=Agent(researcher_model,name="oncojev-researcher",instructions=RESEARCHER_INSTRUCTIONS,deps_type=ResearcherDeps,model_settings=researcher_settings,capabilities=harness())
 director=Agent(director_model,name="oncojev-director",instructions=DIRECTOR_INSTRUCTIONS,deps_type=DirectorDeps,model_settings=director_settings,capabilities=harness())
 register_researcher_tools(researcher);register_director_tools(director);register_workspace_tools(researcher,workspace);register_workspace_tools(director,workspace);return OncoJevAgents(director=director,researcher=researcher)
def create_agents(director_model:str,researcher_model:str,max_tool_calls:int=100)->OncoJevAgents:return _build(director_model,researcher_model,max_tool_calls)
def create_configured_agents(config:ModelsConfig,max_tool_calls:int=100)->OncoJevAgents:
 load_local_environment();return _build(configured_model(config.director),configured_model(config.researcher),max_tool_calls,model_settings(config.director),model_settings(config.researcher))
