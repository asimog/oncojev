from functools import cache

from src.capabilities.models import (
    CapabilityAccessPolicy, CapabilityAvailability, CapabilityDescriptor,
    CapabilityExecutionMode, CapabilityKind, ResourceClass,
)
from src.capabilities.registry import CapabilityRegistry


def _descriptor(capability_id: str, name: str, kind: CapabilityKind, purpose: str, tags: tuple[str, ...], source: str, *, availability: CapabilityAvailability = CapabilityAvailability.KNOWN, execution_mode: CapabilityExecutionMode = CapabilityExecutionMode.METADATA_ONLY, access_policy: CapabilityAccessPolicy = CapabilityAccessPolicy.REVIEW_REQUIRED, resource_class: ResourceClass = ResourceClass.SMALL, limitations: tuple[str, ...] = ("Descriptor only; no executable wrapper is implemented.",)) -> CapabilityDescriptor:
    return CapabilityDescriptor(
        capability_id=capability_id, name=name, kind=kind, purpose=purpose, tags=tags,
        input_contract="Typed request selected by a future capability wrapper.",
        output_contract="Typed result with provenance and explicit failure/missingness semantics.",
        applicability="Selected by bounded deterministic index retrieval; never injected wholesale into prompts.",
        limitations=limitations, assumptions=("Use requires an explicit future wrapper and policy check.",),
        missingness_semantics="Unavailable data, unsupported inputs, and operational failure are explicit states, never zero.",
        availability=availability, execution_mode=execution_mode, access_policy=access_policy,
        implementation_or_source=source, resource_class=resource_class,
        provenance=(".upstream/INDEX.md", source),
    )


