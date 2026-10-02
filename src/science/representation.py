"""Controlled parsing of one source-bound GDC augmented STAR Counts file."""
import csv
import gzip
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


class TabularTransformReceipt(BaseModel, frozen=True):
    version: str = 'gdc-tabular-transform-v1'
    operation: str
    input_references: tuple[ExecutionReference, ...]
    output_reference: ExecutionReference
    input_rows: int
    output_rows: int
    omitted_entities: tuple[str, ...] = ()
    limitations: tuple[str, ...]


def _derived(records, inputs, block_id, operation, representation, entity_unit, *, input_rows, omitted=(), limitations=(), selection=None):
    refs = tuple(ExecutionReference(kind='scientific_artifact' if isinstance(value, ScientificArtifact) else 'acquisition',
        value=value.artifact_id if isinstance(value, ScientificArtifact) else value.acquisition_id,
        sha256=content_hash(value.model_dump(mode='json')), block_id=block_id) for value in inputs)
    limits = (*limitations, 'Validated representation only; no causal interpretation, independent participants or scientific evidence inferred.')
    version = 'gdc-tabular-transform-v2' if selection is not None else 'gdc-tabular-transform-v1'
    record = AcquisitionRecord(source='gdc-derived', request={'transform_version': version,
        'operation': operation, 'representation': representation, 'entity_unit': entity_unit,
        'input_references': [r.model_dump(mode='json') for r in refs], 'omitted_entities': list(omitted),
        **({'selection': selection} if selection is not None else {})},
        records=tuple(records), origin='synthetic' if any(getattr(value, 'origin', 'public') == 'synthetic' for value in inputs) else 'public',
        provenance=tuple(dict.fromkeys(('https://docs.gdc.cancer.gov/', operation, *(ref.value for ref in refs)))),
        coverage=CoverageContract(endpoint=operation, requested_size=input_rows, returned_rows=len(records),
            reported_total=input_rows, id_field='entity_id', unique_entities=len({r['entity_id'] for r in records}),
            ordering='source order', complete=len(records) == input_rows, limitations=limits))
    receipt = TabularTransformReceipt(version=version, operation=operation, input_references=refs,
        output_reference=ExecutionReference(kind='acquisition', value=record.acquisition_id,
            sha256=content_hash(record.model_dump(mode='json')), block_id=block_id),
        input_rows=input_rows, output_rows=len(records), omitted_entities=tuple(omitted), limitations=limits)
    return record, receipt


