"""TypeSafe/Jev adapters. The live client never fabricates a decision on failure."""

from collections.abc import Sequence
from typing import Protocol
import math
from src.provenance import canonical_bytes

import httpx2
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

from src.jev.failure import JevOperationalFailure, classify_jev_exception
from src.jev.models import (
    ChoiceDecision,
    JevDecision,
    JevExecutionFailure,
    JevFailureCategory,
    JevQuestionSpec,
    NoulDecision,
    ScoreDecision,
)


class JevClient(Protocol):
    def evaluate(self, state: dict, questions: Sequence[JevQuestionSpec]) -> tuple[JevDecision, ...]: ...


def _spec_for(question: JevQuestionSpec) -> Noul | Choice | Score:
    instructions = {"question": question.instructions, "known_exclusions": question.known_exclusions,
                    "failure_semantics": question.failure_semantics}
    if question.primitive == "noul":
        return Noul(instructions=instructions, criteria=question.criteria)
    if question.primitive == "choice":
        return Choice(instructions=instructions, criteria=question.criteria)
    return Score(instructions=instructions, criteria=question.criteria)


class JevBatch(tuple):
    def __new__(cls, decisions, metadata):
        value = super().__new__(cls, decisions)
        value.metadata = metadata
        return value


def _decision(question: JevQuestionSpec, context: dict, answer: object) -> JevDecision:
    if question.primitive == "noul":
        return NoulDecision(**context, p_true=answer.noul)
    if question.primitive == "choice":
        if set(answer.probabilities) != set(question.criteria) or answer.choice not in question.criteria:
            raise ValueError("Choice answer does not match declared criteria")
        return ChoiceDecision(
            **context,
            selected_option=answer.choice,
            probabilities=answer.probabilities,
            confidence=answer.confidence,
        )
    if set(answer.probabilities) != set(range(len(question.criteria))) or not math.isfinite(answer.score):
        raise ValueError("Score answer does not match declared levels")
    return ScoreDecision(
        **context,
        expected_score=answer.score,
        level_probabilities=answer.probabilities,
        confidence=answer.confidence,
    )


class TypeSafeJevClient:
    """Live TypeSafe System One measurement; failures are operational, never judgments."""

    def __init__(
        self, api_key: str | None, model: str, http2: bool = True, base_url: str | None = None,
        max_questions: int = 100, max_payload_bytes: int = 131072,
    ) -> None:
        self._client = TypeSafeClient(
            api_key=api_key,
            model=model,
            base_url=base_url,
            http_client=httpx2.Client(http2=True) if http2 else None,
        )
        self._model = model
        self.model_requested = model
        self.max_questions = max_questions
        self.max_payload_bytes = max_payload_bytes

    def evaluate(self, state: dict, questions: Sequence[JevQuestionSpec]) -> tuple[JevDecision, ...]:
        stage = "construction"
        decisions = []
        metadata = None
        try:
            if not 1 <= len(questions) <= self.max_questions:
                raise ValueError("question batch exceeds configured count bound")
            if len({q.question_id for q in questions}) != len(questions):
                raise ValueError("duplicate question IDs are forbidden")
            specs = {question.question_id: _spec_for(question) for question in questions}
            if len(canonical_bytes({"state": state, "questions": {k: v.model_dump(mode="json") for k, v in specs.items()}})) > self.max_payload_bytes:
                raise ValueError("Jev request exceeds configured byte bound")
            stage = "provider"
            response = self._client.system_one(state, specs)
            stage = "decoding"
            usage = getattr(response, "usage", None)
            metadata = {"usage": usage.model_dump(mode="json") if hasattr(usage, "model_dump") else None,
                        "reported_retries": None, "model_resolved": response.model}
            for question in questions:
                answer = response.answers.get(question.question_id)
                if answer is None:
                    raise ValueError("missing Jev answer")
                probabilities = getattr(answer, "probabilities", None)
                if probabilities is not None:
                    if not probabilities or any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities.values()) or abs(sum(probabilities.values()) - 1) > 1e-5:
                        raise ValueError("invalid native probability distribution")
                context = dict(question_id=question.question_id, model_requested=self._model,
                               model_resolved=response.model, question_version=question.question_version,
                               projection_id=question.projection_id)
                decisions.append(_decision(question, context, answer))
            return JevBatch(decisions, metadata)
        except Exception as error:  # noqa: BLE001 - any provider error is operational
            category = JevFailureCategory.VALIDATION if stage != "provider" else classify_jev_exception(error)
            raise JevOperationalFailure(
                tuple(
                    JevExecutionFailure(question_id=question_id, category=category, detail=f"{stage}:{type(error).__name__}")
                    for question_id in (tuple(q.question_id for q in questions if q.question_id not in {d.question_id for d in decisions}) or ("__batch__",))
                ), decisions=decisions, metadata=metadata,
            ) from error


class DeterministicJevClient:
    """Fixture client for tests and deterministic mode; requires no credential."""
    model_requested = "deterministic-fixture"

    def evaluate(self, state: dict, questions: Sequence[JevQuestionSpec]) -> tuple[JevDecision, ...]:
        out: list[JevDecision] = []
        for question in questions:
            context = dict(
                question_id=question.question_id,
                model_requested="deterministic-fixture",
                model_resolved="deterministic-fixture",
                question_version=question.question_version,
                projection_id=question.projection_id,
            )
            if question.primitive == "noul":
                out.append(NoulDecision(**context, p_true=0.72))
            elif question.primitive == "choice":
                out.append(
                    ChoiceDecision(
                        **context,
                        selected_option=next(iter(question.criteria)),
                        probabilities={key:1/len(question.criteria) for key in question.criteria},
                        confidence=1/len(question.criteria),
                    )
                )
            else:
                out.append(
                    ScoreDecision(
                        **context,
                        expected_score=(len(question.criteria)-1)/2,
                        level_probabilities={i:1/len(question.criteria) for i in range(len(question.criteria))},
                        confidence=1/len(question.criteria),
                    )
                )
        return tuple(out)
