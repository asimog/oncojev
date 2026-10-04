"""Actual source-shape parsers and owned tool receipts; controlled data only."""
import asyncio
import base64
import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from src.block.manager import BlockManager
from src.jev.client import DeterministicJevClient
from src.persistence.records import RecordKind
from src.persistence.repository import ResearchRepository
from src.persistence.store import SqliteResearchStore
from src.provenance import content_hash
from src.reasoner.service import DeterministicReasoner
from src.runtime.pydantic_ai.contracts import HarnessRuntime
from src.runtime.pydantic_ai.scientific_tools import register_scientific_tools
from src.science.execution import ScienceExecutor
from src.science.models import InvalidAnalysis
from src.science.representation import COLUMNS, parse_gdc_star_counts, parse_gdc_table, derive_gdc_clinical, assemble_gdc_expression, join_gdc_case_inputs
from src.sources.models import AcquisitionRecord, CoverageContract, ScientificArtifact
from src.sources.representation import RepresentationNeed, assess_retained_representation, representation_alternatives


def acquired(rows, endpoint='cases', origin='synthetic'):
    return AcquisitionRecord(source='gdc', origin=origin, request={'fixture': True}, records=tuple(rows), provenance=('controlled schema fixture',),
        coverage=CoverageContract(endpoint=endpoint, requested_size=max(1, len(rows)), returned_rows=len(rows), reported_total=len(rows),
            id_field='case_id' if endpoint == 'cases' else 'file_id', unique_entities=len(rows), ordering='fixture', complete=True))


def artifact(data, metadata, file_id='file', block_id='block'):
    return ScientificArtifact(source='gdc', block_id=block_id, source_identity=file_id, request={'file_id': file_id, 'metadata': {'file_id': file_id, 'access': 'open', **metadata}},
        byte_sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data), format='tsv', content_base64=base64.b64encode(data).decode(),
        provenance=('controlled format fixture; never evidence',))


def clinical():
    return acquired([{'case_id': 'a', 'demographic': {'vital_status': 'Dead', 'days_to_death': 20}},
        {'case_id': 'b', 'demographic': {'vital_status': 'Alive'}, 'diagnoses': [{'days_to_last_follow_up': 10}], 'follow_ups': [{'days_to_follow_up': 30}]},
        {'case_id': 'c', 'demographic': {'vital_status': 'Unknown'}}])


def test_clinical_survival_missingness_and_outer_join_are_explicit():
    record, receipt = derive_gdc_clinical(clinical(), 'block', 'survival')
    assert [(r['time_days'], r['event']) for r in record.records] == [(20, 1), (30, 0), (None, None)]
    assert record.origin == 'synthetic' and receipt.output_reference.sha256 == content_hash(record.model_dump(mode='json'))
    need = RepresentationNeed(estimand='duration', representation='survival', entity_unit='case', entity_key='case_id',
        fields={'time': 'time_days'}, numeric_roles=('time',), units={'time': 'days'}, minimum_complete_rows=2)
    assert assess_retained_representation(record, need)['eligible']
    assert not assess_retained_representation(record, need.model_copy(update={'units': {'time': 'years'}}))['eligible']
    other, _ = derive_gdc_clinical(acquired([{'case_id': 'b', 'demographic': {}}, {'case_id': 'd', 'demographic': {}}]), 'block', 'clinical')
    joined, joined_receipt = join_gdc_case_inputs(record, other, 'block')
    assert len(joined.records) == 4 and sum(r['pair_complete'] for r in joined.records) == 1
    assert joined_receipt.omitted_entities == ('a', 'c', 'd')
    with pytest.raises(InvalidAnalysis, match='unique'):
        derive_gdc_clinical(acquired([clinical().records[0], clinical().records[0]]), 'block', 'survival')


