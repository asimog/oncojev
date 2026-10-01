"""Service-owned operational allowances; these never judge scientific value."""
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from time import perf_counter


class ResourceBusy(RuntimeError):
    def __init__(self, resource, owner):
        self.directive = {"status": "resource_busy", "resource": resource, "owner": owner,
                          "retryable": False, "scientific_negative": False}
        super().__init__(f"{resource} is held by {owner}")


class ResourceRejected(ValueError):
    def __init__(self, reason, consumed_bytes):
        self.directive = {"status": "resource_rejected", "reason": reason,
                          "consumed_bytes": consumed_bytes, "retryable": False,
                          "scientific_negative": False}
        super().__init__(reason)


@dataclass
class ServiceResources:
    max_file_bytes: int = 10_000_000
    max_block_download_bytes: int = 10_000_000
    max_service_download_bytes: int = 10_000_000
    heavy_owner: str | None = None
    downloaded_bytes: int = 0
    block_downloaded_bytes: dict[str, int] = field(default_factory=dict)
    receipts: list[dict] = field(default_factory=list)

    @asynccontextmanager
    async def heavy(self, owner):
        if self.heavy_owner is not None:
            receipt = ResourceBusy("heavy_local_execution", self.heavy_owner).directive
            self.receipts.append({**receipt, "requester": owner})
            raise ResourceBusy("heavy_local_execution", self.heavy_owner)
        self.heavy_owner = owner
        started = perf_counter()
        receipt = {"resource": "heavy_local_execution", "owner": owner, "status": "acquired"}
        self.receipts.append(receipt)
        try:
            yield receipt
        finally:
            receipt.update(status="released", duration_seconds=perf_counter() - started)
            self.heavy_owner = None

    def charge_download(self, owner, byte_count):
        if byte_count < 0:
            raise ValueError("download usage cannot decrease")
        # Failed attempts and the final rejected chunk remain consumed usage.
        self.downloaded_bytes += byte_count
        self.block_downloaded_bytes[owner] = self.block_downloaded_bytes.get(owner, 0) + byte_count
        if self.downloaded_bytes > self.max_service_download_bytes or self.block_downloaded_bytes[owner] > self.max_block_download_bytes:
            self.receipts.append({"resource": "download_bytes", "owner": owner,
                                  "status": "rejected", "transferred_bytes": self.downloaded_bytes})
            raise ResourceRejected("service or block download budget exhausted", self.downloaded_bytes)

    def snapshot(self):
        return {"heavy_local_execution_limit": 1, "heavy_owner": self.heavy_owner,
                "max_file_bytes": self.max_file_bytes,
                "max_block_download_bytes": self.max_block_download_bytes,
                "max_service_download_bytes": self.max_service_download_bytes,
                "downloaded_bytes": self.downloaded_bytes,
                "process_cpu_memory_enforcement": "requires backend and deployment verification"}
