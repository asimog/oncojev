from datetime import UTC,datetime
from pathlib import Path
from src.block.manager import BlockManager
from src.config.loader import load_models_config,load_runtime_config
from src.director.models import ResourceAllocation
from src.dossier.models import JevBlockDossier
from src.jev.client import DeterministicJevClient
from src.jev.frontier import FrontierPolicy
from src.jev.models import JevQuestionSpec
from src.ledger.events import LedgerEvent
from src.reasoner.service import DeterministicReasoner
from src.science.admission import admit_scientific_evidence
from src.science.execution import ScienceExecutor
from src.science.models import AnalysisSpec
def run_synthetic_vertical_slice(root:Path)->JevBlockDossier:
 load_models_config(root/"config/models.yaml");runtime=load_runtime_config(root/"config/runtime.yaml")
 manager=BlockManager();block=manager.create("Investigate a synthetic treatment-resistance signal.","No prior evidence addresses the supplied direction.",ResourceAllocation(seconds=int(runtime.block["default_seconds"] or 600)));ledger=manager.ledger(block.block_id);ledger.append(LedgerEvent(event_type="DirectorDecision",occurred_at=datetime.now(UTC),payload={"block_id":block.block_id}))
 qs=(JevQuestionSpec(question_id="relevance",semantic_purpose="candidate relevance",primitive="noul",projection_id="candidate-v1",instructions="Assess relevance.",criteria={"criterion":"relevance"},question_version="1"),JevQuestionSpec(question_id="next_action",semantic_purpose="local action",primitive="choice",projection_id="candidate-v1",instructions="Choose a safe action.",criteria={"ADVANCE":"continue","DEFER":"wait","NONE":"no fit"},question_version="1"))
 ds=DeterministicJevClient().evaluate({"objective":block.objective,"candidate":"synthetic subgroup"},qs);frontier=FrontierPolicy().decide("synthetic-candidate",ds,("synthetic-retrieval",));ledger.append(LedgerEvent(event_type="JevExecution",occurred_at=datetime.now(UTC),payload={"question_ids":[x.question_id for x in qs]}));ledger.append(LedgerEvent(event_type="FrontierDecision",occurred_at=datetime.now(UTC),payload={"action":frontier.action}))
 result=ScienceExecutor().execute(AnalysisSpec(analysis_id="synthetic-analysis",question=block.objective,population="synthetic cohort",estimand="group difference",method="synthetic_group_difference",variables=("group","outcome")));evidence=admit_scientific_evidence(result);ledger.append(LedgerEvent(event_type="EvidenceAdmission",occurred_at=datetime.now(UTC),payload={"evidence_id":evidence.evidence_id}))
 reasoner=DeterministicReasoner().generate(block.objective,"Synthetic analysis found effect size 1.2 and p=0.01.");within=next(x for x in reasoner.hypotheses if x.within_scope);beyond=next(x for x in reasoner.hypotheses if not x.within_scope);completed=manager.complete(block,"researcher_complete")
 dossier=JevBlockDossier(block_id=block.block_id,objective=block.objective,termination_reason=completed.termination_reason or "unknown",evidence_refs=(evidence.evidence_id,),positive_findings=("Synthetic group difference measured.",),hypotheses=(within.statement,beyond.statement),unresolved_uncertainties=(reasoner.uncertainty,),important_jev_measurements=tuple(x.question_id for x in ds),frontier_decisions=(frontier.action,),analyses_performed=(result.analysis_id,),resource_usage={"jev_calls":1,"reasoner_calls":1},recommended_next_blocks=(beyond.proposed_test,),preferred_continuation=within.proposed_test,preferred_continuation_reason="Within scope; broader mechanism work is proposed to Director.")
 ledger.append(LedgerEvent(event_type="DossierHandoff",occurred_at=datetime.now(UTC),payload={"block_id":block.block_id}));return dossier
