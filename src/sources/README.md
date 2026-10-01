# Public acquisition

Current source contracts and F5 delivery records are preserved in the
[completed F0–F6 plan](../../docs/IMPLEMENTATION_PLAN_COMPLETED_F0_F6.md).
[The active H0–H15 plan](../../docs/IMPLEMENTATION_PLAN.md) owns next-stage status.

GDC search records offsets, stable ordering, requested/returned sizes, reported
totals and unique IDs. Ordered page combination rejects overlap, gaps, repeated
pages, changing totals and mixed queries. Observed page completeness does not
guarantee source snapshot consistency or population representativeness. Unrequested
fields are distinct from missing analysis requirements; no ORM/internal graph
contract is presented as public API truth.

`acquire_gdc_file` accepts one UUID, checks explicitly open metadata, byte budget,
source size/MD5 where present, and retains exact streamed bytes. It accepts no URL
or credentials and follows no redirects. Licence/release are unknown unless
provided by verified source metadata. The official
[download contract](https://docs.gdc.cancer.gov/API/Users_Guide/Downloading_Files/)
and one 51,100-byte anonymous example were checked on 2026-10-01; this does not
establish accessibility of all examples or scientific utility.

## Next-stage target: bounded data assets and external discovery

**Planned in H6–H8.** Build first-class GDC file/data-asset discovery on the current
bounded metadata retrieval and exact-byte acquisition bridge. Preserve filters,
requested fields, ordering, offsets/pages, reported totals, query identity and
known release identity. Use verified mapping/field contracts where feasible.
Retain file identity/name/access/state/category/type/format, strategy/platform,
size/MD5 and available workflow, release and case/project references with retrieval
time. Missing metadata stays unknown. Current overlap, gap, coverage, ownership
and exact size/hash validation remain authoritative.

Individual GDC files are typed data assets, never OncoLab capability descriptors.
Group actual retrievable representations by type, format, entity unit, strategy,
coverage and transformation level; deterministic availability precedes bounded
Jev sufficiency/assumption-fit measurement. Selected explicitly open files use the
existing artifact bridge with source UUID/request/access/ownership, byte size,
supplied GDC MD5 and OncoJev SHA-256. Controlled files require a separately
supported explicit credential path and must not be silently attempted. Manifests
are bounded to a declared need; bulk harvesting is not the default. Representation
discovery does not mandate new mutation, expression, TMB or survival analyses.

External software discovery is a separate bounded search/describe surface.
bio.tools candidate cards support verified query/domain/EDAM/input/output filters
and pagination, retaining supplied metadata and links, query/page identity,
retrieval time, hashes where feasible, omissions and failures. Returned EDAM
IDs/terms support controlled normalization without full ontology ingestion.
GitHub inspection enriches repository/commit/release/package/lockfile information;
Bioconda enriches compatibility/dependency/build/licence metadata without installing
Conda. Bioconductor records initially remain metadata-only until an actual R
backend is implemented and verified.

External registries are mutable; retained receipts do not imply immutable source
snapshots. Public GitHub visibility does not establish licence permission, a
bio.tools listing does not establish validated execution, and a GDC file record
does not establish open access. Outages/failures remain operational outcomes.
Jev suitability cannot override missing routes, runtimes, inputs or access.
Reusable promotion belongs to versioned Python governance, after execution,
replay, dependency and contract validation; source adapters cannot admit evidence.

See [capability boundaries](../../docs/CAPABILITIES.md) and the
[complete supplied requirements](../../docs/references/NEXT_STAGE_AUTONOMOUS_LAB_REQUIREMENTS.md)
for G19–G33 and G56–G57. These phases partially address D2/D6 and provide access
infrastructure for need-driven D7; the adapter and representation targets are not
claims of delivered behavior.
