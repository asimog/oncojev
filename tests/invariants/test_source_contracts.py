"""Focused observable SDK boundary and reviewed-migration invariants."""
import asyncio
from pathlib import Path
import httpx
import pytest
from pydantic_ai import Agent
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelRequest, ModelResponse, RetryPromptPart, ToolCallPart, TextPart
from src.config.loader import load_models_config
from src.config.models import RuntimeConfig, RuntimeMode
from src.runtime.pydantic_ai.factory import build_harness_runtime
from src.runtime.pydantic_ai.contracts import ResearcherDeps, register_researcher_tools
from src.sources.public import GdcPublicSource
from src.persistence.store import SqliteResearchStore
from src.persistence.records import RecordKind
from src.oncolab.catalogue import initial_oncolab_index
from src.oncolab.registry import OncoLabIndex
from src.oncolab.institution import OncoLabInstitution, refresh_reviewed_search_metadata
ROOT=Path(__file__).resolve().parents[2]


def test_sdk_rejects_unknown_gdc_endpoint_before_transport_and_accepts_cases():
 async def run():
  runtime=build_harness_runtime(load_models_config(ROOT/'config/models.yaml'),RuntimeConfig(mode=RuntimeMode.DETERMINISTIC))
  original=runtime.gdc; requests=[]
  def transport(request):
   requests.append(request)
   return httpx.Response(200,json={'data':{'hits':[],'pagination':{'total':0}}})
  runtime.gdc=GdcPublicSource(httpx.MockTransport(transport))
  runtime.gdc.meter=original.meter;runtime.gdc.response_reserve=original.response_reserve
  block=runtime.manager.allocate('SDK source contract','controlled offline transport');runtime.research_state.start(block.block_id,block.objective)
  calls=0
  async def model(messages,info):
   nonlocal calls
   calls+=1
   if calls==1:
    return ModelResponse(parts=[ToolCallPart('acquire_gdc',{'endpoint':'ssms','filters':{},'fields':['id']},tool_call_id='invalid')])
   if calls==2:
    assert not requests
    assert any(isinstance(part,RetryPromptPart) for message in messages if isinstance(message,ModelRequest) for part in message.parts)
    return ModelResponse(parts=[ToolCallPart('acquire_gdc',{'endpoint':'cases','filters':{},'fields':['id']},tool_call_id='valid')])
   return ModelResponse(parts=[TextPart('observed')])
  agent=Agent(FunctionModel(model),deps_type=ResearcherDeps);register_researcher_tools(agent)
  try:
   await agent.run('exercise actual SDK endpoint validation',deps=ResearcherDeps(runtime,block.block_id))
   assert len(requests)==1 and requests[0].url.path=='/cases'
   assert runtime._counts[f'{block.block_id}:source']==1
   assert not any(e.event_type=='CapabilityFailure' for e in runtime.manager.ledger(block.block_id).history())
  finally:await asyncio.gather(original.aclose(),runtime.gdc.aclose(),runtime.xena.aclose(),runtime.literature.aclose())
 asyncio.run(run())


def test_source_metadata_review_preserves_routes_authority_old_pin_and_is_idempotent():
 store=SqliteResearchStore()
 try:
  seed=initial_oncolab_index(); descriptors=[d.model_copy(update={'limitations':('historical missing-wrapper declaration',)}) if d.capability_id=='source.gdc' else d for d in seed.descriptors()]
  old=OncoLabIndex(descriptors,routes=seed.routes);institution=OncoLabInstitution(store,old,'controlled-fixture');pin=institution.pin()
  assert refresh_reviewed_search_metadata(institution,seed,capability_id='source.gdc') is not None
  current=institution.index();before=old.describe('source.gdc');after=current.describe('source.gdc')
  assert current.routes==old.routes
  assert before.model_dump(exclude={'limitations'})==after.model_dump(exclude={'limitations'})
  assert institution.index(pin).describe('source.gdc')==before
  assert after.limitations==seed.describe('source.gdc').limitations
  count=len(store.records(kind=RecordKind.REGISTRY_REVISION))
  assert refresh_reviewed_search_metadata(institution,seed,capability_id='source.gdc') is None
  assert len(store.records(kind=RecordKind.REGISTRY_REVISION))==count
  with pytest.raises(ValueError,match='unsupported'):
   refresh_reviewed_search_metadata(institution,seed,capability_id='science.source-paired')
 finally:store.close()


from src.science.execution import ScienceExecutor
from src.science.models import InvalidAnalysis
from src.sources.models import AcquisitionRecord

@pytest.mark.parametrize("diagnoses", [[],[{"age_at_diagnosis":50}],[{"age_at_diagnosis":50},{"age_at_diagnosis":60}]])
def test_array_numeric_path_requires_explicit_representation(diagnoses):
    source=AcquisitionRecord(source="fixture",request={},records=({"id":"a","diagnoses":diagnoses},),provenance=("controlled source input",))
    with pytest.raises(InvalidAnalysis,match="array"):
        ScienceExecutor().measure_acquisition(source,"ages","diagnoses.age_at_diagnosis")


def test_dictionary_missingness_and_leaf_array_types_remain_distinct():
    rows=({"d":{"age":50}},{"d":{"age":None}},{"d":{}},{"d":{"age":[60]}})
    source=AcquisitionRecord(source="fixture",request={},records=rows,provenance=("controlled source input",))
    result=ScienceExecutor().measure_acquisition(source,"ages","d.age")
    assert {k:result.values[k] for k in ["valid_numeric","absent","null","invalid_type"]}=={"valid_numeric":1,"absent":1,"null":1,"invalid_type":1}
    assert result.values["mean"]==50
