"""Apply final merged tuning winners to all comparison configs."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELECTED = ROOT / "results" / "tuning" / "selected_parameters.json"
EXAMPLES = ROOT / "config" / "examples"


def main() -> None:
    selected = json.loads(SELECTED.read_text(encoding="utf-8"))
    winners = selected["winners"]
    domain_config = selected["domain_config"]
    runs = selected.get("final_comparison_runs", 30)

    for path in sorted(EXAMPLES.glob("tsp_*_comparison.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["domain_config"] = dict(domain_config)
        payload["runs"] = runs
        for algorithm, winner in winners.items():
            payload.setdefault("algorithm_configs", {})[algorithm] = winner["parameters"]
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"Updated {path.name}")


if __name__ == "__main__":
    main()
