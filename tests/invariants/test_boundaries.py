import os
import subprocess
from datetime import UTC,datetime,timedelta
from pathlib import Path
import pytest
import httpx
from pydantic import ValidationError
from pydantic_ai.messages import ModelResponse,TextPart,ToolCallPart
from pydantic_ai.models.function import DeltaToolCall,FunctionModel
from src.block.manager import BlockManager,HandoffRequired
from src.block.models import BlockStatus
from src.oncolab.catalogue import initial_oncolab_index
from src.oncolab.models import OncoLabKind
from src.config.loader import load_models_config
from src.director.models import ResourceAllocation
from src.dossier.models import JevBlockDossier
from src.jev.client import DeterministicJevClient
from src.jev.frontier import CandidateFrontierPolicy,FrontierAction
from src.jev.models import ChoiceDecision,JevExecutionFailure,JevFailureCategory,JevQuestionSpec,NoulDecision
from src.ledger.events import LedgerEvent
from src.ledger.store import Ledger
from src.reasoner.models import Hypothesis,ReasonerOutput
from src.runtime.pydantic_ai.agents import create_agents
from src.runtime.pydantic_ai.contracts import DirectorDeps,HarnessRuntime,ResearcherDeps
from src.science.execution import ScienceExecutor
from src.science.models import AnalysisSpec
from src.reasoner.service import DeterministicReasoner
from src.sources.public import GdcPublicSource,PublicLiteratureSource,XenaPublicSource
from src.science.admission import admit_scientific_evidence
from src.config.environment import load_local_environment
from src.researcher.state import ProjectionSpec,ResearchState,StateFragment,project_state
from src.oncolab.labskills import BlockSkillStore
from src.science.sandbox import DockerScientificSandbox,GithubMethodRequest,SandboxError,SandboxInvocation,SandboxMeasurementCandidate,SandboxReceipt,validate_sandbox_candidate
ROOT=Path(__file__).resolve().parents[2]
def scripted(function):
 """Coder bundles RepoContext, so POSIX runs stream; adapt a scripted response for both paths."""
 async def stream(messages,info):
  response=await function(messages,info)
  tool_calls={index:part for index,part in enumerate(response.parts) if isinstance(part,ToolCallPart)}
  if tool_calls:
   yield {index:DeltaToolCall(name=part.tool_name,json_args=part.args_as_json_str(),tool_call_id=part.tool_call_id) for index,part in tool_calls.items()}
   return
  text=''.join(part.content for part in response.parts if isinstance(part,TextPart))
  if text:yield text
 return FunctionModel(function=function,stream_function=stream)
def test_local_credentials_are_loaded_without_overriding_host_environment(tmp_path,monkeypatch):
 monkeypatch.delenv('OPENROUTER_API_KEY',raising=False);monkeypatch.delenv('TYPESAFE_API_KEY',raising=False)
 (tmp_path/'.env.local').write_text('OPENROUTER_API_KEY=local-openrouter\nTYPESAFE_API_KEY=local-typesafe\n',encoding='utf-8')
 load_local_environment(tmp_path);assert os.environ['OPENROUTER_API_KEY']=='local-openrouter' and os.environ['TYPESAFE_API_KEY']=='local-typesafe'
 monkeypatch.setenv('OPENROUTER_API_KEY','railway-wins');load_local_environment(tmp_path);assert os.environ['OPENROUTER_API_KEY']=='railway-wins'
def test_two_agents_and_model_policy_config():
 a=create_agents('test','test');assert a.director is not a.researcher
 c=load_models_config(ROOT/'config/models.yaml');roles=(c.director,c.researcher,c.reasoner)
 assert all(x.model=='openrouter:deepseek/deepseek-v4.1-flash' for x in roles)
 assert all(x.fallbacks==('openrouter:openrouter/free',) for x in roles)
 assert c.researcher.max_output_tokens==16000 and c.jev.http2
def test_block_deadline_and_ledger():
 now=datetime(2026,9,30,tzinfo=UTC);clock=[now];m=BlockManager(now=lambda:clock[0]);b=m.create('o','why',ResourceAllocation(seconds=10,handoff_reserve_seconds=2));clock[0]=now+timedelta(seconds=9);assert m.status(b) is BlockStatus.HANDOFF
 with pytest.raises(HandoffRequired):m.require_work_window(b)
 assert m.complete(b,'soft_handoff').status is BlockStatus.COMPLETE
 with pytest.raises(ValidationError):b.deadline=now # type: ignore[misc]
 l=Ledger();e=LedgerEvent(event_type='x',occurred_at=now,payload={'v':1});l.append(e);e.payload['v']=2;assert l.history()[0].payload=={'v':1}
def test_non_science_outputs_cannot_be_evidence():
 for x in (ReasonerOutput(interpretation='x',hypotheses=(Hypothesis(hypothesis_id='h',statement='x',within_scope=True,proposed_test='x'),),uncertainty='x'),NoulDecision(question_id='q',p_true=.5,model_requested='x',model_resolved='x',question_version='1',projection_id='x'),JevBlockDossier(block_id='b',objective='o',termination_reason='x',evidence_refs=(),preferred_continuation='x',preferred_continuation_reason='x')):
  with pytest.raises(AttributeError):admit_scientific_evidence(x) # type: ignore[arg-type]
def test_parallel_jev_and_conservative_frontier():
 qs=(JevQuestionSpec(question_id='a',semantic_purpose='a',primitive='noul',projection_id='p',instructions='a',criteria={},question_version='1'),JevQuestionSpec(question_id='b',semantic_purpose='b',primitive='choice',projection_id='p',instructions='b',criteria={'ADVANCE':'a','DEFER':'d','NONE':'n'},question_version='1'));d=DeterministicJevClient().evaluate({},qs);assert len(d)==2;assert CandidateFrontierPolicy().decide('c',d,('p',)).action is FrontierAction.KEEP_ALIVE
 negative=ChoiceDecision(question_id='negative',selected_option='NONE',probabilities={'ADVANCE':.01,'DEFER':.29,'NONE':.70},confidence=.70,model_requested='x',model_resolved='x',question_version='1',projection_id='p')
 assert CandidateFrontierPolicy().decide('c',(negative,),('p',)).action is FrontierAction.REJECT_RETAIN
