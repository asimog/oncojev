# OncoLab labskills

`labskills` contains short, adapted procedural guidance that a Researcher may
select for one JevBlock. It is not the OncoLab Index, an executable scientific
method, a Pydantic AI capability, or standing prompt context.

The initial cards cover statistical method selection, scientific visualization,
literature retrieval, Biopython/scikit-bio representation choices, and
reproducible public-method acquisition. They were selectively adapted from the
pinned K-Dense Scientific Agent Skills and ClawBio references recorded in
`.upstream/manifest.yaml`. Neither upstream repository is imported, executed,
or automatically trusted.

Each card is selected only by `load_research_skills` for the active block and
is retained only in that block's deterministic `BlockSkillStore`. A skill can
guide selection of a typed wrapper, but it cannot run a method, create
`MeasuredResult`, admit evidence, or promote a method to reusable status.
