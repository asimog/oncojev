from typing import Any
import re

import httpx

from src.sources.models import AcquisitionRecord, LiteratureRecord, LiteratureSearchResult


class GdcPublicSource:
    """Anonymous-only GDC metadata wrapper. It accepts no credential input."""
    allowed_endpoints = frozenset({"projects", "cases", "files", "annotations"})

    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._client = httpx.AsyncClient(base_url="https://api.gdc.cancer.gov", transport=transport, headers={"Accept": "application/json"}, timeout=20)

    async def search(self, endpoint: str, filters: dict[str, Any], fields: tuple[str, ...], size: int = 10) -> AcquisitionRecord:
        if endpoint not in self.allowed_endpoints: raise ValueError("unsupported public GDC endpoint")
        if not 1 <= size <= 100: raise ValueError("size must be between 1 and 100")
        content = list(filters.get("content", [])) if filters.get("op") == "and" else [filters]
        if endpoint == "files": content.append({"op":"in","content":{"field":"files.access","value":["open"]}})
        payload={"filters":{"op":"and","content":content},"fields":",".join(fields),"format":"JSON","size":size}
        response=await self._client.post(f"/{endpoint}",json=payload);response.raise_for_status();body=response.json();hits=body.get("data",{}).get("hits",[])
        return AcquisitionRecord(source="gdc",request=payload,records=tuple(hits[:size]),provenance=("https://api.gdc.cancer.gov",endpoint))


class XenaPublicSource:
    """Anonymous bounded Xena Hub dataset search; no credentials exist here."""
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._client=httpx.AsyncClient(base_url="https://ucscpublic.xenahubs.net",transport=transport,headers={"Accept":"application/json"},timeout=20)
    async def search_datasets(self, query: str, limit: int = 10) -> AcquisitionRecord:
        if not 1 <= limit <= 50: raise ValueError("limit must be between 1 and 50")
        if not re.fullmatch(r"[A-Za-z0-9 ._-]{1,100}", query): raise ValueError("query must contain only simple search text")
        escaped=query.replace('"', '\\"')
        xena_query=f'(query {{:select [:dataset.name :dataset.longtitle :dataset.type] :from [:dataset] :where [:like :dataset.name "%{escaped}%"] :limit {limit}}})'
        response=await self._client.post("/data/",content=xena_query,headers={"Content-Type":"text/plain"});response.raise_for_status();body=response.json()
        if not isinstance(body,list): raise ValueError("unexpected Xena dataset response")
        return AcquisitionRecord(source="ucsc-xena",request={"query":query,"limit":limit,"xena_query":xena_query},records=tuple(body),provenance=("https://ucscpublic.xenahubs.net/data/",))


class PublicLiteratureSource:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._client=httpx.AsyncClient(base_url="https://api.crossref.org",transport=transport,headers={"Accept":"application/json"},timeout=20)
    async def search(self, query: str, limit: int = 5) -> LiteratureSearchResult:
        if not 1 <= limit <= 20: raise ValueError("limit must be between 1 and 20")
        response=await self._client.get("/works",params={"query":query,"rows":limit});response.raise_for_status();items=response.json().get("message",{}).get("items",[])
        records=tuple(LiteratureRecord(title=(item.get("title") or ["Untitled"])[0],doi=item.get("DOI"),url=item.get("URL"),source="crossref") for item in items[:limit])
        return LiteratureSearchResult(query=query,records=records,provenance=("https://api.crossref.org/works",))
