"""Direct WSL2 owning-boundary checks; fixtures never certify scientific utility."""
import asyncio
import errno
import json
import os
from pathlib import Path
import signal
import sys
import tempfile

from src.block.manager import BlockManager
from src.jev.client import DeterministicJevClient
from src.reasoner.service import DeterministicReasoner
from src.runtime.pydantic_ai.contracts import HarnessRuntime
from src.runtime.pydantic_ai.workspace import ConfinedBackend
from src.runtime.resources import ResourceBusy
from src.science.execution import ScienceExecutor


async def main():
    application = Path(__file__).resolve().parents[1]
    runtime = HarnessRuntime(manager=BlockManager(), jev=DeterministicJevClient(), science=ScienceExecutor(),
        reasoner=DeterministicReasoner(), max_jev_calls=1, max_reasoner_calls=1)
    resources = runtime.service_resources
    resources.max_workspace_bytes = 2_000_000
    resources.max_coder_memory_mb = 128
    resources.max_coder_processes = 8
    resources.max_coder_cpu = 1
    resources.max_coder_seconds = 5
    checks = {}
    with tempfile.TemporaryDirectory(prefix="oncojev-resource-proof-") as directory:
        root = Path(directory)
        workspace = root / "workspace"
        workspace.mkdir()
        original = workspace / "original"
        original.write_text("retained scratch")
        backend = ConfinedBackend(workspace, application, runtime)

        async def execute(code):
            return await backend.run([sys.executable, "-c", code])

        # This fails against the prior backend: a new-session child survives the
        # parent and escapes its process group. Always clean the fixture on failure.
        detached = await execute('import subprocess,sys; from pathlib import Path; '
            'p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"],'
            'start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); '
            'Path("child.pid").write_text(str(p.pid))')
        assert detached.exit_code == 0, detached.stderr
        child = int((workspace / "child.pid").read_text())
        try:
            assert not Path(f"/proc/{child}").exists(), "detached child survived command/lease return"
        finally:
            if Path(f"/proc/{child}").exists():
                # This fixture's exact PID sleeps 30s; no arbitrary process is
                # selected and the assertion/cleanup happens immediately.
                os.kill(child, signal.SIGKILL)
        assert resources.heavy_owner is None
        checks["descendants_drained"] = True

        literal = await backend.run('value=literal; printf "%s" "$value"', shell=True)
        assert literal.stdout == "literal", literal
        checks["shell_literals_preserved"] = True

        processes = await execute('import subprocess,sys,errno,json; children=[]\n'
            'try:\n'
            ' for _ in range(32): children.append(subprocess.Popen([sys.executable,"-c","import time; time.sleep(10)"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))\n'
            'except OSError as e: print(json.dumps({"errno":e.errno,"children":len(children)}))\n')
        assert processes.exit_code == 0, processes.stderr
        observed = json.loads(processes.stdout)
        assert observed["errno"] == errno.EAGAIN and 0 < observed["children"] < 32, observed
        pids = resources.receipts[-1]["process_resources"]["pids_peak"]
        assert pids <= resources.max_coder_processes, pids
        checks["process_count"] = True

        disk = await execute('import json; from pathlib import Path\n'
            'try:\n'
            ' for n in range(10): Path("disk-"+str(n)).write_bytes(b"x"*500000)\n'
            'except OSError as e: print(json.dumps({"errno":e.errno}))\n')
        assert disk.exit_code == 0, disk.stderr
        assert json.loads(disk.stdout)["errno"] in {errno.ENOSPC, errno.EDQUOT}
        assert resources.receipts[-1]["process_resources"]["workspace_after_bytes"] <= resources.max_workspace_bytes
        # Remove only this fixture's exact file names before later quota cases.
        for path in workspace.glob("disk-*"): path.unlink()
        checks["aggregate_disk_quota"] = True

        cpu = await execute('import subprocess,sys\n'
            'code="import time; start=time.process_time(); exec(\\\"while time.process_time()-start<0.3: pass\\\")"\n'
            'children=[subprocess.Popen([sys.executable,"-c",code]) for _ in range(3)]\n'
            'assert all(p.wait()==0 for p in children)\n')
        assert cpu.exit_code == 0, cpu.stderr
        stats = dict(line.split() for line in resources.receipts[-1]["process_resources"]["cpu_stat"].splitlines())
        assert int(stats["nr_throttled"]) > 0, stats
        checks["aggregate_cpu_rate"] = True

        memory = await execute('import subprocess,sys,time\n'
            'code="import time; data=bytearray(50000000); time.sleep(10)"\n'
            'children=[subprocess.Popen([sys.executable,"-c",code]) for _ in range(3)]\n'
            'time.sleep(4)\n')
        proof = resources.receipts[-1]["process_resources"]
        assert memory.exit_code != 0 and proof["kernel_controls_verified"] is True
        assert proof["unit_observation"]["Result"] == "oom-kill", proof
        assert original.read_text() == "retained scratch"
        checks["aggregate_memory"] = True

        resources.max_coder_seconds = 1
        timed = await execute('import time; time.sleep(10)')
        proof = resources.receipts[-1]["process_resources"]
        assert timed.exit_code != 0 and (proof.get("status") == "timed_out" or proof["unit_observation"]["Result"] == "timeout"), proof
        assert resources.heavy_owner is None and original.read_text() == "retained scratch"
        checks["wall_timeout_cleanup"] = True
        resources.max_coder_seconds = 5

        pending = asyncio.create_task(execute('import time; time.sleep(.5); print("returned")'))
        while resources.heavy_owner is None and not pending.done(): await asyncio.sleep(.01)
        pending.cancel()
        await asyncio.sleep(.01)
        assert not pending.done()
        try:
            async with resources.heavy("competing-science"):
                raise AssertionError("cancelled command released its live lease")
        except ResourceBusy: pass
        returned = await pending
        assert returned.exit_code == 0 and returned.stdout.strip() == "returned", returned
        assert resources.heavy_owner is None
        checks["cancellation_lease"] = True

        network = await execute('import socket,json\n'
            'try: socket.socket()\n'
            'except OSError as e: print(json.dumps({"errno":e.errno}))\n')
        assert network.exit_code == 0 and json.loads(network.stdout)["errno"] == errno.EPERM
        checks["unmetered_network_denied"] = True

        secret = root / "secret-sentinel"
        secret.write_text("private-output-sentinel")
        output = await execute(f'import os; from pathlib import Path; os.unlink(".owned-stdout"); '
            f'os.symlink({str(secret)!r},".owned-stdout"); print("safe output")')
        assert output.exit_code == 0 and output.stdout.strip() == "safe output", output
        assert "private-output-sentinel" not in output.stdout + output.stderr
        checks["stdout_path_replacement"] = True

        # An existing scratch pointer must not make the trusted supervisor open
        # or truncate a file beyond scratch before it applies command confinement.
        existing_secret = root / "existing-output-secret"
        existing_secret.write_text("retained-private-sentinel")
        existing_pointer = workspace / ".owned-stdout"
        existing_pointer.symlink_to(existing_secret)
        guarded = await execute('print("must not launch")')
        assert existing_secret.read_text() == "retained-private-sentinel", "trusted stdout creation followed an existing scratch symlink"
        assert guarded.exit_code != 0 and resources.heavy_owner is None
        existing_pointer.unlink(missing_ok=True)
        checks["existing_output_symlink"] = True
        assert original.read_text() == "retained scratch"
    print(json.dumps({"status": "passed", "scope": "actual native WSL2 Coder backend; no model/provider/scientific utility",
        "checks": checks, "executions": sum("process_resources" in r for r in resources.receipts)}))


if __name__ == "__main__": asyncio.run(main())