def test_failure_and_local_question_status():
 assert JevExecutionFailure(question_id='q',category=JevFailureCategory.TIMEOUT,detail='x').category is JevFailureCategory.TIMEOUT
 with pytest.raises(ValidationError):JevQuestionSpec(question_id='q',semantic_purpose='q',primitive='noul',projection_id='p',instructions='x',criteria={},question_version='1',status='reusable')
def test_synthetic_measurement_cannot_be_admitted_as_evidence():
 from src.science.models import MeasuredResult
 result=MeasuredResult(analysis_id='synthetic',values={'effect':1.0},provenance=('fixture',),origin='synthetic',input_sha256='0'*64)
 with pytest.raises(ValueError,match='source-bound'):admit_scientific_evidence(result)
def test_research_state_projection_is_deterministic_and_excludes_acquisition_records():
 state=ResearchState(block_id='b',objective='o').append('candidates',StateFragment(fragment_id='c',kind='candidate',summary='candidate',provenance=('test',))).append('acquisitions',StateFragment(fragment_id='a',kind='gdc',summary='one record',provenance=('test',)))
 first=project_state(state,ProjectionSpec(projection_name='candidate',candidate_id='c'));second=project_state(state,ProjectionSpec(projection_name='candidate',candidate_id='c'))
 assert first==second and 'acquisitions' not in first.payload and first.projection_id.startswith('candidate-v2-')
 from src.science.models import MeasuredResult
 from src.provenance import canonical_bytes
 provided=MeasuredResult(analysis_id='provided',values={'zero':0,'missing':None,'mean':1.25},origin='provided',provenance=('test',),input_sha256='0'*64)
 state=state.add_measurement(provided)
 for i in range(100):
  state=state.append('observations',StateFragment(fragment_id=str(i),kind='observation',summary='x'*1000,provenance=('test',)))
 bounded=project_state(state,ProjectionSpec(projection_name='candidate',candidate_id='c',max_items=4,max_payload_bytes=4096))
 assert len(canonical_bytes(bounded.payload))<=4096 and bounded.payload['omitted']['observations']>=96
 assert bounded.payload['measurements'][0]['values']=={'zero':0,'missing':None,'mean':1.25}
 assert bounded.payload['measurements'][0]['origin']=='provided'
def test_deterministic_science_methods_produce_measurements_before_admission():
 executor=ScienceExecutor()
 summary=executor.execute(AnalysisSpec(analysis_id='summary',question='q',population='p',estimand='mean',method='descriptive_summary',variables=('values',),inputs={'values':[1.0,2.0,3.0]}))
 regression=executor.execute(AnalysisSpec(analysis_id='ols',question='q',population='p',estimand='slope',method='ordinary_least_squares',variables=('x','y'),inputs={'x':[1.0,2.0,3.0],'y':[2.0,4.0,6.0]}))
 assert summary.values['mean']==2.0 and regression.values['slope']==pytest.approx(2.0)
 assert summary.interpretation=='exploratory' and regression.interpretation=='exploratory'
 assert summary.provenance[0]=='pandas.Series' and regression.provenance[0]=='statsmodels.OLS'
def test_capability_index_is_bounded_and_distinguishes_metadata_from_execution(tmp_path):
 index=initial_oncolab_index();matches=index.search('GDC cancer',kinds=(OncoLabKind.SOURCE,),limit=3)
 assert matches[0].capability_id=='source.gdc' and matches[0].availability.value=='available'
 assert index.count()>=100
 assert index.verification_records('source.gdc')
 assert index.describe_with_verification('source.gdc')['verification']
 assert index.describe('jev.choice').validation_state.value=='unvalidated'
 assert OncoLabKind.JEV in index.list_kinds()
 with pytest.raises(ValueError):index.search(limit=21)
 sample=index.verification_records('source.gdc')[0]
 before=len(index.verification_records('source.gdc'))
 index.load_verification_records();index.load_verification_records()
 assert len(index.verification_records('source.gdc'))==before
 with pytest.raises(ValueError,match='unknown verification capability'):
  index.record_verification(sample.model_copy(update={'capability_id':'science.scipy.pearsonr'}))
 import yaml
 invalid=sample.model_copy(update={'execution_reference':sample.execution_reference.model_copy(update={'value':'src/oncolab/proven/artifacts/missing.json'})})
 (tmp_path/'invalid.yaml').write_text(yaml.safe_dump({'records':[invalid.model_dump(mode='json')]}),encoding='utf-8')
 with pytest.raises(ValueError,match='unresolved verification artifact'):
  index.load_verification_records(tmp_path)
 invalid=sample.model_copy(update={'execution_reference':sample.execution_reference.model_copy(update={'sha256':'0'*64})})
 (tmp_path/'invalid.yaml').write_text(yaml.safe_dump({'records':[invalid.model_dump(mode='json')]}),encoding='utf-8')
 with pytest.raises(ValueError,match='integrity mismatch'):
  index.load_verification_records(tmp_path)
def test_github_sandbox_is_commit_pinned_credential_free_and_replay_validated():
 seen=[]
 def runner(arguments,**kwargs):
  seen.append((arguments,kwargs))
  if arguments[:2]==('git','ls-remote'):return subprocess.CompletedProcess(arguments,0,'a'*40+'\tHEAD\n','')
  if arguments[:3]==('docker','image','inspect'):return subprocess.CompletedProcess(arguments,0,'sha256:'+'b'*64+'\n','')
  if arguments[:2]==('docker','run'):
   command=arguments[arguments.index('sha256:'+'b'*64)+1:]
   output='{"values":{"effect":1.25}}\n' if command==('python','method.py','/input/request.json') else 'ok\n'
   return subprocess.CompletedProcess(arguments,0,output,'')
  return subprocess.CompletedProcess(arguments,0,'','')
 sandbox=DockerScientificSandbox(runner=runner)
 request=GithubMethodRequest(repository_url='https://github.com/example/public-method',requested_ref='main',test_command=('python','-m','pytest'),execute_command=('python','method.py','/input/request.json'),input_json={'x':[1,2,3]})
 candidate=sandbox.acquire_and_execute(request);measurement=validate_sandbox_candidate(candidate,'sandbox-analysis')
 assert candidate.receipt.commit_sha=='a'*40 and measurement.values=={'effect':1.25}
 assert candidate.receipt.first_run.stdout_sha256==candidate.receipt.replay_run.stdout_sha256
 assert all('OPENROUTER_API_KEY' not in kwargs['env'] and 'TYPESAFE_API_KEY' not in kwargs['env'] for _,kwargs in seen)
 docker_calls=[arguments for arguments,_ in seen if arguments[:2]==('docker','run')]
 assert docker_calls[0][docker_calls[0].index('--network')+1]=='none'
 assert docker_calls[1][docker_calls[1].index('--network')+1]=='bridge'
 assert all('/input/request.json:ro' not in call for call in docker_calls[:2])
 assert all(call[call.index('--network')+1]=='none' for call in docker_calls[2:])
 replayed=sandbox.replay(candidate)
 assert replayed.receipt.commit_sha==candidate.receipt.commit_sha and replayed.values==candidate.values
 assert replayed.receipt.environment['image']=='sha256:'+'b'*64
 from src.provenance import content_hash
 corrupt=candidate.model_copy(update={'values':{'effect':99.0}})
 with pytest.raises(SandboxError,match='values'):validate_sandbox_candidate(corrupt,'bad')
 with pytest.raises(ValidationError):GithubMethodRequest(repository_url='git@github.com:example/public-method.git',test_command=('python','-m','pytest'),execute_command=('python','method.py'),input_json={})
