# ONCOJEV — NEXT STAGE AUTONOMOUS LAB IMPLEMENTATION

Repository:

`https://github.com/asimog/oncojev`

---

# CURRENT BASELINE

At prompt creation, current `main` was:

`c9712e67050548354d32fcd6bb5b910569449431`

Commit:

`Correct completed phase summaries and record GitHub delivery`

Do not assume this remains HEAD.

Before editing:

```bash
git rev-parse HEAD
git status --short
```

Inspect current `main`, compare it against this prompt, and adapt to the repository that actually exists.

Do not mechanically recreate work already completed.

The current implementation plan states that the bounded F0–F6 program is DONE:

```text
F0  truthful lifecycle / recovery
F1  deterministic allocation / budgets / authority
F2  replayable provenance / receipts / telemetry
F3  typed cross-cycle Research Memory / validated start packets
F4  semantic search and Jev measurement core
F5  scientific execution correctness / artifact bridge / curated expansion
F6  retention / cleanup / truthful observability
```

Preserve these contracts and their regressions.

In particular, do NOT reimplement the bounded F4–F6 work.

F4 already supplies first working slices of:

```text
capability/method suitability
representation sufficiency
candidate-frontier semantics
hypothesis/test alignment
semantic duplicate detection
statement-specific dossier support
semantic Research Memory analysis
```

F5 already supplies:

```text
truthful undefined statistics
missing/invalid denominator accounting
GDC coverage/pagination contracts
source-resolved paired analyses
stable admission identity
exact retained scientific artifacts
```

F6 already supplies:

```text
workspace retention/archive-before-cleanup
truthful live/synthetic/offline presentation
failed/incomplete outcome presentation
```

Build the next stage on top of these.

---

# PRIMARY GOAL

Turn OncoJev into a continuously running autonomous computational research laboratory with:

1. one Railway worker;
2. one persistent Director;
3. one active fresh Researcher per JevBlock;
4. Director and Researcher both retaining appropriate Pydantic AI Harness capabilities;
5. heavy but bounded use of Jev for semantic search and comparison;
6. dynamic, revisioned OncoLab institutional knowledge;
7. large-scale capability discovery without bulk-uncontrolled ingestion;
8. scientific execution capable of using installed Python tools and compatible public GitHub repositories;
9. durable typed Research Memory;
10. a separate `oncojevlab` repository as the human-readable laboratory history;
11. the database remaining authoritative scientific state.

Target:

```text
Human research direction
        ↓
Persistent Director
        │
        ├── Research Memory
        ├── OncoLab
        ├── global hypothesis portfolio
        ├── contradiction frontier
        ├── cross-block semantic search
        ├── capability-gap intelligence
        ├── research-program review
        ├── Jev semantic measurement
        ├── Coder / CodeMode scratch capability
        └── global research frontier
                    ↓
              allocate ONE JevBlock
                    ↓
              Fresh Researcher
                    │
                    ├── Coder
                    ├── CodeMode
                    ├── block workspace
                    ├── scientific Python
                    ├── GDC / other sources
                    ├── external GitHub methods
                    ├── deterministic Science
                    ├── Jev
                    └── Reasoner
                    ↓
            validated measurements
                    ↓
              evidence admission
                    ↓
                  dossier
                    ↓
          authoritative database
                    ↓
                BlockDelta
                    ↓
       Research Memory + OncoLab
                    ↓
                 Director
                    ↓
                  repeat
```

Separate generated repository:

```text
github.com/asimog/oncojevlab
```

This repository is a readable projection.

It is NOT scientific authority.

---

# CORE THESIS

Protect this throughout implementation:

> OncoJev is a cumulative scientific decision system in which high-throughput semantic judgment can guide search and comparison without silently becoming scientific evidence or execution authority.

Ownership remains:

```text
Director
    decides globally

Researcher
    decides locally inside one block

Science
    measures deterministically

Jev
    measures semantic properties

Reasoner
    generates interpretations and possibilities

Python
    owns:
        lifecycle
        budgets
        provenance
        deterministic frontier composition
        evidence admission
        registry governance
        persistence
```

Do not blur these boundaries while increasing autonomy.

---

# NON-NEGOTIABLE ARCHITECTURAL BOUNDARIES

Do not:

```text
create an agent swarm
create a global Jev agent
create a global Science agent
create unnecessary microservices
move scientific evidence admission into Director
let Jev allocate blocks
let Jev mutate OncoLab
let Director silently mutate active ResearchState
let Director extend an active block deadline
treat semantic rejection as scientific negative evidence
treat operational failure as scientific negative evidence
make Markdown authoritative
make oncojevlab authoritative
turn every discovered external tool into a capability
bulk-ingest registries without measured need
create multiple simultaneous Researchers yet
```

Maintain:

```text
GLOBAL

Director
Control
Research Memory
OncoLab

BLOCK LOCAL

Researcher
ResearchState
source acquisition
Science
Jev
Reasoner
scientific workspace
measurements
evidence
dossier
```

---

# G0 — AUDIT CURRENT MAIN

Before implementation, inspect at minimum:

```text
AGENTS.md

README.md

docs/ARCHITECTURE.md
docs/EPISTEMIC_CONSTITUTION.md
docs/IMPLEMENTATION_PLAN.md
docs/JEV.md
docs/CAPABILITIES.md
docs/FRONTEND.md

config/runtime.yaml
config/models.yaml

src/autonomous.py

src/runtime/cycle.py
src/runtime/pydantic_ai/agents.py
src/runtime/pydantic_ai/contracts.py
src/runtime/pydantic_ai/controls.py
src/runtime/pydantic_ai/factory.py
src/runtime/pydantic_ai/workspace.py

src/director/
src/researcher/
src/reasoner/

src/block/
src/memory/
src/oncolab/
src/jev/
src/science/
src/sources/
src/persistence/
src/dossier/
src/evals/

Dockerfile
railway.toml

tests/invariants/
scripts/
```

Trace:

```text
Director construction
Researcher construction
Coder harness
CodeMode / Monty
Director workspace
Researcher workspace
launch_researcher
cycle lifecycle
semantic memory
OncoLab search_page
OncoLab verification
OncoLab execution routes
F4 capability suitability
F4 representation frontier
F4 hypothesis alignment
F4 memory semantics
FrontierPolicy.interpret
FrontierPolicy.decide
Science admission
scientific artifacts
DockerScientificSandbox
retention
evaluation
Railway persistence
```

Record starting HEAD.

Do not create a duplicate architecture document.

---

# G1 — RETAIN DIRECTOR CODER + CODEMODE

Do NOT remove the Director's Pydantic Coder Harness.

The Director currently has a deliberate writable:

```text
/work/director
```

scratch workspace.

Preserve it.

The Director should retain:

