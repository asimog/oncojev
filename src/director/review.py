"""Bounded observation of portfolio lifecycle and recorded program resources."""
import math
from src.memory.service import reference
from src.persistence.records import RecordKind, StoredRecord
from src.provenance import canonical_bytes, content_hash


def _snapshot(runtime,limit):
    if not 1<=limit<=20: raise ValueError("review limit must be 1..20")
    if runtime.repository is None: raise ValueError("program review requires durable records")
    store=runtime.repository.store
    with store.transaction():
        ceiling=store.high_water()
        kinds=(RecordKind.GLOBAL_FRONTIER,RecordKind.BLOCK,RecordKind.BLOCK_DELTA,RecordKind.LEDGER_EVENT)
        records=tuple(sorted((r for kind in kinds for r in store.records(kind=kind) if r.seq<=ceiling),key=lambda r:r.seq))
    return store,ceiling,records


def _portfolio(runtime,limit,ceiling,records):
    latest={}; legacy=0; frontier_refs={}
    for record in records:
        if record.kind!=RecordKind.GLOBAL_FRONTIER: continue
        if "mission_id" not in record.payload:
            legacy+=1; continue  # Historical scope is unknown, never relabelled.
        if record.payload["mission_id"]!=runtime.mission_id: continue
        for candidate in record.payload.get("candidates",()):
            latest[candidate["candidate_id"]]=(candidate,record)
            frontier_refs[candidate["candidate_id"]]=reference(record).model_dump(mode="json")
    allocations={}; blocks={}
    for record in records:
        if record.kind==RecordKind.BLOCK and "mission_id" in record.payload and record.payload["mission_id"]==runtime.mission_id: blocks[record.block_id]=record
        if record.kind==RecordKind.LEDGER_EVENT and record.payload.get("event_type")=="DirectorBlockAllocated":
            data=record.payload["payload"]
            if "mission_id" in data and data["mission_id"]==runtime.mission_id and data.get("candidate_id"):
                allocations[data["candidate_id"]]=record
    nodes=[]
    for identity,(candidate,record) in sorted(latest.items(),key=lambda item:(-item[1][1].seq,item[0]))[:limit]:
        allocation=allocations.get(identity); block=blocks.get(allocation.block_id) if allocation else None
        lifecycle=block.payload.get("status","unknown") if block else "allocation_unresolved" if allocation else "deferred" if candidate.get("status")=="defer" else "proposed"
        nodes.append({"candidate_id":identity,"objective":candidate["objective"],"origin":candidate["origin"],
            "semantic_status":candidate.get("status","pending"),"observed_lifecycle":lifecycle,
            "objective_attainment":"unknown","scientific_resolution":"unknown",
            "semantic_call_id":candidate.get("semantic_call_id"),"failure_type":candidate.get("failure_type"),
            "source_refs":candidate["source_refs"][:2],"omitted_refs":max(0,len(candidate["source_refs"])-2),
            "frontier_ref":frontier_refs[identity],"allocation_ref":reference(allocation).model_dump(mode="json") if allocation else None,
            "block_ref":reference(block).model_dump(mode="json") if block else None})
    view={"version":"program-portfolio-v1","mission_id":runtime.mission_id,"high_water":ceiling,"candidates":nodes,
        "omitted_candidates":max(0,len(latest)-len(nodes)),"unscoped_legacy_frontiers":legacy,
        "limitations":["Observed block lifecycle and semantic status are separate; neither establishes scientific resolution.",
                       "Historical frontiers without mission identity remain unscoped.",
                       "Relations/native judgments and original references remain in the referenced immutable frontier."]}
    while len(canonical_bytes(view))>32768 and nodes:
        nodes.pop();view["omitted_candidates"]+=1
    return view


def portfolio(runtime,*,limit=20):
    _,ceiling,records=_snapshot(runtime,limit)
    return _portfolio(runtime,limit,ceiling,records)