def test_researcher_instances_and_skill_selections_are_fresh_per_block():
 agents=create_agents('test','test');assert agents.fresh_researcher() is not agents.researcher
 skills=BlockSkillStore();skills.start('first');assert skills.select('first','statistics')
 skills.start('second');assert skills.selected('second')==()
 first_index=initial_oncolab_index();second_index=initial_oncolab_index();assert first_index is not second_index

def test_resource_budgets_are_isolated_per_block():
 manager=BlockManager();first=manager.create('first','test',ResourceAllocation(seconds=60));second=manager.create('second','test',ResourceAllocation(seconds=60))
 runtime=HarnessRuntime(manager=manager,jev=DeterministicJevClient(),science=ScienceExecutor(),reasoner=DeterministicReasoner(),max_jev_calls=1,max_reasoner_calls=1)
 runtime.claim(first.block_id,'source',1)
 with pytest.raises(RuntimeError,match='budget exhausted'):runtime.claim(first.block_id,'source',1)
 runtime.claim(second.block_id,'source',1)
def test_researcher_can_use_sandbox_tool_without_promoting_method(tmp_path):
 from src.persistence.store import SqliteResearchStore
 from src.persistence.repository import ResearchRepository
 from src.persistence.reconstruct import reconstruct_block
 from src.persistence.records import RecordKind
 database=tmp_path/'sandbox.sqlite3'
 store=SqliteResearchStore(database);repository=ResearchRepository(store)
 class FakeSandbox:
  def acquire_and_execute(self,request):
   assert repository.store.records(kind=RecordKind.SANDBOX_REQUEST)[0].payload['input_json']==request.input_json
   from src.provenance import content_hash
   from src.science.sandbox import SandboxPolicy
   import hashlib
   output='{"values":{"effect":1.0}}'
   invocation=SandboxInvocation(command=request.execute_command,exit_status=0,stdout_sha256=hashlib.sha256(output.encode()).hexdigest(),stderr_sha256=hashlib.sha256(b'').hexdigest())
   environment={'image':'sha256:'+'b'*64}
   receipt=SandboxReceipt(repository_url=request.repository_url,commit_sha='a'*40,environment=environment,environment_sha256=content_hash(environment),input_sha256=content_hash(request.input_json),install=invocation.model_copy(update={'command':request.install_command}),test=invocation.model_copy(update={'command':request.test_command}),first_run=invocation,replay_run=invocation)
   return SandboxMeasurementCandidate(candidate_id='candidate',receipt=receipt,values={'effect':1.0},request=request,policy=SandboxPolicy(),output_json=output)
 manager=BlockManager();block=manager.create('sandbox objective','test',ResourceAllocation(seconds=60));runtime=HarnessRuntime(manager=manager,jev=DeterministicJevClient(),science=ScienceExecutor(),reasoner=DeterministicReasoner(),max_jev_calls=2,max_reasoner_calls=1,sandbox=FakeSandbox())
 runtime.repository=repository;repository.record_block(block)
 runtime.research_state.start(block.block_id,block.objective);runtime.skills.start(block.block_id)
 agents=create_agents('test','test');calls=0
 async def model(messages,info):
  nonlocal calls
  calls+=1
  if calls==1:
   return ModelResponse(parts=[ToolCallPart('run_code',{'code':'await load_research_skills(need="github reproducibility")\ncandidate = await acquire_github_scientific_method(capability_need="statistics novel method", why_existing_capabilities_are_inadequate="installed array statistics do not estimate the requested quantity", repository_url="https://github.com/example/public-method", requested_ref="main", install_command=["python", "-m", "pip", "install", "."], test_command=["python", "-m", "pytest"], execute_command=["python", "method.py", "/input/request.json"], input_json={"x": [1]})\nawait validate_sandbox_measurement(candidate_id=candidate["candidate_id"], analysis_id="sandbox-analysis")\nawait admit_measurement(analysis_id="sandbox-analysis")\ncandidate'},tool_call_id='sandbox-code')])
  return ModelResponse(parts=[TextPart('sandbox complete')])
 researcher=agents.fresh_researcher()
 with researcher.override(model=scripted(model)):
  result=researcher.run_sync('use the sandbox',deps=ResearcherDeps(runtime=runtime,block_id=block.block_id))
 assert result.output=='sandbox complete'
 events={event.event_type for event in manager.ledger(block.block_id).history()}
 assert {'ResearchSkillsLoaded','GithubAcquisitionCompleted','SandboxMeasurementValidated','EvidenceAdmission'}<=events
 assert runtime.oncolab.describe('software.github-scientific').validation_state.value=='unvalidated'
 store.close();store=SqliteResearchStore(database)
 view=reconstruct_block(store,block.block_id)
 assert view.sandbox_requests[0]['input_json']=={'x':[1]}
 candidate=view.sandbox_candidates[0]
 assert candidate['request']['execute_command']==['python','method.py','/input/request.json']
 assert candidate['receipt']['commit_sha']=='a'*40 and candidate['receipt']['environment']['image']=='sha256:'+'b'*64
 assert candidate['output_json']=='{"values":{"effect":1.0}}' and candidate['validator_version']=='sandbox-validator-v2'
 assert view.resolved_inputs[view.measurements[0]['source_refs'][0]]['candidate_id']==candidate['candidate_id']
 assert view.verifications[0]['capability_id']=='software.github-scientific'
 store.close()
