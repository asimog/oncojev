# Public acquisition

`public.py` provides anonymous GDC (`projects`, `cases`, `files`, `annotations`),
UCSC Xena catalogue and public literature metadata clients. `models.py` owns typed
acquisitions/coverage/exact-byte artifacts; `coverage.py` validates page composition.
File discovery preserves open, controlled and unknown access metadata. Anonymous
byte acquisition requires explicit open access. Clients accept no scientific or
provider credentials and bound response bytes.

Literature searches retain the exact query, retrieval time, reported result count
and deposited abstracts where supplied. Raw abstract text/markup is bounded to
2048 UTF-8 bytes per work and 8192 per query, with explicit truncation markers.
Absent abstracts remain absent; no full text is fetched. Even an empty query or
all reported hits cannot establish comprehensive literature coverage or novelty.
Legacy title-only records retain their hashes and unknown retrieval time/coverage.

GDC search records offsets, endpoint-specific ID ordering, requested/returned sizes, reported
totals and unique IDs. Ordered page combination rejects overlap, gaps, repeated
pages, changing totals and mixed queries. Observed page completeness does not
guarantee source snapshot consistency or population representativeness. Unrequested
fields are distinct from missing analysis requirements; no ORM/internal graph
contract is presented as public API truth.

`acquire_gdc_file` accepts one UUID, checks explicitly open metadata, byte budget,
source size/MD5 where present, and retains exact streamed bytes. It accepts no URL
or credentials and follows no redirects. The service reserves block/service download,
workspace/archive and durable-artifact capacity before opening the data stream;
unknown size reserves bounded remaining capacity. Failed transfers retain actual
bytes and operational receipts. Disk checks include SQLite/base64 headroom. Licence/release are unknown unless
provided by source metadata. See the official
[download contract](https://docs.gdc.cancer.gov/API/Users_Guide/Downloading_Files/).
Successful acquisition does not establish scientific utility.

Data-asset discovery and external source expansion belong to the [active plan](../../docs/IMPLEMENTATION_PLAN.md).

`representation.py` checks a bounded declared need against retained row schemas,
entity identities, explicit source units/build facts and coverage. Metadata listings
remain metadata. Missing, incompatible and unmeasured prerequisites defer semantic
eligibility; no assay matrix, join, transformation or independence is inferred.
