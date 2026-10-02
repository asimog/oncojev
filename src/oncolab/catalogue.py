from src.oncolab.models import (
    OncoLabAccessPolicy, OncoLabAvailability, OncoLabDescriptor,
    OncoLabExecutionMode, OncoLabKind, OncoLabResourceClass,
)
from src.oncolab.registry import OncoLabIndex
from src.oncolab.execution import ROUTES


def _oncolab_descriptor(capability_id: str, name: str, kind: OncoLabKind, purpose: str, tags: tuple[str, ...], source: str, *, availability: OncoLabAvailability = OncoLabAvailability.KNOWN, execution_mode: OncoLabExecutionMode = OncoLabExecutionMode.METADATA_ONLY, access_policy: OncoLabAccessPolicy = OncoLabAccessPolicy.REVIEW_REQUIRED, resource_class: OncoLabResourceClass = OncoLabResourceClass.SMALL, limitations: tuple[str, ...] = ("Descriptor only; no executable wrapper is implemented.",)) -> OncoLabDescriptor:
    return OncoLabDescriptor(
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


def initial_oncolab_index() -> OncoLabIndex:
    descriptors = (
        _oncolab_descriptor("transform.gdc-star-counts", "GDC STAR Counts gene selection", OncoLabKind.TRANSFORMATION,
            "Parse one explicitly open retained augmented STAR Counts TSV, preserving exact gene IDs and count/TPM/FPKM units.",
            ("gdc", "expression", "star", "gene", "representation"), "src/science/representation.py",
            availability=OncoLabAvailability.INSTALLED, execution_mode=OncoLabExecutionMode.LOCAL_PYTHON,
            access_policy=OncoLabAccessPolicy.LOCAL_ONLY,
            limitations=("No sample/cohort matrix, case join, identifier remapping or normalization conversion.",)),
        _oncolab_descriptor("science.source-paired","Source-resolved paired association",OncoLabKind.STATISTICAL_METHOD,
            "Pearson correlation or simple OLS over complete paired rows with unique entity keys from one owned acquisition.",
            ("paired","association","correlation","regression"),"src/science/execution.py",availability=OncoLabAvailability.INSTALLED,
            execution_mode=OncoLabExecutionMode.LOCAL_PYTHON,access_policy=OncoLabAccessPolicy.LOCAL_ONLY,
            limitations=("No joins, covariates or causal inference; independent-row/method assumptions must be declared.",)),
        _oncolab_descriptor("source.gdc-file","Open GDC exact-byte file acquisition",OncoLabKind.SOURCE,
            "Bounded file acquisition after GDC metadata explicitly declares open access; retains exact bytes and source identity.",
            ("gdc","file","artifact","bytes"),"src/sources/public.py",availability=OncoLabAvailability.AVAILABLE,
            execution_mode=OncoLabExecutionMode.REMOTE_API,access_policy=OncoLabAccessPolicy.PUBLIC,
            limitations=("Per-file open access, size and checksum checks; release/licence unknown unless supplied by source.",)),
        _oncolab_descriptor("science.acquisition-summary", "Stored acquisition summary", OncoLabKind.SCIENTIFIC_METHOD,
            "Descriptive record count or numeric-field summary of an exact stored public response slice.",
            ("acquisition", "descriptive", "summary"), "src/science/execution.py",
            availability=OncoLabAvailability.INSTALLED, execution_mode=OncoLabExecutionMode.LOCAL_PYTHON,
            limitations=("Population coverage remains unknown; a slice count is not a population total.",)),
        _oncolab_descriptor("stat.numpy", "NumPy", OncoLabKind.SCIENTIFIC_METHOD, "Deterministic numerical array kernels.", ("array", "numerical", "statistics"), "https://numpy.org/", availability=OncoLabAvailability.INSTALLED, execution_mode=OncoLabExecutionMode.LOCAL_PYTHON),
        _oncolab_descriptor("stat.pandas", "pandas", OncoLabKind.TRANSFORMATION, "Deterministic tabular ingestion, joins, and reshaping.", ("table", "transformation", "statistics"), "https://github.com/pandas-dev/pandas", availability=OncoLabAvailability.INSTALLED, execution_mode=OncoLabExecutionMode.LOCAL_PYTHON),
        _oncolab_descriptor("stat.scipy", "SciPy", OncoLabKind.STATISTICAL_METHOD, "Numerical algorithms, distributions, and statistical tests.", ("statistics", "distribution", "hypothesis-test"), "https://github.com/scipy/scipy", availability=OncoLabAvailability.INSTALLED, execution_mode=OncoLabExecutionMode.LOCAL_PYTHON),
        _oncolab_descriptor("stat.statsmodels", "statsmodels", OncoLabKind.STATISTICAL_METHOD, "Regression, diagnostics, and statistical inference.", ("statistics", "regression", "inference"), "https://github.com/statsmodels/statsmodels", availability=OncoLabAvailability.INSTALLED, execution_mode=OncoLabExecutionMode.LOCAL_PYTHON),
        _oncolab_descriptor("bio.scikit-bio", "scikit-bio", OncoLabKind.SCIENTIFIC_METHOD, "Bioinformatics data structures and analysis methods.", ("bioinformatics", "sequence"), "https://github.com/scikit-bio/scikit-bio"),
        _oncolab_descriptor("bio.biopython", "Biopython", OncoLabKind.SOFTWARE, "Biological sequence and record utilities.", ("bioinformatics", "sequence", "annotation"), "https://github.com/biopython/biopython"),
        _oncolab_descriptor("bio.pyensembl", "PyEnsembl", OncoLabKind.SOURCE, "Ensembl annotation and identifier lookup.", ("annotation", "ensembl", "gene"), "https://github.com/openvax/pyensembl"),
        _oncolab_descriptor("bio.ete", "ETE", OncoLabKind.SOFTWARE, "Phylogenetic and tree analysis tooling.", ("phylogeny", "tree", "bioinformatics"), "https://github.com/etetoolkit/ete"),
        _oncolab_descriptor("bio.xarray", "xarray", OncoLabKind.TRANSFORMATION, "Labelled multidimensional scientific data handling.", ("array", "multidimensional", "transformation"), "https://github.com/pydata/xarray"),
        _oncolab_descriptor("source.gdc", "NCI GDC public API", OncoLabKind.SOURCE, "Filtered public cancer metadata search and data retrieval.", ("cancer", "gdc", "metadata", "search"), "https://api.gdc.cancer.gov", availability=OncoLabAvailability.AVAILABLE, execution_mode=OncoLabExecutionMode.REMOTE_API, access_policy=OncoLabAccessPolicy.PUBLIC, resource_class=OncoLabResourceClass.MEDIUM, limitations=("One source family, not a pipeline.", "No GDC wrapper is implemented in this phase.")),
        _oncolab_descriptor("source.gdan", "GDAN public methods", OncoLabKind.SOURCE, "Public GDAN methods and data-reference discovery.", ("cancer", "gdan", "methods"), "https://www.cancer.gov/ccg/research/computational-genomics/genomic-data-analysis-network"),
        _oncolab_descriptor("source.ucsc-xena", "UCSC Xena", OncoLabKind.SOURCE, "Public cancer cohort and genomics data access.", ("cancer", "xena", "cohort"), ".upstream/external/xenaPython", availability=OncoLabAvailability.AVAILABLE, execution_mode=OncoLabExecutionMode.REMOTE_API, access_policy=OncoLabAccessPolicy.PUBLIC),
        _oncolab_descriptor("source.md-anderson-dataapi", "MD Anderson DataAPI", OncoLabKind.SOURCE, "Public cancer data API reference.", ("cancer", "data-api", "cohort"), ".upstream/external/dataapi", availability=OncoLabAvailability.AVAILABLE, execution_mode=OncoLabExecutionMode.REMOTE_API, access_policy=OncoLabAccessPolicy.PUBLIC),
        _oncolab_descriptor("literature.gdc-publications", "GDC Publications", OncoLabKind.LITERATURE, "GDC publication metadata and source context.", ("cancer", "gdc", "literature", "publication"), "https://gdc.cancer.gov/about-data/publications", availability=OncoLabAvailability.AVAILABLE, execution_mode=OncoLabExecutionMode.REMOTE_API, access_policy=OncoLabAccessPolicy.PUBLIC),
        _oncolab_descriptor("literature.public", "Public literature search", OncoLabKind.LITERATURE, "Public literature and knowledge retrieval class.", ("literature", "knowledge", "search"), "future-provider-selection", availability=OncoLabAvailability.ACQUIRABLE),
        _oncolab_descriptor("visualization.scientific", "Scientific visualization", OncoLabKind.VISUALIZATION, "Reproducible scientific visual artifacts.", ("visualization", "plot", "artifact"), "matplotlib", availability=OncoLabAvailability.INSTALLED, execution_mode=OncoLabExecutionMode.LOCAL_PYTHON),
        _oncolab_descriptor("software.github-scientific", "Public GitHub scientific software acquisition", OncoLabKind.SOFTWARE, "Credential-free isolated acquisition, replay, and typed validation of public scientific software.", ("github", "software", "acquisition", "sandbox"), "src/science/sandbox.py", availability=OncoLabAvailability.AVAILABLE, execution_mode=OncoLabExecutionMode.SANDBOX, access_policy=OncoLabAccessPolicy.PUBLIC, resource_class=OncoLabResourceClass.MEDIUM, limitations=("Only HTTPS github.com repositories at resolved commits are accepted.", "Local execution requires verified Linux x86_64 Landlock/seccomp confinement; WSL alone is not an isolation boundary.", "A verified execution does not promote a method to reusable capability.")),
        _oncolab_descriptor("jev.noul", "Jev Noul", OncoLabKind.JEV, "Bounded Boolean semantic proposition with native probability.", ("jev", "semantic", "noul", "probability"), "docs/references/TYPESAFE_JEV_DOSSIER.md", availability=OncoLabAvailability.INSTALLED, execution_mode=OncoLabExecutionMode.SEMANTIC_MEASUREMENT, access_policy=OncoLabAccessPolicy.CREDENTIALS_REQUIRED, limitations=("Local questions are not reusable capabilities.", "Output is not evidence.")),
        _oncolab_descriptor("jev.choice", "Jev Choice", OncoLabKind.JEV, "Closed semantic alternatives with full probability distribution.", ("jev", "semantic", "choice", "frontier"), "docs/references/TYPESAFE_JEV_DOSSIER.md", availability=OncoLabAvailability.INSTALLED, execution_mode=OncoLabExecutionMode.SEMANTIC_MEASUREMENT, access_policy=OncoLabAccessPolicy.CREDENTIALS_REQUIRED, limitations=("A winner does not establish suitability.", "Output is not evidence.")),
        _oncolab_descriptor("jev.score", "Jev Score", OncoLabKind.JEV, "Ordered semantic rubric with expected score and level distribution.", ("jev", "semantic", "score", "rubric"), "docs/references/TYPESAFE_JEV_DOSSIER.md", availability=OncoLabAvailability.INSTALLED, execution_mode=OncoLabExecutionMode.SEMANTIC_MEASUREMENT, access_policy=OncoLabAccessPolicy.CREDENTIALS_REQUIRED, limitations=("A score is not a probability of scientific truth.", "Output is not evidence.")),
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
        *(_oncolab_descriptor(f"gdc.endpoint.{identifier}", name, OncoLabKind.SOURCE, purpose, ("gdc", "api", "endpoint"), "gdc/gdc-docs/docs/API/Users_Guide/Getting_Started.md", availability=OncoLabAvailability.AVAILABLE, execution_mode=OncoLabExecutionMode.REMOTE_API, access_policy=OncoLabAccessPolicy.PUBLIC, limitations=("Descriptor only; no GDC wrapper is implemented.",)) for identifier, name, purpose in gdc_endpoints),
        *(_oncolab_descriptor(f"gdc.retrieval.{identifier}", name, OncoLabKind.SOURCE, purpose, ("gdc", "retrieval", "metadata"), "gdc/gdc-docs/docs/API/Users_Guide/Search_and_Retrieval.md", availability=OncoLabAvailability.AVAILABLE, execution_mode=OncoLabExecutionMode.REMOTE_API, access_policy=OncoLabAccessPolicy.PUBLIC, limitations=("Planning semantics only; field selection must remain bounded.",)) for identifier, name, purpose in gdc_retrieval),
        *(_oncolab_descriptor(f"gdc.pipeline.{name.lower().replace(' ', '-').replace('/', '-')}", f"GDC {name} pipeline reference", OncoLabKind.SCIENTIFIC_METHOD, f"Processing-semantics reference for the GDC {name} pipeline.", ("gdc", "pipeline", "bioinformatics"), "gdc/gdc-docs/docs/Data/Bioinformatics_Pipelines", limitations=("Reference only; not an executable OncoJev pipeline.",)) for name in gdc_pipelines),
        *(_oncolab_descriptor(f"gdc.entity.{name.replace(' ', '-')}", f"GDC {name}", OncoLabKind.SOURCE, f"Data-model navigation for the GDC {name} entity.", ("gdc", "data-model", "entity"), "gdc/gdcdatamodel2/src/gdcdatamodel2/models", availability=OncoLabAvailability.AVAILABLE, execution_mode=OncoLabExecutionMode.REMOTE_API, access_policy=OncoLabAccessPolicy.PUBLIC, limitations=("Data-model descriptor only; it does not retrieve or interpret a value.",)) for name in gdc_entities),
        *(_oncolab_descriptor(f"gdc.workflow.{name.lower().replace(' ', '-').replace('/', '-')}", f"GDC {name}", OncoLabKind.SCIENTIFIC_METHOD, f"Workflow/data-artifact semantics for {name}.", ("gdc", "workflow", "bioinformatics"), "gdc/gdcdatamodel2/src/gdcdatamodel2/models", limitations=("Reference only; no workflow execution is implemented.",)) for name in gdc_artifacts),
        *(_oncolab_descriptor(f"stat.method.{name.lower().replace(' ', '-').replace('/', '-')}", name.title(), OncoLabKind.STATISTICAL_METHOD, f"Statistical method-family descriptor for {name}.", ("statistics", "method", "planning"), "skills/statistical-methods/README.md", limitations=("Method selection requires a defined estimand and diagnostics.", "No executable wrapper is implemented.")) for name in statistical_methods),
    )
    def actual_contract(d):
        routes=ROUTES.get(d.capability_id)
        if not routes:return d
        local=d.capability_id in {"science.acquisition-summary","science.source-paired","stat.scipy","stat.pandas","stat.statsmodels","visualization.scientific"}
        operations=", ".join(r.operation or r.tool for r in routes)
        limitations=tuple(x for x in d.limitations if "future" not in x and "no executable" not in x.lower() and "No GDC wrapper" not in x)
        return d.model_copy(update={"input_contract":"Typed tool inputs: "+"; ".join(f"{r.operation or r.tool}: {', '.join(r.required_inputs) or 'bounded request'}" for r in routes),
            "applicability":"Only application routes: "+operations,"assumptions":("Required inputs, assumptions and access must be checked for the selected operation.",),
            "limitations":(*limitations,"Library-wide functionality is not exposed; exploratory arrays are not evidence." if any(r.exploratory for r in routes) else "Execution is limited to the declared typed route."),
            "execution_mode":OncoLabExecutionMode.REMOTE_API if d.capability_id=="literature.public" else d.execution_mode,
            "access_policy":OncoLabAccessPolicy.LOCAL_ONLY if local else OncoLabAccessPolicy.PUBLIC})
    return OncoLabIndex(actual_contract(d) for d in (*descriptors, *additions)).load_verification_records()
