"""Run inside Linux: actual local backend confinement and fresh replay proof."""
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile

from src.science.local import LocalVenvScientificBackend
from src.science.sandbox import GithubMethodRequest, SandboxPolicy, validate_sandbox_candidate


def main():
    application_config = Path(__file__).resolve().parents[1] / "config/runtime.yaml"
    assert application_config.is_file(), "application write control must target a real file"
    with tempfile.TemporaryDirectory(prefix="scientific-boundary-") as directory:
        root = Path(directory)
        secret = root / "service-secret"
        secret.write_text("never accessible to scientific code")
        peer = root / "peer"
        peer.mkdir()
        script = f'''import json, os, socket, subprocess, sys, importlib.util
from pathlib import Path
import errno
def denied(operation):
    try: operation()
    except OSError as error:
        if error.errno in (errno.EPERM, errno.EACCES, errno.EROFS): return
        raise
    raise AssertionError("external authority was available")
denied(lambda: Path({str(secret)!r}).read_text())
denied(lambda: Path({str(peer / "write")!r}).write_text("escaped"))
denied(lambda: Path({str(application_config)!r}).open("r+"))
denied(lambda: Path(json.__file__).open("r+"))
assert importlib.util.find_spec("httpx") is None, "application packages leaked into fresh experiment"
denied(lambda: socket.socket())
denied(lambda: subprocess.run(["/bin/true"]))
assert not any(key in os.environ for key in ("GITHUB_TOKEN", "OPENROUTER_API_KEY", "TYPESAFE_API_KEY", "ONCOJEV_DATABASE_URL", "ONCOJEV_MIGRATION_DATABASE_URL", "ONCOJEV_WRITER_PASSWORD"))
print(json.dumps({{"values": {{"value": 4.0}}}}))
'''
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w:gz") as tar:
            data = script.encode()
            member = tarfile.TarInfo("fixture/run.py")
            member.size = len(data)
            tar.addfile(member, io.BytesIO(data))
        data = archive.getvalue()
        backend = LocalVenvScientificBackend(root / "owned", SandboxPolicy(memory_mb=512, timeout_seconds=30))
        # Transport fixture isolates authority checks from public connectivity.
        def fetch(_url):
            backend.downloaded += len(data)
            return data
        backend._fetch = fetch
        request = GithubMethodRequest(repository_url="https://github.com/example/fixture", requested_ref="a" * 40,
            install_command=("python", "--version"), test_command=("python", "run.py"),
            execute_command=("python", "run.py"), input_json={"fixture": True})
        candidate = backend.acquire_and_execute(request)
        measured = validate_sandbox_candidate(candidate, "local-boundary-proof")
        replay = backend.replay(candidate)
        assert measured.values == {"value": 4.0}
        assert replay.receipt.environment["experiment_path"] != candidate.receipt.environment["experiment_path"]
        assert secret.read_text() == "never accessible to scientific code"
        assert not (peer / "write").exists()
        # Installation owns its fresh venv, including executable paths. A later
        # phase must confine even an executable replaced by installed software.
        experiment = Path(candidate.receipt.environment["experiment_path"])
        interpreter = experiment / "venv/bin/python"
        interpreter.unlink()
        interpreter.write_text(f'#!/bin/sh\nprintf escaped > {str(secret)!r}\nprintf "tampered interpreter ran\\n"\n', encoding="utf-8")
        interpreter.chmod(0o700)
        _, tampered_output = backend._command(experiment, request.execute_command, "execute")
        assert "tampered interpreter ran" in tampered_output, "control did not execute the modified interpreter"
        assert secret.read_text() == "never accessible to scientific code", "modified experiment interpreter executed before confinement"
        print(json.dumps({"status": "passed", "scope": "fixture transport; actual Linux executor and fresh environments",
            "environment": {key:value for key,value in candidate.receipt.environment.items() if key!="process_resources"},
            "resource_phases": [{"phase":p["phase"],"kernel_controls_verified":p["kernel_controls_verified"],
                "cleanup_confirmed":p["cleanup_confirmed"],"memory_peak":p["memory_peak"],"pids_peak":p["pids_peak"]}
                for p in candidate.receipt.environment["process_resources"]], "independent_replay": True,
            "secret_peer_app_network_process_denial": True, "modified_interpreter_remains_confined": True,
            "output_sha256": hashlib.sha256(candidate.output_json.encode()).hexdigest()}))


if __name__ == "__main__":
    main()