```text
Director
├── Coder
├── CodeMode / Monty
├── RuntimeControls
├── typed Memory tools
├── typed OncoLab tools
├── typed Jev semantic tools
├── global frontier tools
└── block-control tools
```

The point is future flexibility.

The Director may use its scratch workspace for:

```text
temporary analysis
small scripts
transforming bounded exported state
comparing structured results
planning calculations
exploring non-authoritative metadata
future engineering experiments
preparing engineering proposals
```

But preserve the existing authority boundary:

```text
/work/director
    writable

application source
    read-only

Researcher workspaces
    inaccessible

credentials
    inaccessible
```

Director Coder output:

```text
IS NOT evidence
IS NOT Science
IS NOT an OncoLab registry mutation
IS NOT runtime policy
```

The Director must not use Coder to modify live:

```text
src/
config/
Jev questions
FrontierPolicy
OncoLab governance
evidence admission
agent prompts
deployment configuration
```

This preserves future capability without allowing self-modifying production research.

Do NOT remove Researcher Coder.

---

# G2 — MAKE THE DIRECTOR A REAL GLOBAL RESEARCH MANAGER

The current Director is still too close to:

```text
read context
→ search OncoLab
→ allocate
→ launch Researcher
→ wait
→ summarize
```

Change its role into:

> What should the laboratory do next overall?

Director responsibilities must include:

```text
Research Memory search

semantic memory analysis

cross-block synthesis

global hypothesis portfolio

duplicate-research detection

contradiction detection

uncertainty frontier

future block generation

dependency planning

research diversification

capability planning

capability-gap analysis

capability failure analysis

resource planning

failure triage

active-block supervision

continuation planning

program-level research review

research concentration analysis

engineering-problem detection

OncoLab improvement proposals

legitimate stop/pause decisions
```

The Researcher retains:

> How should this bounded investigation proceed?

Do not move block-local method selection to the Director.

---

# G3 — NON-BLOCKING RESEARCHER LIFECYCLE

Do not leave Director suspended for the entire Researcher run.

Current historical behavior effectively does:

```python
await researcher.run(...)
```

inside the launch tool.

Replace this with Python-owned task lifecycle.

Target:

```text
Director
    ↓
allocate_block
    ↓
start_researcher
    ↓
return active-run identity

Python owns active Researcher task

        ┌──────────────────────────────┐
        │                              │
        ▼                              ▼

Researcher executes            Director performs
bounded block                  bounded independent
                               global work

        │                              │
        └───────────────┬──────────────┘
                        ↓
                Researcher terminal event
                        ↓
                   persist result
                        ↓
                  post-block Director
```

Initially retain:

```text
MAX ACTIVE RESEARCHERS = 1
```

Do not introduce a swarm.

Do not add:

```text
Celery
Redis
Kafka
Temporal
distributed workers
```

One Python service remains the target.

---

# G4 — EVENT-DRIVEN DIRECTOR

Do not burn tokens polling.

Python knows whether Researcher is running.

The Director should receive bounded turns when useful:

```text
Researcher started

material persisted event if explicitly useful

Researcher completed

Researcher failed

bounded scheduled program review
```

While Researcher runs, Director may:

```text
review historical memory
analyze global hypotheses
detect duplication
detect contradictions
search OncoLab
search external capability registries
inspect capability history
identify recurring capability gaps
prepare future block candidates
build dependency relationships
review recent research concentration
review failure patterns
review resource usage
prepare engineering proposals
perform program review
```

It must not modify the active block underneath the Researcher.

Once useful independent work is exhausted:

```text
yield
```

Do not keep the Director model continuously active for wall-clock duration.

---

# G5 — ISOLATE ACTIVE RUN STATE

Asynchronous execution must not share mutable cycle-global state unsafely.

Introduce the minimum typed context necessary.

Conceptually:

```text
AutonomousService
├── persistent Director
├── repository
├── Research Memory
├── OncoLab registry
├── runtime/application version
└── ActiveResearchContext | None

ActiveResearchContext
├── mission_id
├── cycle_id
├── block_id
├── OncoLab revision
├── Researcher run ID
├── budgets
├── usage
├── lifecycle
├── task state
└── start-state sequence/high-water mark
```

Avoid generic orchestration frameworks.

---

# G6 — ADD BLOCK DELTA

A dossier describes the block.

The Director additionally needs to know:

> What changed because of the block?

Create a deterministic/reference-linked:

```text
BlockDelta
```

or the smallest equivalent existing model extension.

Possible fields:

```text
new evidence references
new measurement references
new hypotheses
new scientific negative findings
new uncertainties
explicitly resolved uncertainties
new continuation proposals
new operational blockers
new capability demand
new capability gaps
new candidate contradictions
new cross-block relation candidates
resource-use delta
```

No unsupported scientific inference.

Prefer references over duplicated payloads.

Use BlockDelta heavily in the next Director turn.

---

# G7 — GLOBAL DIRECTOR JEV FRONTIER

The Director should maintain a bounded portfolio rather than jumping directly to one block.

Flow:

```text
Research Memory
      ↓
deterministic retrieval
      ↓
candidate future investigations
      ↓
bounded typed projection
      ↓
Jev semantic measurements
      ↓
global deterministic frontier
      ↓
small retained beam
      ↓
Director chooses ONE
```

Candidates may come from:

```text
Researcher continuation proposals
hypotheses
open uncertainties
contradictions
cross-block relation candidates
capability gaps
replication needs
underexplored mission areas
```

Use atomic dimensions such as:

```text
mission relevance

does it address a recorded uncertainty?

does it duplicate completed work?

could it resolve a contradiction?

is it a coherent continuation?

is it dependency-ready?

does it fit one bounded block?

is an appropriate capability available?

would the outcome distinguish hypotheses?

would the result materially change the global research state?
```

Never reduce this to:

```text
"Which is best?"
```

Preserve:

```text
Jev measures
Python composes
Director decides
```

---

# G8 — GLOBAL AND LOCAL FRONTIERS MUST REMAIN DISTINCT

Researcher frontier:

> What should I pursue inside this current block?

Director frontier:

> What should the lab allocate next?

They may share:

```text
Jev primitives
projection infrastructure
receipts
distribution decoding
```

They must NOT share blindly:

```text
candidate types
authority
scope semantics
stop conditions
policy version
threshold interpretation
```

Use separate deterministic policy identities.

---

# G9 — LEGITIMATE PAUSE / STOP

Do not force endless autonomous research.

Add a truthful Director program outcome such as:

```text
ALLOCATE
```

or:

```text
PAUSE
NO_MATERIAL_NEXT_BLOCK
NEEDS_HUMAN_DIRECTION
```

A pause may be justified because:

```text
no meaningful actionable uncertainty remains

all retained candidates depend on unavailable inputs

remaining candidates are materially duplicative

current capabilities cannot test the relevant hypotheses

further work adds detail without material uncertainty reduction

mission direction is exhausted or requires human choice
```

