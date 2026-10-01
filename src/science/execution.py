import hashlib
import json
import math

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from src.science.models import AnalysisSpec,MeasuredResult
from src.sources.models import AcquisitionRecord
class ScienceExecutor:
    def execute(self,spec:AnalysisSpec)->MeasuredResult:
        if spec.method=="independent_t_test":
            a=self._array(spec.inputs,"group_a",minimum=2);b=self._array(spec.inputs,"group_b",minimum=2)
            result=stats.ttest_ind(a,b,equal_var=False);values={"effect_size":float(a.mean()-b.mean()),"statistic":float(result.statistic),"p_value":float(result.pvalue),"n_a":int(a.size),"n_b":int(b.size)};source="scipy.ttest_ind"
        elif spec.method=="pearson_correlation":
            x=self._array(spec.inputs,"x",minimum=2);y=self._array(spec.inputs,"y",minimum=2);self._same_length(x,y);result=stats.pearsonr(x,y)
            values={"correlation":float(result.statistic),"p_value":float(result.pvalue),"n":int(x.size)};source="scipy.pearsonr"
        elif spec.method=="ordinary_least_squares":
            x=self._array(spec.inputs,"x",minimum=3);y=self._array(spec.inputs,"y",minimum=3);self._same_length(x,y);fit=sm.OLS(y,sm.add_constant(x)).fit()
            values={"intercept":float(fit.params[0]),"slope":float(fit.params[1]),"p_value":float(fit.pvalues[1]),"r_squared":float(fit.rsquared),"n":int(x.size)};source="statsmodels.OLS"
        elif spec.method=="descriptive_summary":
            values_input=self._array(spec.inputs,"values",minimum=2);series=pd.Series(values_input,dtype="float64")
            values={"n":int(series.count()),"missing":int(series.isna().sum()),"mean":float(series.mean()),"median":float(series.median()),"standard_deviation":float(series.std(ddof=1))};source="pandas.Series"
        else:raise ValueError(f"unsupported method: {spec.method}")
        self._require_finite(values)
        digest=self._hash({"method":spec.method,"inputs":spec.inputs,"source_refs":spec.source_refs})
        return MeasuredResult(analysis_id=spec.analysis_id,values=values,provenance=(source,spec.analysis_id),origin="provided",source_refs=spec.source_refs,input_sha256=digest)

    def measure_acquisition(self,record:AcquisitionRecord,analysis_id:str,field:str|None=None)->MeasuredResult:
        if field is None:
            values={"record_count":len(record.records)};method="record_count"
        else:
            extracted=[]
            for item in record.records:
                value: object = item
                for part in field.split("."):
                    if not isinstance(value, dict):
                        value = None
                        break
                    value = value.get(part)
                if isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(float(value)):
                    extracted.append(float(value))
            if not extracted:
                raise ValueError(f"no finite numeric values found for field: {field}")
            series=pd.Series(extracted,dtype="float64")
            values={"n":int(series.count()),"mean":float(series.mean()),"median":float(series.median()),"standard_deviation":float(series.std(ddof=1)) if len(series)>1 else 0.0}
            method=f"numeric_summary:{field}"
        self._require_finite(values)
        return MeasuredResult(analysis_id=analysis_id,values=values,provenance=("acquisition-v2",record.source,method),origin="source",source_refs=(record.acquisition_id,),input_sha256=record.content_sha256,
                              limitations=("Descriptive measurement of the stored response slice; population coverage is unknown.",))

    @staticmethod
    def _hash(value:object)->str:
        return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

    @staticmethod
    def _require_finite(values:dict[str,object])->None:
        if not values:
            raise ValueError("measurement values cannot be empty")
        for value in values.values():
            if isinstance(value,(int,float)) and not isinstance(value,bool) and not math.isfinite(float(value)):
                raise ValueError("measurement values must be finite")

    @staticmethod
    def _array(inputs:dict[str,list[float]],name:str,*,minimum:int)->np.ndarray:
        if name not in inputs:
            raise ValueError(f"missing numeric input: {name}")
        values=np.asarray(inputs[name],dtype=float)
        if values.ndim!=1 or values.size<minimum:
            raise ValueError(f"{name} requires at least {minimum} one-dimensional values")
        if not np.isfinite(values).all():
            raise ValueError(f"{name} contains non-finite values")
        return values

    @staticmethod
    def _same_length(first:np.ndarray,second:np.ndarray)->None:
        if first.size!=second.size:
            raise ValueError("paired numeric inputs must have equal lengths")
