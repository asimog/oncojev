# Upstream reference index

`.upstream/` is pinned reference material. Never recursively scan it or runtime-import it. Read this index first.

For a concrete implementation or scientific question:

1. Identify the question.
2. Select the smallest relevant upstream source.
3. Inspect only the relevant documentation, source, or tests.
4. Record the result in the appropriate repository-native contract, test, or documentation.
5. Stop.

`manifest.yaml` is the machine-readable record of the exact local source/version. This file explains why and when to inspect one.

## Runtime and agent infrastructure

| Source | Use it when | Local status |
| --- | --- | --- |
| `pydantic-ai` | Resolving a Pydantic AI runtime, tool, provider, or Harness compatibility question. | Pinned reference clone. |
| `typesafe-sdk-python` | Implementing or validating a supported TypeSafe/Jev SDK primitive. Read current official `llms.txt` before SDK integration. | Pinned reference clone. |
| `openai-plugins` | A concrete plugin or skill interoperability question needs source-level confirmation. | Pinned reference clone. |

## GDC and biological-source semantics

GDC is one public source family, not the OncoJev architecture. For API discovery, start with `gdc/gdc-docs/docs/API/Users_Guide/Search_and_Retrieval.md`. The available fields are a large reference catalogue: query it only for a named entity/field need; do not load `Appendix_A_Available_Fields.md` into ordinary agent context. `Data_Analysis.md` is likewise excluded from ordinary startup context.

Other API-guide targets available for a concrete question are `Additional_Examples.md`, `Appendix_B_Key_Terms.md`, `Appendix_C_Format_of_Submission_Requests_and_Responses.md`, `BAM_Slicing.md`, `Downloading_Files.md`, `Getting_Started.md`, `GraphQL_Examples.md`, `Python_Examples.md`, `Submission.md`, and `System_Information.md`. Use `gdcdictionary`, `gdcdatamodel2`, or `gdc-models` only for a specific entity or field; use `gdc-workflow-overview` only when processing semantics remain unresolved; and use `gdc-client` only for transfer-client behavior.

Example: for “What does this GDC expression value represent?”, inspect `Search_and_Retrieval.md`, then the named data-model node, then `Expression_mRNA_Pipeline.md` only if processing semantics remain unclear. Do not inspect unrelated GDC repositories.

### GDC data-model navigation

For a named entity or relationship, inspect only its matching module under `gdc/gdcdatamodel2/src/gdcdatamodel2/models/`. The complete local module inventory is intentionally listed below for path selection, not loaded as context.

<details>
<summary>359 modules</summary>

