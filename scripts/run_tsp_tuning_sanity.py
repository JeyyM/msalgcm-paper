"""Quick sanity check: 3-algorithm comparison on eil51 with frozen tuned parameters."""

from __future__ import annotations

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
SANITY_DIR = ROOT / "results" / "tuning" / "sanity"


def main() -> None:
    if not SELECTED_PATH.exists():
        raise SystemExit(f"Missing tuned parameters: {SELECTED_PATH}. Run analyze_tsp_tuning.py first.")

    selected = json.loads(SELECTED_PATH.read_text(encoding="utf-8"))
    base = json.loads(BASE_CONFIG.read_text(encoding="utf-8"))
    winners = selected["winners"]

    for algorithm, winner in winners.items():
        base.setdefault("algorithm_configs", {})[algorithm] = winner["parameters"]

    config = ExperimentConfig.model_validate(
        {
            **base,
            "experiment_name": "tuning_sanity_eil51_comparison",
            "runs": 3,
            "output": {"directory": str(SANITY_DIR)},
        }
    )

    config_path = SANITY_DIR / "tuning_sanity_eil51_comparison.json"
    SANITY_DIR.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(json.loads(config.model_dump_json()), indent=2), encoding="utf-8")

    experiment_dir = ExperimentRunner().run(config_path)
    print(f"Sanity check complete: {experiment_dir}")


if __name__ == "__main__":
    main()
