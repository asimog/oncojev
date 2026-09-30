"""Reasoner as an independent sub-agent.

The Reasoner proposes interpretations and testable hypotheses. It never admits
evidence, never allocates scope, and never mutates block lifecycle. In
deterministic mode `DeterministicReasoner` stands in without any credential.
"""

from pydantic_ai import Agent

from src.reasoner.models import ReasonerOutput


REASONER_INSTRUCTIONS = (
    "You are the OncoJev Reasoner. Given an objective and a measured finding, produce a concise "
    "interpretation, an explicit uncertainty statement, and at least one testable hypothesis. "
    "Mark a hypothesis within_scope only when it can be tested inside the current block. Never state "
    "that a hypothesis is evidence, never invent measurements, and never propose new global scope "
    "as if it were already allocated."
)


class LiveReasoner:
    """A separate Pydantic AI sub-agent run; output is possibility, never evidence."""

    def __init__(self, model: object, model_settings: dict | None = None) -> None:
        self._agent: Agent[None, ReasonerOutput] = Agent(
            model,
            name="oncojev-reasoner",
            instructions=REASONER_INSTRUCTIONS,
            output_type=ReasonerOutput,
            model_settings=model_settings,
            defer_model_check=True,
        )

    def generate(self, objective: str, finding: str) -> ReasonerOutput:
        result = self._agent.run_sync(f"Objective: {objective}\nFinding: {finding}")
        return result.output