Do not create a dummy block merely to satisfy an old exactly-one-block cycle invariant.

A pause is a research-program decision.

It is NOT proof that the scientific mission succeeded.

---

# G10 — RESEARCH MEMORY AS GLOBAL SEMANTIC SEARCH

Preserve current F3/F4e.

Do not replace deterministic retrieval.

Canonical flow:

```text
query
   ↓
deterministic high-recall retrieval
   ↓
bounded typed candidates
   ↓
exact duplicate checks
   ↓
Jev semantic dimensions
   ↓
retained memory frontier
```

Semantic dimensions should support:

```text
relevance
semantic duplication
contradiction
recurring uncertainty
newly actionable uncertainty
repeated hypothesis
repeated blocker
recurring capability need
cross-block relationship
```

Never all-pairs compare the entire database.

Block candidate generation using deterministic signals first:

```text
entity
topic
capability ID
hypothesis identity
shared references
time bounds
retrieval terms
block lineage
```

Then apply Jev.

Maximum Jev means maximum semantic leverage, not maximum calls.

---

# G11 — GLOBAL HYPOTHESIS PORTFOLIO

Extend F4d across blocks.

Pipeline:

```text
historical hypotheses
      ↓
stable identity
      ↓
exact normalized duplicate detection
      ↓
bounded semantic candidates
      ↓
Jev
      ↓
global hypothesis portfolio
```

Preserve distinctions:

```text
duplicate
paraphrase
related but distinct
independent replication
contradicted
blocked
newly testable
deferred
resolved
```

Do not turn hypotheses into evidence.

Do not infer a scientific negative from semantic rejection.

---

# G12 — CROSS-BLOCK SEMANTIC DISCOVERY

Create bounded semantic comparison across completed blocks.

Examples:

```text
mutation finding A
expression phenotype B
CNV finding C
clinical phenotype D
```

Possible Jev questions:

```text
Could A and B characterize the same subgroup?

Does C suggest a testable explanation for B?

Does D make A scientifically worth testing in a defined population?

Do A and B materially conflict?

Are two findings independent or merely repeated descriptions?
```

Persist:

```text
CrossBlockRelationCandidate
```

with:

```text
source references
relation type
Jev call IDs
native distributions
limitations
basis sequence / memory revision
status
```

Possible statuses:

```text
candidate_for_testing
possible_duplicate
contradiction
independent_relation
uncertain
```

This is semantic research context.

It is not evidence.

---

# G13 — CONTRADICTION FRONTIER

Treat contradiction as a first-class research opportunity.

Measure:

```text
Is the apparent conflict real?

Could population differences explain it?

Could design differences explain it?

Could measurement method explain it?

Is this merely epistemic phrasing?

Would another bounded block resolve it?
```

Never overwrite either original result.

Preserve both.

Contradiction resolution may become a high-value future block.

---

# G14 — STALE PARALLEL PLANNING

If Director plans while Researcher is active, persist what that plan was based on:

```text
memory digest IDs
database high-water sequence
active block
active block revision
OncoLab revision
application version
```

When Researcher finishes:

```text
REVALIDATE
```

the prepared global frontier.

Do not blindly execute a pre-completion plan.

New evidence may invalidate it.

---

# G15 — PROGRAM REVIEW

Periodically allow Director to inspect recent research history and ask:

```text
Are we repeatedly exploring the same area?

Are hypotheses being rediscovered?

Are contradictions unresolved?

Are capability failures recurring?

Is one modality dominating?

Are we producing measurements without resolving uncertainty?

Are useful capability families repeatedly missing?

Are expensive blocks repeatedly producing little actionable change?

Are rejected/deferred ideas later recurring?
```

Do not create one universal research-quality score.

Do not build a self-reward loop.

Program review produces typed descriptive context for future allocation.

---

# G16 — DIRECTOR ENGINEERING INTELLIGENCE

The Director may recognize:

```text
memory retrieval misses paraphrases

a Jev question is repeatedly ambiguous

a capability descriptor disagrees with observed use

one provider repeatedly fails

Researchers repeatedly need one missing method family

a frontier policy produces pathological retention

deployment constraints block useful work
```

Create:

```text
EngineeringProposal
```

with concrete record references.

The Director's Coder scratch workspace may help analyze or prototype such proposals.

But it may NOT modify production source.

No Engineer agent in this phase.

---

# G17 — ONCOLAB BECOMES INSTITUTIONAL KNOWLEDGE

Preserve the existing OncoLab catalogue, cards, pagination, snapshots, hashes, routes, verification and F4 suitability system.

Expand its meaning from:

> things known to the catalogue

to:

> what the laboratory has learned about available capabilities.

Separate clearly:

```text
STATIC BASE KNOWLEDGE

descriptor
capability schema
execution route definitions
governance
base catalogue

DYNAMIC INSTITUTIONAL KNOWLEDGE

registry revision
verification history
successful execution scopes
failure history
observed limitations
usage history
demand history
semantic suitability history
capability gaps
promotion proposals
review proposals
re-verification state
reusable capability state
```

Descriptor presence must never imply:

```text
installed
executable
appropriate
validated
reusable
```

---

# G18 — VERSION ONCOLAB

Create immutable durable OncoLab revisions.

Example:

```text
R17
 ↓
Block A starts against R17

validated capability promoted
 ↓
R18

Block B starts against R18
```

Each new block records:

```text
OncoLab revision
application/runtime version
```

Historical blocks retain their original registry context.

Do not reinterpret historical decisions through current capabilities.

Normal OncoLab revision changes must NOT require Railway restart.

Refresh/reconstruct registry state between blocks.

---

# G19 — ONCOLAB SHOULD HAVE THREE DISCOVERY LAYERS

Do not make one giant catalogue.

Use three conceptual layers:

```text
LAYER 1 — CURATED ONCOLAB

current descriptors
current routes
verified/promoted reusable capabilities

LAYER 2 — EXTERNAL CAPABILITY DISCOVERY

bio.tools
GitHub
Bioconda
Bioconductor
future compatible registries

LAYER 3 — DATA ASSET DISCOVERY

GDC files
GDC metadata
other approved scientific datasets/resources
```

External candidates do not automatically become Layer 1.

---

# G20 — IMPORTANT: DATA FILES ARE NOT CAPABILITIES

Do NOT insert every GDC file UUID into the OncoLab capability catalogue.

A GDC file is:

```text
data asset / source resource
```

not:

```text
scientific capability
```

OncoLab should contain capabilities such as:

```text
gdc.file.search
gdc.file.describe
gdc.file.acquire
gdc.manifest.create
```

Individual file search results should become typed:

```text
ScientificDataAssetCandidate
```

or the nearest existing source model.

Data asset records should carry:

```text
source
file_id
file_name
access
data_category
data_type
data_format
experimental_strategy
file_size
md5sum
state
release/version metadata where available
case/project references
query identity
retrieval time
```

Promote only actual methods/tools, not file UUIDs.

---

# G21 — GDC FILE DISCOVERY EXPANSION

Expand current GDC integration to make the file layer a first-class search surface.

Support bounded `/files` discovery with appropriate metadata.

Relevant metadata includes at minimum where returned/available:

```text
file_id
file_name
md5sum
file_size
access
state
data_category
data_type
data_format
experimental_strategy
platform
analysis/workflow metadata
case references
project references
data release/version
```

Use GDC field/mapping contracts rather than hardcoded assumptions when feasible.

Allow scientific need queries such as:

```text
Find open-access gene-expression files
for the current cohort.

Find mutation files compatible with
the required representation.

Find CNV files for the selected project.

Find clinical/file resources needed
for a declared analysis.
```

Search must preserve:

```text
filters
requested fields
ordering
offset/page
total
query identity
release identity when known
```

Current F5 coverage contracts remain authoritative.

Do not regress pagination/overlap handling.

---

# G22 — GDC FILE ACQUISITION

Use the existing F5 exact scientific artifact bridge.

For a selected open-access file:

```text
GDC file metadata
      ↓
/data acquisition
      ↓
exact retained bytes
      ↓
source hash/size validation
      ↓
ScientificArtifact
      ↓
block-owned scientific input
```

Preserve:

```text
GDC MD5 when supplied
OncoJev SHA-256
byte size
source UUID
request identity
ownership
access status
```

Controlled-access files require explicit supported credentials.

Do not silently attempt them.

Large sets may use a manifest workflow only when the current bounded research need justifies it.

Do not turn bulk GDC harvesting into the default behavior.

---

# G23 — GDC REPRESENTATION SEARCH

Tie GDC file discovery into F4c representation selection.

Example:

```text
scientific need
      ↓
GDC available data assets
      ↓
group by useful representation:
    data type
    format
    entity unit
    strategy
    coverage
    transformation level
      ↓
deterministic availability
      ↓
Jev sufficiency / assumption fit
      ↓
retained representation frontier
```

This is where D2 can be earned.

Do not implement an artificial universal representation ladder.

Use only actual retrievable representations.

---

# G24 — BIO.TOOLS SEARCH ADAPTER

Add bio.tools as an external capability-discovery source.

Do NOT bulk-import its entire registry into OncoLab.

Implement bounded on-demand search.

Support useful current search dimensions such as:

```text
free-text query
tool ID
tool name
domain
EDAM topic
EDAM operation
input data type
input format
output data type
output format
pagination
```

Create typed:

```text
ExternalCapabilityCandidate
```

containing the relevant bounded fields.

Possible fields:

```text
external_source = bio.tools
external_id
name
description
homepage
tool types
EDAM topics
EDAM operations
inputs
outputs
formats
publications
download/package/repository links where supplied
license where supplied
version metadata
retrieved_at
response/query identity
```

External metadata is candidate information.

It does not prove:

```text
execution works
software is appropriate
the version is current
dependencies are installable
licence permits a particular use
scientific validity
```

---

# G25 — USE EDAM SEMANTICS WITHOUT BULK ONTOLOGY INGESTION

bio.tools exposes EDAM concepts.

Use them for controlled normalization where useful:

```text
operation
topic
data type
format
```

This can improve deterministic recall before Jev.

Initially:

```text
use IDs/terms returned in candidate records
```

Do NOT ingest the whole ontology unless retrieval evaluation demonstrates need.

If D6 later earns deeper ontology support, add a versioned EDAM snapshot or bounded resolver.

---

# G26 — BIO.TOOLS → JEV CAPABILITY SELECTION

Flow:

```text
Researcher or Director scientific need
      ↓
current OncoLab search
      ↓
if insufficient:
    bio.tools discovery
      ↓
ExternalCapabilityCandidate cards
      ↓
deterministic compatibility checks
      ↓
bounded contract enrichment
      ↓
Jev suitability dimensions
      ↓
retained candidate frontier
```

Jev may measure:

```text
estimand/method fit
operation fit
input semantic fit
output semantic fit
limitation compatibility
```

Python checks:

```text
actual execution route?
repository available?
supported runtime?
inputs available?
access acceptable?
```

Jev cannot turn a bio.tools metadata record into an executable capability.

---

# G27 — GITHUB EXTERNAL METHOD DISCOVERY

Preserve current controlled GitHub acquisition.

Expand discovery only through bounded public metadata/search where useful.

Candidate inspection may include:

```text
repository identity
default branch
resolved commit
release/tag
language
declared license
README/docs
requirements/lockfiles
tests
package metadata
```

Researcher can acquire compatible public repositories when current capabilities are inadequate.

Director may inspect candidate metadata for planning/capability-gap purposes.

Director does not perform scientific evidence admission.

---

# G28 — BIOCONDA ENRICHMENT

Use Bioconda as an optional external metadata source for tools discovered through:

```text
bio.tools
GitHub
OncoLab gaps
```

Useful information includes:

```text
package name
version
source URL
source checksum
runtime dependencies
build/runtime constraints
test commands
license metadata
platform support
```

Do not automatically install Conda in this phase merely because metadata exists.

For the Railway Python executor, Bioconda may initially be:

```text
metadata / compatibility / reproducibility enrichment
```

If later a selected capability genuinely requires Conda and evaluation justifies it, add a separate execution-backend decision.

---

# G29 — BIOCONDUCTOR DISCOVERY

Allow bounded Bioconductor package discovery where the scientific need points toward an R/Bioconductor method.

Treat initially as:

```text
metadata-only external capability candidate
```

because current target scientific execution remains Python-compatible local environments unless the repo already supports R.

Capture where available:

```text
package identity
purpose
BiocViews/categories
version/release
dependencies
documentation/vignettes
source repository
license
build status
```

Do not advertise a Bioconductor package as executable until an actual supported R environment exists and has been verified.

---

# G30 — OTHER OPTIONAL DISCOVERY SOURCES

Design the external discovery interface so additional adapters can be added without changing Director/Researcher semantics.

Candidates may later include:

```text
PyPI metadata for Python tools

BioContainers metadata for
packaged bioinformatics software

other curated open scientific registries

future approved cancer-data resources
```

Do not implement all of them automatically.

Add only the minimal next source whose measured retrieval value justifies it.

No cBioPortal or Hugging Face expansion unless explicitly approved later.

---

# G31 — EXTERNAL DISCOVERY INTERFACE

Create one bounded interface rather than source-specific agent tools everywhere.

Conceptually:

```text
ExternalCapabilityDiscovery

search(source, need, filters, continuation)
describe(source, external_id)
```

or an equivalent existing-domain design.

Possible source enum:

```text
BIOTOOLS
GITHUB
BIOCONDA
BIOCONDUCTOR
```

GDC FILES should remain a data-resource search surface, not be forced into the same capability model.

Every search must persist or emit a receipt containing:

```text
source
query
filters
page/cursor
retrieved candidate IDs
retrieved_at
response/content hash where feasible
omissions
failure
```

External registries are mutable.

Do not pretend they have immutable snapshots unless a snapshot is actually retained.

---

# G32 — MULTI-STAGE CAPABILITY SEARCH

Target complete capability search:

```text
scientific need
      ↓
1. deterministic current OncoLab retrieval
      ↓
2. cards
      ↓
3. expand promising contracts
      ↓
4. deterministic execution/input checks
      ↓
5. Jev semantic suitability
      ↓
6. retained current-capability frontier

IF inadequate:
      ↓
7. external discovery:
      bio.tools
      GitHub
      optional ecosystem metadata
      ↓
8. bounded external candidates
      ↓
9. deterministic runtime/input checks
      ↓
10. Jev suitability
      ↓
11. Researcher chooses acquisition/prototype
```

Do not automatically prefer external software over a verified local capability.

Do not let an installed lexical match block a genuinely unmet need.

Preserve the current F4a improvement.

---

# G33 — SEARCH SCALE / D6

Current catalogue scan may remain adequate.

Benchmark it.

Measure:

```text
recall
latency
catalogue size
continuation behavior
context size
```

If real scale makes current scanning inadequate, add the smallest justified deterministic search index.

Preferred order:

```text
current deterministic retrieval

→ SQLite FTS5 / equivalent

→ controlled vocabulary expansion

→ only then embeddings if evaluation shows
   additional useful recall
```

Do not jump directly to a vector database.

Do not bulk harvest tens of thousands of records without demonstrated use.

---

# G34 — CAPABILITY GAP RECORDS

Persist recurring unmet needs.

Example:

```text
CapabilityGap

semantic family:
    pathway enrichment

observed in:
    block A
    block D
    block G

attempted capabilities:
    ...

external candidates:
    ...

reason still unmet:
    ...
```

A capability gap is:

```text
research-program knowledge
```

not an executable capability.

Director may use Jev to group semantically equivalent needs.

---

# G35 — GOVERNED CAPABILITY PROMOTION

Activate D1 carefully.

One successful external method is NOT enough.

Flow:

```text
repeated need
      ↓
successful controlled executions
      ↓
Director identifies promotion candidate
      ↓
CapabilityPromotionProposal
      ↓
Python governance
      ↓
generalization / replay / contract checks
      ↓
ACCEPT or REJECT
      ↓
new OncoLab revision
```

Promotion should consider:

```text
source identity
repository + commit
package/version
scientific purpose
typed inputs
typed outputs
execution contract
dependency identity
replayability
validated scopes
observed failures
limitations
access conditions
licence status if known
measured utility
overlap with existing capabilities
```

Do not use one arbitrary minimum execution count as proof of scientific validity.

Governance must be versioned and explicit.

---

# G36 — DECLARATIVE VS CODE-REQUIRING PROMOTION

Important distinction:

## Declarative reusable capability

If the existing generic scientific executor can run it from:

```text
repo/package
commit/version
environment
commands
typed inputs
typed outputs
validation contract
```

it can be dynamically promoted into OncoLab without modifying application code.

## Code-requiring capability

If reuse requires:

```text
new parser
new wrapper
new Science algorithm
new runtime route
new source adapter
new admission semantics
```

Director creates:

```text
EngineeringProposal
```

It does NOT modify live code.

---

# G37 — ONCOLAB REVIEW / REVERIFICATION

Director should be able to propose:

```text
CapabilityPromotionProposal
CapabilityReviewProposal
CapabilityUpdateProposal
ReverificationProposal
CapabilityRetirementProposal
```

Use the minimum models actually needed.

Do not provide unrestricted:

```text
add_capability
edit_capability
delete_capability
```

Python governance owns accepted state transitions.

---

# G38 — SCIENTIFIC WORKSPACE: REMOVE DOCKER-IN-DOCKER DEPENDENCY

Current production configuration still uses:

```text
DockerScientificSandbox
```

This is a deployment mismatch for standard Railway.

Do not remove the scientific-execution contract.

Replace Docker-specific canonical ownership with an interface.

Conceptually:

```text
ScientificExecutionBackend

├── LocalVenvScientificExecutor
└── DockerScientificExecutor
```

Railway:

```text
LocalVenvScientificExecutor
```

Local verification may retain:

```text
DockerScientificExecutor
```

if useful.

Both must produce the same canonical scientific execution result contract.

---

# G39 — RESEARCHER SCIENTIFIC ENVIRONMENT

Each experiment gets isolated dependency state.

Example:

```text
var/workspaces/<block-id>/
    experiments/
        <experiment-id>/
            repository/
            venv/
            inputs/
            outputs/
```

Do NOT install research packages into the OncoJev application `.venv`.

A fresh Researcher must not inherit dependencies accidentally installed by an earlier block.

Initially support honestly:

```text
Python-compatible scientific repositories
```

Do not claim support for:

```text
R
Conda
CUDA
Docker-required methods
system daemons
```

unless separately implemented and verified.

---

# G40 — EXACT EXPERIMENT IDENTITY

A Git commit is insufficient by itself.

Persist:

```text
repository URL
resolved commit SHA
package/version identity
application version
execution backend
Python version
OS/base runtime identity
dependency-resolution identity
install command
test command
execute command
input references
input hashes
parameters
output hashes
validator version
first run
replay run
limitations
```

Generalize the current Docker-image-specific receipt contract.

A local backend should not pretend it has an immutable Docker image hash.

Use provider-specific typed environment identity.

---

# G41 — ACTIVATE D8 DEPENDENCY LOCKING

For reusable external methods, strengthen dependency reproducibility.

Prefer:

```text
repo lockfile

then pinned requirements

then reproducibly resolved dependency set

then post-install freeze + hash
```

Persist the exact result.

If dependencies cannot be made reproducible:

```text
record limitation
prevent unsupported REUSABLE promotion
```

A fixed repository commit alone is not sufficient for reusable capability status.

---

# G42 — PRESERVE EVIDENCE DISCIPLINE

This remains the strongest architecture rule.

Researcher may run arbitrary allowed exploratory code.

But:

```text
Coder output
shell output
model prose
Reasoner hypothesis
Jev judgment
plot
temporary notebook
```

does NOT automatically become evidence.

Canonical path remains:

```text
declared scientific experiment
       ↓
exact software + input identity
       ↓
deterministic/controlled execution
       ↓
replay / validation
       ↓
typed measurement candidate
       ↓
Science validation
       ↓
explicit evidence admission
```

Never bypass this to make external scientific tooling easier.

---

