"""Re-review retained distinct source uses against current proof; never fabricate utility."""
import json
from pathlib import Path
from src.config.loader import load_models_config, load_runtime_config
from src.persistence.records import RecordKind
from src.persistence.repository import ResearchRepository
from src.persistence.store import SqliteResearchStore
from src.runtime.pydantic_ai.factory import build_harness_runtime
from src.oncolab.governance import CapabilityProposal, propose, review
from src.memory.service import reference


def main():
    root = Path(__file__).resolve().parents[1]
    previous = json.loads((root / 'var/task10-proof/reusable-mean.json').read_text())
    store = SqliteResearchStore(previous['database'])
    try:
        runtime = build_harness_runtime(load_models_config(root / 'config/models.yaml'), load_runtime_config(root / 'config/runtime.yaml'), repository=ResearchRepository(store))
        saved = next(r for r in store.records(kind=RecordKind.CAPABILITY_PROPOSAL) if r.record_id == previous['proposal_id'])
        old = CapabilityProposal.model_validate(saved.payload)
        supporting = [store.record_at(ref.seq) for ref in old.references if ref.kind not in {RecordKind.LOCAL_VERIFICATION, RecordKind.EXTERNAL_LOOKUP, RecordKind.UTILITY_EVALUATION}]
        candidate = next(r for r in supporting if r.kind == RecordKind.SANDBOX_CANDIDATE and r.record_id == old.routes[0].candidate_id)
        licence = next(r for r in store.records(kind=RecordKind.EXTERNAL_LOOKUP) if any(c.get('homepage') == candidate.payload['receipt']['repository_url']
            and c.get('metadata', {}).get('commit_sha') == candidate.payload['receipt']['commit_sha'] for c in r.payload.get('cards', [])))
        utility = store.record_at(previous['utility_reference']['seq'])
        # The current application identity is recomputed by the existing runtime owner.
        # Rebind an unsupported comparison honestly; it still cannot pass.
        from src.oncolab.utility import retain_utility_evaluation
        comparison = store.record_at(utility.payload['comparison_reference']['seq']).payload['comparison']
        utility = retain_utility_evaluation(store, candidate.record_id, old.scope, comparison, application_identity=runtime.institution.application)
        supporting.extend([store.latest(RecordKind.LOCAL_VERIFICATION), licence, utility])
        proposal = CapabilityProposal(**{**old.model_dump(exclude={'proposal_id'}), 'parent': runtime.institution.pin().oncolab_registry_revision,
            'references': tuple(reference(r) for r in supporting if r is not None)})
        propose(runtime.institution, proposal); outcome = review(runtime.institution, proposal.proposal_id)
        assert outcome['status'] == 'rejected' and any('utility' in r for r in outcome['reasons'])
        (root / 'var/task10-proof/review-current.json').write_text(json.dumps(outcome, indent=2) + '\n')
        print(json.dumps(outcome))
    finally: store.close()


if __name__ == '__main__': main()
