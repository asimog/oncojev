"""Explicit WSL2 qualification writer. Never imports testing results into research."""
import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

from src.config.environment import process_settings
from src.config.loader import load_runtime_config
from src.oncolab.institution import application_identity
from src.persistence.records import RecordKind, StoredRecord
from src.persistence.store import SqliteResearchStore
from src.provenance import content_hash
from src.runtime.paths import select_paths
from src.runtime.verification import LOCAL_CHECKS, LOCAL_VERIFICATION_VERSION, environment_basis, local_verification_passed

PROBES = ('verify_coder_container', 'verify_coder_resources', 'verify_local_science',
          'verify_science_resources', 'verify_installed_science', 'verify_profile_paths')


def checks_from_observations(observations):
    coder, resources, science, external, installed, paths = (observations[p] for p in PROBES)
    if not all(coder.get(role) and all(value is True for value in coder[role].values()) for role in ('director', 'researcher')):
        raise ValueError('incomplete role confinement observations')
    for probe in (resources, external, installed, paths):
        if probe.get('status') != 'passed' or not probe.get('checks') or not all(v is True for v in probe['checks'].values()):
            raise ValueError('incomplete adverse control observations')
    if (science.get('status') != 'passed' or science.get('secret_peer_app_network_process_denial') is not True
            or science.get('independent_replay') is not True or len(science.get('resource_phases', [])) != 5
            or not all(p.get('cleanup_confirmed') is True and p.get('kernel_controls_verified') is True for p in science['resource_phases'])):
        raise ValueError('incomplete five-phase scientific observations')
    executions = installed.get('executions', []) + [installed.get('shutdown_receipt', {})]
    if not executions or not all(r.get('cleanup_confirmed') is True and r.get('kernel_controls_verified') is True for r in executions):
        raise ValueError('installed cleanup or kernel controls unconfirmed')
    # These mappings name precisely the direct observations each contract relies on.
    return {
        'director_coder': {'filesystem': coder['director']['peer_read_denied'] and coder['director']['application_write_denied'],
            'credentials': coder['director']['provider_environment_absent'] and coder['director']['credential_file_denied'],
            'descendants': coder['director']['descendant_write_denied']},
        'researcher_coder': {'filesystem': coder['researcher']['peer_read_denied'] and coder['researcher']['application_write_denied'],
            'credentials': coder['researcher']['provider_environment_absent'] and coder['researcher']['credential_file_denied'],
            'descendants': coder['researcher']['descendant_write_denied']},
        'scientific_execution': {'filesystem': science['secret_peer_app_network_process_denial'],
            'credentials': science['secret_peer_app_network_process_denial'], 'network': science['secret_peer_app_network_process_denial'],
            'process': science['secret_peer_app_network_process_denial'], 'replay': science['independent_replay']},
        'resource_enforcement': {'process': resources['checks']['process_count'], 'cpu': resources['checks']['aggregate_cpu_rate'],
            'memory': resources['checks']['aggregate_memory'] and external['checks']['aggregate_scientific_memory'],
            'disk': resources['checks']['aggregate_disk_quota'] and external['checks']['expanded_archive_rejected_under_governor'],
            'downloads': external['checks']['actual_failed_body_bytes_charged_and_reservation_released'],
            'heavy_lease': installed['checks']['director_exclusion'],
            'cancellation': resources['checks']['cancellation_lease'] and external['checks']['cancelled_pipeline_drains_all_five_phases']},
        'installed_science': {name: installed['checks'][name] for name in LOCAL_CHECKS['installed_science']}}


def retain_qualification(store, application, basis, observations):
    checks = checks_from_observations(observations)
    identity = content_hash(basis)
    with store.transaction():
        refs = []
        for probe in PROBES:
            payload = {'event_type': 'LocalExecutionObservation', 'operational_only': True, 'status': 'passed',
                       'probe': probe, 'environment_identity': identity, 'observation': observations[probe]}
            record = store.append(StoredRecord(kind=RecordKind.SERVICE_EVENT, record_id=uuid4().hex, payload=payload))
            refs.append({'seq': record.seq, 'record_id': record.record_id, 'sha256': content_hash(payload), 'probe': probe})
        payload = {'contract_version': LOCAL_VERIFICATION_VERSION, 'status': 'passed', 'backend': 'local_venv',
            'application_identity': application, 'environment_identity': identity, 'execution_environment': basis,
            'checks': checks, 'observation_references': refs, 'scope': 'native execution controls; fixture scientific inputs; no scientific utility'}
        if not local_verification_passed(payload, application, environment_provider=lambda: basis, store=store):
            raise ValueError('qualification fails its own consumer')
        return store.append(StoredRecord(kind=RecordKind.LOCAL_VERIFICATION, record_id=uuid4().hex, payload=payload))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='Owned directory for raw probe logs')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    settings = process_settings(root)
    paths = select_paths(root, settings)
    policy = load_runtime_config(root / 'config/runtime.yaml', testing=settings.testing)
    basis = environment_basis(policy, paths)
    if (basis['system'] != 'Linux' or 'microsoft-standard-WSL2' not in basis['release']
            or any(value['filesystems'][0]['fstype'] not in {'ext4', 'xfs', 'btrfs'} for value in basis['filesystems'].values())):
        parser.error('qualification requires native WSL2 storage')
    args.output.mkdir(parents=True, exist_ok=True)
    before = application_identity(policy)
    (args.output / 'basis.json').write_text(json.dumps(basis, indent=2))
    environment = os.environ.copy()
    environment.update(LOGFIRE_SEND_TO_LOGFIRE='false', PYTHONDONTWRITEBYTECODE='1')
    observations = {}
    for probe in PROBES:
        command = [sys.executable, '-B', '-m', 'scripts.' + probe]
        if probe == 'verify_profile_paths':
            command = [sys.executable, '-B', '-m', 'pytest', '-p', 'no:cacheprovider', '-o', 'addopts=',
                'tests/invariants/test_persistence.py', '-k', 'testing_linked_paths_cannot_reach_normal_history or workspace_retention_exports_before_cleanup', '-q']
        with (args.output / (probe + '.log')).open('w') as log:
            result = subprocess.run(command, cwd=root, env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f'{probe} failed; raw log retained, no qualification written')
        if probe == 'verify_profile_paths':
            observations[probe] = {'status': 'passed', 'checks': {'linked_paths_denied': True, 'retention_scope': True},
                'raw_log': (args.output / (probe + '.log')).read_text()}
        else:
            lines = (args.output / (probe + '.log')).read_text().splitlines()
            observations[probe] = next(json.loads(line) for line in reversed(lines) if line.startswith('{'))
        print(json.dumps({'probe': probe, 'status': 'passed'}), flush=True)
    if before != application_identity(policy) or content_hash(basis) != content_hash(environment_basis(policy, paths)):
        raise RuntimeError('application/environment changed during probes; no qualification written')
    if paths.testing:
        checks_from_observations(observations)
        print(json.dumps({'status': 'passed', 'testing': True, 'qualifying': False, 'scope': 'isolated observations only'}))
        return
    paths.data.mkdir(parents=True, exist_ok=True)
    store = SqliteResearchStore(paths.database(settings.database_path))
    try:
        record = retain_qualification(store, before, basis, observations)
        print(json.dumps({'status': 'passed', 'qualifying': True, 'record_id': record.record_id, 'seq': record.seq, 'database': str(paths.database(settings.database_path))}))
    finally:
        store.close()


if __name__ == '__main__':
    main()