def test_harness_code_mode_runs_contract_tools_and_director_delegates():
 seen=[]
 def response(request):
  seen.append(request)
  if request.url.host=='api.gdc.cancer.gov':return httpx.Response(200,json={'data':{'hits':[{'file_id':'public-file'}]}})
  if request.url.host=='ucscpublic.xenahubs.net':return httpx.Response(200,json=[{'name':'TCGA cohort'}])
  return httpx.Response(200,json={'message':{'items':[{'title':['Public study'],'DOI':'10.1/example','URL':'https://doi.org/10.1/example'}]}})
 manager=BlockManager();transport=httpx.MockTransport(response);runtime=HarnessRuntime(manager=manager,jev=DeterministicJevClient(),science=ScienceExecutor(),reasoner=DeterministicReasoner(),max_jev_calls=2,max_reasoner_calls=1,gdc=GdcPublicSource(transport),xena=XenaPublicSource(transport),literature=PublicLiteratureSource(transport))
 agents=create_agents('test','test',max_tool_calls=20);runtime.researcher=agents.researcher
 director_calls=0;researcher_calls=0
 async def director_model(messages,info):
  nonlocal director_calls
  director_calls+=1
  tools={tool.name for tool in info.function_tools}
  if os.name=='posix' and director_calls==1:
   assert {'list_files','shell','run_code'}<=tools
   return ModelResponse(parts=[ToolCallPart('list_files',{'path':'.'},tool_call_id='director-coder')])
  if director_calls==1+(os.name=='posix'):
   assert 'run_code' in tools
   return ModelResponse(parts=[ToolCallPart('run_code',{'code':'await search_oncolab(query="GDC", kinds=["source"], limit=3)\nawait describe_oncolab(capability_id="source.gdc")\nblock = await allocate_block(objective="synthetic", why_now="test", seconds=60)\nawait launch_researcher(block_id=block["block_id"])\nblock'},tool_call_id='director-code')])
  return ModelResponse(parts=[TextPart('director complete')])
 async def researcher_model(messages,info):
  nonlocal researcher_calls
  researcher_calls+=1
  tools={tool.name for tool in info.function_tools}
  if os.name=='posix' and researcher_calls==1:
   assert {'list_files','shell','run_code'}<=tools
   return ModelResponse(parts=[ToolCallPart('list_files',{'path':'.'},tool_call_id='researcher-coder')])
  if researcher_calls==1+(os.name=='posix'):
   assert 'run_code' in tools
   return ModelResponse(parts=[ToolCallPart('run_code',{'code':'await search_oncolab(query="regression", kinds=["statistical_method"], limit=3)\nawait describe_oncolab(capability_id="stat.statsmodels")\ngdc = await acquire_gdc(endpoint="files", filters={"op":"in", "content":{"field":"files.data_type", "value":["Gene Expression Quantification"]}}, fields=["file_id"], size=1)\nawait search_xena(query="TCGA", limit=1)\nawait search_public_literature(query="oncology", limit=1)\nawait measure_acquisition(acquisition_id=gdc["acquisition_id"], analysis_id="analysis")\nawait admit_measurement(analysis_id="analysis")\nawait create_line_figure(title="synthetic", x=[1.0, 2.0, 3.0], y=[1.0, 4.0, 9.0])\nawait block_status()\nawait evaluate_candidate(candidate_id="candidate", candidate_summary="synthetic subgroup")\nhypotheses = await generate_hypotheses(finding="effect found")\nawait request_scope_escalation(proposed_test="mechanistic experiment", rationale="beyond scope")\nawait complete_block(reason="researcher complete")\nhypotheses'},tool_call_id='researcher-code')])
  return ModelResponse(parts=[TextPart('researcher complete')])
 with agents.director.override(model=scripted(director_model)),agents.researcher.override(model=scripted(researcher_model)):
  import asyncio
  async def run_owned():
   result = await agents.director.run('allocate and investigate', deps=DirectorDeps(runtime))
   await runtime.active_research.task
   return result
  result=asyncio.run(run_owned())
 assert result.output=='director complete'
 block=manager.blocks()[0];assert manager.status(block) is BlockStatus.COMPLETE
 event_types={event.event_type for event in manager.ledger(block.block_id).history()}
 assert {'DirectorBlockAllocated','CapabilityInvocation','CapabilityResult','ScienceMeasurement','EvidenceAdmission','JevExecution','FrontierDecision','ReasonerOutput','ScopeEscalationRequested','ResearcherCompletion'}<=event_types
 gdc_request=next(request for request in seen if request.url.host=='api.gdc.cancer.gov');assert 'x-auth-token' not in gdc_request.headers and b'"files.access"' not in gdc_request.content
 xena_request=next(request for request in seen if request.url.host=='ucscpublic.xenahubs.net');assert xena_request.method=='POST' and xena_request.url.path=='/data/' and xena_request.headers['content-type']=='text/plain'


