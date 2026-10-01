"""Versioned local measurement contracts. Primitives do not choose actions.

Cookbook patterns: skill suggestion (absolute per-candidate fit), reranking
(retrieve first), citation checking (statement-specific support), parallel
questions (independent dimensions share bounded state).
"""
from typing import Literal
from src.jev.models import JevQuestionSpec
from src.provenance import content_hash

SemanticContext = Literal["method", "representation", "hypothesis", "memory", "statement"]
VERSION = "semantic-contracts-v1"
DIMENSIONS = {
    "method": {
        "estimand_fit": "Does `contract` estimate the target quantity in `need`, rather than merely a related descriptive quantity?",
        "design_fit": "Are the declared design and assumptions of `contract` compatible with `need`?",
        "variable_fit": "Do the semantic meanings of required variables match `need`? Actual input presence is checked separately in `checks`.",
        "limitations_fit": "Are the contract's limitations and missingness semantics compatible with the need without overstating what it can infer?",
    },
    "representation": {
        "sufficiency": "Can the actually available `representation` address `need`, respecting its unit, coverage, missingness and limitations?",
        "assumption_fit": "Does using this representation preserve the design/estimand assumptions in `need`?",
    },
    "hypothesis": {
        "test_alignment": "Does `proposed_test` actually test `hypothesis` for the target estimand in `objective`?",
        "duplication": "Is `hypothesis` substantively the same investigation as one of `prior_hypotheses`, rather than an independent replication or distinct test?",
    },
    "memory": {
        "relevance": "Does `memory` materially inform the current `objective`?",
        "duplication": "Does this memory duplicate the same investigation or uncertainty in the other retrieved context?",
        "contradiction": "Does this memory materially conflict with a statement in `comparison`, respecting different populations, epistemic types and failures?",
        "capability_gap": "Does this memory reveal a recurring unmet capability relevant to `objective`?",
        "actionability": "Does the available current context make a previously blocked uncertainty actionable for allocation review? This grants no execution authority.",
    },
}


def semantic_questions(context: SemanticContext, identity: str, projection_id: str) -> tuple[JevQuestionSpec, ...]:
    if context == "statement":
        definitions = (
            ("support", "choice", "How does `resolved_support` relate to this exact `statement`, its epistemic type and scientific limitations?",
             {"supports": "Support establishes this exact statement within its declared scope.",
              "contradicts": "Support contradicts this exact statement.",
              "unaddressed": "Support does not establish the statement; missing is not contradiction."}),
            ("overstatement", "noul", "Does `statement` overstate the scientific or epistemic scope of `resolved_support`?",
             {"true": "Statement claims more than the supplied support permits.", "false": "Statement stays within support's scope."}),
        )
    else:
        definitions = tuple((name,"noul",instruction,
            {"true":"The specified semantic property holds on the supplied bounded context.",
             "false":"The supplied context explicitly indicates that this property does not hold."})
            for name,instruction in DIMENSIONS[context].items())
    key=content_hash({"context":context,"identity":identity})[:16]
    return tuple(JevQuestionSpec(question_id=f"{key}:{name}",semantic_purpose=f"{context}.{name}",primitive=primitive,
        projection_id=projection_id,question_version=VERSION,
        instructions={"question":instruction,"uncertainty":"Missing information is unknown. Do not infer false from absence or operational failure."},
        criteria=criteria,known_exclusions=("Not evidence, execution permission or allocation authority.",),
        provenance=(VERSION,context)) for name,primitive,instruction,criteria in definitions)
