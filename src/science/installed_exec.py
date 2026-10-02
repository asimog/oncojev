"""Trusted installed-operation worker; no service state or credentials enter here."""
import importlib.util
import json
from pathlib import Path
import sys


def main():
    application = Path(sys.argv[1]).resolve(strict=True)
    root = Path(sys.argv[2]).resolve(strict=True)
    spec = importlib.util.spec_from_file_location("confinement", application / "src/runtime/confinement.py")
    confinement = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(confinement)
    confinement.restrict_filesystem((root,), (application / "src", Path(sys.prefix), Path(sys.base_prefix)))
    confinement.restrict_process_authority()
    # -I omits the checkout from sys.path. Only this trusted owner adds it.
    sys.path.insert(0, str(application))
    from src.science.execution import ScienceExecutor
    from src.science.models import AnalysisSpec, InvalidAnalysis
    from src.sources.models import AcquisitionRecord, ScientificArtifact
    request = json.loads((root / "request.json").read_text(encoding="utf-8"))
    inputs, name = request["inputs"], request["operation"]
    science = ScienceExecutor()
    try:
        if name == "execute":
            value = science.execute(AnalysisSpec.model_validate(inputs[0]))
        elif name == "execute_source":
            value = science.execute_source(AcquisitionRecord.model_validate(inputs[0]), AnalysisSpec.model_validate(inputs[1]))
        elif name == "measure_acquisition":
            value = science.measure_acquisition(AcquisitionRecord.model_validate(inputs[0]), *inputs[1:])
        elif name == "parse_gdc_star_counts":
            from src.science.representation import parse_gdc_star_counts
            value = parse_gdc_star_counts(ScientificArtifact.model_validate(inputs[0]), tuple(inputs[1]))
        elif name == "parse_gdc_table":
            from src.science.representation import parse_gdc_table
            value = parse_gdc_table(ScientificArtifact.model_validate(inputs[0]), inputs[1], tuple(inputs[2]) if len(inputs) > 2 else ())
        elif name == "derive_gdc_clinical":
            from src.science.representation import derive_gdc_clinical
            value = derive_gdc_clinical(AcquisitionRecord.model_validate(inputs[0]), *inputs[1:])
        elif name == "join_gdc_case_inputs":
            from src.science.representation import join_gdc_case_inputs
            value = join_gdc_case_inputs(AcquisitionRecord.model_validate(inputs[0]), AcquisitionRecord.model_validate(inputs[1]), inputs[2])
        elif name == "assemble_gdc_expression":
            from src.science.representation import assemble_gdc_expression
            value = assemble_gdc_expression(tuple(AcquisitionRecord.model_validate(v) for v in inputs[0]), AcquisitionRecord.model_validate(inputs[1]), *inputs[2:])
        elif name == "line_figure":
            from src.visualization.service import line_figure
            value = line_figure(*inputs)
        else:
            raise InvalidAnalysis("unsupported installed scientific operation")
        payload = {"status": "success", "value": [v.model_dump(mode="json") for v in value]
                   if isinstance(value, tuple) else value.model_dump(mode="json")}
    except ValueError as error:
        payload = {"status": "invalid", "error": str(error)}
    (root / "result.json").write_text(json.dumps(payload, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
