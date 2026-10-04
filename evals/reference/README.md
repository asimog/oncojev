# Published reference comparisons

The default mission is lung cancer. `scientific-v1.json` contains reference-only
numerical data from R's published Anscombe dataset, independent SciFact expert
annotations for twelve lung/pulmonary claim-document pairs, and generated adverse
contracts. Each label retains its own basis and review status. Generated memory,
relation and invalid-input contracts are not independently scientifically reviewed.

SciFact attribution: David Wadden, Shanchuan Lin, Kyle Lo, Lucy Lu Wang,
Madeleine van Zuylen, Arman Cohan and Hannaneh Hajishirzi,
[Fact or Fiction: Verifying Scientific Claims](https://aclanthology.org/2020.emnlp-main.609/),
EMNLP 2020. Claims/annotations are CC BY 4.0; abstracts are ODC-By 1.0.
[Source and licence](https://github.com/allenai/scifact/blob/master/LICENSE.md).
The downloaded release SHA256 and original annotation identities accompany the cases.

Adapters receive public inputs only. Expected outputs, reviewer records, rationales,
case IDs and split labels are withheld from runtime/model projections. Published
material may occur in model pretraining; the split does not prove independence from
pretraining. Tuning and held-out results remain separate. Fixture clients establish
routing; repeated live measurements report native distributions and failures.

Run `python -B -m scripts.evaluate_references --output var/reference-report.json`
for offline checks. Explicit provider qualification adds `--live --repeats 3`;
`--case-prefix scifact-lung-` selects the independently annotated lung cases.
The existing fresh-condition harness owns the four semantic conditions, matched
policy and bounded memory ablations. No winner or clinical utility is assumed.
Candidate-bound utility remains unsupported without reviewed scope-bound live proof.
No benchmark label is scientific evidence and no comparison imports into research.

`semantic-continuation-v1.json` uses the same reference contract and consumer.
It retains fresh LUAD/LUSC case responses for matched replay, source-backed clinical/
duration alternatives, selected-input summaries and paired exploratory analyses.
Its explicit relation and memory cases are generated tuning contracts. Every new
suitability/usefulness label has pending independent review; published API/method
documentation supports input/numerical contracts, not scientific decision utility.
The comparison scores representation/method recall from production generator views
and durable receipts, rather than counting supplied alternatives as retrieved.
Probability, label classification, Python policy and selected-choice variability
are separate observations. Costs and unavailable classifiers remain unknown.

`semantic-source-catalogue-v1.json` measures actual mixed-modality generator recall
and durable omissions without declaring any discovered asset ready.
`semantic-relations-v1.json` retains explicit generated relation controls; the dated
assessment preserves baseline, failed first wording variant and final v3 repeats.
All are tuning-only; the final fixed contract replay does not qualify live scientific
utility or the ordinary-budget autonomous environment.
