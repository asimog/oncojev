"""Typed tool contracts exposed to Pydantic AI agents through Code Mode.

The harness is allowed to orchestrate these operations, but deterministic Python
remains the authority for deadlines, frontier policy, and evidence admission.
"""

import asyncio
import threading
from collections.abc import Callable
from contextlib import nullcontext
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal
from decimal import Decimal
from uuid import uuid4
from time import perf_counter
from pydantic_ai.usage import RunUsage, UsageLimits

from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.exceptions import IncompleteToolCall, UsageLimitExceeded, RunCancelled
from src.runtime.resources import ServiceResources
from src.runtime.process import ProcessCleanupFailed
from src.block.manager import BlockManager
from src.block.models import BlockStatus, ServiceResearchState
from src.oncolab.catalogue import initial_oncolab_index
from src.oncolab.registry import OncoLabIndex, OncoLabVerificationRecord, IndexReceipt
from src.provenance import ExecutionReference, content_hash
from src.oncolab.models import OncoLabKind
from src.director.models import ResourceAllocation
from src.evidence.models import ScientificEvidence
from src.jev.client import JevClient
from src.jev.failure import JevOperationalFailure
from src.jev.frontier import CandidateFrontierPolicy
from src.jev.models import JevDecision, JevQuestionSpec, JevCallReceipt, JevExecutionFailure, JevFailureCategory
from src.ledger.events import LedgerEvent
from src.reasoner.service import ReasonerService
from src.science.admission import admit_scientific_evidence
from src.science.execution import ScienceExecutor
from src.science.models import AnalysisSpec, MeasuredResult
from src.science.sandbox import DockerScientificSandbox, ScientificExecutionBackend, GithubMethodRequest, SandboxMeasurementCandidate, validate_sandbox_candidate
from src.sources.models import AcquisitionRecord
from src.persistence.records import RecordKind
from src.persistence.repository import ResearchRepository
from src.persistence.reconstruct import reconstruct_block
from src.sources.public import GdcPublicSource, PublicLiteratureSource, XenaPublicSource
from src.visualization.models import FigureArtifact
from src.visualization.service import line_figure
from src.researcher.state import ProjectionSpec, ResearchStateStore, StateFragment, project_state
from src.oncolab.labskills import BlockSkillStore
from src.memory.service import ResearchMemory
from src.memory.models import MemoryFilters, MemoryReference
from src.provenance import canonical_bytes
from src.runtime.pydantic_ai.search_tools import register_search_page, register_local_semantic_tools, semantic_memory_context_async


def is_director_truncation(error: Exception) -> bool:
    """Classify installed budget/token truncation exceptions, never generic errors."""
    return isinstance(error, (UsageLimitExceeded, IncompleteToolCall))


def is_director_event_yield(error):
    return isinstance(error, RunCancelled)


class WorkStopped(RuntimeError):
    """A deterministic, non-retryable directive issued before any work starts."""
    def __init__(self, reason: str, resource: str | None = None):
        self.directive = {"status": "handoff_required", "reason": reason, "resource": resource,
                          "retryable": False, "next_action": "inspect partial results and request complete_block"}
        super().__init__(reason.replace("_", " "))