# G43 — SINGLE RAILWAY WORKER

Target:

```text
ONE Railway service

AutonomousService
├── API server
├── persistent Director
├── Director Coder workspace
├── Research Memory
├── dynamic OncoLab
├── repository/database
├── one active Researcher
├── Researcher workspace
├── Jev client
├── Reasoner
└── local scientific executor
```

These events must NOT require restart:

```text
new block
new dossier
new evidence
new hypothesis
new memory
new capability verification
new OncoLab revision
new capability promotion
new program review
new oncojevlab export
```

Redeploy only for actual application/software changes.

---

# G44 — PERSISTENCE ON RAILWAY

Do not rely on ephemeral filesystem state.

Current database abstraction remains preferred.

For Railway, ensure:

```text
ONCOJEV_DB_PATH
```

points to durable storage.

SQLite + one worker + Railway persistent volume is acceptable at the current scale.

Do not migrate to Postgres without demonstrated need.

Expose an operational status indicating:

```text
database location
persistent-storage configuration state
```

without exposing credentials.

---

# G45 — RAILWAY CODER VERIFICATION

Retaining both Director and Researcher Coder means the Landlock deployment question remains important.

Run the existing Linux verifier in the actual deployed environment if possible.

Verify:

```text
Landlock ABI

Director own workspace write

Researcher own workspace write

application read-only

peer workspace denied

credential files denied

provider environment variables unavailable

child processes retain confinement
```

If actual Railway verification is unavailable or fails closed:

```text
report a deployment blocker
```

Do not weaken confinement silently.

---

# G46 — DIRECTOR CODER AUTHORITY

Because Director Coder is intentionally retained, explicitly test that it cannot:

```text
write application source

write Researcher workspace

read credential files

change OncoLab authoritative state

change evidence

change lifecycle policy
```

Scratch engineering remains separate from production authority.

This is intentional future optionality.

Do not remove it merely because current Director logic does not require it.

---

# G47 — COST AND BUDGET CONTROL

Retain existing independent bounds for:

```text
Director model requests
Director CodeMode executions
Director tool calls

Researcher model requests
Researcher CodeMode executions
Researcher provider tool calls

Jev calls
Jev questions

Reasoner calls

source calls

scientific executions

download bytes

cycle aggregate use
```

Director parallel work gets a specific bounded allowance.

Do not let ten minutes of Researcher wall time imply ten minutes of Director model use.

Current monetary cost may still be unknown.

Expose:

```text
monetary bound configured?
reported cost known?
reported cost unknown?
```

Do not invent provider pricing.

Do not hardcode an arbitrary dollar value unless configuration already provides one.

---

# G48 — ONCOJEVLAB

Support separate repository:

```text
asimog/oncojevlab
```

Purpose:

> human-readable intellectual and operational history of the autonomous laboratory.

Authority remains:

```text
database
   ↓
typed records
   ↓
deterministic exporter
   ↓
oncojevlab
```

Never read Markdown back as scientific truth.

---

# G49 — ONCOJEVLAB STRUCTURE

Keep compact.

Example:

```text
oncojevlab/
├── README.md
│
├── program/
│   ├── current-direction.md
│   ├── frontier.md
│   ├── open-uncertainties.md
│   └── contradictions.md
│
├── blocks/
│   └── <block-id>/
│       ├── summary.md
│       └── dossier.json
│
├── hypotheses/
│   └── current.md
│
├── capabilities/
│   ├── current.md
│   ├── gaps.md
│   ├── revisions.md
│   └── proposals/
│
├── program-reviews/
│
└── engineering/
    └── proposals/
```

Only generate useful populated paths.

Do not create documentation sprawl.

---

# G50 — DETERMINISTIC EXPORTER

Director does not directly edit the notebook.

Flow:

```text
Director outcome
      ↓
typed persisted state
      ↓
deterministic renderer
      ↓
Markdown / JSON
      ↓
Git commit
```

Examples:

```text
BlockDelta
→ blocks/<id>/summary.md

CrossBlockRelation
→ program/frontier.md

Contradiction
→ program/contradictions.md

CapabilityGap
→ capabilities/gaps.md

OncoLabRevision
→ capabilities/current.md

ProgramReview
→ program-reviews/

EngineeringProposal
→ engineering/proposals/
```

Clearly label:

```text
evidence
measurement
hypothesis
semantic judgment
Director decision
operational failure
```

---

# G51 — GITHUB PUBLICATION FAILURE

Publishing `oncojevlab` is downstream observability.

If GitHub fails:

```text
record publication failure
retain DB state
continue scientific correctness
```

Do not roll back evidence or block finalization because publication failed.

Do not expose Git credentials to Coder environments.

If repository credentials/setup are absent, finish exporter and report the external setup requirement.

---

# G52 — MEANINGFUL COMMIT BOUNDARIES

Do not commit every model turn.

Commit at boundaries such as:

```text
block completed
material global-frontier update
new contradiction
accepted OncoLab revision
capability proposal
program review
engineering proposal
mission change
```

Use deterministic/templated commit messages.

---

# G53 — THREE MEMORY SURFACES

Keep these distinct:

```text
1. authoritative database
2. typed Research Memory
3. oncojevlab human-readable projection
```

Director primarily consumes #2.

Python owns #1.

Humans inspect #3.

---

# G54 — FRONTIER POLICY AUDIT

Audit every caller of:

```text
FrontierPolicy.interpret
FrontierPolicy.decide
```

Current `interpret()` is the multidimensional semantic path.

Older `decide()` contains generic historical thresholds.

Do not leave two competing policies canonical accidentally.

If `decide()` is legacy:

```text
migrate callers
deprecate/remove
```

If genuinely needed:

```text
identify its exact context
version separately
evaluate separately
```

Do not treat generic:

```text
.2
.25
.4-.6
.5
```

thresholds as universal scientific facts.

Policy changes must be:

```text
versioned
tested
evaluation-backed
```

---

# G55 — DEFERRED D1–D8 RECONCILIATION

Do not erase current deferred history.

Update it honestly.

## D1 — automatic capability promotion

PARTIALLY ACTIVATE.

Implement governed promotion for declaratively reusable external scientific capabilities.

Keep unsupported automatic Jev/self-promotion deferred.

## D2 — deeper representation/schema search

PARTIALLY ACTIVATE where real GDC/data representation search demonstrates benefit.

Do not build a speculative universal ladder.

## D3 — universal candidate generator

KEEP DEFERRED unless multiple real domain generators demonstrate a reusable shared contract.

## D4 — deeper hypothesis frontier

Implement the global portfolio and cross-block relation layer.

Keep additional refinement deferred until labelled failures justify it.

## D5 — semantic calibration / self-consistency / Autoresearch

KEEP EARNED.

First measure instability.

Only add bounded experiments if results justify them.

Do not automatically rewrite questions or policies.

