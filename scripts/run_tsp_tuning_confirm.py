"""10-run confirmation: all three algorithms on eil51 with frozen tuned parameters."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from optimize.config.loader import load_experiment_config  # noqa: E402
from optimize.experiments.models import ExperimentConfig  # noqa: E402
from optimize.experiments.runner import ExperimentRunner  # noqa: E402

SELECTED_PATH = ROOT / "results" / "tuning" / "selected_parameters.json"
BASE_CONFIG = ROOT / "config" / "examples" / "tsp_eil51_comparison.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "tuning_v2" / "confirmation")
    parser.add_argument("--selected", type=Path, default=SELECTED_PATH)
    args = parser.parse_args()

    if not args.selected.exists():
        raise SystemExit(f"Missing tuned parameters: {args.selected}")

    selected = json.loads(args.selected.read_text(encoding="utf-8"))
    base = json.loads(BASE_CONFIG.read_text(encoding="utf-8"))
    winners = selected["winners"]

    for algorithm, winner in winners.items():
        base.setdefault("algorithm_configs", {})[algorithm] = winner["parameters"]

    if selected.get("initial_solution"):
        base.setdefault("domain_config", {})["initial_solution"] = selected["initial_solution"]

    config = ExperimentConfig.model_validate(
        {
            **base,
            "experiment_name": "tuning_confirm_eil51_comparison",
            "runs": args.runs,
            "output": {"directory": str(args.output)},
        }
    )

    args.output.mkdir(parents=True, exist_ok=True)
    config_path = args.output / "tuning_confirm_eil51_comparison.json"
    config_path.write_text(json.dumps(json.loads(config.model_dump_json()), indent=2), encoding="utf-8")

    experiment_dir = ExperimentRunner().run(config_path)
    print(f"Confirmation complete: {experiment_dir}")


if __name__ == "__main__":
    main()
