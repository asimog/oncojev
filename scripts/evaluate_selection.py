"""Run labelled selection evaluation; provider smoke is not scientific utility."""
import argparse
import json
from pathlib import Path

from src.config.environment import load_local_environment
from src.config.loader import load_models_config, load_runtime_config
from src.config.models import RuntimeMode
from src.evals.selection import evaluate_selection
from src.persistence.repository import ResearchRepository
from src.persistence.store import SqliteResearchStore
from src.runtime.pydantic_ai.factory import build_harness_runtime, build_jev_client


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--live",action="store_true")
    parser.add_argument("--output",type=Path)
    parser.add_argument("--diagnostic-candidate-k",type=int, help="Separate larger-budget diagnostic; baseline always uses configured limits")
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    load_local_environment(root)
    models=load_models_config(root/"config/models.yaml")
    policy=load_runtime_config(root/"config/runtime.yaml").model_copy(update={"mode":RuntimeMode.DETERMINISTIC})
    reports=[]
    budgets = [("configured_baseline", policy.oncolab.candidate_k)]
    if args.diagnostic_candidate_k:
        if args.diagnostic_candidate_k <= policy.oncolab.candidate_k: parser.error("diagnostic must exceed configured candidate budget")
        budgets.append(("larger_budget_diagnostic", args.diagnostic_candidate_k))
    for budget_kind, candidate_k in budgets:
      for condition in ("deterministic","jev_assisted"):
        store=SqliteResearchStore();repository=ResearchRepository(store)
        try:
            runtime=build_harness_runtime(models,policy,repository=repository)
            runtime.oncolab_candidate_k=candidate_k
            if args.live and condition=="jev_assisted":runtime.jev=build_jev_client(models,RuntimeMode.LIVE,policy=policy)
            block=runtime.manager.allocate("Labelled capability selection","evaluation")
            repository.record_block(block)
            report=evaluate_selection(runtime,block.block_id,condition=condition)
            report["budget_kind"] = budget_kind
            report["limits"] = {"candidate_k": candidate_k, "search_k": policy.oncolab.search_k}
            report["provider_mode"]="live" if args.live and condition=="jev_assisted" else "deterministic_fixture"
            from src.persistence.records import RecordKind
            latest={r.record_id:r.payload for r in store.records(kind=RecordKind.JEV_CALL)}
            report["jev_receipts"]=list(latest.values())
            reports.append(report)
        finally:store.close()
    artifact={"reports":reports,"limits":{"configured_candidate_k":policy.oncolab.candidate_k,"search_k":policy.oncolab.search_k,"source_execution":False},
              "scope":"Capability selection labels; no downstream scientific acquisition or utility claim."}
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(artifact,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps([{"condition":r["condition"],"mode":r["provider_mode"],"rows":[{"task_id":x["task_id"],"retrieval_recall":x["retrieval_recall"],"retained_recall":x["retained_recall"],"failures":len(x["operational_failures"])} for x in r["rows"]]} for r in reports]))


if __name__=="__main__":main()
