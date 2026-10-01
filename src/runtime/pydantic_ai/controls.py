"""Deterministic role and aggregate controls, including Code Mode inner calls."""

from dataclasses import dataclass

from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.exceptions import UsageLimitExceeded

from src.runtime.pydantic_ai.contracts import WorkStopped
from src.runtime.resources import ResourceBusy, ResourceRejected


@dataclass
class RuntimeControls(AbstractCapability):
    role: str
    code_mode_tool_limit: int = 100

    def stopped(self, ctx, reason):
        runtime = ctx.deps.runtime
        directive = WorkStopped(reason).directive
        if self.role == "researcher":
            runtime.manager.request_handoff(runtime.manager.block(ctx.deps.block_id))
            runtime.append_event(ctx.deps.block_id, "WorkNotStarted", directive)
        return directive

    async def before_model_request(self, ctx, request_context):
        if ctx.deps is None:
            return request_context
        runtime = ctx.deps.runtime
        # Direct standalone fixtures still register their actual usage object.
        if self.role == "director":
            runtime.director_usage = ctx.usage
        elif self.role == "reasoner":
            runtime.reasoner_usage[ctx.deps.block_id] = ctx.usage
        else:
            runtime.researcher_usage[ctx.deps.block_id] = ctx.usage
        total = runtime.total_usage()
        limits = runtime.usage_limits(self.role)
        limits.check_before_request(ctx.usage)
        if self.role in {"researcher", "reasoner"}:
            reasoner = runtime.reasoner_usage.get(ctx.deps.block_id)
            researcher = runtime.researcher_budget(ctx.deps.block_id)
            if researcher.requests + (reasoner.requests if reasoner else 0) >= runtime.max_model_requests:
                raise UsageLimitExceeded("Researcher allocation model request budget exhausted")
            role_cost = float(researcher.cost or 0) + (float(reasoner.cost or 0) if reasoner else 0)
            if runtime.max_cost is not None and role_cost >= runtime.max_cost:
                raise UsageLimitExceeded("Researcher allocation reported cost budget exhausted")
        if total.requests >= runtime.cycle_request_limit:
            raise UsageLimitExceeded("aggregate cycle request budget exhausted")
        if runtime.cycle_cost_limit is not None and total.cost is not None and total.cost >= runtime.cycle_cost_limit:
            raise UsageLimitExceeded("aggregate reported cycle cost budget exhausted")
        return request_context

    async def wrap_tool_execute(self, ctx, *, call, tool_def, args, handler):
        if ctx.deps is None:
            return await handler(args)
        runtime = ctx.deps.runtime
        role_key = "director" if self.role == "director" else ctx.deps.block_id
        role_attempts = f"{role_key}:provider_tools"
        role_limit = runtime.director_tool_limit if self.role == "director" else runtime.max_provider_tool_calls
        if runtime._counts.get(role_attempts, 0) >= role_limit:
            return self.stopped(ctx, "role_tool_budget_exhausted")
        attempts = runtime._counts.get("cycle:provider_tools", 0)
        if attempts >= runtime.cycle_tool_limit:
            return self.stopped(ctx, "aggregate_tool_budget_exhausted")
        runtime._counts["cycle:provider_tools"] = attempts + 1
        runtime._counts[role_attempts] = runtime._counts.get(role_attempts, 0) + 1
        if call.tool_name == "run_code":
            if self.code_mode_tool_limit == 0:
                return self.stopped(ctx, "code_mode_tool_budget_exhausted")
            key = f"{role_key}:code_mode_executions"
            used = runtime._counts.get(key, 0)
            limit = runtime.director_code_limit if self.role == "director" else runtime.max_code_mode_executions
            if used >= limit:
                return self.stopped(ctx, "code_mode_execution_budget_exhausted")
            runtime._counts[key] = used + 1
        try:
            if self.role == "researcher" and call.tool_name in {"shell", "write_file", "edit_file"}:
                runtime.check_work(ctx.deps.block_id)
            return await handler(args)
        except (WorkStopped, ResourceBusy, ResourceRejected) as stopped:
            return stopped.directive

    async def after_model_request(self, ctx, *, request_context, response):
        if ctx.deps is None:
            return response
        runtime = ctx.deps.runtime
        reported = response.usage.cost
        if reported is not None:
            runtime._counts["cycle:cost_reports"] = runtime._counts.get("cycle:cost_reports", 0) + 1
        total = runtime.total_usage()
        over_cycle = runtime.cycle_cost_limit is not None and reported is not None and float(total.cost or 0) + float(reported) > runtime.cycle_cost_limit
        over_role = False
        if self.role != "director" and runtime.max_cost is not None and reported is not None:
            researcher = runtime.researcher_budget(ctx.deps.block_id)
            reasoner = runtime.reasoner_usage.get(ctx.deps.block_id)
            spent = float(researcher.cost or 0) + (float(reasoner.cost or 0) if reasoner else 0)
            over_role = spent + float(reported) > runtime.max_cost
        if over_cycle or over_role:
            # The framework records response usage after this hook. Preserve
            # the charge before raising, since it will not reach that step.
            ctx.usage.incr(response.usage)
            raise UsageLimitExceeded("reported aggregate or allocation cost budget exceeded")
        return response