@pytest.mark.parametrize('modality,header,row', [
    ('mutation_events', 'Hugo_Symbol\tNCBI_Build\tChromosome\tStart_Position\tEnd_Position\tReference_Allele\tTumor_Seq_Allele2\tTumor_Sample_Barcode\tVariant_Classification', 'GENE\tGRCh38\t1\t10\t10\tA\tT\taliquot\tMissense_Mutation'),
    ('cnv_segments', 'GDC_Aliquot\tChromosome\tStart\tEnd\tNum_Probes\tSegment_Mean', 'aliquot\t1\t10\t20\t5\t-0.3')])
def test_tabular_parsers_keep_entities_builds_units_and_reject_duplicates(modality, header, row):
    metadata = {'data_format': 'MAF' if modality == 'mutation_events' else 'TXT', 'data_type': 'Masked Somatic Mutation' if modality == 'mutation_events' else 'Copy Number Segment'}
    source = artifact((header + '\n' + row + '\n').encode(), metadata)
    parsed, receipt = parse_gdc_table(source, modality)
    assert receipt.input_references[0].value == source.artifact_id and len(parsed.records) == 1
    assert parsed.request['entity_unit'] != 'case'
    if modality == 'mutation_events': assert parsed.records[0]['build'] == 'GRCh38'
    else: assert parsed.records[0]['units']['segment_mean'] == 'log2(copy_number/2)'
    with pytest.raises(InvalidAnalysis, match='duplicate'):
        parse_gdc_table(artifact((header + '\n' + row + '\n' + row + '\n').encode(), metadata), modality)
    with pytest.raises(InvalidAnalysis): parse_gdc_table(source.model_copy(update={'access': 'controlled'}), modality)


def expression_inputs():
    data = ('\t'.join(COLUMNS) + '\n' + '\t'.join(('ENSG000001', 'GENE', 'protein_coding', '0', '0', '0', '0', '0', '0')) + '\n').encode()
    records, files = [], []
    for i in range(2):
        file_id = 'file-' + str(i)
        source = artifact(data, {'data_format': 'TSV', 'data_type': 'Gene Expression Quantification', 'analysis': {'workflow_type': 'STAR - Counts'}}, file_id)
        records.append(parse_gdc_star_counts(source, ('ENSG000001', 'ENSG000002'))[0])
        files.append({'file_id': file_id, 'cases': [{'case_id': 'case-' + str(i), 'samples': [{'sample_id': 'sample-' + str(i),
            'portions': [{'analytes': [{'aliquots': [{'aliquot_id': 'aliquot-' + str(i)}]}]}]}]}]})
    return tuple(records), acquired(files, 'files')


def test_expression_assembly_preserves_zero_missing_genes_and_explicit_case_links():
    records, links = expression_inputs()
    matrix, receipt = assemble_gdc_expression(records, links, 'block', 'tpm_unstranded')
    assert len(matrix.records) == 2 and matrix.records[0]['gene_0'] == 0 and matrix.records[0]['gene_1'] is None
    assert matrix.request['gene_columns'] == {'gene_0': 'ENSG000001', 'gene_1': 'ENSG000002'}
    assert receipt.output_reference.sha256 == content_hash(matrix.model_dump(mode='json')) and len(receipt.input_references) == 3
    assert matrix.origin == 'synthetic'
    need = RepresentationNeed(estimand='abundance', representation='expression_matrix', entity_unit='case', entity_key='case_id', fields={'x': 'gene_0'}, numeric_roles=('x',), units={'x': 'TPM'})
    assert assess_retained_representation(matrix, need)['eligible']
    bad = links.model_copy(update={'records': (links.records[0], links.records[0])})
    with pytest.raises(InvalidAnalysis): assemble_gdc_expression(records, bad, 'block', 'tpm_unstranded')
    with pytest.raises(InvalidAnalysis): assemble_gdc_expression(records, acquired([], 'files'), 'block', 'tpm_unstranded')


