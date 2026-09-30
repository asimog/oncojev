from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from oncojev.block.models import BlockStatus,JevBlock
from oncojev.director.models import JevBlockStart,ResourceAllocation
from oncojev.ledger.store import Ledger
class BlockManager:
    def __init__(self,now:Callable[[],datetime]|None=None)->None:
        self._now=now or (lambda:datetime.now(UTC)); self._ledgers:dict[str,Ledger]={}
    def create(self,objective:str,why_now:str,allocation:ResourceAllocation)->JevBlock:
        started=self._now(); start=JevBlockStart(block_id=str(uuid4()),objective=objective,why_now=why_now,allocation=allocation,deadline=started+timedelta(seconds=allocation.seconds))
        self._ledgers[start.block_id]=Ledger(); return JevBlock(block_id=start.block_id,start=start,started_at=started,deadline=start.deadline)
    def ledger(self,block_id:str)->Ledger:return self._ledgers[block_id]
    def remaining(self,block:JevBlock)->timedelta:return max(block.deadline-self._now(),timedelta(0))
    def status(self,block:JevBlock)->BlockStatus:return BlockStatus.EXPIRED if block.status is BlockStatus.ACTIVE and not self.remaining(block) else block.status
    def complete(self,block:JevBlock,reason:str)->JevBlock:
        if self.status(block) is BlockStatus.EXPIRED:return block.model_copy(update={"status":BlockStatus.EXPIRED,"termination_reason":"deadline"})
        return block.model_copy(update={"status":BlockStatus.COMPLETE,"termination_reason":reason})
