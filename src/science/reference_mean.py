"""Canonical public-method probe, not a registered biological capability."""
import importlib.util
import json
import math
from pathlib import Path
import sys


def main():
    request = json.loads(Path(sys.argv[1]).read_text())
    if set(request) != {"values"}:
        raise ValueError("undeclared mean parameter")
    values = request["values"]
    if not isinstance(values, list) or not values or any(
        isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values
    ):
        raise ValueError("a nonempty finite numeric vector is required")
    # Caller acquired an immutable TheAlgorithms/Python repository. Import only
    # this canonical operation; its result is compared independently by the probe.
    spec = importlib.util.spec_from_file_location("canonical_mean", Path.cwd() / "maths" / "average_mean.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print(json.dumps({"values": {"mean": module.mean(values)}}))


if __name__ == "__main__":
    main()
