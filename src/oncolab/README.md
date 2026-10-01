# OncoLab Index

`OncoLabIndex` is the only OncoJev domain index used by Director and Researcher.
It holds bounded, typed planning descriptors and loads durable verified-execution
records from `proven/verified-executions.yaml`. The agents receive one bounded
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
references also identify their owning block. Factory composition loads resolvable
durable receipts alongside bundles and deduplicates verification identities.
Historical artifacts explicitly disclose missing inputs. Execution observation,
validated measurement and exploratory artifact creation do not promote a family
or a local method into reusable capability.
