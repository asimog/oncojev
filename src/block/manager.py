from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from src.block.models import BlockStatus,JevBlock
from src.director.models import JevBlockStart,ResourceAllocation
from src.ledger.store import Ledger


class HandoffRequired(RuntimeError):
    """Raised before new work starts once a block enters its handoff window."""


class BlockManager:
    def __init__(self,now:Callable[[],datetime]|None=None)->None:
        self._now=now or (lambda:datetime.now(UTC)); self._ledgers:dict[str,Ledger]={}; self._blocks:dict[str,JevBlock]={}
    def create(self,objective:str,why_now:str,allocation:ResourceAllocation)->JevBlock:
        started=self._now(); start=JevBlockStart(block_id=str(uuid4()),objective=objective,why_now=why_now,allocation=allocation,deadline=started+timedelta(seconds=allocation.seconds))
        block=JevBlock(block_id=start.block_id,start=start,started_at=started,deadline=start.deadline)
        self._blocks[start.block_id]=block; self._ledgers[start.block_id]=Ledger(); return block
    def block(self,block_id:str)->JevBlock:return self._blocks[block_id]
    def blocks(self)->tuple[JevBlock,...]:return tuple(self._blocks.values())
    def ledger(self,block_id:str)->Ledger:return self._ledgers[block_id]
    def remaining(self,block:JevBlock)->timedelta:return max(block.deadline-self._now(),timedelta(0))
    def status(self,block:JevBlock)->BlockStatus:
        current = self._blocks.get(block.block_id, block)
        if current.status is BlockStatus.COMPLETE:
            return BlockStatus.COMPLETE
        return BlockStatus.HANDOFF if self._now() >= current.handoff_at else BlockStatus.ACTIVE
    def require_work_window(self, block:JevBlock)->None:
        status = self.status(block)
        if status is not BlockStatus.ACTIVE:
            raise HandoffRequired(f"block {block.block_id} is in handoff; no new work may start")
    def complete(self,block:JevBlock,reason:str)->JevBlock:
        current=self._blocks.get(block.block_id,block)
        completed=current.model_copy(update={"status":BlockStatus.COMPLETE,"termination_reason":reason})
        self._blocks[block.block_id]=completed
        return completed
