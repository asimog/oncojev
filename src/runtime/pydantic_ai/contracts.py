"""Typed tool contracts exposed to Pydantic AI agents through Code Mode.

The harness is allowed to orchestrate these operations, but deterministic Python
remains the authority for deadlines, frontier policy, and evidence admission.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from pydantic_ai import Agent, RunContext

from src.block.manager import BlockManager
from src.block.models import BlockStatus
from src.capabilities.catalogue import initial_capability_registry
from src.capabilities.registry import CapabilityRegistry, ProvenCapabilityRecord
from src.capabilities.models import CapabilityKind
from src.director.models import ResourceAllocation
from src.jev.client import JevClient
from src.jev.frontier import FrontierPolicy
from src.jev.models import JevQuestionSpec
from src.ledger.events import LedgerEvent
from src.reasoner.service import DeterministicReasoner
from src.science.admission import admit_scientific_evidence
from src.science.execution import ScienceExecutor
from src.science.models import AnalysisSpec, MeasuredResult
from src.sources.public import GdcPublicSource, PublicLiteratureSource, XenaPublicSource
from src.visualization.service import line_figure
from src.researcher.state import ProjectionSpec, ResearchStateStore, StateFragment, project_state


@dataclass
class HarnessRuntime:
    manager: BlockManager
    jev: JevClient
    science: ScienceExecutor
    reasoner: DeterministicReasoner
    max_jev_calls: int
    max_reasoner_calls: int
    max_source_calls: int = 20
    capabilities: CapabilityRegistry = field(default_factory=initial_capability_registry)
    gdc: GdcPublicSource = field(default_factory=GdcPublicSource)
    xena: XenaPublicSource = field(default_factory=XenaPublicSource)
    literature: PublicLiteratureSource = field(default_factory=PublicLiteratureSource)
    measurements: dict[str, MeasuredResult] = field(default_factory=dict)
    research_state: ResearchStateStore = field(default_factory=ResearchStateStore)
    researcher: Agent["ResearcherDeps", str] | None = None
    _counts: dict[str, int] = field(default_factory=dict)

    def claim(self, resource: str, limit: int) -> None:
        count = self._counts.get(resource, 0) + 1
        if count > limit:
            raise RuntimeError(f"{resource} budget exhausted")
        self._counts[resource] = count


@dataclass(frozen=True)
class DirectorDeps:
    runtime: HarnessRuntime


@dataclass(frozen=True)
class ResearcherDeps:
    runtime: HarnessRuntime
    block_id: str


def register_director_tools(
    agent: Agent[DirectorDeps, str],
) -> None:
    @agent.tool
    async def search_capabilities(
        ctx: RunContext[DirectorDeps], query: str = "", kinds: list[CapabilityKind] = [], tags: list[str] = [], limit: int = 8
    ) -> list[dict[str, Any]]:
        """Search bounded capability planning metadata; this never executes science."""
        matches = ctx.deps.runtime.capabilities.search(query, kinds=kinds, tags=tags, limit=limit)
        return [match.model_dump(mode="json") for match in matches]

    @agent.tool
    async def describe_capability(ctx: RunContext[DirectorDeps], capability_id: str) -> dict[str, Any] | None:
        """Describe one capability; descriptor presence never grants execution authority."""
        match = ctx.deps.runtime.capabilities.describe(capability_id)
        return None if match is None else match.model_dump(mode="json")

    @agent.tool
    async def allocate_block(
        ctx: RunContext[DirectorDeps], objective: str, why_now: str, seconds: int
    ) -> dict[str, Any]:
        """Create a bounded block. Only BlockManager computes its deadline."""
        block = ctx.deps.runtime.manager.create(
            objective, why_now, ResourceAllocation(seconds=seconds)
        )
        ctx.deps.runtime.research_state.start(block.block_id, block.objective)
        ctx.deps.runtime.manager.ledger(block.block_id).append(
            LedgerEvent(
                event_type="DirectorBlockAllocated",
                occurred_at=datetime.now(UTC),
                payload={"objective": objective, "deadline": block.deadline.isoformat()},
            )
        )
        return block.model_dump(mode="json")

    @agent.tool
    async def inspect_block(
        ctx: RunContext[DirectorDeps], block_id: str
    ) -> dict[str, Any]:
        """Read lifecycle state and immutable ledger history for one block."""
        manager = ctx.deps.runtime.manager
        block = manager.block(block_id)
        return {
            "block": block.model_dump(mode="json"),
            "status": manager.status(block).value,
            "remaining_seconds": int(manager.remaining(block).total_seconds()),
            "ledger": [event.model_dump(mode="json") for event in manager.ledger(block_id).history()],
        }

    @agent.tool
    async def launch_researcher(
        ctx: RunContext[DirectorDeps], block_id: str
    ) -> str:
        """Run the separate Researcher agent inside an already allocated active block."""
        runtime = ctx.deps.runtime
        block = runtime.manager.block(block_id)
        if runtime.manager.status(block) is not BlockStatus.ACTIVE:
            raise RuntimeError("cannot launch a non-active block")
        if runtime.researcher is None:
            raise RuntimeError("Researcher agent is not configured")
        ledger = runtime.manager.ledger(block_id)
        ledger.append(LedgerEvent(event_type="ResearcherRunStarted", occurred_at=datetime.now(UTC), payload={"block_id": block_id}))
        try:
            result = await runtime.researcher.run(
                f"Investigate block {block_id}: {block.objective}",
                deps=ResearcherDeps(runtime=runtime, block_id=block_id),
                usage=ctx.usage,
            )
        except Exception as error:
            ledger.append(LedgerEvent(event_type="ResearcherRunFailed", occurred_at=datetime.now(UTC), payload={"error_type": type(error).__name__}))
            raise
        ledger.append(LedgerEvent(event_type="ResearcherRunCompleted", occurred_at=datetime.now(UTC), payload={"block_id": block_id}))
        return result.output


def register_researcher_tools(
    agent: Agent[ResearcherDeps, str],
) -> None:
    def block_for(ctx: RunContext[ResearcherDeps]):
        return ctx.deps.runtime.manager.block(ctx.deps.block_id)

    def append(ctx: RunContext[ResearcherDeps], event_type: str, payload: dict[str, Any]) -> None:
        ctx.deps.runtime.manager.ledger(ctx.deps.block_id).append(
            LedgerEvent(event_type=event_type, occurred_at=datetime.now(UTC), payload=payload)
        )

    def state(ctx: RunContext[ResearcherDeps]):
        try: return ctx.deps.runtime.research_state.get(ctx.deps.block_id)
        except KeyError: return ctx.deps.runtime.research_state.start(ctx.deps.block_id, block_for(ctx).objective)
    def save(ctx: RunContext[ResearcherDeps], value): return ctx.deps.runtime.research_state.put(value)

    @agent.tool
    async def inspect_research_state(ctx: RunContext[ResearcherDeps]) -> dict[str, Any]:
        """Read this block's immutable provider-agnostic state, not raw provider responses."""
        return state(ctx).model_dump(mode="json")

    @agent.tool
    async def record_candidate(ctx: RunContext[ResearcherDeps], candidate_id: str, summary: str) -> dict[str, Any]:
        """Add a local candidate before semantic measurement; this is not evidence."""
        updated = state(ctx).append("candidates", StateFragment(fragment_id=candidate_id, kind="candidate", summary=summary, provenance=("researcher",)))
        save(ctx, updated); return updated.model_dump(mode="json")

    @agent.tool
    async def search_capabilities(
        ctx: RunContext[ResearcherDeps], query: str = "", kinds: list[CapabilityKind] = [], tags: list[str] = [], limit: int = 8
    ) -> list[dict[str, Any]]:
        """Search the same bounded global index for local block planning; this never executes a result."""
        matches = ctx.deps.runtime.capabilities.search(query, kinds=kinds, tags=tags, limit=limit)
        return [match.model_dump(mode="json") for match in matches]

    @agent.tool
    async def describe_capability(ctx: RunContext[ResearcherDeps], capability_id: str) -> dict[str, Any] | None:
        """Describe one global capability before choosing a typed local wrapper."""
        match = ctx.deps.runtime.capabilities.describe(capability_id)
        return None if match is None else match.model_dump(mode="json")

    @agent.tool
    async def acquire_gdc(
        ctx: RunContext[ResearcherDeps], endpoint: str, filters: dict[str, Any], fields: list[str], size: int = 10
    ) -> dict[str, Any]:
        """Acquire bounded anonymous GDC metadata. Tokens and controlled access are impossible here."""
        runtime = ctx.deps.runtime
        runtime.claim("source", runtime.max_source_calls)
        append(ctx, "CapabilityInvocation", {"capability_id": "source.gdc", "endpoint": endpoint})
        try:
            record = await runtime.gdc.search(endpoint, filters, tuple(fields), size)
        except Exception as error:
            append(ctx, "CapabilityFailure", {"capability_id": "source.gdc", "error_type": type(error).__name__})
            raise
        append(ctx, "CapabilityResult", {"capability_id": "source.gdc", "acquisition_id": record.acquisition_id, "records": len(record.records)})
        save(ctx, state(ctx).append("acquisitions", StateFragment(fragment_id=record.acquisition_id, kind="gdc", summary=f"{endpoint}: {len(record.records)} public records", provenance=record.provenance)))
        return record.model_dump(mode="json")

    @agent.tool
    async def search_xena(ctx: RunContext[ResearcherDeps], query: str, limit: int = 10) -> dict[str, Any]:
        """Search the anonymous UCSC Xena dataset catalogue when a block needs that source."""
        runtime = ctx.deps.runtime
        runtime.claim("source", runtime.max_source_calls)
        append(ctx, "CapabilityInvocation", {"capability_id": "source.ucsc-xena", "query": query})
        try:
            record = await runtime.xena.search_datasets(query, limit)
        except Exception as error:
            append(ctx, "CapabilityFailure", {"capability_id": "source.ucsc-xena", "error_type": type(error).__name__})
            raise
        append(ctx, "CapabilityResult", {"capability_id": "source.ucsc-xena", "acquisition_id": record.acquisition_id, "records": len(record.records)})
        save(ctx, state(ctx).append("acquisitions", StateFragment(fragment_id=record.acquisition_id, kind="xena", summary=f"dataset search: {len(record.records)} records", provenance=record.provenance)))
        return record.model_dump(mode="json")

    @agent.tool
    async def search_public_literature(ctx: RunContext[ResearcherDeps], query: str, limit: int = 5) -> dict[str, Any]:
        """Retrieve public literature metadata; it is source context, not evidence."""
        runtime = ctx.deps.runtime
        runtime.claim("source", runtime.max_source_calls)
        append(ctx, "CapabilityInvocation", {"capability_id": "literature.public", "query": query})
        try:
            result = await runtime.literature.search(query, limit)
        except Exception as error:
            append(ctx, "CapabilityFailure", {"capability_id": "literature.public", "error_type": type(error).__name__})
            raise
        append(ctx, "CapabilityResult", {"capability_id": "literature.public", "records": len(result.records)})
        save(ctx, state(ctx).append("observations", StateFragment(fragment_id=f"literature-{len(state(ctx).observations)}", kind="literature", summary=f"{len(result.records)} public literature records", provenance=result.provenance)))
        return result.model_dump(mode="json")

    @agent.tool
    async def run_statistics(
        ctx: RunContext[ResearcherDeps], analysis_id: str, question: str, estimand: str, method: str, inputs: dict[str, list[float]]
    ) -> dict[str, Any]:
        """Run one supported deterministic method and retain its measured result for explicit admission."""
        result = ctx.deps.runtime.science.execute(AnalysisSpec(analysis_id=analysis_id, question=question, population="block-selected", estimand=estimand, method=method, variables=tuple(inputs), inputs=inputs))
        ctx.deps.runtime.measurements[analysis_id] = result
        save(ctx, state(ctx).add_measurement(result))
        append(ctx, "ScienceMeasurement", {"analysis_id": analysis_id, "method": method})
        return result.model_dump(mode="json")

    @agent.tool
    async def admit_measurement(ctx: RunContext[ResearcherDeps], analysis_id: str) -> dict[str, Any]:
        """Admit only a deterministic result previously produced by run_statistics or run_science."""
        result = ctx.deps.runtime.measurements[analysis_id]
        evidence = admit_scientific_evidence(result)
        save(ctx, state(ctx).add_evidence(evidence.evidence_id))
        ctx.deps.runtime.capabilities.record_proven(ProvenCapabilityRecord(capability_id="science." + result.provenance[0], verification_id=evidence.evidence_id, execution_reference=analysis_id, evidence=("MeasuredResult", evidence.evidence_id)))
        append(ctx, "EvidenceAdmission", {"evidence_id": evidence.evidence_id, "analysis_id": analysis_id})
        return evidence.model_dump(mode="json")

    @agent.tool
    async def create_line_figure(ctx: RunContext[ResearcherDeps], title: str, x: list[float], y: list[float]) -> dict[str, Any]:
        """Create a deterministic SVG FigureArtifact; visual artifacts are never scientific evidence."""
        artifact = line_figure(title, x, y)
        ctx.deps.runtime.capabilities.record_proven(ProvenCapabilityRecord(capability_id="visualization.scientific", verification_id=artifact.sha256, execution_reference=artifact.artifact_id, evidence=("FigureArtifact", artifact.sha256)))
        append(ctx, "CapabilityResult", {"capability_id": "visualization.scientific", "artifact_id": artifact.artifact_id, "sha256": artifact.sha256})
        return artifact.model_dump(mode="json")

    @agent.tool
    async def block_status(ctx: RunContext[ResearcherDeps]) -> dict[str, Any]:
        """Read the current deadline; a Researcher cannot alter it."""
        block = block_for(ctx)
        return {
            "block_id": block.block_id,
            "status": ctx.deps.runtime.manager.status(block).value,
            "remaining_seconds": int(ctx.deps.runtime.manager.remaining(block).total_seconds()),
        }

    @agent.tool
    async def evaluate_candidate(
        ctx: RunContext[ResearcherDeps], candidate_id: str, candidate_summary: str
    ) -> dict[str, Any]:
        """Run bounded Jev measurements, then deterministic FrontierPolicy."""
        runtime = ctx.deps.runtime
        runtime.claim("jev", runtime.max_jev_calls)
        questions = (
            JevQuestionSpec(
                question_id=f"{candidate_id}-relevance",
                semantic_purpose="candidate relevance",
                primitive="noul",
                projection_id="candidate-v1",
                instructions="Assess relevance to the active block.",
                criteria={"criterion": "relevance"},
                question_version="1",
            ),
            JevQuestionSpec(
                question_id=f"{candidate_id}-action",
                semantic_purpose="local action",
                primitive="choice",
                projection_id="candidate-v1",
                instructions="Choose a conservative local action.",
                criteria={"ADVANCE": "continue", "DEFER": "wait", "NONE": "no fit"},
                question_version="1",
            ),
        )
        current = state(ctx)
        if not any(fragment.fragment_id == candidate_id for fragment in current.candidates):
            current = current.append("candidates", StateFragment(fragment_id=candidate_id, kind="candidate", summary=candidate_summary, provenance=("researcher",)))
            save(ctx, current)
        projection = project_state(current, ProjectionSpec(projection_name="candidate", candidate_id=candidate_id))
        questions = tuple(question.model_copy(update={"projection_id": projection.projection_id}) for question in questions)
        decisions = runtime.jev.evaluate(projection.payload, questions)
        frontier = FrontierPolicy().decide(candidate_id, decisions, (candidate_id,))
        append(ctx, "JevExecution", {"question_ids": [question.question_id for question in questions], "projection_id": projection.projection_id})
        append(ctx, "FrontierDecision", frontier.model_dump(mode="json"))
        return {
            "decisions": [decision.model_dump(mode="json") for decision in decisions],
            "frontier": frontier.model_dump(mode="json"),
        }

    @agent.tool
    async def run_science(
        ctx: RunContext[ResearcherDeps],
        analysis_id: str,
        question: str,
        population: str,
        estimand: str,
        method: str,
        variables: list[str],
    ) -> dict[str, Any]:
        """Execute a supported deterministic analysis; admission remains explicit."""
        result = ctx.deps.runtime.science.execute(
            AnalysisSpec(
                analysis_id=analysis_id,
                question=question,
                population=population,
                estimand=estimand,
                method=method,
                variables=tuple(variables),
            )
        )
        ctx.deps.runtime.measurements[analysis_id] = result
        save(ctx, state(ctx).add_measurement(result))
        append(ctx, "ScienceMeasurement", {"analysis_id": analysis_id, "method": method})
        return result.model_dump(mode="json")

    @agent.tool
    async def generate_hypotheses(
        ctx: RunContext[ResearcherDeps], finding: str
    ) -> dict[str, Any]:
        """Generate alternatives; beyond-scope hypotheses become proposals, never new scope."""
        runtime = ctx.deps.runtime
        runtime.claim("reasoner", runtime.max_reasoner_calls)
        output = runtime.reasoner.generate(block_for(ctx).objective, finding)
        append(ctx, "ReasonerOutput", output.model_dump(mode="json"))
        return output.model_dump(mode="json")

    @agent.tool
    async def request_scope_escalation(
        ctx: RunContext[ResearcherDeps], proposed_test: str, rationale: str
    ) -> dict[str, str]:
        """Propose work beyond scope for the Director; this never creates a new block."""
        append(ctx, "ScopeEscalationRequested", {"proposed_test": proposed_test, "rationale": rationale})
        return {"status": "proposed_to_director", "proposed_test": proposed_test}

    @agent.tool
    async def complete_block(ctx: RunContext[ResearcherDeps], reason: str) -> dict[str, Any]:
        """Ask deterministic BlockManager to finish the current block without extending it."""
        completed = ctx.deps.runtime.manager.complete(block_for(ctx), reason)
        append(ctx, "ResearcherCompletion", {"status": completed.status.value, "reason": completed.termination_reason})
        return completed.model_dump(mode="json")
