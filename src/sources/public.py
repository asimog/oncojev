from typing import Any
import re
import asyncio
from contextlib import nullcontext
from datetime import UTC, datetime

import httpx

from src.runtime.resources import ResourceRejected
from src.sources.models import AcquisitionRecord, CoverageContract, ScientificArtifact, LiteratureRecord, LiteratureSearchResult


async def bounded_response(client, method, url, ceiling, meter=None, reserve=None, **kwargs):
    """Bound decoded response content while streaming, including failed attempts."""
    chunks = []
    size = 0
    with reserve() if reserve is not None else nullcontext(None) as capacity:
        effective_ceiling = min(ceiling, capacity.capacity) if capacity is not None else ceiling
        async with client.stream(method, url, **kwargs) as response:
            response.raise_for_status()
            declared = response.headers.get("content-length")
            if declared is not None and int(declared) > effective_ceiling:
                raise ResourceRejected("public source response exceeded the configured byte budget", size)
            async for chunk in response.aiter_bytes(chunk_size=min(65536, effective_ceiling + 1)):
                size += len(chunk)
                try:
                    if capacity is not None:
                        capacity.consume(len(chunk))
                finally:
                    if meter is not None:
                        meter(len(chunk))
                if size > effective_ceiling:
                    raise ResourceRejected("public source response exceeded the configured byte budget", size)
                chunks.append(chunk)
            return httpx.Response(response.status_code, content=b"".join(chunks), request=response.request)


