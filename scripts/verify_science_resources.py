"""Native WSL owning resource probes with fixture transport, never utility proof."""
import asyncio
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import tarfile
import zipfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from src.block.manager import BlockManager
from src.jev.client import DeterministicJevClient
from src.reasoner.service import DeterministicReasoner
from src.runtime.pydantic_ai.contracts import HarnessRuntime
from src.runtime.resources import ResourceBusy,ResourceRejected,ServiceResources
from src.science.execution import ScienceExecutor
from src.science.local import LocalVenvScientificBackend
from src.science.sandbox import GithubMethodRequest, LockedWheel, SandboxError, SandboxPolicy, validate_sandbox_candidate


def archive(files):
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w:gz') as output:
        for name,data in files.items():
            member=tarfile.TarInfo('fixture/'+name);member.size=len(data)
            output.addfile(member,io.BytesIO(data))
    return buffer.getvalue()


def transport(backend,data,wheel=None):
    def fetch(url):
        value=wheel if 'pythonhosted.org' in url else data
        backend.downloaded+=len(value)
        return value
    backend._fetch=fetch


def rejected(backend,request):
    try:backend.acquire_and_execute(request)
    except SandboxError:return
    raise AssertionError('resource-exhausted experiment unexpectedly produced a candidate')


async def main():
    request=GithubMethodRequest(repository_url='https://github.com/example/fixture',requested_ref='a'*40,
        install_command=('python','--version'),test_command=('python','run.py'),execute_command=('python','run.py'),input_json={})
    data=archive({'run.py':b'import json\nprint(json.dumps({"values":{"value":4.0}}))\n'})
    policy=SandboxPolicy(memory_mb=512,cpu=1,timeout_seconds=30)
    checks={}
    with tempfile.TemporaryDirectory(prefix='science-resource-proof-') as temporary:
        root=Path(temporary)
        # Prior bootstrap runs unbounded, then notices excess only after its
        # first external command starts. The original retained tree exceeds 8MB.
        small=LocalVenvScientificBackend(root/'small',policy,workspace_limit=8_000_000)
        transport(small,data);rejected(small,request)
        assert small._disk_used()<=8_000_000,'bootstrap exceeded the hard workspace ceiling before detection'
        assert small.downloaded==len(data)
        checks['bootstrap_disk_quota']=True

        expanded=LocalVenvScientificBackend(root/'expanded',policy,workspace_limit=4_000_000)
        expanded_data=archive({'large.dat':b'x'*3_000_000})
        transport(expanded,expanded_data);rejected(expanded,request)
        assert expanded._disk_used()<=4_000_000 and expanded.process_resources[0]['kernel_controls_verified']
        assert 'prepare'==expanded.process_resources[0]['phase']
        checks['expanded_archive_rejected_under_governor']=True

        # A valid pure wheel writes many individually small files. A per-file
        # ceiling does not bound their aggregate uncompressed installation.
        wheel_buffer=io.BytesIO()
        metadata='resource_payload-0.0.1.dist-info/'
        files={f'resource_payload/blob{i}.dat':b'x'*500_000 for i in range(40)}
        files[metadata+'METADATA']=b'Metadata-Version: 2.1\nName: resource-payload\nVersion: 0.0.1\n'
        files[metadata+'WHEEL']=b'Wheel-Version: 1.0\nGenerator: native-resource-fixture\nRoot-Is-Purelib: true\nTag: py3-none-any\n'
        files[metadata+'RECORD']=''.join(f'{name},,\n' for name in (*files,metadata+'RECORD')).encode()
        with zipfile.ZipFile(wheel_buffer,'w',zipfile.ZIP_DEFLATED) as output:
            for name,value in files.items():output.writestr(name,value)
        wheel=wheel_buffer.getvalue()
        locked=LockedWheel(url='https://files.pythonhosted.org/resource_payload-0.0.1-py3-none-any.whl',sha256=hashlib.sha256(wheel).hexdigest())
        install_request=request.model_copy(update={'dependency_wheels':(locked,),
            'install_command':('python','-m','pip','install','resource-payload')})
        install=LocalVenvScientificBackend(root/'install',policy,workspace_limit=16_000_000)
        transport(install,data,wheel);rejected(install,install_request)
        proof=install.process_resources[-1]
        assert proof['phase']=='install' and proof['kernel_controls_verified'] and proof['cleanup_confirmed'],proof
        assert install._disk_used()<=16_000_000
        last=list(install.root.glob('*/outputs/install-*.stderr'))
        assert last and 'No space left on device' in last[-1].read_text(),last
        assert install.downloaded==len(data)+len(wheel)
        checks['aggregate_offline_install_disk']=True

        # Cumulative retained scratch is part of the next experiment's quota.
        retained=LocalVenvScientificBackend(root/'retained',policy,workspace_limit=16_000_000)
        transport(retained,data)
        candidate=retained.acquire_and_execute(request)
        assert validate_sandbox_candidate(candidate,'resource-fixture').values=={'value':4.0}
        rejected(retained,request)
        assert retained._disk_used()<=16_000_000
        checks['retained_workspace_capacity']=True

        runtime=HarnessRuntime(manager=BlockManager(),jev=DeterministicJevClient(),science=ScienceExecutor(),
            reasoner=DeterministicReasoner(),max_jev_calls=1,max_reasoner_calls=1)
        block=runtime.manager.allocate('kernel resource fixture','test',300)
        drained=LocalVenvScientificBackend(root/'drained',policy)
        transport(drained,archive({'run.py':b'import json,time\ntime.sleep(.25)\nprint(json.dumps({"values":{"value":4.0}}))\n'}))
        pending=asyncio.create_task(runtime.heavy_operation(block.block_id,drained.acquire_and_execute,request))
        while not drained.process_resources and not pending.done():await asyncio.sleep(.01)
        pending.cancel();await asyncio.sleep(.01)
        assert not pending.done()
        try:
            async with runtime.service_resources.heavy('director'):raise AssertionError('active science lease was released on cancellation')
        except ResourceBusy:pass
        returned=await pending
        assert returned.values=={'value':4.0} and runtime.service_resources.heavy_owner is None
        assert len(drained.process_resources)==5 and all(p['cleanup_confirmed'] for p in drained.process_resources)
        checks['cancelled_pipeline_drains_all_five_phases']=True

        experiment=Path(returned.receipt.environment['experiment_path'])
        padding=experiment/'inputs/memory-pad';padding.write_bytes(b'x'*80_000_000)
        (experiment/'repository/memory.py').write_text('data=bytearray(450000000)\nprint("unexpected")\n')
        try:drained._command(experiment,('python','memory.py'),'test')
        except SandboxError:pass
        else:raise AssertionError('aggregate scientific memory exceeded its cgroup')
        assert drained.process_resources[-1]['unit_observation']['Result']=='oom-kill',drained.process_resources[-1]
        assert padding.stat().st_size==80_000_000
        checks['aggregate_scientific_memory']=True

        slow=LocalVenvScientificBackend(root/'slow',policy.model_copy(update={'timeout_seconds':10}))
        transport(slow,archive({'run.py':b'import time\ntime.sleep(20)\n'}))
        started=time.monotonic();rejected(slow,request)
        proof=slow.process_resources[-1]
        assert time.monotonic()-started<20 and (proof.get('status')=='timed_out' or proof['unit_observation']['Result']=='timeout') and proof['cleanup_confirmed'],proof
        checks['whole_pipeline_wall_allowance']=True

        # Real transport, including a rejected complete received chunk. Headers
        # omit length, so reservation release/failed usage cannot rely on it.
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200);self.end_headers();self.wfile.write(b'x'*4096)
            def log_message(self,*_args):pass
        server=HTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        resources=ServiceResources(max_file_bytes=1000,max_block_download_bytes=1000,max_service_download_bytes=1000)
        received=LocalVenvScientificBackend(root/'received',policy,download_limit=1000)
        try:
            with resources.reserve_download('failed-block',None) as reservation:
                try:
                    received._fetch(f'http://127.0.0.1:{server.server_port}/fixture')
                finally:
                    try:reservation.consume(received.downloaded)
                    finally:resources.charge_download('failed-block',received.downloaded)
        except (SandboxError,ResourceRejected):pass
        finally:server.shutdown();server.server_close();thread.join()
        assert 1000<received.downloaded<=4096 and resources.downloaded_bytes==received.downloaded
        assert not resources.reservations
        try:
            with resources.reserve_download('fresh-block',None):raise AssertionError('fresh block reset failed service download usage')
        except ResourceRejected:pass
        checks['actual_failed_body_bytes_charged_and_reservation_released']=True

        from src.config.loader import load_models_config,load_runtime_config
        from src.config.models import RuntimeMode
        from src.runtime.pydantic_ai.factory import build_harness_runtime
        application=Path(__file__).resolve().parents[1]
        previous=os.environ.get('ONCOJEV_DATA_ROOT')
        os.environ['ONCOJEV_DATA_ROOT']=str(root/'factory')
        try:
            configured=build_harness_runtime(load_models_config(application/'config/models.yaml'),
                load_runtime_config(application/'config/runtime.yaml').model_copy(update={'mode':RuntimeMode.DETERMINISTIC}),environment={})
            owned=root/'factory/workspaces/owner'
            owned.mkdir(parents=True)
            (owned/'base-python').symlink_to(sys.executable)
            with configured.gdc.reserve('owner',1) as reservation:reservation.consume(1)
            assert not configured.service_resources.reservations
            for source in (configured.gdc,configured.xena,configured.literature):await source.aclose()
        finally:
            if previous is None:os.environ.pop('ONCOJEV_DATA_ROOT',None)
            else:os.environ['ONCOJEV_DATA_ROOT']=previous
        checks['actual_factory_reservation_ignores_external_link_bytes']=True
    print(json.dumps({'status':'passed','scope':'fixture transport, native WSL kernel controls; no model/provider or scientific utility','checks':checks}))


if __name__=='__main__':asyncio.run(main())
