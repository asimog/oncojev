"""Compatibility one-cycle launcher; delegates to the canonical production CLI.

Use --direction or ONCOJEV_DIRECTION for the broad human research direction.
This launcher supplies no scientific procedure or independent lifecycle.
"""
import sys

from src.__main__ import main as production_main


def main() -> None:
    production_main(["cycle", *sys.argv[1:]])


if __name__ == "__main__":
    main()