def test_semantic_method_tools_keep_routes_uncertainty_and_replayable_lineage(tmp_path):
    from src.persistence.store import SqliteResearchStore
    from src.persistence.repository import ResearchRepository
    from src.persistence.reconstruct import reconstruct_block
    from src.sources.models import AcquisitionRecord
    store=SqliteResearchStore(tmp_path/'semantic.sqlite3');repo=ResearchRepository(store)
    manager=BlockManager();block=manager.create('paired association','test',ResourceAllocation(seconds=300))
    runtime=HarnessRuntime(manager=manager,jev=DeterministicJevClient(),science=ScienceExecutor(),reasoner=DeterministicReasoner(),max_jev_calls=10,max_reasoner_calls=1,repository=repo)
    repo.record_block(block);runtime.research_state.start(block.block_id,block.objective)
    record=AcquisitionRecord(source='fixture',request={},records=({'id':'a','x':1,'y':2},{'id':'b','x':2,'y':4}),provenance=('fixture',))
    runtime.retain_acquisition(block.block_id,record)
    split_x=AcquisitionRecord(source='fixture',request={'side':'x'},records=({'id':'a','x':1},{'id':'b','x':2}),provenance=('fixture',))
    split_y=AcquisitionRecord(source='fixture',request={'side':'y'},records=({'id':'a','y':2},{'id':'b','y':4}),provenance=('fixture',))
    runtime.retain_acquisition(block.block_id,split_x);runtime.retain_acquisition(block.block_id,split_y)
    text_input=AcquisitionRecord(source='fixture',request={'values':'text'},records=({'id':'a','x':'1','y':2},{'id':'b','x':'2','y':4}),provenance=('fixture',))
    runtime.retain_acquisition(block.block_id,text_input)
    responses=[]
    async def model(messages,info):
        if not any(isinstance(m,ModelResponse) for m in messages):
            code=f'page = await search_oncolab_page(query="paired association", limit=2)\ncontract = await describe_oncolab(capability_id="stat.scipy")\nfit = await assess_method(capability_id="stat.scipy", need={{"estimand":"correlation","design":"paired"}}, acquisition_ids=["{record.acquisition_id}"], operation="pearson_correlation")\nmissing = await assess_method(capability_id="stat.scipy", need={{"estimand":"correlation"}}, acquisition_ids=[])\nmeta = await assess_method(capability_id="stat.method.correlation", need={{"estimand":"correlation"}})\nawait assess_representation(acquisition_id="{record.acquisition_id}", need={{"estimand":"paired correlation"}})\nfirst = await assess_hypothesis(hypothesis="X relates to Y", proposed_test="paired correlation")\nduplicate = await assess_hypothesis(hypothesis=" X  relates to Y ", proposed_test="paired correlation")\nassert duplicate["exact_duplicate"]\nassert not missing["checks"]["eligible"]\nassert not meta["checks"]["eligible"]\nassert fit["checks"]["eligible"]\nfit'
            code=(f'need = {{"question":"Do X and Y correlate?", "estimand":"correlation", "population":"retained rows", "design":"paired", '
                  '"representation_need":{"estimand":"correlation","representation":"paired_data","entity_key":"id","fields":{"x":"x","y":"y"},"numeric_roles":["x","y"],"minimum_complete_rows":2}}\n'
                  f'generated = await generate_method_candidates(need=need, acquisition_ids=["{record.acquisition_id}"], limit=8)\n'
                  'source = [c for c in generated["candidates"] if c["capability_id"] == "science.source-paired"][0]\n'
                  'assert source["input_ready"]\nassert source["scientific_suitability"] == "unmeasured"\n'
                  f'planned_fit = await assess_method(capability_id="science.source-paired", need=need, acquisition_ids=["{record.acquisition_id}"], operation="pearson_correlation")\n'
                  'assert planned_fit["checks"]["eligible"]\n'
                  'assert any(c["status"] == "prerequisites_unmet" for c in generated["candidates"])\n'
                  f'split = await generate_method_candidates(need=need, acquisition_ids=["{split_x.acquisition_id}","{split_y.acquisition_id}"], limit=8)\n'
                  'assert not any(c["input_ready"] for c in split["candidates"])\n'
                  f'no_join = await assess_method(capability_id="science.source-paired", need=need, acquisition_ids=["{split_x.acquisition_id}","{split_y.acquisition_id}"], operation="pearson_correlation")\n'
                  'assert not no_join["checks"]["eligible"]\nassert no_join["frontier"]["action"] == "defer"\n'
                  'need["representation_need"]["numeric_roles"] = []\n'
                  f'text = await generate_method_candidates(need=need, acquisition_ids=["{text_input.acquisition_id}"], limit=8)\n'
                  'assert not [c for c in text["candidates"] if c["capability_id"] == "science.source-paired"][0]["input_ready"]\n'
                  'need["representation_need"]["fields"]["covariate"] = "absent_covariate"\n'
                  f'blocked = await generate_method_candidates(need=need, acquisition_ids=["{record.acquisition_id}"], limit=8)\n'
                  'assert not any(c["input_ready"] for c in blocked["candidates"])\n'+code)
            return ModelResponse(parts=[ToolCallPart('run_code',{'code':code},tool_call_id='selection')])
        responses.extend(str(p.content) for m in messages for p in m.parts if hasattr(p,'content'))
        return ModelResponse(parts=[TextPart('done')])
    agent=create_agents('test','test').researcher
    with agent.override(model=scripted(model)):agent.run_sync('select method',deps=ResearcherDeps(runtime,block.block_id))
    assert not any('AssertionError' in s or 'Exception:' in s or 'Type error' in s or 'Runtime error' in s for s in responses),responses[-1]
    assert runtime.resources(block.block_id)['jev']['attempted']==7
    assert runtime.resources(block.block_id)['jev_questions']['attempted']==24
    store.close();store=SqliteResearchStore(tmp_path/'semantic.sqlite3');view=reconstruct_block(store,block.block_id)
    assert len(view.jev_calls)==7 and not view.evidence
    assert all(c['projection_sha256'] and c['question_hashes'] for c in view.jev_calls)
    assert len([r for r in view.index_receipts if r['operation']=='method_generation'])==4
    assert len(view.method_candidates)==4
    from src.application.export import render_snapshot
    exported=b''.join(data for name,data in render_snapshot(store).items() if name.endswith('/records.json'))
    assert b'method_candidates' in exported and b'absent_covariate' in exported
    assert any(h['action']=='defer' for h in view.candidate_history)
    assert any(h['action']=='keep_alive' for h in view.candidate_history)
    assert all(len(p['returned_ids'])<=2 for p in view.index_receipts if p['operation']=='search_page')
    store.close()


