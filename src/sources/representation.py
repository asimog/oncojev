"""Bounded need-to-retained-schema checks before semantic sufficiency."""
import math
from typing import Literal

from pydantic import BaseModel, Field
from src.sources.models import AcquisitionRecord


class RepresentationNeed(BaseModel, frozen=True):
    estimand: str = Field(min_length=1, max_length=1000)
    representation: Literal["metadata", "paired_data", "expression_matrix", "mutation_events",
                            "cnv_segments", "gene_summary", "pathway_summary", "clinical", "survival"] | None = None
    entity_key: str | None = Field(default=None, max_length=100)
    entity_unit: str | None = Field(default=None, max_length=100)
    fields: dict[str, str] = Field(default_factory=dict, max_length=20)
    numeric_roles: tuple[str, ...] = Field(default=(), max_length=20)
    units: dict[str, str] = Field(default_factory=dict, max_length=20)
    identities: dict[str, str] = Field(default_factory=dict, max_length=10)
    require_complete_coverage: bool = False
    minimum_complete_rows: int = Field(default=1, ge=1, le=100)
    # Unknown need fields are retained by the caller's semantic payload; they do
    # not become a deterministic input contract or an execution grant.


def field_value(row, path, missing=None):
    if len(path) > 100 or len(path.split(".")) > 5:
        raise ValueError("bounded scalar schema path required")
    value = row
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return missing
        value = value[part]
    return value


