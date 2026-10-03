"""Budgeted live Reasoner execution owned by the runtime integration."""

from src.reasoner.agent import LiveReasoner
from src.reasoner.agent import REASONER_INSTRUCTIONS
from src.reasoner.models import ReasonerOutput
from pydantic_ai import Agent
from pydantic_ai.usage import UsageLimits


class BudgetedLiveReasoner(LiveReasoner):
    def __init__(self, model, model_settings=None):
        from src.runtime.pydantic_ai.controls import RuntimeControls
        self._agent = Agent(model, name="oncojev-reasoner", instructions=REASONER_INSTRUCTIONS,
                            output_type=ReasonerOutput, deps_type=object, model_settings=model_settings,
                            capabilities=[RuntimeControls("reasoner")], defer_model_check=True)

    async def generate(self, objective, finding, *, usage=None, usage_limits=None, deps=None):
        # Retain the standalone service contract with an explicit finite cap;
        # autonomous calls always supply allocation and aggregate context.
        if usage_limits is None:
            usage_limits = UsageLimits(request_limit=10, tool_calls_limit=0)
        result = await self._agent.run(f"Objective: {objective}\nFinding: {finding}",
                                       usage=usage, usage_limits=usage_limits, deps=deps)
        return result.output
