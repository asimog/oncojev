# Capability semantics

`CapabilityRegistry` is the one shared application registry for Director and Researcher. It provides the broad global catalogue through bounded deterministic retrieval and records verified execution separately from descriptor status. The Pydantic AI harness is only a client of this registry through runtime dependencies; it owns no registry. The `registries/capabilities/` directory is the repository-native record/evidence location for that one registry, not a second runtime implementation.

The Index describes data/source capabilities, scientific and statistical methods, transformations, software, visualization, literature/knowledge, and Jev measurements. It uses typed descriptors with purpose, contracts, applicability, limitations, assumptions, missingness semantics, availability, execution/access policy, resource class, validation state, and provenance. It is metadata only: typed wrappers remain the only route to execution.

Index availability is explicit: `known`, `available`, `installed`, `acquirable`, `validated`, `reusable`, `unavailable`, or `forbidden`. It is distinct from validation state: a known or acquirable item is not a validated executable scientific capability. Retrieval is deterministic metadata/text matching and capped at 20 results; neither agent receives the complete catalogue in its prompt.

The initial catalogue contains over 100 descriptors. It includes GDC endpoint, retrieval, pipeline, entity, and workflow-reference metadata plus statistical-method planning families; these entries remain descriptors, not pipelines or arbitrary Python APIs.

Phase 3 makes a deliberately small subset executable through typed Researcher tools: anonymous GDC metadata retrieval (with an enforced `files.access == open` filter for file searches), anonymous UCSC Xena catalogue lookup, public literature metadata retrieval, NumPy/pandas/SciPy/statsmodels measurements, and matplotlib SVG `FigureArtifact` production. Each source wrapper accepts no credentials. It returns provenance-bearing acquisition context, never ScientificEvidence. Deterministic Science returns a `MeasuredResult`; only a separate admission call can produce ScientificEvidence. Figures and literature remain non-evidentiary artifacts/context.

Capability maturity remains explicit:

| State | Meaning |
| --- | --- |
| Descriptor | Catalogue metadata only. |
| Local capability | A block- or application-local implementation or question. |
| Validated capability | Has defined validation evidence for its declared use. |
| Reusable capability | Validated, provenance-bearing, and eligible for registry reuse. |

`ScientificCapability` is deterministic executable scientific work. `JevCapability` is an evaluated reusable semantic measurement. A `JevQuestionSpec` is normally a local semantic probe. A Skill is progressive procedural/domain guidance. Pydantic AI capabilities/tools are framework plumbing and live behind `src/runtime/pydantic_ai/`.
