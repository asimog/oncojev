"""Verify both Coder/Code Mode roles directly on Linux, including local WSL2.

The historical filename is retained; no container runtime is invoked.
"""

from __future__ import annotations

import json
import os
import shlex
import sys
from pathlib import Path
from uuid import uuid4
from src.runtime.paths import data_root, director_root as director_path, workspace_root

from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import DeltaToolCall, FunctionModel

from src.block.manager import BlockManager
from src.director.models import ResourceAllocation
from src.jev.client import DeterministicJevClient
from src.reasoner.service import DeterministicReasoner
from src.runtime.pydantic_ai.agents import create_agents
from src.runtime.pydantic_ai.contracts import DirectorDeps, HarnessRuntime, ResearcherDeps
from src.science.execution import ScienceExecutor

APPLICATION = Path(__file__).resolve().parents[1]


def _as_stream(respond):
    """Coder bundles RepoContext, so runs are streamed; adapt a scripted response."""

    async def stream(messages, info):
        response = await respond(messages, info)
        tool_calls = {
            index: part for index, part in enumerate(response.parts) if isinstance(part, ToolCallPart)
        }
        if tool_calls:
            yield {
                index: DeltaToolCall(name=part.tool_name, json_args=part.args_as_json_str(), tool_call_id=part.tool_call_id)
                for index, part in tool_calls.items()
            }
            return
        text = "".join(part.content for part in response.parts if isinstance(part, TextPart))
        if text:
            yield text

    return stream


def _model(role: str, peer: Path, secret: Path, proof_root: Path, block_peer: Path):
    calls = 0

    async def respond(_messages, info):
        nonlocal calls
        calls += 1
        tools = {tool.name for tool in info.function_tools}
        assert {"list_files", "shell", "run_code"} <= tools
        if calls == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "write_file",
                        {"path": "coder-write-proof.txt", "content": f"{role} workspace is writable\n"},
                        tool_call_id=f"{role}-write",
                    )
                ]
            )
        if calls == 2:
            return ModelResponse(parts=[ToolCallPart("read_file", {"path": str(APPLICATION / "config/runtime.yaml")}, tool_call_id=f"{role}-read-app")])
        if calls == 3:
            return ModelResponse(parts=[ToolCallPart("write_file", {"path": str(peer / "native-write-denied.txt"), "content": "denied"}, tool_call_id=f"{role}-native-denial")])
        if calls == 4:
            code = f'''
import json, os, pathlib, subprocess, sys
p = pathlib.Path
def denied(operation):
    try:
        operation()
    except OSError as error:
        if error.errno in (1, 13, 30):
            return True
        raise
    return False
def open_write(path):
    with open(path, "r+"):
        pass
own = p.cwd()
(own / "shell-write-proof.txt").write_text("writable")
(own / "app-alias").symlink_to("/app/config/runtime.yaml")
checks = {{
    "own_shell_write": (own / "shell-write-proof.txt").read_text() == "writable",
    "application_readable": "default_seconds" in p("/app/config/runtime.yaml").read_text(),
    "application_write_denied": denied(lambda: open_write("/app/config/runtime.yaml")),
    "interpreter_library_write_denied": denied(lambda: open_write(json.__file__)),
    "application_symlink_write_denied": denied(lambda: open_write(own / "app-alias")),
    "production_source_write_denied": denied(lambda: open_write("/app/src/director/agent.py")),
    "questions_write_denied": denied(lambda: open_write("/app/src/jev/questions.py")),
    "policy_write_denied": denied(lambda: open_write("/app/src/jev/frontier.py")),
    "registry_write_denied": denied(lambda: open_write("/app/src/oncolab/catalogue.py")),
    "deployment_write_denied": denied(lambda: open_write("/app/railway.toml")),
    "database_read_denied": denied(lambda: p("/app/var/authoritative-db-sentinel").read_bytes()),
    "database_write_denied": denied(lambda: open_write("/app/var/authoritative-db-sentinel")),
    "peer_write_denied": denied(lambda: (p({str(peer)!r}) / "shell-write-denied.txt").write_text("denied")),
    "other_block_write_denied": denied(lambda: (p({str(block_peer)!r}) / "other-block-write-denied.txt").write_text("denied")),
    "peer_read_denied": denied(lambda: (p({str(peer)!r}) / "peer-private.txt").read_text()),
    "credential_file_denied": denied(lambda: p({str(secret)!r}).read_text()),
    "proc_environment_denied": denied(lambda: p("/proc/1/environ").read_bytes()),
    "provider_environment_absent": not any(name in os.environ for name in ("OPENROUTER_API_KEY", "TYPESAFE_API_KEY", "LOGFIRE_TOKEN", "AWS_SECRET_ACCESS_KEY", "GH_TOKEN", "GITHUB_TOKEN", "ONCOJEV_DB_PATH", "ONCOJEV_DATABASE_URL", "ONCOJEV_MIGRATION_DATABASE_URL", "ONCOJEV_WRITER_PASSWORD")),
    "publisher_credential_denied": denied(lambda: p("/app/var/publisher-credential-sentinel").read_text()),
}}
child = subprocess.run([sys.executable, "-c", "from pathlib import Path; Path(" + repr(str(p({str(peer)!r}) / "child-write-denied.txt")) + ").write_text('denied')"], capture_output=True)
checks["descendant_write_denied"] = child.returncode != 0 and b"PermissionError" in child.stderr
allowed_child = subprocess.run([sys.executable, "-c", "from pathlib import Path; Path('child-own-proof.txt').write_text('writable')"], capture_output=True)
checks["descendant_own_write"] = allowed_child.returncode == 0 and (own / "child-own-proof.txt").exists()
(own / "boundary-check.json").write_text(json.dumps(checks))
assert all(checks.values())
'''
            code = code.replace('"/app/var/', '"' + str(proof_root) + '/')
            code = code.replace('"/app/', '"' + str(APPLICATION) + '/')
            command = shlex.quote(sys.executable) + " -c " + shlex.quote(code)
            return ModelResponse(parts=[ToolCallPart("shell", {"command": command}, tool_call_id=f"{role}-shell")])
        if calls == 5:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "run_code",
                        {"code": f'await search_oncolab(query="GDC", kinds=["source"], limit=1)\n"{role} code mode complete"'},
                        tool_call_id=f"{role}-code-mode",
                    )
                ]
            )
        return ModelResponse(parts=[TextPart(f"{role} complete")])

    return FunctionModel(function=respond, stream_function=_as_stream(respond))


