"""Agent telemetry keeps useful hierarchy without exporting payload content."""

import json
import os
from pathlib import Path
import subprocess
import sys


def test_configured_agent_traces_omit_prompt_and_output_content():
    # A child process isolates the process-wide OpenTelemetry provider and hooks.
    script = """
import asyncio
import json
from pathlib import Path
import logfire
from opentelemetry import trace
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pydantic_ai.models.test import TestModel
from src.config.loader import load_models_config, load_runtime_config
from src.runtime.pydantic_ai.factory import build_system

system = build_system(
    load_models_config(Path('config/models.yaml')),
    load_runtime_config(Path('config/runtime.yaml')),
)
exporter = InMemorySpanExporter()
trace.get_tracer_provider().add_span_processor(SimpleSpanProcessor(exporter))
sentinel = 'PRIVATE_PAYLOAD_78b622'
model = TestModel(custom_output_args={
    'interpretation': sentinel,
    'hypotheses': [{'hypothesis_id': 'h', 'statement': sentinel,
                    'within_scope': True, 'proposed_test': sentinel}],
    'uncertainty': sentinel,
})
with system.runtime.reasoner._agent.override(model=model):
    result = asyncio.run(system.runtime.reasoner.generate(sentinel, sentinel))
assert result.interpretation == sentinel
logfire.force_flush()
spans = exporter.get_finished_spans()
roots = [s for s in spans if s.attributes.get('gen_ai.operation.name') == 'invoke_agent']
assert len(roots) == 1
assert roots[0].attributes['gen_ai.agent.name'] == 'oncojev-reasoner'
assert roots[0].resource.attributes['service.name'] == 'oncojev-agents'
assert any(s.parent and s.parent.span_id == roots[0].context.span_id for s in spans)
for span in spans:
    assert sentinel not in json.dumps(dict(span.attributes))
    for event in span.events:
        assert sentinel not in json.dumps(dict(event.attributes))
print(json.dumps({'spans': len(spans)}))
"""
    environment = os.environ.copy()
    environment.update(
        LOGFIRE_SEND_TO_LOGFIRE="false",
        OPENROUTER_API_KEY="unused-test-credential",
        TYPESAFE_API_KEY="unused-test-credential",
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[2],
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    assert json.loads(result.stdout)["spans"] >= 2
