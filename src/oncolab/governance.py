"""Deterministic source-linked reviews. Agents propose; Python accepts scoped state."""
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from src.memory.models import MemoryReference
from src.memory.service import ResearchMemory
from src.oncolab.execution import ExecutionRoute
from src.oncolab.institution import InstitutionalObservation
from src.oncolab.models import OncoLabDescriptor, OncoLabValidationState, OncoLabAvailability
from src.persistence.records import RecordKind, StoredRecord
from src.provenance import content_hash
from src.runtime.verification import local_verification_passed
from src.science.qualification import scientific_qualification_resolves
from src.evals.reference import utility_evaluation_resolves


class CapabilityProposal(BaseModel, frozen=True):
    proposal_id: str = Field(default_factory=lambda: str(uuid4()))
    capability_id: str
    transition: Literal['promotion','update','retirement','reverification']
    parent: str
    descriptor: OncoLabDescriptor
    routes: tuple[ExecutionRoute, ...]
    scope: dict
    references: tuple[MemoryReference,...] = Field(min_length=1,max_length=30)
    requires_code_change: bool = False
    rationale: str = Field(min_length=1,max_length=2000)


def propose(institution, proposal):
    if proposal.capability_id!=proposal.descriptor.capability_id:raise ValueError('proposal capability identity mismatch')
    memory=ResearchMemory(institution.store)
    for ref in proposal.references:memory.resolve(ref)
    if proposal.parent!=institution.pin().oncolab_registry_revision:raise ValueError('stale proposal parent')
    saved=institution.store.append(StoredRecord(kind=RecordKind.CAPABILITY_PROPOSAL,record_id=proposal.proposal_id,
        payload=proposal.model_dump(mode='json')))
    institution.observe(InstitutionalObservation(observation_id='proposal:'+proposal.proposal_id,
        capability_id=proposal.capability_id,kind='proposal',source_seq=saved.seq,
        payload={'transition':proposal.transition,'scope':proposal.scope},provenance='proposed; no registry authority'))
    return saved


