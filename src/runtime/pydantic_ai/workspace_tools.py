"""Windows-compatible raw workspace tools for Pydantic AI agents.

They are intentionally confined to the repository workspace. Secrets remain
outside the agent-visible surface; a container workspace can replace these when
one is available.
"""
from pathlib import Path
import subprocess

from pydantic_ai import Agent


def register_workspace_tools(agent: Agent, root: Path) -> None:
    root = root.resolve()
    def path_for(relative: str) -> Path:
        path = (root / relative).resolve()
        if root not in path.parents and path != root: raise ValueError("path escapes workspace")
        if path.name.startswith(".env"): raise ValueError("secret files are unavailable")
        return path

    @agent.tool_plain
    def read_workspace_file(path: str) -> str:
        """Read a UTF-8 workspace file, excluding secret environment files."""
        return path_for(path).read_text(encoding="utf-8")

    @agent.tool_plain
    def write_workspace_file(path: str, content: str) -> str:
        """Create or overwrite a UTF-8 workspace file, excluding secret environment files."""
        target = path_for(path); target.parent.mkdir(parents=True, exist_ok=True); target.write_text(content, encoding="utf-8"); return str(target.relative_to(root))

    @agent.tool_plain
    def list_workspace(path: str = ".") -> list[str]:
        """List one workspace directory without exposing secret environment files."""
        return sorted(item.name for item in path_for(path).iterdir() if not item.name.startswith(".env"))

    @agent.tool_plain
    def run_workspace_shell(command: str, timeout_seconds: int = 60) -> dict[str, str | int]:
        """Run a raw shell command in the workspace; secret-file references are rejected."""
        if ".env" in command: raise ValueError("secret files are unavailable")
        result = subprocess.run(command, cwd=root, shell=True, capture_output=True, text=True, timeout=timeout_seconds, env={"PATH": __import__("os").environ.get("PATH", "")})
        return {"exit_code": result.returncode, "stdout": result.stdout[-50000:], "stderr": result.stderr[-50000:]}
