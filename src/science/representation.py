"""Controlled parsing of one source-bound GDC augmented STAR Counts file."""
import csv
import io
import math
import re

from pydantic import BaseModel
from src.provenance import ExecutionReference, content_hash
from src.science.models import InvalidAnalysis
from src.sources.models import AcquisitionRecord, CoverageContract, ScientificArtifact

PARSER_VERSION = "gdc-star-gene-selection-v1"
REFERENCE = "https://docs.gdc.cancer.gov/Data/Bioinformatics_Pipelines/Expression_mRNA_Pipeline/"
COLUMNS = ("gene_id", "gene_name", "gene_type", "unstranded", "stranded_first", "stranded_second",
           "tpm_unstranded", "fpkm_unstranded", "fpkm_uq_unstranded")
UNITS = {"unstranded": "read_count", "stranded_first": "read_count", "stranded_second": "read_count",
         "tpm_unstranded": "TPM", "fpkm_unstranded": "FPKM", "fpkm_uq_unstranded": "FPKM-UQ"}
SUMMARY_ROWS = {"N_unmapped", "N_multimapping", "N_noFeature", "N_ambiguous"}
GENE = re.compile(r"ENSG[0-9]+(?:\.[0-9]+)?(?:_PAR_Y)?")


class RepresentationParseReceipt(BaseModel, frozen=True):
    parser_version: str = PARSER_VERSION
    input_reference: ExecutionReference
    output_reference: ExecutionReference
    byte_sha256: str
    source_gene_count: int
    selected_gene_ids: tuple[str, ...]
    missing_gene_ids: tuple[str, ...]
    gene_model: str | None
    units: dict[str, str]
    limitations: tuple[str, ...]


