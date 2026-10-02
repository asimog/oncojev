"""Explicit provider-backed Task 12 observation through the stock service.

The cycle count bounds the experiment, never an in-flight scientific procedure.
Exceptions and incomplete scientific prerequisites remain retained observations.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
from time import perf_counter

from src.autonomous import service_from_environment
from src.config.environment import load_local_environment
from src.application.export import render_snapshot, write_snapshot
from src.persistence.records import RecordKind
from src.persistence.reconstruct import reconstruct_block
from src.persistence.store import SqliteResearchStore
from src.science.qualification import record_reference

ROOT = Path(__file__).resolve().parents[1]
DIRECTION = (
    'Investigate a bounded, public-data lung cancer question using TCGA-LUAD or TCGA-LUSC. '
    'First inspect retained research history and local capabilities. Choose a scientifically eligible descriptive '
    'question about recorded clinical age or mutation events, with explicit source coverage and units. '
    'Compare representation and method alternatives; consider why using file metadata as mutation measurements '
    'would be invalid. Execute and validate the selected analysis on acquired source-bound data. '
    'Do not invent source fields, missing values, mutation absence, callable territory, survival endpoints or expert review. '
    'Check literature context and challenge the result when an eligible method exists; otherwise retain the exact '
    'unavailable prerequisite. An inconclusive result is acceptable. Use actual limitations and prior experience to '
    'choose the next useful test. Do bounded global work while the Researcher runs, wait for events, and yield '
    'after the block completes. Do not repeat equivalent calls. Qualified reusable promotion and remote publication '
    'are unavailable unless their actual retained prerequisites resolve.'
)


class ScenarioComplete(BaseException):
    """Stop only at an observed cycle boundary."""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('run_once', 'serve'), default='run_once')
    parser.add_argument('--cycles', type=int, default=2)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8081)
    args = parser.parse_args()
    if not 1 <= args.cycles <= 3:
        raise ValueError('one to three explicit cycles required')
    load_local_environment(ROOT)
    os.environ['ONCOJEV_MAINTENANCE'] = '0'
    service = service_from_environment(ROOT)
    database = service.paths.database()
    initial = max((r.seq for r in service.store.records()), default=0)
    observations = []
    original_cycle = service.run_once_async
    original_review = service._post_block_review
    completed = 0

    async def cycle(direction):
        nonlocal completed
        if completed >= args.cycles:
            raise ScenarioComplete()
        started = perf_counter()
        item = {'phase': 'run_once', 'cycle_index': completed + 1}
        try:
            result = await original_cycle(direction)
            item.update(status=result.status.value, director_outcome=result.director_outcome.value,
                        block_ids=list(result.block_ids), director_error_type=result.director_error_type)
            return result
        except Exception as error:
            item.update(status='raised', error_type=type(error).__name__)
            raise
        finally:
            completed += 1
            item['elapsed_seconds'] = perf_counter() - started
            observations.append(item)
            print('TRAJECTORY PHASE ' + json.dumps(item), flush=True)

    async def review(direction):
        started = perf_counter()
        try:
            await original_review(direction)
        finally:
            item = {'phase': 'post_block_review', 'cycle_index': completed,
                    'elapsed_seconds': perf_counter() - started}
            observations.append(item)
            print('TRAJECTORY PHASE ' + json.dumps(item), flush=True)
        if args.mode == 'serve' and completed >= args.cycles:
            raise ScenarioComplete()

    service.run_once_async = cycle
    service._post_block_review = review
    args.output.mkdir(parents=True, exist_ok=True)
    frozen = {'application_identity': service.application_content_identity,
              'testing': service.settings.testing, 'policy': service.policy.model_dump(mode='json')}
    error_type = None
    try:
        if args.mode == 'serve':
            service.serve('127.0.0.1', args.port, DIRECTION, 1)
        else:
            async def once():
                try:
                    await cycle(DIRECTION)
                finally:
                    await review(DIRECTION)
            service._loop_runner.run(once())
    except ScenarioComplete:
        pass
    except Exception as error:
        error_type = type(error).__name__
    finally:
        if args.mode != 'serve':
            service.close()
        store = SqliteResearchStore(database)
        try:
            records = [r for r in store.records() if r.seq > initial]
            blocks = sorted({r.block_id for r in records if r.block_id})
            reconstructed = {b: reconstruct_block(store, b).model_dump(mode='json') for b in blocks}
            files = render_snapshot(store)
            write_snapshot(files, args.output / 'export')
            retained = {'basis': frozen, 'mode': args.mode, 'database': str(database),
                        'initial_high_water': initial, 'phases': observations, 'error_type': error_type,
                        'record_counts': dict(Counter(r.kind.value for r in records)),
                        'record_references': [record_reference(r) for r in records],
                        'blocks': reconstructed, 'export_manifest': json.loads(files['manifest.json']),
                        'scientific_utility': None, 'remote_publication': 'unavailable',
                        'qualification': 'observations; evaluate all Task 12 criteria against retained records'}
            (args.output / 'observation.json').write_text(json.dumps(retained, indent=2) + '\n')
            print('TRAJECTORY RETAINED ' + json.dumps({'output': str(args.output), 'database': str(database),
                  'phases': observations, 'record_counts': retained['record_counts'], 'error_type': error_type}), flush=True)
        finally:
            store.close()


if __name__ == '__main__':
    main()