def review_program(runtime,*,limit=20):
    store,ceiling,records=_snapshot(runtime,limit)
    blocks={}; deltas={}; failures={}
    for record in records:
        if record.kind==RecordKind.BLOCK and "mission_id" in record.payload and record.payload["mission_id"]==runtime.mission_id: blocks[record.block_id]=record
        if record.kind==RecordKind.BLOCK_DELTA: deltas[record.block_id]=record
    selected=sorted(blocks.values(),key=lambda r:-r.seq)[:limit]
    selected_ids={r.block_id for r in selected}; resources=[]; refs=[]; tags={"entities":{},"topics":{}}
    for record in selected:
        refs.append(reference(record).model_dump(mode="json"))
        delta=deltas.get(record.block_id)
        if delta:
            refs.append(reference(delta).model_dump(mode="json")); data=delta.payload.get("resources",{})
        else: data={}
        resources.append({"block_id":record.block_id,"block_ref":reference(record).model_dump(mode="json"),
            "allocated_seconds":record.payload.get("start",{}).get("allocation",{}).get("seconds"),
            **{key:data.get(key) for key in ("actual_elapsed_seconds","unused_allowance_seconds","researcher_active_seconds",
                "director_turn_seconds","director_idle_wait_seconds","downloaded_bytes","scientific_executions",
                "heavy_lease_acquisitions","resource_limit_failures","workspace_peak_bytes","cpu_seconds")}})
        for field in tags:
            for tag in set(record.payload.get("start",{}).get(field,())):
                label=tag if len(tag)<=200 else tag[:180]+":"+content_hash(tag)[:16]
                tags[field][label]=tags[field].get(label,0)+1
    for record in records:
        if record.block_id not in selected_ids or record.kind!=RecordKind.LEDGER_EVENT: continue
        if record.payload.get("event_type") not in {"CapabilityFailure","ResourceRejected","WorkNotStarted"}: continue
        data=record.payload["payload"]; key=(record.payload["event_type"],str(data.get("capability_id",data.get("resource","unknown")))[:200])
        value=failures.setdefault(key,{"event_type":key[0],"capability_or_resource":key[1],"count":0,"source_refs":[]})
        value["count"]+=1
        if len(value["source_refs"])<2: value["source_refs"].append(reference(record).model_dump(mode="json"))
    totals={}
    for key in resources[0] if resources else ():
        if key in {"block_id","block_ref"}: continue
        values=[r[key] for r in resources if isinstance(r[key],(int,float)) and not isinstance(r[key],bool) and math.isfinite(r[key])]
        totals[key]={"recorded_sum":sum(values) if values else None,"observed_blocks":len(values),"missing_blocks":len(resources)-len(values)}
    longest=sorted((r for r in resources if isinstance(r["actual_elapsed_seconds"],(int,float))),key=lambda r:-r["actual_elapsed_seconds"])[:3]
    view={"version":"program-review-v1","mission_id":runtime.mission_id,"high_water":ceiling,
        "selected_blocks":len(selected),"omitted_blocks":max(0,len(blocks)-len(selected)),"window":"most recent retained blocks",
        "resources":totals,"declared_concentration":{key:dict(sorted(values.items(),key=lambda item:(-item[1],item[0]))[:20]) for key,values in tags.items()},
        "omitted_concentration_labels":{key:max(0,len(values)-20) for key,values in tags.items()},
        "longest_recorded_blocks":longest,"failures":list(failures.values())[:10],"omitted_failure_groups":max(0,len(failures)-10),
        "source_refs":refs,"omitted_source_refs":0,"omitted_longest_blocks":0,"portfolio":_portfolio(runtime,limit,ceiling,records),
        "scientific_value":"unknown","deadline_action":"none",
        "limitations":["Durations are recorded wall time, not measured CPU use.","Missing metrics stay unknown; sums cover only the selected observed blocks.",
            "Concentration uses declared entity/topic tags, not inferred modality coverage or scientific diversity.",
            "Expensive blocks, early completion and failure counts do not establish scientific value or authorize deadline changes."]}
    # The portfolio remains separately queryable when the combined review is large.
    while len(canonical_bytes(view))>32768 and view["portfolio"]["candidates"]:
        view["portfolio"]["candidates"].pop();view["portfolio"]["omitted_candidates"]+=1
    while len(canonical_bytes(view))>32768:
        labels=[key for key in tags if view["declared_concentration"][key]]
        if labels:
            key=max(labels,key=lambda key:len(canonical_bytes(view["declared_concentration"][key])))
            view["declared_concentration"][key].pop(next(reversed(view["declared_concentration"][key])))
            view["omitted_concentration_labels"][key]+=1
        elif view["failures"]:
            view["failures"].pop();view["omitted_failure_groups"]+=1
        elif view["longest_recorded_blocks"]:
            view["longest_recorded_blocks"].pop();view["omitted_longest_blocks"]+=1
        elif view["source_refs"]:
            view["source_refs"].pop();view["omitted_source_refs"]+=1
        else: raise ValueError("mandatory program review exceeds byte bound")
    identity=content_hash({k:v for k,v in view.items() if k!="high_water" and k!="portfolio"} | {"portfolio":{k:v for k,v in view["portfolio"].items() if k!="high_water"}})
    existing=next((r for r in store.records(kind=RecordKind.PROGRAM_REVIEW) if r.record_id==identity),None)
    if existing: return existing.payload
    view["review_id"]=identity
    store.append(StoredRecord(kind=RecordKind.PROGRAM_REVIEW,record_id=identity,payload=view))
    runtime.retain_export("program_review:"+identity)
    return view
