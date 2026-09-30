"""Minimal executable entry point for the initial vertical slice."""

from pathlib import Path

from oncojev.service import run_synthetic_vertical_slice


def main() -> None:
    dossier = run_synthetic_vertical_slice(Path(__file__).resolve().parents[2])
    print(f"CURRENT BLOCK COMPLETE: {dossier.block_id}; continuation={dossier.preferred_continuation}")


if __name__ == "__main__":
    main()