def parse_gdc_star_counts(artifact: ScientificArtifact, gene_ids: tuple[str, ...]):
    """Validate the entire bounded table; retain only requested exact gene IDs."""
    if not 1 <= len(gene_ids) <= 20 or len(set(gene_ids)) != len(gene_ids) or any(len(g)>64 or not GENE.fullmatch(g) for g in gene_ids):
        raise InvalidAnalysis("select 1..20 unique exact Ensembl gene IDs; versions are not interchangeable")
    metadata = artifact.request.get("metadata", {})
    if not isinstance(metadata, dict) or not isinstance(metadata.get("analysis"), dict):
        raise InvalidAnalysis("explicit STAR metadata required")
    if (artifact.source != "gdc" or artifact.access != "open" or artifact.format != "tsv"
        or metadata.get("access") != "open" or metadata.get("data_format") != "TSV"
        or metadata.get("data_type") != "Gene Expression Quantification"
        or metadata.get("analysis", {}).get("workflow_type") != "STAR - Counts"
        or metadata.get("file_id") != artifact.source_identity or artifact.request.get("file_id") != artifact.source_identity):
        raise InvalidAnalysis("explicit open GDC STAR Counts TSV source metadata required")
    if artifact.size_bytes > 8*1024*1024:
        raise InvalidAnalysis("STAR parser byte bound exceeded")
    data = artifact.bytes()
    try:
        lines = io.StringIO(data.decode("utf-8"), newline="")
    except UnicodeDecodeError as error:
        raise InvalidAnalysis("STAR table requires UTF-8 TSV") from error
    first = lines.readline()
    gene_model = None
    if first.startswith("# gene-model: "):
        gene_model = first.removeprefix("# gene-model: ").strip()
        if not gene_model or len(gene_model) > 200:
            raise InvalidAnalysis("bounded source gene-model declaration required")
        first = lines.readline()
    if tuple(first.rstrip("\r\n").split("\t")) != COLUMNS:
        raise InvalidAnalysis("unsupported STAR table header; no inferred columns or normalization")
    seen = set(); selected = {}; summaries = set(); wanted = set(gene_ids)
    for row in csv.reader(lines, delimiter="\t", quoting=csv.QUOTE_NONE):
        if len(row) != len(COLUMNS) or any(len(cell) > 200 for cell in row):
            raise InvalidAnalysis("malformed or oversized STAR row")
        identity = row[0]
        if identity in seen:
            raise InvalidAnalysis("duplicate STAR entity identity; aggregation is not implemented")
        seen.add(identity)
        summary = identity in SUMMARY_ROWS
        if len(seen)-len(summaries)-int(summary) > 100000:
            raise InvalidAnalysis("STAR gene row bound exceeded")
        if not summary and not GENE.fullmatch(identity):
            raise InvalidAnalysis("unsupported STAR gene identity")
        values = {}
        for column, cell in zip(COLUMNS[3:6], row[3:6]):
            if not re.fullmatch(r"[0-9]+", cell):
                raise InvalidAnalysis("STAR read counts require nonnegative integers")
            values[column] = int(cell)
            if values[column] > 2**63-1:
                raise InvalidAnalysis("STAR read count exceeds supported integer range")
        for column, cell in zip(COLUMNS[6:], row[6:]):
            if summary:
                if cell != "": raise InvalidAnalysis("STAR summary rows must not supply gene normalization")
                continue
            try: value = float(cell)
            except ValueError as error: raise InvalidAnalysis("missing or invalid STAR normalized expression") from error
            if not math.isfinite(value) or value < 0:
                raise InvalidAnalysis("STAR normalized expression requires finite nonnegative values")
            values[column] = value
        if summary:
            summaries.add(identity); continue
        if not row[1] or not row[2]:
            raise InvalidAnalysis("STAR gene annotation missing")
        if identity in wanted:
            selected[identity] = {"gene_id": identity, "gene_name": row[1], "gene_type": row[2],
                **values, "units": dict(UNITS), "file_id": artifact.source_identity, "gene_model": gene_model}
    total = len(seen)-len(summaries)
    if total < 1:
        raise InvalidAnalysis("STAR table has no gene rows")
    missing = tuple(g for g in gene_ids if g not in selected)
    input_ref = ExecutionReference(kind="scientific_artifact", value=artifact.artifact_id,
        sha256=content_hash(artifact.model_dump(mode="json")), block_id=artifact.block_id)
    limitations = ("One file, selected genes; no sample/aliquot/case linkage, participant independence or cohort matrix is inferred.",
        "Gene IDs retain exact source versions; no identifier remapping, joins, aggregation or normalization conversion is performed.",
        "Missing selected genes remain absent, never zero; observed zero expression remains zero.",
        "Genome build, release and population coverage remain unknown unless separately source-bound.",
        "Parsing validates format/units, not biological conclusions, model assumptions or reusable qualification.")
    record = AcquisitionRecord(source="gdc-star-counts", request={"parser_version": PARSER_VERSION,
        "input_artifact": input_ref.model_dump(mode="json"), "byte_sha256": artifact.byte_sha256,
        "selected_gene_ids": list(gene_ids), "missing_gene_ids": list(missing), "source_gene_count": total,
        "gene_model": gene_model}, records=tuple(selected[g] for g in gene_ids if g in selected),
        response_bytes=len(data), provenance=(REFERENCE, PARSER_VERSION, artifact.artifact_id),
        coverage=CoverageContract(endpoint="selected_genes_in_one_file", requested_size=len(gene_ids),
            returned_rows=len(selected), reported_total=len(gene_ids), id_field="gene_id", unique_entities=len(selected),
            ordering="requested exact gene order", complete=not missing, limitations=limitations))
    receipt = RepresentationParseReceipt(input_reference=input_ref,
        output_reference=ExecutionReference(kind="acquisition", value=record.acquisition_id,
            sha256=content_hash(record.model_dump(mode="json")), block_id=artifact.block_id),
        byte_sha256=artifact.byte_sha256, source_gene_count=total, selected_gene_ids=gene_ids,
        missing_gene_ids=missing, gene_model=gene_model, units=dict(UNITS), limitations=limitations)
    return record, receipt
