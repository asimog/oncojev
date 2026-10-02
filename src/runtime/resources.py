"""Service-owned operational allowances; these never judge scientific value."""
from contextlib import asynccontextmanager, contextmanager
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
    max_block_download_bytes: int = 50_000_000
    max_service_download_bytes: int = 500_000_000
    max_workspace_bytes: int = 100_000_000
    max_durable_artifact_bytes: int = 1_000_000_000
    minimum_free_disk_bytes: int = 10_000_000
    max_coder_processes: int = 16
    max_coder_memory_mb: int = 512
    max_coder_cpu: int = 2
    max_coder_seconds: int = 60
    max_science_processes: int = 16
    execution_failure: str | None = None
    reservations: dict[str, dict] = field(default_factory=dict)
    heavy_owner: str | None = None
    downloaded_bytes: int = 0
    block_downloaded_bytes: dict[str, int] = field(default_factory=dict)
    receipts: list[dict] = field(default_factory=list)

    @asynccontextmanager
    async def heavy(self, owner):
        if self.execution_failure:
            raise ResourceRejected(self.execution_failure, 0)
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

    @contextmanager
    def reserve_download(self, owner, declared_size, *, workspace_used=0, durable_used=0, paths=(), archive_limit=None):
        """Reserve before opening bytes; unknown size reserves bounded available capacity."""
        import shutil
        from pathlib import Path
        from uuid import uuid4
        if declared_size is not None and (isinstance(declared_size, bool) or not isinstance(declared_size, int) or declared_size < 0):
            raise ValueError("invalid declared file size")
        held = sum(max(0, r['capacity'] - r['consumed']) for r in self.reservations.values())
        held_owner = sum(max(0, r['capacity'] - r['consumed']) for r in self.reservations.values() if r['owner'] == owner)
        disk_held = sum(r['capacity'] for r in self.reservations.values())
        capacity = min(self.max_file_bytes,
            self.max_service_download_bytes - self.downloaded_bytes - held,
            self.max_block_download_bytes - self.block_downloaded_bytes.get(owner, 0) - held_owner,
            self.max_workspace_bytes - workspace_used - disk_held,
            self.max_durable_artifact_bytes - durable_used - disk_held)
        if archive_limit is not None:
            capacity = min(capacity, archive_limit - workspace_used)
        for path in paths:
            target = Path(path).resolve()
            while not target.exists():
                target = target.parent
            # Exact bytes, JSON/base64 and SQLite journal need bounded headroom.
            capacity = min(capacity, (shutil.disk_usage(target).free - self.minimum_free_disk_bytes) // 4 - disk_held)
        if capacity <= 0 or (declared_size is not None and declared_size > capacity):
            raise ResourceRejected("insufficient reserved download/disk capacity", 0)
        amount = capacity if declared_size is None else declared_size
        key = str(uuid4())
        receipt = {'reservation_id': key, 'owner': owner, 'declared_size': declared_size,
                   'capacity': amount, 'consumed': 0, 'status': 'reserved'}
        self.reservations[key] = receipt
        self.receipts.append(receipt)
        class Reservation:
            capacity = amount

            def consume(inner, count):
                receipt['consumed'] += count
                if receipt['consumed'] > amount:
                    raise ResourceRejected("transfer exceeded reserved capacity", receipt['consumed'])
                for path in paths:
                    target = Path(path).resolve()
                    while not target.exists():
                        target = target.parent
                    if shutil.disk_usage(target).free < self.minimum_free_disk_bytes + 4 * receipt['consumed']:
                        raise ResourceRejected("free disk capacity exhausted during transfer", receipt['consumed'])
        try:
            yield Reservation()
        finally:
            receipt['status'] = 'released'
            self.reservations.pop(key, None)

    def charge_download(self, owner, byte_count):
        if byte_count < 0:
            raise ValueError("download usage cannot decrease")
        # Failed attempts and the final rejected chunk remain consumed usage.
        self.downloaded_bytes += byte_count
        self.block_downloaded_bytes[owner] = self.block_downloaded_bytes.get(owner, 0) + byte_count
        held = sum(max(0, r['capacity'] - r['consumed']) for r in self.reservations.values())
        held_owner = sum(max(0, r['capacity'] - r['consumed']) for r in self.reservations.values() if r['owner'] == owner)
        if self.downloaded_bytes + held > self.max_service_download_bytes or self.block_downloaded_bytes[owner] + held_owner > self.max_block_download_bytes:
            self.receipts.append({"resource": "download_bytes", "owner": owner,
                                  "status": "rejected", "transferred_bytes": self.downloaded_bytes})
            raise ResourceRejected("service or block download budget exhausted", self.downloaded_bytes)

    def snapshot(self):
        last_coder = next((r["process_resources"] for r in reversed(self.receipts) if "process_resources" in r), None)
        return {"heavy_local_execution_limit": 1, "heavy_owner": self.heavy_owner,
                "max_file_bytes": self.max_file_bytes,
                "max_block_download_bytes": self.max_block_download_bytes,
                "max_service_download_bytes": self.max_service_download_bytes,
                "downloaded_bytes": self.downloaded_bytes,
                "coder_limits": {"processes": self.max_coder_processes, "memory_mb": self.max_coder_memory_mb,
                    "cpu": self.max_coder_cpu, "seconds": self.max_coder_seconds,
                    "workspace_bytes": self.max_workspace_bytes},
                "last_coder_execution": last_coder, "execution_failure": self.execution_failure,
                "max_science_processes": self.max_science_processes,
                "process_cpu_memory_enforcement": "Coder and local external science: owned-command-v1; installed in-process science has no kernel family quota"}