def main() -> None:
    # Every negative control must target a real file, not a missing path.
    for relative in ("src/director/agent.py", "src/jev/questions.py", "src/jev/frontier.py",
                     "src/oncolab/catalogue.py", "config/runtime.yaml", "railway.toml"):
        assert (APPLICATION / relative).is_file(), relative
    runtime = HarnessRuntime(
        manager=BlockManager(),
        jev=DeterministicJevClient(),
        science=ScienceExecutor(),
        reasoner=DeterministicReasoner(),
        max_jev_calls=2,
        max_reasoner_calls=1,
    )
    from src.config.loader import load_runtime_config
    from src.runtime.resources import ServiceResources
    runtime.service_resources = ServiceResources.from_policy(load_runtime_config(APPLICATION / "config/runtime.yaml"))
    block = runtime.manager.create("Coder smoke block", "verify harness composition", ResourceAllocation(seconds=3600))
    runtime.research_state.start(block.block_id, block.objective)
    runtime.skills.start(block.block_id)
    proof_root = data_root(APPLICATION) / "verification" / str(uuid4())
    proof_root.mkdir(parents=True)
    os.environ["ONCOJEV_DATA_ROOT"] = str(proof_root)
    agents = create_agents("test", "test")
    director_root = director_path(APPLICATION)
    researcher_root = workspace_root(APPLICATION) / block.block_id
    peer = workspace_root(APPLICATION) / "peer"
    peer.mkdir(parents=True)
    (peer / "peer-private.txt").write_text("fake private block data")
    secret = proof_root / "provider-secret-sentinel"
    secret.write_text("fake secret sentinel")
    (proof_root / "authoritative-db-sentinel").write_text("fake authoritative records")
    (proof_root / "publisher-credential-sentinel").write_text("fake publisher credential")
    director_root.mkdir(parents=True, exist_ok=True)
    (director_root / "peer-private.txt").write_text("fake Director scratch data")
    for name in ("OPENROUTER_API_KEY", "TYPESAFE_API_KEY", "LOGFIRE_TOKEN", "AWS_SECRET_ACCESS_KEY", "GH_TOKEN", "GITHUB_TOKEN", "ONCOJEV_DB_PATH", "ONCOJEV_DATABASE_URL", "ONCOJEV_MIGRATION_DATABASE_URL", "ONCOJEV_WRITER_PASSWORD"):
        os.environ[name] = "fake-verifier-sentinel"

    with agents.director.override(model=_model("director", peer, secret, proof_root, peer)):
        director = agents.director.run_sync("Inspect the workspace and OncoLab Index.", deps=DirectorDeps(runtime))
    researcher_agent = agents.fresh_researcher(block.block_id)
    with researcher_agent.override(model=_model("researcher", director_root, secret, proof_root, peer)):
        researcher = researcher_agent.run_sync(
            "Inspect the workspace and OncoLab Index.", deps=ResearcherDeps(runtime, block.block_id)
        )

    assert director.output == "director complete"
    assert researcher.output == "researcher complete"
    for result in (director, researcher):
        read_results = [part.content for message in result.new_messages() for part in message.parts
                        if isinstance(part, ToolReturnPart) and part.tool_name == "read_file"]
        assert any("default_seconds" in json.dumps(content, default=str) for content in read_results), read_results
    assert (director_root / "coder-write-proof.txt").exists(), [part.content for message in director.new_messages()
        for part in message.parts if getattr(part, "tool_name", None) == "write_file" and hasattr(part, "content")]
    assert (director_root / "coder-write-proof.txt").read_text() == "director workspace is writable\n"
    researcher_proof = researcher_root / "coder-write-proof.txt"
    assert researcher_proof.read_text() == "researcher workspace is writable\n"
    for result, root in ((director, director_root), (researcher, researcher_root)):
        if not (root / "boundary-check.json").exists():
            shell_results = [part.content for message in result.new_messages() for part in message.parts
                             if isinstance(part, ToolReturnPart) and part.tool_name == "shell"]
            raise AssertionError(f"shell boundary proof missing: {shell_results}")
    results = {role: json.loads((root / "boundary-check.json").read_text())
               for role, root in (("director", director_root), ("researcher", researcher_root))}
    assert all(all(checks.values()) for checks in results.values())
    assert (proof_root / "authoritative-db-sentinel").read_text() == "fake authoritative records"
    assert not (peer / "native-write-denied.txt").exists()
    assert not (director_root / "native-write-denied.txt").exists()
    print(json.dumps(results, sort_keys=True))


if __name__ == "__main__":
    main()