- `__init__.py`
- `aggregated_somatic_mutation.py`
- `aggregatedsomaticmutationdatafromsomaticaggregationworkflow.py`
- `aggregatedsomaticmutationderivedfromproject.py`
- `aggregatedsomaticmutationrelatestocase.py`
- `aligned_reads_index.py`
- `aligned_reads.py`
- `alignedreadsdatafromalignmentcocleaningworkflow.py`
- `alignedreadsdatafromalignmentworkflow.py`
- `alignedreadsindexderivedfromalignedreads.py`
- `alignedreadsindexderivedfromsubmittedalignedreads.py`
- `alignedreadsindexrelatestocase.py`
- `alignedreadsmatchedtosubmittedalignedreads.py`
- `alignedreadsmatchedtosubmittedunalignedreads.py`
- `alignedreadsrelatestocase.py`
- `alignment_cocleaning_workflow.py`
- `alignment_workflow.py`
- `alignmentcocleaningworkflowperformedonsubmittedalignedreads.py`
- `alignmentcocleaningworkflowperformedonsubmittedunalignedreads.py`
- `alignmentcocleaningworkflowrelatestocase.py`
- `alignmentworkflowperformedonsubmittedalignedreads.py`
- `alignmentworkflowperformedonsubmittedunalignedreads.py`
- `alignmentworkflowrelatestocase.py`
- `aliquot.py`
- `aliquotderivedfromanalyte.py`
- `aliquotderivedfromsample.py`
- `aliquotrelatestocase.py`
- `aliquotshippedtocenter.py`
- `analysis_metadata.py`
- `analysismetadataderivedfromfile.py`
- `analysismetadataderivedfromsubmittedalignedreads.py`
- `analysismetadatarelatestocase.py`
- `analyte.py`
- `analytederivedfromportion.py`
- `analytederivedfromsample.py`
- `analyterelatestocase.py`
- `annotated_somatic_mutation.py`
- `annotatedsomaticmutationdatafromgenomicprofileharmonizationworkflow.py`
- `annotatedsomaticmutationdatafromsomaticannotationworkflow.py`
- `annotatedsomaticmutationrelatestocase.py`
- `annotation.py`
- `annotationannotatesaggregatedsomaticmutation.py`
- `annotationannotatesalignedreads.py`
- `annotationannotatesalignedreadsindex.py`
- `annotationannotatesaliquot.py`
- `annotationannotatesanalysismetadata.py`
- `annotationannotatesanalyte.py`
- `annotationannotatesannotatedsomaticmutation.py`
- `annotationannotatesarchive.py`
- `annotationannotatesbiospecimensupplement.py`
- `annotationannotatescase.py`
- `annotationannotatescenter.py`
- `annotationannotatesclinicalsupplement.py`
- `annotationannotatescopynumberauxiliaryfile.py`
- `annotationannotatescopynumberestimate.py`
- `annotationannotatescopynumbersegment.py`
- `annotationannotatesdemographic.py`
- `annotationannotatesdiagnosis.py`
- `annotationannotatesexperimentmetadata.py`
- `annotationannotatesexposure.py`
- `annotationannotatesfamilyhistory.py`
- `annotationannotatesfile.py`
- `annotationannotatesfilteredcopynumbersegment.py`
- `annotationannotatesfollowup.py`
- `annotationannotatesgeneexpression.py`
- `annotationannotatesgermlinemutationindex.py`
- `annotationannotatesmaskedmethylationarray.py`
- `annotationannotatesmaskedsomaticmutation.py`
- `annotationannotatesmethylationbetavalue.py`
- `annotationannotatesmirnaexpression.py`
- `annotationannotatesmoleculartest.py`
- `annotationannotatesotherclinicalattribute.py`
- `annotationannotatespathologydetail.py`
- `annotationannotatespathologyreport.py`
- `annotationannotatesportion.py`
- `annotationannotatesproteinexpression.py`
- `annotationannotatesrawmethylationarray.py`
- `annotationannotatesreadgroup.py`
- `annotationannotatesreadgroupqc.py`
- `annotationannotatesrunmetadata.py`
- `annotationannotatessample.py`
- `annotationannotatessecondaryexpressionanalysis.py`
- `annotationannotatessimplegermlinevariation.py`
- `annotationannotatessimplesomaticmutation.py`
- `annotationannotatesslide.py`
- `annotationannotatesslideimage.py`
- `annotationannotatessomaticmutationindex.py`
- `annotationannotatesstructuralvariation.py`
- `annotationannotatessubmittedalignedreads.py`
- `annotationannotatessubmittedexpressionarray.py`
- `annotationannotatessubmittedgenomicprofile.py`
- `annotationannotatessubmittedgenotypingarray.py`
- `annotationannotatessubmittedmethylationbetavalue.py`
- `annotationannotatessubmittedtangentcopynumber.py`
- `annotationannotatessubmittedunalignedreads.py`
- `annotationannotatestissuesourcesite.py`
- `annotationannotatestreatment.py`
- `annotationrelatestocase.py`
- `archive.py`
- `archivememberofproject.py`
- `archiverelatedtofile.py`
- `archiverelatestocase.py`
- `biospecimen_supplement.py`
- `biospecimensupplementderivedfromcase.py`
- `biospecimensupplementmemberofarchive.py`
- `biospecimensupplementrelatestocase.py`
- `case.py`
- `casememberofproject.py`
- `caseprocessedattissuesourcesite.py`
- `center.py`
- `clinical_supplement.py`
- `clinical.py`
- `clinicaldescribescase.py`
- `clinicalrelatestocase.py`
- `clinicalsupplementderivedfromcase.py`
- `clinicalsupplementmemberofarchive.py`
- `clinicalsupplementrelatestocase.py`
- `copy_number_auxiliary_file.py`
- `copy_number_estimate.py`
- `copy_number_liftover_workflow.py`
- `copy_number_segment.py`
- `copy_number_variation_workflow.py`
- `copynumberauxiliaryfilederivedfromsomaticcopynumberworkflow.py`
- `copynumberauxiliaryfilerelatestocase.py`
- `copynumberestimatederivedfromcopynumbervariationworkflow.py`
- `copynumberestimatederivedfromgenomicprofileharmonizationworkflow.py`
- `copynumberestimatederivedfromsomaticcopynumberworkflow.py`
- `copynumberestimaterelatestocase.py`
- `copynumberliftoverworkflowperformedonsubmittedtangentcopynumber.py`
- `copynumberliftoverworkflowrelatestocase.py`
- `copynumbersegmentderivedfromcopynumberliftoverworkflow.py`
- `copynumbersegmentderivedfromgenomicprofileharmonizationworkflow.py`
- `copynumbersegmentderivedfromsomaticcopynumberworkflow.py`
- `copynumbersegmentrelatestocase.py`
- `copynumbervariationworkflowperformedoncopynumbersegment.py`
- `copynumbervariationworkflowrelatestocase.py`
- `data_format.py`
- `data_release.py`
- `data_subtype.py`
- `data_type.py`
- `datareleasedescribesroot.py`
- `datareleaserelatestocase.py`
- `datasubtypememberofdatatype.py`
- `demographic.py`
- `demographicdescribescase.py`
- `demographicrelatestocase.py`
- `diagnosis.py`
- `diagnosisdescribescase.py`
- `diagnosisrelatestocase.py`
- `experiment_metadata.py`
- `experimental_strategy.py`
- `experimentmetadataderivedfromfile.py`
- `experimentmetadataderivedfromreadgroup.py`
- `experimentmetadatarelatestocase.py`
- `exposure.py`
- `exposuredescribescase.py`
- `exposurerelatestocase.py`
- `expression_analysis_workflow.py`
- `expressionanalysisworkflowperformedongeneexpression.py`
- `expressionanalysisworkflowrelatestocase.py`
- `family_history.py`
- `familyhistorydescribescase.py`
- `familyhistoryrelatestocase.py`
- `file.py`
- `filedatafromaliquot.py`
- `filedatafromanalyte.py`
- `filedatafromcase.py`
- `filedatafromfile.py`
- `filedatafromportion.py`
- `filedatafromsample.py`
- `filedatafromslide.py`
- `filedescribescase.py`
- `filegeneratedfromplatform.py`
- `filememberofarchive.py`
- `filememberofdataformat.py`
- `filememberofdatasubtype.py`
- `filememberofexperimentalstrategy.py`
- `filememeberoftag.py`
- `filerelatedtofile.py`
- `filerelatestocase.py`
- `filesubmittedbycenter.py`
- `filtered_copy_number_segment.py`
- `filteredcopynumbersegmentdatafromcopynumberliftoverworkflow.py`
- `filteredcopynumbersegmentrelatestocase.py`
- `follow_up.py`
- `followupdescribescase.py`
- `followupdescribesdiagnosis.py`
- `followuprelatestocase.py`
- `gene_expression.py`
- `geneexpressiondatafromrnaexpressionworkflow.py`
- `geneexpressionrelatestocase.py`
- `genomic_profile_harmonization_workflow.py`
- `genomicprofileharmonizationworkflowperformedonsubmittedgenomicprofile.py`
- `genomicprofileharmonizationworkflowrelatestocase.py`
- `germline_mutation_calling_workflow.py`
- `germline_mutation_index.py`
- `germlinemutationcallingworkflowperformedonalignedreads.py`
- `germlinemutationcallingworkflowperformedonsubmittedgenotypingarray.py`
- `germlinemutationcallingworkflowrelatestocase.py`
- `germlinemutationindexderivedfromsimplegermlinevariation.py`
- `germlinemutationindexrelatestocase.py`
- `masked_methylation_array.py`
- `masked_somatic_mutation.py`
- `maskedmethylationarraydatafrommethylationarrayharmonizationworkflow.py`
- `maskedmethylationarrayrelatestocase.py`
- `maskedsomaticmutationdatafromgenomicprofileharmonizationworkflow.py`
- `maskedsomaticmutationdatafromsomaticaggregationworkflow.py`
- `maskedsomaticmutationderivedfromproject.py`
- `maskedsomaticmutationrelatestocase.py`
- `methylation_array_harmonization_workflow.py`
- `methylation_beta_value.py`
- `methylation_liftover_workflow.py`
- `methylationarrayharmonizationworkflowperformedonrawmethylationarray.py`
- `methylationarrayharmonizationworkflowrelatestocase.py`
- `methylationbetavaluedatafrommethylationarrayharmonizationworkflow.py`
- `methylationbetavaluedatafrommethylationliftoverworkflow.py`
- `methylationbetavaluerelatestocase.py`
- `methylationliftoverworkflowperformedonsubmittedmethylationbetavalue.py`
- `methylationliftoverworkflowrelatestocase.py`
- `mirna_expression_workflow.py`
- `mirna_expression.py`
- `mirnaexpressiondatafrommirnaexpressionworkflow.py`
- `mirnaexpressionrelatestocase.py`
- `mirnaexpressionworkflowperformedonalignedreads.py`
- `mirnaexpressionworkflowrelatestocase.py`
- `molecular_test.py`
- `moleculartestperformedatfollowup.py`
- `moleculartestrelatedtodiagnosis.py`
- `moleculartestrelatedtoslide.py`
- `moleculartestrelatestocase.py`
- `other_clinical_attribute.py`
- `otherclinicalattributedescribescase.py`
- `otherclinicalattributedescribesfollowup.py`
- `otherclinicalattributerelatestocase.py`
- `pathology_detail.py`
- `pathology_report.py`
- `pathologydetaildescribesdiagnosis.py`
- `pathologydetailrelatestocase.py`
- `pathologyreportderivedfromsample.py`
- `pathologyreportrelatestocase.py`
- `platform.py`
- `portion.py`
- `portionderivedfromsample.py`
- `portionrelatestocase.py`
- `portionshippedtocenter.py`
- `program.py`
- `project.py`
- `projectmemberofprogram.py`
- `protein_expression.py`
- `proteinexpressionderivedfromportion.py`
- `proteinexpressionderivedfromsample.py`
- `proteinexpressionrelatestocase.py`
- `publication.py`
- `publicationreferstofile.py`
- `raw_methylation_array.py`
- `rawmethylationarraydatafromaliquot.py`
- `rawmethylationarrayrelatestocase.py`
- `read_group_qc.py`
- `read_group.py`
- `readgroupderivedfromaliquot.py`
- `readgroupqcdatafromsubmittedalignedreads.py`
- `readgroupqcdatafromsubmittedunalignedreads.py`
- `readgroupqcgeneratedfromreadgroup.py`
- `readgroupqcrelatestocase.py`
- `readgrouprelatestocase.py`
- `rna_expression_workflow.py`
- `rnaexpressionworkflowperformedonalignedreads.py`
- `rnaexpressionworkflowperformedonsubmittedalignedreads.py`
- `rnaexpressionworkflowperformedonsubmittedexpressionarray.py`
- `rnaexpressionworkflowperformedonsubmittedunalignedreads.py`
- `rnaexpressionworkflowrelatestocase.py`
- `root.py`
- `rootrelatestocase.py`
- `run_metadata.py`
- `runmetadataderivedfromfile.py`
- `runmetadataderivedfromreadgroup.py`
- `runmetadatarelatestocase.py`
- `sample.py`
- `samplederivedfromcase.py`
- `samplederivedfromsample.py`
- `sampleprocessedattissuesourcesite.py`
- `samplerelatedtodiagnosis.py`
- `samplerelatestocase.py`
- `secondary_expression_analysis.py`
- `secondaryexpressionanalysisdatafromexpressionanalysisworkflow.py`
- `secondaryexpressionanalysisrelatestocase.py`
- `simple_germline_variation.py`
- `simple_somatic_mutation.py`
- `simplegermlinevariationdatafromgermlinemutationcallingworkflow.py`
- `simplegermlinevariationrelatestocase.py`
- `simplesomaticmutationdatafromgenomicprofileharmonizationworkflow.py`
- `simplesomaticmutationdatafromsomaticmutationcallingworkflow.py`
- `simplesomaticmutationrelatestocase.py`
- `slide_image.py`
- `slide.py`
- `slidederivedfromportion.py`
- `slidederivedfromsample.py`
- `slideimagedatafromslide.py`
- `slideimagerelatestocase.py`
- `sliderelatestocase.py`
- `somatic_aggregation_workflow.py`
- `somatic_annotation_workflow.py`
- `somatic_copy_number_workflow.py`
- `somatic_mutation_calling_workflow.py`
- `somatic_mutation_index.py`
- `somaticaggregationworkflowperformedonannotatedsomaticmutation.py`
- `somaticaggregationworkflowperformedonsimplesomaticmutation.py`
- `somaticaggregationworkflowrelatestocase.py`
- `somaticannotationworkflowperformedonsimplesomaticmutation.py`
- `somaticannotationworkflowrelatestocase.py`
- `somaticcopynumberworkflowperformedonalignedreads.py`
- `somaticcopynumberworkflowperformedonsubmittedgenotypingarray.py`
- `somaticcopynumberworkflowrelatestocase.py`
- `somaticmutationcallingworkflowperformedonalignedreads.py`
- `somaticmutationcallingworkflowrelatestocase.py`
- `somaticmutationindexderivedfromannotatedsomaticmutation.py`
- `somaticmutationindexderivedfromsimplesomaticmutation.py`
- `somaticmutationindexderivedfromstructuralvariation.py`
- `somaticmutationindexrelatestocase.py`
- `structural_variant_calling_workflow.py`
- `structural_variation.py`
- `structuralvariantcallingworkflowperformedonalignedreads.py`
- `structuralvariantcallingworkflowrelatestocase.py`
- `structuralvariationdatafromgenomicprofileharmonizationworkflow.py`
- `structuralvariationdatafromstructuralvariantcallingworkflow.py`
- `structuralvariationrelatestocase.py`
- `submitted_aligned_reads.py`
- `submitted_expression_array.py`
- `submitted_genomic_profile.py`
- `submitted_genotyping_array.py`
- `submitted_methylation_beta_value.py`
- `submitted_tangent_copy_number.py`
- `submitted_unaligned_reads.py`
- `submittedalignedreadsdatafromreadgroup.py`
- `submittedalignedreadsrelatestocase.py`
- `submittedexpressionarrayderivedfromaliquot.py`
- `submittedexpressionarrayrelatestocase.py`
- `submittedgenomicprofiledatafromreadgroup.py`
- `submittedgenomicprofilerelatestocase.py`
- `submittedgenotypingarrayderivedfromaliquot.py`
- `submittedgenotypingarrayrelatestocase.py`
- `submittedmethylationbetavaluederivedfromaliquot.py`
- `submittedmethylationbetavaluerelatestocase.py`
- `submittedtangentcopynumberderivedfromaliquot.py`
- `submittedtangentcopynumberrelatestocase.py`
- `submittedunalignedreadsdatafromreadgroup.py`
- `submittedunalignedreadsrelatestocase.py`
- `tag.py`
- `tissue_source_site.py`
- `treatment.py`
- `treatmentdescribesdiagnosis.py`
- `treatmentrelatestocase.py`
- `helpers/__init__.py`
- `helpers/base.py`
- `helpers/datetime_hooks.py`
- `helpers/indexes.py`
- `helpers/related_cases.py`
- `helpers/versioned_nodes.py`
- `helpers/versioning.py`

