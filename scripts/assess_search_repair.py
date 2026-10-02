"""Matched retained-registry retrieval before/after the scoped metadata correction."""
import json
from pathlib import Path
from types import SimpleNamespace
from src.evals.selection import SELECTION_TASKS, SelectionTask, evaluate_selection
from src.oncolab.institution import OncoLabInstitution, RegistryPin, application_identity
from src.oncolab.catalogue import initial_oncolab_index
from src.persistence.store import SqliteResearchStore


def main():
    root = Path(__file__).resolve().parents[1]
    migration = json.loads((root / 'var/task11-proof/registry-metadata.json').read_text())
    store = SqliteResearchStore(root / 'var/oncojev.sqlite3')
    try:
        institution = OncoLabInstitution(store, initial_oncolab_index(), application_identity())
        tasks = (*SELECTION_TASKS,
            SelectionTask(task_id='heldout-linear', query='paired linear relationship', need={'estimand': 'correlation', 'design': 'paired'}, useful_ids=('stat.scipy',), available_inputs={'x': 11, 'y': 11}, information_space='statistics'),
            SelectionTask(task_id='heldout-welch', query='Welch independent group comparison', need={'estimand': 'mean contrast', 'design': 'independent'}, useful_ids=('stat.scipy',), available_inputs={'group_a': 5, 'group_b': 5}, information_space='statistics'))
        reports = []
        for phase, pin in [('before', migration['previous_pin']), ('after', migration['current_pin'])]:
            index = institution.index(RegistryPin.model_validate(pin))
            runtime = SimpleNamespace(index_for=lambda _: index, oncolab_candidate_k=80, oncolab_search_k=8,
                resources=lambda _: {'source': {'attempted': 0}})
            report = evaluate_selection(runtime, None, tasks, condition='deterministic')
            report['phase'] = phase; report['pin'] = pin
            reports.append(report)
        before = institution.index(RegistryPin.model_validate(migration['previous_pin']))
        after = institution.index(RegistryPin.model_validate(migration['current_pin']))
        page = before.search_page('co movement linear association', limit=8)
        same = before.search_page('co movement linear association', limit=8, continuation=page.continuation)
        try: after.search_page('co movement linear association', limit=8, continuation=page.continuation)
        except ValueError: changed_rejected = True
        else: changed_rejected = False
        assert changed_rejected and not set(c.capability_id for c in page.cards) & set(c.capability_id for c in same.cards)
        output = {'reports': reports, 'unchanged_limits': {'candidate_k': 80, 'search_k': 8}, 'changed_cursor_rejected': changed_rejected,
            'same_snapshot_continuation_disjoint': True, 'execution_routes_unchanged': before.routes == after.routes,
            'scientific_utility': None, 'label_review': 'Generated route coverage labels; independent scientific utility review pending.'}
        (root / 'var/task11-proof/retrieval-before-after.json').write_text(json.dumps(output, indent=2) + '\n')
        print(json.dumps([{'phase': r['phase'], 'recall': {x['task_id']: x['retrieval_recall'] for x in r['rows']}} for r in reports]))
    finally: store.close()


if __name__ == '__main__': main()
