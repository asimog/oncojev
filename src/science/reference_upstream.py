"""Independent direct invocation of pinned upstream mean for reference comparison."""
import importlib.util
import json
from pathlib import Path
import sys


def main():
    request = json.loads(Path(sys.argv[1]).read_text())
    if set(request) != {'values'}:
        raise ValueError('undeclared reference parameter')
    spec = importlib.util.spec_from_file_location('upstream_reference', Path.cwd() / 'maths/average_mean.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print(json.dumps({'values': {'mean': module.mean(request['values'])}}))


if __name__ == '__main__':
    main()
