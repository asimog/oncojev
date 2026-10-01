"""Label-isolated evaluation of the production retained-representation path."""
from time import perf_counter
from typing import Literal
from pydantic import BaseModel, Field

from src.provenance import content_hash
from src.sources.representation import RepresentationNeed, assess_retained_representation
from src.runtime.pydantic_ai.semantic import measure_async


class RepresentationCase(BaseModel, frozen=True):
    case_id: str
    split: Literal["tuning", "held_out"]
    need: RepresentationNeed
    candidate_ids: tuple[str, ...] = Field(max_length=20)
    useful_ids: tuple[str, ...]
    label_basis: str = Field(min_length=1)
    label_scope: Literal["input_contract", "scientifically_reviewed"] = "input_contract"


async def evaluate_representations(runtime, block_id, cases, *, condition="deterministic"):
    if condition not in {"deterministic", "jev_assisted"}:
        raise ValueError("unsupported representation evaluation condition")
    rows = []
    for case in cases:
        started = perf_counter()
        candidates, retained, failures = [], [], []
        for identity in case.candidate_ids:
            try:
                record = runtime.resolve_acquisition(block_id, identity)
                checks = assess_retained_representation(record, case.need)
            except Exception as error:
                failures.append({"candidate_id": identity, "stage": "resolved_input", "error_type": type(error).__name__})
                continue
            candidate = {"candidate_id": identity, "checks": checks, "action": "keep_alive" if checks["eligible"] else "defer"}
            if condition == "jev_assisted":
                try:
                    # Labels, case identity/split and expected useful IDs never
                    # enter the provider projection or runtime science records.
                    result = await measure_async(runtime, block_id, "representation", identity,
                        {"need": case.need.model_dump(mode="json"), "representation": checks["representation"], "checks": checks},
                        eligible=checks["eligible"], escalate=True)
                    candidate["measurement"] = result
                    candidate["action"] = result["frontier"]["action"]
                except Exception as error:
                    failures.append({"candidate_id": identity, "stage": "semantic_measurement", "error_type": type(error).__name__})
                    candidate["fallback"] = "deterministic_input_gate"
            # Deterministic prerequisites apply even on provider failure.
            if checks["eligible"] and candidate["action"] not in {"defer", "reject_retain"}:
                retained.append(identity)
            candidates.append(candidate)
        useful = set(case.useful_ids)
        eligible = {c["candidate_id"] for c in candidates if c["checks"]["eligible"]}
        inspected = {c["candidate_id"] for c in candidates}
        rows.append({"case_id": case.case_id, "split": case.split, "label_scope": case.label_scope,
            "label_basis": case.label_basis, "labels": case.useful_ids, "candidates": candidates,
            "retrieved_ids": case.candidate_ids, "retained_ids": retained,
            "retrieval_recall": len(useful & set(case.candidate_ids))/len(useful) if useful else None,
            "input_gate_recall": len(useful & eligible)/len(useful) if useful else None,
            "retained_recall": len(useful & set(retained))/len(useful) if useful else None,
            "missed_useful_ids": sorted(useful - set(retained)),
            "invalid_retained_ids": sorted(set(retained) - eligible),
            "unresolved_ids": sorted(set(case.candidate_ids) - inspected),
            "operational_failures": failures, "elapsed_seconds": perf_counter()-started,
            "scientific_utility": None, "cost": None})
    return {"version": "representation-evaluation-v1", "condition": condition,
        "dataset_sha256": content_hash([case.model_dump(mode="json") for case in cases]),
        "input_contract_version": "representation-input-v1", "rows": rows,
        "resources": runtime.resources(block_id),
        "interpretation": "Input-contract labels measure retained schema suitability; they do not establish scientific validity or clinical utility."}
