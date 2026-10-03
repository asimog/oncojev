"""Quick published-reference checks through fresh existing evaluation conditions."""
import argparse
import json
from pathlib import Path
from src.config.loader import load_models_config, load_runtime_config
from src.config.models import RuntimeMode
from src.evals.reference import evaluate_reference_cases, load_reference_corpus, reference_consumer_adapter
from src.runtime.pydantic_ai.agents import create_agents


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus', type=Path, help='Explicit retained corpus using the existing reference contract')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--live', action='store_true', help='Explicit provider comparisons; scientific labels never enter model prompts')
    parser.add_argument('--repeats', type=int, default=1)
    parser.add_argument('--case-prefix', default='')
    parser.add_argument('--memory-alternatives', nargs='+', type=int, choices=(0, 3), default=[0, 3])
    parser.add_argument('--search-comparison', action='store_true', help='Matched cases for the five existing search owners')
    parser.add_argument('--conditions', nargs='+', choices=('science_only', 'science_reasoner', 'science_jev', 'science_jev_reasoner'))
    parser.add_argument('--whole-lab', action='store_true', help='Controlled multi-block SDK composition using the same reference owner')
    parser.add_argument('--search-mode', choices=('retained_only', 'open_proposal'), default='open_proposal')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    cases = tuple(case for case in load_reference_corpus(args.corpus or root / 'evals/reference/scientific-v1.json') if case.case_id.startswith(args.case_prefix))
    if args.search_comparison:
        cases = tuple(case for case in cases if case.public_inputs['operation'] == 'search_comparison' and case.split == 'tuning')
    if args.whole_lab:
        cases = tuple(case.model_copy(update={'public_inputs': {**case.public_inputs, 'operation': 'whole_lab', 'search_mode': args.search_mode}})
            for case in cases if case.public_inputs['operation'] == 'numeric' and not case.expected.get('invalid_rejected'))
    if not cases: parser.error('no selected cases')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    partial = args.output.with_suffix('.jsonl')
    def retain_row(row):
        with partial.open('a') as stream:
            stream.write(json.dumps(row) + '\n')
        print(json.dumps({'case_id': row['case_id'], 'condition': row['condition'], 'repetition': row['repetition'],
            'agreement': row['agreement'], 'failure_type': row['observations'].get('failure_type')}), flush=True)
    from src.evals.harness import CONDITIONS
    from src.evals.models import EvaluationCondition
    selected_conditions = tuple(EvaluationCondition(value) for value in args.conditions) if args.conditions else CONDITIONS
    policy = load_runtime_config(root / 'config/runtime.yaml').model_copy(update={'mode': RuntimeMode.LIVE if args.live else RuntimeMode.DETERMINISTIC})
    report = evaluate_reference_cases(cases, reference_consumer_adapter, models=load_models_config(root / 'config/models.yaml'),
        policy=policy,
        environment=None if args.live else {}, repeats=args.repeats, conditions=selected_conditions, memory_alternatives=tuple(args.memory_alternatives), on_row=retain_row, agents_factory=lambda: create_agents('test', 'test', enable_coder=False, unbounded_work=policy.unbounded_work))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'cases': len(cases), 'comparisons': len(report['rows']), 'agreement': sum(r['agreement'] is True for r in report['rows']),
        'disagreement': sum(r['agreement'] is False for r in report['rows']), 'unknown': sum(r['agreement'] is None for r in report['rows']),
        'mode': report['mode'], 'scientific_utility': None, 'reviewed_cases': sum(case.independent_review == 'reviewed' for case in cases)}))


if __name__ == '__main__': main()
