from typing import Any
import re
import asyncio

import httpx

from src.runtime.resources import ResourceRejected
from src.sources.models import AcquisitionRecord, CoverageContract, ScientificArtifact, LiteratureRecord, LiteratureSearchResult


async def bounded_response(client, method, url, ceiling, meter=None, **kwargs):
    """Bound decoded response content while streaming, including failed attempts."""
    chunks = []
    size = 0
    async with client.stream(method, url, **kwargs) as response:
        response.raise_for_status()
        declared = response.headers.get("content-length")
        if declared is not None and int(declared) > ceiling:
            raise ResourceRejected("public source response exceeded the configured byte budget", size)
        async for chunk in response.aiter_bytes(chunk_size=min(65536, ceiling + 1)):
            size += len(chunk)
            if meter is not None:
                meter(len(chunk))
            if size > ceiling:
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

    async def aclose(self):
        await self._client.aclose()

    async def search(self, endpoint: str, filters: dict[str, Any], fields: tuple[str, ...], size: int = 10, offset: int = 0, sort: str = "id:asc") -> AcquisitionRecord:
        if endpoint not in self.allowed_endpoints: raise ValueError("unsupported public GDC endpoint")
        if not 1 <= size <= 100: raise ValueError("size must be between 1 and 100")
        if offset < 0 or offset > 1_000_000: raise ValueError("offset is outside bounded pagination")
        if not re.fullmatch(r"[A-Za-z0-9_.]+:(asc|desc)",sort): raise ValueError("declare one stable ordering field")
        content = list(filters.get("content", [])) if filters.get("op") == "and" else [filters]
        if endpoint == "files": content.append({"op":"in","content":{"field":"files.access","value":["open"]}})
        payload={"filters":{"op":"and","content":content},"fields":",".join(fields),"format":"JSON","size":size,"from":offset,"sort":sort}
        response=await bounded_response(self._client,"POST",f"/{endpoint}",self._max_download_bytes,self.meter,json=payload);body=await asyncio.to_thread(response.json);hits=body.get("data",{}).get("hits",[])
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

    async def acquire_file(self,file_id:str,block_id:str,format:str)->ScientificArtifact:
        """A single open GDC file; no credentials, arbitrary URL or redirects."""
        import base64
        import hashlib
        from uuid import UUID
        UUID(file_id)
        if format not in {"tsv","json","text","binary","gzip"}:raise ValueError("declare supported byte format")
        metadata=await bounded_response(self._client,"GET",f"/files/{file_id}",self._max_download_bytes,self.meter,params={"fields":"access,file_name,data_format,md5sum,file_size"})
        metadata.raise_for_status();self._validate_size(metadata)
        info=metadata.json().get("data",{})
        if info.get("access")!="open":raise ValueError("only explicitly open GDC files may be acquired")
        if isinstance(info.get("file_size"),int) and info["file_size"]>self._max_download_bytes:
            raise ResourceRejected("artifact exceeds byte budget", 0)
        chunks=[];size=0
        async with self._client.stream("GET",f"/data/{file_id}") as response:
            response.raise_for_status()
            async for chunk in response.aiter_raw(chunk_size=min(65536,self._max_download_bytes+1)):
                size+=len(chunk)
                if self.meter is not None:self.meter(len(chunk))
                if size>self._max_download_bytes:raise ResourceRejected("artifact exceeds byte budget", size)
                chunks.append(chunk)
        data=b"".join(chunks)
        if info.get("file_size") is not None and info["file_size"]!=size:raise ValueError("file size differs from source metadata")
        if info.get("md5sum") and hashlib.md5(data).hexdigest()!=info["md5sum"]:raise ValueError("source MD5 differs from retained bytes")
        return ScientificArtifact(block_id=block_id,source="gdc",request={"file_id":file_id,"metadata":info},source_identity=file_id,
            content_base64=base64.b64encode(data).decode("ascii"),byte_sha256=hashlib.sha256(data).hexdigest(),size_bytes=size,format=format,
            provenance=("https://api.gdc.cancer.gov",f"/data/{file_id}"))

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
    async def aclose(self):
        await self._client.aclose()

    async def search_datasets(self, query: str, limit: int = 10) -> AcquisitionRecord:
        if not 1 <= limit <= 50: raise ValueError("limit must be between 1 and 50")
        if not re.fullmatch(r"[A-Za-z0-9 ._-]{1,100}", query): raise ValueError("query must contain only simple search text")
        escaped=query.replace('"', '\\"')
        xena_query=f'(query {{:select [:dataset.name :dataset.longtitle :dataset.type] :from [:dataset] :where [:like :dataset.name "%{escaped}%"] :limit {limit}}})'
        response=await bounded_response(self._client,"POST","/data/",self._max_download_bytes,self.meter,content=xena_query,headers={"Content-Type":"text/plain"})
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
        items=response.json().get("message",{}).get("items",[])
        records=tuple(LiteratureRecord(title=(item.get("title") or ["Untitled"])[0],doi=item.get("DOI"),url=item.get("URL"),source="crossref") for item in items[:limit])
        return LiteratureSearchResult(query=query,request={"query":query,"rows":limit},records=records,provenance=("https://api.crossref.org/works",),response_bytes=len(response.content))