## D6 — bulk harvesting / FTS / embeddings / broad ontology

PARTIALLY ADDRESS by adding external on-demand discovery.

Do not bulk harvest.

Benchmark first.

FTS before embeddings.

Use EDAM IDs opportunistically without full ontology ingestion.

## D7 — additional scientific operations

KEEP NEED-DRIVEN.

Do not add methods merely to increase catalogue size.

GDC file discovery is infrastructure/data access, not a mandate to implement every file analysis.

## D8 — dependency locking

ACTIVATE for reusable external capability promotion.

---

# G56 — ACCESS AND LICENCE TRUTHFULNESS

Do not infer:

```text
GitHub public
=
licensed for every use
```

Do not infer:

```text
bio.tools listing
=
validated software
```

Do not infer:

```text
GDC file exists
=
open access
```

Keep explicit:

```text
known
unknown
controlled
public
unverified
```

where applicable.

Promotion must not fabricate missing licensing/access information.

---

# G57 — HISTORICAL UNREPLAYABLE INPUTS

Do not rewrite history.

Historical acquisitions without retained bytes remain unreplayable unless exact bytes can be verifiably recovered.

Retain the limitation.

New infrastructure does not retroactively make old runs replayable.

---

# G58 — F6 RETENTION REMAINS CANONICAL

Preserve current retention.

Extend only for new experiment structures.

Once required state is durable, retention may remove:

```text
cloned repos
venvs
temporary outputs
Coder scratch files
```

but must preserve:

```text
scientific artifacts
receipts
evidence
measurement identity
dependency/environment identity
OncoLab revisions
Research Memory
ledger history
```

Director `/work/director` remains outside block-retention semantics unless separately bounded.

---

# G59 — EVALUATE THE ACTUAL THESIS

Do not confuse unit tests with proof Jev improves research.

Expand evaluation to measure:

```text
capability retrieval recall

external capability discovery recall

GDC representation retrieval

capability suitability retention

semantic duplicate suppression

independent-replication preservation

hypothesis/test alignment

cross-block relationship recovery

contradiction detection

memory reranking relevance

important-alternative retention

global frontier diversity

duplicate-block suppression

uncertainty resolution

unique source-bound outcomes

operational failure rate

elapsed/resource consumption

Jev failure fallback
```

Compare meaningful conditions:

```text
deterministic retrieval/policy only

deterministic + Reasoner when appropriate

deterministic + Jev

current full Researcher/Director system
```

Resource differences must be reported.

Do not declare a winner from one tiny live evaluation.

---

# G60 — ADD EVALUATION CORPUS

Extend `src/evals/` with labelled cases for:

```text
static OncoLab selection

bio.tools discovery

capability semantic mismatch

representation sufficiency

GDC file/representation discovery

hypothesis duplicate

independent replication

hypothesis/test alignment

contradiction vs population difference

cross-block relationship

memory relevance

actionable uncertainty

capability-gap grouping
```

Retain:

```text
retrieval version
projection version
question version
policy version
model requested
model resolved
native distributions
```

Labels are evaluation data.

They are not runtime scientific evidence.

---

# G61 — DIRECTOR TOOL SURFACE

Adapt names to current code rather than inventing unnecessary duplicates.

Conceptually Director should have:

```text
MEMORY

search_research_memory
resolve_memory_reference
get_dossier
get_evidence
get_hypotheses
get_negative_results
get_open_uncertainties

SEMANTIC CONTROL

analyze_memory_frontier
analyze_hypothesis_relations
analyze_cross_block_relation
analyze_contradiction
compare_block_candidates
review_research_program

ONCOLAB

search_oncolab
describe_oncolab
assess_capability_suitability
review_capability_history
identify_capability_gap
search_external_capabilities
describe_external_capability
propose_capability_promotion
propose_capability_review
propose_reverification

CONTROL

allocate_block
start_researcher
inspect_active_research
inspect_block
read_completed_block
pause_program

CODER

existing bounded file/shell scratch capabilities
through /work/director
```

Do not give Director direct evidence-admission tools.

Do not give it a generic unrestricted Jev escape hatch if typed semantic operations suffice.

---

# G62 — RESEARCHER OWNERSHIP REMAINS

Researcher controls:

```text
local source selection
local method selection
local representation selection
local scientific analysis
candidate generation
local frontier
Jev evaluation
Reasoner use
hypothesis exploration
scientific software acquisition
GitHub repository execution
scope escalation proposal
block completion
```

Director allocates the question.

Director does not prescribe a fixed pipeline.

---

# G63 — TESTS: DIRECTOR

Verify:

```text
Director Coder remains available on POSIX

Director can write /work/director

Director cannot write app source

Director cannot access Researcher workspace

Director cannot access credentials

Director start_researcher does not block entire run

only one Researcher can be active

completion/failure persisted

Director can do bounded independent work

Director does not busy poll

Director cannot change active ResearchState

Director cannot extend active deadline

stale prepared frontier invalidated after Researcher completion

pause outcome creates no fake block
```

---

# G64 — TESTS: GLOBAL JEV

Verify:

```text
deterministic retrieval happens first

bounded projections only

exact duplicates before semantic duplicate detection

contradictions preserve both records

cross-block relation does not become evidence

hypothesis rejection does not become negative result

independent replication is preserved

Jev failure returns deterministic fallback

multiple useful alternatives remain retained

global/local frontier policies remain distinct
```

---

# G65 — TESTS: ONCOLAB

Verify:

```text
current static catalogue remains valid seed

dynamic registry survives reopen

revisions immutable

block pins exact revision

historical revision remains reconstructable

verification history preserved

capability gap references actual records

one external execution does not auto-promote

promotion policy versioned

rejected promotion leaves registry unchanged

accepted declarative capability creates new revision

accepted capability usable without process restart

code-requiring capability creates engineering proposal

Jev suitability cannot grant execution authority
```

---

# G66 — TESTS: GDC FILES

Verify with deterministic fixtures and bounded live smoke where appropriate:

```text
/files pagination

query identity

ordering

totals

access

data category/type/format

experimental strategy

file size

md5

project/case references

open vs controlled distinction

selected file acquisition

exact byte retention

MD5 where supplied

SHA-256 identity

wrong size/hash rejection

wrong-owner rejection

representation grouping

no individual file becomes OncoLab capability
```

Preserve F5 pagination/coverage regressions.

---

# G67 — TESTS: BIO.TOOLS / EXTERNAL SEARCH

Verify:

```text
pagination

query preservation

EDAM filters

domain filters

data type/input/output filters

bounded candidate cards

external candidates remain non-authoritative

metadata-only candidate cannot execute

Jev cannot override missing execution route

candidate promotion requires validation

mutable external result stores retrieval time/hash

registry outage is operational failure, not scientific negative
```

Do not make unit tests depend permanently on live bio.tools availability.

