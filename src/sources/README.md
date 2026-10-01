# Public acquisition

`public.py` provides anonymous GDC (`projects`, `cases`, `files`, `annotations`),
UCSC Xena catalogue and public literature metadata clients. `models.py` owns typed
acquisitions/coverage/exact-byte artifacts; `coverage.py` validates page composition.
File search enforces open access. Clients accept no scientific/provider credentials
and bound response bytes.

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

Data-asset discovery and external source expansion belong to the [active plan](../../docs/IMPLEMENTATION_PLAN.md) (H6-H8).
