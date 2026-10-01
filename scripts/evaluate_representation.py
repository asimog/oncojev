"""Evaluate retained representation alternatives with labels isolated from runtime."""
import argparse
import asyncio
import json
from pathlib import Path

from src.config.environment import load_local_environment
from src.config.loader import load_models_config, load_runtime_config
from src.config.models import RuntimeMode
from src.evals.representation import RepresentationCase, evaluate_representations
from src.persistence.repository import ResearchRepository
from src.persistence.store import SqliteResearchStore
from src.persistence.records import RecordKind
from src.runtime.pydantic_ai.factory import build_harness_runtime, build_jev_client
from src.sources.models import AcquisitionRecord


async def main_async(args):
    root = Path(__file__).resolve().parents[1]
    dataset = json.loads(args.corpus.read_text(encoding="utf-8"))
    cases = tuple(RepresentationCase.model_validate(row) for row in dataset["cases"])
    inputs = tuple(AcquisitionRecord.model_validate(row) for row in dataset["acquisitions"])
    models = load_models_config(root / "config/models.yaml")
    policy = load_runtime_config(root / "config/runtime.yaml").model_copy(update={"mode": RuntimeMode.DETERMINISTIC})
    reports = []
    if args.live:
        load_local_environment(root)
    for condition in ("deterministic", "jev_assisted"):
        store = SqliteResearchStore()
        runtime = None
        try:
            runtime = build_harness_runtime(models, policy, repository=ResearchRepository(store))
            runtime.max_jev_calls = args.jev_calls
            runtime.max_jev_questions = args.jev_questions
            if args.live and condition == "jev_assisted":
                runtime.jev = build_jev_client(models, RuntimeMode.LIVE, policy=policy)
            block = runtime.manager.allocate("Labelled retained-representation evaluation", "evaluation")
            runtime.repository.record_block(block)
            for record in inputs:
                runtime.retain_acquisition(block.block_id, record)
            report = await evaluate_representations(runtime, block.block_id, cases, condition=condition)
            report["provider_mode"] = "live" if args.live and condition == "jev_assisted" else "deterministic_fixture"
            report["jev_receipts"] = list({r.record_id:r.payload for r in store.records(kind=RecordKind.JEV_CALL)}.values())
            reports.append(report)
        finally:
            if runtime:
                await asyncio.gather(*(client.aclose() for client in (runtime.gdc, runtime.xena, runtime.literature)))
            store.close()
    artifact = {"corpus_version": dataset["version"], "reports": reports,
                "scope": dataset["scope"], "scientific_admission": False}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps([{ "condition": r["condition"], "provider_mode": r["provider_mode"],
        "rows": [{"case_id": row["case_id"], "retained_recall": row["retained_recall"],
                   "missed": row["missed_useful_ids"], "failures": len(row["operational_failures"])} for row in r["rows"]]} for r in reports]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Path("evals/representation/input-contracts-v1.json"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--jev-calls", type=int, default=16, choices=range(1,101))
    parser.add_argument("--jev-questions", type=int, default=100, choices=range(1,501))
    asyncio.run(main_async(parser.parse_args()))


if __name__ == "__main__":
    main()