def test_representation_input_gates_precede_semantic_sufficiency_and_preserve_alternatives(tmp_path):
    """Actual Researcher tool/policy: optimistic semantic answers cannot grant missing inputs."""
    import json
    from src.persistence.store import SqliteResearchStore
    from src.persistence.repository import ResearchRepository
    from src.persistence.records import RecordKind
    from src.sources.models import AcquisitionRecord, CoverageContract
    store = SqliteResearchStore(tmp_path / 'representation.sqlite3')
    manager = BlockManager(); block = manager.create('representation alternatives', 'test', ResourceAllocation(seconds=300))
    runtime = HarnessRuntime(manager=manager, jev=DeterministicJevClient(), science=ScienceExecutor(),
        reasoner=DeterministicReasoner(), repository=ResearchRepository(store), max_jev_calls=20, max_jev_questions=100, max_reasoner_calls=1)
    runtime.repository.record_block(block)
    paired = AcquisitionRecord(source='public-table', request={}, provenance=('retained-fixture',), records=(
        {'person':'a', 'signal':{'z':1}, 'outcome':2, 'units':{'signal':{'z':'counts'}}},
        {'person':'b', 'signal':{'z':2}, 'outcome':4, 'units':{'signal':{'z':'counts'}}},
        {'person':'c', 'signal':{'z':3}, 'outcome':5, 'units':{'signal':{'z':'counts'}}}))
    files = AcquisitionRecord(source='gdc', request={}, provenance=('retained-fixture',),
        records=({'id':'controlled', 'access':'controlled', 'data_type':'Gene Expression Quantification'},),
        coverage=CoverageContract(endpoint='files', returned_rows=1))
    base = {'estimand':'paired association', 'representation':'paired_data', 'entity_key':'person',
            'fields':{'x':'signal.z','y':'outcome'}, 'numeric_roles':['x','y'], 'minimum_complete_rows':3}
    cases = [
        (paired, {**base, 'units':{'x':'TPM'}}, False, 'unmeasured'),
        (paired, base, True, 'directly_available'),
        (paired, {**base, 'fields':{'x':'missing','y':'outcome'}}, False, 'absent_from_inspected_source'),
        (paired, {**base, 'require_complete_coverage':True}, False, 'unmeasured'),
        (paired, {**base, 'identities':{'genome_build':'GRCh38'}}, False, 'unmeasured'),
        (paired.model_copy(update={'acquisition_id':'duplicate-row-fixture','records':(paired.records[0],paired.records[0],paired.records[2])}), base, False, 'unmeasured'),
        (files, {'estimand':'gene expression contrast','representation':'expression_matrix'}, False, 'controlled_inaccessible'),
        (files, {'estimand':'file metadata','representation':'metadata','fields':{'id':'id'}}, True, 'directly_available'),
    ]
    for record, _, _, _ in cases:
        runtime.retain_acquisition(block.block_id, record)
    code = []
    for number, (record, need, eligible, availability) in enumerate(cases):
        code.append(f'r{number} = await assess_representation(acquisition_id="{record.acquisition_id}", need={need!r})')
        code.append(f'assert r{number}["eligible"] == {eligible!r}, "schema incompatibility cannot be overridden by semantics"')
        code.append(f'assert r{number}["checks"]["eligible"] == {eligible!r}')
        code.append(f'assert r{number}["checks"]["availability"] == "{availability}"')
        if not eligible:
            code.append(f'assert r{number}["frontier"]["action"] == "defer"')
    results = []
    async def model(messages, info):
        if not any(isinstance(m, ModelResponse) for m in messages):
            return ModelResponse(parts=[ToolCallPart('run_code', {'code':'\n'.join(code)}, tool_call_id='representations')])
        results.extend(str(p.content) for m in messages for p in m.parts if hasattr(p,'content'))
        return ModelResponse(parts=[TextPart('reviewed')])
    agent = create_agents('test','test').researcher
    with agent.override(model=scripted(model)):
        agent.run_sync('assess actual retained alternatives', deps=ResearcherDeps(runtime, block.block_id))
    assert not any('AssertionError' in value or 'Runtime error' in value or 'Exception:' in value or 'Type error' in value for value in results), results
    calls = store.records(kind=RecordKind.JEV_CALL)
    completed = [r for r in calls if r.payload['outcome']=='completed']
    assert len(completed) == len(cases)
    assert all(r.payload['projection']['payload']['checks']['unmet_requirements'] for r in completed
               if not r.payload['projection']['payload']['checks']['eligible'])
    assert not store.records(kind=RecordKind.EVIDENCE)
    store.close()


def test_oncolab_continuation_recovers_zero_overlap_candidates_and_rejects_stale_cursor():
    from src.oncolab.registry import OncoLabIndex
    original=initial_oncolab_index()
    page=original.search_page('unseen-synonym',limit=1)
    ids=[]
    while True:
        ids.extend(c.capability_id for c in page.cards)
        if page.exhausted:break
        page=original.search_page('unseen-synonym',limit=20,continuation=page.continuation)
    assert len(set(ids))==original.count()
    assert 'stat.scipy' in ids
    cursor=original.search_page('unseen-synonym',limit=1).continuation
    with pytest.raises(ValueError):original.search_page('different-query',continuation=cursor)
    changed=original.describe('stat.scipy').model_copy(update={'purpose':'changed scientific contract'})
    index=OncoLabIndex((changed,))
    with pytest.raises(ValueError):index.search_page('unseen-synonym',continuation=cursor)


def test_source_summary_reports_undefined_sd_and_missingness_denominators():
 from src.sources.models import AcquisitionRecord
 executor=ScienceExecutor()
 record=AcquisitionRecord(source="fixture",request={},records=({"v":4},{"v":None},{"v":"invalid"},{}),provenance=("controlled-source",))
 result=executor.measure_acquisition(record,"summary-single","v")
 assert result.values["standard_deviation"] is None
 assert result.values["mean"]==4 and result.values["n"]==1
 assert {k:result.values[k] for k in ("total_rows","valid_numeric","absent","null","invalid_type","nonfinite")}=={
  "total_rows":4,"valid_numeric":1,"absent":1,"null":1,"invalid_type":1,"nonfinite":0}
 assert "n>=2" in result.diagnostics["undefined"]["standard_deviation"]
 empty=executor.measure_acquisition(record.model_copy(update={"records":({"v":None},)}),"empty","v")
 assert empty.values["mean"] is None and empty.values["n"]==0
 two=executor.measure_acquisition(record.model_copy(update={"records":({"v":2},{"v":4})}),"two","v")
 assert two.values["standard_deviation"]==pytest.approx(2**.5)
 # Nonfinite structured acquisitions cannot acquire a canonical identity.
 with pytest.raises(ValueError):executor.measure_acquisition(record.model_copy(update={"records":({"v":float("nan")},)}),"nonfinite","v")