def test_real_tools_generate_and_transform_owned_alternatives_then_reopen(tmp_path):
    runtime = HarnessRuntime(BlockManager(), DeterministicJevClient(), ScienceExecutor(), DeterministicReasoner(), 1, 1)
    store = SqliteResearchStore(tmp_path / 'representations.sqlite3')
    runtime.repository = ResearchRepository(store)
    block = runtime.manager.allocate('duration assets', 'fixture', 240)
    runtime.repository.record_block(block)
    source = clinical()
    runtime.retain_acquisition(block.block_id, source)
    agent = Agent(TestModel())
    register_scientific_tools(agent)
    ctx = SimpleNamespace(deps=SimpleNamespace(runtime=runtime, block_id=block.block_id))
    async def run():
        generated = await agent._function_toolset.tools['generate_representation_candidates'].function(ctx,
            {'estimand': 'time until event', 'representation': 'survival', 'entity_key': 'case_id', 'entity_unit': 'case', 'fields': {'time': 'time_days'}, 'numeric_roles': ['time']}, [source.acquisition_id])
        assert any(c['availability'] == 'derivable' and c['operation'] == 'derive_gdc_clinical' for c in generated['candidates'])
        assert not any(c['input_ready'] for c in generated['candidates'])
        transformed = await agent._function_toolset.tools['transform_gdc_representation'].function(ctx, 'derive_gdc_clinical', [source.acquisition_id], representation='survival')
        assert len(transformed['records']) == 3
        with pytest.raises(ValueError):
            await agent._function_toolset.tools['transform_gdc_representation'].function(ctx, 'derive_gdc_clinical', ['foreign'], representation='survival')
        return transformed
    output = asyncio.run(run())
    assert len(store.records(kind=RecordKind.REPRESENTATION_PARSE)) == 1 and not store.records(kind=RecordKind.EVIDENCE)
    store.close()
    reopened = SqliteResearchStore(tmp_path / 'representations.sqlite3')
    retained = reopened.latest(RecordKind.REPRESENTATION_PARSE)
    assert retained.payload['output_reference']['value'] == output['acquisition_id']
    reopened.close()


def test_representation_generation_retains_modalities_before_need_narrowing():
    source = acquired([{'file_id': 'maf', 'data_type': 'Masked Somatic Mutation', 'data_format': 'MAF', 'access': 'open'},
        {'file_id': 'cnv', 'data_type': 'Copy Number Segment', 'data_format': 'TXT', 'access': 'open'},
        {'file_id': 'rna', 'data_type': 'Gene Expression Quantification', 'data_format': 'TSV', 'access': 'controlled',
         'analysis': {'workflow_type': 'STAR - Counts'}}], endpoint='files')
    # Paired data may require an assay/parser/join prerequisite. A declared need
    # must not silently erase real source-backed options before fit assessment.
    need = RepresentationNeed(estimand='explore paired measurements', representation='paired_data',
        entity_key='case_id', entity_unit='case', fields={'x': 'x', 'y': 'y'})
    result = representation_alternatives([source], [], need)
    files = {c['file_id']: c for c in result['candidates'] if 'file_id' in c}
    assert set(files) == {'maf', 'cnv', 'rna'}
    assert {c['representation'] for c in files.values()} == {'mutation_events', 'cnv_segments', 'gene_summary'}
    assert not any(c['input_ready'] for c in files.values())
    assert files['rna']['availability'] == 'controlled_inaccessible'
    limited = representation_alternatives([source], [], need, limit=1)
    assert set(limited['omitted_candidate_ids']) == {c['candidate_id'] for c in files.values()}


