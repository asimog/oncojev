# Evaluation

Evaluation code exercises production owners and records scoped comparisons. It is
outside the installed `src` package; production never imports it. Labels, expected
results, scripted component choices and generated reports are not scientific evidence.

Use `scripts/evaluate_references.py`, `scripts/evaluate_selection.py` and
`scripts/evaluate_representation.py` for the corresponding comparisons. Reference
corpora and their retained assessments live in `reference/`; generated outputs live
under `results/` or the launcher’s explicit output path. Scripted component evaluations
prove their declared contracts, not whole-lab autonomy.

Candidate utility proof retention and resolution are shared production mechanisms in
`src/oncolab/utility.py`. Evaluation may produce observations for that owner; existing
candidate, scope, application, independent-review and repetition guards determine
whether a proof resolves. An evaluation pass alone does not qualify a capability.