def parse_gdc_table(artifact: ScientificArtifact, modality: str, gene_symbols: tuple[str, ...] = ()):
    """Validate complete bounded source table; optional exact mutation-gene panel."""
    if (len(gene_symbols) > 20 or len(set(gene_symbols)) != len(gene_symbols)
            or any(not isinstance(g, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", g) for g in gene_symbols)
            or gene_symbols and modality != "mutation_events"):
        raise InvalidAnalysis("select at most 20 unique exact mutation gene symbols")
    metadata = artifact.request.get('metadata', {})
    data_type = {'mutation_events': 'Masked Somatic Mutation', 'cnv_segments': 'Copy Number Segment'}.get(modality)
    if (not data_type or artifact.source != 'gdc' or artifact.access != 'open'
            or metadata.get('access') != 'open' or metadata.get('file_id') != artifact.source_identity
            or artifact.request.get('file_id') != artifact.source_identity
            or metadata.get('data_type') != data_type or artifact.size_bytes > 8 * 1024 * 1024
            or metadata.get('data_format') not in {'MAF', 'TXT', 'TSV'}):
        raise InvalidAnalysis('explicit supported open GDC tabular metadata required')
    raw = artifact.bytes()
    compressed = artifact.format == 'gzip'
    if artifact.format not in {'tsv', 'text', 'gzip'}:
        raise InvalidAnalysis('declare supported TSV/text or gzip byte format')
    if compressed:
        if not str(metadata.get('file_name', '')).endswith('.gz'):
            raise InvalidAnalysis('gzip requires source-declared .gz filename')
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
                data = stream.read(8 * 1024 * 1024 + 1)
        except (OSError, EOFError) as error:
            raise InvalidAnalysis('corrupt or truncated gzip table') from error
        if len(data) > 8 * 1024 * 1024:
            raise InvalidAnalysis('decoded gzip byte bound exceeded')
    else:
        data = raw
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError as error:
        raise InvalidAnalysis('decoded UTF-8 table required') from error
    reader = csv.DictReader((line for line in io.StringIO(text) if not line.startswith('#')), delimiter='\t')
    required = (('Hugo_Symbol', 'NCBI_Build', 'Chromosome', 'Start_Position', 'End_Position', 'Reference_Allele',
                 'Tumor_Seq_Allele2', 'Tumor_Sample_Barcode', 'Variant_Classification') if modality == 'mutation_events'
                else ('GDC_Aliquot', 'Chromosome', 'Start', 'End', 'Num_Probes', 'Segment_Mean'))
    if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames) or not set(required) <= set(reader.fieldnames):
        raise InvalidAnalysis('unsupported or duplicate tabular schema')
    rows, seen, builds = [], set(), set()
    source_rows = 0; wanted = set(gene_symbols); found = set()
    for item in reader:
        source_rows += 1
        if source_rows > 100000 or None in item or any(item.get(key) in (None, '') for key in required) or any(len(str(item[k])) > 500 for k in required) or any(len(str(v)) > 65536 for v in item.values()):
            raise InvalidAnalysis('malformed row or source table row bound exceeded')
        try:
            start = int(item['Start_Position' if modality == 'mutation_events' else 'Start'])
            end = int(item['End_Position' if modality == 'mutation_events' else 'End'])
            if start < 1 or end < start:
                raise ValueError()
            sample = item['Tumor_Sample_Barcode' if modality == 'mutation_events' else 'GDC_Aliquot']
            identity = content_hash({'sample': sample, 'chromosome': item['Chromosome'], 'start': start, 'end': end,
                'reference': item.get('Reference_Allele'), 'tumor': item.get('Tumor_Seq_Allele2')})
            if identity in seen: raise ValueError()
            seen.add(identity)
            if modality == 'mutation_events':
                builds.add(item['NCBI_Build'])
                row = {'entity_id': identity, 'sample_id': sample, 'chromosome': item['Chromosome'],
                    'start': start, 'end': end, 'gene': item['Hugo_Symbol'], 'build': item['NCBI_Build'],
                    'reference_allele': item['Reference_Allele'], 'tumor_allele': item['Tumor_Seq_Allele2'],
                    'classification': item['Variant_Classification'], 'units': {'start': 'base_1', 'end': 'base_1'}}
            else:
                mean, probes = float(item['Segment_Mean']), int(item['Num_Probes'])
                if not math.isfinite(mean) or probes < 0: raise ValueError()
                row = {'entity_id': identity, 'sample_id': sample, 'chromosome': item['Chromosome'], 'start': start, 'end': end,
                    'segment_mean': mean, 'num_probes': probes, 'units': {'segment_mean': 'log2(copy_number/2)', 'start': 'base_1', 'end': 'base_1'}}
        except (ValueError, TypeError) as error:
            raise InvalidAnalysis('invalid coordinates, duplicate event or numerical values') from error
        if not wanted or row['gene'] in wanted:
            if len(rows) >= 100: raise InvalidAnalysis('selected table exceeds 100-row bound; declare a smaller panel')
            rows.append(row)
            if wanted: found.add(row['gene'])
    if not source_rows or len(builds) > 1:
        raise InvalidAnalysis('nonempty table with one source genome build required')
    return _derived(rows, (artifact,), artifact.block_id, 'parse_gdc_table:' + modality, modality,
        'mutation_event' if modality == 'mutation_events' else 'aliquot_segment', input_rows=source_rows,
        selection={'content_encoding': 'gzip' if compressed else 'identity', 'decoded_bytes': len(data),
            'gene_symbols': list(gene_symbols), 'missing_gene_symbols': [g for g in gene_symbols if g not in found],
            'omitted_source_rows': source_rows - len(rows), 'source_validation': 'entire bounded table', 'projected_columns': list(required),
            'discarded_annotation_columns': [c for c in reader.fieldnames if c not in required]} if compressed or wanted or set(reader.fieldnames) - set(required) else None,
        limitations=('No case linkage, absent-variant zeros or gene-level CNV aggregation inferred.',
                     'CNV build remains unknown unless separately source-bound; source coordinates retained.',
                     'Gene-panel selection omits other source events; absent panel genes do not establish mutation absence, callable territory or TMB.'))


def derive_gdc_clinical(record: AcquisitionRecord, block_id: str, representation: str):
    """Case-level clinical fields; strict survival extraction retains missing cases."""
    if record.source != 'gdc' or not record.coverage or record.coverage.endpoint != 'cases' or representation not in {'clinical', 'survival'}:
        raise InvalidAnalysis('owned GDC case response and clinical/survival modality required')
    if not 1 <= len(record.records) <= 100:
        raise InvalidAnalysis('bounded nonempty case response required')
    rows, seen = [], set()
    for case in record.records:
        identity = case.get('case_id')
        if not isinstance(identity, str) or not identity or identity in seen:
            raise InvalidAnalysis('unique case UUID required; no barcode truncation')
        seen.add(identity)
        demographic = case.get('demographic') or {}
        diagnoses = case.get('diagnoses') or []
        if not isinstance(demographic, dict) or not isinstance(diagnoses, list):
            raise InvalidAnalysis('unsupported clinical schema')
        row = {'entity_id': identity, 'case_id': identity, 'demographic': demographic, 'diagnoses': diagnoses}
        if representation == 'survival':
            status = str(demographic.get('vital_status', '')).casefold()
            death = demographic.get('days_to_death')
            followups = [d.get('days_to_last_follow_up') for d in diagnoses if isinstance(d, dict)]
            followups += [d.get('days_to_follow_up') for d in case.get('follow_ups', []) if isinstance(d, dict)]
            duration = death if status == 'dead' else max((v for v in followups if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and v >= 0), default=None) if status == 'alive' else None
            valid = isinstance(duration, (int, float)) and not isinstance(duration, bool) and math.isfinite(duration) and duration >= 0
            row.update(time_days=duration if valid else None, event=1 if status == 'dead' and valid else 0 if status == 'alive' and valid else None,
                       units={'time_days': 'days', 'event': 'death_indicator'}, missing_reason=None if valid else 'unknown vital status or nonnegative duration')
        rows.append(row)
    return _derived(rows, (record,), block_id, 'derive_gdc_clinical:' + representation, representation, 'case', input_rows=len(rows),
        limitations=('Time origin follows source diagnosis-relative fields; heterogeneity and censoring assumptions require assessment.',
                     'No clinical field is fabricated; ambiguous/unknown survival times remain missing.'))


def join_gdc_case_inputs(left: AcquisitionRecord, right: AcquisitionRecord, block_id: str):
    """One-to-one outer join on explicit case UUID; no implicit sample aggregation."""
    for record in (left, right):
        if record.source != 'gdc-derived' or record.request.get('entity_unit') != 'case' or not 1 <= len(record.records) <= 100:
            raise InvalidAnalysis('validated case-level inputs required')
    def indexed(record):
        result = {}
        for row in record.records:
            identity = row.get('case_id')
            if not isinstance(identity, str) or not identity or identity in result:
                raise InvalidAnalysis('unique exact case keys required')
            result[identity] = row
        return result
    a, b = indexed(left), indexed(right)
    keys = sorted(set(a) | set(b))
    if len(keys) > 100: raise InvalidAnalysis('joined case bound exceeded')
    rows = [{'entity_id': key, 'case_id': key, 'left': a.get(key), 'right': b.get(key),
             'pair_complete': key in a and key in b, 'units': {'left': a.get(key, {}).get('units', {}), 'right': b.get(key, {}).get('units', {})}} for key in keys]
    return _derived(rows, (left, right), block_id, 'join_gdc_case_inputs', 'paired_data', 'case', input_rows=len(keys),
        omitted=tuple(key for key in keys if key not in a or key not in b),
        limitations=('Outer join retains unmatched cases as missing; no imputation or deduplication.',
                     'Nested source units/builds remain separate; incompatible variables must fail the declared need.'))


def assemble_gdc_expression(records: tuple[AcquisitionRecord, ...], links: AcquisitionRecord, block_id: str, column: str):
    """Selected genes, one explicitly source-linked file/aliquot per case; no averaging."""
    if column not in UNITS or not 1 <= len(records) <= 20 or links.source != 'gdc' or not links.coverage or links.coverage.endpoint != 'files':
        raise InvalidAnalysis('STAR inputs, supported normalization and source file/case/aliquot links required')
    mapping = {}
    for file in links.records:
        cases = file.get('cases', [])
        if not isinstance(cases, list) or len(cases) != 1 or not isinstance(cases[0], dict):
            raise InvalidAnalysis('one explicitly linked case per expression file required')
        case = cases[0]
        samples = case.get('samples', [])
        aliquots = [(sample.get('sample_id'), aliquot.get('aliquot_id')) for sample in samples if isinstance(sample, dict)
                    for portion in sample.get('portions', []) if isinstance(portion, dict)
                    for analyte in portion.get('analytes', []) if isinstance(analyte, dict)
                    for aliquot in analyte.get('aliquots', []) if isinstance(aliquot, dict)]
        if len(aliquots) != 1 or not all(isinstance(v, str) and v for v in (case.get('case_id'), *aliquots[0])) or not file.get('file_id') or file['file_id'] in mapping:
            raise InvalidAnalysis('unique file, case, sample and aliquot UUID relationships required')
        mapping[file['file_id']] = (case['case_id'], *aliquots[0])
    gene_ids, gene_model, rows, cases_seen, files_seen = None, None, [], set(), set()
    for record in records:
        if record.source != 'gdc-star-counts' or record.request.get('parser_version') != PARSER_VERSION:
            raise InvalidAnalysis('validated STAR selected-gene input required')
        selected = record.request['selected_gene_ids']
        model = record.request['gene_model']
        if gene_ids is None: gene_ids, gene_model = selected, model
        if selected != gene_ids or model != gene_model: raise InvalidAnalysis('identical exact genes and gene model required')
        file_ids = {row.get('file_id') for row in record.records}
        if len(file_ids) != 1: raise InvalidAnalysis('one nonempty source file per parsed input required')
        file_id = next(iter(file_ids))
        if file_id not in mapping or file_id in files_seen: raise InvalidAnalysis('missing or duplicate source file linkage')
        files_seen.add(file_id)
        case_id, sample_id, aliquot_id = mapping[file_id]
        if case_id in cases_seen: raise InvalidAnalysis('multiple expression observations per case need explicit aggregation')
        cases_seen.add(case_id)
        values = {row['gene_id']: row for row in record.records}
        row = {'entity_id': case_id, 'case_id': case_id, 'sample_id': sample_id, 'aliquot_id': aliquot_id,
               'file_id': file_id, 'gene_model': gene_model, 'units': {}}
        for i, gene in enumerate(gene_ids):
            field = 'gene_' + str(i)
            source = values.get(gene)
            if source and source['units'].get(column) != UNITS[column]: raise InvalidAnalysis('incompatible source normalization')
            row[field] = source[column] if source else None
            row['units'][field] = UNITS[column]
        rows.append(row)
    record, receipt = _derived(rows, (*records, links), block_id, 'assemble_gdc_expression', 'expression_matrix', 'case', input_rows=len(records),
        limitations=('One source-linked aliquot per case; distinct cases do not by themselves prove participant independence.',
                     'Missing genes remain missing; no normalization conversion, build liftover or cohort representativeness inferred.'))
    record = record.model_copy(update={'request': {**record.request, 'gene_columns': dict(zip(('gene_' + str(i) for i in range(len(gene_ids))), gene_ids)), 'normalization': column}})
    receipt = receipt.model_copy(update={'output_reference': ExecutionReference(kind='acquisition', value=record.acquisition_id, sha256=content_hash(record.model_dump(mode='json')), block_id=block_id)})
    return record, receipt
