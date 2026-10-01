"""Owned event waits and bounded Director turns over persisted notifications."""
import asyncio
from time import perf_counter
from uuid import uuid4

from src.block.models import ServiceResearchState
from src.provenance import canonical_bytes
from src.runtime.pydantic_ai.contracts import DirectorDeps, is_director_event_yield


async def wait_for_research(runtime, director, direction, *, allow_global_work=True):
    active = runtime.active_research
    review_at = perf_counter() + runtime.director_review_interval_seconds
    global_enabled = allow_global_work
    runtime.director_idle_started = perf_counter()
    try:
        while not active.task.done():
            runtime.set_service_state(ServiceResearchState.WAITING_FOR_RESEARCH_EVENT, cause=active.run_id)
            used = runtime._counts.get("director:event_turns", 0)
            if not global_enabled or used >= runtime.director_event_turn_limit:
                await asyncio.shield(active.task)
                break
            notification = asyncio.create_task(runtime.research_events.get())
            scheduled = asyncio.create_task(asyncio.sleep(max(0, review_at-perf_counter())))
            try:
                done, _ = await asyncio.wait((active.task, notification, scheduled), return_when=asyncio.FIRST_COMPLETED)
                if active.task in done:
                    break
                if notification in done:
                    event = notification.result()
                else:
                    event = {"event_id": f"scheduled:{active.run_id}:{uuid4()}", "event_type": "ScheduledProgramReview",
                             "block_id": active.block_id, "ledger_seq": None,
                             "detail": {"remaining_seconds": runtime.manager.remaining(runtime.manager.block(active.block_id)).total_seconds()}}
                review_at = perf_counter() + runtime.director_review_interval_seconds
            finally:
                # These are owned wake-up waiters, never the active Researcher task.
                notification.cancel()
                scheduled.cancel()
                await asyncio.gather(notification, scheduled, return_exceptions=True)
            if active.finished.is_set():
                break
            if any(e.event_type == "DirectorEventTurnStarted" and e.payload.get("event_id") == event["event_id"]
                   for e in runtime.manager.ledger(active.block_id).history()):
                continue
            runtime._counts["director:event_turns"] = used + 1
            runtime.director_idle_seconds += perf_counter()-runtime.director_idle_started
            runtime.director_idle_started = None
            runtime.append_event(active.block_id, "DirectorEventTurnStarted", event)
            runtime.set_service_state(ServiceResearchState.DIRECTOR_GLOBAL_WORK, cause=event["event_id"])
            started = perf_counter()
            runtime.director_turn_started = started
            runtime.director_supervising_turn = True
            runtime.director_terminal_yield = False
            runtime.director_request_error = None
            try:
                prompt = ("Persisted research event permits one bounded global turn. Broad direction: " + direction +
                          "\nDo useful planning over immutable references, then yield. Do not allocate, launch, "
                          "mutate ResearchState or treat operational failure as scientific absence.\n" +
                          canonical_bytes(event).decode())
                if len(prompt.encode()) > 32768:
                    raise ValueError("event context exceeds the Director context bound")
                result = await director.run(prompt, deps=DirectorDeps(runtime), usage=runtime.director_usage,
                                            usage_limits=runtime.usage_limits("director"))
                runtime.append_event(active.block_id, "DirectorEventTurnCompleted", {"event_id": event["event_id"],
                    "summary": result.output[:2000], "epistemic_status": "non_authoritative_planning"})
            except Exception as error:
                retained = runtime.director_request_error or error
                if runtime.director_terminal_yield and is_director_event_yield(retained):
                    runtime.append_event(active.block_id, "DirectorEventTurnYielded", {"event_id": event["event_id"], "reason": "ResearcherTerminalEvent"})
                else:
                    runtime.append_event(active.block_id, "DirectorEventTurnFailed", {"event_id": event["event_id"], "error_type": type(retained).__name__})
                    global_enabled = False
            finally:
                runtime.director_supervising_turn = False
                runtime.director_context = None
                runtime.director_turn_started = None
                runtime.director_turn_seconds += perf_counter()-started
                runtime.director_idle_started = perf_counter()
    finally:
        if runtime.director_idle_started is not None:
            runtime.director_idle_seconds += perf_counter()-runtime.director_idle_started
            runtime.director_idle_started = None
