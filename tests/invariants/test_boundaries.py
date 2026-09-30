import os
import subprocess
from datetime import UTC,datetime,timedelta
from pathlib import Path
import pytest
import httpx
from pydantic import ValidationError
from pydantic_ai.messages import ModelResponse,TextPart,ToolCallPart
from pydantic_ai.models.function import DeltaToolCall,FunctionModel
from src.block.manager import BlockManager
from src.block.models import BlockStatus
from src.oncolab.catalogue import initial_oncolab_index
from src.oncolab.models import OncoLabKind
from src.config.loader import load_models_config
from src.director.models import ResourceAllocation
from src.dossier.models import Dossier
from src.jev.client import DeterministicJevClient
from src.jev.frontier import FrontierAction,FrontierPolicy
from src.jev.models import JevExecutionFailure,JevFailureCategory,JevQuestionSpec,NoulDecision
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
from src.science.execution import GeneratedAnalysisCode
from src.service import run_synthetic_vertical_slice
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
 now=datetime(2026,9,30,tzinfo=UTC);clock=[now];m=BlockManager(now=lambda:clock[0]);b=m.create('o','why',ResourceAllocation(seconds=10));clock[0]=now+timedelta(seconds=11);assert m.status(b) is BlockStatus.EXPIRED
 with pytest.raises(ValidationError):b.deadline=now # type: ignore[misc]
 l=Ledger();e=LedgerEvent(event_type='x',occurred_at=now,payload={'v':1});l.append(e);e.payload['v']=2;assert l.history()[0].payload=={'v':1}
def test_non_science_outputs_cannot_be_evidence():
 for x in (ReasonerOutput(interpretation='x',hypotheses=(Hypothesis(hypothesis_id='h',statement='x',within_scope=True,proposed_test='x'),),uncertainty='x'),GeneratedAnalysisCode(source='x'),NoulDecision(question_id='q',p_true=.5,model_requested='x',model_resolved='x',question_version='1',projection_id='x'),Dossier(block_id='b',objective='o',termination_reason='x',evidence_refs=(),preferred_continuation='x',preferred_continuation_reason='x')):
  with pytest.raises(AttributeError):admit_scientific_evidence(x) # type: ignore[arg-type]
def test_parallel_jev_and_conservative_frontier():
 qs=(JevQuestionSpec(question_id='a',semantic_purpose='a',primitive='noul',projection_id='p',instructions='a',criteria={},question_version='1'),JevQuestionSpec(question_id='b',semantic_purpose='b',primitive='choice',projection_id='p',instructions='b',criteria={'ADVANCE':'a','DEFER':'d','NONE':'n'},question_version='1'));d=DeterministicJevClient().evaluate({},qs);assert len(d)==2;assert FrontierPolicy().decide('c',d,('p',)).action is FrontierAction.KEEP_ALIVE
def test_failure_and_local_question_status():
 assert JevExecutionFailure(question_id='q',category=JevFailureCategory.TIMEOUT,detail='x').category is JevFailureCategory.TIMEOUT
 with pytest.raises(ValidationError):JevQuestionSpec(question_id='q',semantic_purpose='q',primitive='noul',projection_id='p',instructions='x',criteria={},question_version='1',status='reusable')
def test_vertical_slice():
 d=run_synthetic_vertical_slice(ROOT);assert d.evidence_refs and d.preferred_continuation=='replicate cohort' and d.recommended_next_blocks==('mechanistic experiment',)
def test_research_state_projection_is_deterministic_and_excludes_acquisition_records():
 state=ResearchState(block_id='b',objective='o').append('candidates',StateFragment(fragment_id='c',kind='candidate',summary='candidate',provenance=('test',))).append('acquisitions',StateFragment(fragment_id='a',kind='gdc',summary='one record',provenance=('test',)))
 first=project_state(state,ProjectionSpec(projection_name='candidate',candidate_id='c'));second=project_state(state,ProjectionSpec(projection_name='candidate',candidate_id='c'))
 assert first==second and 'acquisitions' not in first.payload and first.projection_id.startswith('candidate-v1-')
