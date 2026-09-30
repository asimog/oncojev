"""TypeSafe/Jev adapters. The live client never fabricates a decision on failure."""

from collections.abc import Sequence
from typing import Protocol

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
    if question.primitive == "noul":
        return Noul(instructions=question.instructions, criteria=question.criteria)
    if question.primitive == "choice":
        return Choice(instructions=question.instructions, criteria=question.criteria)
    return Score(instructions=question.instructions, criteria=question.criteria)


def _decision(question: JevQuestionSpec, context: dict, answer: object) -> JevDecision:
    if question.primitive == "noul":
        return NoulDecision(**context, p_true=answer.noul)
    if question.primitive == "choice":
        return ChoiceDecision(
            **context,
            selected_option=answer.choice,
            probabilities=answer.probabilities,
            confidence=answer.confidence,
        )
    return ScoreDecision(
        **context,
        expected_score=answer.score,
        level_probabilities=answer.probabilities,
        confidence=answer.confidence,
    )


class TypeSafeJevClient:
    """Live TypeSafe System One measurement; failures are operational, never judgments."""

    def __init__(
        self, api_key: str | None, model: str, http2: bool = True, base_url: str | None = None
    ) -> None:
        self._client = TypeSafeClient(
            api_key=api_key,
            model=model,
            base_url=base_url,
            http_client=httpx2.Client(http2=True) if http2 else None,
        )
        self._model = model

    def evaluate(self, state: dict, questions: Sequence[JevQuestionSpec]) -> tuple[JevDecision, ...]:
        specs = {question.question_id: _spec_for(question) for question in questions}
        try:
            response = self._client.system_one(state, specs)
        except Exception as error:  # noqa: BLE001 - any provider error is operational
            category = classify_jev_exception(error)
            raise JevOperationalFailure(
                tuple(
                    JevExecutionFailure(question_id=question.question_id, category=category, detail=type(error).__name__)
                    for question in questions
                )
            ) from error

        decisions: list[JevDecision] = []
        failures: list[JevExecutionFailure] = []
        for question in questions:
            answer = response.answers.get(question.question_id)
            if answer is None:
                failures.append(
                    JevExecutionFailure(
                        question_id=question.question_id,
                        category=JevFailureCategory.VALIDATION,
                        detail="no answer returned",
                    )
                )
                continue
            context = dict(
                question_id=question.question_id,
                model_requested=self._model,
                model_resolved=response.model,
                question_version=question.question_version,
                projection_id=question.projection_id,
            )
            decisions.append(_decision(question, context, answer))
        if failures:
            raise JevOperationalFailure(tuple(failures))
        return tuple(decisions)


class DeterministicJevClient:
    """Fixture client for tests and deterministic mode; requires no credential."""

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
                        selected_option="ADVANCE",
                        probabilities={"ADVANCE": 0.56, "DEFER": 0.44},
                        confidence=0.56,
                    )
                )
            else:
                out.append(
                    ScoreDecision(
                        **context,
                        expected_score=2.7,
                        level_probabilities={0: 0.05, 1: 0.1, 2: 0.2, 3: 0.45, 4: 0.2},
                        confidence=0.65,
                    )
                )
        return tuple(out)