def assess_retained_representation(record: AcquisitionRecord, need: RepresentationNeed):
    """Source facts only. Query terms and file names never establish assay units."""
    rows = record.records[:100]
    endpoint = record.coverage.endpoint if record.coverage else None
    unit = {"files": "file", "cases": "case", "projects": "project", "annotations": "annotation"}.get(endpoint) if record.source == "gdc" else None
    parsed_star = record.source == "gdc-star-counts" and record.request.get("parser_version") == "gdc-star-gene-selection-v1"
    parsed_table = record.source == "gdc-derived" and record.request.get("transform_version") in {"gdc-tabular-transform-v1", "gdc-tabular-transform-v2"}
    if parsed_star: unit = "gene_in_file"
    if parsed_table: unit = record.request.get("entity_unit")
    metadata = record.source in {"gdc", "xena"}
    profile = {"acquisition_id": record.acquisition_id, "source": record.source,
        "content_sha256": record.content_sha256, "request": record.request,
        "observed_representation": record.request["representation"] if parsed_table else "gene_summary" if parsed_star else "metadata" if metadata else "structured_rows",
        "entity_unit": unit, "inspected_rows": len(rows), "omitted_rows": max(0, len(record.records)-len(rows)),
        "coverage": record.coverage.model_dump(mode="json") if record.coverage else None}
    if parsed_star:
        profile.update({key: record.request[key] for key in ("parser_version", "input_artifact", "byte_sha256",
            "selected_gene_ids", "missing_gene_ids", "source_gene_count", "gene_model")})
    gaps = []
    def gap(code, requirement, observed=None):
        gaps.append({"code": code, "requirement": requirement, "observed": observed})
    if need.representation is None:
        gap("unspecified_representation", "declare the representation required by the estimand")
    elif metadata and need.representation != "metadata":
        gap("metadata_only", need.representation, "metadata does not contain acquired assay bytes or a validated parsed matrix")
    elif parsed_table and need.representation not in {record.request["representation"], "paired_data"}:
        gap("incompatible_derived_representation", need.representation, record.request["representation"])
    elif parsed_star and need.representation not in {"gene_summary", "paired_data"}:
        gap("unsupported_derived_representation", need.representation, "one parsed file cannot establish a sample/cohort matrix or another assay")
    elif not parsed_table and not parsed_star and not metadata and need.representation not in {"metadata", "paired_data"}:
        gap("unmeasured_assay_schema", need.representation, "structured rows alone do not establish a modality contract")
    if parsed_table:
        profile.update(transform_version=record.request["transform_version"], operation=record.request["operation"],
            input_references=record.request["input_references"], omitted_entities=record.request["omitted_entities"])
    if not rows:
        gap("empty_inspected_response", "nonempty retained inputs")
    if need.entity_unit and need.entity_unit != unit:
        gap("unmeasured_entity_unit" if unit is None else "incompatible_entity_unit", need.entity_unit, unit)
    if need.representation == "paired_data" and (not need.entity_key or len(need.fields) < 2):
        gap("incomplete_pairing_contract", "entity key and at least two mapped variables")
    if need.entity_key:
        entities = [field_value(row, need.entity_key) for row in rows]
        scalar = all(isinstance(v, (str, int)) and not isinstance(v, bool) and v != "" for v in entities)
        if not scalar:
            gap("missing_entity_identity", need.entity_key)
        elif len(set(entities)) != len(entities):
            gap("duplicate_entity_identity", "one row per declared entity; aggregation requires a separate validated operation")
    if set(need.numeric_roles) - set(need.fields) or set(need.units) - set(need.fields):
        raise ValueError("numeric roles and units must name mapped variables")
    counts = {}
    complete = 0
    for role, path in need.fields.items():
        missing = object()
        values = [field_value(row, path, missing) for row in rows]
        valid = [v is not missing and v is not None and (role not in need.numeric_roles or
                 isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)) for v in values]
        absent = sum(v is missing for v in values)
        nulls = sum(v is None for v in values)
        counts[role] = {"field": path, "valid_rows": sum(valid), "absent_rows": absent,
                        "null_rows": nulls, "invalid_rows": len(rows)-sum(valid)-absent-nulls}
        if not any(valid):
            gap("absent_field" if absent == len(rows) else "unmeasured_or_incompatible_field", {role: path})
    for row in rows:
        values = {role: field_value(row, path) for role, path in need.fields.items()}
        if values and all(value is not None and (role not in need.numeric_roles or
            isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)) for role, value in values.items()):
            complete += 1
    if need.fields and complete < need.minimum_complete_rows:
        gap("insufficient_complete_rows", need.minimum_complete_rows, complete)
    # Units and release/build/annotation identities must occur as explicit
    # source-returned facts. We never read them from caller query parameters.
    for role, expected in need.units.items():
        observed = [field_value(row, "units." + need.fields[role]) for row in rows]
        if any(v is None for v in observed) or not observed:
            gap("unmeasured_units", {role: expected})
        elif any(v != expected for v in observed):
            gap("incompatible_units", {role: expected}, sorted({str(v) for v in observed}))
    for path, expected in need.identities.items():
        observed = [field_value(row, path) for row in rows]
        if any(v is None for v in observed) or not observed:
            gap("unmeasured_identity", {path: expected})
        elif any(v != expected for v in observed):
            gap("incompatible_identity", {path: expected}, sorted({str(v) for v in observed}))
    if need.require_complete_coverage and (not record.coverage or not record.coverage.complete):
        gap("unmeasured_complete_coverage", "complete retained source coverage")
    if profile["omitted_rows"]:
        gap("bounded_schema_inspection", "validate all rows through the selected Science operation", profile["omitted_rows"])
    access = {row.get("access", "unknown") for row in rows} if endpoint == "files" and record.source == "gdc" else set()
    status = "directly_available" if not gaps else "unmeasured"
    if gaps and access == {"controlled"} and need.representation != "metadata":
        status = "controlled_inaccessible"
    elif gaps and any(g["code"] == "absent_field" for g in gaps):
        status = "absent_from_inspected_source"
    return {"version": "representation-input-v1", "need": need.model_dump(mode="json"),
            "representation": {**profile, "variables": counts, "complete_rows": complete},
            "eligible": not gaps, "availability": status, "unmet_requirements": gaps,
            "limitations": ["Eligibility is input sufficiency for the declared need, never scientific validity or execution authority.",
                            "Absent fields refer only to inspected source rows; missing inputs are not biological negatives.",
                            "Participant independence, joins, assay semantics and population representativeness are not inferred."]}