class GdcPublicSource:
    """Anonymous-only GDC metadata wrapper. It accepts no credential input."""
    allowed_endpoints = frozenset({"projects", "cases", "files", "annotations"})

    def __init__(self, transport: httpx.AsyncBaseTransport | None = None, max_download_bytes: int = 10_000_000) -> None:
        self._client = httpx.AsyncClient(base_url="https://api.gdc.cancer.gov", transport=transport, headers={"Accept": "application/json"}, timeout=20)
        if max_download_bytes <= 0: raise ValueError("download ceiling must be positive")
        self._max_download_bytes = min(max_download_bytes, 10_000_000)
        self.meter = None
        self.reserve = None
        self.response_reserve = None
        self.transfer_receipt = None

    async def aclose(self):
        await self._client.aclose()

    async def search(self, endpoint: str, filters: dict[str, Any], fields: tuple[str, ...], size: int = 10, offset: int = 0, sort: str = "id:asc") -> AcquisitionRecord:
        if endpoint not in self.allowed_endpoints: raise ValueError("unsupported public GDC endpoint")
        if not 1 <= size <= 100: raise ValueError("size must be between 1 and 100")
        if offset < 0 or offset > 1_000_000: raise ValueError("offset is outside bounded pagination")
        if not re.fullmatch(r"[A-Za-z0-9_.]+:(asc|desc)",sort): raise ValueError("declare one stable ordering field")
        identity_field = {'files':'file_id','cases':'case_id','projects':'project_id','annotations':'annotation_id'}[endpoint]
        if sort.startswith('id:'):
            sort = identity_field + sort[2:]
        fields = tuple(identity_field if field == 'id' else field for field in fields)
        payload={"fields":",".join(fields),"format":"JSON","size":size,"from":offset,"sort":sort}
        if filters:
            from copy import deepcopy
            payload["filters"] = deepcopy(filters)
        response=await bounded_response(self._client,"POST",f"/{endpoint}",self._max_download_bytes,self.meter,self.response_reserve,json=payload);body=await asyncio.to_thread(response.json);hits=body.get("data",{}).get("hits",[])
        if body.get('error'):
            raise RuntimeError('GDC query failed despite HTTP success')
        if not isinstance(hits,list) or any(not isinstance(row,dict) for row in hits):
            raise RuntimeError('invalid GDC hits response')
        pagination=body.get("data",{}).get("pagination",{})
        total=pagination.get("total")
        total=total if isinstance(total,int) and not isinstance(total,bool) and total>=0 else None
        rows=hits[:size];ids=[row.get("id") for row in rows]
        known=all(isinstance(i,str) and i for i in ids)
        unique=len(set(ids)) if known else None
        duplicate=len(rows)-unique if unique is not None else 0
        complete=offset==0 and total is not None and len(rows)==total and known and duplicate==0
        coverage=CoverageContract(endpoint=endpoint,offset=offset,requested_size=size,returned_rows=len(rows),reported_total=total,
            ordering=sort,id_field="id",unique_entities=unique,duplicate_rows=duplicate,complete=complete,
            limitations=() if complete else ("Bounded page; completeness not established.",))
        return AcquisitionRecord(source="gdc",request=payload,records=tuple(rows),coverage=coverage,
            provenance=("https://api.gdc.cancer.gov",endpoint),response_bytes=len(response.content))

    def asset_cards(self, record):
        from src.sources.models import DataAssetCard
        from src.provenance import content_hash
        if record.source != 'gdc' or record.coverage is None or record.coverage.endpoint != 'files':
            raise ValueError('GDC file acquisition required for asset cards')
        cards = []
        for row in record.records:
            cases = row.get('cases') or []
            if not isinstance(cases, list):
                cases = []
            case_ids = tuple(str(c['case_id']) for c in cases if isinstance(c, dict) and c.get('case_id'))
            projects = tuple(sorted({str(c['project']['project_id']) for c in cases
                if isinstance(c, dict) and isinstance(c.get('project'), dict) and c['project'].get('project_id')}))
            fields = ('file_name', 'state', 'data_category', 'data_type', 'data_format', 'experimental_strategy', 'platform', 'md5sum')
            values = {k: str(row[k])[:500] if row.get(k) is not None else None for k in fields}
            size = row.get('file_size')
            size = size if isinstance(size, int) and not isinstance(size, bool) and size >= 0 else None
            workflow = row.get('analysis') or {}
            cards.append(DataAssetCard(acquisition_id=record.acquisition_id, file_id=row.get('file_id') or row.get('id'),
                access=row.get('access') if row.get('access') in {'open', 'controlled'} else 'unknown',
                file_size=size, workflow=workflow.get('workflow_type') if isinstance(workflow, dict) else None,
                cases=case_ids[:20], projects=projects[:20], **values,
                request_sha256=content_hash(record.request), content_sha256=record.content_sha256,
                retrieved_at=record.retrieved_at.isoformat(),
                omissions=tuple(k for k in (*fields, 'file_size', 'access') if row.get(k) is None)
                    + (('case/project references truncated',) if len(case_ids) > 20 or len(projects) > 20 else ())))
        return tuple(cards)

    async def acquire_file(self,file_id:str,block_id:str,format:str)->ScientificArtifact:
        """A single explicitly open file with reserved capacity and exact byte identity."""
        import base64
        import hashlib
        from uuid import UUID
        UUID(file_id)
        if format not in {"tsv","json","text","binary","gzip"}:raise ValueError("declare supported byte format")
        declared=None;size=0;metadata_bytes=None;status='failed';error_type=None
        try:
            metadata=await bounded_response(self._client,"GET",f"/files/{file_id}",self._max_download_bytes,self.meter,self.response_reserve,
                params={"fields":"file_id,access,file_name,data_format,data_type,analysis.workflow_type,md5sum,file_size"})
            metadata_bytes=len(metadata.content)
            info=metadata.json().get("data",{})
            declared=info.get('file_size')
            if info.get('file_id',file_id) != file_id:raise ValueError('source file identity mismatch')
            if info.get("access")!="open":raise ValueError("only explicitly open GDC files may be acquired")
            if declared is not None and (isinstance(declared,bool) or not isinstance(declared,int) or declared<0):
                raise ValueError('invalid advertised GDC file size')
            if declared is not None and declared>self._max_download_bytes:
                raise ResourceRejected("artifact exceeds byte budget",0)
            chunks=[]
            reservation=self.reserve(block_id,declared) if self.reserve else nullcontext(None)
            with reservation as capacity:
                async with self._client.stream("GET",f"/data/{file_id}") as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_raw(chunk_size=min(65536,self._max_download_bytes+1,capacity.capacity+1 if capacity else self._max_download_bytes+1)):
                        size+=len(chunk)
                        try:
                            if capacity is not None:capacity.consume(len(chunk))
                        finally:
                            if self.meter is not None:self.meter(len(chunk))
                        if size>self._max_download_bytes:raise ResourceRejected("artifact exceeds byte budget",size)
                        chunks.append(chunk)
                data=b"".join(chunks)
                if declared is not None and declared!=size:raise ValueError("file size differs from source metadata")
                if info.get("md5sum") and hashlib.md5(data).hexdigest()!=info["md5sum"]:
                    raise ValueError("source MD5 differs from retained bytes")
                artifact=ScientificArtifact(block_id=block_id,source="gdc",request={"file_id":file_id,"metadata":info},
                    source_identity=file_id,content_base64=base64.b64encode(data).decode("ascii"),
                    byte_sha256=hashlib.sha256(data).hexdigest(),size_bytes=size,format=format,
                    provenance=("https://api.gdc.cancer.gov",f"/data/{file_id}"))
                status='retained_bytes_validated'
                return artifact
        except BaseException as error:
            error_type=type(error).__name__
            raise
        finally:
            if self.transfer_receipt:
                self.transfer_receipt(block_id, {'file_id':file_id,'declared_size':declared,'metadata_bytes':metadata_bytes,
                    'transferred_bytes':size,'status':status,'error_type':error_type})

    def _validate_size(self, response: httpx.Response) -> None:
        if len(response.content) > self._max_download_bytes:
            raise ResourceRejected("public source response exceeded the configured byte budget", len(response.content))


