"""Small procedural labskills selected afresh for each OncoLab JevBlock."""

from pydantic import BaseModel, Field


class ResearchSkill(BaseModel, frozen=True):
    skill_id: str
    purpose: str
    triggers: tuple[str, ...]
    procedure: tuple[str, ...] = Field(min_length=1)
    provenance: tuple[str, ...] = Field(min_length=1)


SKILLS = (
    ResearchSkill(
        skill_id="statistical-method-selection",
        purpose="Select a statistical method from the estimand and study design.",
        triggers=("statistics", "regression", "comparison", "survival"),
        procedure=("State the estimand and population.", "Inspect design, sample size, missingness, and assumptions.", "Choose diagnostics and multiplicity handling before interpreting a result."),
        provenance=(".upstream/external/scientific-agent-skills/skills/statistical-analysis/SKILL.md", "skills/statistical-methods/README.md"),
    ),
    ResearchSkill(
        skill_id="scientific-visualization",
        purpose="Create an interpretable scientific figure with reproducible inputs.",
        triggers=("visualization", "figure", "plot", "matplotlib"),
        procedure=("Match visual encoding to the estimand.", "Show uncertainty and sample context where applicable.", "Persist a typed artifact and its input provenance; never treat the figure as evidence."),
        provenance=(".upstream/external/scientific-agent-skills/skills/scientific-visualization/SKILL.md", ".upstream/external/clawbio/skills/diff-visualizer/SKILL.md"),
    ),
    ResearchSkill(
        skill_id="literature-research",
        purpose="Retrieve and assess public scientific literature as contextual knowledge.",
        triggers=("literature", "publication", "paper", "knowledge"),
        procedure=("Search primary and review sources separately.", "Retain query, source, and retrieval date.", "Treat literature as context and generate testable alternatives, not ScientificEvidence."),
        provenance=(".upstream/external/scientific-agent-skills/skills/literature-review/SKILL.md",),
    ),
    ResearchSkill(
        skill_id="bioinformatics-library-use",
        purpose="Use Biopython or scikit-bio with explicit biological representation semantics.",
        triggers=("biopython", "scikit-bio", "sequence", "phylogeny", "annotation"),
        procedure=("Declare reference assembly, identifier namespace, and sequence representation.", "Pin library and data versions.", "Validate a small known fixture before applying a method to acquired data."),
        provenance=(".upstream/external/scientific-agent-skills/skills/biopython/SKILL.md", ".upstream/external/scientific-agent-skills/skills/scikit-bio/SKILL.md"),
    ),
    ResearchSkill(
        skill_id="reproducible-external-method",
        purpose="Acquire and run a public scientific method without losing replay information.",
        triggers=("github", "external", "sandbox", "reproducibility", "software"),
        procedure=("Resolve an immutable commit before installation.", "Run only in the isolated sandbox with credential-free environment.", "Require a strict typed output and identical replay before Science validation."),
        provenance=(".upstream/external/clawbio/skills/profile-report/SKILL.md", ".upstream/external/scientific-agent-skills/skills/statistical-analysis/SKILL.md"),
    ),
)


class BlockSkillStore:
    """Block-scoped selections; no skill selection crosses a Researcher run."""

    def __init__(self) -> None:
        self._selected: dict[str, tuple[ResearchSkill, ...]] = {}

    def start(self, block_id: str) -> None:
        self._selected[block_id] = ()

    def select(self, block_id: str, need: str, limit: int = 3) -> tuple[ResearchSkill, ...]:
        if not 1 <= limit <= 5:
            raise ValueError("skill limit must be between 1 and 5")
        terms = frozenset(need.lower().replace("-", " ").split())
        ranked = sorted(
            ((len(terms.intersection(skill.triggers)), skill) for skill in SKILLS),
            key=lambda item: (-item[0], item[1].skill_id),
        )
        selected = tuple(skill for score, skill in ranked if score > 0)[:limit]
        self._selected.setdefault(block_id, ())
        self._selected[block_id] = tuple({skill.skill_id: skill for skill in (*self._selected[block_id], *selected)}.values())
        return selected

    def selected(self, block_id: str) -> tuple[ResearchSkill, ...]:
        return self._selected.get(block_id, ())
