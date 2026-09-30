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
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.science.models import MeasuredResult


GITHUB_URL = re.compile(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?")
SHA = re.compile(r"[0-9a-f]{40}")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_hash(value: object) -> str:
    return _sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


class SandboxPolicy(BaseModel, frozen=True):
    image: str = "python:3.12-slim"
    cpu: int = Field(default=2, ge=1, le=8)
    memory_mb: int = Field(default=4096, ge=512, le=32768)
    timeout_seconds: int = Field(default=300, ge=10, le=1800)


class GithubMethodRequest(BaseModel, frozen=True):
    repository_url: str
    requested_ref: str = "HEAD"
    install_command: tuple[str, ...] = ("python", "-m", "pip", "install", ".")
    test_command: tuple[str, ...]
    execute_command: tuple[str, ...]
    input_json: dict[str, Any]

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


class SandboxMeasurementCandidate(BaseModel, frozen=True):
    candidate_id: str
    receipt: SandboxReceipt
    values: dict[str, float]


class SandboxError(RuntimeError):
    pass


class DockerScientificSandbox:
    """Run external code only in a credential-free Docker container sequence."""

    def __init__(self, policy: SandboxPolicy | None = None, runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run) -> None:
        self.policy = policy or SandboxPolicy()
        self._runner = runner

    def acquire_and_execute(self, request: GithubMethodRequest) -> SandboxMeasurementCandidate:
        with tempfile.TemporaryDirectory(prefix="oncojev-sandbox-") as temporary:
            root = Path(temporary)
            environment = self._environment(root)
            commit = self._resolve_commit(request.repository_url, request.requested_ref, root, environment)
            repository = root / "repository"
            self._require_success("clone", self._run(("git", "clone", "--no-checkout", "--depth", "1", request.repository_url, str(repository)), root, environment))
            self._require_success("fetch", self._run(("git", "-C", str(repository), "fetch", "--depth", "1", "origin", commit), root, environment))
            self._require_success("checkout", self._run(("git", "-C", str(repository), "checkout", "--detach", commit), root, environment))
            input_file = root / "input.json"
            input_file.write_text(json.dumps(request.input_json, sort_keys=True), encoding="utf-8")
            venv = root / "venv"
            venv.mkdir()
            install = self._docker("bridge", repository, venv, input_file, request.install_command, root, environment, include_input=False)
            test = self._docker("none", repository, venv, input_file, request.test_command, root, environment, include_input=True)
            first = self._docker("none", repository, venv, input_file, request.execute_command, root, environment, include_input=True)
            replay = self._docker("none", repository, venv, input_file, request.execute_command, root, environment, include_input=True)
            for name, invocation in (("install", install), ("test", test), ("first run", first), ("replay", replay)):
                if invocation[0].exit_status != 0:
                    raise SandboxError(f"sandbox {name} failed with exit status {invocation[0].exit_status}")
            values = self._parse_replayed_output(first[1], replay[1])
            receipt = SandboxReceipt(
                repository_url=request.repository_url,
                commit_sha=commit,
                environment={"image": self.policy.image, "cpu": self.policy.cpu, "memory_mb": self.policy.memory_mb, "network": {"install": "bridge", "test_and_run": "none"}},
                environment_sha256=_canonical_hash({"image": self.policy.image, "cpu": self.policy.cpu, "memory_mb": self.policy.memory_mb}),
                input_sha256=_canonical_hash(request.input_json),
                install=install[0], test=test[0], first_run=first[0], replay_run=replay[0],
            )
            candidate_id = _canonical_hash({"repository": request.repository_url, "commit": commit, "input": receipt.input_sha256, "output": first[0].stdout_sha256})[:24]
            return SandboxMeasurementCandidate(candidate_id=candidate_id, receipt=receipt, values=values)

    def _environment(self, root: Path) -> dict[str, str]:
        return {"PATH": os.environ.get("PATH", ""), "HOME": str(root / "home"), "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0", "GIT_ALLOW_PROTOCOL": "https", "GIT_LFS_SKIP_SMUDGE": "1", "PIP_NO_INPUT": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1"}

    def _resolve_commit(self, repository_url: str, requested_ref: str, root: Path, environment: dict[str, str]) -> str:
        result = self._run(("git", "ls-remote", repository_url, requested_ref), root, environment)
        match = next((parts[0] for line in result.stdout.splitlines() if (parts := line.split()) and SHA.fullmatch(parts[0])), None)
        if result.returncode != 0 or match is None:
            raise SandboxError("could not resolve an immutable public Git commit")
        return match

    def _docker(self, network: str, repository: Path, venv: Path, input_file: Path, command: tuple[str, ...], root: Path, environment: dict[str, str], *, include_input: bool) -> tuple[SandboxInvocation, str]:
        mounts = ("-v", f"{repository}:/repo:ro", "-v", f"{venv}:/venv")
        if include_input:
            mounts = (*mounts, "-v", f"{input_file}:/input/request.json:ro")
        args = ("docker", "run", "--rm", "--network", network, "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "128", "--cpus", str(self.policy.cpu), "--memory", f"{self.policy.memory_mb}m", "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=256m", *mounts, "-w", "/repo", "-e", "HOME=/tmp/sandbox", "-e", "PYTHONNOUSERSITE=1", "-e", "PIP_NO_INPUT=1", "-e", "PATH=/venv/bin:/usr/local/bin:/usr/bin:/bin", self.policy.image, *command)
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
    return MeasuredResult(
        analysis_id=analysis_id,
        values=candidate.values,
        provenance=("sandbox-replay-v1", candidate.receipt.repository_url, candidate.receipt.commit_sha, candidate.receipt.input_sha256, candidate.receipt.first_run.stdout_sha256),
    )
