"""Typed tool contracts exposed to Pydantic AI agents through Code Mode.

The harness is allowed to orchestrate these operations, but deterministic Python
remains the authority for deadlines, frontier policy, and evidence admission.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from decimal import Decimal
from pydantic_ai.usage import RunUsage, UsageLimits

from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import IncompleteToolCall, UsageLimitExceeded
from src.block.manager import BlockManager
from src.block.models import BlockStatus
from src.oncolab.catalogue import initial_oncolab_index
from src.oncolab.registry import OncoLabIndex, OncoLabVerificationRecord
from src.oncolab.models import OncoLabKind
from src.director.models import ResourceAllocation
from src.evidence.models import ScientificEvidence
from src.jev.client import JevClient
from src.jev.failure import JevOperationalFailure
from src.jev.frontier import FrontierPolicy
from src.jev.models import JevDecision, JevQuestionSpec
from src.ledger.events import LedgerEvent
from src.reasoner.service import ReasonerService
from src.science.admission import admit_scientific_evidence
from src.science.execution import ScienceExecutor
from src.science.models import AnalysisSpec, MeasuredResult
from src.science.sandbox import DockerScientificSandbox, GithubMethodRequest, SandboxMeasurementCandidate, validate_sandbox_candidate
from src.sources.models import AcquisitionRecord
from src.persistence.records import RecordKind
from src.persistence.repository import ResearchRepository
from src.sources.public import GdcPublicSource, PublicLiteratureSource, XenaPublicSource
from src.visualization.models import FigureArtifact
from src.visualization.service import line_figure
from src.researcher.state import ProjectionSpec, ResearchStateStore, StateFragment, project_state
from src.oncolab.labskills import BlockSkillStore


def is_director_truncation(error: Exception) -> bool:
    """Classify installed budget/token truncation exceptions, never generic errors."""
    return isinstance(error, (UsageLimitExceeded, IncompleteToolCall))


class WorkStopped(RuntimeError):
    """A deterministic, non-retryable directive issued before any work starts."""
    def __init__(self, reason: str, resource: str | None = None):
        self.directive = {"status": "handoff_required", "reason": reason, "resource": resource,
                          "retryable": False, "next_action": "inspect partial results and request complete_block"}
        super().__init__(reason.replace("_", " "))


@dataclass
class HarnessRuntime:
    manager: BlockManager
    jev: JevClient
    science: ScienceExecutor
    reasoner: ReasonerService
    max_jev_calls: int
    max_reasoner_calls: int
    max_reasoner_model_requests: int = 10
    max_tool_calls: int = 100
    max_model_requests: int = 200
    max_provider_tool_calls: int = 500
    max_code_mode_executions: int = 100
    max_jev_questions: int = 200
    director_request_limit: int = 50
    director_tool_limit: int = 100
    director_code_limit: int = 30
    director_cost_limit: float | None = None
    cycle_request_limit: int = 300
    cycle_tool_limit: int = 700
    cycle_cost_limit: float | None = None
    director_usage: RunUsage = field(default_factory=RunUsage)
    researcher_usage: dict[str, RunUsage] = field(default_factory=dict)
    reasoner_usage: dict[str, RunUsage] = field(default_factory=dict)
    handoff_reserve_seconds: int = 60
    max_cost: float | None = None
    max_source_calls: int = 20
    max_sandbox_calls: int = 2
    oncolab_search_k: int = 20
    repository: ResearchRepository | None = None
    oncolab: OncoLabIndex = field(default_factory=initial_oncolab_index)
    gdc: GdcPublicSource = field(default_factory=GdcPublicSource)
    xena: XenaPublicSource = field(default_factory=XenaPublicSource)
    literature: PublicLiteratureSource = field(default_factory=PublicLiteratureSource)
    measurements: dict[tuple[str, str], MeasuredResult] = field(default_factory=dict)
    evidence: dict[str, "ScientificEvidence"] = field(default_factory=dict)
    artifacts: dict[str, dict[str, FigureArtifact]] = field(default_factory=dict)
    jev_history: dict[str, list[JevDecision]] = field(default_factory=dict)
    acquisitions: dict[str, AcquisitionRecord] = field(default_factory=dict)
    research_state: ResearchStateStore = field(default_factory=ResearchStateStore)
    skills: BlockSkillStore = field(default_factory=BlockSkillStore)
    sandbox: DockerScientificSandbox = field(default_factory=DockerScientificSandbox)
    sandbox_candidates: dict[str, SandboxMeasurementCandidate] = field(default_factory=dict)
    researcher: Agent["ResearcherDeps", str] | None = None
    researcher_factory: Callable[[str | None], Agent["ResearcherDeps", str]] | None = None
    enable_jev: bool = True
    enable_reasoner: bool = True
    mission_id: str | None = None
    cycle_id: str | None = None
    _counts: dict[str, int] = field(default_factory=dict)

    def claim(self, block_id: str, resource: str, limit: int) -> None:
        self.check_work(block_id, {resource: (1, limit)})
        key = f"{block_id}:{resource}"
        count = self._counts.get(key, 0) + 1
        self._counts[key] = count
        self.append_event(block_id, "ResourceAttempt", {"resource": resource, "attempt": count, "limit": limit})

    def check_work(self, block_id: str, resources: dict[str, tuple[int, int]] | None = None) -> None:
        reason = "soft_deadline_handoff" if self.manager.status(self.manager.block(block_id)) is not BlockStatus.ACTIVE else None
        exhausted = next((name for name, (amount, limit) in (resources or {}).items()
                          if self._counts.get(f"{block_id}:{name}", 0) + amount > limit), None)
        if reason or exhausted:
            stopped = WorkStopped(reason or "budget_exhausted", exhausted)
            self.manager.request_handoff(self.manager.block(block_id))
            self.append_event(block_id, "WorkNotStarted", stopped.directive)
            raise stopped

    def resources(self, block_id: str) -> dict[str, dict[str, int]]:
        limits = {"source": self.max_source_calls, "sandbox": self.max_sandbox_calls,
                  "tool": self.max_tool_calls, "jev": self.max_jev_calls,
                  "jev_questions": self.max_jev_questions, "reasoner": self.max_reasoner_calls}
        return {name: {"attempted": self._counts.get(f"{block_id}:{name}", 0),
                       "remaining": max(0, limit - self._counts.get(f"{block_id}:{name}", 0)), "limit": limit}
                for name, limit in limits.items()}

    def total_usage(self) -> RunUsage:
        total = RunUsage()
        for usage in (self.director_usage, *self.researcher_usage.values(), *self.reasoner_usage.values()):
            total.incr(usage)
        return total

    def usage_summary(self) -> dict[str, Any]:
        def summary(usage):
            return {"requests": usage.requests, "tool_calls": usage.tool_calls,
                    "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens,
                    "reported_cost": str(usage.cost) if usage.cost is not None else None}
        total = self.total_usage()
        def budget(used, limit):
            return {"attempted": used, "remaining": max(0, limit - used), "limit": limit}
        def role_budget(key, requests, request_limit, tool_limit, code_limit):
            return {"model_requests": budget(requests, request_limit),
                    "provider_tools": budget(self._counts.get(f"{key}:provider_tools", 0), tool_limit),
                    "code_mode_executions": budget(self._counts.get(f"{key}:code_mode_executions", 0), code_limit)}
        budgets = {"director": role_budget("director", self.director_usage.requests, self.director_request_limit,
                                            self.director_tool_limit, self.director_code_limit),
                   "allocations": {key: role_budget(key, usage.requests + self.reasoner_usage.get(key, RunUsage()).requests,
                                                   self.max_model_requests, self.max_provider_tool_calls, self.max_code_mode_executions)
                                   for key, usage in self.researcher_usage.items()},
                   "cycle": {"model_requests": budget(total.requests, self.cycle_request_limit),
                             "provider_tools": budget(self._counts.get("cycle:provider_tools", 0), self.cycle_tool_limit)}}
        return {"director": summary(self.director_usage),
                "researchers": {key: summary(value) for key, value in self.researcher_usage.items()},
                "reasoners": {key: summary(value) for key, value in self.reasoner_usage.items()},
                "total": summary(total), "cost_complete": self._counts.get("cycle:cost_reports", 0) == total.requests,
                "provider_tool_attempts": self._counts.get("cycle:provider_tools", 0), "budgets": budgets}

    def usage_limits(self, role: str) -> UsageLimits:
        cost = self.director_cost_limit if role == "director" else self.max_cost
        return UsageLimits(request_limit=self.director_request_limit if role == "director" else self.max_model_requests,
                           tool_calls_limit=self.director_tool_limit if role == "director" else self.max_provider_tool_calls,
                           cost_limit=Decimal(str(cost)) if cost is not None else None)

    def researcher_budget(self, block_id: str) -> RunUsage:
        return self.researcher_usage.setdefault(block_id, RunUsage())

    def append_event(self, block_id: str, event_type: str, payload: dict[str, Any]) -> LedgerEvent:
        event = LedgerEvent(event_type=event_type, occurred_at=datetime.now(UTC), payload=payload)
        self.manager.ledger(block_id).append(event)
        if self.repository is not None:
            self.repository.record_ledger_event(block_id, event)
        return event

    def persist_state(self, value):
        saved = self.research_state.put(value)
        if self.repository is not None:
            self.repository.record_state_revision(saved)
        return saved

    def start_researcher(self, block_id: str, launched_by: str) -> None:
        if any(event.event_type == "ResearcherRunStarted" for event in self.manager.ledger(block_id).history()):
            self.append_event(block_id, "ResearcherLaunchRejected", {"reason": "no_retry_contract"})
            raise RuntimeError("Researcher already launched for this block; retries are forbidden")
        self.manager.require_work_window(self.manager.block(block_id))
        self.append_event(block_id, "ResearcherRunStarted", {"block_id": block_id, "launched_by": launched_by, "workspace": f"var/workspaces/{block_id}"})

    def complete_researcher(self, block_id: str) -> None:
        self.append_event(block_id, "ResearcherRunCompleted", {"block_id": block_id})
        block = self.manager.block(block_id)
        requests = [e for e in self.manager.ledger(block_id).history() if e.event_type == "ResearcherHandoffRequested"]
        reason = requests[-1].payload["reason"] if requests else (
            "soft_deadline_handoff" if self.manager.status(block) is BlockStatus.HANDOFF else "researcher_returned")
        completed = self.manager.complete(block, reason)
        self.append_event(block_id, "ResearcherCompletion", {"status": completed.status.value, "reason": reason})
        if self.repository is not None:
            self.repository.record_block(completed)


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
    async def search_oncolab(
        ctx: RunContext[DirectorDeps], query: str = "", kinds: list[OncoLabKind] = [], tags: list[str] = [], limit: int = 8
    ) -> list[dict[str, Any]]:
        """Search bounded capability planning metadata; this never executes science."""
        matches = ctx.deps.runtime.oncolab.search(query, kinds=kinds, tags=tags, limit=min(limit, ctx.deps.runtime.oncolab_search_k))
        return [match.model_dump(mode="json") for match in matches]

    @agent.tool
    async def describe_oncolab(ctx: RunContext[DirectorDeps], capability_id: str) -> dict[str, Any] | None:
        """Describe one capability and bounded verification history; neither grants execution authority."""
        return ctx.deps.runtime.oncolab.describe_with_verification(capability_id)

    @agent.tool
    async def allocate_block(
        ctx: RunContext[DirectorDeps], objective: str, why_now: str, seconds: int | None = None
    ) -> dict[str, Any]:
        """Create a bounded block. Only BlockManager computes its deadline."""
        runtime = ctx.deps.runtime
        block = runtime.manager.allocate(
            objective, why_now, seconds, mission_id=runtime.mission_id, cycle_id=runtime.cycle_id
        )
        state = runtime.research_state.start(block.block_id, block.objective)
        runtime.skills.start(block.block_id)
        if runtime.repository is not None:
            runtime.repository.record_block(block)
            runtime.repository.record_state_revision(state)
        runtime.append_event(block.block_id, "DirectorBlockAllocated", {"objective": objective, "deadline": block.deadline.isoformat(), "handoff_at": block.handoff_at.isoformat(), "mission_id": runtime.mission_id, "cycle_id": runtime.cycle_id})
        return block.model_dump(mode="json")

    @agent.tool
    async def read_research_memory(ctx: RunContext[DirectorDeps], limit: int = 10) -> list[dict[str, Any]]:
        """Read recent persisted research summaries; memory is context, never evidence."""
        repository = ctx.deps.runtime.repository
        if repository is None:
            return []
        records = repository.store.records(kind=RecordKind.RESEARCH_MEMORY)
        return [record.payload for record in records[-max(1, min(limit, 20)):]]

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
            "resources": ctx.deps.runtime.resources(block_id),
            "model_usage": ctx.deps.runtime.usage_summary(),
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
        runtime.start_researcher(block_id, "director")
        try:
            researcher = runtime.researcher_factory(block_id) if runtime.researcher_factory else runtime.researcher
            if researcher is None:
                raise RuntimeError("Researcher agent is not configured")
            result = await researcher.run(
                f"Investigate block {block_id}: {block.objective}",
                deps=ResearcherDeps(runtime=runtime, block_id=block_id),
                usage=runtime.researcher_budget(block_id), usage_limits=runtime.usage_limits("researcher"),
            )
        except Exception as error:
            runtime.append_event(block_id, "ResearcherRunFailed", {"error_type": type(error).__name__})
            raise
        runtime.complete_researcher(block_id)
        return result.output


def register_researcher_tools(
    agent: Agent[ResearcherDeps, str],
) -> None:
    def block_for(ctx: RunContext[ResearcherDeps]):
        return ctx.deps.runtime.manager.block(ctx.deps.block_id)

    def append(ctx: RunContext[ResearcherDeps], event_type: str, payload: dict[str, Any]) -> None:
        ctx.deps.runtime.append_event(ctx.deps.block_id, event_type, payload)

    def state(ctx: RunContext[ResearcherDeps]):
        try: return ctx.deps.runtime.research_state.get(ctx.deps.block_id)
        except KeyError: return ctx.deps.runtime.research_state.start(ctx.deps.block_id, block_for(ctx).objective)
    def save(ctx: RunContext[ResearcherDeps], value): return ctx.deps.runtime.persist_state(value)

    @agent.tool
    async def load_research_skills(ctx: RunContext[ResearcherDeps], need: str, limit: int = 3) -> list[dict[str, Any]]:
        """Select short procedural skills for this block only; prior Researcher runs are never reused."""
        selected = ctx.deps.runtime.skills.select(ctx.deps.block_id, need, limit)
        append(ctx, "ResearchSkillsLoaded", {"skill_ids": [skill.skill_id for skill in selected]})
        return [skill.model_dump(mode="json") for skill in selected]

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
    async def search_oncolab(
        ctx: RunContext[ResearcherDeps], query: str = "", kinds: list[OncoLabKind] = [], tags: list[str] = [], limit: int = 8
    ) -> list[dict[str, Any]]:
        """Search the same bounded global index for local block planning; this never executes a result."""
        matches = ctx.deps.runtime.oncolab.search(query, kinds=kinds, tags=tags, limit=limit)
        return [match.model_dump(mode="json") for match in matches]

    @agent.tool
    async def describe_oncolab(ctx: RunContext[ResearcherDeps], capability_id: str) -> dict[str, Any] | None:
        """Describe one global capability and its verification history before choosing a typed wrapper."""
        return ctx.deps.runtime.oncolab.describe_with_verification(capability_id)

    @agent.tool
    async def acquire_gdc(
        ctx: RunContext[ResearcherDeps], endpoint: str, filters: dict[str, Any], fields: list[str], size: int = 10
    ) -> dict[str, Any]:
        """Acquire bounded anonymous GDC metadata. Tokens and controlled access are impossible here."""
        runtime = ctx.deps.runtime
        runtime.claim(ctx.deps.block_id, "source", runtime.max_source_calls)
        append(ctx, "CapabilityInvocation", {"capability_id": "source.gdc", "endpoint": endpoint})
        try:
            record = await runtime.gdc.search(endpoint, filters, tuple(fields), size)
        except Exception as error:
            append(ctx, "CapabilityFailure", {"capability_id": "source.gdc", "error_type": type(error).__name__})
            raise
        append(ctx, "CapabilityResult", {"capability_id": "source.gdc", "acquisition_id": record.acquisition_id, "records": len(record.records)})
        runtime.acquisitions[record.acquisition_id] = record
        save(ctx, state(ctx).append("acquisitions", StateFragment(fragment_id=record.acquisition_id, kind="gdc", summary=f"{endpoint}: {len(record.records)} public records", provenance=record.provenance)))
        return record.model_dump(mode="json")

    @agent.tool
    async def search_xena(ctx: RunContext[ResearcherDeps], query: str, limit: int = 10) -> dict[str, Any]:
        """Search the anonymous UCSC Xena dataset catalogue when a block needs that source."""
        runtime = ctx.deps.runtime
        runtime.claim(ctx.deps.block_id, "source", runtime.max_source_calls)
        append(ctx, "CapabilityInvocation", {"capability_id": "source.ucsc-xena", "query": query})
        try:
            record = await runtime.xena.search_datasets(query, limit)
        except Exception as error:
            append(ctx, "CapabilityFailure", {"capability_id": "source.ucsc-xena", "error_type": type(error).__name__})
            raise
        append(ctx, "CapabilityResult", {"capability_id": "source.ucsc-xena", "acquisition_id": record.acquisition_id, "records": len(record.records)})
        runtime.acquisitions[record.acquisition_id] = record
        save(ctx, state(ctx).append("acquisitions", StateFragment(fragment_id=record.acquisition_id, kind="xena", summary=f"dataset search: {len(record.records)} records", provenance=record.provenance)))
        return record.model_dump(mode="json")

    @agent.tool
    async def search_public_literature(ctx: RunContext[ResearcherDeps], query: str, limit: int = 5) -> dict[str, Any]:
        """Retrieve public literature metadata; it is source context, not evidence."""
        runtime = ctx.deps.runtime
        runtime.claim(ctx.deps.block_id, "source", runtime.max_source_calls)
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
    async def acquire_github_scientific_method(
        ctx: RunContext[ResearcherDeps], capability_need: str, why_existing_capabilities_are_inadequate: str,
        repository_url: str, requested_ref: str, install_command: list[str], test_command: list[str],
        execute_command: list[str], input_json: dict[str, Any],
    ) -> dict[str, Any]:
        """Acquire public GitHub code only through the credential-free Docker sandbox; no stdout or files are returned."""
        if not why_existing_capabilities_are_inadequate.strip():
            raise ValueError("an explicit inadequacy rationale is required before external acquisition")
        installed = [item.capability_id for item in ctx.deps.runtime.oncolab.search(capability_need, limit=20) if item.availability.value == "installed"]
        if installed:
            raise ValueError(f"existing installed capabilities must be considered first: {installed}")
        runtime = ctx.deps.runtime
        runtime.claim(ctx.deps.block_id, "sandbox", runtime.max_sandbox_calls)
        request = GithubMethodRequest(repository_url=repository_url, requested_ref=requested_ref, install_command=tuple(install_command), test_command=tuple(test_command), execute_command=tuple(execute_command), input_json=input_json)
        append(ctx, "GithubAcquisitionStarted", {"repository_url": request.repository_url, "requested_ref": request.requested_ref, "capability_need": capability_need})
        candidate = runtime.sandbox.acquire_and_execute(request)
        runtime.sandbox_candidates[candidate.candidate_id] = candidate
        append(ctx, "GithubAcquisitionCompleted", {"candidate_id": candidate.candidate_id, "repository_url": candidate.receipt.repository_url, "commit_sha": candidate.receipt.commit_sha, "input_sha256": candidate.receipt.input_sha256, "output_sha256": candidate.receipt.first_run.stdout_sha256, "exit_status": candidate.receipt.first_run.exit_status})
        return {"candidate_id": candidate.candidate_id, "receipt": candidate.receipt.model_dump(mode="json"), "values": candidate.values}

    @agent.tool
    async def validate_sandbox_measurement(ctx: RunContext[ResearcherDeps], candidate_id: str, analysis_id: str) -> dict[str, Any]:
        """Turn a replay-stable sandbox candidate into a deterministic MeasuredResult; this is not evidence admission."""
        ctx.deps.runtime.claim(ctx.deps.block_id, "tool", ctx.deps.runtime.max_tool_calls)
        candidate = ctx.deps.runtime.sandbox_candidates[candidate_id]
        measurement = validate_sandbox_candidate(candidate, analysis_id)
        ctx.deps.runtime.measurements[(ctx.deps.block_id, analysis_id)] = measurement
        save(ctx, state(ctx).add_measurement(measurement))
        if ctx.deps.runtime.repository is not None:
            ctx.deps.runtime.repository.record_measurement(measurement, ctx.deps.block_id)
        append(ctx, "SandboxMeasurementValidated", {"candidate_id": candidate_id, "analysis_id": analysis_id, "commit_sha": candidate.receipt.commit_sha})
        return measurement.model_dump(mode="json")

    @agent.tool
    async def run_statistics(
        ctx: RunContext[ResearcherDeps], analysis_id: str, question: str, estimand: str, method: str, inputs: dict[str, list[float]]
    ) -> dict[str, Any]:
        """Run one supported deterministic method and retain its measured result for explicit admission."""
        ctx.deps.runtime.claim(ctx.deps.block_id, "tool", ctx.deps.runtime.max_tool_calls)
        result = ctx.deps.runtime.science.execute(AnalysisSpec(analysis_id=analysis_id, question=question, population="agent-provided exploratory values", estimand=estimand, method=method, variables=tuple(inputs), inputs=inputs))
        ctx.deps.runtime.measurements[(ctx.deps.block_id, analysis_id)] = result
        save(ctx, state(ctx).add_measurement(result))
        if ctx.deps.runtime.repository is not None:
            ctx.deps.runtime.repository.record_measurement(result, ctx.deps.block_id)
        append(ctx, "ScienceMeasurement", {"analysis_id": analysis_id, "method": method})
        return result.model_dump(mode="json")

    @agent.tool
    async def measure_acquisition(
        ctx: RunContext[ResearcherDeps], acquisition_id: str, analysis_id: str, numeric_field: str | None = None
    ) -> dict[str, Any]:
        """Measure a stored public acquisition deterministically; this is the source-bound evidence path."""
        runtime = ctx.deps.runtime
        runtime.claim(ctx.deps.block_id, "tool", runtime.max_tool_calls)
        record = runtime.acquisitions[acquisition_id]
        result = runtime.science.measure_acquisition(record, analysis_id, numeric_field)
        runtime.measurements[(ctx.deps.block_id, analysis_id)] = result
        save(ctx, state(ctx).add_measurement(result))
        if runtime.repository is not None:
            runtime.repository.record_measurement(result, ctx.deps.block_id)
        append(ctx, "ScienceMeasurement", {"analysis_id": analysis_id, "method": "acquisition_measurement", "acquisition_id": acquisition_id})
        return result.model_dump(mode="json")

    @agent.tool
    async def admit_measurement(ctx: RunContext[ResearcherDeps], analysis_id: str) -> dict[str, Any]:
        """Admit only a deterministic result previously produced by run_statistics or run_science."""
        result = ctx.deps.runtime.measurements[(ctx.deps.block_id, analysis_id)]
        evidence = admit_scientific_evidence(result)
        ctx.deps.runtime.evidence[evidence.evidence_id] = evidence
        save(ctx, state(ctx).add_evidence(evidence.evidence_id))
        if ctx.deps.runtime.repository is not None:
            ctx.deps.runtime.repository.record_evidence(evidence, ctx.deps.block_id)
        if result.origin == "sandbox":
            capability_id = "software.github-scientific"
        else:
            source = result.provenance[1] if len(result.provenance) > 1 else ""
            capability_id = {"gdc": "source.gdc", "ucsc-xena": "source.ucsc-xena"}.get(source)
        if capability_id is not None:
            ctx.deps.runtime.oncolab.record_verification(OncoLabVerificationRecord(capability_id=capability_id, verification_id=evidence.evidence_id, execution_reference=analysis_id, evidence=("MeasuredResult", evidence.evidence_id)))
        append(ctx, "EvidenceAdmission", {"evidence_id": evidence.evidence_id, "analysis_id": analysis_id})
        return evidence.model_dump(mode="json")

    @agent.tool
    async def create_line_figure(ctx: RunContext[ResearcherDeps], title: str, x: list[float], y: list[float]) -> dict[str, Any]:
        """Create a deterministic SVG FigureArtifact; visual artifacts are never scientific evidence."""
        ctx.deps.runtime.claim(ctx.deps.block_id, "tool", ctx.deps.runtime.max_tool_calls)
        artifact = line_figure(title, x, y)
        ctx.deps.runtime.artifacts.setdefault(ctx.deps.block_id, {})[artifact.artifact_id] = artifact
        if ctx.deps.runtime.repository is not None:
            ctx.deps.runtime.repository.record_artifact(ctx.deps.block_id, artifact)
        ctx.deps.runtime.oncolab.record_verification(OncoLabVerificationRecord(capability_id="visualization.scientific", verification_id=artifact.sha256, execution_reference=artifact.artifact_id, evidence=("FigureArtifact", artifact.sha256)))
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
            "resources": ctx.deps.runtime.resources(block.block_id),
            "model_usage": ctx.deps.runtime.usage_summary(),
        }

    @agent.tool
    async def evaluate_candidate(
        ctx: RunContext[ResearcherDeps], candidate_id: str, candidate_summary: str
    ) -> dict[str, Any]:
        """Run bounded Jev measurements, then deterministic FrontierPolicy."""
        runtime = ctx.deps.runtime
        if not runtime.enable_jev:
            raise RuntimeError("Jev measurement is disabled in this evaluation condition")
        runtime.check_work(ctx.deps.block_id, {"jev": (1, runtime.max_jev_calls), "jev_questions": (2, runtime.max_jev_questions)})
        runtime.claim(ctx.deps.block_id, "jev", runtime.max_jev_calls)
        key = f"{ctx.deps.block_id}:jev_questions"
        runtime._counts[key] = runtime._counts.get(key, 0) + 2
        append(ctx, "ResourceAttempt", {"resource": "jev_questions", "attempt": runtime._counts[key], "limit": runtime.max_jev_questions})
        questions = (
            JevQuestionSpec(
                question_id=f"{candidate_id}-relevance",
                semantic_purpose="candidate relevance",
                primitive="noul",
                projection_id="candidate-v1",
                instructions="Assess relevance to the active block.",
                criteria={
                    "true": "The candidate is relevant to the active block objective and merits local consideration.",
                    "false": "The candidate is unrelated or cannot inform the active block objective.",
                },
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
        try:
            decisions = runtime.jev.evaluate(projection.payload, questions)
        except JevOperationalFailure as error:
            append(ctx, "JevExecutionFailure", {"question_ids": [failure.question_id for failure in error.failures], "categories": [failure.category.value for failure in error.failures]})
            if runtime.repository is not None:
                runtime.repository.record_jev_failure(ctx.deps.block_id, error.failures)
            raise
        runtime.jev_history.setdefault(ctx.deps.block_id, []).extend(decisions)
        if runtime.repository is not None:
            runtime.repository.record_jev_decisions(ctx.deps.block_id, decisions)
        frontier = FrontierPolicy().decide(candidate_id, decisions, (candidate_id,))
        append(ctx, "JevExecution", {"question_ids": [question.question_id for question in questions], "projection_id": projection.projection_id})
        append(ctx, "FrontierDecision", frontier.model_dump(mode="json"))
        return {
            "decisions": [decision.model_dump(mode="json") for decision in decisions],
            "frontier": frontier.model_dump(mode="json"),
        }

    @agent.tool
    async def generate_hypotheses(
        ctx: RunContext[ResearcherDeps], finding: str
    ) -> dict[str, Any]:
        """Generate alternatives; beyond-scope hypotheses become proposals, never new scope."""
        runtime = ctx.deps.runtime
        from src.runtime.pydantic_ai.reasoner import BudgetedLiveReasoner
        if not runtime.enable_reasoner:
            raise RuntimeError("Reasoner is disabled in this evaluation condition")
        usage = runtime.reasoner_usage.setdefault(ctx.deps.block_id, RunUsage())
        researcher_usage = runtime.researcher_budget(ctx.deps.block_id)
        remaining = min(runtime.max_reasoner_model_requests,
                        runtime.max_model_requests - researcher_usage.requests - usage.requests,
                        runtime.cycle_request_limit - runtime.total_usage().requests)
        if isinstance(runtime.reasoner, BudgetedLiveReasoner) and remaining <= 0:
            raise WorkStopped("reasoner_model_budget_exhausted", "reasoner")
        runtime.claim(ctx.deps.block_id, "reasoner", runtime.max_reasoner_calls)
        try:
            if isinstance(runtime.reasoner, BudgetedLiveReasoner):
                budgets = []
                if runtime.max_cost is not None:
                    budgets.append(runtime.max_cost - float(researcher_usage.cost or 0))
                if runtime.cycle_cost_limit is not None:
                    budgets.append(float(usage.cost or 0) + runtime.cycle_cost_limit - float(runtime.total_usage().cost or 0))
                cost_limit = min(budgets) if budgets else None
                output = await runtime.reasoner.generate(block_for(ctx).objective, finding, usage=usage, deps=ctx.deps,
                    usage_limits=UsageLimits(request_limit=usage.requests + remaining, tool_calls_limit=0,
                                             cost_limit=Decimal(str(cost_limit)) if cost_limit is not None else None))
            else:
                output = await runtime.reasoner.generate(block_for(ctx).objective, finding)
        except Exception as error:
            append(ctx, "ReasonerFailure", {"error_type": type(error).__name__})
            raise
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
        """Request handoff; closure requires a successful Researcher return receipt."""
        completed = ctx.deps.runtime.manager.request_handoff(block_for(ctx))
        append(ctx, "ResearcherHandoffRequested", {"reason": reason})
        if ctx.deps.runtime.repository is not None:
            ctx.deps.runtime.repository.record_block(completed)
        return completed.model_dump(mode="json")
