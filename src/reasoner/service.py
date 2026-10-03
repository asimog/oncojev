"""Reasoner services. Both implementations return possibilities, never evidence."""

from typing import Protocol

from src.reasoner.models import Hypothesis, ReasonerOutput


class ReasonerService(Protocol):
    async def generate(self, objective: str, finding: str) -> ReasonerOutput: ...


class DeterministicReasoner:
    """Credential-free fixture used by deterministic mode and tests."""

    async def generate(self, objective: str, finding: str) -> ReasonerOutput:
        return ReasonerOutput(
            interpretation=finding,
            uncertainty="Replication needed.",
            hypotheses=(
                Hypothesis(hypothesis_id="within", statement="Replicate the association.", within_scope=True, proposed_test="replicate cohort"),
                Hypothesis(hypothesis_id="beyond", statement="Test a causal mechanism.", within_scope=False, proposed_test="mechanistic experiment"),
            ),
        )
