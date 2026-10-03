"""Coder shell tool with Python-owned foreground execution, never detached jobs."""
from typing import Literal

from pydantic_ai.capabilities import Capability
from pydantic_ai.tools import RunContext


async def shell(ctx: RunContext, command: str, *, mode: Literal["foreground", "background"] = "foreground",
                timeout: float | None = None) -> dict:
    """Run bounded scratch code to completion; Python owns waiting and cleanup.

    Commands cannot detach across tools or runs. Use typed tools for acquisition
    and scientific work; scratch has no network or scientific admission authority.
    """
    if mode != "foreground":
        return {"status": "resource_rejected", "reason": "detached_scratch_commands_are_unsupported",
                "scientific_negative": False, "retryable": False}
    result = await ctx.workspace.run(command, shell=True, timeout=timeout)
    return {"exit_code": result.exit_code, "stdout": result.stdout, "stderr": result.stderr,
            "origin": "scratch", "scientific_negative": False, "retryable": False}


def owned_shell():
    return Capability(id="owned_shell", tools=[shell],
        instructions="Scratch shell is foreground-only and network-disabled. Python owns its wait and all descendant cleanup; no polling or detached work. Acquisition uses typed tools.")
