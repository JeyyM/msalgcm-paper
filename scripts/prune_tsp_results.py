"""Keep one TSP batch per (instance, algorithm) and delete duplicate experiment folders."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from optimize.api.services.tsp_catalog import prune_duplicate_tsp_experiments  # noqa: E402


def main() -> int:
    removed = prune_duplicate_tsp_experiments()
    if removed:
        print(f"Removed {len(removed)} duplicate TSP experiment folder(s):")
        for experiment_id in removed:
            print(f"  - {experiment_id}")
    else:
        print("No duplicate TSP experiment folders to remove.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