@cache
def initial_capability_registry() -> CapabilityRegistry:
    descriptors = (
        _descriptor("stat.numpy", "NumPy", CapabilityKind.SCIENTIFIC_METHOD, "Deterministic numerical array kernels.", ("array", "numerical", "statistics"), "https://numpy.org/", availability=CapabilityAvailability.INSTALLED, execution_mode=CapabilityExecutionMode.LOCAL_PYTHON),
        _descriptor("stat.pandas", "pandas", CapabilityKind.TRANSFORMATION, "Deterministic tabular ingestion, joins, and reshaping.", ("table", "transformation", "statistics"), "https://github.com/pandas-dev/pandas", availability=CapabilityAvailability.INSTALLED, execution_mode=CapabilityExecutionMode.LOCAL_PYTHON),
        _descriptor("stat.scipy", "SciPy", CapabilityKind.STATISTICAL_METHOD, "Numerical algorithms, distributions, and statistical tests.", ("statistics", "distribution", "hypothesis-test"), "https://github.com/scipy/scipy", availability=CapabilityAvailability.INSTALLED, execution_mode=CapabilityExecutionMode.LOCAL_PYTHON),
        _descriptor("stat.statsmodels", "statsmodels", CapabilityKind.STATISTICAL_METHOD, "Regression, diagnostics, and statistical inference.", ("statistics", "regression", "inference"), "https://github.com/statsmodels/statsmodels", availability=CapabilityAvailability.INSTALLED, execution_mode=CapabilityExecutionMode.LOCAL_PYTHON),
        _descriptor("bio.scikit-bio", "scikit-bio", CapabilityKind.SCIENTIFIC_METHOD, "Bioinformatics data structures and analysis methods.", ("bioinformatics", "sequence"), "https://github.com/scikit-bio/scikit-bio"),
        _descriptor("bio.biopython", "Biopython", CapabilityKind.SOFTWARE, "Biological sequence and record utilities.", ("bioinformatics", "sequence", "annotation"), "https://github.com/biopython/biopython"),
        _descriptor("bio.pyensembl", "PyEnsembl", CapabilityKind.SOURCE, "Ensembl annotation and identifier lookup.", ("annotation", "ensembl", "gene"), "https://github.com/openvax/pyensembl"),
        _descriptor("bio.ete", "ETE", CapabilityKind.SOFTWARE, "Phylogenetic and tree analysis tooling.", ("phylogeny", "tree", "bioinformatics"), "https://github.com/etetoolkit/ete"),
        _descriptor("bio.xarray", "xarray", CapabilityKind.TRANSFORMATION, "Labelled multidimensional scientific data handling.", ("array", "multidimensional", "transformation"), "https://github.com/pydata/xarray"),
        _descriptor("source.gdc", "NCI GDC public API", CapabilityKind.SOURCE, "Filtered public cancer metadata search and data retrieval.", ("cancer", "gdc", "metadata", "search"), "https://api.gdc.cancer.gov", availability=CapabilityAvailability.AVAILABLE, execution_mode=CapabilityExecutionMode.REMOTE_API, access_policy=CapabilityAccessPolicy.PUBLIC, resource_class=ResourceClass.MEDIUM, limitations=("One source family, not a pipeline.", "No GDC wrapper is implemented in this phase.")),
        _descriptor("source.gdan", "GDAN public methods", CapabilityKind.SOURCE, "Public GDAN methods and data-reference discovery.", ("cancer", "gdan", "methods"), "https://www.cancer.gov/ccg/research/computational-genomics/genomic-data-analysis-network"),
        _descriptor("source.ucsc-xena", "UCSC Xena", CapabilityKind.SOURCE, "Public cancer cohort and genomics data access.", ("cancer", "xena", "cohort"), ".upstream/external/xenaPython", availability=CapabilityAvailability.AVAILABLE, execution_mode=CapabilityExecutionMode.REMOTE_API, access_policy=CapabilityAccessPolicy.PUBLIC),
        _descriptor("source.md-anderson-dataapi", "MD Anderson DataAPI", CapabilityKind.SOURCE, "Public cancer data API reference.", ("cancer", "data-api", "cohort"), ".upstream/external/dataapi", availability=CapabilityAvailability.AVAILABLE, execution_mode=CapabilityExecutionMode.REMOTE_API, access_policy=CapabilityAccessPolicy.PUBLIC),
        _descriptor("literature.gdc-publications", "GDC Publications", CapabilityKind.LITERATURE, "GDC publication metadata and source context.", ("cancer", "gdc", "literature", "publication"), "https://gdc.cancer.gov/about-data/publications", availability=CapabilityAvailability.AVAILABLE, execution_mode=CapabilityExecutionMode.REMOTE_API, access_policy=CapabilityAccessPolicy.PUBLIC),
        _descriptor("literature.public", "Public literature search", CapabilityKind.LITERATURE, "Public literature and knowledge retrieval class.", ("literature", "knowledge", "search"), "future-provider-selection", availability=CapabilityAvailability.ACQUIRABLE),
        _descriptor("visualization.scientific", "Scientific visualization", CapabilityKind.VISUALIZATION, "Reproducible scientific visual artifacts.", ("visualization", "plot", "artifact"), "matplotlib", availability=CapabilityAvailability.INSTALLED, execution_mode=CapabilityExecutionMode.LOCAL_PYTHON),
        _descriptor("software.github-scientific", "Public GitHub scientific software acquisition", CapabilityKind.SOFTWARE, "Controlled acquisition and evaluation of public scientific software.", ("github", "software", "acquisition"), "future-sandbox-policy", availability=CapabilityAvailability.ACQUIRABLE, execution_mode=CapabilityExecutionMode.SANDBOX, resource_class=ResourceClass.MEDIUM),
        _descriptor("jev.noul", "Jev Noul", CapabilityKind.JEV, "Bounded Boolean semantic proposition with native probability.", ("jev", "semantic", "noul", "probability"), "docs/references/TYPESAFE_JEV_DOSSIER.md", availability=CapabilityAvailability.INSTALLED, execution_mode=CapabilityExecutionMode.SEMANTIC_MEASUREMENT, access_policy=CapabilityAccessPolicy.CREDENTIALS_REQUIRED, limitations=("Local questions are not reusable capabilities.", "Output is not evidence.")),
        _descriptor("jev.choice", "Jev Choice", CapabilityKind.JEV, "Closed semantic alternatives with full probability distribution.", ("jev", "semantic", "choice", "frontier"), "docs/references/TYPESAFE_JEV_DOSSIER.md", availability=CapabilityAvailability.INSTALLED, execution_mode=CapabilityExecutionMode.SEMANTIC_MEASUREMENT, access_policy=CapabilityAccessPolicy.CREDENTIALS_REQUIRED, limitations=("A winner does not establish suitability.", "Output is not evidence.")),
        _descriptor("jev.score", "Jev Score", CapabilityKind.JEV, "Ordered semantic rubric with expected score and level distribution.", ("jev", "semantic", "score", "rubric"), "docs/references/TYPESAFE_JEV_DOSSIER.md", availability=CapabilityAvailability.INSTALLED, execution_mode=CapabilityExecutionMode.SEMANTIC_MEASUREMENT, access_policy=CapabilityAccessPolicy.CREDENTIALS_REQUIRED, limitations=("A score is not a probability of scientific truth.", "Output is not evidence.")),
    )
    gdc_endpoints = (
        ("status", "GDC API status", "API status and version metadata."),
        ("projects", "GDC projects", "Project-level public metadata search."),
        ("cases", "GDC cases", "Case-level public metadata search."),
        ("files", "GDC files", "File-level public metadata search."),
        ("annotations", "GDC annotations", "Post-curation annotation search."),
        ("data", "GDC data", "Selected public data-object retrieval."),
        ("manifest", "GDC manifest", "Transfer manifest generation."),
        ("slicing", "GDC slicing", "Selected aligned-read region retrieval."),
        ("submission", "GDC submission", "Submission resource metadata."),
    )
    gdc_retrieval = (
        ("filters", "GDC structured filters", "Boolean filter construction for GDC search endpoints."),
        ("fields", "GDC selected fields", "Explicit response-field selection for bounded metadata retrieval."),
        ("get", "GDC GET retrieval", "Short query retrieval through GDC HTTP GET."),
        ("post", "GDC POST retrieval", "Large structured query retrieval through GDC HTTP POST."),
        ("format", "GDC response formats", "JSON, TSV, and XML response-format selection."),
        ("uuid", "GDC entity UUID lookup", "Entity identification through GDC UUIDs."),
    )
    gdc_pipelines = (
        "Aligned reads summary metrics", "CNV", "DNA-seq variant calling", "DNA-seq WGS",
        "Expression mRNA", "Methylation", "miRNA", "RPPA",
    )
    gdc_entities = (
        "case", "project", "program", "file", "aliquot", "analyte", "portion", "sample",
        "diagnosis", "demographic", "exposure", "treatment", "follow-up", "pathology detail",
        "molecular test", "gene expression", "miRNA expression", "protein expression",
        "copy-number segment", "methylation beta value", "simple somatic mutation",
        "annotated somatic mutation", "structural variation", "aggregated somatic mutation",
        "germline mutation index", "aligned reads", "submitted aligned reads", "read group",
        "experiment metadata", "analysis metadata", "slide", "slide image",
    )
    gdc_artifacts = (
        "RNA expression workflow", "miRNA expression workflow", "somatic mutation calling workflow",
        "somatic copy-number workflow", "copy-number liftover workflow", "methylation liftover workflow",
        "methylation harmonization workflow", "genomic profile harmonization workflow",
        "somatic annotation workflow", "somatic aggregation workflow", "structural variant calling workflow",
        "germline mutation calling workflow",
    )
    statistical_methods = (
        "independent group difference", "paired group difference", "linear regression", "logistic regression",
        "Poisson regression", "negative-binomial regression", "mixed-effects regression", "robust regression",
        "contingency table association", "Fisher exact association", "rank-based comparison", "correlation",
        "survival comparison", "proportional-hazards survival model", "competing-risks analysis",
        "multiple-testing correction", "permutation inference", "bootstrap uncertainty",
    )
    additions = (
        *(_descriptor(f"gdc.endpoint.{identifier}", name, CapabilityKind.SOURCE, purpose, ("gdc", "api", "endpoint"), "gdc/gdc-docs/docs/API/Users_Guide/Getting_Started.md", availability=CapabilityAvailability.AVAILABLE, execution_mode=CapabilityExecutionMode.REMOTE_API, access_policy=CapabilityAccessPolicy.PUBLIC, limitations=("Descriptor only; no GDC wrapper is implemented.",)) for identifier, name, purpose in gdc_endpoints),
        *(_descriptor(f"gdc.retrieval.{identifier}", name, CapabilityKind.SOURCE, purpose, ("gdc", "retrieval", "metadata"), "gdc/gdc-docs/docs/API/Users_Guide/Search_and_Retrieval.md", availability=CapabilityAvailability.AVAILABLE, execution_mode=CapabilityExecutionMode.REMOTE_API, access_policy=CapabilityAccessPolicy.PUBLIC, limitations=("Planning semantics only; field selection must remain bounded.",)) for identifier, name, purpose in gdc_retrieval),
        *(_descriptor(f"gdc.pipeline.{name.lower().replace(' ', '-').replace('/', '-')}", f"GDC {name} pipeline reference", CapabilityKind.SCIENTIFIC_METHOD, f"Processing-semantics reference for the GDC {name} pipeline.", ("gdc", "pipeline", "bioinformatics"), "gdc/gdc-docs/docs/Data/Bioinformatics_Pipelines", limitations=("Reference only; not an executable OncoJev pipeline.",)) for name in gdc_pipelines),
        *(_descriptor(f"gdc.entity.{name.replace(' ', '-')}", f"GDC {name}", CapabilityKind.SOURCE, f"Data-model navigation for the GDC {name} entity.", ("gdc", "data-model", "entity"), "gdc/gdcdatamodel2/src/gdcdatamodel2/models", availability=CapabilityAvailability.AVAILABLE, execution_mode=CapabilityExecutionMode.REMOTE_API, access_policy=CapabilityAccessPolicy.PUBLIC, limitations=("Data-model descriptor only; it does not retrieve or interpret a value.",)) for name in gdc_entities),
        *(_descriptor(f"gdc.workflow.{name.lower().replace(' ', '-').replace('/', '-')}", f"GDC {name}", CapabilityKind.SCIENTIFIC_METHOD, f"Workflow/data-artifact semantics for {name}.", ("gdc", "workflow", "bioinformatics"), "gdc/gdcdatamodel2/src/gdcdatamodel2/models", limitations=("Reference only; no workflow execution is implemented.",)) for name in gdc_artifacts),
        *(_descriptor(f"stat.method.{name.lower().replace(' ', '-').replace('/', '-')}", name.title(), CapabilityKind.STATISTICAL_METHOD, f"Statistical method-family descriptor for {name}.", ("statistics", "method", "planning"), "skills/statistical-methods/README.md", limitations=("Method selection requires a defined estimand and diagnostics.", "No executable wrapper is implemented.")) for name in statistical_methods),
    )
    return CapabilityRegistry((*descriptors, *additions))