Use fixtures plus bounded smoke.

---

# G68 — TESTS: SCIENTIFIC EXECUTION

Verify:

```text
Railway backend does not require Docker daemon

each experiment gets isolated environment

application .venv unchanged

commit pinned

dependency identity persisted

input identity persisted

first run/replay checked

output identity checked

corrupted artifact rejected

generic Coder output cannot enter evidence

existing Docker test backend still obeys same contract if retained
```

---

# G69 — TESTS: RAILWAY / PERSISTENCE

Verify:

```text
multiple sequential blocks without restart

dynamic OncoLab update without restart

Director remains service-lifetime where intended

service reconstruction restores durable state

interrupted Researcher closes honestly

DB persistence configuration visible

Coder confinement verification truthful

no secrets appear in logs/exports
```

---

# G70 — TESTS: ONCOJEVLAB

Verify:

```text
export based only on authoritative records

identical DB state gives deterministic output

repo content cannot modify scientific state

no credentials exported

publication failure does not damage DB

commit only on defined boundaries

exported claims reference authoritative IDs
```

---

# G71 — IMPLEMENTATION ORDER

Do not do one giant refactor.

Use dependency order:

```text
H0
audit current HEAD and reconcile prompt

H1
retain/verify Director Coder + CodeMode;
update Director role/tool surface

H2
non-blocking single-Researcher lifecycle
+ ActiveResearchContext

H3
event-driven Director
+ BlockDelta
+ PAUSE outcome
+ stale-plan invalidation

H4
global Director semantic frontier:
memory
hypotheses
contradictions
cross-block relations
program review

H5
dynamic/versioned OncoLab institutional state

H6
GDC file/data-asset discovery and representation integration

H7
bio.tools on-demand external capability discovery
+ EDAM normalization

H8
Bioconda/Bioconductor/GitHub enrichment interfaces
without uncontrolled bulk ingestion

H9
governed capability promotion
+ OncoLab revision transitions
+ engineering proposals

H10
scientific execution backend abstraction
+ Railway local venv backend
+ exact environment/dependency identity

H11
Railway durable persistence
+ actual Coder/Landlock verification

H12
oncojevlab deterministic exporter/publisher

H13
expanded semantic/scientific evaluation corpus

H14
frontier policy cleanup/calibration review

H15
documentation reconciliation
+ full verification
```

After every coherent batch:

```text
run owning focused tests
run architecture checker
run git diff --check
commit the batch
```

At integration completion run the full suite.

Do not leave parallel canonical implementations.

---

# G72 — KISS

Do not solve this with:

```text
microservices
agent swarms
distributed queues
generic workflow engines
multiple databases
vector infrastructure without evidence
mass ontology ingestion
mass software harvesting
```

The target remains:

```text
one Python service

one persistent Director
with bounded Coder + CodeMode

one active fresh Researcher

one durable database

one revisioned OncoLab

one scientific-execution abstraction

one generated oncojevlab repository
```

---

# G73 — DOCUMENTATION

Update only existing docs after implementation matches reality.

At minimum:

```text
README.md
docs/ARCHITECTURE.md
docs/EPISTEMIC_CONSTITUTION.md
docs/JEV.md
docs/CAPABILITIES.md
docs/IMPLEMENTATION_PLAN.md

src/oncolab/README.md
src/memory/README.md
src/science/README.md
```

Do not rewrite historical F0–F6 completion evidence.

Add this work as the next implementation stage.

Update D1–D8 disposition only where actual implementation justifies it.

---

# ACCEPTANCE CRITERIA

Implementation is complete only when:

## Director

```text
persistent global research manager
retains Coder
retains CodeMode where useful
bounded /work/director scratch authority
cannot mutate production policy/source
runs bounded work while Researcher is active
event-driven rather than polling
uses semantic Research Memory
maintains global hypothesis/frontier context
detects contradictions
detects capability gaps
supports program review
can truthfully pause
revalidates stale future plans
```

## Researcher

```text
fresh per block
retains Coder
retains CodeMode
owns local research strategy
can use installed scientific Python
can acquire compatible public GitHub methods
uses isolated experiment dependencies
cannot bypass evidence admission
```

## Jev

```text
central to semantic retrieval/comparison
used across memory, capabilities, representations,
hypotheses, contradictions and block candidates

bounded typed projections
native distributions retained
not evidence authority
not lifecycle authority
not capability authority
```

## OncoLab

```text
static catalogue retained
dynamic institutional state added
immutable revisions
block revision pinning
verification/failure/demand history
external capability discovery
bio.tools search
GDC data-asset discovery
GitHub/Bioconda/Bioconductor enrichment
governed promotion
no bulk uncontrolled ingestion
no file UUIDs treated as capabilities
updates between blocks without worker restart
```

## Science

```text
GDC files can be searched and selected truthfully
open files can use exact artifact bridge
controlled access stays explicit
scientific repos can run without Docker-in-Docker
execution identity is reproducible/auditable
Coder output remains non-evidence
```

## Railway

```text
one worker
sequential autonomous blocks
no normal research restart
durable DB
actual Coder confinement status verified or
explicitly blocked
```

## oncojevlab

```text
separate generated repository
human-readable lab history
deterministic
reference-linked
non-authoritative
publication failure harmless to scientific state
```

## Evaluation

```text
correctness tested
semantic utility separately evaluated
capability-search expansion evaluated
cross-block behavior evaluated
resource use reported
no unsupported claim that Jev improves discovery
```

---

# FINAL CODEX REPORT

At completion report:

```text
1. starting HEAD
2. ending HEAD
3. commits/batches
4. files changed

5. F0–F6 contracts preserved

6. Director:
   before
   after
   Coder behavior
   CodeMode behavior
   async lifecycle

7. global Jev capabilities implemented

8. Research Memory changes

9. cross-block/hypothesis/contradiction behavior

10. OncoLab:
    static catalogue
    dynamic state
    revisions
    external discovery
    GDC file discovery
    bio.tools
    Bioconda
    Bioconductor
    GitHub
    promotion governance

11. D1–D8:
    prior disposition
    new disposition
    what remains deferred

12. scientific execution:
    Docker before
    Railway backend after
    environment isolation
    dependency identity

13. Railway:
    persistence
    Coder/Landlock verification
    unresolved blockers

14. oncojevlab:
    exporter
    publication
    failure semantics

15. tests run
16. exact results
17. live smokes performed
18. evaluations performed
19. semantic utility limitations
20. scientific gaps remaining
21. capability gaps remaining
22. deployment gaps remaining
23. intentionally deferred work
24. discrepancies between this prompt and actual current main
```

Do not claim completion because a type, descriptor, test fixture or document exists.

Verify actual behavior.

The final system should remain recognizably OncoJev:

> a disciplined autonomous computational research laboratory, not a generic agent platform.