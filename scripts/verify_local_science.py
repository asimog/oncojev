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
    with tempfile.TemporaryDirectory(prefix="scientific-boundary-") as directory:
        root = Path(directory)
        secret = root / "service-secret"
        secret.write_text("never accessible to scientific code")
        peer = root / "peer"
        peer.mkdir()
        script = f'''import json, os, socket, subprocess
from pathlib import Path
def denied(operation):
    try: operation()
    except (OSError, PermissionError): return
    raise AssertionError("external authority was available")
denied(lambda: Path({str(secret)!r}).read_text())
denied(lambda: Path({str(peer / "write")!r}).write_text("escaped"))
denied(lambda: Path("/app/config/runtime.yaml").write_text("escaped"))
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
        print(json.dumps({"status": "passed", "scope": "fixture transport; actual Linux executor and fresh environments",
            "environment": candidate.receipt.environment, "independent_replay": True,
            "secret_peer_app_network_process_denial": True, "output_sha256": hashlib.sha256(candidate.output_json.encode()).hexdigest()}))


if __name__ == "__main__":
    main()
