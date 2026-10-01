"""Autonomous worker and read-only API entry point."""

import argparse
import os
from pathlib import Path

from src.autonomous import DEFAULT_DIRECTION, service_from_environment


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("serve", "cycle"), nargs="?", default="serve")
    parser.add_argument("--direction", default=os.environ.get("ONCOJEV_DIRECTION", DEFAULT_DIRECTION))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    service = service_from_environment(root)
    if args.command == "cycle":
        try:
            result = service.run_once(args.direction)
            print(f"AUTONOMOUS CYCLE {result.status.value.upper()}: {result.block_ids[0]}; director={result.director_outcome.value}; dossiers={len(result.dossiers)}")
        finally:
            service.close()
        return
    service.serve(
        os.environ.get("HOST", "0.0.0.0"),
        int(os.environ.get("PORT", "8080")),
        args.direction,
        int(os.environ.get("ONCOJEV_AUTONOMOUS_INTERVAL_SECONDS", "3600")),
    )


if __name__ == "__main__":
    main()
