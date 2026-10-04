# OncoLab Index

`OncoLabIndex` is the only OncoJev domain index used by Director and Researcher.
It holds current bounded planning descriptors and reference-linked durable execution
observations. Fresh bootstrap imports no historical verification. The explicit
`load_verification_records` archive reader can inspect `proven/verified-executions.yaml`;
that archive is not production bootstrap or fresh qualification. The agents receive one bounded
descriptor plus its verification summary through `describe_oncolab`; they do
not read YAML files directly. A descriptor is not execution authority, and a
proven record does not automatically promote local work to reusable capability.

OncoLab is deliberately separate from Pydantic AI's framework capabilities and
tools. Framework integration remains under `src/runtime/pydantic_ai/`.

`labskills/` contains selected procedural guidance for Researcher blocks. Skills
can guide use of the index and typed wrappers, but never execute work or create
evidence.

Jev descriptors remain distinct from local `JevQuestionSpec`s. A reusable Jev
capability requires reproducible evaluation evidence.

Verification records use typed, integrity-bound execution references and a declared
scope/outcome. Bundled artifacts must live under `proven/artifacts/`; durable record
references also identify their owning block. Institutional composition resolves
durable receipts under their stored registry/application basis; fresh construction
loads current definitions without bundled observations.
Historical artifacts explicitly disclose missing inputs. Execution observation,
validated measurement and exploratory artifact creation do not promote a family
or a local method into reusable capability.

Progressive search returns compact cards with a contract hash and explicit
snapshot-bound continuation. The response cap is separate from the configured
candidate budget. Zero lexical overlap stays reachable on later pages; lexical
ranking is not a suitability judgment. Describe selected IDs to obtain contracts
and declared routes. Execution checks distinguish metadata-only, access, missing
inputs and callable operation prerequisites. Library installation is not authority.

ScientificNeed expresses the question/estimand, population/design, information and
relationship requirements, measurement requirements, constraints and uncertainty.
Discovery can retain that context before acquisition or representation selection.
Index receipts link the complete need and hash to the returned cards. Constraints
remain planning context, not automatically satisfied prerequisites. Method readiness
requires an actual representation contract and owned input checks; unbound input
requirements remain unknown/unready. Jev comparison is optional and cannot grant
execution or evidence authority.

Current institutional and discovery contracts are described in
[institutional ownership](../../docs/ARCHITECTURE.md#ownership-boundaries). Unfinished work is tracked only in
the [active plan](../../docs/IMPLEMENTATION_PLAN.md).
