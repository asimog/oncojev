"""Director-only global projection/receipt/policy composition."""
from typing import Any
from uuid import uuid4

from pydantic_ai import RunContext

from src.director.frontier import GlobalFrontierPolicy, PreparedFrontier, beam, current_basis, generate
from src.memory.service import terms
from src.persistence.records import RecordKind, StoredRecord
from src.provenance import canonical_bytes
from src.runtime.pydantic_ai.semantic import measure_async


async def prepare_frontier(runtime, objective, *, limit=10):
    if not 1 <= limit <= 20 or not objective.strip() or len(objective) > 1000:
        raise ValueError("bounded nonempty objective and limit 1..20 required")
    memory = runtime.memory_service()
    if memory is None:
        raise RuntimeError("durable memory required for global frontier")
    memory.backfill()
    basis = current_basis(runtime)
    index = runtime.index_for()
    candidates, omitted = generate(memory.search(objective, mission_id=runtime.mission_id, limit=20), limit=limit)
    measured, relations = [], []
    seen_pairs = set()
    stopped = None
    async def measure(context, identity, payload):
        nonlocal stopped
        from src.runtime.pydantic_ai.contracts import WorkStopped
        if stopped:
            return None, stopped
        try:
            return await measure_async(runtime, None, context, identity, payload, policy=GlobalFrontierPolicy()), None
        except Exception as error:
            if isinstance(error, WorkStopped) or not runtime.enable_jev:
                stopped = type(error).__name__
            return None, type(error).__name__
    for candidate in candidates:
        for ref in candidate.source_refs:
            memory.resolve(ref)
        # Retrieval precedes semantic comparison; at most two neighbours per
        # candidate. No unbounded pair matrix or destructive hypothesis merge.
        neighbours = sorted((c for c in candidates if c.candidate_id != candidate.candidate_id),
                            key=lambda c: -len(terms(candidate.objective) & terms(c.objective)))[:2]
        for other in neighbours:
            pair = tuple(sorted((candidate.candidate_id, other.candidate_id)))
            if pair in seen_pairs or not (terms(candidate.objective) & terms(other.objective)):
                continue
            seen_pairs.add(pair)
            relation = {"relation_id": str(uuid4()), "left": candidate.model_dump(mode="json"),
                        "right": other.model_dump(mode="json"), "basis": basis,
                        "status": "unmeasured", "epistemic_status": "relation_candidate"}
            result, failure = await measure("global_relation", ":".join(pair), relation)
            if result:
                relation.update(status="measured", semantic_call_id=result["call_id"], decisions=result["decisions"])
            else:
                relation["failure_type"] = failure
            runtime.repository.store.append(StoredRecord(kind=RecordKind.GLOBAL_RELATION,
                record_id=relation["relation_id"], payload=relation))
            relations.append(relation)
        cards = index.search(candidate.objective, limit=3)
        payload = {"mission": objective, "candidate": candidate.model_dump(mode="json"),
                   "comparison": [c.model_dump(mode="json") for c in neighbours],
                   "capabilities": [index.card(c).model_dump(mode="json") for c in cards],
                   "block_seconds": runtime.manager.policy.default_seconds if runtime.manager.policy else 900,
                   "relations": [{"relation_id": r["relation_id"], "status": r["status"]} for r in relations[-2:]]}
        result, failure = await measure("global_investigation", candidate.candidate_id, payload)
        if result:
            candidate = candidate.model_copy(update={"status": result["frontier"]["action"], "semantic_call_id": result["call_id"]})
        else:
            candidate = candidate.model_copy(update={"status": "keep_alive", "failure_type": failure})
        measured.append(candidate)
    frontier = PreparedFrontier(frontier_id=str(uuid4()), objective=objective, basis=basis,
                                candidates=tuple(measured), beam=beam(measured), omitted=omitted, relations=tuple(relations))
    runtime.repository.store.append(StoredRecord(kind=RecordKind.GLOBAL_FRONTIER,
        record_id=frontier.frontier_id, payload=frontier.model_dump(mode="json")))
    runtime.retain_export("global_frontier:" + frontier.frontier_id)
    return frontier


def validate_selection(runtime, frontier_id, candidate_id, objective):
    record = next((r for r in reversed(runtime.repository.store.records(kind=RecordKind.GLOBAL_FRONTIER))
                   if r.record_id == frontier_id), None)
    if record is None:
        raise ValueError("unknown prepared frontier")
    frontier = PreparedFrontier.model_validate(record.payload)
    if frontier.basis != current_basis(runtime):
        raise ValueError("prepared frontier stale; reprepare against material changes")
    candidate = next((c for c in frontier.candidates if c.candidate_id == candidate_id), None)
    if candidate is None or candidate_id not in frontier.beam or candidate.objective != objective:
        raise ValueError("selection must name an allowed original frontier question")
    for ref in candidate.source_refs:
        runtime.memory_service().resolve(ref)
    return candidate


def register_global_tools(agent):
    @agent.tool
    async def prepare_global_frontier(ctx: RunContext[Any], objective: str, limit: int = 10) -> dict[str, Any]:
        """Generate and compare referenced questions; retain alternatives and failed semantic fallbacks."""
        frontier = await prepare_frontier(ctx.deps.runtime, objective, limit=limit)
        view = frontier.model_dump(mode="json")
        view["relations"] = [{"relation_id": r["relation_id"], "status": r["status"],
                              "left_id": r["left"]["candidate_id"], "right_id": r["right"]["candidate_id"]}
                             for r in view["relations"]]
        for candidate in view["candidates"]:
            candidate["omitted_refs"] = max(0, len(candidate["source_refs"]) - 2)
            candidate["source_refs"] = candidate["source_refs"][:2]
        while len(canonical_bytes(view)) > 32768 and view["candidates"]:
            removed = view["candidates"].pop()
            view["beam"] = [identity for identity in view["beam"] if identity != removed["candidate_id"]]
            view["omitted"] += 1
        return view

    @agent.tool
    async def propose_engineering(ctx: RunContext[Any], problem: str, reference_seqs: list[int]) -> dict[str, Any]:
        """Record a reference-linked operational proposal, never modify runtime or registry."""
        from src.memory.service import reference
        runtime = ctx.deps.runtime
        if not problem.strip() or len(problem) > 2000 or not 1 <= len(reference_seqs) <= 10:
            raise ValueError("bounded problem and 1..10 real references required")
        records = [runtime.repository.store.record_at(seq) for seq in reference_seqs]
        if any(r is None for r in records):
            raise ValueError("unresolved proposal reference")
        proposal = {"proposal_id": str(uuid4()), "problem": problem,
                    "source_refs": [reference(r).model_dump(mode="json") for r in records],
                    "status": "proposed", "authority": "none"}
        runtime.repository.store.append(StoredRecord(kind=RecordKind.ENGINEERING_PROPOSAL,
                                                     record_id=proposal["proposal_id"], payload=proposal))
        runtime.retain_export("engineering_proposal:" + proposal["proposal_id"])
        return proposal
