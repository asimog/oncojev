import numpy as np
import pandas as pd
from pydantic import BaseModel
from scipy import stats
import statsmodels.api as sm
from src.science.models import AnalysisSpec,MeasuredResult
class GeneratedAnalysisCode(BaseModel,frozen=True): source:str
class ScienceExecutor:
    def execute(self,spec:AnalysisSpec)->MeasuredResult:
        if spec.method=="synthetic_group_difference":
            values={"effect_size":1.2,"p_value":0.01,"n":24};source="synthetic-fixture-v1"
        elif spec.method=="independent_t_test":
            a=np.asarray(spec.inputs["group_a"],dtype=float);b=np.asarray(spec.inputs["group_b"],dtype=float)
            result=stats.ttest_ind(a,b,equal_var=False);values={"effect_size":float(a.mean()-b.mean()),"statistic":float(result.statistic),"p_value":float(result.pvalue),"n_a":int(a.size),"n_b":int(b.size)};source="scipy.ttest_ind"
        elif spec.method=="pearson_correlation":
            x=np.asarray(spec.inputs["x"],dtype=float);y=np.asarray(spec.inputs["y"],dtype=float);result=stats.pearsonr(x,y)
            values={"correlation":float(result.statistic),"p_value":float(result.pvalue),"n":int(x.size)};source="scipy.pearsonr"
        elif spec.method=="ordinary_least_squares":
            x=np.asarray(spec.inputs["x"],dtype=float);y=np.asarray(spec.inputs["y"],dtype=float);fit=sm.OLS(y,sm.add_constant(x)).fit()
            values={"intercept":float(fit.params[0]),"slope":float(fit.params[1]),"p_value":float(fit.pvalues[1]),"r_squared":float(fit.rsquared),"n":int(x.size)};source="statsmodels.OLS"
        elif spec.method=="descriptive_summary":
            series=pd.Series(spec.inputs["values"],dtype="float64")
            values={"n":int(series.count()),"missing":int(series.isna().sum()),"mean":float(series.mean()),"median":float(series.median()),"standard_deviation":float(series.std(ddof=1))};source="pandas.Series"
        else:raise ValueError(f"unsupported method: {spec.method}")
        return MeasuredResult(analysis_id=spec.analysis_id,values=values,provenance=(source,spec.analysis_id))