def test_deterministic_science_methods_produce_measurements_before_admission():
 executor=ScienceExecutor()
 summary=executor.execute(AnalysisSpec(analysis_id='summary',question='q',population='p',estimand='mean',method='descriptive_summary',variables=('values',),inputs={'values':[1.0,2.0,3.0]}))
 regression=executor.execute(AnalysisSpec(analysis_id='ols',question='q',population='p',estimand='slope',method='ordinary_least_squares',variables=('x','y'),inputs={'x':[1.0,2.0,3.0],'y':[2.0,4.0,6.0]}))
 assert summary.values['mean']==2.0 and regression.values['slope']==pytest.approx(2.0)
 assert summary.provenance[0]=='pandas.Series' and regression.provenance[0]=='statsmodels.OLS'
def test_capability_index_is_bounded_and_distinguishes_metadata_from_execution():
 index=initial_oncolab_index();matches=index.search('GDC cancer',kinds=(OncoLabKind.SOURCE,),limit=3)
 assert matches[0].capability_id=='source.gdc' and matches[0].availability.value=='available'
 assert index.count()>=100
 assert index.verification_records('source.gdc')
 assert index.describe_with_verification('source.gdc')['verification']
 assert index.describe('jev.choice').validation_state.value=='unvalidated'
 assert OncoLabKind.JEV in index.list_kinds()
 with pytest.raises(ValueError):index.search(limit=21)
def test_github_sandbox_is_commit_pinned_credential_free_and_replay_validated():
 seen=[]
 def runner(arguments,**kwargs):
  seen.append((arguments,kwargs))
  if arguments[:2]==('git','ls-remote'):return subprocess.CompletedProcess(arguments,0,'a'*40+'\tHEAD\n','')
  if arguments[0]=='docker':
   command=arguments[arguments.index('python:3.12-slim')+1:]
   output='{"values":{"effect":1.25}}\n' if command==('python','method.py','/input/request.json') else 'ok\n'
   return subprocess.CompletedProcess(arguments,0,output,'')
  return subprocess.CompletedProcess(arguments,0,'','')
 sandbox=DockerScientificSandbox(runner=runner)
 request=GithubMethodRequest(repository_url='https://github.com/example/public-method',requested_ref='main',test_command=('python','-m','pytest'),execute_command=('python','method.py','/input/request.json'),input_json={'x':[1,2,3]})
 candidate=sandbox.acquire_and_execute(request);measurement=validate_sandbox_candidate(candidate,'sandbox-analysis')
 assert candidate.receipt.commit_sha=='a'*40 and measurement.values=={'effect':1.25}
 assert candidate.receipt.first_run.stdout_sha256==candidate.receipt.replay_run.stdout_sha256
 assert all('OPENROUTER_API_KEY' not in kwargs['env'] and 'TYPESAFE_API_KEY' not in kwargs['env'] for _,kwargs in seen)
 docker_calls=[arguments for arguments,_ in seen if arguments[0]=='docker'];assert '--network' in docker_calls[0] and docker_calls[0][docker_calls[0].index('--network')+1]=='bridge'
 assert '/input/request.json:ro' not in docker_calls[0]
 assert all(call[call.index('--network')+1]=='none' for call in docker_calls[1:])
 with pytest.raises(ValidationError):GithubMethodRequest(repository_url='git@github.com:example/public-method.git',test_command=('python','-m','pytest'),execute_command=('python','method.py'),input_json={})
def test_researcher_instances_and_skill_selections_are_fresh_per_block():
 agents=create_agents('test','test');assert agents.fresh_researcher() is not agents.researcher
 skills=BlockSkillStore();skills.start('first');assert skills.select('first','statistics')
 skills.start('second');assert skills.selected('second')==()
 first_index=initial_oncolab_index();second_index=initial_oncolab_index();assert first_index is not second_index
