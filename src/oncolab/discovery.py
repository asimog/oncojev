"""Bounded mutable-source capability discovery, separate from registry authority."""
import base64
import hashlib
import json
import re
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlparse
from uuid import uuid4
from typing import Literal

import httpx
from pydantic import BaseModel, Field

from src.provenance import content_hash
from src.sources.public import bounded_response


class ExternalCapabilityCandidate(BaseModel, frozen=True):
    source: str
    external_id: str
    name: str
    description: str
    homepage: str | None = None
    licence: str | None = None
    versions: tuple[str, ...] = ()
    tool_types: tuple[str, ...] = ()
    topics: tuple[dict, ...] = ()
    operations: tuple[dict, ...] = ()
    inputs: tuple[dict, ...] = ()
    outputs: tuple[dict, ...] = ()
    links: tuple[dict, ...] = ()
    publications: tuple[dict, ...] = ()
    metadata: dict = Field(default_factory=dict)
    limitations: tuple[str, ...] = ("Listing does not establish operation fidelity or scientific validity.",)
    omissions: tuple[str, ...] = ()
    authority: Literal["metadata_only; no installed route or scientific validation"] = "metadata_only; no installed route or scientific validation"


class ExternalLookup(BaseModel, frozen=True):
    lookup_id: str = Field(default_factory=lambda: str(uuid4()))
    source: str
    operation: str
    request: dict
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    response_sha256: str
    response_bytes: int = Field(ge=0)
    raw_json: str
    cards: tuple[ExternalCapabilityCandidate, ...] = Field(max_length=20)
    reported_total: int | None = Field(default=None, ge=0)
    continuation: str | None = None
    omitted: int = Field(default=0, ge=0)
    limitations: tuple[str, ...] = ("Mutable source: retained response is exact, successive pages are not a frozen snapshot.",)


class ExternalDiscovery:
    filters = frozenset({'biotoolsID','name','domain','topic','topicID','operation','operationID',
        'inputDataType','inputDataTypeID','inputDataFormat','inputDataFormatID',
        'outputDataType','outputDataTypeID','outputDataFormat','outputDataFormatID','toolType','license'})

    def __init__(self, transport=None, *, max_bytes=2_000_000):
        self.transport = transport
        if not 1<=max_bytes<=2_000_000:raise ValueError("invalid external response ceiling")
        self.max_bytes = max_bytes
        self.meter = None

    async def _get(self, url, params):
        async with httpx.AsyncClient(transport=self.transport, timeout=20, follow_redirects=False) as client:
            return await bounded_response(client, 'GET', url, self.max_bytes, self.meter, params=params)

    @staticmethod
    def _card(row):
        if not isinstance(row,dict) or not row.get('biotoolsID') or not row.get('name'):
            raise ValueError('invalid bio.tools identity')
        functions = row.get('function') or []
        values = {key: [item for function in functions for item in function.get(key, [])]
                  for key in ('operation','input','output')}
        lists = {'versions': row.get('version') or [], 'tool_types': row.get('toolType') or [],
                 'topics': row.get('topic') or [], 'operations': values['operation'],
                 'inputs': values['input'], 'outputs': values['output'],
                 'links': [*(row.get('link') or []), *(row.get('download') or [])],
                 'publications': row.get('publication') or []}
        omissions = [key for key, items in lists.items() if len(items)>10]
        if len(row.get('description',''))>1500:omissions.append('description')
        # Preserve bounded EDAM IDs/terms and formats without ingesting an ontology.
        def compact(item, depth=0):
            if depth>4:return "nested metadata omitted"
            if isinstance(item,dict):return {str(k)[:100]:compact(v,depth+1) for k,v in list(item.items())[:12]}
            if isinstance(item,list):return [compact(v,depth+1) for v in item[:10]]
            return str(item)[:500] if item is not None else None
        return ExternalCapabilityCandidate(source='bio.tools', external_id=str(row['biotoolsID']),
            name=str(row['name'])[:200], description=str(row.get('description',''))[:1500],
            homepage=row.get('homepage'), licence=row.get('license'), omissions=tuple(omissions),
            **{key:tuple(compact(i) for i in items[:10]) for key,items in lists.items()})

    async def search(self, source, need, filters=None, continuation=None, *, limit=10):
        if source != 'bio.tools':raise ValueError('unsupported external discovery source')
        if not 1<=limit<=20 or not need.strip() or len(need)>1000:raise ValueError('bounded need/limit required')
        filters = filters or {}
        if set(filters)-self.filters or any(not isinstance(v,str) or len(v)>200 for v in filters.values()):
            raise ValueError('unsupported external discovery filter')
        identity=content_hash({'source':source,'need':need,'filters':filters,'limit':limit})
        page=1
        if continuation:
            if len(continuation)>4000:raise ValueError("oversized discovery continuation")
            try:
                cursor=json.loads(base64.urlsafe_b64decode(continuation))
                if cursor['identity']!=identity or not isinstance(cursor['page'],int) or not 1<=cursor['page']<=1000:
                    raise ValueError('changed discovery cursor')
                page=cursor['page']
            except (ValueError,KeyError,TypeError) as error:raise ValueError('invalid discovery continuation') from error
        params={'q':need,'format':'json','page':page,'per_page':limit,'sort':'name','ord':'asc',**filters}
        for key in filters:
            if key.endswith('ID'):params[key]='"'+filters[key].strip('"')+'"'
        response=await self._get('https://bio.tools/api/tool/',params)
        body=response.json()
        rows=body.get('list')
        if not isinstance(rows,list):raise ValueError('invalid bio.tools result list')
        cards=tuple(self._card(row) for row in rows[:limit])
        next_cursor=None
        if body.get('next'):
            parsed=urlparse(body['next'])
            if parsed.netloc and parsed.netloc!='bio.tools':raise ValueError('foreign bio.tools continuation')
            next_page=int(parse_qs(parsed.query).get('page',[page+1])[0])
            if not page<next_page<=1000:raise ValueError('invalid next page')
            next_cursor=base64.urlsafe_b64encode(json.dumps({'identity':identity,'page':next_page}).encode()).decode()
        count=body.get('count')
        count=count if isinstance(count,int) and not isinstance(count,bool) and count>=0 else None
        return ExternalLookup(source=source,operation='search',request=params,
            response_sha256=hashlib.sha256(response.content).hexdigest(), response_bytes=len(response.content),
            raw_json=response.text,cards=cards,reported_total=count,continuation=next_cursor,omitted=max(0,len(rows)-limit))

    async def describe(self, source, external_id):
        if source in {'github','bioconda','bioconductor'}:
            from src.oncolab.enrichment import describe_package
            return await describe_package(self,source,external_id)
        if source!='bio.tools' or not re.fullmatch(r'[A-Za-z0-9._+-]{1,150}',external_id):
            raise ValueError('unsupported source or invalid external identity')
        response=await self._get('https://bio.tools/api/tool/'+external_id+'/',{'format':'json'})
        card=self._card(response.json())
        if card.external_id.casefold()!=external_id.casefold():raise ValueError('external identity mismatch')
        return ExternalLookup(source=source,operation='describe',request={'external_id':external_id},
            response_sha256=hashlib.sha256(response.content).hexdigest(),response_bytes=len(response.content),
            raw_json=response.text,cards=(card,))