</details>

### GDC bioinformatics pipeline navigation

Use these only to resolve processing semantics after API and model inspection: `Aligned_reads_summary_metrics.md`, `CNV_Pipeline.md`, `DNA_Seq_Variant_Calling_Pipeline.md`, `DNA_Seq_WGS.md`, `Expression_mRNA_Pipeline.md`, `Methylation_Pipeline.md`, `miRNA_Pipeline.md`, and `RPPA_intro.md`.

## Scientific Python and statistics candidates

These are un-cloned reference scaffolds, not implied runtime dependencies. A Phase 2+ capability contract must choose a library deliberately; source inspection is justified only when an implementation decision requires it. The initial deterministic-analysis candidates are NumPy (arrays), pandas (tables), SciPy (numerics/distributions/tests), and statsmodels (regression and inference). The remaining candidates are optional domain extensions, not defaults.

| Source | Purpose and likely relevance | Status |
| --- | --- | --- |
| [SciPy](https://github.com/scipy/scipy) | Numerical algorithms, distributions, hypothesis tests, optimization. | Initial deterministic-analysis candidate; not cloned or installed. |
| [scikit-bio](https://github.com/scikit-bio/scikit-bio) | Bioinformatics data structures and methods. | Optional domain extension; not cloned. |
| [NumPy](https://numpy.org/) | Array computation for deterministic kernels. | Initial deterministic-analysis candidate; not cloned or installed. |
| [Biopython](https://github.com/biopython/biopython) | Sequence and biological-record utilities. | Optional domain extension; not cloned. |
| [pyensembl](https://github.com/openvax/pyensembl) | Ensembl annotation and identifier access. | Optional domain extension; not cloned. |
| [ETE](https://github.com/etetoolkit/ete) | Phylogenetic and tree tooling. | Optional domain extension; not cloned. |
| [pandas](https://github.com/pandas-dev/pandas) | Tabular ingestion, joins, and transformations. | Initial deterministic-analysis candidate; not cloned or installed. |
| [statsmodels](https://github.com/statsmodels/statsmodels) | Regression, model diagnostics, and inference. | Initial deterministic-analysis candidate; not cloned or installed. |
| [xarray](https://github.com/pydata/xarray) | Labelled multidimensional scientific data. | Optional domain extension; not cloned. |

Use [the short statistical-method selection guide](../skills/statistical-methods/README.md) before proposing a test. It is procedural guidance, not an analysis engine or a substitute for a pre-specified estimand.

## Public cancer and data sources

Use [GDC public API/docs](https://docs.gdc.cancer.gov/API/Users_Guide/Getting_Started/), [GDC publications](https://gdc.cancer.gov/about-data/publications), locally pinned `external/xenaPython`, or locally pinned `external/dataapi` only when a block needs a named public source and Phase 3 has introduced a source capability contract. GDC publication metadata may be retrieved as source context through that future source capability; it is not present runtime behavior. None implies automatic download, runtime use, or scientific validity.

## Scientific agent and skill references

`external/scientific-agent-skills` and `external/clawbio` are locally pinned procedural/reference sources. Their skills are not automatically trusted, installed, executable, or promoted into the OncoJev Capability Index. Select a single skill only when a task requires its domain procedure, then independently validate any resulting capability or scientific claim.