def test_researcher_can_use_sandbox_tool_without_promoting_method():
 class FakeSandbox:
  def acquire_and_execute(self,request):
   invocation=SandboxInvocation(command=('python','method.py'),exit_status=0,stdout_sha256='o',stderr_sha256='e')
   receipt=SandboxReceipt(repository_url=request.repository_url,commit_sha='a'*40,environment={'image':'test'},environment_sha256='environment',input_sha256='input',install=invocation,test=invocation,first_run=invocation,replay_run=invocation)
   return SandboxMeasurementCandidate(candidate_id='candidate',receipt=receipt,values={'effect':1.0})
 manager=BlockManager();block=manager.create('sandbox objective','test',ResourceAllocation(seconds=60));runtime=HarnessRuntime(manager=manager,jev=DeterministicJevClient(),science=ScienceExecutor(),reasoner=DeterministicReasoner(),max_jev_calls=2,max_reasoner_calls=1,sandbox=FakeSandbox())
 runtime.research_state.start(block.block_id,block.objective);runtime.skills.start(block.block_id)
 agents=create_agents('test','test');calls=0
 async def model(messages,info):
  nonlocal calls
  calls+=1
  if calls==1:
   return ModelResponse(parts=[ToolCallPart('run_code',{'code':'await load_research_skills(need="github reproducibility")\ncandidate = await acquire_github_scientific_method(capability_need="novel method", why_existing_capabilities_are_inadequate="no installed method fits", repository_url="https://github.com/example/public-method", requested_ref="main", install_command=["python", "-m", "pip", "install", "."], test_command=["python", "-m", "pytest"], execute_command=["python", "method.py", "/input/request.json"], input_json={"x": [1]})\nawait validate_sandbox_measurement(candidate_id=candidate["candidate_id"], analysis_id="sandbox-analysis")\nawait admit_measurement(analysis_id="sandbox-analysis")\ncandidate'},tool_call_id='sandbox-code')])
  return ModelResponse(parts=[TextPart('sandbox complete')])
 researcher=agents.fresh_researcher()
 with researcher.override(model=scripted(model)):
  result=researcher.run_sync('use the sandbox',deps=ResearcherDeps(runtime=runtime,block_id=block.block_id))
 assert result.output=='sandbox complete'
 events={event.event_type for event in manager.ledger(block.block_id).history()}
 assert {'ResearchSkillsLoaded','GithubAcquisitionCompleted','SandboxMeasurementValidated','EvidenceAdmission'}<=events
 assert runtime.oncolab.describe('software.github-scientific').validation_state.value=='unvalidated'
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
   return ModelResponse(parts=[ToolCallPart('run_code',{'code':'await search_oncolab(query="regression", kinds=["statistical_method"], limit=3)\nawait describe_oncolab(capability_id="stat.statsmodels")\nawait acquire_gdc(endpoint="files", filters={"op":"in", "content":{"field":"files.data_type", "value":["Gene Expression Quantification"]}}, fields=["file_id"], size=1)\nawait search_xena(query="TCGA", limit=1)\nawait search_public_literature(query="oncology", limit=1)\nawait run_statistics(analysis_id="analysis", question="synthetic", estimand="difference", method="independent_t_test", inputs={"group_a":[1.0, 2.0, 3.0], "group_b":[4.0, 5.0, 6.0]})\nawait admit_measurement(analysis_id="analysis")\nawait create_line_figure(title="synthetic", x=[1.0, 2.0, 3.0], y=[1.0, 4.0, 9.0])\nawait block_status()\nawait evaluate_candidate(candidate_id="candidate", candidate_summary="synthetic subgroup")\nhypotheses = await generate_hypotheses(finding="effect found")\nawait request_scope_escalation(proposed_test="mechanistic experiment", rationale="beyond scope")\nawait complete_block(reason="researcher complete")\nhypotheses'},tool_call_id='researcher-code')])
  return ModelResponse(parts=[TextPart('researcher complete')])
 with agents.director.override(model=scripted(director_model)),agents.researcher.override(model=scripted(researcher_model)):
  result=agents.director.run_sync('allocate and investigate',deps=DirectorDeps(runtime))
 assert result.output=='director complete'
 block=manager.blocks()[0];assert manager.status(block) is BlockStatus.COMPLETE
 event_types={event.event_type for event in manager.ledger(block.block_id).history()}
 assert {'DirectorBlockAllocated','CapabilityInvocation','CapabilityResult','ScienceMeasurement','EvidenceAdmission','JevExecution','FrontierDecision','ReasonerOutput','ScopeEscalationRequested','ResearcherCompletion'}<=event_types
 gdc_request=next(request for request in seen if request.url.host=='api.gdc.cancer.gov');assert 'x-auth-token' not in gdc_request.headers and b'"files.access"' in gdc_request.content and b'"open"' in gdc_request.content
 xena_request=next(request for request in seen if request.url.host=='ucscpublic.xenahubs.net');assert xena_request.method=='POST' and xena_request.url.path=='/data/' and xena_request.headers['content-type']=='text/plain'
