"""Explicit migration of the reviewed Task 11 canonical retrieval correction."""
import json
from pathlib import Path
from src.oncolab.catalogue import initial_oncolab_index
from src.oncolab.institution import OncoLabInstitution, application_identity, refresh_reviewed_search_metadata
from src.persistence.store import SqliteResearchStore


def main():
    root = Path(__file__).resolve().parents[1]
    store = SqliteResearchStore(root / 'var/oncojev.sqlite3')
    try:
        seed = initial_oncolab_index()
        institution = OncoLabInstitution(store, seed, application_identity())
        before = institution.pin()
        revision = refresh_reviewed_search_metadata(institution, seed)
        after = institution.pin()
        assert institution.index(before).routes == institution.index(after).routes
        output = {'previous_pin': before.model_dump(), 'current_pin': after.model_dump(),
            'changed': revision is not None, 'scope': 'Search metadata only; original execution/validation contracts preserved.'}
        path = root / 'var/task11-proof'; path.mkdir(exist_ok=True)
        (path / 'registry-metadata.json').write_text(json.dumps(output, indent=2) + '\n')
        print(json.dumps(output))

    finally: store.close()


if __name__ == '__main__': main()
