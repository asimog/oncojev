"""Export a persisted prefix; publishing runs only in an isolated local checkout."""
import argparse
import json
from pathlib import Path

from src.application.export import render_snapshot, write_snapshot
from src.application.publication import publish_snapshot
from src.persistence.store import SqliteResearchStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--high-water", type=int)
    parser.add_argument("--publish-checkout")
    args = parser.parse_args()
    store = SqliteResearchStore(Path(args.database))
    try:
        files = render_snapshot(store, high_water=args.high_water)
        write_snapshot(files, args.out)
        manifest = json.loads(files["manifest.json"])
        print(json.dumps({"manifest": manifest, "publication": publish_snapshot(store, files, args.publish_checkout)
                          if args.publish_checkout else "dry_run"}))
    finally:
        store.close()


if __name__ == "__main__":
    main()
