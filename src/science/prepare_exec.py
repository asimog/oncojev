"""Trusted archive/bootstrap work inside the owned aggregate Linux governor."""
import importlib.util
import json
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import tarfile


def main():
    settings = json.loads(sys.argv[1])
    root = Path(settings['root']).resolve(strict=True)
    application = Path(settings['application']).resolve(strict=True)
    spec = importlib.util.spec_from_file_location('oncojev_confinement', application / 'src/runtime/confinement.py')
    confinement = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(confinement)
    confinement.restrict_filesystem((root,), (Path(sys.prefix), Path(sys.base_prefix), application / 'src'))
    confinement.restrict_process_authority()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
    repository = root / 'repository'
    repository.mkdir()
    count, expanded = 0, 0
    # Stream headers/members: a compressed metadata bomb cannot allocate an
    # unbounded getmembers() list before the count/expanded-size checks.
    with tarfile.open(root / 'inputs/repository.tar.gz', mode='r|gz') as archive:
        for member in archive:
            count += 1
            if count > 20000: raise ValueError('repository archive member ceiling exceeded')
            destination = (repository / Path(*Path(member.name).parts[1:])).resolve()
            if (not destination.is_relative_to(repository) or member.issym() or member.islnk()
                or not (member.isfile() or member.isdir())):
                raise ValueError('repository archive contains unsupported path/link/type')
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            expanded += member.size
            if expanded > settings['workspace_bytes'] // 2:
                raise ValueError('expanded repository exceeds disk reservation')
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as source, destination.open('wb') as target:
                shutil.copyfileobj(source, target, length=65536)
    # Only the trusted base interpreter/ensurepip runs here, never repository
    # code or network package resolution. All descendants share the same cgroup.
    bootstrap = subprocess.run([sys.executable, '-I', '-m', 'venv', '--symlinks', str(root / 'venv')],
                               stdin=subprocess.DEVNULL, check=False)
    if bootstrap.returncode: raise RuntimeError('fresh experiment venv initialization failed')


if __name__ == '__main__':
    try: main()
    except Exception as error:
        print('Scientific preparation failed: ' + type(error).__name__ + ': ' + str(error), file=sys.stderr)
        sys.exit(126)