class XenaPublicSource:
    """Anonymous bounded Xena Hub dataset search; no credentials exist here."""
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None, max_download_bytes: int = 10_000_000) -> None:
        self._client=httpx.AsyncClient(base_url="https://ucscpublic.xenahubs.net",transport=transport,headers={"Accept":"application/json"},timeout=20)
        if max_download_bytes <= 0: raise ValueError("download ceiling must be positive")
        self._max_download_bytes=min(max_download_bytes, 10_000_000)
        self.meter = None
        self.response_reserve = None
    async def aclose(self):
        await self._client.aclose()

    async def search_datasets(self, query: str, limit: int = 10) -> AcquisitionRecord:
        if not 1 <= limit <= 50: raise ValueError("limit must be between 1 and 50")
        if not re.fullmatch(r"[A-Za-z0-9 ._-]{1,100}", query): raise ValueError("query must contain only simple search text")
        escaped=query.replace('"', '\\"')
        xena_query=f'(query {{:select [:dataset.name :dataset.longtitle :dataset.type] :from [:dataset] :where [:like :dataset.name "%{escaped}%"] :limit {limit}}})'
        response=await bounded_response(self._client,"POST","/data/",self._max_download_bytes,self.meter,self.response_reserve,content=xena_query,headers={"Content-Type":"text/plain"})
        if len(response.content)>self._max_download_bytes:raise ResourceRejected("public source response exceeded the configured byte budget", len(response.content))
        body=response.json()
        if not isinstance(body,list): raise ValueError("unexpected Xena dataset response")
        return AcquisitionRecord(source="ucsc-xena",request={"query":query,"limit":limit,"xena_query":xena_query},records=tuple(body),provenance=("https://ucscpublic.xenahubs.net/data/",),response_bytes=len(response.content))


class PublicLiteratureSource:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None, max_download_bytes: int = 10_000_000) -> None:
        self._client=httpx.AsyncClient(base_url="https://api.crossref.org",transport=transport,headers={"Accept":"application/json"},timeout=20)
        if max_download_bytes <= 0: raise ValueError("download ceiling must be positive")
        self._max_download_bytes=min(max_download_bytes, 10_000_000)
        self.meter = None
    async def aclose(self):
        await self._client.aclose()

    async def search(self, query: str, limit: int = 5) -> LiteratureSearchResult:
        if not 1 <= limit <= 20: raise ValueError("limit must be between 1 and 20")
        response=await bounded_response(self._client,"GET","/works",self._max_download_bytes,self.meter,params={"query":query,"rows":limit})
        if len(response.content)>self._max_download_bytes:raise ResourceRejected("public source response exceeded the configured byte budget", len(response.content))
        message = response.json().get("message", {})
        items = message.get("items", [])
        records = []
        remaining_abstract_bytes = 8192
        for item in items[:limit]:
            abstract = item.get("abstract")
            truncated = False
            if isinstance(abstract, str) and abstract.strip():
                encoded = abstract.encode("utf-8")
                retained = encoded[:min(2048, remaining_abstract_bytes)].decode("utf-8", errors="ignore")
                truncated = retained != abstract
                remaining_abstract_bytes -= len(retained.encode("utf-8"))
                abstract = retained or None
            else:
                abstract = None
            records.append(LiteratureRecord(title=(item.get("title") or ["Untitled"])[0],
                doi=item.get("DOI"), url=item.get("URL"), source="crossref",
                abstract=abstract, abstract_truncated=truncated))
        total = message.get("total-results")
        if type(total) is not int or total < 0:
            total = None
        coverage = CoverageContract(endpoint="/works", requested_size=limit,
            returned_rows=len(records), reported_total=total, ordering="Crossref query relevance",
            complete=False, limitations=(
                "One bounded Crossref metadata query; not comprehensive literature coverage.",
                "Deposited abstracts may be absent; no full text was acquired.",
                "Abstracts retain raw source text/markup, at most 2048 UTF-8 bytes per work and 8192 per query; truncation is explicit.",
                "An empty result does not establish novelty or absence of contrary reports.",
            ))
        return LiteratureSearchResult(query=query, request={"query":query,"rows":limit},
            records=tuple(records), provenance=("https://api.crossref.org/works",),
            response_bytes=len(response.content), retrieved_at=datetime.now(UTC), coverage=coverage)
