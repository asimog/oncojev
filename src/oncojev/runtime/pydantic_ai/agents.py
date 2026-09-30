from dataclasses import dataclass
from pydantic_ai import Agent
from oncojev.config.models import ModelsConfig
from oncojev.director.agent import DIRECTOR_INSTRUCTIONS
from oncojev.researcher.agent import RESEARCHER_INSTRUCTIONS
from oncojev.runtime.pydantic_ai.providers import configured_model, model_settings
@dataclass(frozen=True)
class OncoJevAgents: director:Agent[None,str]; researcher:Agent[None,str]
def create_agents(director_model:str,researcher_model:str)->OncoJevAgents:return OncoJevAgents(Agent(director_model,name="oncojev-director",instructions=DIRECTOR_INSTRUCTIONS),Agent(researcher_model,name="oncojev-researcher",instructions=RESEARCHER_INSTRUCTIONS))
def create_configured_agents(config:ModelsConfig)->OncoJevAgents:return OncoJevAgents(Agent(configured_model(config.director),name="oncojev-director",instructions=DIRECTOR_INSTRUCTIONS,model_settings=model_settings(config.director)),Agent(configured_model(config.researcher),name="oncojev-researcher",instructions=RESEARCHER_INSTRUCTIONS,model_settings=model_settings(config.researcher)))
