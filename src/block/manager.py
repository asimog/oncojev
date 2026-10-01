from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from src.block.models import BlockStatus,JevBlock
from src.director.models import JevBlockStart,ResourceAllocation
from src.ledger.store import Ledger
from src.config.models import BlockConfig


class HandoffRequired(RuntimeError):
    """Raised before new work starts once a block enters its handoff window."""


class BlockManager:
    def __init__(self,now:Callable[[],datetime]|None=None, *, policy:BlockConfig|None=None)->None:
        self.policy=policy
        self._now=now or (lambda:datetime.now(UTC)); self._ledgers:dict[str,Ledger]={}; self._blocks:dict[str,JevBlock]={}
    def create(self,objective:str,why_now:str,allocation:ResourceAllocation, *, mission_id:str|None=None, cycle_id:str|None=None)->JevBlock:
        if self.policy is not None:
            if not self.policy.min_seconds <= allocation.seconds <= self.policy.max_seconds:
                raise ValueError("block duration is outside configured min/max bounds")
            if allocation.handoff_reserve_seconds != self.policy.handoff_reserve_seconds:
                raise ValueError("block reserve must match deterministic policy")
        started=self._now(); start=JevBlockStart(block_id=str(uuid4()),objective=objective,why_now=why_now,allocation=allocation,deadline=started+timedelta(seconds=allocation.seconds))
        block=JevBlock(block_id=start.block_id,start=start,started_at=started,deadline=start.deadline,mission_id=mission_id,cycle_id=cycle_id)
        self._blocks[start.block_id]=block; self._ledgers[start.block_id]=Ledger(); return block
    def allocate(self, objective:str, why_now:str, seconds:int|None=None, **references)->JevBlock:
        policy=self.policy or BlockConfig(min_seconds=1, handoff_reserve_seconds=0)
        return self.create(objective, why_now, ResourceAllocation(seconds=policy.default_seconds if seconds is None else seconds,
                           handoff_reserve_seconds=policy.handoff_reserve_seconds), **references)
    def block(self,block_id:str)->JevBlock:return self._blocks[block_id]
    def blocks(self)->tuple[JevBlock,...]:return tuple(self._blocks.values())
    def ledger(self,block_id:str)->Ledger:return self._ledgers[block_id]
    def remaining(self,block:JevBlock)->timedelta:return max(block.deadline-self._now(),timedelta(0))
    def status(self,block:JevBlock)->BlockStatus:
        current = self._blocks.get(block.block_id, block)
        if current.status in (BlockStatus.COMPLETE, BlockStatus.FAILED, BlockStatus.INTERRUPTED, BlockStatus.HANDOFF):
            return current.status
        return BlockStatus.HANDOFF if self._now() >= current.handoff_at else BlockStatus.ACTIVE
    def require_work_window(self, block:JevBlock)->None:
        status = self.status(block)
        if status is not BlockStatus.ACTIVE:
            raise HandoffRequired(f"block {block.block_id} is in handoff; no new work may start")
    def complete(self,block:JevBlock,reason:str)->JevBlock:
        return self.finalize(block, BlockStatus.COMPLETE, reason)
    def request_handoff(self,block:JevBlock)->JevBlock:
        current=self._blocks[block.block_id]
        if current.status is BlockStatus.ACTIVE:
            current=current.model_copy(update={"status":BlockStatus.HANDOFF})
            self._blocks[block.block_id]=current
        return current
    def finalize(self,block:JevBlock,status:BlockStatus,reason:str)->JevBlock:
        current=self._blocks.get(block.block_id,block)
        completed=current.model_copy(update={"status":status,"termination_reason":reason})
        self._blocks[block.block_id]=completed
        return completed
