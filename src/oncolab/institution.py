"""Append-only institutional state and observations, with reconstructible pins."""
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from src.oncolab.execution import ExecutionRoute, ROUTES
from src.oncolab.models import OncoLabDescriptor
from src.oncolab.registry import OncoLabIndex, OncoLabVerificationRecord
from src.persistence.records import RecordKind, StoredRecord
from src.provenance import content_hash


def application_identity(policy=None):
    root = Path(__file__).resolve().parents[2]
    paths = sorted((*root.joinpath('src').rglob('*.py'), *root.joinpath('config').glob('*.yaml'), root / 'pyproject.toml'))
    files = {str(p.relative_to(root)).replace('\\', '/'): content_hash(p.read_text(encoding='utf-8')) for p in paths}
    if policy is not None and policy.testing_enabled:
        return 'application-testing-v1:' + content_hash({'files': files, 'profile': 'isolated-testing-v1',
                                                        'effective_config': policy.model_dump(mode='json')})
    return 'application-v1:' + content_hash(files)


class RegistryRevision(BaseModel, frozen=True):
    revision_id: str
    parent: str | None = None
    application_identity: str
    governance_version: Literal["registry-governance-v1"] = "registry-governance-v1"
    descriptors: tuple[OncoLabDescriptor, ...]
    routes: dict[str, tuple[ExecutionRoute, ...]]
    governance_reference: int | None = None
    provenance: Literal['curated_seed', 'accepted_change']


class InstitutionalObservation(BaseModel, frozen=True):
    observation_id: str
    capability_id: str | None = None
    kind: Literal['usage', 'execution', 'failure', 'limitation', 'demand', 'suitability', 'gap',
                  'external_inspection', 'proposal', 'review', 'reverification', 'verification']
    source_seq: int | None = Field(default=None, gt=0)
    payload: dict[str, Any]
    provenance: str


class RegistryPin(BaseModel, frozen=True):
    oncolab_registry_revision: str
    oncolab_history_high_water: int = Field(ge=0)
    application_identity: str