@dataclass
class ActiveResearchContext:
    run_id: str
    block_id: str
    mission_id: str | None
    cycle_id: str | None
    start_sequence: int
    task: asyncio.Task | None = None
    error: Exception | None = None
    output: str | None = None
    dossier: Any = None
    delta: Any = None
    started_counter: float = field(default_factory=perf_counter)
    finished: asyncio.Event = field(default_factory=asyncio.Event)

    def handle(self):
        return {"run_id": self.run_id, "block_id": self.block_id,
                "mission_id": self.mission_id, "cycle_id": self.cycle_id,
                "start_sequence": self.start_sequence,
                "status": "active" if self.task is None or not self.task.done() else "failed" if self.error else "completed"}


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
    projection_max_items: int = 20
    projection_max_payload_bytes: int = 65536
    director_event_turn_limit: int = 8
    director_review_interval_seconds: float = 300
    research_events: asyncio.Queue = field(default_factory=lambda: asyncio.Queue(maxsize=16))
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
    acquisition_owners: dict[str, str] = field(default_factory=dict)
    sandbox_owners: dict[str, str] = field(default_factory=dict)
    research_state: ResearchStateStore = field(default_factory=ResearchStateStore)
    skills: BlockSkillStore = field(default_factory=BlockSkillStore)
    sandbox: ScientificExecutionBackend = field(default_factory=DockerScientificSandbox)
    sandbox_candidates: dict[str, SandboxMeasurementCandidate] = field(default_factory=dict)
    researcher: Agent["ResearcherDeps", str] | None = None
    researcher_factory: Callable[[str | None], Agent["ResearcherDeps", str]] | None = None
    enable_jev: bool = True
    enable_reasoner: bool = True
    mission_id: str | None = None
    cycle_id: str | None = None
    memory_limit: int = 20
    oncolab_candidate_k: int = 80
    memory_jev_calls: int = 4
    memory_jev_questions: int = 20
    memory_jev_bytes: int = 131072
    memory_jev_seconds: float = 20
    memory_elapsed: float = 0
    method_assessments: dict[str, dict[str, Any]] = field(default_factory=dict)
    service_resources: ServiceResources = field(default_factory=ServiceResources)
    installed_science_runner: Any = None
    unbounded_work: bool = False
    _jev_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    active_research: ActiveResearchContext | None = None
    service_state: ServiceResearchState = ServiceResearchState.ALLOCATING
    director_supervising_turn: bool = False
    director_context: Any = None
    director_terminal_yield: bool = False
    director_request_error: Exception | None = None
    director_turn_started: float | None = None
    director_idle_started: float | None = None
    director_turn_seconds: float = 0
    director_idle_seconds: float = 0
    _owner_loop: asyncio.AbstractEventLoop | None = None
    _owner_thread: int | None = None
    _counts: dict[str, int] = field(default_factory=dict)
    external_discovery: Any = None
    application_content_identity: str | None = None
    verification_environment_provider: Any = None
    runtime_paths: Any = None
    reserve_software: Any = None
    institution: Any = None
    _block_indexes: dict[str, Any] = field(default_factory=dict)

    def initialize_institution(self):
        if self.repository is not None and self.institution is None:
            from src.oncolab.institution import OncoLabInstitution, application_identity
            self.institution = OncoLabInstitution(self.repository.store, self.oncolab,
                self.application_content_identity or application_identity(), self.verification_environment_provider)
            self.manager.registry_pin_provider = lambda: self.institution.pin().model_dump()

    def index_for(self, block_id=None):
        self.initialize_institution()
        if self.institution is None:
            return self.oncolab
        if block_id is None:
            self.oncolab = self.institution.index()
            return self.oncolab
        if block_id not in self._block_indexes:
            from src.oncolab.institution import RegistryPin
            start = self.manager.block(block_id).start
            if start.oncolab_registry_revision is None:
                return self.oncolab  # explicit unpinned legacy/fixture block
            pin = RegistryPin(oncolab_registry_revision=start.oncolab_registry_revision,
                              oncolab_history_high_water=start.oncolab_history_high_water,
                              application_identity=start.application_identity)
            self._block_indexes[block_id] = self.institution.index(pin)
        return self._block_indexes[block_id]

    def memory_service(self):
        return ResearchMemory(self.repository.store) if self.repository is not None else None

    def claim_memory_measurement(self, questions, payload_bytes):
        limits={"memory_jev":(1,self.memory_jev_calls),"memory_questions":(questions,self.memory_jev_questions),
                "memory_bytes":(payload_bytes,self.memory_jev_bytes)}
        if not self.unbounded_work and (self.memory_elapsed>=self.memory_jev_seconds or any(self._counts.get(k,0)+v>limit for k,(v,limit) in limits.items())):
            raise WorkStopped("memory_retrieval_budget_exhausted")
        for k,(v,limit) in limits.items():self._counts[k]=self._counts.get(k,0)+v

    def researcher_prompt(self, block_id):
        block = self.manager.block(block_id)
        return (f"Investigate block {block_id}: {block.objective}\n"
                "Validated start packet (prior context only; never evidence admission authority):\n" +
                canonical_bytes(block.start.model_dump(mode="json")).decode("utf-8"))

    def claim(self, block_id: str, resource: str, limit: int) -> None:
        self.check_work(block_id, {resource: (1, limit)})
        key = f"{block_id}:{resource}"
        count = self._counts.get(key, 0) + 1
        self._counts[key] = count
        self.append_event(block_id, "ResourceAttempt", {"resource": resource, "attempt": count,
                          "limit": None if self.unbounded_work else limit})

    def check_work(self, block_id: str, resources: dict[str, tuple[int, int]] | None = None) -> None:
        reason = "soft_deadline_handoff" if self.manager.status(self.manager.block(block_id)) is not BlockStatus.ACTIVE else None
        exhausted = None if self.unbounded_work else next((name for name, (amount, limit) in (resources or {}).items()
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
                       "remaining": None if self.unbounded_work else max(0, limit - self._counts.get(f"{block_id}:{name}", 0)),
                       "limit": None if self.unbounded_work else limit}
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
            return {"attempted": used, "remaining": None if self.unbounded_work else max(0, limit - used),
                    "limit": None if self.unbounded_work else limit}
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
        if self.unbounded_work:
            return UsageLimits(request_limit=None, tool_calls_limit=None, cost_limit=None)
        cost = self.director_cost_limit if role == "director" else self.max_cost
        return UsageLimits(request_limit=self.director_request_limit if role == "director" else self.max_model_requests,
                           tool_calls_limit=self.director_tool_limit if role == "director" else self.max_provider_tool_calls,
                           cost_limit=Decimal(str(cost)) if cost is not None else None)

    def researcher_budget(self, block_id: str) -> RunUsage:
        return self.researcher_usage.setdefault(block_id, RunUsage())

    def append_event(self, block_id: str, event_type: str, payload: dict[str, Any]) -> LedgerEvent:
        if self._owner_thread is not None and threading.get_ident() != self._owner_thread:
            raise RuntimeError("runtime mutations belong to the service event-loop owner")
        if event_type == "CapabilityInvocation":
            from src.oncolab.models import OncoLabAvailability, OncoLabAccessPolicy
            index = self.index_for(block_id)
            capability = payload.get("capability_id")
            descriptor = index.describe(capability)
            if (descriptor is None or not index.routes.get(capability)
                    or descriptor.availability in {OncoLabAvailability.FORBIDDEN, OncoLabAvailability.UNAVAILABLE, OncoLabAvailability.KNOWN}
                    or descriptor.access_policy in {OncoLabAccessPolicy.FORBIDDEN, OncoLabAccessPolicy.REVIEW_REQUIRED}):
                raise ValueError("capability execution disallowed by pinned registry")
        event = LedgerEvent(event_type=event_type, occurred_at=datetime.now(UTC), payload=payload)
        self.manager.ledger(block_id).append(event)
        stored = self.repository.record_ledger_event(block_id, event) if self.repository else None
        history_kind = {"CapabilityInvocation": "usage", "CapabilityResult": "execution",
                        "CapabilityFailure": "failure", "ExternalCapabilityRequested": "demand"}.get(event_type)
        if stored and history_kind:
            self.initialize_institution()
            from src.oncolab.institution import InstitutionalObservation
            self.institution.observe(InstitutionalObservation(observation_id=event.event_id,
                capability_id=payload.get("capability_id"), kind=history_kind, source_seq=stored.seq,
                payload=payload, provenance="typed runtime event; execution outcome is not a scientific interpretation"))
        if event_type in {"EvidenceAdmission", "ScopeEscalationRequested", "CapabilityFailure"}:
            notification = {"event_id": event.event_id, "event_type": event_type, "block_id": block_id,
                            "ledger_seq": stored.seq if stored else None, "detail": payload}
            if self.repository:
                self.repository.record_immutable(RecordKind.SERVICE_EVENT, event.event_id, notification, block_id)
            try:
                self.research_events.put_nowait(notification)
            except asyncio.QueueFull:
                # The durable event and terminal Delta retain the change. A
                # full wake-up queue cannot stall or lose scientific admission.
                key = f"{block_id}:event_notifications_omitted"
                self._counts[key] = self._counts.get(key, 0) + 1
        return event

    def persist_state(self, value):
        saved = self.research_state.put(value)
        if self.repository is not None:
            self.repository.record_state_revision(saved)
        return saved

    def retain_acquisition(self, block_id, record):
        owner = self.acquisition_owners.get(record.acquisition_id)
        if owner is not None and owner != block_id:
            raise ValueError("acquisition is owned by another block")
        if self.repository is not None:
            self.repository.record_acquisition(block_id, record)
        self.acquisitions[record.acquisition_id] = record.model_copy(deep=True)
        self.acquisition_owners[record.acquisition_id] = block_id

    def resolve_acquisition(self, block_id, acquisition_id):
        if self.repository is not None:
            # Explicit fixture inputs are registered before use; production
            # acquisitions have already been persisted at the acquisition tool.
            if acquisition_id in self.acquisitions and acquisition_id not in self.acquisition_owners:
                self.retain_acquisition(block_id, self.acquisitions[acquisition_id])
            return self.repository.resolve_acquisition(block_id, acquisition_id)
        record = self.acquisitions[acquisition_id]
        self.retain_acquisition(block_id, record)
        return self.acquisitions[acquisition_id].model_copy(deep=True)

    def verification(self, block_id, capability_id, record_id, kind, value, scope, outcome="execution_observed"):
        record = OncoLabVerificationRecord(capability_id=capability_id, verification_id=f"{block_id}:{kind}:{record_id}:{outcome}",
            execution_reference=ExecutionReference(kind=kind, value=record_id, block_id=block_id,
                                                   sha256=content_hash(value.model_dump(mode="json"))),
            execution_scope=scope, outcome=outcome, source_reference="runtime typed execution",
            evidence=(kind, record_id))
        if self.repository is not None:
            saved = self.repository.record_verification(record)
        self.initialize_institution()
        if self.institution is not None:
            from src.oncolab.institution import InstitutionalObservation
            self.institution.observe(InstitutionalObservation(
                observation_id='durable:' + saved.record_id, capability_id=capability_id,
                kind='verification', source_seq=saved.seq, payload=saved.payload,
                provenance='durable verification; historical block pins unknown'))
        else:
            self.oncolab.record_verification(record)

    def index_receipt(self, actor, operation, *, block_id=None, **detail):
        index = self.index_for(block_id)
        selected = detail.get("selected_id")
        if selected is not None and index.describe(selected) is None:
            raise ValueError("selected capability is not in the catalogue")
        receipt = IndexReceipt(actor=actor, operation=operation, block_id=block_id,
                               mission_id=self.mission_id, cycle_id=self.cycle_id,
                               oncolab_registry_revision=index.revision_id,
                               oncolab_history_high_water=index.history_high_water,
                               application_identity=(self.manager.block(block_id).start.application_identity if block_id
                                   else self.institution.application if self.institution else None), **detail)
        if self.repository is not None:
            self.repository.record_index_receipt(receipt)
        if block_id is not None:
            self.append_event(block_id, "IndexReceipt", receipt.model_dump(mode="json"))
        return receipt

    def set_service_state(self, value, *, cause=None):
        self.service_state = value
        if self.repository:
            from src.persistence.records import StoredRecord
            self.repository.store.append(StoredRecord(kind=RecordKind.SERVICE_EVENT, record_id=str(uuid4()),
                block_id=self.active_research.block_id if self.active_research else None,
                payload={"state": value.value, "mission_id": self.mission_id, "cycle_id": self.cycle_id,
                         "cause": cause, "operational_only": True}))

    async def execute_external(self, owner, request, *, recovery_inputs=None):
        """One governed external pipeline owner shared by qualification and tools."""
        from src.science.local import LocalVenvScientificBackend
        if isinstance(self.sandbox, LocalVenvScientificBackend):
            if self.runtime_paths is not None:
                self.runtime_paths.require_owned(self.sandbox.root / owner / "experiments")
            backend = LocalVenvScientificBackend(self.sandbox.root / owner / "experiments", self.sandbox.policy,
                workspace_limit=self.service_resources.max_workspace_bytes,workspace_base=self.sandbox.root / owner,
                max_processes=self.service_resources.max_science_processes,
                minimum_free_disk_bytes=self.service_resources.minimum_free_disk_bytes, recovery_inputs=recovery_inputs)
            with self.reserve_software(owner, None) as reservation:
                backend.download_limit = reservation.capacity
                try:
                    candidate = await self.heavy_operation(owner, backend.acquire_and_execute, request.model_copy(deep=True))
                finally:
                    try:
                        reservation.consume(backend.downloaded)
                    finally:
                        try:
                            self.service_resources.charge_download(owner, backend.downloaded, category="software")
                        finally:
                            try:
                                self.append_event(owner, "ScientificResourceReceipt", {'executions':backend.process_resources,'operational_only':True})
                            finally:
                                self.append_event(owner, "ScientificTransferReceipt", {"consumed_bytes": backend.downloaded,
                                    "reserved_bytes": reservation.capacity, "backend": "local_venv"})
        else:
            backend = self.sandbox
            if self.runtime_paths is not None:
                parent = self.runtime_paths.workspaces / owner / "experiments"
                self.runtime_paths.require_owned(parent)
                backend = DockerScientificSandbox(self.sandbox.policy, self.sandbox._runner, owned_parent=parent)
            candidate = await self.heavy_operation(owner, backend.acquire_and_execute, request.model_copy(deep=True))
        if self.repository is not None:
            self.repository.record_immutable(RecordKind.SANDBOX_CANDIDATE, candidate.candidate_id, candidate, owner)
        self.sandbox_candidates[candidate.candidate_id] = candidate.model_copy(deep=True)
        self.sandbox_owners[candidate.candidate_id] = owner
        return candidate

    async def heavy_operation(self, block_id, operation, *inputs):
        async with self.service_resources.heavy(block_id) as receipt:
            self.append_event(block_id, "HeavyExecutionLease", dict(receipt))
            try:
                from src.science.installed import operation_name
                if self.installed_science_runner is not None and operation_name(operation):
                    if self.runtime_paths is None:
                        raise RuntimeError("installed Science requires frozen service paths")
                    workspace = self.runtime_paths.require_owned(self.runtime_paths.workspaces / block_id)
                    first = len(self.installed_science_runner.executions)
                    try:
                        return await self.offload(self.installed_science_runner.run, workspace, operation, *inputs)
                    finally:
                        for observation in self.installed_science_runner.executions[first:]:
                            self.service_resources.record_execution(block_id, observation)
                            self.append_event(block_id, "InstalledScienceResourceReceipt", observation)
                return await self.offload(operation, *inputs)
            except ProcessCleanupFailed as error:
                from src.runtime.resources import ResourceRejected
                self.service_resources.execution_failure = 'owned_command_stop_unconfirmed'
                receipt['operational_error'] = self.service_resources.execution_failure
                raise ResourceRejected(self.service_resources.execution_failure, 0) from error
            finally:
                self.append_event(block_id, "HeavyExecutionUnconfirmed" if self.service_resources.execution_failure
                                  else "HeavyExecutionReleased", {"owner": block_id})

    def retain_export(self, cause):
        if self.repository is None:
            return
        from src.application.export import retain_export
        try:
            return retain_export(self.repository.store, cause=cause)
        except Exception as error:
            # Export is downstream; completed scientific persistence stands.
            print("NOTEBOOK EXPORT FAILED: " + type(error).__name__, flush=True)

    async def evaluate_jev(self, payload, questions):
        from copy import deepcopy
        async with self._jev_lock:
            return await self.offload(self.jev.evaluate, deepcopy(payload), tuple(questions))

    async def offload(self, operation, *inputs):
        """Only detached computation/transport; the caller owns state and persistence.

        Cancellation drains bounded work rather than releasing child ownership
        while it is still executing. Shutdown may take its operation timeout.
        """
        # Runner.close cancels every Task. An executor Future is not in that
        # set, so aggregate shutdown cannot cancel our handle before the actual
        # thread/process family drains. Preserve to_thread's context propagation.
        from contextvars import copy_context
        task = asyncio.get_running_loop().run_in_executor(None, copy_context().run, operation, *inputs)
        while True:
            try:
                return await asyncio.shield(task)
            except asyncio.CancelledError:
                if task.done():
                    return task.result()

    def schedule_researcher(self, block_id: str, launched_by: str) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        if self._owner_loop is not None and self._owner_loop is not loop:
            raise RuntimeError("Researcher lifecycle belongs to another event loop")
        self._owner_loop = loop
        self._owner_thread = threading.get_ident()
        if self.active_research is not None and not self.active_research.task.done():
            raise RuntimeError("one active Researcher is already running")
        self.start_researcher(block_id, launched_by)
        active = ActiveResearchContext(str(uuid4()), block_id, self.mission_id, self.cycle_id,
                                       self.repository.store.high_water() if self.repository else 0)
        self.active_research = active
        self.set_service_state(ServiceResearchState.RESEARCHER_ACTIVE, cause=active.run_id)
        self.append_event(block_id, "ResearcherRunHandle", active.handle())
        active.task = loop.create_task(self._run_researcher(active), name=f"researcher:{active.run_id}")
        return active.handle()

    async def _run_researcher(self, active: ActiveResearchContext) -> None:
        try:
            researcher = self.researcher_factory(active.block_id) if self.researcher_factory else self.researcher
            if researcher is None:
                raise RuntimeError("Researcher agent is not configured")
            result = await researcher.run(self.researcher_prompt(active.block_id),
                deps=ResearcherDeps(self, active.block_id), usage=self.researcher_budget(active.block_id),
                usage_limits=self.usage_limits("researcher"))
            active.output = result.output
        except asyncio.CancelledError:
            active.error = RuntimeError("Researcher cancelled by aggregate shutdown")
        except Exception as error:
            active.error = error
        # No await/foreign authority inside this terminal transaction. Run receipt,
        # outcome and dossier are visible together to API readers and recovery.
        transaction = self.repository.store.transaction() if self.repository else nullcontext()
        with transaction:
            if active.error is None:
                self.complete_researcher(active.block_id)
            else:
                self.append_event(active.block_id, "ResearcherRunFailed", {"error_type": type(active.error).__name__})
                self.manager.finalize(self.manager.block(active.block_id), BlockStatus.FAILED, "researcher_failed")
            from src.dossier.builder import build_dossier
            block = self.manager.block(active.block_id)
            self.append_event(active.block_id, "ModelUsage", self.usage_summary())
            state = self.research_state.get(block.block_id)
            evidence = {r.record_id: r.payload for r in self.repository.store.records(kind=RecordKind.EVIDENCE, block_id=block.block_id)} if self.repository else {
                i: e.model_dump(mode="json") for i, e in self.evidence.items() if i in state.evidence_ids}
            dossier = build_dossier(block, self.manager.ledger(block.block_id).history(), state,
                                    block.termination_reason or "unknown", evidence_records=evidence)
            if self.repository:
                self.repository.record_terminal(block, dossier)
            self.append_event(block.block_id, "DossierHandoff", {"block_id": block.block_id, "status": block.status.value})
        active.dossier = dossier
        if self.repository:
            from src.dossier.delta import build_delta
            active.delta = build_delta(self.repository.store, block, active.run_id, active.start_sequence,
                datetime.now(UTC), researcher_seconds=perf_counter()-active.started_counter,
                director_seconds=self.director_turn_seconds + (perf_counter()-self.director_turn_started if self.director_turn_started is not None else 0),
                idle_seconds=self.director_idle_seconds + (perf_counter()-self.director_idle_started if self.director_idle_started is not None else 0))
            self.repository.record_immutable(RecordKind.BLOCK_DELTA, active.run_id, active.delta, block.block_id)
            self.retain_export("block_terminal:" + active.run_id)
        self.set_service_state(ServiceResearchState.POST_BLOCK_REVIEW, cause=active.run_id)
        active.finished.set()
        if self.director_supervising_turn and self.director_context is not None and self.director_request_error is None:
            self.director_terminal_yield = True
            self.director_context.cancel()


    def start_researcher(self, block_id: str, launched_by: str) -> None:
        if any(event.event_type == "ResearcherRunStarted" for event in self.manager.ledger(block_id).history()):
            self.append_event(block_id, "ResearcherLaunchRejected", {"reason": "no_retry_contract"})
            raise RuntimeError("Researcher already launched for this block; retries are forbidden")
        self.manager.require_work_window(self.manager.block(block_id))
        self.append_event(block_id, "ResearcherRunStarted", {"block_id": block_id, "launched_by": launched_by,
            "workspace": str(self.runtime_paths.workspaces / block_id) if self.runtime_paths else f"var/workspaces/{block_id}"})

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


def register_memory_tools(agent):
    def bounded(value):
        if len(canonical_bytes(value)) > 32768:
            return {"available": True, "omitted": "Requested payload exceeds the 32768-byte context bound; use its typed references."}
        return value

    def items(ctx, field, query, filters, limit):
        memory = ctx.deps.runtime.memory_service()
        return bounded(list(memory.items(field, query, limit=min(limit, ctx.deps.runtime.memory_limit),
                       **MemoryFilters.model_validate(filters or {}).model_dump())) if memory else [])

    @agent.tool
    async def search_research_memory(ctx: RunContext[Any], query: str = "", filters: dict[str, Any] | None = None, limit: int = 10) -> dict[str, Any]:
        """Search historical typed outcomes by mission/entity/topic/time; bounded context, not evidence."""
        memory = ctx.deps.runtime.memory_service()
        return await semantic_memory_context_async(ctx.deps.runtime, query, limit=min(limit, ctx.deps.runtime.memory_limit), block_id=getattr(ctx.deps,"block_id",None), **MemoryFilters.model_validate(filters or {}).model_dump())

    @agent.tool
    async def resolve_memory_reference(ctx: RunContext[Any], reference: MemoryReference) -> dict[str, Any] | None:
        """Resolve exact recorded context by sequence, kind, owner and hash; never grants admission authority."""
        memory = ctx.deps.runtime.memory_service()
        return bounded(memory.resolve(reference)) if memory else None

    @agent.tool
    async def get_dossier(ctx: RunContext[Any], block_id: str) -> dict[str, Any] | None:
        """Resolve a persisted historical dossier with effective outcome corrections; summary, not evidence."""
        memory = ctx.deps.runtime.memory_service()
        return bounded(memory.get_dossier(block_id)) if memory else None

    @agent.tool
    async def get_evidence(ctx: RunContext[Any], evidence_id: str, block_id: str) -> dict[str, Any] | None:
        """Resolve prior admitted evidence for reading; cannot admit it into the current block."""
        memory = ctx.deps.runtime.memory_service()
        return bounded(memory.get_evidence(evidence_id, block_id)) if memory else None

    @agent.tool
    async def get_hypotheses(ctx: RunContext[Any], query: str = "", filters: dict[str, Any] | None = None, limit: int = 10) -> list[dict[str, Any]] | dict[str, Any]:
        """Retrieve reference-linked hypotheses as possibilities, never findings."""
        return items(ctx, "hypotheses", query, filters, limit)

    @agent.tool
    async def get_negative_results(ctx: RunContext[Any], query: str = "", filters: dict[str, Any] | None = None, limit: int = 10) -> list[dict[str, Any]] | dict[str, Any]:
        """Read explicit scientific negatives only; missing, failure and semantic rejection are not negatives."""
        return items(ctx, "scientific_negative_findings", query, filters, limit)

    @agent.tool
    async def get_open_uncertainties(ctx: RunContext[Any], query: str = "", filters: dict[str, Any] | None = None, limit: int = 10) -> list[dict[str, Any]] | dict[str, Any]:
        """Read unresolved recorded uncertainty without converting it to absence."""
        return items(ctx, "uncertainties", query, filters, limit)


def register_director_tools(
    agent: Agent[DirectorDeps, str],
) -> None:
    @agent.output_validator
    def require_cycle_allocation(ctx: RunContext[DirectorDeps], output: str) -> str:
        if ctx.deps is None:
            return output
        runtime = ctx.deps.runtime
        if (not runtime.cycle_id or not runtime.director_supervising_turn
                or runtime.service_state is not ServiceResearchState.ALLOCATING
                or any(block.cycle_id == runtime.cycle_id for block in runtime.manager.blocks())):
            return output
        key = f"director:allocation_correction:{runtime.cycle_id}"
        if runtime._counts.get(key, 0):
            return output  # The cycle owner retains InvalidBlockCount after refusal.
        runtime._counts[key] = 1
        if runtime.repository is not None:
            runtime.repository.record_immutable(RecordKind.SERVICE_EVENT, str(uuid4()), {
                "event_type": "DirectorAllocationCorrectionRequested", "operational_only": True,
                "mission_id": runtime.mission_id, "cycle_id": runtime.cycle_id,
                "reason": "InvalidBlockCount", "output_sha256": content_hash(output)}, None)
        raise ModelRetry("This allocation turn returned without its required block. Use the Director functions in run_code to choose and allocate one defensible bounded investigation. Do not retry rejected scratch commands, invent an allocation or force unsupported science. Python owns launch fallback and outcome validation; planning alone does not satisfy this turn.")

    register_memory_tools(agent)
    register_search_page(agent)
    from src.runtime.pydantic_ai.discovery_tools import register_discovery_tools
    register_discovery_tools(agent)
    from src.runtime.pydantic_ai.global_tools import register_global_tools
    register_global_tools(agent)
    @agent.tool
    async def inspect_director_resources(ctx: RunContext[DirectorDeps]) -> dict[str, Any]:
        """Read independent Director and aggregate allowances without allocating or changing a block.

        Reported costs are partial unless every model response supplied cost; no pricing is inferred.
        """
        runtime = ctx.deps.runtime
        usage = runtime.usage_summary()
        memory_limits = {"calls": ("memory_jev", runtime.memory_jev_calls),
                         "questions": ("memory_questions", runtime.memory_jev_questions),
                         "bytes": ("memory_bytes", runtime.memory_jev_bytes)}
        memory = {name: {"attempted": runtime._counts.get(key, 0), "limit": limit,
                         "remaining": max(0, limit - runtime._counts.get(key, 0))}
                  for name, (key, limit) in memory_limits.items()}
        memory["seconds"] = {"attempted": runtime.memory_elapsed, "limit": runtime.memory_jev_seconds,
                             "remaining": max(0, runtime.memory_jev_seconds - runtime.memory_elapsed)}
        return {"director": usage["director"], "director_budgets": usage["budgets"]["director"],
                "director_cost_limit": runtime.director_cost_limit,
                "aggregate": usage["total"], "aggregate_budgets": usage["budgets"]["cycle"],
                "aggregate_cost_limit": runtime.cycle_cost_limit, "cost_complete": usage["cost_complete"],
                "memory_semantics": memory, "service_resources": runtime.service_resources.snapshot(),
                "event_turns": {"attempted": runtime._counts.get("director:event_turns", 0),
                                "limit": runtime.director_event_turn_limit,
                                "program_review_interval_seconds": runtime.director_review_interval_seconds}}

    @agent.tool
    async def search_oncolab(
        ctx: RunContext[DirectorDeps], query: str = "", kinds: list[OncoLabKind] = [], tags: list[str] = [], limit: int = 8
    ) -> list[dict[str, Any]]:
        """Search bounded capability planning metadata; this never executes science."""
        matches = ctx.deps.runtime.index_for().search(query, kinds=kinds, tags=tags, limit=min(limit, ctx.deps.runtime.oncolab_search_k))
        ctx.deps.runtime.index_receipt("director", "search", query=query, kinds=tuple(kinds), tags=tuple(tags),
                                      requested_limit=limit, effective_limit=min(limit, ctx.deps.runtime.oncolab_search_k),
                                      returned_ids=tuple(m.capability_id for m in matches))
        return [ctx.deps.runtime.index_for().card(match).model_dump(mode="json") for match in matches]

    @agent.tool
    async def describe_oncolab(ctx: RunContext[DirectorDeps], capability_id: str) -> dict[str, Any] | None:
        """Describe one capability and bounded verification history; neither grants execution authority."""
        result = ctx.deps.runtime.index_for().describe_with_verification(capability_id)
        ctx.deps.runtime.index_receipt("director", "describe", requested_id=capability_id,
                                      returned_ids=(capability_id,) if result else ())
        return result

    @agent.tool
    async def allocate_block(
        ctx: RunContext[DirectorDeps], objective: str, why_now: str, seconds: int | None = None,
        entities: list[str] = [], topics: list[str] = [],
        frontier_id: str | None = None, candidate_id: str | None = None
    ) -> dict[str, Any]:
        """Create a bounded block. Only BlockManager computes its deadline."""
        runtime = ctx.deps.runtime
        pending = [b for b in runtime.manager.blocks() if runtime.manager.status(b) in {BlockStatus.ACTIVE, BlockStatus.HANDOFF}
                   or (runtime.cycle_id is not None and b.cycle_id == runtime.cycle_id)]
        if pending:
            runtime.append_event(pending[0].block_id, "DirectorAllocationRejected", {"reason": "single_researcher_allocation"})
            raise RuntimeError("another Researcher block is already allocated")
        runtime.initialize_institution()
        memory = runtime.memory_service()
        start_memory = memory.start_context(objective, context=await semantic_memory_context_async(runtime,objective)) if memory else None
        selected_candidate = None
        if frontier_id is not None or candidate_id is not None:
            if frontier_id is None or candidate_id is None or runtime.repository is None:
                raise ValueError("frontier and candidate identities require durable memory")
            from src.runtime.pydantic_ai.global_tools import validate_selection
            selected_candidate = validate_selection(runtime, frontier_id, candidate_id, objective)
        block = runtime.manager.allocate(
            objective, why_now, seconds, mission_id=runtime.mission_id, cycle_id=runtime.cycle_id,
            memory=start_memory,
            entities=tuple(entities), topics=tuple(topics),
        )
        state = runtime.research_state.start(block.block_id, block.objective)
        runtime.skills.start(block.block_id)
        if runtime.repository is not None:
            runtime.repository.record_block(block)
            runtime.repository.record_state_revision(state)
        runtime.append_event(block.block_id, "DirectorBlockAllocated", {"objective": objective, "deadline": block.deadline.isoformat(), "handoff_at": block.handoff_at.isoformat(), "mission_id": runtime.mission_id, "cycle_id": runtime.cycle_id, "frontier_id": frontier_id, "candidate_id": candidate_id,
            "experience_refs": [r.model_dump(mode="json") for r in selected_candidate.source_refs] if selected_candidate else [],
            "selection_basis": selected_candidate.scope if selected_candidate else None,
            "memory_digest_ids": list(start_memory.digest_ids) if start_memory else []})
        return block.model_dump(mode="json")

    @agent.tool
    async def read_research_memory(ctx: RunContext[DirectorDeps], query: str = "", limit: int = 10,
                                   mission_id: str | None = None, entity: str | None = None, topic: str | None = None,
                                   since: datetime | None = None, until: datetime | None = None) -> dict[str, Any]:
        """Retrieve bounded typed outcomes by relevance and filters, never legacy prose as facts."""
        memory = ctx.deps.runtime.memory_service()
        return await semantic_memory_context_async(ctx.deps.runtime, query, limit=min(limit,ctx.deps.runtime.memory_limit), mission_id=mission_id, entity=entity, topic=topic, since=since, until=until)

    @agent.tool
    async def inspect_block(
        ctx: RunContext[DirectorDeps], block_id: str
    ) -> dict[str, Any]:
        """Read lifecycle state and immutable ledger history for one block."""
        manager = ctx.deps.runtime.manager
        if block_id not in {b.block_id for b in manager.blocks()}:
            repository = ctx.deps.runtime.repository
            if repository is None:
                raise KeyError(block_id)
            return reconstruct_block(repository.store, block_id).model_dump(mode="json")
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
    ) -> dict[str, Any]:
        """Schedule one fresh Researcher and return its identity without waiting."""
        return ctx.deps.runtime.schedule_researcher(block_id, "director")



