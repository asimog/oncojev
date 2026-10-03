"""Credential-free Docker execution for public GitHub scientific software."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, computed_field

from src.science.models import MeasuredResult
from src.sources.models import ScientificArtifact
from src.provenance import content_hash


GITHUB_URL = re.compile(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?")
SHA = re.compile(r"[0-9a-f]{40}")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_hash(value: object) -> str:
    return content_hash(value)


class SandboxPolicy(BaseModel, frozen=True):
    image: str = "python:3.12-slim"
    cpu: int = Field(default=2, ge=1, le=8)
    memory_mb: int = Field(default=4096, ge=512, le=32768)
    timeout_seconds: int = Field(default=300, ge=10, le=1800)


class LockedWheel(BaseModel, frozen=True):
    url: str = Field(pattern=r"^https://files\.pythonhosted\.org/[^ ?#]+\.whl$")
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class GithubMethodRequest(BaseModel, frozen=True):
    repository_url: str
    requested_ref: str = "HEAD"
    install_command: tuple[str, ...] = ("python", "-m", "pip", "install", ".")
    test_command: tuple[str, ...]
    execute_command: tuple[str, ...]
    input_json: dict[str, Any]
    input_artifacts: tuple[ScientificArtifact,...] = ()
    dependency_wheels: tuple[LockedWheel,...] = Field(default=(), max_length=30)

    def input_identity(self) -> str:
        for artifact in self.input_artifacts:artifact.validate_bytes()
        if not self.input_artifacts:return _canonical_hash(self.input_json)
        return _canonical_hash({"json":self.input_json,"artifacts":[{"id":a.artifact_id,"sha256":a.byte_sha256,"size":a.size_bytes,"format":a.format} for a in self.input_artifacts]})

    @field_validator("repository_url")
    @classmethod
    def public_github_only(cls, value: str) -> str:
        if not GITHUB_URL.fullmatch(value):
            raise ValueError("only an HTTPS github.com owner/repository URL is allowed")
        return value.removesuffix(".git")

    @field_validator("requested_ref")
    @classmethod
    def safe_ref(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9._/-]{1,128}", value) or ".." in value:
            raise ValueError("requested_ref must be a simple Git reference")
        return value

    @field_validator("install_command", "test_command", "execute_command")
    @classmethod
    def shell_free_command(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value or value[0] not in {"python", "pytest"}:
            raise ValueError("commands must begin with python or pytest")
        if any(not argument or "\x00" in argument or any(token in argument for token in (";", "&&", "|", "`", "$(`")) for argument in value):
            raise ValueError("commands are argument lists, not shell expressions")
        if "-c" in value:
            raise ValueError("inline code is not allowed")
        return value


class SandboxInvocation(BaseModel, frozen=True):
    command: tuple[str, ...]
    exit_status: int
    stdout_sha256: str
    stderr_sha256: str
    effective_command: tuple[str,...] | None = None


class SandboxReceipt(BaseModel, frozen=True):
    repository_url: str
    commit_sha: str
    environment: dict[str, Any]
    environment_sha256: str
    input_sha256: str
    install: SandboxInvocation
    test: SandboxInvocation
    first_run: SandboxInvocation
    replay_run: SandboxInvocation
    bootstrap: SandboxInvocation | None = None


class SandboxMeasurementCandidate(BaseModel, frozen=True):
    candidate_id: str
    receipt: SandboxReceipt
    values: dict[str, float]
    request: GithubMethodRequest | None = None
    policy: SandboxPolicy | None = None
    output_json: str | None = None
    validator_version: str = "sandbox-validator-v2"

    @computed_field
    @property
    def content_sha256(self) -> str:
        identity = {"repository": self.receipt.repository_url, "commit": self.receipt.commit_sha,
            "input": self.receipt.input_sha256, "values": self.values, "image": self.receipt.environment.get("image"),
            "cpu": self.receipt.environment.get("cpu"), "memory_mb": self.receipt.environment.get("memory_mb"),
            "commands": [self.receipt.install.command, self.receipt.test.command, self.receipt.first_run.command]}
        if self.receipt.environment.get("backend") == "local_venv":
            identity["environment"] = self.receipt.environment_sha256
        return _canonical_hash(identity)


class SandboxError(RuntimeError):
    pass


class ScientificExecutionBackend(Protocol):
    def acquire_and_execute(self, request: GithubMethodRequest) -> SandboxMeasurementCandidate: ...
    def replay(self, candidate: SandboxMeasurementCandidate) -> SandboxMeasurementCandidate: ...


class DockerScientificSandbox:
    """Run external code only in a credential-free Docker container sequence."""

    def __init__(self, policy: SandboxPolicy | None = None, runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run, *, owned_parent: Path | None = None) -> None:
        self.policy = policy or SandboxPolicy()
        self._runner = runner
        self.owned_parent = owned_parent

    def acquire_and_execute(self, request: GithubMethodRequest) -> SandboxMeasurementCandidate:
        request.input_identity()  # Reject corrupted bytes before acquisition or execution.
        if self.owned_parent is not None:
            self.owned_parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="oncojev-sandbox-", dir=self.owned_parent) as temporary:
            root = Path(temporary)
            environment = self._environment(root)
            image = self._resolve_image(root, environment)
            commit = request.requested_ref if SHA.fullmatch(request.requested_ref) else self._resolve_commit(request.repository_url, request.requested_ref, root, environment)
            repository = root / "repository"
            self._require_success("clone", self._run(("git", "clone", "--no-checkout", "--depth", "1", request.repository_url, str(repository)), root, environment))
            self._require_success("fetch", self._run(("git", "-C", str(repository), "fetch", "--depth", "1", "origin", commit), root, environment))
            self._require_success("checkout", self._run(("git", "-C", str(repository), "checkout", "--detach", commit), root, environment))
            input_file = root / "input.json"
            input_file.write_text(json.dumps(request.input_json, sort_keys=True), encoding="utf-8")
            artifact_directory=root / "artifacts"
            artifact_directory.mkdir()
            for artifact in request.input_artifacts:
                (artifact_directory / artifact.byte_sha256).write_bytes(artifact.bytes())
            venv = root / "venv"
            venv.mkdir()
            bootstrap = self._docker("none", repository, venv, input_file, ("python", "-m", "venv", "/venv"), root, environment, image=image, include_input=False)
            if bootstrap[0].exit_status != 0:
                raise SandboxError("sandbox environment initialization failed")
            install = self._docker("bridge", repository, venv, input_file, request.install_command, root, environment, image=image, include_input=False)
            test = self._docker("none", repository, venv, input_file, request.test_command, root, environment, image=image, include_input=True)
            first = self._docker("none", repository, venv, input_file, request.execute_command, root, environment, image=image, include_input=True)
            replay = self._docker("none", repository, venv, input_file, request.execute_command, root, environment, image=image, include_input=True)
            for name, invocation in (("install", install), ("test", test), ("first run", first), ("replay", replay)):
                if invocation[0].exit_status != 0:
                    raise SandboxError(f"sandbox {name} failed with exit status {invocation[0].exit_status}")
            values = self._parse_replayed_output(first[1], replay[1])
            resolved_environment = {"image": image, "requested_image": self.policy.image, "cpu": self.policy.cpu,
                "memory_mb": self.policy.memory_mb, "network": {"install": "bridge", "test_and_run": "none"},
                "executor_version": "docker-scientific-v2", "dependency_lock": "install dependencies are not independently locked"}
            receipt = SandboxReceipt(
                repository_url=request.repository_url,
                commit_sha=commit,
                environment=resolved_environment,
                environment_sha256=_canonical_hash(resolved_environment),
                input_sha256=request.input_identity(),
                install=install[0], test=test[0], first_run=first[0], replay_run=replay[0], bootstrap=bootstrap[0],
            )
            candidate_id = str(uuid4())
            return SandboxMeasurementCandidate(candidate_id=candidate_id, receipt=receipt, values=values,
                request=request, policy=self.policy, output_json=first[1])

    def replay(self, candidate: SandboxMeasurementCandidate) -> SandboxMeasurementCandidate:
        """Explicit review operation; never called by recovery or Index loading."""
        validate_sandbox_candidate(candidate, "replay-preflight")
        policy = candidate.policy.model_copy(update={"image": candidate.receipt.environment["image"]})
        request = candidate.request.model_copy(update={"requested_ref": candidate.receipt.commit_sha})
        replayed = DockerScientificSandbox(policy, self._runner, owned_parent=self.owned_parent).acquire_and_execute(request)
        if replayed.receipt.first_run.stdout_sha256 != candidate.receipt.first_run.stdout_sha256:
            raise SandboxError("independent historical replay produced different output")
        return replayed

    def _resolve_image(self, root: Path, environment: dict[str, str]) -> str:
        arguments = ("docker", "image", "inspect", "--format", "{{.Id}}", self.policy.image)
        result = self._run(arguments, root, environment)
        if result.returncode != 0:
            self._require_success("image pull", self._run(("docker", "pull", self.policy.image), root, environment))
            result = self._run(arguments, root, environment)
        image = result.stdout.strip()
        if result.returncode or not re.fullmatch(r"sha256:[0-9a-f]{64}", image):
            raise SandboxError("could not resolve an immutable Docker image identity")
        return image

    def _environment(self, root: Path) -> dict[str, str]:
        return {"PATH": os.environ.get("PATH", ""), "HOME": str(root / "home"), "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0", "GIT_ALLOW_PROTOCOL": "https", "GIT_LFS_SKIP_SMUDGE": "1", "PIP_NO_INPUT": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1"}

    def _resolve_commit(self, repository_url: str, requested_ref: str, root: Path, environment: dict[str, str]) -> str:
        result = self._run(("git", "ls-remote", repository_url, requested_ref), root, environment)
        match = next((parts[0] for line in result.stdout.splitlines() if (parts := line.split()) and SHA.fullmatch(parts[0])), None)
        if result.returncode != 0 or match is None:
            raise SandboxError("could not resolve an immutable public Git commit")
        return match

    def _docker(self, network: str, repository: Path, venv: Path, input_file: Path, command: tuple[str, ...], root: Path, environment: dict[str, str], *, image: str, include_input: bool) -> tuple[SandboxInvocation, str]:
        mounts = ("-v", f"{repository}:/repo:ro", "-v", f"{venv}:/venv")
        if include_input:
            mounts = (*mounts, "-v", f"{input_file}:/input/request.json:ro", "-v", f"{root / 'artifacts'}:/input/artifacts:ro")
        args = ("docker", "run", "--rm", "--network", network, "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "128", "--cpus", str(self.policy.cpu), "--memory", f"{self.policy.memory_mb}m", "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=256m", *mounts, "-w", "/repo", "-e", "HOME=/tmp/sandbox", "-e", "PYTHONNOUSERSITE=1", "-e", "PIP_NO_INPUT=1", "-e", "PATH=/venv/bin:/usr/local/bin:/usr/bin:/bin", image, *command)
        result = self._run(args, root, environment)
        invocation = SandboxInvocation(command=command, exit_status=result.returncode, stdout_sha256=_sha256(result.stdout.encode()), stderr_sha256=_sha256(result.stderr.encode()))
        return invocation, result.stdout

    def _run(self, arguments: tuple[str, ...], cwd: Path, environment: dict[str, str]) -> subprocess.CompletedProcess[str]:
        try:
            return self._runner(arguments, cwd=cwd, env=environment, capture_output=True, text=True, timeout=self.policy.timeout_seconds, check=False)
        except FileNotFoundError as error:
            raise SandboxError("Docker and Git must be installed for public software acquisition") from error
        except subprocess.TimeoutExpired as error:
            raise SandboxError("sandbox command exceeded its time budget") from error

    @staticmethod
    def _require_success(name: str, result: subprocess.CompletedProcess[str]) -> None:
        if result.returncode != 0:
            raise SandboxError(f"sandbox {name} failed with exit status {result.returncode}")

    @staticmethod
    def _parse_replayed_output(first: str, replay: str) -> dict[str, float]:
        if _sha256(first.encode()) != _sha256(replay.encode()):
            raise SandboxError("sandbox output was not replay-stable")
        try:
            parsed = json.loads(first)
        except json.JSONDecodeError as error:
            raise SandboxError("sandbox stdout must be one JSON object") from error
        if set(parsed) != {"values"} or not isinstance(parsed["values"], dict) or not parsed["values"]:
            raise SandboxError("sandbox JSON must contain only a non-empty values object")
        values: dict[str, float] = {}
        for key, value in parsed["values"].items():
            if not isinstance(key, str) or not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
                raise SandboxError("sandbox values must be finite numeric measurements")
            values[key] = float(value)
        return values


def validate_sandbox_candidate(candidate: SandboxMeasurementCandidate, analysis_id: str) -> MeasuredResult:
    """The sole deterministic path from a replayed sandbox candidate to a measurement."""
    receipt = candidate.receipt
    if candidate.request is None or candidate.policy is None or candidate.output_json is None:
        raise SandboxError("candidate lacks replayable request, policy or output")
    if not SHA.fullmatch(receipt.commit_sha):raise SandboxError("candidate commit must be immutable")
    backend=receipt.environment.get('backend','docker')
    if backend=='docker':
        if not re.fullmatch(r"sha256:[0-9a-f]{64}",str(receipt.environment.get('image'))):
            raise SandboxError("candidate environment and commit must be immutable")
    elif backend=='local_venv':
        required=('python_sha256','archive_sha256','dependencies_sha256','executor_version','platform')
        if any(not receipt.environment.get(k) for k in required) or receipt.environment.get('network')!='disabled_for_install_test_execute':
            raise SandboxError('incomplete confined local environment identity')
        confinement=receipt.environment.get('confinement')
        if confinement not in {'landlock-seccomp-single-process-v1','landlock-seccomp-single-process-v2-trusted-launcher'}:
            raise SandboxError('unqualified local confinement')
        if confinement=='landlock-seccomp-single-process-v2-trusted-launcher' and receipt.environment.get('executor_version') not in {'local-venv-v3','local-venv-v4'}:
            raise SandboxError('local trusted launcher version mismatch')
        if receipt.environment.get('executor_version')=='local-venv-v4':
            resources=receipt.environment.get('process_resources',[])
            if (receipt.environment.get('aggregate_controls')!='owned-command-v1'
                or [r.get('phase') for r in resources]!=['prepare','install','test','execute','replay']
                or any(r.get('kernel_controls_verified') is not True or r.get('cleanup_confirmed') is not True
                       or r.get('workspace_committed') is not True or r.get('exit_code')!=0 for r in resources)):
                raise SandboxError('incomplete owned scientific resource proof')
        if receipt.environment.get('dependencies_sha256')!=content_hash([w.model_dump(mode='json') for w in candidate.request.dependency_wheels]):
            raise SandboxError('local dependency identity mismatch')
    else:raise SandboxError('unsupported scientific execution backend')
    if receipt.repository_url != candidate.request.repository_url or receipt.input_sha256 != candidate.request.input_identity():
        raise SandboxError("sandbox input identity mismatch")
    if receipt.environment_sha256 != _canonical_hash(receipt.environment):
        raise SandboxError("sandbox environment identity mismatch")
    if any(i.exit_status != 0 for i in (receipt.install, receipt.test, receipt.first_run, receipt.replay_run)):
        raise SandboxError("sandbox execution did not pass")
    if receipt.bootstrap is not None and receipt.bootstrap.exit_status != 0:
        raise SandboxError("sandbox environment initialization did not pass")
    if (receipt.install.command != candidate.request.install_command or receipt.test.command != candidate.request.test_command
            or receipt.first_run.command != candidate.request.execute_command or receipt.replay_run.command != candidate.request.execute_command):
        raise SandboxError("sandbox commands do not match retained request")
    if _sha256(candidate.output_json.encode()) != receipt.first_run.stdout_sha256 or receipt.first_run.stdout_sha256 != receipt.replay_run.stdout_sha256:
        raise SandboxError("sandbox output identity mismatch")
    if DockerScientificSandbox._parse_replayed_output(candidate.output_json, candidate.output_json) != candidate.values:
        raise SandboxError("sandbox measured values do not match retained output")
    return MeasuredResult(
        analysis_id=analysis_id,
        values=candidate.values,
        provenance=("sandbox-validator-v2", candidate.receipt.repository_url, candidate.receipt.commit_sha, candidate.receipt.input_sha256, candidate.receipt.first_run.stdout_sha256, receipt.environment_sha256),
        origin="sandbox",
        source_refs=(candidate.candidate_id,),
        input_sha256=candidate.receipt.input_sha256,
        limitations=("In-workspace replay passed; independent reinstall may differ because install dependencies are not locked.",),
    )
