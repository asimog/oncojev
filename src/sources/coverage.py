"""Conservative combination of explicitly ordered retained metadata pages."""
from src.sources.models import AcquisitionRecord,CoverageContract
from src.provenance import content_hash


def combine_pages(pages:tuple[AcquisitionRecord,...])->AcquisitionRecord:
    if not pages:raise ValueError("pages required")
    pages=tuple(sorted(pages,key=lambda p:p.coverage.offset if p.coverage else -1))
    base=pages[0];seen=set();rows=[];expected=0;totals=set()
    signature=lambda p:content_hash({"source":p.source,"provenance":p.provenance,"query":{k:v for k,v in p.request.items() if k not in {"from","size"}}})
    for page in pages:
        coverage=page.coverage
        if coverage is None or signature(page)!=signature(base) or coverage.ordering != base.coverage.ordering:
            raise ValueError("pages must share query, source and declared ordering")
        if coverage.offset!=expected:raise ValueError("repeated, missing or noncontiguous page")
        expected+=len(page.records)
        totals.add(coverage.reported_total)
        for row in page.records:
            key=row.get(coverage.id_field or "id")
            if not isinstance(key,str) or not key:raise ValueError("page lacks entity identity")
            if key in seen:raise ValueError("overlapping entity rows cannot establish completeness")
            seen.add(key);rows.append(row)
    if len(totals)!=1:raise ValueError("source total changed across pages")
    total=totals.pop()
    complete=total is not None and expected==total
    coverage=CoverageContract(endpoint=base.coverage.endpoint,returned_rows=len(rows),reported_total=total,
        ordering=base.coverage.ordering,id_field=base.coverage.id_field,unique_entities=len(seen),complete=complete,
        limitations=("Ordered observed pages; source snapshot consistency and population representativeness are not guaranteed.",))
    return AcquisitionRecord(source=base.source,request={"page_content_sha256":[p.content_sha256 for p in pages],"query":base.request},
        records=tuple(rows),provenance=base.provenance,coverage=coverage,
        response_bytes=sum(p.response_bytes for p in pages) if all(p.response_bytes is not None for p in pages) else None)
