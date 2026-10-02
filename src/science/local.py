"""Confined Linux single-process Python experiments; no Docker daemon needed."""
import hashlib
import json
from pathlib import Path
import platform
import re
import sys
import time
from urllib.parse import unquote, urlparse
from uuid import uuid4

import httpx

from src.provenance import content_hash
from src.runtime.process import ProcessLimits, run_owned_command, workspace_bytes
from src.science.sandbox import (GithubMethodRequest,SandboxPolicy,SandboxError,SandboxInvocation,
    SandboxReceipt,SandboxMeasurementCandidate,DockerScientificSandbox,SHA,validate_sandbox_candidate)


class LocalVenvScientificBackend:
    def __init__(self, root, policy=None, *, download_limit=10_000_000, workspace_limit=100_000_000,
                 workspace_base=None, max_processes=16, minimum_free_disk_bytes=10_000_000):
        self.root=Path(root).resolve()
        self.policy=policy or SandboxPolicy()
        self.download_limit=download_limit
        self.workspace_limit=workspace_limit
        self.downloaded=0
        self.workspace_base=Path(workspace_base).resolve() if workspace_base is not None else self.root
        if not self.root.is_relative_to(self.workspace_base):raise ValueError('experiment root must belong to its workspace')
        self.max_processes=max_processes
        self.minimum_free_disk_bytes=minimum_free_disk_bytes
        self.process_resources=[]
        self.deadline=None

    def _remaining(self):
        remaining=self.policy.timeout_seconds if self.deadline is None else self.deadline-time.monotonic()
        if remaining<=0:raise SandboxError('scientific pipeline exceeded its total wall allowance')
        return remaining

    def _fetch(self,url):
        chunks=[]
        deadline=time.monotonic()+self._remaining()
        with httpx.Client(timeout=min(20,self._remaining()),follow_redirects=False,trust_env=False,headers={'Accept-Encoding':'identity'}) as client:
            with client.stream('GET',url) as response:
                response.raise_for_status()
                if response.headers.get('content-encoding','identity')!='identity':raise SandboxError('unsupported encoded acquisition response')
                declared=response.headers.get('content-length')
                if declared and int(declared)>self.download_limit-self.downloaded:raise SandboxError('declared acquisition exceeds reserved byte ceiling')
                # Charge each received body chunk before checking its ceiling;
                # never stop partway through a buffered chunk and hide its bytes.
                for chunk in response.iter_raw():
                    self.downloaded+=len(chunk)
                    if time.monotonic()>deadline:raise SandboxError('scientific acquisition exceeded its total wall allowance')
                    if self.downloaded>self.download_limit:raise SandboxError('scientific acquisition exceeded reserved byte ceiling')
                    chunks.append(chunk)
        return b''.join(chunks)

    def _disk_used(self):
        return workspace_bytes(self.workspace_base)

    def _write_input(self,path,data):
        self._remaining()
        if self._disk_used()+len(data)>self.workspace_limit:
            raise SandboxError('experiment inputs exceed aggregate workspace capacity')
        path.write_bytes(data)

    def _owned(self,root,argv,environment,phase):
        # Other retained experiments and Coder scratch share the block's ceiling.
        # The active experiment alone is mounted; peer paths stay inaccessible.
        allowance=self.workspace_limit-(self._disk_used()-workspace_bytes(root))
        if allowance<=0:raise SandboxError('no aggregate experiment workspace capacity')
        limits=ProcessLimits(processes=self.max_processes,memory_mb=self.policy.memory_mb,cpu=self.policy.cpu,
            wall_seconds=self._remaining(),workspace_bytes=allowance,
            minimum_free_disk_bytes=self.minimum_free_disk_bytes)
        result=run_owned_command(root,argv,environment,limits)
        self.process_resources.append({'phase':phase,**result.resources})
        return result

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
        if phase=='install':
            temporary=root/'outputs'/'install-temp';temporary.mkdir(exist_ok=True)
            env.update(TMPDIR=str(temporary),PIP_PROGRESS_BAR='off')
        out=root/'outputs'/f'{phase}-{uuid4().hex}.stdout'
        err=out.with_suffix('.stderr')
        result=self._owned(root,argv,env,phase)
        raw,errors=result.stdout_raw,result.stderr_raw
        self._write_input(out,raw);self._write_input(err,errors)
        invocation=SandboxInvocation(command=command,effective_command=tuple(effective),exit_status=result.exit_code,
            stdout_sha256=hashlib.sha256(raw).hexdigest(),stderr_sha256=hashlib.sha256(errors).hexdigest())
        if result.exit_code:raise SandboxError('confined scientific '+phase+' failed: '+errors.decode(errors='replace')[-500:])
        return invocation,raw.decode('utf-8')

    def acquire_and_execute(self,request:GithubMethodRequest):
        if sys.platform!='linux' or platform.machine()!='x86_64':raise SandboxError('local scientific execution requires Linux x86_64; no unconfined fallback')
        self.downloaded=0
        self.process_resources=[]
        self.deadline=time.monotonic()+self.policy.timeout_seconds
        request.input_identity()
        self.root.mkdir(parents=True,exist_ok=True)
        root=self.root/str(uuid4());root.mkdir()
        try:
            slug=request.repository_url.removeprefix('https://github.com/')
            if SHA.fullmatch(request.requested_ref):commit=request.requested_ref
            else:
                from urllib.parse import quote
                metadata_bytes=self._fetch('https://api.github.com/repos/'+slug+'/commits/'+quote(request.requested_ref,safe=''))
                if len(metadata_bytes)>262144:raise SandboxError('repository metadata exceeds bounded parsing ceiling')
                metadata=json.loads(metadata_bytes)
                commit=metadata.get('sha')
                if not SHA.fullmatch(commit or ''):raise SandboxError('unresolved public repository commit')
            archive=self._fetch('https://codeload.github.com/'+slug+'/tar.gz/'+commit)
            inputs=root/'inputs';inputs.mkdir();(inputs/'artifacts').mkdir();(inputs/'wheels').mkdir();(root/'outputs').mkdir()
            self._write_input(inputs/'repository.tar.gz',archive)
            self._write_input(inputs/'request.json',json.dumps(request.input_json,sort_keys=True).encode('utf-8'))
            for artifact in request.input_artifacts:self._write_input(inputs/'artifacts'/artifact.byte_sha256,artifact.bytes())
            for wheel in request.dependency_wheels:
                data=self._fetch(wheel.url)
                if hashlib.sha256(data).hexdigest()!=wheel.sha256:raise SandboxError('dependency wheel identity mismatch')
                name=unquote(Path(urlparse(wheel.url).path).name)
                if not re.fullmatch(r'[A-Za-z0-9_.+-]+\.whl',name):raise SandboxError('unsupported wheel filename')
                self._write_input(inputs/'wheels'/name,data)
            settings={'root':str(root),'application':str(Path(__file__).resolve().parents[2]),'workspace_bytes':self.workspace_limit}
            bootstrap=self._owned(root,[sys.executable,'-I',str(Path(__file__).with_name('prepare_exec.py')),json.dumps(settings)],
                {'PATH':str(Path(sys.executable).parent)+':/usr/local/bin:/usr/bin:/bin','HOME':str(root/'outputs'),
                 'TMPDIR':str(root/'outputs'),'PYTHONDONTWRITEBYTECODE':'1'},'prepare')
            if bootstrap.exit_code:raise SandboxError('confined experiment preparation failed: '+bootstrap.stderr[-500:])
            install=self._command(root,request.install_command,'install')
            test=self._command(root,request.test_command,'test')
            first=self._command(root,request.execute_command,'execute')
            replay=self._command(root,request.execute_command,'replay')
            values=DockerScientificSandbox._parse_replayed_output(first[1],replay[1])
            environment={'backend':'local_venv','executor_version':'local-venv-v4','platform':platform.platform(),
                'python_version':platform.python_version(),'python_sha256':hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest(),
                'interpreter_link_mode':'read_only_base_interpreter','base_python_prefix':sys.base_prefix,
                'archive_sha256':hashlib.sha256(archive).hexdigest(),'dependencies':[w.model_dump(mode='json') for w in request.dependency_wheels],
                'dependencies_sha256':content_hash([w.model_dump(mode='json') for w in request.dependency_wheels]),
                'network':'disabled_for_install_test_execute','confinement':'landlock-seccomp-single-process-v2-trusted-launcher',
                'cpu':self.policy.cpu,'memory_mb':self.policy.memory_mb,'workspace_bytes':self._disk_used(),
                'aggregate_controls':'owned-command-v1','process_resources':self.process_resources,
                'downloaded_bytes':self.downloaded,'experiment_path':str(root),'dependency_lock':'retained exact wheel bytes/hashes; fresh qualification is separate'}
            receipt=SandboxReceipt(repository_url=request.repository_url,commit_sha=commit,environment=environment,
                environment_sha256=content_hash(environment),input_sha256=request.input_identity(),
                install=install[0],test=test[0],first_run=first[0],replay_run=replay[0],
                bootstrap=SandboxInvocation(command=('python','-m','venv','--symlinks'),exit_status=bootstrap.exit_code,
                    stdout_sha256=hashlib.sha256(bootstrap.stdout_raw).hexdigest(),stderr_sha256=hashlib.sha256(bootstrap.stderr_raw).hexdigest()))
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
