from datetime import UTC,datetime,timedelta
from pathlib import Path
import pytest
from pydantic import ValidationError
from oncojev.block.manager import BlockManager
from oncojev.block.models import BlockStatus
from oncojev.config.loader import load_models_config
from oncojev.director.models import ResourceAllocation
from oncojev.dossier.models import Dossier
from oncojev.jev.client import DeterministicJevClient
from oncojev.jev.frontier import FrontierAction,FrontierPolicy
from oncojev.jev.models import JevExecutionFailure,JevFailureCategory,JevQuestionSpec,NoulDecision
from oncojev.ledger.events import LedgerEvent
from oncojev.ledger.store import Ledger
from oncojev.reasoner.models import Hypothesis,ReasonerOutput
from oncojev.runtime.pydantic_ai.agents import create_agents
from oncojev.science.admission import admit_scientific_evidence
from oncojev.science.execution import GeneratedAnalysisCode
from oncojev.service import run_synthetic_vertical_slice
ROOT=Path(__file__).resolve().parents[2]
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
