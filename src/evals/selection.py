"""Recall-sensitive capability-selection evaluation, separate from SDK smoke.

Labels and distributions are reported without declaring a winning condition.
The same lookup/description/check/measurement composition is used in production.
"""
from time import perf_counter
from pydantic import BaseModel, Field
from src.oncolab.execution import check_routes
from src.provenance import content_hash
from src.runtime.pydantic_ai.semantic import measure


class SelectionTask(BaseModel, frozen=True):
    task_id: str
    query: str
    need: dict
    useful_ids: tuple[str, ...]
    available_inputs: dict[str, int | bool] = Field(default_factory=dict)
    information_space: str


SELECTION_TASKS = (
    SelectionTask(task_id="public-literature",query="publication knowledge search",need={"estimand":"relevant publication metadata","design":"context discovery"},
                  useful_ids=("literature.public",),information_space="literature"),
    SelectionTask(task_id="slice-summary",query="stored response descriptive summary",need={"estimand":"response-slice count","design":"descriptive"},
                  useful_ids=("science.acquisition-summary",),available_inputs={"acquisition":True},information_space="public-metadata"),
    SelectionTask(task_id="lexical-mismatch",query="co movement linear association",need={"estimand":"linear correlation","design":"paired exploratory"},
                  useful_ids=("stat.scipy",),available_inputs={"x":5,"y":5},information_space="statistics"),
    SelectionTask(task_id="missing-pair",query="correlation statistics",need={"estimand":"correlation","design":"paired"},
                  useful_ids=("stat.scipy",),available_inputs={"x":5},information_space="statistics"),
    SelectionTask(task_id="unimplemented-survival",query="survival inference",need={"estimand":"censoring-aware survival contrast","design":"cohort"},
                  useful_ids=(),information_space="statistics"),
)


def evaluate_selection(runtime,block_id,tasks=SELECTION_TASKS,*,condition="jev_assisted",queries=None):
    """Optional Reasoner-proposed queries supplied explicitly with resource use.

    Label recall measures retrieval/retention, not scientific validity. Execution
    outcomes are unknown unless the caller actually performs source-bound work.
    """
    index = runtime.index_for(block_id)
    rows=[]
    for task in tasks:
        start=perf_counter();query=(queries or {}).get(task.task_id,task.query)
        retrieved=[];cursor=None;pages=[]
        while len(retrieved)<runtime.oncolab_candidate_k:
            page=index.search_page(query,limit=min(runtime.oncolab_search_k,runtime.oncolab_candidate_k-len(retrieved)),continuation=cursor)
            pages.append({"snapshot_id":page.snapshot_id,"retrieval_version":page.retrieval_version,"returned_ids":[c.capability_id for c in page.cards],"continuation":cursor})
            retrieved.extend(c.capability_id for c in page.cards);cursor=page.continuation
            if cursor is None:break
        candidates=[];retained=[];failures=[]
        for identity in retrieved:
            contract=index.describe_with_verification(identity)
            checks=check_routes(index.describe(identity),task.available_inputs,routes=index.routes)
            candidate={"capability_id":identity,"checks":checks,"contract_sha256":contract["contract_sha256"]}
            # Planning-only results stay visible and count toward discovery recall.
            if condition=="jev_assisted" and checks["eligible"]:
                try:
                    result=measure(runtime,block_id,"method",identity,{"need":task.need,"contract":contract["descriptor"],"checks":checks,
                        "contract_sha256":contract["contract_sha256"],"retrieval":pages},eligible=checks["eligible"])
                    candidate["measurement"]=result
                    if result["frontier"]["action"]!="reject_retain":retained.append(identity)
                except Exception as error:
                    failures.append({"candidate_id":identity,"error_type":type(error).__name__})
                    retained.append(identity) # Operational failure is not semantic rejection.
            else:retained.append(identity)
            candidates.append(candidate)
        useful=set(task.useful_ids)
        rows.append({"task_id":task.task_id,"information_space":task.information_space,"query":query,"need":task.need,
            "labels":task.useful_ids,"retrieved_ids":retrieved,"retained_ids":retained,"retrieval":pages,"candidates":candidates,
            "retrieval_recall":len(useful & set(retrieved))/len(useful) if useful else None,
            "retained_recall":len(useful & set(retained))/len(useful) if useful else None,
            "operational_failures":failures,"elapsed_seconds":perf_counter()-start,
            "downstream_scientific_utility":None,"cost":None,"source_attempts":runtime.resources(block_id)["source"]["attempted"]})
    return {"version":"selection-evaluation-v1","condition":condition,"rows":rows,"resources":runtime.resources(block_id),
            "label_set_sha256":content_hash([t.model_dump(mode="json") for t in tasks]),
            "reasoner_query_use":queries or {},"limits_comparable":queries is None,
            "interpretation":"Deterministic clients prove routing only; empirical utility requires real labelled model measurements."}
