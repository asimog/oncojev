"""Confined Linux single-process Python experiments; no Docker daemon needed."""
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import sys
import tarfile
import time
from urllib.parse import unquote, urlparse
from uuid import uuid4

import httpx

from src.provenance import content_hash
from src.science.sandbox import (GithubMethodRequest,SandboxPolicy,SandboxError,SandboxInvocation,
    SandboxReceipt,SandboxMeasurementCandidate,DockerScientificSandbox,SHA,validate_sandbox_candidate)


class LocalVenvScientificBackend:
    def __init__(self, root, policy=None, *, download_limit=10_000_000, workspace_limit=100_000_000):
        self.root=Path(root).resolve()
        self.policy=policy or SandboxPolicy()
        self.download_limit=download_limit
        self.workspace_limit=workspace_limit
        self.downloaded=0

    def _fetch(self,url):
        chunks=[]
        with httpx.Client(timeout=20,follow_redirects=False) as client:
            with client.stream('GET',url) as response:
                response.raise_for_status()
                declared=response.headers.get('content-length')
                if declared and int(declared)>self.download_limit-self.downloaded:raise SandboxError('declared acquisition exceeds reserved byte ceiling')
                for chunk in response.iter_bytes(chunk_size=min(65536,max(1,self.download_limit-self.downloaded+1))):
                    self.downloaded+=len(chunk)
                    if self.downloaded>self.download_limit:raise SandboxError('scientific acquisition exceeded reserved byte ceiling')
                    chunks.append(chunk)
        return b''.join(chunks)

    def _disk_used(self):
        return sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file() and not p.is_symlink())

    def _command(self,root,command,phase):
        effective=list(command)
        effective[0]=str(root/'venv'/'bin'/('python' if command[0]=='python' else 'pytest'))
        effective=[arg.replace('/input/request.json',str(root/'inputs'/'request.json'))
            .replace('/input/artifacts/',str(root/'inputs'/'artifacts')+'/').replace('/repo/',str(root/'repository')+'/') for arg in effective]
        if phase=='install':
            if command==('python','--version'):pass
            elif command[:4]==('python','-m','pip','install'):
                # Only pre-acquired wheels or this repository; offline build
                # failures remain unsupported, never enable install networking.
                effective.extend(('--no-index','--no-deps','--no-build-isolation','--find-links',str(root/'inputs'/'wheels')))
            else:raise SandboxError('local installation requires offline pip or explicit no-install Python identity')
        settings={'root':str(root),'application':str(Path(__file__).resolve().parents[2]),'phase':phase,
            'memory_mb':self.policy.memory_mb,'timeout':self.policy.timeout_seconds,'max_output_bytes':1_000_000}
        launcher=Path(__file__).with_name('confined_exec.py')
        # Installation can replace files in the experiment venv. Always apply
        # confinement with the application interpreter before exec'ing any of
        # those files, including the experiment's Python/pytest entry points.
        argv=[sys.executable,'-I',str(launcher),json.dumps(settings),*effective]
        env={'PATH':str(root/'venv'/'bin')+':/usr/local/bin:/usr/bin:/bin','HOME':str(root/'outputs'),
            'TMPDIR':str(root/'outputs'),'PYTHONNOUSERSITE':'1','PYTHONDONTWRITEBYTECODE':'1',
            'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','LANG':'C.UTF-8','PIP_NO_INPUT':'1','PIP_DISABLE_PIP_VERSION_CHECK':'1'}
        out=root/'outputs'/f'{phase}-{uuid4().hex}.stdout'
        err=out.with_suffix('.stderr')
        start=time.monotonic()
        with out.open('wb') as stdout,err.open('wb') as stderr:
            process=subprocess.Popen(argv,cwd=root/'repository',env=env,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,
                start_new_session=True,close_fds=True)
            try:
                while process.poll() is None:
                    if time.monotonic()-start>self.policy.timeout_seconds:raise SandboxError('scientific command exceeded wall time')
                    if self._disk_used()>self.workspace_limit:raise SandboxError('experiment workspace exceeded reserved disk ceiling')
                    time.sleep(.05)
            except BaseException:
                os.killpg(process.pid,signal.SIGKILL);process.wait();raise
        raw=out.read_bytes();errors=err.read_bytes()
        if len(raw)>1_000_000 or len(errors)>1_000_000:raise SandboxError('scientific command output exceeded ceiling')
        invocation=SandboxInvocation(command=command,effective_command=tuple(effective),exit_status=process.returncode,
            stdout_sha256=hashlib.sha256(raw).hexdigest(),stderr_sha256=hashlib.sha256(errors).hexdigest())
        if process.returncode:raise SandboxError('confined scientific '+phase+' failed: '+errors.decode(errors='replace')[-500:])
        return invocation,raw.decode('utf-8')

    def acquire_and_execute(self,request:GithubMethodRequest):
        if sys.platform!='linux' or platform.machine()!='x86_64':raise SandboxError('local scientific execution requires Linux x86_64; no unconfined fallback')
        self.downloaded=0
        request.input_identity()
        self.root.mkdir(parents=True,exist_ok=True)
        root=self.root/str(uuid4());root.mkdir()
        try:
            slug=request.repository_url.removeprefix('https://github.com/')
            if SHA.fullmatch(request.requested_ref):commit=request.requested_ref
            else:
                from urllib.parse import quote
                metadata=json.loads(self._fetch('https://api.github.com/repos/'+slug+'/commits/'+quote(request.requested_ref,safe='')))
                commit=metadata.get('sha')
                if not SHA.fullmatch(commit or ''):raise SandboxError('unresolved public repository commit')
            archive=self._fetch('https://codeload.github.com/'+slug+'/tar.gz/'+commit)
            repository=root/'repository';repository.mkdir()
            unpacked=0
            with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as tar:
                members=tar.getmembers()
                if len(members)>20000:raise SandboxError('repository archive member ceiling exceeded')
                for member in members:
                    path=Path(*Path(member.name).parts[1:])
                    destination=(repository/path).resolve()
                    if not destination.is_relative_to(repository) or member.issym() or member.islnk() or not(member.isfile() or member.isdir()):
                        raise SandboxError('repository archive contains unsupported path/link/type')
                    if member.isdir():destination.mkdir(parents=True,exist_ok=True);continue
                    unpacked+=member.size
                    if unpacked>self.workspace_limit//2:raise SandboxError('expanded repository exceeds disk reservation')
                    destination.parent.mkdir(parents=True,exist_ok=True)
                    destination.write_bytes(tar.extractfile(member).read())
            inputs=root/'inputs';inputs.mkdir();(inputs/'artifacts').mkdir();(inputs/'wheels').mkdir();(root/'outputs').mkdir()
            (inputs/'repository.tar.gz').write_bytes(archive)
            (inputs/'request.json').write_text(json.dumps(request.input_json,sort_keys=True),encoding='utf-8')
            for artifact in request.input_artifacts:(inputs/'artifacts'/artifact.byte_sha256).write_bytes(artifact.bytes())
            for wheel in request.dependency_wheels:
                data=self._fetch(wheel.url)
                if hashlib.sha256(data).hexdigest()!=wheel.sha256:raise SandboxError('dependency wheel identity mismatch')
                name=unquote(Path(urlparse(wheel.url).path).name)
                if not re.fullmatch(r'[A-Za-z0-9_.+-]+\.whl',name):raise SandboxError('unsupported wheel filename')
                (inputs/'wheels'/name).write_bytes(data)
            bootstrap=subprocess.run([sys.executable,'-I','-m','venv','--symlinks',str(root/'venv')],env={'PATH':'/usr/local/bin:/usr/bin:/bin'},
                stdin=subprocess.DEVNULL,capture_output=True,timeout=self.policy.timeout_seconds,check=False)
            if bootstrap.returncode:raise SandboxError('fresh experiment venv initialization failed')
            install=self._command(root,request.install_command,'install')
            test=self._command(root,request.test_command,'test')
            first=self._command(root,request.execute_command,'execute')
            replay=self._command(root,request.execute_command,'replay')
            values=DockerScientificSandbox._parse_replayed_output(first[1],replay[1])
            environment={'backend':'local_venv','executor_version':'local-venv-v3','platform':platform.platform(),
                'python_version':platform.python_version(),'python_sha256':hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest(),
                'interpreter_link_mode':'read_only_base_interpreter','base_python_prefix':sys.base_prefix,
                'archive_sha256':hashlib.sha256(archive).hexdigest(),'dependencies':[w.model_dump(mode='json') for w in request.dependency_wheels],
                'dependencies_sha256':content_hash([w.model_dump(mode='json') for w in request.dependency_wheels]),
                'network':'disabled_for_install_test_execute','confinement':'landlock-seccomp-single-process-v2-trusted-launcher',
                'cpu':self.policy.cpu,'memory_mb':self.policy.memory_mb,'workspace_bytes':self._disk_used(),
                'downloaded_bytes':self.downloaded,'experiment_path':str(root),'dependency_lock':'retained exact wheel bytes/hashes; fresh qualification is separate'}
            receipt=SandboxReceipt(repository_url=request.repository_url,commit_sha=commit,environment=environment,
                environment_sha256=content_hash(environment),input_sha256=request.input_identity(),
                install=install[0],test=test[0],first_run=first[0],replay_run=replay[0])
            return SandboxMeasurementCandidate(candidate_id=str(uuid4()),receipt=receipt,values=values,request=request,policy=self.policy,output_json=first[1])
        except BaseException as error:
            if isinstance(error,Exception):error.consumed_bytes=self.downloaded
            raise

    def replay(self,candidate):
        validate_sandbox_candidate(candidate,'independent-replay-preflight')
        replayed=self.acquire_and_execute(candidate.request.model_copy(update={'requested_ref':candidate.receipt.commit_sha}))
        if replayed.receipt.first_run.stdout_sha256!=candidate.receipt.first_run.stdout_sha256:
            raise SandboxError('independent fresh replay differs from retained output')
        return replayed
