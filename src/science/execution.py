import hashlib
import json
import math

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from src.science.models import AnalysisSpec, MeasuredResult, InvalidAnalysis
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
        return MeasuredResult(analysis_id=spec.analysis_id,values=values,provenance=(source,spec.analysis_id),origin="provided",source_refs=spec.source_refs,input_sha256=digest,interpretation="exploratory")

    def measure_acquisition(self,record:AcquisitionRecord,analysis_id:str,field:str|None=None)->MeasuredResult:
        if field is None:
            values={"record_count":len(record.records)};method="record_count"
        else:
            extracted=[]
            counts={"total_rows":len(record.records),"valid_numeric":0,"absent":0,"null":0,"invalid_type":0,"nonfinite":0}
            for item in record.records:
                category,value=self._numeric(item,field)
                counts[category]+=1
                if category=="valid_numeric":extracted.append(value)
            series=pd.Series(extracted,dtype="float64")
            values={**counts,"n":len(extracted),"mean":float(series.mean()) if extracted else None,
                    "median":float(series.median()) if extracted else None,
                    "standard_deviation":float(series.std(ddof=1)) if len(extracted)>1 else None}
            method=f"numeric_summary:{field}"
        self._require_finite(values)
        return MeasuredResult(analysis_id=analysis_id,values=values,provenance=("acquisition-v2",record.source,method),origin="synthetic" if record.origin=="synthetic" else "source",source_refs=(record.acquisition_id,),input_sha256=record.content_sha256,
                              limitations=("Descriptive measurement of the stored response slice; population coverage is not inferred.",),
                              interpretation="descriptive",analysis_key=self._hash({"input":record.content_sha256,"method":method,"version":"source-summary-v3"}),
                              diagnostics={"coverage":record.coverage.model_dump(mode="json") if record.coverage else None,
                                           "undefined":{key:"no valid numeric observations" if not values.get("n") else "sample SD requires n>=2"
                                                        for key in ("mean","median","standard_deviation") if key in values and values[key] is None}})

    def execute_source(self,record:AcquisitionRecord,spec:AnalysisSpec)->MeasuredResult:
        """Resolve paired values from one owned row set; never join caller arrays."""
        if spec.inputs or spec.source_refs != (record.acquisition_id,):
            raise InvalidAnalysis("source analysis requires exact resolved acquisition, not supplied arrays")
        if spec.method not in {"pearson_correlation","ordinary_least_squares"}:
            raise InvalidAnalysis("unsupported source-resolved method")
        if set(spec.fields)!={"x","y"} or not spec.entity_field or not spec.population.strip() or not spec.estimand.strip():
            raise InvalidAnalysis("declare entity key, population, estimand and x/y fields")
        if record.source=="gdc":
            endpoint=record.coverage.endpoint if record.coverage else record.provenance[-1]
            units={"cases":{"case","patient"},"files":{"file"},"projects":{"project"},"annotations":{"annotation"}}
            if endpoint not in units or spec.entity_unit not in units[endpoint] or spec.entity_field!="id":
                raise InvalidAnalysis("GDC entity unit/key must match endpoint; joined rows require a separate contract")
        if record.source == "gdc-derived" and (record.request.get("transform_version") != "gdc-tabular-transform-v1"
                or record.request.get("entity_unit") != spec.entity_unit or spec.entity_field not in {"entity_id", "case_id"}):
            raise InvalidAnalysis("derived source entity unit/key must match its validated transform")
        if spec.covariates or set(spec.transformations)-{"x","y"}:
            raise InvalidAnalysis("this operation does not implement covariates or undeclared transformations")
        pairs={"x":[],"y":[]};entities=[];seen=set();excluded={};counts={"total_rows":len(record.records),"complete_pairs":0,"excluded_rows":0}
        for row in record.records:
            entity=self._field(row,spec.entity_field)
            if entity is None or isinstance(entity,(dict,list,bool)):
                raise InvalidAnalysis("missing or non-scalar entity identity")
            identity=self._hash({"entity":entity})
            if identity in seen:raise InvalidAnalysis("duplicate entity rows require an explicit aggregation/join contract")
            seen.add(identity)
            pair={};valid=True
            for axis,field in spec.fields.items():
                category,value=self._numeric(row,field)
                if category!="valid_numeric":
                    excluded[f"{axis}:{category}"]=excluded.get(f"{axis}:{category}",0)+1;valid=False
                elif spec.transformations.get(axis,"identity")=="log1p":
                    if value<=-1:raise InvalidAnalysis("log1p requires values greater than -1")
                    pair[axis]=math.log1p(value)
                else:pair[axis]=value
            if not valid:counts["excluded_rows"]+=1;continue
            entities.append(entity)
            for axis in pairs:pairs[axis].append(pair[axis])
        counts["complete_pairs"]=len(entities)
        minimum=3 if spec.method=="ordinary_least_squares" else 2
        if len(entities)<minimum or len(set(pairs["x"]))<2 or len(set(pairs["y"]))<2:
            raise InvalidAnalysis("paired analysis requires enough complete nonconstant observations")
        standardization = {}
        for axis in ("x", "y"):
            if spec.transformations.get(axis) == "zscore":
                values = np.asarray(pairs[axis], dtype=float)
                mean, deviation = float(values.mean()), float(values.std(ddof=1))
                if not math.isfinite(deviation) or deviation <= 0:
                    raise InvalidAnalysis("zscore requires finite nonzero complete-pair sample SD")
                pairs[axis] = ((values - mean) / deviation).tolist()
                standardization[axis] = {"mean": mean, "sample_sd": deviation, "ddof": 1, "n": len(values)}
        exploratory=self.execute(spec.model_copy(update={"inputs":pairs}))
        exclusions = {"analysis_id", "source_refs", "inputs", "replication_id"}
        if spec.test_plan is None:
            exclusions.add("test_plan")  # preserve historical v1 analysis identity
        contract=spec.model_dump(mode="json",exclude=exclusions)
        version = "source-paired-test-v1" if spec.test_plan else "source-paired-v1"
        if standardization:
            version = "source-paired-standardized-test-v1" if spec.test_plan else "source-paired-standardized-v1"
        key=self._hash({"content":record.content_sha256,"contract":contract,"version":version})
        test = self._test_association(pairs, spec) if spec.test_plan else None
        if test:
            exploratory = exploratory.model_copy(update={"values": {**exploratory.values, **test["values"]}})
            self._require_finite(exploratory.values)
        return exploratory.model_copy(update={"origin":"synthetic" if record.origin=="synthetic" else "source","source_refs":(record.acquisition_id,),"input_sha256":record.content_sha256,
            "analysis_key":key,"replication_id":spec.replication_id,"interpretation":"associative",
            "provenance":(*exploratory.provenance,"source-paired-v1",version,key) if spec.test_plan else (*exploratory.provenance,"source-paired-v1",key),
            "diagnostics":{"counts":counts,"excluded_fields":excluded,"paired_entities":entities,"fields":spec.fields,
                           "design":spec.design,"entity_unit":spec.entity_unit,"population":spec.population,"estimand":spec.estimand,
                           "transformations":spec.transformations,"standardization":standardization,"coverage":record.coverage.model_dump(mode="json") if record.coverage else None,
                           **({"hypothesis_test": test["diagnostics"]} if test else {})},
            "limitations":("Association over complete stored rows; no causal interpretation.",
                            "Inference requires independent observations and method-specific assumptions; these are declared, not empirically guaranteed.",
                            "Response coverage does not establish population representativeness.",
                            *(("Exploratory directional test; adaptive data/hypothesis selection and model-assumption failures are not ruled out.",) if test else ()))})

    @staticmethod
    def _test_association(pairs, spec):
        plan = spec.test_plan
        alpha = plan.alpha / len(plan.multiplicity_family)
        if spec.method == "pearson_correlation":
            if plan.minimum_effect >= 1:
                raise InvalidAnalysis("correlation effect bound must be less than one")
            result = stats.pearsonr(pairs["x"], pairs["y"])
            interval = result.confidence_interval(confidence_level=1-alpha)
            low, high, p_value = float(interval.low), float(interval.high), float(result.pvalue)
            uncertainty_method = "scipy.pearsonr Fisher confidence interval"
        else:
            fit = sm.OLS(pairs["y"], sm.add_constant(pairs["x"])).fit()
            low, high = (float(v) for v in fit.conf_int(alpha=alpha)[1])
            p_value = float(fit.pvalues[1])
            uncertainty_method = "statsmodels.OLS slope t confidence interval"
        if not all(math.isfinite(value) for value in (low, high, p_value)):
            raise InvalidAnalysis("undefined effect uncertainty cannot establish a hypothesis outcome")
        signed_low, signed_high = (low, high) if plan.direction == "positive" else (-high, -low)
        outcome = ("supported" if signed_low > plan.minimum_effect else
                   "contradicted" if signed_high < -plan.minimum_effect else "inconclusive")
        return {"values": {"effect_ci_low": low, "effect_ci_high": high, "alpha_per_test": alpha,
                           "p_value_adjusted": min(1., p_value * len(plan.multiplicity_family))},
                "diagnostics": {"plan": plan.model_dump(mode="json"), "outcome": outcome,
                    "uncertainty_method": uncertainty_method, "multiplicity": "Bonferroni simultaneous intervals",
                    "meaning": "Directional effect-bound comparison conditional on the declared association model; no causal, absence or clinical claim."}}

    @staticmethod
    def _field(row,field):
        value=row
        for part in field.split("."):
            if not isinstance(value,dict) or part not in value:return None
            value=value[part]
        return value

    @staticmethod
    def _numeric(row,field):
        value=row
        for part in field.split("."):
            if isinstance(value,(list,tuple)):
                raise InvalidAnalysis("numeric field crosses an array; declare a supported representation or aggregation first")
            if not isinstance(value,dict) or part not in value:return "absent",None
            value=value[part]
        if value is None:return "null",None
        if isinstance(value,bool) or not isinstance(value,(int,float)):return "invalid_type",None
        if not math.isfinite(float(value)):return "nonfinite",None
        return "valid_numeric",float(value)

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