def review(institution, proposal_id):
    """Qualification records must match exact candidate, scope and current application."""
    with institution.store.transaction():
        saved=next((r for r in institution.store.records(kind=RecordKind.CAPABILITY_PROPOSAL) if r.record_id==proposal_id),None)
        if saved is None:raise ValueError('unknown capability proposal')
        proposal=CapabilityProposal.model_validate(saved.payload)
        memory=ResearchMemory(institution.store)
        linked=[]
        for ref in proposal.references:
            memory.resolve(ref)
            linked.append(institution.store.record_at(ref.seq))
        reasons=[]
        parent=institution.pin().oncolab_registry_revision
        scope_hash=content_hash(proposal.scope)
        if proposal.parent!=parent:reasons.append('stale_registry_basis')
        if proposal.requires_code_change:reasons.append('requires_reviewed_engineering')
        if not proposal.scope:reasons.append('missing_scientific_scope')
        if proposal.transition in {'promotion','update'}:
            kinds={r.kind for r in linked}
            required={RecordKind.SANDBOX_CANDIDATE,RecordKind.MEASUREMENT,RecordKind.EVIDENCE,
                RecordKind.REFERENCE_VALIDATION,RecordKind.ENVIRONMENT_QUALIFICATION,
                RecordKind.UTILITY_EVALUATION,RecordKind.LOCAL_VERIFICATION}
            reasons.extend('missing:'+kind.value for kind in sorted(required-kinds,key=str))
            candidates=[r for r in linked if r.kind==RecordKind.SANDBOX_CANDIDATE]
            candidate_ids={r.record_id for r in candidates}
            if not candidate_ids:reasons.append('missing_qualified_operation')
            operations={content_hash({'repository':r.payload.get('receipt',{}).get('repository_url'),
                'commit':r.payload.get('receipt',{}).get('commit_sha'),
                'commands':{k:r.payload.get('request',{}).get(k) for k in ('install_command','test_command','execute_command')}}) for r in candidates}
            if len(operations)!=1:reasons.append('conflicting_operation_identity')
            for kind in (RecordKind.REFERENCE_VALIDATION,RecordKind.ENVIRONMENT_QUALIFICATION,RecordKind.UTILITY_EVALUATION):
                proofs=[r for r in linked if r.kind==kind]
                if proofs and not any(r.payload.get('status')=='passed' and r.payload.get('candidate_id') in candidate_ids
                    and r.payload.get('scope_sha256')==scope_hash
                    and (utility_evaluation_resolves(institution.store, r.payload, institution.application) if kind==RecordKind.UTILITY_EVALUATION
                         else scientific_qualification_resolves(institution.store, kind, r.payload)) for r in proofs):
                    reasons.append('failed_or_changed_scope:'+kind.value)
            references=[r for r in linked if r.kind==RecordKind.REFERENCE_VALIDATION]
            if references and not any(all(r.payload.get(key) is True for key in
                ('canonical_reference_matched','changed_input_correct','invalid_input_rejected','scientific_scope_valid')) for r in references):
                reasons.append('incomplete_reference_or_scientific_adverse_case_proof')
            qualifications=[r for r in linked if r.kind==RecordKind.ENVIRONMENT_QUALIFICATION]
            if qualifications and not any(r.payload.get('fresh_environment') is True and r.payload.get('recoverable_lock') is True
                and r.payload.get('independent_replay') is True for r in qualifications):
                reasons.append('missing_fresh_locked_reinstall_replay')
            local=[r for r in linked if r.kind==RecordKind.LOCAL_VERIFICATION]
            if local and not any(local_verification_passed(r.payload, institution.application, environment_provider=institution.environment_provider, store=institution.store) for r in local):
                reasons.append('local_execution_not_verified_for_application')
            if not proposal.descriptor.version or any(r.payload.get('receipt',{}).get('commit_sha')!=proposal.descriptor.version for r in candidates):reasons.append('missing_or_conflicting_immutable_operation_version')
            if not proposal.routes or any(r.tool!='run_reusable_method' or r.candidate_id not in candidate_ids or r.scope_sha256!=scope_hash for r in proposal.routes):
                reasons.append('unsupported_declarative_execution_route')
            if proposal.descriptor.validation_state!=OncoLabValidationState.REUSABLE or proposal.descriptor.availability!=OncoLabAvailability.REUSABLE:
                reasons.append('promotion_requires_explicit_scoped_reusable_contract')
            licences=[r for r in linked if r.kind==RecordKind.EXTERNAL_LOOKUP]
            commits={r.payload.get('receipt',{}).get('commit_sha') for r in candidates}
            repositories={r.payload.get('receipt',{}).get('repository_url') for r in candidates}
            if not licences or not any(any(c.get('licence') and c.get('licence') not in {'NOASSERTION','UNKNOWN'}
                and c.get('homepage') in repositories and c.get('metadata',{}).get('commit_sha') in commits
                and (c.get('homepage')==proposal.descriptor.implementation_or_source or c.get('external_id') in
                    {proposal.descriptor.implementation_or_source,proposal.scope.get('external_id')})
                for c in r.payload.get('cards',[])) for r in licences):
                reasons.append('unresolved_licence_source_binding')
            # Actual validated use must bind candidate inputs/software; independent
            # scope/reference/utility gates above cannot be replaced with run count.
            measurements=[r for r in linked if r.kind==RecordKind.MEASUREMENT and r.payload.get('origin')=='sandbox'
                and any(cid in r.payload.get('source_refs',[]) for cid in candidate_ids)]
            evidence=[r for r in linked if r.kind==RecordKind.EVIDENCE
                and r.payload.get('measurement',{}).get('analysis_id') in {m.record_id for m in measurements}]
            if not measurements or not evidence:reasons.append('missing_candidate_bound_admitted_use')
            if len({m.block_id for m in measurements if m.block_id})<2:
                reasons.append('missing_repeated_validated_use_history')
            if len({m.payload.get('input_sha256') for m in measurements})<2:
                reasons.append('missing_distinct_validated_input_history')
        elif proposal.transition=='retirement':
            if not any(r.kind==RecordKind.REFERENCE_VALIDATION and r.payload.get('status')=='failed' and r.payload.get('scope_sha256')==scope_hash for r in linked):reasons.append('retirement_requires_scoped_failed_reverification')
            if proposal.descriptor.availability not in {OncoLabAvailability.FORBIDDEN,OncoLabAvailability.UNAVAILABLE} or proposal.routes:
                reasons.append('retirement_must_remove_execution_routes')
        elif proposal.transition=='reverification':
            reasons.append('history_only_reverification')
        descriptors=list(institution.index().descriptors())
        descriptors=[d for d in descriptors if d.capability_id!=proposal.capability_id]+[proposal.descriptor]
        routes=dict(institution.index().routes)
        if proposal.routes:routes[proposal.capability_id]=proposal.routes
        else:routes.pop(proposal.capability_id,None)
        change_hash=content_hash({'descriptors':[d.model_dump(mode='json') for d in descriptors],
                                 'routes':{k:[r.model_dump(mode='json') for r in v] for k,v in routes.items()}})
        payload={'review_id':str(uuid4()),'proposal_id':proposal_id,'parent':parent,'policy_version':'scoped-governance-v3-resolved',
            'status':'rejected' if reasons else 'accepted','reasons':reasons,'scope_sha256':scope_hash,'change_sha256':change_hash}
        review_record=institution.store.append(StoredRecord(kind=RecordKind.REGISTRY_REVIEW,record_id=payload['review_id'],payload=payload))
        institution.observe(InstitutionalObservation(observation_id='review:'+payload['review_id'],capability_id=proposal.capability_id,
            kind='review',source_seq=review_record.seq,payload=payload,provenance='deterministic scoped governance'))
        if not reasons:
            revision=institution.accept(descriptors,routes,expected_parent=parent,governance_reference=review_record.seq)
            payload={**payload,'registry_revision':revision.revision_id}
        if proposal.requires_code_change:
            institution.store.append(StoredRecord(kind=RecordKind.ENGINEERING_PROPOSAL,record_id=proposal_id,
                payload={'proposal_id':proposal_id,'source_refs':[r.model_dump(mode='json') for r in proposal.references],
                         'problem':proposal.rationale,'status':'proposed','authority':'none'}))
        return payload



def review_pending(institution):
    """Service boundary consumes fresh proposals once, outside active block mutation."""
    reviewed={r.payload.get('proposal_id') for r in institution.store.records(kind=RecordKind.REGISTRY_REVIEW)}
    return tuple(review(institution,r.record_id) for r in institution.store.records(kind=RecordKind.CAPABILITY_PROPOSAL)
        if r.record_id not in reviewed)
