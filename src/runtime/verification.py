"""Current native execution proof. Operational observations never admit evidence."""
from pathlib import Path
import hashlib
import importlib.metadata
import os
import platform
import shutil
import subprocess
import sys

from src.provenance import content_hash

LOCAL_VERIFICATION_VERSION = "local-verification-v1"
LOCAL_CHECKS = {
    "director_coder": ("filesystem", "credentials", "descendants"),
    "researcher_coder": ("filesystem", "credentials", "descendants"),
    "scientific_execution": ("filesystem", "credentials", "network", "process", "replay"),
    "resource_enforcement": ("process", "cpu", "memory", "disk", "downloads", "heavy_lease", "cancellation"),
    "installed_science": ("statistics", "parser", "figure", "memory_cgroup", "cancellation_drain", "aggregate_shutdown_drain", "retained_workspace_allowance"),
}


def environment_basis(policy=None, paths=None):
    """Measure bytes afresh; package metadata or helper caches cannot qualify drift."""
    root = Path(__file__).resolve().parents[2]
    if policy is None or paths is None:
        from src.config.environment import process_settings
        from src.config.loader import load_runtime_config
        from src.runtime.paths import select_paths
        settings = process_settings(root)
        policy = policy or load_runtime_config(root / "config/runtime.yaml", testing=settings.testing)
        paths = paths or select_paths(root, settings)
    def sha(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    contents = hashlib.sha256()
    packages = []
    for distribution in sorted(importlib.metadata.distributions(), key=lambda d: d.metadata['Name']):
        packages.append((distribution.metadata['Name'], distribution.version))
        for relative in sorted(distribution.files or [], key=str):
            if '__pycache__' in relative.parts or relative.suffix == '.pyc':
                continue
            path = distribution.locate_file(relative)
            contents.update(str(path).encode())
            contents.update(bytes.fromhex(sha(path)) if path.is_file() else b'missing')
    # Include the standard library used by the trusted governor and workers.
    stdlib = hashlib.sha256()
    for path in sorted((Path(sys.base_prefix) / f'lib/python{sys.version_info.major}.{sys.version_info.minor}').rglob('*')):
        if path.is_file() and 'site-packages' not in path.parts and '__pycache__' not in path.parts and path.suffix != '.pyc':
            stdlib.update(str(path).encode()); stdlib.update(bytes.fromhex(sha(path)))
    binaries = {name: {"path": shutil.which(name), "sha256": sha(shutil.which(name)) if shutil.which(name) else None}
                for name in ('systemd-run', 'systemctl', 'unshare', 'mount', 'timeout')}
    libraries = {}
    if platform.system() == 'Linux':
        import re
        for executable in (sys.executable, *(value['path'] for value in binaries.values() if value['path'])):
            result = subprocess.run(['ldd', str(executable)], capture_output=True, text=True, timeout=10)
            for name in re.findall(r'(/[^\s()]+)', result.stdout):
                path = Path(name)
                if path.is_file(): libraries[str(path.resolve())] = sha(path)
    native_settings = {str(path): path.read_text() if path.is_file() else None for path in (
        Path('/proc/sys/kernel/unprivileged_userns_clone'), Path('/proc/sys/user/max_user_namespaces'),
        Path('/sys/fs/cgroup/cgroup.controllers'))}
    filesystems = {}
    if platform.system() == 'Linux':
        for name, directory in {'data': paths.data, 'workspaces': paths.workspaces, 'director': paths.director}.items():
            target = directory
            while not target.exists(): target = target.parent
            result = subprocess.run(['findmnt', '--json', '--target', str(target), '--output', 'TARGET,SOURCE,FSTYPE,OPTIONS'],
                                    capture_output=True, check=True, text=True, timeout=10)
            import json
            filesystems[name] = json.loads(result.stdout)
    worktree = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
                              capture_output=True, check=True, timeout=10).stdout.decode().split('\0')
    # Exact retained worktree identity, excluding scientific data, secrets and retired documentation.
    code = {name: sha(root / name) for name in sorted(set(worktree)) if name and
            (root / name).is_file() and (Path(name).parts[0] in {'src', 'scripts', 'config', 'tests', 'skills'}
            or name in {'pyproject.toml', 'uv.lock', 'AGENTS.md', 'architecture.yaml'})}
    head = subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'], capture_output=True, check=True, text=True, timeout=10).stdout.strip()
    return {'system': platform.system(), 'release': platform.release(), 'machine': platform.machine(),
        'python': sys.version, 'executable': sys.executable, 'interpreter_sha256': sha(Path(sys.executable).resolve()),
        'prefix': sys.prefix, 'base_prefix': sys.base_prefix, 'stdlib_sha256': stdlib.hexdigest(),
        'packages': packages, 'package_bytes_sha256': contents.hexdigest(), 'control_binaries': binaries,
        'shared_libraries': libraries, 'kernel_settings': native_settings, 'uid': os.getuid() if hasattr(os, 'getuid') else None,
        'head': head, 'worktree_sha256': content_hash(code), 'effective_config': policy.model_dump(mode='json'),
        'filesystems': filesystems, 'owned_paths': {'data': str(paths.data), 'workspaces': str(paths.workspaces), 'director': str(paths.director), 'testing': paths.testing}}


def local_verification_passed(payload, application, *, environment_provider=None, store=None):
    """Require one complete same-basis receipt and resolvable supporting observations."""
    if application.startswith('application-testing-v1:'):
        return False
    environment = payload.get('execution_environment', {})
    checks = payload.get('checks', {})
    if not isinstance(environment, dict) or not isinstance(checks, dict):
        return False
    structural = (payload.get('contract_version') == LOCAL_VERIFICATION_VERSION
        and payload.get('status') == 'passed' and payload.get('application_identity') == application
        and payload.get('backend') == 'local_venv' and environment.get('system') == 'Linux'
        and environment.get('machine') == 'x86_64'
        and 'microsoft-standard-WSL2' in str(environment.get('release', ''))
        and all(isinstance(environment.get(key), str) and environment[key] for key in ('python', 'executable'))
        and all(isinstance(checks.get(group), dict) and all(checks[group].get(name) is True for name in names)
                for group, names in LOCAL_CHECKS.items()))
    if not structural:
        return False
    try:
        current = (environment_provider or environment_basis)()
        if (payload.get('environment_identity') != content_hash(environment)
                or payload['environment_identity'] != content_hash(current)
                or environment.get('owned_paths', {}).get('testing') is not False):
            return False
        from src.persistence.records import RecordKind
        refs = payload.get('observation_references', [])
        if store is None or not refs or {ref['probe'] for ref in refs} != {
                'verify_coder_container', 'verify_coder_resources', 'verify_local_science',
                'verify_science_resources', 'verify_installed_science', 'verify_profile_paths'}:
            return False
        for ref in refs:
            record = store.record_at(ref['seq'])
            if (record is None or record.kind != RecordKind.SERVICE_EVENT or record.record_id != ref['record_id']
                    or content_hash(record.payload) != ref['sha256']
                    or record.payload.get('probe') != ref['probe']
                    or record.payload.get('environment_identity') != payload['environment_identity']
                    or record.payload.get('status') != 'passed'):
                return False
        return True
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        return False