def test_repeat_admission_is_identity_stable():
 from src.sources.models import AcquisitionRecord
 record=AcquisitionRecord(source="fixture",request={},records=({"id":"a"},),provenance=("controlled-source",))
 result=ScienceExecutor().measure_acquisition(record,"repeat")
 assert admit_scientific_evidence(result).evidence_id==admit_scientific_evidence(result).evidence_id


def test_ordered_source_pages_preserve_totals_and_reject_overlap():
 import asyncio
 from src.sources.coverage import combine_pages
 def transport(request):
  payload=__import__("json").loads(request.content)
  offset=payload["from"]
  return httpx.Response(200,json={"data":{"hits":[{"id":str(offset+1),"age":10+offset}],"pagination":{"total":2}}})
 source=GdcPublicSource(httpx.MockTransport(transport))
 first=asyncio.run(source.search("cases",{},("id","age"),size=1))
 second=asyncio.run(source.search("cases",{},("id","age"),size=1,offset=1))
 assert not first.coverage.complete and first.coverage.reported_total==2
 merged=combine_pages((first,second))
 assert merged.coverage.complete and merged.coverage.unique_entities==2 and merged.coverage.returned_rows==2
 with pytest.raises(ValueError,match="repeated"):combine_pages((first,first))
 with pytest.raises(ValueError,match="overlapping"):combine_pages((first,second.model_copy(update={"records":first.records})))
 with pytest.raises(ValueError,match="total changed"):combine_pages((first,second.model_copy(update={"coverage":second.coverage.model_copy(update={"reported_total":3})})))
 unknown=first.model_copy(update={"coverage":first.coverage.model_copy(update={"reported_total":None})})
 assert not combine_pages((unknown,)).coverage.complete


@pytest.mark.parametrize("populated", [False, True])
def test_literature_search_retains_bounded_excerpts_without_claiming_complete_coverage(populated):
 import asyncio
 items = [{"title": [str(i)], "DOI": f"10.1/{i}", "abstract": "癌" * 4000} for i in range(6)] if populated else []
 source = PublicLiteratureSource(httpx.MockTransport(lambda request: httpx.Response(200,
  json={"message": {"items": items, "total-results": 6 if populated else 0}})))
 async def run():
  try:
   result = await source.search("bounded oncology query", limit=6)
   assert result.retrieved_at is not None
   assert result.coverage.returned_rows == len(items)
   assert result.coverage.reported_total == len(items)
   assert not result.coverage.complete  # Even all returned hits do not cover world literature.
   retained = [record.abstract for record in result.records if record.abstract is not None]
   assert sum(len(text.encode("utf-8")) for text in retained) <= 8192
   assert all(len(text.encode("utf-8")) <= 2048 and "�" not in text for text in retained)
   if populated:
    assert retained and all(record.abstract_truncated for record in result.records)
    assert result.records[-1].abstract is None
   else:
    assert result.records == ()
  finally:
   await source.aclose()
 asyncio.run(run())


@pytest.mark.parametrize("source_kind", ["gdc", "xena", "literature"])
def test_public_sources_stop_unknown_length_stream_at_the_byte_ceiling(source_kind):
 import asyncio
 from src.runtime.resources import ResourceRejected
 reached_tail=[]
 class Oversized(httpx.AsyncByteStream):
  async def __aiter__(self):
   yield b"123"
   yield b"456"
   reached_tail.append(True)
   yield b"unbounded tail"
 transport=httpx.MockTransport(lambda request:httpx.Response(200,stream=Oversized()))
 source={"gdc":GdcPublicSource,"xena":XenaPublicSource,"literature":PublicLiteratureSource}[source_kind](transport,max_download_bytes=4)
 async def run():
  try:
   with pytest.raises(ResourceRejected) as rejected:
    if source_kind=="gdc":await source.search("cases",{},("id",))
    elif source_kind=="xena":await source.search_datasets("TCGA")
    else:await source.search("oncology")
   assert rejected.value.directive["scientific_negative"] is False
   assert rejected.value.directive["consumed_bytes"]==5
   assert not reached_tail
  finally:await source.aclose()
 asyncio.run(run())


def test_download_service_consumption_survives_fresh_runtime_allocations():
 import asyncio
 from src.config.loader import load_models_config
 from src.config.models import RuntimeConfig,RuntimeMode
 from src.runtime.pydantic_ai.factory import build_harness_runtime
 from src.runtime.resources import ResourceRejected,ServiceResources
 resources=ServiceResources(max_service_download_bytes=48)
 payload=b'{"message":{"items":[]}}'
 assert len(payload)==24
 async def run():
  for index in range(3):
   runtime=build_harness_runtime(load_models_config(ROOT/"config"/"models.yaml"),RuntimeConfig(mode=RuntimeMode.DETERMINISTIC),resources=resources)
   # Replace only network transport; preserve the production governor meter.
   original=runtime.literature
   runtime.literature=PublicLiteratureSource(httpx.MockTransport(lambda request:httpx.Response(200,content=payload)))
   runtime.literature.meter=original.meter
   block=runtime.manager.allocate(f"block {index}","test")
   from src.runtime.pydantic_ai.contracts import ActiveResearchContext
   runtime.active_research=ActiveResearchContext(f"run-{index}",block.block_id,"mission","cycle",0)
   try:
    if index<2:await runtime.literature.search("oncology")
    else:
     with pytest.raises(ResourceRejected,match="service or block"):
      await runtime.literature.search("oncology")
    assert resources.downloaded_bytes==24*(index+1)
    assert resources.block_downloaded_bytes[block.block_id]==24
   finally:
    await asyncio.gather(original.aclose(),runtime.literature.aclose(),runtime.gdc.aclose(),runtime.xena.aclose())
 asyncio.run(run())


@pytest.mark.parametrize("access", ["open", "controlled", None])
def test_gdc_file_discovery_retains_access_without_silent_open_filter(access):
    import asyncio
    import json
    requests = []
    def transport(request):
        body = json.loads(request.content)
        requests.append(body)
        return httpx.Response(200, json={"data": {"hits": [{"id": "asset", "access": access,
            "data_type": "Gene Expression Quantification", "data_format": "TSV"}], "pagination": {"total": 1}}})
    async def run():
        source = GdcPublicSource(httpx.MockTransport(transport))
        try:
            record = await source.search("files", {}, ("id", "access", "data_type", "data_format"), size=1)
            assert record.records[0]["access"] == access
            assert requests[0].get("filters", {}) == {}, "empty discovery filters must not add hidden constraints"
            cards = source.asset_cards(record)
            assert cards[0].access == (access or "unknown")
            assert cards[0].file_size is None and cards[0].entity_unit == "file"
            assert cards[0].acquisition_id == record.acquisition_id
            assert cards[0].request_sha256 and cards[0].limitations
        finally:
            await source.aclose()
    asyncio.run(run())


