from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from src.block.models import BlockStatus,JevBlock
from src.director.models import JevBlockStart,ResourceAllocation
from src.ledger.store import Ledger
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
    def status(self,block:JevBlock)->BlockStatus:return BlockStatus.EXPIRED if block.status is BlockStatus.ACTIVE and not self.remaining(block) else block.status
    def complete(self,block:JevBlock,reason:str)->JevBlock:
        completed=block.model_copy(update={"status":BlockStatus.EXPIRED,"termination_reason":"deadline"}) if self.status(block) is BlockStatus.EXPIRED else block.model_copy(update={"status":BlockStatus.COMPLETE,"termination_reason":reason})
        self._blocks[block.block_id]=completed
        return completed
