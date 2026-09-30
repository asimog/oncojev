from pydantic import BaseModel
from oncojev.science.models import AnalysisSpec,MeasuredResult
class GeneratedAnalysisCode(BaseModel,frozen=True): source:str
class ScienceExecutor:
    def execute(self,spec:AnalysisSpec)->MeasuredResult:
        if spec.method!="synthetic_group_difference":raise ValueError("unsupported method")
        return MeasuredResult(analysis_id=spec.analysis_id,values={"effect_size":1.2,"p_value":0.01,"n":24},provenance=("synthetic-fixture-v1",spec.analysis_id))
