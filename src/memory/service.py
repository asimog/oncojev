"""Deterministic memory derivation and bounded retrieval over persisted records."""

import re
from datetime import datetime

from src.memory.models import CycleDigest, MemoryContext, MemoryItem, MemoryReference, StartMemory
from src.persistence.records import RecordKind, StoredRecord
from src.persistence.reconstruct import effective_cycle, reconstruct_block
from src.provenance import canonical_bytes, content_hash


def reference(record: StoredRecord) -> MemoryReference:
    return MemoryReference(kind=record.kind.value, record_id=record.record_id, seq=record.seq,
                           block_id=record.block_id, sha256=content_hash(record.payload))


def terms(text):
    return set(re.findall(r"[\w-]+", text.casefold()))


class ResearchMemory:
    max_results = 20

    def __init__(self, store):
        self.store = store

    def resolve(self, ref: MemoryReference):
        record = self.store.record_at(ref.seq)
        if record is None or record.kind.value != ref.kind or record.record_id != ref.record_id or record.block_id != ref.block_id or content_hash(record.payload) != ref.sha256:
            raise ValueError("unresolved or changed memory reference")
        return record.payload

    def validate(self, digest):
        for ref in digest.references:
            self.resolve(ref)
        for field in (digest.hypotheses, digest.scientific_negative_findings, digest.candidates,
                      digest.operational_blockers, digest.scientific_attempts, digest.literature_contexts, digest.scientific_followups, digest.uncertainties, digest.continuation_proposals, digest.legacy_notes):
            for item in field:
                for ref in item.references:
                    self.resolve(ref)
        if digest.director_note is not None:
            for ref in digest.director_note.references:
                self.resolve(ref)

    def backfill(self):
        """Append derived snapshots; corrections invalidate snapshots, never overwrite them."""
        cycles = list(self.store.records(kind=RecordKind.CYCLE))
        covered = {b for c in cycles for b in c.payload.get("block_ids", ())}
        for block_id in self.store.block_ids():
            block = self.store.latest(RecordKind.BLOCK, block_id=block_id)
            if block and block_id not in covered and block.payload.get("status") in {"complete", "failed", "interrupted"}:
                cycles.append(block)
        saved = {r.record_id for r in self.store.records(kind=RecordKind.MEMORY_DIGEST)}
        for cycle in cycles:
            digest = self._derive(cycle)
            if digest.digest_id not in saved:
                self.validate(digest)
                self.store.append(StoredRecord(kind=RecordKind.MEMORY_DIGEST, record_id=digest.digest_id,
                                              payload=digest.model_dump(mode="json")))
                saved.add(digest.digest_id)
        linked_notes = {ref.seq for d in self.digests() for item in (*d.legacy_notes, *((d.director_note,) if d.director_note else ())) for ref in item.references}
        for note in self.store.records(kind=RecordKind.RESEARCH_MEMORY):
            if note.seq in linked_notes:
                continue
            digest = CycleDigest(digest_id=f"legacy:{note.seq}:{content_hash(note.payload)}", cycle_id=f"legacy:{note.seq}",
                mission_id=note.payload.get("mission_id"), direction="", recorded_at=note.recorded_at,
                cycle_status="unknown", director_outcome="unknown", inferred=True,
                limitations=("Unassociated legacy prose; no outcome, evidence or scientific result can be inferred.",),
                legacy_notes=(MemoryItem(item_id=note.record_id, summary=note.payload.get("summary", ""),
                    epistemic_status="legacy_prose", references=(reference(note),)),))
            if digest.digest_id not in saved:
                self.store.append(StoredRecord(kind=RecordKind.MEMORY_DIGEST, record_id=digest.digest_id, payload=digest.model_dump(mode="json")))

    def _derive(self, cycle):
        orphan = cycle.kind == RecordKind.BLOCK
        payload = {"block_ids": [cycle.block_id], "mission_id": cycle.payload.get("mission_id"),
                   "direction": cycle.payload["start"]["objective"], "status": "incomplete"} if orphan else effective_cycle(self.store, cycle.payload)
        block_ids = tuple(payload.get("block_ids", ()))
        records = [cycle]
        for block_id in block_ids:
            records.extend(r for r in self.store.records(block_id=block_id) if r.kind != RecordKind.MEMORY_DIGEST)
        notes = [r for r in self.store.records(kind=RecordKind.RESEARCH_MEMORY)
                 if r.payload.get("cycle_id") == cycle.record_id or
                 (not r.payload.get("cycle_id") and payload.get("mission_id") and
                  (r.payload.get("mission_id") == payload["mission_id"] or r.record_id.startswith(payload["mission_id"] + ":memory:"))
                  and (orphan or r.seq < cycle.seq))]
        records.extend(notes)
        records = list({r.seq: r for r in records}.values())
        refs = tuple(reference(r) for r in records if r.kind in {RecordKind.CYCLE, RecordKind.BLOCK, RecordKind.DOSSIER,
            RecordKind.MEASUREMENT, RecordKind.EVIDENCE, RecordKind.STATE_REVISION, RecordKind.OUTCOME_CORRECTION, RecordKind.SCIENTIFIC_ATTEMPT, RecordKind.LITERATURE_CONTEXT, RecordKind.FOLLOWUP_PLAN, RecordKind.FOLLOWUP_RESULT})
        priority = {"evidence": 0, "measurement": 1, "dossier": 2, "outcome_correction": 3, "cycle": 4, "block": 5, "state_revision": 6, "scientific_attempt": 2, "literature_context": 2, "followup_plan":2, "followup_result":2}
        refs = tuple(sorted(refs, key=lambda r: (priority[r.kind], -r.seq)))
        fingerprint = content_hash({"derivation":"research-memory-v4-followup-questions-v1", "records": [(r.seq, content_hash(r.payload)) for r in sorted(records, key=lambda r: r.seq)]})
        hypotheses, candidates, blockers, uncertainties, proposals = [], [], [], [], []
        attempts, attempt_unresolved = self._attempt_items(records)
        followups, followup_unresolved = self._followup_items(records)
        contexts = []
        objectives, lifecycle, limitations, unresolved = [], [], [], [*attempt_unresolved,*followup_unresolved]
        usage = {}
        entities, topics = set(), set()
        inferred = orphan or bool(payload.get("outcome_inferred"))
        for block_id in block_ids:
            view = reconstruct_block(self.store, block_id)
            if view.block is None:
                unresolved.append(f"block:{block_id}")
                continue
            objectives.append(view.block["start"]["objective"])
            entities.update(view.block["start"].get("entities", ()))
            topics.update(view.block["start"].get("topics", ()))
            lifecycle.append({"block_id": block_id, "status": view.block["status"], "run_outcome": view.run_outcome.value,
                              "termination_reason": view.block.get("termination_reason"), "inferred": view.outcome_inferred})
            inferred |= view.outcome_inferred
            unresolved.extend(view.unresolved_source_refs)
            for record in (r for r in records if r.block_id == block_id):
                if record.kind == RecordKind.MEASUREMENT:
                    limitations.extend(record.payload.get("limitations", ()))
                    if record.payload.get("origin") in {"provided", "synthetic"}:
                        limitations.append(f"{record.record_id}: exploratory {record.payload['origin']} input; not admitted evidence.")
                if record.kind == RecordKind.LITERATURE_CONTEXT:
                    from src.memory.literature import LiteratureContext
                    context = LiteratureContext.model_validate(record.payload)
                    missing = []
                    for ref in context.basis:
                        try: self.resolve(ref)
                        except ValueError: missing.append(f"{ref.kind}:{ref.record_id}:{ref.seq}")
                    unresolved.extend(missing)
                    category = "unknown" if missing else context.category
                    attempt_ref = next((ref for ref in context.basis if ref.kind == RecordKind.SCIENTIFIC_ATTEMPT), None)
                    contract = self.resolve(attempt_ref).get("analysis", {}) if attempt_ref and not missing else {}
                    contexts.append(MemoryItem(item_id=context.assessment_id,
                        summary=f"Tentative {category}: {context.claim}", epistemic_status="tentative_literature_context",
                        references=(reference(record), *(ref for ref in context.basis if f"{ref.kind}:{ref.record_id}:{ref.seq}" not in missing)),
                        details={"category": category, "claim": context.claim, "semantic_status": context.semantic_status,
                                 "population": contract.get("population"), "design": contract.get("design"), "method": contract.get("method"),
                                 "unresolved": (*context.unresolved, *missing), "limitations": context.limitations}))
                if record.kind == RecordKind.STATE_REVISION and record == self.store.latest(RecordKind.STATE_REVISION, block_id=block_id):
                    for fragment in record.payload.get("uncertainties", ()):
                        uncertainties.append(MemoryItem(item_id=fragment["fragment_id"], summary=fragment["summary"],
                            epistemic_status="uncertainty", references=(reference(record),)))
                    # Only explicitly labelled entities/topics support exact filters.
                    for fragment in (*record.payload.get("candidates", ()), *record.payload.get("observations", ())):
                        entities.update(str(e) for e in fragment.get("details", {}).get("entities", ()))
                        topics.update(str(e) for e in fragment.get("details", {}).get("topics", ()))
                if record.kind != RecordKind.LEDGER_EVENT:
                    continue
                event = record.payload
                data = event["payload"]
                kind = event["event_type"]
                ref = (reference(record),)
                if kind == "ReasonerOutput":
                    for i, h in enumerate(data.get("hypotheses", ())):
                        hypotheses.append(MemoryItem(item_id=f"{record.record_id}:{i}", summary=h["statement"],
                            epistemic_status="hypothesis", references=ref, details=h))
                        if h.get("proposed_test"):
                            proposals.append(MemoryItem(item_id=f"{record.record_id}:test:{i}", summary=h["proposed_test"],
                                epistemic_status="proposal", references=ref))
                    if data.get("uncertainty"):
                        uncertainties.append(MemoryItem(item_id=record.record_id, summary=data["uncertainty"], epistemic_status="uncertainty", references=ref))
                if kind == "FrontierDecision":
                    candidates.append(MemoryItem(item_id=data.get("candidate_id", record.record_id),
                        summary=data.get("candidate_summary", data.get("candidate_id", "semantic candidate")),
                        epistemic_status="semantic_history", references=ref, details=data))
                if kind in {"CapabilityFailure", "ResearcherRunFailed", "DirectorRunFailed", "DirectorRunTruncated", "InterruptedBlockRecovered", "CycleFinalizationFailed"}:
                    blockers.append(MemoryItem(item_id=record.record_id, summary=f"{kind}: {data.get('capability_id', '')} {data.get('error_type', data.get('reason', 'unknown'))}".strip(),
                                              epistemic_status="operational_failure", references=ref, details=data))
                if kind == "ScopeEscalationRequested" and data.get("proposed_test"):
                    proposals.append(MemoryItem(item_id=record.record_id, summary=data["proposed_test"], epistemic_status="proposal", references=ref))
                if kind == "ModelUsage":
                    usage[block_id] = dict(data)
            if view.dossier:
                usage.setdefault(block_id, {})["recorded_resources"] = view.dossier.get("resource_usage", {})
                evidence = {r.record_id for r in records if r.kind == RecordKind.EVIDENCE and r.block_id == block_id}
                unresolved.extend(f"evidence:{e}" for e in view.dossier.get("evidence_refs", ()) if e not in evidence)
        if payload.get("error_type") and not blockers:
            blockers.append(MemoryItem(item_id=cycle.record_id, summary=payload["error_type"], epistemic_status="operational_failure", references=(reference(cycle),)))
        if inferred:
            limitations.append("Historical outcome is inferred or corrected; closure does not establish scientific success.")
        limitations.append("Scientific negatives are not inferred from semantic rejection, missing evidence or provider failure.")
        legacy = tuple(MemoryItem(item_id=r.record_id, summary=r.payload.get("summary", ""), epistemic_status="legacy_prose", references=(reference(r),)) for r in notes if not r.payload.get("cycle_id"))
        current_note = next((MemoryItem(item_id=r.record_id, summary=r.payload.get("summary", ""), epistemic_status="director_note", references=(reference(r),))
                             for r in reversed(notes) if r.payload.get("cycle_id") == cycle.record_id), None)
        return CycleDigest(digest_id=f"{cycle.record_id}:{fingerprint}", cycle_id=cycle.record_id, mission_id=payload.get("mission_id"),
            direction=payload.get("direction", ""), recorded_at=cycle.recorded_at, cycle_status=payload.get("status", "incomplete"),
            director_outcome=payload.get("director_outcome", "unknown"), failure_reason=payload.get("error_type"), block_ids=block_ids,
            objectives=tuple(objectives), lifecycle=tuple(lifecycle), references=refs, limitations=tuple(dict.fromkeys(limitations)),
            unresolved_references=tuple(sorted(set(unresolved))), hypotheses=tuple(hypotheses), candidates=tuple(candidates),
            operational_blockers=tuple(blockers), scientific_attempts=attempts, literature_contexts=tuple(contexts), scientific_followups=followups, uncertainties=tuple(uncertainties), continuation_proposals=tuple(proposals),
            resource_usage=usage, entities=tuple(sorted(entities)), topics=tuple(sorted(topics)), inferred=inferred, legacy_notes=legacy, director_note=current_note)

    def _followup_items(self, records):
        from src.science.followup import FollowupPlan, FollowupResult
        items, unresolved = [], []
        for stored in records:
            if stored.kind != RecordKind.FOLLOWUP_PLAN: continue
            plan=FollowupPlan.model_validate(stored.payload)
            terminal=next((r for r in reversed(records) if r.kind==RecordKind.FOLLOWUP_RESULT and r.record_id==plan.followup_id and r.block_id==plan.block_id),None)
            result=FollowupResult.model_validate(terminal.payload) if terminal else None
            if result and result.baseline_measurement!=plan.baseline_measurement:
                raise ValueError("follow-up result changed its original baseline")
            refs=[reference(stored),*((reference(terminal),) if terminal else ())]
            missing=[]
            for ref in (plan.baseline_measurement,plan.baseline_input,*((result.target_measurement,result.target_input) if result else ())):
                if ref is None: continue
                target=next((r for r in reversed(self.store.records(kind=RecordKind(ref.kind),block_id=ref.block_id))
                    if r.record_id==ref.value and content_hash(r.payload)==ref.sha256),None)
                if target: refs.append(reference(target))
                else: missing.append(f"{plan.followup_id}:{ref.kind}:{ref.value}")
            unresolved.extend(missing)
            outcome="unknown" if missing else result.outcome if result else "attempted"
            details={"outcome":outcome,"stage":result.stage if result else "declared", "kind":plan.kind,
                "question":plan.target_analysis.question,
                "population":plan.target_analysis.population,"design":plan.target_analysis.design,"method":plan.target_analysis.method,
                "independence":result.independence if result else "unknown", "overlap_count":result.overlap_count if result else None,
                "confirmation_access":result.confirmation_access if result else "unknown",
                "intervals":result.intervals if result else {}, "unresolved":(*missing,*(result.unresolved if result else ("Declared comparison has no terminal result.",))),
                "expected_discrimination":plan.expected_discrimination,"alternative_explanations":plan.alternative_explanations,
                "limitations":result.limitations if result else plan.limitations}
            items.append(MemoryItem(item_id=plan.followup_id,summary=f"{outcome} (model-conditional retained-query comparison): {plan.kind}; {plan.target_analysis.question}; independence={details['independence']}; confirmation_access={details['confirmation_access']}",
                epistemic_status="scientific_followup",references=tuple(refs),details=details))
        return tuple(items),tuple(unresolved)

    def _attempt_items(self, records):
        from src.science.models import ScientificAttempt
        latest = {}
        for record in records:
            if record.kind == RecordKind.SCIENTIFIC_ATTEMPT:
                value = ScientificAttempt.model_validate(record.payload)
                latest[value.attempt_id] = (record, value)
        items, unresolved = [], []
        for stored, attempt in latest.values():
            refs = [reference(stored)]
            measurement = None
            for ref in (attempt.input_reference, attempt.measurement_reference):
                if ref is None:
                    continue
                target = next((r for r in reversed(records) if r.kind.value == ref.kind and
                    r.record_id == ref.value and r.block_id == ref.block_id and content_hash(r.payload) == ref.sha256), None)
                if target:
                    refs.append(reference(target))
                    if ref.kind == "measurement":
                        measurement = target
                else:
                    unresolved.append(f"{attempt.attempt_id}:{ref.kind}:{ref.value}")
            if attempt.hypothesis_record_seq:
                hypothesis = self.store.record_at(attempt.hypothesis_record_seq)
                if hypothesis is None or hypothesis.kind != RecordKind.STATE_REVISION or not any(
                    f.get("kind") == "hypothesis" and f.get("fragment_id") == attempt.analysis.test_plan.hypothesis_id
                    for f in hypothesis.payload.get("candidates", ())):
                    unresolved.append(f"{attempt.attempt_id}:hypothesis:{attempt.hypothesis_record_seq}")
                else:
                    refs.append(reference(hypothesis))
            test = measurement.payload.get("diagnostics", {}).get("hypothesis_test", {}) if measurement else {}
            expected = test.get("outcome", "unknown") if attempt.stage == "completed" else attempt.outcome
            if attempt.stage == "completed" and measurement and attempt.outcome != expected:
                raise ValueError("scientific attempt outcome contradicts its originating measurement")
            outcome = "unknown" if any(u.startswith(attempt.attempt_id + ":") for u in unresolved) else expected
            evidence = [r for r in records if r.kind == RecordKind.EVIDENCE and measurement and
                        r.block_id == attempt.block_id and r.payload.get("measurement") == measurement.payload]
            refs.extend(reference(r) for r in evidence)
            spec = attempt.analysis
            qualifier = " (model-conditional exploratory association)" if test else ""
            summary = f"{outcome}{qualifier}: {spec.question}; {spec.method}; population={spec.population}; stage={attempt.stage}"
            details = {"attempt_id": attempt.attempt_id, "analysis_id":spec.analysis_id,
                "capability_id":attempt.capability_id, "stage":attempt.stage, "outcome":outcome,
                "population":spec.population, "design":spec.design, "method":spec.method,
                "hypothesis_id":spec.test_plan.hypothesis_id if spec.test_plan else None,
                "contract":spec.model_dump(mode="json"), "failure_type":attempt.failure_type,
                "measurement_values": measurement.payload.get("values", {}) if measurement else {},
                "measurement_origin":measurement.payload.get("origin") if measurement else None,
                "hypothesis_test":test, "evidence_ids":[r.record_id for r in evidence],
                "limitations":attempt.limitations}
            items.append(MemoryItem(item_id=attempt.attempt_id, summary=summary, epistemic_status="scientific_attempt",
                                    references=tuple(refs), details=details))
        # Bound context without letting repeated supported results hide the
        # unfinished/invalid work that determines a useful next investigation.
        priority = {"invalid":0, "inconclusive":1, "attempted":2, "unknown":3, "contradicted":4, "supported":5}
        items.sort(key=lambda item: (priority[item.details["outcome"]], item.item_id))
        return tuple(items), tuple(unresolved)

    @staticmethod
    def _compact_attempt(details):
        contract = details.get("contract", {})
        return {"stage":details.get("stage"), "outcome":details.get("outcome"),
                "capability_id":details.get("capability_id"), "failure_type":details.get("failure_type"),
                "population":str(contract.get("population", ""))[:500], "estimand":str(contract.get("estimand", ""))[:500],
                "method":contract.get("method"), "entity_unit":contract.get("entity_unit"),
                "design":str(contract.get("design", ""))[:500],
                "fields":{str(k)[:100]:str(v)[:100] for k,v in list(contract.get("fields", {}).items())[:8]},
                "transformations":{str(k)[:100]:str(v)[:100] for k,v in list(contract.get("transformations", {}).items())[:8]},
                "test":{k:v for k,v in (contract.get("test_plan") or {}).items()
                    if k in {"hypothesis_id", "direction", "minimum_effect", "alpha", "interpretation"}},
                "family_size":len((contract.get("test_plan") or {}).get("multiplicity_family", ())),
                "meaning":str(details.get("hypothesis_test", {}).get("meaning", "No scientific test interpretation established."))[:500],
                "origin":details.get("measurement_origin"),
                "effect_uncertainty":{k:v for k,v in details.get("measurement_values", {}).items()
                    if k in {"correlation","slope","effect_ci_low","effect_ci_high","p_value_adjusted","alpha_per_test"}}}

    def digests(self):
        latest = {}
        for record in self.store.records(kind=RecordKind.MEMORY_DIGEST):
            digest = CycleDigest.model_validate(record.payload)
            latest[digest.cycle_id] = digest
        for digest in latest.values():
            self.validate(digest)
        return tuple(latest.values())

    def search(self, query="", *, mission_id=None, entity=None, topic=None, since: datetime | None = None,
               until: datetime | None = None, limit=10, capability=None, hypothesis=None,
               shared_reference=None, lineage=None, alternative_limit=3):
        if not 1 <= limit <= self.max_results:
            raise ValueError("memory search limit must be between 1 and 20")
        if not 0 <= alternative_limit <= 3:
            raise ValueError("alternative limit must be 0..3")
        ranked, alternatives = [], []
        for d in self.digests():
            if mission_id is not None and d.mission_id != mission_id or entity is not None and entity not in d.entities or topic is not None and topic not in d.topics:
                continue
            if since is not None and d.recorded_at < since or until is not None and d.recorded_at > until:
                continue
            items = (*d.hypotheses, *d.candidates, *d.scientific_attempts, *d.literature_contexts, *d.scientific_followups, *d.operational_blockers, *d.uncertainties, *d.continuation_proposals)
            refs = (*d.references, *(r for item in items for r in item.references))
            if shared_reference is not None and not any(r.record_id == shared_reference for r in refs):
                continue
            if lineage is not None and lineage not in (*d.block_ids, d.cycle_id, *(r.block_id for r in refs)):
                continue
            if capability is not None and not any(capability in (i.details.get('capability_id'), *i.details.get('capability_ids', ())) for i in items):
                continue
            if hypothesis is not None and not any(hypothesis == i.item_id or terms(hypothesis) <= terms(i.summary) for i in d.hypotheses):
                continue
            # Legacy Director prose never supplies relevance or facts.
            text = " ".join((d.direction, *d.objectives, *d.entities, *d.topics,
                             *(i.summary for field in (d.hypotheses, d.candidates, d.scientific_attempts, d.literature_contexts, d.scientific_followups, d.operational_blockers, d.uncertainties, d.continuation_proposals) for i in field)))
            score = len(terms(query) & terms(text))
            if query and score == 0:
                # Empty/operational-only cycles provide no scientific alternative.
                # Keep failed attempts and unresolved scientific context, not an
                # unrelated no-allocation event merely because it has a receipt.
                scientific_items = (*d.hypotheses, *d.candidates, *d.scientific_attempts,
                    *d.literature_contexts, *d.scientific_followups, *d.uncertainties, *d.continuation_proposals)
                if scientific_items:
                    alternatives.append(d)
                continue
            ranked.append((score, d))
        ranked.sort(key=lambda pair: (-pair[0], pair[1].cycle_id, pair[1].digest_id))
        alternatives.sort(key=lambda d: (-d.recorded_at.timestamp(), d.cycle_id, d.digest_id))
        reserve = min(alternative_limit, len(alternatives), limit // 4 if ranked else limit) if query else 0
        selected = [d for _, d in ranked[:max(0, limit - reserve)]]
        selected.extend(alternatives[:min(reserve, limit - len(selected))])
        if len(selected) < limit:
            selected.extend(d for _, d in ranked if d not in selected)
        return tuple(selected[:limit])

    def context(self, query, *, limit=5, **filters):
        digests = self.search(query, limit=limit, **filters)
        views = []
        for digest in digests:
            view = digest.model_dump(mode="json")
            truncated = {"direction": len(view["direction"]) > 1000,
                         "objectives": sum(len(s) > 1000 for s in view["objectives"][:20])}
            view["direction"] = view["direction"][:1000]
            view["objectives"] = [s[:1000] for s in view["objectives"][:20]]
            view["legacy_notes"] = []  # available only through explicit reference lookup
            view["director_note"] = None  # optional prose is not canonical retrieved context
            view["legacy_note_count"] = len(digest.legacy_notes)
            view["director_note_available"] = digest.director_note is not None
            view["resource_usage"] = {b: {"recorded_resources": v.get("recorded_resources", {})} for b, v in list(digest.resource_usage.items())[:20]}
            omitted = {}
            for key in ("references", "hypotheses", "scientific_negative_findings", "scientific_attempts", "literature_contexts", "scientific_followups", "candidates", "operational_blockers", "uncertainties", "continuation_proposals", "limitations", "unresolved_references", "entities", "topics", "lifecycle"):
                omitted[key] = max(0, len(view[key]) - 20)
                view[key] = view[key][:20]
                truncated[key] = sum(len(i if isinstance(i, str) else i.get("summary", "")) > 1000 for i in view[key])
                for index, item in enumerate(view[key]):
                    if isinstance(item, str):
                        view[key][index] = item[:1000]
                    elif "summary" in item:
                        item["summary"] = item["summary"][:1000]
                        item["details"] = (self._compact_attempt(item["details"]) if key == "scientific_attempts" else
                                           {k: item["details"][k] for k in ("category", "semantic_status", "unresolved", "limitations")}
                                           if key == "literature_contexts" else
                                           {k:item["details"].get(k) for k in ("outcome","kind","independence","confirmation_access","overlap_count","intervals","unresolved","limitations")}
                                           if key == "scientific_followups" else {})
                        # Native distributions/full contracts stay reference-resolvable.
                        item["references"] = item["references"][:2]
            view["omitted_items"] = omitted
            view["truncated_text"] = truncated
            # Preserve a compact representative of each category before dropping
            # whole digests, so a large history cannot hide its failure reason.
            while len(canonical_bytes(view)) > 12288:
                fields = [k for k in omitted if len(view[k]) > 1]
                if not fields:
                    break
                key = max(fields, key=lambda k: len(canonical_bytes(view[k])))
                view[key].pop()
                omitted[key] += 1
            views.append(view)
        alternatives = [d.digest_id for d in digests if query and not terms(query) & terms(" ".join((d.direction, *d.objectives,
            *d.entities, *d.topics, *(i.summary for field in (d.hypotheses, d.candidates, d.scientific_attempts,
            d.literature_contexts, d.scientific_followups, d.operational_blockers, d.uncertainties, d.continuation_proposals) for i in field))))]
        context = MemoryContext(query=query[:1000], digests=tuple(views), retrieval={
            "version": "memory-retrieval-v3-bounded-alternatives", "alternative_digest_ids": alternatives,
            "alternative_limit": filters.get("alternative_limit", 3), "result_limit": limit,
            "basis": "lexical matches plus bounded recent filtered alternatives; relevance unmeasured"})
        while len(canonical_bytes(context.model_dump(mode="json"))) > context.max_bytes and context.digests:
            context = context.model_copy(update={"digests": context.digests[:-1], "omitted_digests": context.omitted_digests + 1})
        return context

    def start_context(self, objective, context=None):
        context = context or self.context(objective, limit=5).model_dump(mode="json")
        views = context["digests"]
        refs = tuple(MemoryReference.model_validate(r) for d in views for r in d["references"])
        refs = tuple({r.seq: r for r in refs}.values())[:20]
        for ref in refs:
            self.resolve(ref)
        start = StartMemory(digest_ids=tuple(d["digest_id"] for d in views), references=refs,
            prior_failures=tuple(i["summary"] for d in views for i in d["operational_blockers"])[:20],
            prior_attempts=tuple(i["summary"] for d in views for i in d.get("scientific_attempts", ()))[:20],
            prior_contexts=tuple(i["summary"] for d in views for i in d.get("literature_contexts", ()))[:20],
            prior_followups=tuple(i["summary"] for d in views for i in d.get("scientific_followups", ()))[:20],
            uncertainties=tuple(i["summary"] for d in views for i in d["uncertainties"])[:20],
            candidate_directions=tuple(i["summary"] for d in views for i in (*d["candidates"], *d["continuation_proposals"]))[:20],
            limitations=tuple(dict.fromkeys(s for d in views for s in d["limitations"]))[:20], omitted_digests=context["omitted_digests"])
        while len(canonical_bytes(start.model_dump(mode="json"))) > 16384:
            field = max(("prior_failures", "prior_attempts", "prior_contexts", "prior_followups", "uncertainties", "candidate_directions", "limitations", "references"),
                        key=lambda f: len(canonical_bytes(getattr(start, f) if f != "references" else [r.model_dump(mode="json") for r in start.references])))
            start = start.model_copy(update={field: getattr(start, field)[:-1], "omitted_items": start.omitted_items + 1})
        return start

    def get_dossier(self, block_id):
        view = reconstruct_block(self.store, block_id)
        return view.dossier

    def get_evidence(self, evidence_id, block_id):
        record = next((r for r in self.store.records(kind=RecordKind.EVIDENCE, block_id=block_id) if r.record_id == evidence_id), None)
        return {"reference": reference(record).model_dump(mode="json"), "evidence": record.payload} if record else None

    def items(self, field, query="", **filters):
        return tuple({"digest_id": d.digest_id, **i.model_dump(mode="json")} for d in self.search(query, **filters) for i in getattr(d, field))[:20]