def register_researcher_tools(
    agent: Agent[ResearcherDeps, str],
) -> None:
    register_memory_tools(agent)
    register_search_page(agent)
    from src.runtime.pydantic_ai.discovery_tools import register_discovery_tools
    register_discovery_tools(agent)
    semantic_tools=register_local_semantic_tools(agent)
    from src.runtime.pydantic_ai.scientific_tools import register_scientific_tools
    register_scientific_tools(agent)
    from src.runtime.pydantic_ai.context_tools import register_context_tools
    register_context_tools(agent)
    from src.runtime.pydantic_ai.followup_tools import register_followup_tools
    register_followup_tools(agent)
    def block_for(ctx: RunContext[ResearcherDeps]):
        return ctx.deps.runtime.manager.block(ctx.deps.block_id)

    def append(ctx: RunContext[ResearcherDeps], event_type: str, payload: dict[str, Any]) -> None:
        ctx.deps.runtime.append_event(ctx.deps.block_id, event_type, payload)

    def state(ctx: RunContext[ResearcherDeps]):
        try: return ctx.deps.runtime.research_state.get(ctx.deps.block_id)
        except KeyError: return ctx.deps.runtime.research_state.start(ctx.deps.block_id, block_for(ctx).objective)
    def save(ctx: RunContext[ResearcherDeps], value): return ctx.deps.runtime.persist_state(value)

    def invocation(ctx, capability_id, **detail):
        call_id = str(uuid4())
        ctx.deps.runtime.index_receipt("researcher", "execute", block_id=ctx.deps.block_id, selected_id=capability_id)
        append(ctx, "CapabilityInvocation", {"invocation_id": call_id, "capability_id": capability_id, **detail})
        return call_id

    def failure(ctx, call_id, capability_id, error):
        response = getattr(error, "response", None)
        detail = {"invocation_id": call_id, "capability_id": capability_id, "error_type": type(error).__name__,
                  "response_bytes": len(response.content) if response is not None else None}
        append(ctx, "CapabilityFailure", detail)
        save(ctx, state(ctx).append("uncertainties", StateFragment(fragment_id=call_id, kind="operational_failure",
            summary=f"{capability_id} failed; this is not biological absence.", provenance=(call_id, capability_id), details=detail)))

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
        runtime = ctx.deps.runtime
        effective = min(limit, runtime.oncolab_search_k)
        matches = runtime.index_for(ctx.deps.block_id).search(query, kinds=kinds, tags=tags, limit=effective)
        runtime.index_receipt("researcher", "search", block_id=ctx.deps.block_id, query=query, kinds=tuple(kinds),
                              tags=tuple(tags), requested_limit=limit, effective_limit=effective,
                              returned_ids=tuple(m.capability_id for m in matches))
        return [runtime.index_for(ctx.deps.block_id).card(match).model_dump(mode="json") for match in matches]

    @agent.tool
    async def describe_oncolab(ctx: RunContext[ResearcherDeps], capability_id: str) -> dict[str, Any] | None:
        """Describe one global capability and its verification history before choosing a typed wrapper."""
        result = ctx.deps.runtime.index_for(ctx.deps.block_id).describe_with_verification(capability_id)
        ctx.deps.runtime.index_receipt("researcher", "describe", block_id=ctx.deps.block_id, requested_id=capability_id,
                                      returned_ids=(capability_id,) if result else ())
        return result

    @agent.tool
    async def acquire_gdc(
        ctx: RunContext[ResearcherDeps], endpoint: Literal["projects", "cases", "files", "annotations"], filters: dict[str, Any], fields: list[str], size: int = 10, offset: int = 0, sort: str = "id:asc"
    ) -> dict[str, Any]:
        """Acquire bounded anonymous GDC metadata. Tokens and controlled access are impossible here."""
        runtime = ctx.deps.runtime
        runtime.claim(ctx.deps.block_id, "source", runtime.max_source_calls)
        call_id = invocation(ctx, "source.gdc", endpoint=endpoint)
        try:
            record = await runtime.gdc.search(endpoint, filters, tuple(fields), size, offset, sort)
        except Exception as error:
            failure(ctx, call_id, "source.gdc", error)
            raise
        runtime.retain_acquisition(ctx.deps.block_id, record)
        append(ctx, "CapabilityResult", {"invocation_id": call_id, "capability_id": "source.gdc", "acquisition_id": record.acquisition_id, "records": len(record.records), "response_bytes": record.response_bytes})
        runtime.verification(ctx.deps.block_id, "source.gdc", record.acquisition_id, "acquisition", record, f"Anonymous {endpoint} retrieval; bounded response slice only.")
        save(ctx, state(ctx).append("acquisitions", StateFragment(fragment_id=record.acquisition_id, kind="gdc", summary=f"{endpoint}: {len(record.records)} public records", provenance=record.provenance,
            details={"source": record.source, "content_sha256": record.content_sha256, "request_sha256": content_hash(record.request),
                     "record_count": len(record.records), "coverage": record.coverage.model_dump(mode="json") if record.coverage else None, "source_refs": [record.acquisition_id]})))
        view = record.model_dump(mode="json")
        if endpoint == "files":
            view["asset_cards"] = [c.model_dump(mode="json") for c in runtime.gdc.asset_cards(record)]
        return view

    @agent.tool
    async def search_xena(ctx: RunContext[ResearcherDeps], query: str, limit: int = 10) -> dict[str, Any]:
        """Search the anonymous UCSC Xena dataset catalogue when a block needs that source."""
        runtime = ctx.deps.runtime
        runtime.claim(ctx.deps.block_id, "source", runtime.max_source_calls)
        call_id = invocation(ctx, "source.ucsc-xena", query=query)
        try:
            record = await runtime.xena.search_datasets(query, limit)
        except Exception as error:
            failure(ctx, call_id, "source.ucsc-xena", error)
            raise
        runtime.retain_acquisition(ctx.deps.block_id, record)
        append(ctx, "CapabilityResult", {"invocation_id": call_id, "capability_id": "source.ucsc-xena", "acquisition_id": record.acquisition_id, "records": len(record.records), "response_bytes": record.response_bytes})
        runtime.verification(ctx.deps.block_id, "source.ucsc-xena", record.acquisition_id, "acquisition", record, "Public dataset catalogue lookup; not genomic data measurement.")
        save(ctx, state(ctx).append("acquisitions", StateFragment(fragment_id=record.acquisition_id, kind="xena", summary=f"dataset search: {len(record.records)} records", provenance=record.provenance,
            details={"source": record.source, "content_sha256": record.content_sha256, "record_count": len(record.records),
                     "coverage": "unknown", "source_refs": [record.acquisition_id]})))
        return record.model_dump(mode="json")

    @agent.tool
    async def search_public_literature(ctx: RunContext[ResearcherDeps], query: str, limit: int = 5) -> dict[str, Any]:
        """Retrieve public literature metadata; it is source context, not evidence."""
        runtime = ctx.deps.runtime
        runtime.claim(ctx.deps.block_id, "source", runtime.max_source_calls)
        call_id = invocation(ctx, "literature.public", query=query)
        try:
            result = await runtime.literature.search(query, limit)
        except Exception as error:
            failure(ctx, call_id, "literature.public", error)
            raise
        if runtime.repository is not None:
            runtime.repository.record_literature(ctx.deps.block_id, result)
        append(ctx, "CapabilityResult", {"invocation_id": call_id, "capability_id": "literature.public", "context_id": result.context_id, "records": len(result.records), "response_bytes": result.response_bytes})
        runtime.verification(ctx.deps.block_id, "literature.public", result.context_id, "literature", result, "Public metadata context retrieval; not scientific evidence.")
        save(ctx, state(ctx).append("observations", StateFragment(fragment_id=result.context_id, kind="literature", summary=f"{len(result.records)} public literature records", provenance=result.provenance,
            details={"context_id": result.context_id, "content_sha256": result.content_sha256,
                     "records": [r.model_dump(mode="json") for r in result.records[:5]], "omitted_records": max(0, len(result.records)-5)})))
        return result.model_dump(mode="json")

    @agent.tool
    async def acquire_github_scientific_method(
        ctx: RunContext[ResearcherDeps], capability_need: str, why_existing_capabilities_are_inadequate: str,
        repository_url: str, requested_ref: str, install_command: list[str], test_command: list[str],
        execute_command: list[str], input_json: dict[str, Any], artifact_ids: list[str] = [],
    ) -> dict[str, Any]:
        """Acquire public GitHub code only through the credential-free Docker sandbox; no stdout or files are returned."""
        if not why_existing_capabilities_are_inadequate.strip():
            raise ValueError("an explicit inadequacy rationale is required before external acquisition")
        runtime = ctx.deps.runtime
        matches = runtime.index_for(ctx.deps.block_id).search(capability_need, limit=runtime.oncolab_search_k)
        runtime.index_receipt("researcher", "search", block_id=ctx.deps.block_id, query=capability_need,
                              requested_limit=20, effective_limit=runtime.oncolab_search_k,
                              returned_ids=tuple(m.capability_id for m in matches))
        # Installed lexical overlap is neither adequacy nor authority. Retain the
        # alternatives/known assessments and the Researcher's explicit rationale.
        append(ctx, "ExternalMethodInadequacy", {"need":capability_need,"rationale":why_existing_capabilities_are_inadequate,
            "alternatives":[{"capability_id":m.capability_id,"assessment":runtime.method_assessments.get(f"{ctx.deps.block_id}:{m.capability_id}")} for m in matches]})
        runtime.claim(ctx.deps.block_id, "sandbox", runtime.max_sandbox_calls)
        artifacts=[]
        for artifact_id in artifact_ids:
            if runtime.repository is None:raise ValueError("file execution requires durable retained artifacts")
            artifacts.append(runtime.repository.resolve_scientific_artifact(ctx.deps.block_id,artifact_id))
        request = GithubMethodRequest(input_artifacts=tuple(artifacts), repository_url=repository_url, requested_ref=requested_ref, install_command=tuple(install_command), test_command=tuple(test_command), execute_command=tuple(execute_command), input_json=input_json)
        request_id = str(uuid4())
        if runtime.repository is not None:
            runtime.repository.record_immutable(RecordKind.SANDBOX_REQUEST, request_id, request, ctx.deps.block_id)
        call_id = invocation(ctx, "software.github-scientific", request_id=request_id)
        append(ctx, "GithubAcquisitionStarted", {"invocation_id": call_id, "request_id": request_id, "request_sha256": content_hash(request.model_dump(mode="json")), "repository_url": request.repository_url, "requested_ref": request.requested_ref, "capability_need": capability_need})
        try:
            candidate = await runtime.execute_external(ctx.deps.block_id, request)
            if runtime.repository is not None:
                runtime.repository.record_immutable(RecordKind.SANDBOX_CANDIDATE, candidate.candidate_id, candidate, ctx.deps.block_id)
        except Exception as error:
            failure(ctx, call_id, "software.github-scientific", error)
            raise
        runtime.sandbox_candidates[candidate.candidate_id] = candidate.model_copy(deep=True)
        runtime.sandbox_owners[candidate.candidate_id] = ctx.deps.block_id
        append(ctx, "CapabilityResult", {"invocation_id": call_id, "capability_id": "software.github-scientific", "candidate_id": candidate.candidate_id})
        append(ctx, "GithubAcquisitionCompleted", {"candidate_id": candidate.candidate_id, "repository_url": candidate.receipt.repository_url, "commit_sha": candidate.receipt.commit_sha, "input_sha256": candidate.receipt.input_sha256, "output_sha256": candidate.receipt.first_run.stdout_sha256, "exit_status": candidate.receipt.first_run.exit_status})
        return {"candidate_id": candidate.candidate_id, "receipt": candidate.receipt.model_dump(mode="json"), "values": candidate.values}

    @agent.tool
    async def validate_sandbox_measurement(ctx: RunContext[ResearcherDeps], candidate_id: str, analysis_id: str) -> dict[str, Any]:
        """Turn a replay-stable sandbox candidate into a deterministic MeasuredResult; this is not evidence admission."""
        ctx.deps.runtime.claim(ctx.deps.block_id, "tool", ctx.deps.runtime.max_tool_calls)
        runtime = ctx.deps.runtime
        if runtime.repository is not None:
            matches = [r for r in runtime.repository.store.records(kind=RecordKind.SANDBOX_CANDIDATE, block_id=ctx.deps.block_id) if r.record_id == candidate_id]
            if not matches:
                raise ValueError("sandbox candidate is not owned by this block")
            candidate = SandboxMeasurementCandidate.model_validate(matches[-1].payload)
        else:
            if runtime.sandbox_owners.get(candidate_id) != ctx.deps.block_id:
                raise ValueError("sandbox candidate is not owned by this block")
            candidate = runtime.sandbox_candidates[candidate_id].model_copy(deep=True)
        if candidate.request and candidate.request.input_artifacts:
            if runtime.repository is None:raise ValueError("file validation requires durable owned inputs")
            for artifact in candidate.request.input_artifacts:
                retained=runtime.repository.resolve_scientific_artifact(ctx.deps.block_id,artifact.artifact_id)
                if retained.byte_sha256 != artifact.byte_sha256 or retained.request != artifact.request:
                    raise ValueError("sandbox retained artifact identity mismatch")
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
        capability_id = {"independent_t_test": "stat.scipy", "pearson_correlation": "stat.scipy",
                         "ordinary_least_squares": "stat.statsmodels", "descriptive_summary": "stat.pandas"}.get(method)
        if capability_id is None:
            raise ValueError(f"unsupported method: {method}")
        spec = AnalysisSpec(analysis_id=analysis_id, question=question, population="agent-provided exploratory values", estimand=estimand, method=method, variables=tuple(inputs), inputs=inputs)
        call_id = invocation(ctx, capability_id, method=method, analysis_id=analysis_id)
        try:
            result = await ctx.deps.runtime.heavy_operation(ctx.deps.block_id, ctx.deps.runtime.science.execute, spec.model_copy(deep=True))
        except Exception as error:
            failure(ctx, call_id, capability_id, error)
            raise
        ctx.deps.runtime.measurements[(ctx.deps.block_id, analysis_id)] = result
        save(ctx, state(ctx).add_measurement(result))
        if ctx.deps.runtime.repository is not None:
            ctx.deps.runtime.repository.record_measurement(result, ctx.deps.block_id)
        append(ctx, "ScienceMeasurement", {"analysis_id": analysis_id, "method": method})
        append(ctx, "CapabilityResult", {"invocation_id": call_id, "capability_id": capability_id, "analysis_id": analysis_id, "origin": result.origin})
        ctx.deps.runtime.verification(ctx.deps.block_id, capability_id, analysis_id, "measurement", result,
                                     f"Exploratory {method} execution on provided arrays; not source-bound science; input arrays are not retained.")
        return result.model_dump(mode="json")

    @agent.tool
    async def measure_acquisition(
        ctx: RunContext[ResearcherDeps], acquisition_id: str, analysis_id: str, numeric_field: str | None = None
    ) -> dict[str, Any]:
        """Measure a stored public acquisition deterministically; this is the source-bound evidence path."""
        runtime = ctx.deps.runtime
        runtime.claim(ctx.deps.block_id, "tool", runtime.max_tool_calls)
        record = runtime.resolve_acquisition(ctx.deps.block_id, acquisition_id)
        call_id = invocation(ctx, "science.acquisition-summary", analysis_id=analysis_id, acquisition_id=acquisition_id, numeric_field=numeric_field)
        from src.science.models import ScientificAttempt, InvalidAnalysis
        method = "record_count" if numeric_field is None else f"numeric_summary:{numeric_field}"
        spec = AnalysisSpec(analysis_id=analysis_id, question="Describe the owned stored response slice",
            population="stored response slice", estimand=method, method=method,
            variables=(numeric_field,) if numeric_field is not None else (), source_refs=(acquisition_id,))
        attempt = ScientificAttempt(attempt_id=call_id, block_id=ctx.deps.block_id,
            capability_id="science.acquisition-summary", analysis=spec,
            input_reference=ExecutionReference(kind="acquisition", value=acquisition_id,
                sha256=content_hash(record.model_dump(mode="json")), block_id=ctx.deps.block_id),
            stage="started", outcome="attempted", limitations=(
                "Descriptive stored response slice; no population, clinical or independent-replication inference.",))
        def retain(value):
            if runtime.repository is not None:
                runtime.repository.record_immutable(RecordKind.SCIENTIFIC_ATTEMPT,
                    value.attempt_id + ":" + value.stage, value, ctx.deps.block_id)
        retain(attempt)
        try:
            result = await runtime.heavy_operation(ctx.deps.block_id, runtime.science.measure_acquisition, record.model_copy(deep=True), analysis_id, numeric_field)
        except BaseException as error:
            invalid = isinstance(error, InvalidAnalysis)
            stage = "invalid" if invalid else "interrupted" if isinstance(error, asyncio.CancelledError) else "operational_failed"
            retain(attempt.model_copy(update={"stage":stage, "outcome":"invalid" if invalid else "attempted",
                "failure_type":type(error).__name__}))
            if invalid:
                append(ctx, "CapabilityFailure", {"invocation_id":call_id, "capability_id":"science.acquisition-summary",
                    "error_type":type(error).__name__, "scientific_invalid":True})
            else:
                failure(ctx, call_id, "science.acquisition-summary", error)
            raise
        runtime.measurements[(ctx.deps.block_id, analysis_id)] = result
        save(ctx, state(ctx).add_measurement(result))
        if runtime.repository is not None:
            with runtime.repository.store.transaction():
                runtime.repository.record_measurement(result, ctx.deps.block_id)
                retain(attempt.model_copy(update={"stage":"completed", "outcome":"unknown",
                    "measurement_reference":ExecutionReference(kind="measurement", value=analysis_id,
                        sha256=content_hash(result.model_dump(mode="json")), block_id=ctx.deps.block_id)}))
        append(ctx, "ScienceMeasurement", {"analysis_id": analysis_id, "method": "acquisition_measurement", "acquisition_id": acquisition_id})
        append(ctx, "CapabilityResult", {"invocation_id": call_id, "capability_id": "science.acquisition-summary", "analysis_id": analysis_id, "origin": result.origin})
        return result.model_dump(mode="json")

    @agent.tool
    async def admit_measurement(ctx: RunContext[ResearcherDeps], analysis_id: str) -> dict[str, Any]:
        """Admit only a deterministic result previously produced by run_statistics or run_science."""
        result = ctx.deps.runtime.measurements[(ctx.deps.block_id, analysis_id)]
        evidence = admit_scientific_evidence(result,ctx.deps.block_id)
        if runtime := ctx.deps.runtime:
            existing=runtime.evidence.get(evidence.evidence_id)
            if existing is None and runtime.repository is not None:
                matches=[r for r in runtime.repository.store.records(kind=RecordKind.EVIDENCE,block_id=ctx.deps.block_id) if r.record_id==evidence.evidence_id]
                if matches:
                    from src.evidence.models import ScientificEvidence
                    existing=ScientificEvidence.model_validate(matches[-1].payload)
            if existing is not None:
                append(ctx,"EvidenceAdmissionReused",{"evidence_id":existing.evidence_id,"analysis_id":analysis_id})
                save(ctx,state(ctx).add_evidence(existing.evidence_id))
                return existing.model_dump(mode="json")
        ctx.deps.runtime.evidence[evidence.evidence_id] = evidence
        save(ctx, state(ctx).add_evidence(evidence.evidence_id))
        if ctx.deps.runtime.repository is not None:
            ctx.deps.runtime.repository.record_evidence(evidence, ctx.deps.block_id)
        capability_id = "software.github-scientific" if result.origin == "sandbox" else "science.source-paired" if "source-paired-v1" in result.provenance else "science.acquisition-summary"
        ctx.deps.runtime.verification(ctx.deps.block_id, capability_id, analysis_id, "measurement", result,
                                     f"Validated {result.origin} measurement: {result.provenance}; declared execution only.", "measurement_validated")
        append(ctx, "EvidenceAdmission", {"evidence_id": evidence.evidence_id, "analysis_id": analysis_id})
        return evidence.model_dump(mode="json")

    @agent.tool
    async def create_line_figure(ctx: RunContext[ResearcherDeps], title: str, x: list[float], y: list[float]) -> dict[str, Any]:
        """Create a deterministic SVG FigureArtifact; visual artifacts are never scientific evidence."""
        ctx.deps.runtime.claim(ctx.deps.block_id, "tool", ctx.deps.runtime.max_tool_calls)
        call_id = invocation(ctx, "visualization.scientific")
        try:
            artifact = await ctx.deps.runtime.heavy_operation(ctx.deps.block_id, line_figure, title, list(x), list(y))
        except Exception as error:
            failure(ctx, call_id, "visualization.scientific", error)
            raise
        ctx.deps.runtime.artifacts.setdefault(ctx.deps.block_id, {})[artifact.artifact_id] = artifact
        if ctx.deps.runtime.repository is not None:
            ctx.deps.runtime.repository.record_artifact(ctx.deps.block_id, artifact)
        ctx.deps.runtime.verification(ctx.deps.block_id, "visualization.scientific", artifact.artifact_id, "artifact", artifact,
                                     "Exploratory SVG rendering from provided arrays; no scientific input validation.", "artifact_created")
        append(ctx, "CapabilityResult", {"invocation_id": call_id, "capability_id": "visualization.scientific", "artifact_id": artifact.artifact_id, "sha256": artifact.sha256, "epistemic_status": artifact.epistemic_status})
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
        """Run bounded relevance/action measurements under candidate-frontier-v1."""
        runtime = ctx.deps.runtime
        if not runtime.enable_jev:
            raise RuntimeError("Jev measurement is disabled in this evaluation condition")
        runtime.check_work(ctx.deps.block_id, {"jev": (1, runtime.max_jev_calls), "jev_questions": (2, runtime.max_jev_questions)})
        runtime.claim(ctx.deps.block_id, "jev", runtime.max_jev_calls)
        key = f"{ctx.deps.block_id}:jev_questions"
        runtime._counts[key] = runtime._counts.get(key, 0) + 2
        append(ctx, "ResourceAttempt", {"resource": "jev_questions", "attempt": runtime._counts[key], "limit": runtime.max_jev_questions})
        call_id = str(uuid4())
        started_at = datetime.now(UTC)
        started = perf_counter()
        policy = CandidateFrontierPolicy()
        receipt = JevCallReceipt(call_id=call_id, block_id=ctx.deps.block_id, candidate_id=candidate_id,
            candidate_summary=candidate_summary[:2000], started_at=started_at, duration_ms=0, outcome="started",
            model_requested=getattr(runtime.jev, "model_requested", "unreported"), policy_version=policy.version)
        if runtime.repository is not None:
            runtime.repository.record_jev_call(receipt)
        append(ctx, "JevCallStarted", {"call_id": call_id, "candidate_id": candidate_id, "question_count": 2})
        questions = ()
        try:
            current = state(ctx)
            if not any(fragment.fragment_id == candidate_id for fragment in current.candidates):
                current = current.append("candidates", StateFragment(fragment_id=candidate_id, kind="candidate", summary=candidate_summary, provenance=("researcher",)))
                save(ctx, current)
            projection = project_state(current, ProjectionSpec(projection_name="candidate", candidate_id=candidate_id,
                                       max_items=runtime.projection_max_items, max_payload_bytes=runtime.projection_max_payload_bytes))
            questions = (
            JevQuestionSpec(
                question_id=f"{candidate_id}-relevance",
                semantic_purpose="candidate relevance",
                primitive="noul",
                projection_id=projection.projection_id,
                instructions="Assess whether `candidate` can inform `objective` within the active block using only the bounded state provided.",
                criteria={
                    "true": "The candidate is relevant to the active block objective and merits local consideration.",
                    "false": "The candidate is unrelated or cannot inform the active block objective.",
                },
                question_version="2",
                known_exclusions=("Relevance is not scientific validity or evidence admission.", "Missing context is unknown, not absence."),
            ),
            JevQuestionSpec(
                question_id=f"{candidate_id}-action",
                semantic_purpose="local action",
                primitive="choice",
                projection_id=projection.projection_id,
                instructions="Select the appropriate local investigation recommendation from the bounded candidate and block context.",
                criteria={"ADVANCE": "Candidate can inform the objective and an in-scope investigation is actionable with available context.",
                          "DEFER": "Potentially relevant but missing context, a dependency or uncertainty prevents choosing an actionable investigation now.",
                          "NONE": "Available context explicitly indicates no fit to this block objective; retain the candidate identity for audit."},
                question_version="2",
                known_exclusions=("This is a local recommendation, not action authority or a scientific negative result.",
                                  "Do not select NONE merely because measured input is missing or a provider failed."),
            ),
            )
            receipt = receipt.model_copy(update={"projection": projection.model_dump(mode="json"),
                                                 "projection_sha256": projection.payload_sha256, "questions": questions,
                                                 "question_hashes": tuple(content_hash(q.model_dump(mode="json")) for q in questions)})
            if runtime.repository is not None:
                runtime.repository.record_jev_call(receipt)
            decisions = await runtime.evaluate_jev(projection.payload, questions)
        except Exception as error:
            failures = error.failures if isinstance(error, JevOperationalFailure) else (
                JevExecutionFailure(question_id=f"{candidate_id}-batch", category=JevFailureCategory.VALIDATION,
                                    detail=f"construction:{type(error).__name__}"),)
            receipt = receipt.model_copy(update={"outcome": "failed", "duration_ms": (perf_counter()-started)*1000,
                                                 "failures": failures, "decisions": getattr(error, "decisions", ()),
                                                 "reported_metadata": getattr(error, "metadata", None),
                                                 "models_resolved": (error.metadata["model_resolved"],) if getattr(error, "metadata", None) else ()})
            append(ctx, "JevExecutionFailure", {"call_id": call_id, "candidate_id": candidate_id,
                "question_ids": [f.question_id for f in failures], "categories": [f.category.value for f in failures]})
            if runtime.repository is not None:
                runtime.repository.record_jev_call(receipt)
                runtime.repository.record_jev_failure(ctx.deps.block_id, failures)
            raise
        receipt = receipt.model_copy(update={"outcome": "completed", "duration_ms": (perf_counter()-started)*1000,
                                             "decisions": tuple(decisions), "models_resolved": tuple(sorted({d.model_resolved for d in decisions})),
                                             "reported_metadata": getattr(decisions, "metadata", None)})
        runtime.jev_history.setdefault(ctx.deps.block_id, []).extend(decisions)
        if runtime.repository is not None:
            runtime.repository.record_jev_call(receipt)
            runtime.repository.record_jev_decisions(ctx.deps.block_id, decisions)
        frontier = policy.decide(candidate_id, decisions, (call_id, projection.projection_id))
        append(ctx, "JevExecution", {"call_id": call_id, "question_ids": [q.question_id for q in questions], "projection_id": projection.projection_id})
        append(ctx, "FrontierDecision", {**frontier.model_dump(mode="json"), "call_id": call_id,
            "candidate_summary": next((f.summary for f in current.candidates if f.fragment_id == candidate_id), candidate_summary),
            "projection_id": projection.projection_id, "projection_sha256": projection.payload_sha256,
            "policy_version": receipt.policy_version, "decisions": [d.model_dump(mode="json") for d in decisions],
            "epistemic_status": "semantic_search_history"})
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
        if isinstance(runtime.reasoner, BudgetedLiveReasoner) and remaining <= 0 and not runtime.unbounded_work:
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
                    usage_limits=runtime.usage_limits("reasoner") if runtime.unbounded_work else
                    UsageLimits(request_limit=usage.requests + remaining, tool_calls_limit=0,
                                cost_limit=Decimal(str(cost_limit)) if cost_limit is not None else None))
            else:
                output = await runtime.reasoner.generate(block_for(ctx).objective, finding)
        except Exception as error:
            append(ctx, "ReasonerFailure", {"error_type": type(error).__name__})
            raise
        append(ctx, "ReasonerOutput", output.model_dump(mode="json"))
        from src.runtime.pydantic_ai.search_tools import retain_hypothesis
        # Generate/retain the entire proposal batch before any semantic narrowing.
        for hypothesis in output.hypotheses:
            retain_hypothesis(runtime, ctx.deps.block_id, hypothesis.statement, hypothesis.proposed_test,
                provenance=("reasoner-proposal", hypothesis.hypothesis_id))
        if runtime.enable_jev:
            for hypothesis in output.hypotheses[:5]:
                try:
                    await semantic_tools["assess_hypothesis"](ctx,hypothesis.statement,hypothesis.proposed_test)
                except Exception as error:
                    append(ctx,"HypothesisAlignmentUnavailable",{"error_type":type(error).__name__})
                    break
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