def representation_alternatives(records, artifacts, need: RepresentationNeed, *, limit=20):
    """Inspect bounded retained assets by schema/modality, independent of query wording."""
    from src.provenance import content_hash
    if not 1 <= limit <= 20 or len(records) > 20 or len(artifacts) > 20:
        raise ValueError('bounded owned asset alternatives required')
    alternatives = []
    supported = {'Masked Somatic Mutation': ('mutation_events', 'parse_gdc_table'),
        'Copy Number Segment': ('cnv_segments', 'parse_gdc_table'),
        'Gene Expression Quantification': ('gene_summary', 'parse_gdc_star_counts')}
    for record in records:
        checks = assess_retained_representation(record, need)
        alternatives.append({'candidate_id': record.acquisition_id, 'acquisition_id': record.acquisition_id,
            'content_sha256': record.content_sha256, 'availability': checks['availability'],
            'input_ready': checks['eligible'], 'checks': checks, 'operation': None})
        if record.source == 'gdc' and record.coverage and record.coverage.endpoint == 'cases' and need.representation in {'clinical', 'survival'}:
            alternatives.append({'candidate_id': content_hash({'source': record.content_sha256, 'operation': 'derive_gdc_clinical', 'need': need.model_dump(mode='json')}),
                'acquisition_id': record.acquisition_id, 'availability': 'derivable', 'input_ready': False,
                'operation': 'derive_gdc_clinical', 'representation': need.representation, 'entity_unit': 'case',
                'limitations': ['Validate source keys and clinical/time fields before readiness; missing cases remain missing.']})
        if record.source == 'gdc' and record.coverage and record.coverage.endpoint == 'files':
            for file in record.records:
                contract = supported.get(file.get('data_type'))
                if not contract: continue
                modality, operation = contract
                if need.representation and modality != need.representation and not (need.representation == 'expression_matrix' and modality == 'gene_summary'):
                    continue
                access = file.get('access')
                required = ('file_id', 'data_format', 'data_type', 'access')
                schema = file.get('data_format') in {'MAF', 'TXT', 'TSV'}
                if modality == 'gene_summary': schema = schema and file.get('analysis', {}).get('workflow_type') == 'STAR - Counts'
                alternatives.append({'candidate_id': content_hash({'acquisition': record.acquisition_id, 'file': file.get('file_id')}),
                    'acquisition_id': record.acquisition_id, 'file_id': file.get('file_id'), 'source_content_sha256': record.content_sha256,
                    'availability': 'controlled_inaccessible' if access == 'controlled' else 'derivable' if access == 'open' and schema and all(file.get(k) is not None for k in required) else 'unmeasured',
                    'input_ready': False, 'representation': modality, 'operation': operation,
                    'schema': {k: file.get(k) for k in required},
                    'limitations': ['Acquire exact file bytes, validate parser, then link explicit samples/cases; file metadata is not assay data.',
                                   'Compression, genome build, missingness and cohort coverage require actual bytes and source linkage.']})
    for artifact in artifacts:
        metadata = artifact.request.get('metadata', {})
        contract = supported.get(metadata.get('data_type')) if artifact.source == 'gdc' else None
        if not contract: continue
        modality, operation = contract
        if need.representation and modality != need.representation and not (need.representation == 'expression_matrix' and modality == 'gene_summary'): continue
        alternatives.append({'candidate_id': artifact.artifact_id, 'artifact_id': artifact.artifact_id,
            'byte_sha256': artifact.byte_sha256, 'representation': modality, 'operation': operation,
            'availability': 'derivable' if artifact.access == 'open' else 'controlled_inaccessible',
            'input_ready': False, 'limitations': ['Owned bytes still require the supported parser and declared entity/unit/build checks.']})
    return {'version': 'representation-alternatives-v1', 'need': need.model_dump(mode='json'), 'candidates': alternatives[:limit],
        'omitted_candidates': max(0, len(alternatives)-limit),
        'omitted_candidate_ids': [candidate['candidate_id'] for candidate in alternatives[limit:]],
        'acquisition_ids': [record.acquisition_id for record in records], 'artifact_ids': [artifact.artifact_id for artifact in artifacts], 'inspected_acquisitions': len(records), 'inspected_artifacts': len(artifacts),
        'retrieval': 'bounded owned schema/modality scan; lexical terms do not exclude alternatives', 'authority': 'planning_only'}