class OncoLabInstitution:
    def __init__(self, store, seed, application, environment_provider=None):
        self.store = store
        self.application = application
        self.environment_provider = environment_provider
        with store.transaction():
            if store.latest(RecordKind.REGISTRY_REVISION) is None:
                self._append_revision(None, seed.descriptors(), seed.routes, None, 'curated_seed')
            for descriptor in seed.descriptors():
                for verification in seed.verification_records(descriptor.capability_id):
                    self.observe(InstitutionalObservation(observation_id='bundled:' + verification.capability_id + ':' + verification.verification_id,
                        capability_id=verification.capability_id, kind='verification',
                        payload=verification.model_dump(mode='json'), provenance='integrity-checked bundled seed; historical block pins unknown'))
            for record in store.records(kind=RecordKind.VERIFICATION):
                self.observe(InstitutionalObservation(observation_id='durable:' + record.record_id,
                    capability_id=record.payload['capability_id'], kind='verification', source_seq=record.seq,
                    payload=record.payload, provenance='durable verification; historical block pins unknown'))

    def observe(self, observation):
        matches = [r for r in self.store.records(kind=RecordKind.INSTITUTIONAL_OBSERVATION) if r.record_id == observation.observation_id]
        payload = observation.model_dump(mode='json')
        if matches:
            if matches[-1].payload != payload:
                raise ValueError('conflicting institutional observation identity')
            return matches[-1]
        if observation.source_seq is not None and self.store.record_at(observation.source_seq) is None:
            raise ValueError('unresolved institutional observation source')
        return self.store.append(StoredRecord(kind=RecordKind.INSTITUTIONAL_OBSERVATION,
            record_id=observation.observation_id, payload=payload))

    def pin(self):
        with self.store.transaction():
            revision = self.store.latest(RecordKind.REGISTRY_REVISION)
            history = self.store.latest(RecordKind.INSTITUTIONAL_OBSERVATION)
            return RegistryPin(oncolab_registry_revision=revision.record_id,
                               oncolab_history_high_water=history.seq if history else 0,
                               application_identity=self.application)

    def index(self, pin=None):
        pin = pin or self.pin()
        saved = next((r for r in self.store.records(kind=RecordKind.REGISTRY_REVISION) if r.record_id == pin.oncolab_registry_revision), None)
        if saved is None:
            raise ValueError('unresolved immutable registry revision')
        if pin.oncolab_history_high_water:
            history = self.store.record_at(pin.oncolab_history_high_water)
            if history is None or history.kind != RecordKind.INSTITUTIONAL_OBSERVATION:
                raise ValueError('unresolved institutional history boundary')
        revision = RegistryRevision.model_validate(saved.payload)
        check = {key:value for key,value in saved.payload.items() if key!='revision_id'}
        if content_hash(check) != revision.revision_id:
            raise ValueError('registry revision integrity mismatch')
        index = OncoLabIndex(revision.descriptors, routes=revision.routes,
                             revision_id=revision.revision_id, history_high_water=pin.oncolab_history_high_water)
        for record in self.store.records(kind=RecordKind.INSTITUTIONAL_OBSERVATION):
            if record.seq > pin.oncolab_history_high_water:
                break
            observation = InstitutionalObservation.model_validate(record.payload)
            if observation.kind in {'verification', 'reverification'} and 'verification_id' in observation.payload:
                verification = OncoLabVerificationRecord.model_validate(observation.payload)
                if index.describe(verification.capability_id) is not None:
                    index.record_verification(verification)
        return index

    def accept(self, descriptors, routes, *, expected_parent, governance_reference):
        """Python-owned accepted review only; no agent add/edit/delete endpoint."""
        with self.store.transaction():
            review = self.store.record_at(governance_reference)
            if review is None or review.kind != RecordKind.REGISTRY_REVIEW or review.payload.get('status') != 'accepted':
                raise ValueError('accepted governed review required')
            parent = self.pin().oncolab_registry_revision
            if parent != expected_parent or review.payload.get('parent') != parent:
                raise ValueError('stale governed registry change')
            change_hash = content_hash({'descriptors': [d.model_dump(mode='json') for d in descriptors],
                                       'routes': {k: [r.model_dump(mode='json') for r in v] for k, v in routes.items()}})
            if review.payload.get('change_sha256') != change_hash:
                raise ValueError('review does not bind this exact capability-state change')
            return self._append_revision(parent, descriptors, routes, governance_reference, 'accepted_change')

    def _append_revision(self, parent, descriptors, routes, governance_reference, provenance):
        # Validate ID closure before committing a revision; route presence alone
        # never expands the installed application tool surface.
        validated = OncoLabIndex(descriptors, routes=routes)
        if set(routes) - {d.capability_id for d in validated.descriptors()}:
            raise ValueError('route refers to unknown capability')
        values = dict(parent=parent, application_identity=self.application, descriptors=validated.descriptors(),
                      routes=routes, governance_reference=governance_reference, provenance=provenance)
        revision = RegistryRevision(revision_id='pending', **values)
        revision = revision.model_copy(update={'revision_id': content_hash(revision.model_dump(mode='json', exclude={'revision_id'}))})
        self.store.append(StoredRecord(kind=RecordKind.REGISTRY_REVISION, record_id=revision.revision_id, payload=revision.model_dump(mode='json')))
        return revision


def refresh_reviewed_search_metadata(institution, seed, *, capability_id="stat.scipy"):
    """Explicit reviewed engineering migration; preserves all routes and old pins.

    Only Task 11 stat.scipy purpose/tags and source.gdc limitations are supported.
    Scientific promotion remains governed separately.
    """
    with institution.store.transaction():
        parent = institution.pin().oncolab_registry_revision
        index = institution.index()
        fields = {'stat.scipy': ('purpose', 'tags'), 'source.gdc': ('limitations',)}.get(capability_id)
        if fields is None: raise ValueError('unsupported reviewed metadata correction')
        existing = index.describe(capability_id)
        canonical = seed.describe(capability_id)
        if existing is None or canonical is None: raise ValueError('canonical descriptor missing')
        updated = existing.model_copy(update={name: getattr(canonical, name) for name in fields})
        if updated == existing: return None
        descriptors = [updated if d.capability_id == existing.capability_id else d for d in index.descriptors()]
        routes = dict(index.routes)
        change_hash = content_hash({'descriptors': [d.model_dump(mode='json') for d in descriptors],
            'routes': {k: [r.model_dump(mode='json') for r in v] for k, v in routes.items()}})
        payload = {'review_id': content_hash({'parent': parent, 'change': change_hash}), 'parent': parent,
            'status': 'accepted', 'policy_version': 'reviewed-search-metadata-v1', 'change_sha256': change_hash,
            'application_identity': institution.application, 'capability_id': existing.capability_id,
            'before': existing.model_dump(mode='json', include=set(fields)),
            'after': updated.model_dump(mode='json', include=set(fields)),
            'scope': 'Reviewed Task 11 canonical metadata correction; no authority, route or scientific-validation change.'}
        saved = institution.store.append(StoredRecord(kind=RecordKind.REGISTRY_REVIEW, record_id=payload['review_id'], payload=payload))
        return institution.accept(descriptors, routes, expected_parent=parent, governance_reference=saved.seq)