@pytest.mark.parametrize("limits", [
    {"max_block_download_bytes": 10}, {"max_workspace_bytes": 7},
    {"max_durable_artifact_bytes": 7}, {"minimum_free_disk_bytes": 2**60},
])
def test_gdc_file_preflight_rejects_cumulative_capacity_before_data_request(tmp_path, limits):
    import asyncio
    from src.runtime.resources import ServiceResources, ResourceRejected
    requests = []
    file_id = "00000000-0000-4000-8000-000000000001"
    def transport(request):
        requests.append(request.url.path)
        if request.url.path.startswith("/files/"):
            return httpx.Response(200, json={"data": {"access": "open", "file_size": 8}})
        class FileBytes(httpx.AsyncByteStream):
            async def __aiter__(self):
                yield b"12345678"
        return httpx.Response(200, stream=FileBytes())
    async def run():
        source = GdcPublicSource(httpx.MockTransport(transport))
        resources = ServiceResources(**limits)
        resources.charge_download("block", 4)
        source.reserve = lambda owner, size: resources.reserve_download(owner, size, paths=(tmp_path,))
        try:
            with pytest.raises(ResourceRejected, match="capacity") as rejected:
                await source.acquire_file(file_id, "block", "text")
            assert rejected.value.directive["scientific_negative"] is False
            assert requests == [f"/files/{file_id}"]
            assert resources.downloaded_bytes == 4
        finally:
            await source.aclose()
    asyncio.run(run())



def test_gdc_http_200_embedded_error_is_failure_not_empty_source_result():
    import asyncio
    source = GdcPublicSource(httpx.MockTransport(lambda request: httpx.Response(200,
        json={"data": {"hits": []}, "error": {"status": 400, "error": {"reason": "invalid sort mapping"}}})))
    async def run():
        try:
            with pytest.raises(RuntimeError, match="GDC query failed"):
                await source.search("files", {}, ("file_id",), size=1)
        finally:
            await source.aclose()
    asyncio.run(run())



def test_unknown_gdc_file_stream_records_failed_bytes_and_releases_reservation():
    import asyncio
    from src.runtime.resources import ServiceResources, ResourceRejected
    reached_tail = []
    receipts = []
    file_id = "00000000-0000-4000-8000-000000000001"
    class Bytes(httpx.AsyncByteStream):
        async def __aiter__(self):
            yield b"123"
            yield b"456"
            reached_tail.append(True)
            yield b"unbounded tail"
    def transport(request):
        if request.url.path.startswith('/files/'):
            return httpx.Response(200, json={"data": {"access": "open"}})
        return httpx.Response(200, stream=Bytes())
    async def run():
        source = GdcPublicSource(httpx.MockTransport(transport), max_download_bytes=256)
        resources = ServiceResources(max_file_bytes=4)
        source.reserve = lambda owner, size: resources.reserve_download(owner, size)
        source.meter = lambda count: resources.charge_download('block', count)
        source.transfer_receipt = lambda owner, receipt: receipts.append(receipt)
        try:
            with pytest.raises(ResourceRejected, match='reserved capacity'):
                await source.acquire_file(file_id, 'block', 'text')
            assert receipts[0]['declared_size'] is None
            assert receipts[0]['transferred_bytes'] == 5 and receipts[0]['status'] == 'failed'
            assert resources.downloaded_bytes == receipts[0]['metadata_bytes'] + 5
            assert not resources.reservations and not reached_tail
        finally:
            await source.aclose()
    asyncio.run(run())


@pytest.mark.parametrize('source', ['github', 'bioconda', 'bioconductor'])
def test_targeted_enrichment_preserves_distinct_source_and_blocked_runtime_contracts(source):
    import asyncio
    from src.oncolab.discovery import ExternalDiscovery
    requests=[]
    sha='a'*40
    def transport(request):
        requests.append(request)
        if request.url.host=='api.github.com':
            if '/commits/' in request.url.path:return httpx.Response(200,json={'sha':sha})
            if '/git/trees/' in request.url.path:return httpx.Response(200,json={'tree':[{'path':'README.md','type':'blob'},{'path':'pyproject.toml','type':'blob'}]})
            return httpx.Response(200,json={'name':'method','full_name':'owner/method','private':False,'default_branch':'main','html_url':'https://github.com/owner/method','license':{'spdx_id':'MIT'}})
        if request.url.host=='api.anaconda.org':
            return httpx.Response(200,json={'name':'package','summary':'scientific package','latest_version':'1.0','license':'BSD-3-Clause',
                'files':[{'version':'1.0','md5':'b'*32,'attrs':{'subdir':'linux-64','depends':['r-base >=4'],'build':'r_0'}}]})
        return httpx.Response(200,text='<h1>Package</h1><p>Bioconductor version: 3.23 Package version: 1.0</p>'
            '<table><tr><td>License</td><td>LGPL</td></tr><tr><td>biocViews</td><td>RNASeq</td></tr></table>'
            '<a href="../vignettes/Package/inst/doc/guide.html">Reference</a>')
    client=ExternalDiscovery(httpx.MockTransport(transport))
    result=asyncio.run(client.describe(source,{'github':'owner/method','bioconda':'package','bioconductor':'Package'}[source]))
    card=result.cards[0]
    assert card.source==source and result.raw_json and result.response_sha256 and result.response_bytes>0
    assert 'metadata_only' in card.authority
    if source=='github':
        assert card.metadata['commit_sha']==sha and card.licence=='MIT'
        assert all(sha in link['url'] for link in card.links)
        assert len(requests)==3
    elif source=='bioconda':
        assert card.metadata['builds'][0]['dependencies']==['r-base >=4']
        assert card.metadata['runtime']=='Conda backend unsupported' and card.versions==('1.0',)
    else:
        assert card.metadata['runtime']=='R backend unsupported'
        assert card.licence=='LGPL' and card.metadata['release']=='3.23'
        assert card.links[0]['url'].startswith('https://bioconductor.org/')
