"""Archive terminal block scratch files before bounded, fail-closed cleanup."""
import base64
from datetime import UTC,datetime,timedelta
import hashlib
from pathlib import Path
import shutil
from uuid import uuid4

from src.persistence.records import RecordKind
from src.persistence.reconstruct import reconstruct_block
from src.sources.models import ScientificArtifact


def _linked(path:Path)->bool:
    return path.is_symlink() or path.is_junction()


def cleanup_workspaces(repository,root:Path,*,minimum_age_seconds:int=604800,max_archive_bytes:int=100_000_000,
                       max_workspaces:int=20,excluded_block_ids:tuple[str,...]=(),now:datetime|None=None)->tuple[dict,...]:
    """No ledger deletion, automatic research resume or active workspace cleanup."""
    if minimum_age_seconds<0 or max_archive_bytes<1 or not 1<=max_workspaces<=100:raise ValueError("invalid retention bounds")
    original=root.absolute()
    if any(_linked(p) for p in (original,*original.parents)):raise ValueError("workspace root cannot contain links")
    allowed=original.resolve()
    if not allowed.is_dir():return ()
    cutoff=(now or datetime.now(UTC))-timedelta(seconds=minimum_age_seconds)
    results=[]
    for directory in sorted(allowed.iterdir()):
        if len(results)>=max_workspaces:break
        block_id=directory.name
        if block_id in excluded_block_ids or not directory.is_dir() or _linked(directory):continue
        target=directory.resolve()
        if target.parent != allowed or target==allowed:raise ValueError("cleanup target escaped workspace root")
        block=repository.store.latest(RecordKind.BLOCK,block_id=block_id)
        dossier=repository.store.latest(RecordKind.DOSSIER,block_id=block_id)
        if block is None or dossier is None or block.payload.get("status") not in {"complete","failed","interrupted"}:continue
        if max(block.recorded_at,dossier.recorded_at)>cutoff:continue
        view=reconstruct_block(repository.store,block_id)
        if view.unresolved_source_refs or any(e.get("event_type") in {"PersistenceFailure","PersistenceFailed","ArchiveFailed"} for e in view.ledger):continue
        removed=False;deletion_started=False
        try:
            files=[];total=0
            # Inspect without traversing directory links or Windows junctions.
            pending=[target]
            while pending:
                current=pending.pop()
                for entry in sorted(current.iterdir()):
                    if _linked(entry):raise ValueError("workspace contains a link")
                    if entry.is_dir():pending.append(entry)
                    elif entry.is_file():
                        if not entry.resolve().is_relative_to(target):raise ValueError("archive path escaped target")
                        total+=entry.stat().st_size
                        if total>max_archive_bytes:raise ValueError("workspace exceeds archive byte bound")
                        files.append(entry)
                    else:raise ValueError("workspace contains unsupported filesystem entry")
            manifest=[]
            for file in files:
                data=file.read_bytes()
                if len(data)>max_archive_bytes:raise ValueError("workspace file exceeds byte bound")
                if len(data)!=file.stat().st_size:raise ValueError("workspace changed during archival")
                relative=file.relative_to(target).as_posix()
                digest=hashlib.sha256(data).hexdigest()
                artifact=ScientificArtifact(artifact_id=f"workspace:{block_id}:{digest}:{hashlib.sha256(relative.encode()).hexdigest()}",
                    block_id=block_id,source="coder-workspace",request={"path":relative},source_identity=relative,
                    content_base64=base64.b64encode(data).decode("ascii"),byte_sha256=digest,size_bytes=len(data),format="binary",
                    access="local-only",provenance=("workspace-archive-v1",block_id,relative))
                repository.record_scientific_artifact(artifact)
                manifest.append({"path":relative,"artifact_id":artifact.artifact_id,"sha256":digest,"size_bytes":len(data)})
            archive={"block_id":block_id,"version":"workspace-archive-v1","files":manifest,"total_bytes":total,"target":str(target)}
            archive_id=str(uuid4())
            repository.record_immutable(RecordKind.WORKSPACE_ARCHIVE,archive_id,archive,block_id)
            # Verify all exports and current bytes immediately before removal.
            current_files=[];pending=[target]
            while pending:
                current=pending.pop()
                for entry in current.iterdir():
                    if _linked(entry):raise ValueError("workspace changed to contain a link")
                    if entry.is_dir():pending.append(entry)
                    elif entry.is_file():current_files.append(entry.relative_to(target).as_posix())
                    else:raise ValueError("unsupported entry after archive")
            current_files.sort()
            if current_files!=sorted(m["path"] for m in manifest):raise ValueError("workspace changed after archive")
            for item in manifest:
                file=target/item["path"]
                if _linked(file) or not file.resolve().is_relative_to(target) or hashlib.sha256(file.read_bytes()).hexdigest()!=item["sha256"]:
                    raise ValueError("workspace changed after archive")
                repository.resolve_scientific_artifact(block_id,item["artifact_id"])
            latest=repository.store.latest(RecordKind.BLOCK,block_id=block_id)
            if latest.seq!=block.seq or latest.payload.get("status") not in {"complete","failed","interrupted"}:
                raise ValueError("block changed during cleanup")
            if _linked(directory) or directory.resolve()!=target or target.parent!=allowed:
                raise ValueError("cleanup target changed")
            deletion_started=True
            shutil.rmtree(target)
            removed=True
            receipt={"block_id":block_id,"archive_id":archive_id,"status":"removed","files":len(manifest),"bytes":total}
            repository.record_immutable(RecordKind.WORKSPACE_CLEANUP,str(uuid4()),receipt,block_id)
            results.append(receipt)
        except Exception as error:
            # A failed export or identity check cannot authorize deletion.
            results.append({"block_id":block_id,"status":"removed_receipt_failed" if removed else "cleanup_failed" if deletion_started else "skipped","error_type":type(error).__name__})
    return tuple(results)
