from oncojev.reasoner.models import Hypothesis,ReasonerOutput
class DeterministicReasoner:
 def generate(self,objective:str,finding:str)->ReasonerOutput:return ReasonerOutput(interpretation=finding,uncertainty="Replication needed.",hypotheses=(Hypothesis(hypothesis_id="within",statement="Replicate the association.",within_scope=True,proposed_test="replicate cohort"),Hypothesis(hypothesis_id="beyond",statement="Test a causal mechanism.",within_scope=False,proposed_test="mechanistic experiment")))