def test_gzip_panel_validates_excluded_rows_and_retains_source_coverage():
    import gzip
    header = 'Hugo_Symbol\tNCBI_Build\tChromosome\tStart_Position\tEnd_Position\tReference_Allele\tTumor_Seq_Allele2\tTumor_Sample_Barcode\tVariant_Classification'
    row = lambda gene, i: f'{gene}\tGRCh38\t1\t{i}\t{i}\tA\tT\tsample\tMissense_Mutation'
    data = (header + '\n' + '\n'.join([row('OTHER', i) for i in range(1, 121)] + [row('TP53', 121)]) + '\n').encode()
    metadata = {'data_format': 'MAF', 'data_type': 'Masked Somatic Mutation', 'file_name': 'fixture.maf.gz'}
    source = artifact(gzip.compress(data), metadata).model_copy(update={'format': 'gzip'})
    parsed, receipt = parse_gdc_table(source, 'mutation_events', ('TP53', 'EGFR'))
    assert receipt.version == 'gdc-tabular-transform-v2' and receipt.input_rows == 121 and receipt.output_rows == 1
    assert parsed.records[0]['gene'] == 'TP53' and not parsed.coverage.complete
    assert parsed.request['selection']['omitted_source_rows'] == 120
    assert parsed.request['selection']['missing_gene_symbols'] == ['EGFR']
    assert parsed.request['selection']['decoded_bytes'] == len(data)
    need = RepresentationNeed(estimand='retained variant event', representation='mutation_events', entity_unit='mutation_event',
        entity_key='entity_id', fields={'position': 'start'}, numeric_roles=('position',), units={'position': 'base_1'})
    assert assess_retained_representation(parsed, need)['eligible']
    with pytest.raises(InvalidAnalysis, match='100-row'): parse_gdc_table(source, 'mutation_events')
    # A bad unselected event may not be silently excluded from source validation.
    malformed = data.replace(b'OTHER\tGRCh38\t1\t1\t1', b'OTHER\tGRCh38\t1\tBAD\t1', 1)
    with pytest.raises(InvalidAnalysis, match='coordinates'):
        parse_gdc_table(artifact(gzip.compress(malformed), metadata).model_copy(update={'format': 'gzip'}), 'mutation_events', ('TP53',))
    absent, _ = parse_gdc_table(source, 'mutation_events', ('ABSENT',))
    assert not absent.records and absent.request['selection']['missing_gene_symbols'] == ['ABSENT']
    assert not assess_retained_representation(absent, need)['eligible']


@pytest.mark.parametrize('case', ('truncated', 'corrupt', 'oversized', 'undeclared'))
def test_gzip_corruption_and_expansion_limits_reject(case):
    import gzip
    metadata = {'data_format': 'MAF', 'data_type': 'Masked Somatic Mutation', 'file_name': 'fixture.maf.gz'}
    data = gzip.compress(b'x' * (8 * 1024 * 1024 + 1) if case == 'oversized' else b'fixture')
    if case == 'truncated': data = data[:-4]
    if case == 'corrupt': data = data[:-8] + b'\0' * 8
    if case == 'undeclared': metadata['file_name'] = 'fixture.maf'
    with pytest.raises(InvalidAnalysis):
        parse_gdc_table(artifact(data, metadata).model_copy(update={'format': 'gzip'}), 'mutation_events', ('TP53',))


def test_unused_long_source_annotation_is_disclosed_without_changing_event():
    header = 'Hugo_Symbol\tNCBI_Build\tChromosome\tStart_Position\tEnd_Position\tReference_Allele\tTumor_Seq_Allele2\tTumor_Sample_Barcode\tVariant_Classification\tDOMAINS'
    row = 'KRAS\tGRCh38\t1\t10\t10\tA\tT\tsample\tMissense_Mutation\t' + 'annotation' * 1000
    metadata = {'data_format': 'MAF', 'data_type': 'Masked Somatic Mutation'}
    parsed, receipt = parse_gdc_table(artifact((header + '\n' + row + '\n').encode(), metadata), 'mutation_events')
    assert parsed.records[0]['gene'] == 'KRAS' and 'DOMAINS' not in parsed.records[0]
    assert parsed.request['selection']['discarded_annotation_columns'] == ['DOMAINS']
    assert receipt.version == 'gdc-tabular-transform-v2'
